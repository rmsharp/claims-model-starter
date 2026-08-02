"""Deterministic tests for :class:`OpenCodeLLMClient` (intake agent).

**No test here spawns a process.** The client's ``runner`` seam is replaced with
:class:`_FakeRunner`, and every JSONL sample is a **verbatim capture** committed by
spec Phase 1 under ``tests/fixtures/opencode/`` (see that directory's README for
provenance: ``opencode`` v1.18.11, real ``anthropic/claude-haiku-4-5`` runs).
Hand-written fixtures would test the specification rather than OpenCode, which is
exactly the failure the captures exist to prevent.

Scope: the OpenCode-specific surface only — argv construction, the stdin
discipline, event-stream extraction, the error-mapping table (spec §4.7 as
amended by Appendix A.4) and the sandbox/agent-definition safety controls. Every
prompt, the interview methods and ``_extract_json`` are *inherited* from
:class:`AnthropicLLMClient` and are already covered by ``test_anthropic_client.py``
and the cross-provider ``tests/test_llm_json_parity.py`` battery.

**On the safety property.** Spec Appendix A.4 C1 established — live — that
OpenCode's permission default does **not** refuse file reads, and that the
tool-denying agent definition *does*. That live refusal cannot be re-verified
hermetically, so what is pinned here is the part this module actually controls:
the definition denies every tool, it is written into the sandbox, ``--agent``
always selects it, and no constructor path skips it.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from model_project_constructor.agents.intake.anthropic_client import AnthropicLLMClient
from model_project_constructor.agents.intake.opencode_client import (
    AGENT_DEFINITION,
    DEFAULT_AGENT_NAME,
    DEFAULT_MODEL,
    SYSTEM_USER_SEPARATOR,
    OpenCodeLLMClient,
    _extract_assistant_text,
    _iter_events,
)
from model_project_constructor.agents.intake.protocol import IntakeLLMError

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "opencode"


def _fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


class _FakeRunner:
    """Stands in for ``subprocess.run``; records calls, spawns nothing.

    ``--version`` probes are answered separately because the client fires one
    lazily when building certain diagnostics (spec §4.5).
    """

    def __init__(
        self,
        stdout: str = "",
        stderr: str = "",
        returncode: int = 0,
        version: str | None = "1.18.11",
        raises: BaseException | None = None,
    ) -> None:
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode
        self.version = version
        self.raises = raises
        self.calls: list[tuple[list[str], dict[str, Any]]] = []

    def __call__(self, argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        self.calls.append((argv, kwargs))
        if "--version" in argv:
            if self.version is None:
                raise OSError("version probe exploded")
            return subprocess.CompletedProcess(argv, 0, self.version, "")
        if self.raises is not None:
            raise self.raises
        return subprocess.CompletedProcess(argv, self.returncode, self.stdout, self.stderr)

    @property
    def run_calls(self) -> list[tuple[list[str], dict[str, Any]]]:
        """Calls that were real runs, i.e. excluding ``--version`` probes."""
        return [call for call in self.calls if "--version" not in call[0]]


def _client(runner: _FakeRunner, **overrides: Any) -> OpenCodeLLMClient:
    """Build a client whose executable resolves without installing anything.

    ``sys.executable`` is guaranteed to exist and be executable, so the
    construction-time ``shutil.which`` check passes on any machine — including CI,
    where ``opencode`` is deliberately not installed (hermeticity, spec §4.5).
    """
    return OpenCodeLLMClient(executable=sys.executable, runner=runner, **overrides)


# --- §7.1.1 argv construction --------------------------------------------


def test_argv_requests_json_format() -> None:
    runner = _FakeRunner(stdout=_fixture("success_single_step.jsonl"))
    _client(runner)._call_json("sys", "user")
    argv = runner.run_calls[0][0]
    assert argv[1] == "run"
    assert "--format" in argv
    assert argv[argv.index("--format") + 1] == "json"


def test_argv_never_contains_auto() -> None:
    """Hazard H4 as an executable assertion.

    ``--auto`` (aliases ``--yolo`` / ``--dangerously-skip-permissions``)
    auto-approves tool permissions; its own help string says "(dangerous!)". This
    is a safety property, not a detail — it gets its own test so a future
    "convenience" flag addition trips here.
    """
    runner = _FakeRunner(stdout=_fixture("success_single_step.jsonl"))
    _client(runner)._call_json("sys", "user")
    argv = runner.run_calls[0][0]
    for forbidden in ("--auto", "--yolo", "--dangerously-skip-permissions"):
        assert forbidden not in argv


def test_argv_sandbox_is_outside_the_repository() -> None:
    """Hazard H3: ``--dir`` must not point at the working tree."""
    runner = _FakeRunner(stdout=_fixture("success_single_step.jsonl"))
    _client(runner)._call_json("sys", "user")
    argv = runner.run_calls[0][0]
    assert "--dir" in argv
    sandbox = Path(argv[argv.index("--dir") + 1]).resolve()
    repo_root = Path(__file__).resolve().parents[3]
    assert repo_root not in sandbox.parents
    assert sandbox != repo_root


def test_argv_omits_model_when_none_is_configured() -> None:
    """Spec D6: ``DEFAULT_MODEL is None`` means "let the operator's OpenCode
    config choose the vendor" — so no ``--model`` flag at all."""
    runner = _FakeRunner(stdout=_fixture("success_single_step.jsonl"))
    _client(runner)._call_json("sys", "user")
    assert "--model" not in runner.run_calls[0][0]


