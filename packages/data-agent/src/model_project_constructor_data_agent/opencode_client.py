"""OpenCode-CLI-backed :class:`LLMClient` for the Data Agent (standalone wheel).

Where the ``anthropic`` and ``bedrock`` providers call an SDK, this one shells out
to the **``opencode`` command-line agent** (``github.com/anomalyco/opencode``) with
``run --format json`` and parses its JSONL event stream. OpenCode is itself a
vendor-agnostic multiplexer (75+ providers via the AI SDK / Models.dev), so this
one adapter reaches many underlying vendors through the *operator's* OpenCode
config — which is the whole point: see ``Architecture-Decisions.md`` AD-11 and the
full design in ``docs/planning/opencode-adapter-spec.md``.

**Naming caveat — please read before "fixing" it.** This class inherits from
:class:`AnthropicLLMClient` while not necessarily talking to Anthropic. That is
deliberate. The base class is this wheel's **prompt-and-parse** layer that happens
to carry an Anthropic transport; the subclass replaces *only* the transport. Every
prompt, every JSON-shape instruction, the ``PrimaryQuerySpec`` constructors, the
per-caller fenced-text ``_extract_json`` and the optional
``rank_candidate_tables`` are **inherited unchanged**, so prompt drift across
providers is structurally impossible — exactly the argument that justifies
``bedrock_client.py`` (spec D1).

**Decoupling (C4).** This module imports only the wheel and the stdlib — never the
orchestrator (``tests/test_data_agent_decoupling.py``). It is a near-twin of
``src/model_project_constructor/agents/intake/opencode_client.py``; the duplication
is forced by that boundary and guarded by ``tests/test_llm_json_parity.py``.

**The system prompt is folded into the user message (spec D2).** ``opencode run``
has **no** ``--system`` flag, so each call sends ``system + "\\n\\n" + user`` as one
message. This is a real, measured quality risk — verified end-to-end for the
intake seam's ``next_question`` in spec Appendix A.3, but **no data-agent method
was exercised at all** in that spike (Appendix A.5). The eval gate (spec Phase 4)
is what discharges it. Do not flip a production default on this provider before
those thresholds are measured.

**Safety — the agent definition is a control, not a nicety.** Spec hazard H4
originally claimed OpenCode's permission default was already safe. Phase 1
**disproved that**: with no ``--auto``, a live run listed a directory, read a file
and disclosed its contents, exiting 0 (spec Appendix A.4 C1). Permission
auto-reject does **not** cover the ``read`` tool. So this client *always* writes
:data:`AGENT_DEFINITION` — which denies ``edit``/``write``/``bash``/``read``/
``webfetch`` — into its sandbox and *always* selects it with ``--agent``. There is
deliberately **no** constructor option to run without it; ``agent_name`` renames
the generated definition, it does not substitute a caller-owned one. Together with
the ephemeral ``--dir`` sandbox that is the only thing standing between this
adapter and the host filesystem — which for this wheel may sit next to database
credentials.

Other hazards closed here, each verified in spec Phase 1:

* the prompt goes on **stdin**, never argv, so ``DataRequest`` free text cannot
  leak via ``ps`` (H2), and stdin is a pipe this process closes — never inherited,
  which hung a probe for a full timeout with zero output (H1);
* ``--auto`` is never passed (H4), pinned by a negative test;
* the sandbox is created **once per client instance**, never per call: an agent
  definition makes OpenCode materialise ``.opencode/node_modules`` at runtime
  (spec Appendix A.4 C6).

**Zero new Python dependencies** — stdlib only (spec D5). The cost is a new *class*
of dependency instead: the ``opencode`` binary must be on ``PATH``, checked at
construction so a missing binary fails immediately rather than mid-run.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from collections.abc import Callable
from typing import Any

from model_project_constructor_data_agent.anthropic_client import (
    DEFAULT_MAX_TOKENS,
    AnthropicLLMClient,
    LLMParseError,
)

#: No model is pinned by default (spec D6). OpenCode model ids are
#: ``provider/model`` strings drawn from Models.dev; naming one here would
#: silently re-introduce vendor choice into *this* repository, which is the
#: opposite of the adapter's purpose. ``None`` means "omit ``--model`` and let the
#: operator's own ``opencode.json`` decide". The cost is reproducibility, so every
#: evaluated or production run must still pass an explicit model.
DEFAULT_MODEL: str | None = None

#: Stored in ``self._model`` when no model is configured. The parent types
#: ``_model`` as ``str``, so the "unset" state is the empty string rather than
#: ``None``; :meth:`OpenCodeLLMClient._argv` then omits ``--model`` entirely.
_NO_MODEL = ""

#: Matches the Anthropic SDK's own default request timeout, so a slow provider
#: behind OpenCode fails on the same clock as a slow provider behind the SDK.
DEFAULT_TIMEOUT_S = 600.0

DEFAULT_EXECUTABLE = "opencode"

#: Basename of the generated agent definition — OpenCode derives the agent id from
#: the filename.
DEFAULT_AGENT_NAME = "mpc-structured"

#: Spec D2's fold. Pinned as a constant so both packages' copies stay identical
#: and the parity battery can assert on it.
SYSTEM_USER_SEPARATOR = "\n\n"

#: The locked-down agent definition written into every sandbox.
#:
#: **The YAML must stay block-style.** Flow-style (``permission: {edit: deny, …}``)
#: silently breaks agent loading: OpenCode prints usage help to stderr, emits
#: nothing on stdout and exits non-zero (spec Appendix A.4 C5). Since this file is
#: generated by *us*, that failure would be a bug in this module — which is why
#: :meth:`OpenCodeLLMClient._run` diagnoses it distinctly.
#:
#: ``read`` and ``webfetch`` are denied alongside the mutating tools because the
#: default is **not** safe (Appendix A.4 C1). ``mode: primary`` is kept because
#: every verified Phase 1 run set it; whether it is strictly required was never
#: isolated (Appendix A.5).
AGENT_DEFINITION = """\
---
description: Non-interactive structured-output adapter for Model Project Constructor
mode: primary
permission:
  edit: deny
  write: deny
  bash: deny
  read: deny
  webfetch: deny