def test_argv_includes_model_when_configured() -> None:
    runner = _FakeRunner(stdout=_fixture("success_single_step.jsonl"))
    _client(runner, model="anthropic/claude-haiku-4-5")._call_json("sys", "user")
    argv = runner.run_calls[0][0]
    assert argv[argv.index("--model") + 1] == "anthropic/claude-haiku-4-5"


def test_argv_always_selects_the_locked_down_agent() -> None:
    runner = _FakeRunner(stdout=_fixture("success_single_step.jsonl"))
    _client(runner)._call_json("sys", "user")
    argv = runner.run_calls[0][0]
    assert argv[argv.index("--agent") + 1] == DEFAULT_AGENT_NAME


# --- §7.1.2/3 the stdin discipline ---------------------------------------


def test_prompt_goes_on_stdin_not_argv() -> None:
    """Hazard H2: interview transcripts may carry PII, and anything in ``argv`` is
    world-readable via ``ps``."""
    runner = _FakeRunner(stdout=_fixture("success_single_step.jsonl"))
    _client(runner)._call_json("SYSTEM-SECRET", "USER-SECRET")
    argv, kwargs = runner.run_calls[0]
    assert kwargs["input"] == "SYSTEM-SECRET" + SYSTEM_USER_SEPARATOR + "USER-SECRET"
    joined = " ".join(argv)
    assert "SYSTEM-SECRET" not in joined
    assert "USER-SECRET" not in joined


def test_stdin_is_never_inherited() -> None:
    """Hazard H1: an inherited, never-closed stdin hangs ``opencode`` for the full
    timeout with zero output (verified live in spec Phase 1).

    ``input=`` is what closes it — subprocess opens a pipe, writes and closes.
    Passing ``stdin=`` *as well* would be a ``ValueError``, so the correct
    assertion is that ``input`` is present and ``stdin`` is absent.
    """
    runner = _FakeRunner(stdout=_fixture("success_single_step.jsonl"))
    _client(runner)._call_json("sys", "user")
    kwargs = runner.run_calls[0][1]
    assert "input" in kwargs
    assert "stdin" not in kwargs


def test_a_timeout_is_always_passed() -> None:
    runner = _FakeRunner(stdout=_fixture("success_single_step.jsonl"))
    _client(runner, timeout=12.5)._call_json("sys", "user")
    assert runner.run_calls[0][1]["timeout"] == 12.5


# --- §7.1.4/5 happy paths over verbatim captures --------------------------


def test_happy_path_returns_parsed_json() -> None:
    runner = _FakeRunner(stdout=_fixture("success_single_step.jsonl"))
    assert _client(runner)._call_json("sys", "user") == {"ok": True}


def test_happy_path_under_the_shipped_agent_definition() -> None:
    """The capture taken with the locked-down agent in place — i.e. the
    configuration this adapter actually ships."""
    runner = _FakeRunner(stdout=_fixture("success_with_agent.jsonl"))
    assert _client(runner)._call_json("sys", "user") == {"ok": True}


def test_realistic_intake_payload_parses_with_the_inherited_parser() -> None:
    """Spec Appendix A.3: the real ``next_question`` payload, folded per D2, run
    live, parses to exactly the two keys the inherited ``next_question`` reads."""
    runner = _FakeRunner(stdout=_fixture("success_realistic_intake.jsonl"))
    parsed = _client(runner)._call_json("sys", "user")
    assert set(parsed) == {"question", "believe_enough_info"}
    assert isinstance(parsed["question"], str)


def test_non_json_preamble_is_skipped() -> None:
    """``opencode`` writes human-readable output to stdout before the event stream
    on some paths, so the parser skips unparseable lines instead of failing on
    them; the exit code is the authority on success."""
    stdout = "Loading configuration...\n\n" + _fixture("success_single_step.jsonl")
    runner = _FakeRunner(stdout=stdout)
    assert _client(runner)._call_json("sys", "user") == {"ok": True}


def test_multistep_run_returns_the_answer_not_the_narration() -> None:
    """Spec Appendix A.4 C4. This capture is a real 3-step agentic run whose first
    two ``text`` events are narration ("I'll list the files…", "Now let me read…").
    Naive concatenation — what the spec originally prescribed — would return all
    three glued together. The answer is the text of the final step, the one whose
    ``step_finish.reason`` is ``"stop"``.
    """
    text = _extract_assistant_text(_iter_events(_fixture("multistep_tool_use.jsonl")))
    assert text.startswith("The directory contains")
    assert "I'll list the files" not in text
    assert "Now let me read" not in text


def test_text_without_step_finish_still_extracts() -> None:
    """Fallback path: a stream that never closes a step still yields its text."""
    events = _iter_events(
        json.dumps({"type": "text", "part": {"type": "text", "text": '{"a": 1}'}})
    )
    assert _extract_assistant_text(events) == '{"a": 1}'


def test_per_call_telemetry_is_surfaced() -> None:
    """Spec Appendix A.4 C3: ``step_finish`` carries ``reason``/``tokens``/``cost``
    — per-call telemetry the SDK clients do not expose. Phase 4 needs it to report
    cost per interview alongside quality (risk #12)."""
    runner = _FakeRunner(stdout=_fixture("success_with_agent.jsonl"))
    client = _client(runner)
    client._call_json("sys", "user")
    assert client.last_usage is not None
    assert client.last_usage["reason"] == "stop"
    assert client.last_usage["tokens"]["cache"]["write"] == 4837
    assert client.last_usage["cost"] == pytest.approx(0.00611425)


# --- §7.1.6 the error-mapping table (spec §4.7 as amended) ----------------


def test_missing_binary_fails_at_construction() -> None:
    """Fail fast, with an install hint — not mid-interview (spec §4.5)."""
    with pytest.raises(IntakeLLMError) as exc:
        OpenCodeLLMClient(executable="opencode-definitely-not-installed-xyz")
    assert "not found on PATH" in str(exc.value)
    assert "npm i -g opencode-ai" in str(exc.value)


def test_timeout_maps_to_the_seam_error() -> None:
    runner = _FakeRunner(raises=subprocess.TimeoutExpired(cmd="opencode", timeout=7.0))
    with pytest.raises(IntakeLLMError) as exc:
        _client(runner, timeout=7.0)._call_json("sys", "user")
    assert str(exc.value) == "opencode run timed out after 7.0s"
    assert isinstance(exc.value.__cause__, subprocess.TimeoutExpired)


def test_spawn_failure_maps_to_the_seam_error() -> None:
    runner = _FakeRunner(raises=OSError("Exec format error"))
    with pytest.raises(IntakeLLMError) as exc:
        _client(runner)._call_json("sys", "user")
    assert str(exc.value) == "failed to spawn opencode: Exec format error"