---

Answer the user's message directly and return only what it asks for. Never use
tools. Do not describe your reasoning, and add no commentary before or after the
requested output.
"""

#: OpenCode colours its human-readable output; stripped before an excerpt goes
#: into an exception message.
_ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")

#: The finish reason that means "the model hit its output ceiling". ``opencode
#: run`` exposes no ``--max-tokens`` flag, so ``max_tokens`` is inert for this
#: provider — but ``step_finish.reason`` restores the truncation guard the SDK
#: clients get from ``stop_reason`` (spec Appendix A.4 C3). Phase 1 observed
#: ``"stop"`` and ``"tool-calls"``; no truncation was forced, so this exact
#: spelling is inferred from the AI SDK's vocabulary, not observed (Appendix A.5).
_TRUNCATION_REASON = "length"

#: Characters of a raw stream echoed into an error message.
_TAIL_LIMIT = 500

Runner = Callable[..., "subprocess.CompletedProcess[str]"]


class _UnusedSDKClient:
    """Placeholder handed to :class:`AnthropicLLMClient`'s constructor.

    The parent builds a live ``anthropic.Anthropic()`` when ``client is None``,
    which would demand an ``ANTHROPIC_API_KEY`` this provider does not need. Any
    attribute access raises loudly, so a future edit that leaks an SDK call into
    this client fails with an explanation instead of a mystery.
    """

    def __getattr__(self, name: str) -> Any:
        raise AttributeError(
            "OpenCodeLLMClient does not use an Anthropic SDK client (attempted "
            f"access: {name!r}); its transport is the opencode CLI."
        )


_UNUSED_SDK_CLIENT = _UnusedSDKClient()


def _default_runner(argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
    """Spawn ``opencode``. Replaced wholesale in tests, which never spawn."""
    completed: subprocess.CompletedProcess[str] = subprocess.run(argv, **kwargs)
    return completed


class OpenCodeLLMClient(AnthropicLLMClient):
    """:class:`LLMClient` backed by the ``opencode`` CLI.

    Overrides only construction and :meth:`_call_claude`; see the module docstring
    for why that is the whole adapter. ``max_tokens`` is accepted for signature
    parity with its siblings and is **inert** — ``opencode run`` has no flag for
    it (pinned by a test so a future reader does not assume otherwise).

    ``runner`` is the single test seam: it defaults to :func:`_default_runner` and
    is the only thing the deterministic tier replaces, so no test spawns a
    process. ``last_usage`` carries the final step's ``reason`` / ``tokens`` /
    ``cost`` from the most recent call — per-call telemetry the SDK clients do not
    expose (spec Appendix A.4 C3).
    """

    def __init__(
        self,
        model: str | None = DEFAULT_MODEL,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        *,
        executable: str = DEFAULT_EXECUTABLE,
        agent_name: str = DEFAULT_AGENT_NAME,
        workdir: str | None = None,
        timeout: float = DEFAULT_TIMEOUT_S,
        runner: Runner | None = None,
    ) -> None:
        if shutil.which(executable) is None:
            raise LLMParseError(
                f"opencode executable not found on PATH (looked for {executable!r}); "
                "install it (npm i -g opencode-ai) or pass executable=..."
            )
        super().__init__(
            client=_UNUSED_SDK_CLIENT,
            model=model or _NO_MODEL,
            max_tokens=max_tokens,
        )
        self._executable = executable
        self._agent_name = agent_name
        self._workdir = workdir
        self._timeout = timeout
        self._runner: Runner = _default_runner if runner is None else runner
        self._tempdir: tempfile.TemporaryDirectory[str] | None = None
        self._agent_ready = False
        self._version: str | None = None
        self.last_usage: dict[str, Any] | None = None

    # --- transport override ---------------------------------------------

    def _call_claude(self, system: str, user: str) -> str:
        """Run one ``opencode`` invocation and return the assistant's **raw text**.

        Same return contract as the parent — this seam keeps the round-trip and
        the parse apart (each caller runs ``_extract_json`` itself), unlike the
        intake seam which fuses them. That asymmetry is load-bearing; preserving
        it is why the two adapters override differently named methods.
        """
        return self._run(system, user)

    # --- internals -------------------------------------------------------

    def _run(self, system: str, user: str) -> str:
        """Spawn one ``opencode run`` and return the assistant's answer text."""
        prompt = system + SYSTEM_USER_SEPARATOR + user
        try:
            completed = self._runner(
                self._argv(),
                # ``input=`` makes subprocess open a pipe, write the prompt and
                # close it. Passing ``stdin=`` as well is a ValueError — and an
                # *inherited* stdin is the H1 hang (verified: a full 25s timeout
                # with zero output), so this kwarg is load-bearing, not stylistic.
                input=prompt,
                capture_output=True,
                text=True,
                timeout=self._timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise LLMParseError(f"opencode run timed out after {self._timeout}s") from exc
        except OSError as exc:
            raise LLMParseError(f"failed to spawn opencode: {exc}") from exc

        stdout = completed.stdout or ""
        stderr = completed.stderr or ""
        events = _iter_events(stdout)

        # Non-zero exit with nothing parseable on stdout is NOT a provider
        # failure: OpenCode rejected the invocation itself and printed usage help
        # (spec Appendix A.4 C5). The most likely cause is the agent definition
        # this module generates, so it is diagnosed separately — a bug here, not
        # out there.
        if completed.returncode != 0 and not events:
            detail = _tail(stderr) or _tail(stdout) or "(no output)"
            raise LLMParseError(
                f"opencode rejected its invocation (exit {completed.returncode}) and "
                f"emitted no JSON events; this usually means a malformed agent "
                f"definition or an unsupported flag{self._version_suffix()}: {detail}"
            )

        # Every diagnostic arrives on stdout as an ``error`` event — stderr is
        # empty on this path, so the spec's original ``{stderr_tail}`` message
        # would have rendered as "" (Appendix A.4 C2). An ``error`` event with a
        # zero exit is still a failure; do not silently succeed.
        errors = _error_payloads(events)
        if errors:
            raise LLMParseError(
                f"opencode run failed (exit {completed.returncode}): {'; '.join(errors)}"
            )
        if completed.returncode != 0:
            raise LLMParseError(
                f"opencode run failed (exit {completed.returncode}) with no error event; "
                f"stderr: {_tail(stderr) or '(empty)'}"
            )

        self.last_usage = _final_step_summary(events)
        if self.last_usage is not None and self.last_usage.get("reason") == _TRUNCATION_REASON:
            raise LLMParseError(
                f"opencode run stopped with reason={_TRUNCATION_REASON!r}; the response "
                "is incomplete. max_tokens is inert for this provider (opencode run has "
                "no flag for it) — raise the output limit in your OpenCode model config."
            )

        text = _extract_assistant_text(events)
        if not text:
            raise LLMParseError(f"opencode returned no assistant text{self._version_suffix()}")
        return text

    def _argv(self) -> list[str]:
        """Build the argv. The prompt is *never* here — that is hazard H2."""
        argv = [self._executable, "run", "--format", "json"]
        if self._model:
            argv += ["--model", self._model]
        # Always selected: there is no path that runs without the tool denial.
        argv += ["--agent", self._agent_name, "--dir", self._sandbox()]
        return argv

    def _sandbox(self) -> str:
        """Return the sandbox directory, creating it and the agent file once.

        Never per call: writing the agent definition makes OpenCode materialise
        ``.opencode/node_modules`` from npm at runtime (spec Appendix A.4 C6), so
        a per-call sandbox would mean a per-call install.
        """
        if self._workdir is None:
            if self._tempdir is None:
                self._tempdir = tempfile.TemporaryDirectory(prefix="mpc-opencode-")
            self._workdir = self._tempdir.name
        if not self._agent_ready:
            agents_dir = os.path.join(self._workdir, ".opencode", "agents")
            os.makedirs(agents_dir, exist_ok=True)
            agent_file = os.path.join(agents_dir, f"{self._agent_name}.md")
            with open(agent_file, "w", encoding="utf-8") as handle:
                handle.write(AGENT_DEFINITION)
            self._agent_ready = True
        return self._workdir

    def _version_suffix(self) -> str:
        """`` (opencode vX)``, best-effort and cached — "" if it cannot be read.

        A schema break upstream should be one line away from "you are on a version
        we have not validated" (spec §4.5). Deliberately lazy: the happy path
        spawns exactly one process per call.
        """
        if self._version is None:
            try:
                completed = self._runner(
                    [self._executable, "--version"],
                    input="",
                    capture_output=True,
                    text=True,
                    timeout=self._timeout,
                    check=False,
                )
                self._version = (completed.stdout or "").strip().splitlines()[0]
            except Exception:  # diagnostics must never mask the real error
                self._version = ""
        return f" (opencode {self._version})" if self._version else ""

    def close(self) -> None:
        """Remove the ephemeral sandbox. Idempotent; a caller-supplied ``workdir``
        is never deleted. Also runs on garbage collection via
        :class:`tempfile.TemporaryDirectory`'s own finaliser."""
        if self._tempdir is not None:
            self._tempdir.cleanup()
            self._tempdir = None
            self._workdir = None
            self._agent_ready = False


# --- JSONL event helpers (C4-forced twins — see tests/test_llm_json_parity.py) ---
#
# These four functions are duplicated byte-for-byte in the intake agent's
# ``opencode_client.py``. The duplication is FORCED by C4: this standalone wheel
# cannot import the orchestrator, and the package dependency is one-way. The
# ``_extract_json`` twins drifted once and cost three sessions to repair
# (Sessions 98-100), so a parity battery for these lands in the same commit that
# creates them — not later.
#
# Signature note: the spec sketched these as taking raw ``stdout``. They take the
# already-parsed event list instead, so the "skip unparseable lines" rule lives in
# exactly one place (:func:`_iter_events`) and one call parses the stream once.


def _iter_events(stdout: str) -> list[dict[str, Any]]:
    """Parse the JSONL event stream, **skipping** lines that are not JSON objects.

    ``opencode`` writes some human-readable output to stdout before the event
    stream starts (early ``UI.error`` / ``die`` paths), so an unparseable line is
    expected, not fatal; the exit code is the authority on success.
    """
    events: list[dict[str, Any]] = []
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(event, dict):
            events.append(event)
    return events


def _extract_assistant_text(events: list[dict[str, Any]]) -> str:
    """Return the assistant's answer: the text of the final step that stopped.

    Naive concatenation of every ``text`` event is what the spec originally
    prescribed and it is **wrong once tools fire** — an observed 3-step run
    emitted "I'll list the files…", "Now let me read…" and only then the answer
    (spec Appendix A.4 C4). Steps are delimited by ``step_start`` / ``step_finish``
    and the closing part carries a ``reason``, so the answer is the text of the
    last step whose reason is ``"stop"``. Tool denial should keep runs single-step
    anyway; this is the belt to that suspenders. Falls back to concatenating
    everything when no step closed cleanly (a stream with no ``step_finish`` at
    all still yields its text). Returns "" when there is no text — the caller
    turns that into the seam's error.
    """
    steps: list[tuple[list[str], str | None]] = []
    current: list[str] = []
    for event in events:
        event_type = event.get("type")
        part = event.get("part")
        if event_type == "text" and isinstance(part, dict):
            text = part.get("text")
            if isinstance(text, str):
                current.append(text)
        elif event_type == "step_finish":
            reason = part.get("reason") if isinstance(part, dict) else None
            steps.append((current, reason if isinstance(reason, str) else None))
            current = []
    if current:
        steps.append((current, None))
    for texts, reason in reversed(steps):
        if reason == "stop" and texts:
            return "".join(texts)
    return "".join(text for texts, _ in steps for text in texts)


def _error_payloads(events: list[dict[str, Any]]) -> list[str]:
    """Summarise every ``error`` event as ``name: message (ref=…)``.

    The ``ref`` is included because the observed payload is otherwise generic
    ("Unexpected server error"), making it the only distinguishing detail (spec
    Appendix A.4 C2).
    """
    payloads: list[str] = []
    for event in events:
        if event.get("type") != "error":
            continue
        error = event.get("error")
        if not isinstance(error, dict):
            payloads.append(str(error))
            continue
        data = error.get("data")
        data = data if isinstance(data, dict) else {}
        summary = str(error.get("name") or "error")
        message = data.get("message")
        if message:
            summary = f"{summary}: {message}"
        ref = data.get("ref")
        if ref:
            summary = f"{summary} (ref={ref})"
        payloads.append(summary)
    return payloads


def _final_step_summary(events: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Return the last ``step_finish``'s ``reason`` / ``tokens`` / ``cost``.

    ``reason`` is the truncation guard's analogue of the SDK's ``stop_reason``;
    ``tokens`` and ``cost`` are per-call telemetry the SDK clients do not expose
    (spec Appendix A.4 C3). ``None`` when the stream carried no ``step_finish``.
    """
    summary: dict[str, Any] | None = None
    for event in events:
        if event.get("type") != "step_finish":
            continue
        part = event.get("part")
        if not isinstance(part, dict):
            continue
        summary = {
            "reason": part.get("reason"),
            "tokens": part.get("tokens"),
            "cost": part.get("cost"),
        }
    return summary


def _tail(stream: str, limit: int = _TAIL_LIMIT) -> str:
    """Last ``limit`` characters of a raw stream, ANSI-stripped, for error text."""
    return _ANSI.sub("", stream).strip()[-limit:]