def test_error_event_reports_name_message_and_ref() -> None:
    """Spec Appendix A.4 C2: stderr is EMPTY on this path, so the message must be
    built from the stdout ``error`` event. The payload is generic ("Unexpected
    server error"), which makes ``ref`` the only distinguishing detail."""
    runner = _FakeRunner(stdout=_fixture("error_invalid_model.jsonl"), returncode=1)
    with pytest.raises(IntakeLLMError) as exc:
        _client(runner)._call_json("sys", "user")
    message = str(exc.value)
    assert "UnknownError" in message
    assert "Unexpected server error" in message
    assert "ref=err_d5066603" in message


def test_error_event_with_exit_zero_still_fails() -> None:
    """Do not silently succeed just because the process exited 0."""
    runner = _FakeRunner(stdout=_fixture("error_invalid_model.jsonl"), returncode=0)
    with pytest.raises(IntakeLLMError):
        _client(runner)._call_json("sys", "user")


def test_nonzero_exit_without_json_events_is_diagnosed_as_our_own_bug() -> None:
    """Spec Appendix A.4 C5. A malformed agent definition makes ``opencode`` print
    usage help and emit nothing parseable. Since *this module generates* that
    file, the failure is a bug here rather than a provider fault, so it is
    diagnosed distinctly — and the fixture proves such output really does reach
    stdout (ANSI-coloured), not only stderr.
    """
    runner = _FakeRunner(stdout=_fixture("usage_error_nonjson_stdout.txt"), returncode=1)
    with pytest.raises(IntakeLLMError) as exc:
        _client(runner)._call_json("sys", "user")
    message = str(exc.value)
    assert "rejected its invocation" in message
    assert "malformed agent definition" in message
    assert "You must provide a message" in message
    assert "\x1b[" not in message  # ANSI stripped so logs stay readable


def test_invocation_error_names_the_binary_version() -> None:
    """A schema break upstream should be one line from "you are on a version we
    have not validated" (spec §4.5). OpenCode ships releases daily."""
    runner = _FakeRunner(stdout="", returncode=1, version="1.99.0")
    with pytest.raises(IntakeLLMError) as exc:
        _client(runner)._call_json("sys", "user")
    assert "opencode 1.99.0" in str(exc.value)


def test_a_failing_version_probe_does_not_mask_the_real_error() -> None:
    """The version lookup is a diagnostic nicety. If it throws — the binary
    vanished mid-run, the machine is out of file descriptors — the caller must
    still receive the failure that actually happened, not the probe's."""
    runner = _FakeRunner(stdout="", returncode=1, version=None)
    with pytest.raises(IntakeLLMError) as exc:
        _client(runner)._call_json("sys", "user")
    assert "rejected its invocation" in str(exc.value)
    assert "(opencode" not in str(exc.value)  # the version suffix is simply omitted


def test_nonzero_exit_with_events_but_no_error_event() -> None:
    runner = _FakeRunner(stdout=_fixture("success_single_step.jsonl"), returncode=1)
    with pytest.raises(IntakeLLMError) as exc:
        _client(runner)._call_json("sys", "user")
    assert "no error event" in str(exc.value)


def test_no_text_events_is_the_empty_content_analogue() -> None:
    """The structural replacement for the inherited "empty content list" guard —
    which is SDK-response-shaped and has no OpenCode equivalent (spec §2.3)."""
    runner = _FakeRunner(stdout=json.dumps({"type": "step_start", "part": {}}))
    with pytest.raises(IntakeLLMError) as exc:
        _client(runner)._call_json("sys", "user")
    assert "no assistant text" in str(exc.value)


def test_truncation_is_detected_via_step_finish_reason() -> None:
    """Spec Appendix A.4 C3 restores the truncation guard §3.3 declared impossible.

    ``max_tokens`` is inert for this provider, so the message must NOT tell the
    caller to raise it — that would send them somewhere with no effect.
    (The ``"length"`` spelling is inferred from the AI SDK's finish-reason
    vocabulary; Phase 1 never forced a truncation — spec Appendix A.5.)
    """
    stdout = "\n".join(
        [
            json.dumps({"type": "text", "part": {"type": "text", "text": '{"a": 1'}}),
            json.dumps({"type": "step_finish", "part": {"reason": "length"}}),
        ]
    )
    runner = _FakeRunner(stdout=stdout)
    with pytest.raises(IntakeLLMError) as exc:
        _client(runner)._call_json("sys", "user")
    message = str(exc.value)
    assert "reason='length'" in message
    assert "max_tokens is inert" in message
    assert "Raise max_tokens" not in message


def test_malformed_assistant_json_raises_through_the_inherited_parser() -> None:
    """The last row of the error table is *inherited*, not reimplemented."""
    stdout = "\n".join(
        [
            json.dumps({"type": "text", "part": {"type": "text", "text": "not json"}}),
            json.dumps({"type": "step_finish", "part": {"reason": "stop"}}),
        ]
    )
    runner = _FakeRunner(stdout=stdout)
    with pytest.raises(IntakeLLMError) as exc:
        _client(runner)._call_json("sys", "user")
    assert "non-JSON" in str(exc.value)


# --- §7.1.7/8 structural properties --------------------------------------


def test_is_subclass_of_anthropic_client() -> None:
    """Spec D1: the transport is overridden, everything else is inherited — which
    is what makes prompt drift across providers structurally impossible."""
    assert issubclass(OpenCodeLLMClient, AnthropicLLMClient)


def test_inherited_interview_method_runs_over_the_cli() -> None:
    """End-to-end through an *inherited* method: the prompt is built by
    :class:`AnthropicLLMClient`, the round trip is OpenCode's."""
    from model_project_constructor.agents.intake.protocol import InterviewContext

    runner = _FakeRunner(stdout=_fixture("success_realistic_intake.jsonl"))
    result = _client(runner).next_question(
        InterviewContext(
            stakeholder_id="s",
            session_id="sess",
            domain="pc_claims",
            initial_problem="Subrogation recovery is down.",
            qa_pairs=[{"question": "Q1", "answer": "A1"}],
            questions_asked=1,
        )
    )
    assert result.question
    assert result.believe_enough_info is False


def test_no_anthropic_sdk_client_is_constructed() -> None:
    """The parent builds a live ``anthropic.Anthropic()`` when ``client is None``,
    which would demand an ``ANTHROPIC_API_KEY`` this provider does not need. The
    placeholder raises loudly if anything ever reaches for it."""
    client = _client(_FakeRunner())
    with pytest.raises(AttributeError) as exc:
        client._client.messages.create()
    assert "does not use an Anthropic SDK client" in str(exc.value)


def test_module_imports_no_third_party_package() -> None:
    """Spec D5: this adapter adds **no Python dependency** — its own imports are
    stdlib plus its own package. That is what keeps ``pyproject.toml`` unchanged,
    and it is a genuine advantage over every SDK-based provider (the
    ``anthropic[bedrock]`` extra dragged ``boto3``/``botocore`` into every
    install).

    **What this does NOT claim:** that constructing the client loads no SDK. It
    does — the base class it inherits imports ``anthropic.types.TextBlock`` at
    module level, so ``anthropic`` still reaches ``sys.modules``. The property
    guarded here is what *this file* requires, which is the claim D5 actually
    makes. An earlier draft of this test asserted the stronger thing and failed;
    the assertion was wrong, not the code.
    """
    import ast
    import sys as _sys

    source = Path(__file__).resolve().parents[3] / (
        "src/model_project_constructor/agents/intake/opencode_client.py"
    )
    roots: set[str] = set()
    for node in ast.walk(ast.parse(source.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            roots.add(node.module.split(".")[0])
    third_party = {
        root
        for root in roots
        if root not in _sys.stdlib_module_names and root != "model_project_constructor"
    }
    assert third_party == set()


def test_default_model_is_none_and_stored_as_empty() -> None:
    """Spec D6. ``_model`` is typed ``str`` by the parent, so "unset" is ``""``."""
    assert DEFAULT_MODEL is None
    assert _client(_FakeRunner())._model == ""


def test_max_tokens_is_inert() -> None:
    """Pinned so a future reader does not assume it is honoured: ``opencode run``
    has no flag for it, and the value never reaches the argv."""
    runner = _FakeRunner(stdout=_fixture("success_single_step.jsonl"))
    client = _client(runner, max_tokens=1234)
    client._call_json("sys", "user")
    assert client._max_tokens == 1234
    assert "1234" not in " ".join(runner.run_calls[0][0])


def test_happy_path_spawns_exactly_one_process() -> None:
    """The version probe is lazy — it must not double the cost of every call."""
    runner = _FakeRunner(stdout=_fixture("success_single_step.jsonl"))
    _client(runner)._call_json("sys", "user")
    assert len(runner.calls) == 1


# --- the safety controls (spec Appendix A.4 C1) ---------------------------


def test_agent_definition_denies_every_tool() -> None:
    """The definition is a SAFETY control, not a nicety. Phase 1 proved live that
    without ``read: deny`` the agent reads files and discloses their contents,
    exit 0, with no ``--auto``."""
    for tool in ("edit", "write", "bash", "read", "webfetch"):
        assert f"  {tool}: deny" in AGENT_DEFINITION


def test_agent_definition_is_block_style_yaml() -> None:
    """Flow-style (``permission: {edit: deny, …}``) silently breaks agent loading
    and surfaces as usage-help-on-stderr with empty stdout (spec Appendix A.4 C5).
    This module *generates* the file, so that would be our bug."""
    assert "permission:\n  edit: deny\n" in AGENT_DEFINITION
    assert "{" not in AGENT_DEFINITION


def test_agent_definition_is_written_into_the_sandbox(tmp_path: Path) -> None:
    runner = _FakeRunner(stdout=_fixture("success_single_step.jsonl"))
    _client(runner, workdir=str(tmp_path))._call_json("sys", "user")
    written = tmp_path / ".opencode" / "agents" / f"{DEFAULT_AGENT_NAME}.md"
    assert written.read_text(encoding="utf-8") == AGENT_DEFINITION


def test_the_tool_denial_cannot_be_switched_off() -> None:
    """Spec §4.4's "caller supplied an agent ⇒ the adapter writes nothing" escape
    hatch was REMOVED as unsafe (Appendix A.4 C1): the tool denial is the only
    thing preventing file reads. ``agent_name`` renames the generated definition;
    it does not substitute a caller-owned one, so there is no path to an
    unlocked agent.
    """
    import inspect

    signature = inspect.signature(OpenCodeLLMClient.__init__)
    assert "agent" not in signature.parameters
    assert "agent_name" in signature.parameters


def test_renaming_the_agent_still_writes_and_selects_it(tmp_path: Path) -> None:
    runner = _FakeRunner(stdout=_fixture("success_single_step.jsonl"))
    client = _client(runner, workdir=str(tmp_path), agent_name="custom-name")
    client._call_json("sys", "user")
    argv = runner.run_calls[0][0]
    assert argv[argv.index("--agent") + 1] == "custom-name"
    assert (tmp_path / ".opencode" / "agents" / "custom-name.md").exists()


def test_the_sandbox_is_created_once_not_per_call(tmp_path: Path) -> None:
    """Spec Appendix A.4 C6: writing the agent definition makes OpenCode
    materialise ``.opencode/node_modules`` from npm at runtime, so a per-call
    sandbox would mean a per-call install (and a runtime npm dependency per
    call)."""
    runner = _FakeRunner(stdout=_fixture("success_single_step.jsonl"))
    client = _client(runner)
    client._call_json("sys", "user")
    client._call_json("sys", "user")
    first, second = (call[0] for call in runner.run_calls)
    assert first[first.index("--dir") + 1] == second[second.index("--dir") + 1]


def test_close_removes_the_ephemeral_sandbox() -> None:
    runner = _FakeRunner(stdout=_fixture("success_single_step.jsonl"))
    client = _client(runner)
    client._call_json("sys", "user")
    sandbox = Path(runner.run_calls[0][0][-1])
    assert sandbox.exists()
    client.close()
    assert not sandbox.exists()
    client.close()  # idempotent


def test_close_does_not_delete_a_caller_supplied_workdir(tmp_path: Path) -> None:
    runner = _FakeRunner(stdout=_fixture("success_single_step.jsonl"))
    client = _client(runner, workdir=str(tmp_path))
    client._call_json("sys", "user")
    client.close()
    assert tmp_path.exists()
