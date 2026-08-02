"""Behavioral-parity guard for the two ``_extract_json`` LLM-JSON parsers.

**Why two copies exist (do NOT "fix" this by merging).** The intake agent
(``src/model_project_constructor/agents/intake/anthropic_client.py``) and the
data agent
(``packages/data-agent/src/model_project_constructor_data_agent/anthropic_client.py``)
each carry their own ``_extract_json`` + ``_CODE_FENCE`` + content/parse guards.
They are deliberately separate because the data agent ships as a *standalone,
decoupled wheel* — constraint **C4** (``architecture-plan.md:36``, "reusable as
a standalone query tool for analysts"), enforced by
``tests/test_data_agent_decoupling.py`` ("the single most important structural
guarantee"). The package dependency is one-way (root → data-agent), so a shared
helper could not live in the orchestrator and be imported by the standalone
wheel without inverting that dependency. O2 (``docs/planning/o2-shared-llm-json-plan.md``)
evaluated consolidation and **chose not to merge** — see §3/§4 there.

**Why this test exists.** The two parsers are byte-identical *modulo the raised
error class* — but they have drifted before. The intake copy was a stale
pre-hardening version whose anchored ``^…$`` regex crashed on prose-wrapped
fences (Session 51 live run ``run_id=run_b1_resume_live_1776570556``); it was
only hardened in #16/#16b/#16c (Sessions 98/99/100), three sessions of
latent-bug remediation traceable to the twins silently diverging. This test is
the drift guard: it converts a future divergence from a latent live-LLM crash
into a deterministic CI failure on the offending commit. It pins three things:

  * §5.1 parse parity — an identical input battery (incl. the Session-51
    prose-wrapped-fence cases) parses identically in both copies;
  * §5.2 raise parity — malformed input is rejected by both, *each with its own
    error type*; the ``IntakeLLMError`` (RuntimeError) vs ``LLMParseError``
    (ValueError) divergence is INTENTIONAL and load-bearing (plan §2.3) and is
    asserted as such, not unified;
  * §5.3 guard-message parity — the empty-content and non-``TextBlock`` guards
    raise the same message text (modulo error class).

The plan's §5.4 *source-identity backstop* (an AST comparison of the two parser
bodies) was implemented and verified, then dropped: an AST-identity assertion
trips on a benign one-sided reformat of the twins (e.g. renaming a local in one
copy) even when behaviour is unchanged — the brittleness the plan flagged when
it marked §5.4 optional and named behavioural parity the robust core. The
battery above catches the drift class that actually caused bugs (the Session-51
prose-fence crash), so the marginal detection of an AST check did not justify a
false-failure-on-cosmetic-edit risk for a 14-line function.

The test imports the private ``_extract_json`` from both packages. That is legal
in the test tree (``pyproject.toml`` puts both ``src`` roots on the pytest
``pythonpath``) and does NOT run in either package's runtime, so it does not add
a package-source import and cannot affect the decoupling guarantee.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import pytest
from anthropic.types import TextBlock
from model_project_constructor_data_agent import anthropic_client as da_client
from model_project_constructor_data_agent import opencode_client as da_opencode
from model_project_constructor_data_agent.anthropic_client import LLMParseError

from model_project_constructor.agents.intake import anthropic_client as intake_client
from model_project_constructor.agents.intake import opencode_client as intake_opencode
from model_project_constructor.agents.intake.protocol import IntakeLLMError

# The two parsers under test — the same private helper, one per package. The
# whole point of this file is that ``intake_client._extract_json`` and
# ``da_client._extract_json`` behave identically (modulo the raised error class).

# --- fakes for the guard-message tests (§5.3) ----------------------------
#
# Both production clients call ``self._client.messages.create(...)`` and then
# read ``response.content``; nothing else of the SDK surface is touched by the
# guards under test. A response object exposing ``.content`` is therefore a
# sufficient fake for both ``_call_json`` (intake) and ``_call_claude``
# (data agent).


@dataclass
class _FakeResponse:
    content: list[Any]
    # Mirrors the real ``anthropic.types.Message.stop_reason``. Defaults to
    # ``None`` so the content/parse-guard tests below stay byte-identical; the
    # max_tokens-truncation guard (Session 167) sets it to ``"max_tokens"``.
    stop_reason: str | None = None


class _FakeMessages:
    def __init__(self, content: list[Any], stop_reason: str | None = None) -> None:
        self._content = content
        self._stop_reason = stop_reason
        self.calls: list[dict[str, Any]] = []

    def create(self, **kwargs: Any) -> _FakeResponse:
        self.calls.append(kwargs)
        return _FakeResponse(content=self._content, stop_reason=self._stop_reason)


class _FakeAnthropic:
    def __init__(self, content: list[Any], stop_reason: str | None = None) -> None:
        self.messages = _FakeMessages(content, stop_reason)


class _NotATextBlock:
    """A non-``TextBlock`` first content block, to trip the type guard."""


def _client_pair(
    content: list[Any],
    stop_reason: str | None = None,
) -> tuple[intake_client.AnthropicLLMClient, da_client.AnthropicLLMClient]:
    """Build one intake + one data-agent client, each over a fake returning
    ``content`` as ``response.content`` and ``stop_reason`` as
    ``response.stop_reason``."""
    return (
        intake_client.AnthropicLLMClient(client=_FakeAnthropic(content, stop_reason)),
        da_client.AnthropicLLMClient(client=_FakeAnthropic(content, stop_reason)),
    )


# --- provider registry (the cross-PROVIDER extension point) --------------
#
# Each seam carries its OWN ``_extract_json`` copy and its OWN error class
# (constraint C4 — see the module docstring); today both seams run a single
# provider (``anthropic``). Phase C of the multi-provider LLM plan
# (``docs/architecture-history/multi-provider-llm-plan.md`` §5) adds a second provider by
# appending one ``_Seam`` row per ``(seam, provider)`` — e.g.
# ``_Seam("intake", "bedrock", intake_bedrock._extract_json, IntakeLLMError)`` —
# after which the parity battery below asserts every provider's parser agrees on
# the same inputs and raises its seam's error class. No test-body edits needed:
# the parity notion generalises from "the two copies" to "every registered
# (seam, provider) parser".


@dataclass(frozen=True)
class _Seam:
    seam: str  # 'intake' | 'data_agent'
    provider: str  # 'anthropic' (Phase C adds more)
    extract_json: Callable[[str], Any]
    error_cls: type[Exception]

    @property
    def label(self) -> str:
        return f"{self.seam}:{self.provider}"


_SEAMS: list[_Seam] = [
    _Seam("intake", "anthropic", intake_client._extract_json, IntakeLLMError),
    _Seam("data_agent", "anthropic", da_client._extract_json, LLMParseError),
    # Phase C — AWS Bedrock-hosted Claude. ``BedrockLLMClient`` *subclasses* each
    # package's ``AnthropicLLMClient`` (the SDK's ``AnthropicBedrockMantle`` is a
    # drop-in with an identical Messages API), so it reuses that package's
    # ``_extract_json`` and seam error class — there is no separate parser copy
    # to drift. These rows document the (seam, provider) matrix and pin that the
    # Bedrock provider parses + raises through its seam's error class.
    _Seam("intake", "bedrock", intake_client._extract_json, IntakeLLMError),
    _Seam("data_agent", "bedrock", da_client._extract_json, LLMParseError),
    # AD-11 — the ``opencode`` CLI. ``OpenCodeLLMClient`` also *subclasses* each
    # package's ``AnthropicLLMClient``, overriding only the transport method, so it
    # too reuses that package's ``_extract_json`` and seam error class — there is
    # no third parser copy to drift. What this provider DOES add is a new twin
    # pair (the JSONL event helpers), guarded by the separate battery below.
    _Seam("intake", "opencode", intake_client._extract_json, IntakeLLMError),
    _Seam("data_agent", "opencode", da_client._extract_json, LLMParseError),
]


# --- §5.1 parse parity ---------------------------------------------------

PARSE_CASES: list[tuple[str, Any]] = [
    # bare JSON (fast path) — no fence
    ('{"a": 1}', {"a": 1}),
    ('  {"a": 1}  ', {"a": 1}),
    ("[1, 2, 3]", [1, 2, 3]),
    # fenced, no surrounding prose
    ('```json\n{"a": 1}\n```', {"a": 1}),
    ('```\n{"a": 1}\n```', {"a": 1}),
    # prose around the fence — the historically divergent cases (Session 51,
    # run_id=run_b1_resume_live_1776570556): the stale intake regex anchored
    # ^...$ and crashed on these until #16 (Session 98).
    ('Here is the JSON:\n```json\n{"a": 1}\n```', {"a": 1}),  # prose-before
    (
        '```json\n[{"k": "v"}]\n```\n\nExplanation: the array holds one item.',
        [{"k": "v"}],
    ),  # prose-after
    (
        'Response below:\n```json\n{"x": [1, 2]}\n```\nLet me know if...',
        {"x": [1, 2]},
    ),  # prose-both
    ('Sure, here you go:\n```\n{"ok": true}\n```', {"ok": True}),  # plain fence + prose
]


@pytest.mark.parametrize(("raw", "expected"), PARSE_CASES)
def test_parse_parity(raw: str, expected: Any) -> None:
    """An identical input parses to an identical result in every registered
    seam/provider parser (and to the pinned expected value). Equality to a single
    expected value across all parsers is what makes them mutually consistent."""
    for seam in _SEAMS:
        result = seam.extract_json(raw)
        assert result == expected, f"{seam.label} parsed {result!r}, expected {expected!r}"


# --- §5.2 raise parity ---------------------------------------------------

RAISE_CASES: list[str] = [
    "this is not json",
    "```json\nnot valid json\n```",  # fence found, body unparseable
    "",  # empty response
]


@pytest.mark.parametrize("raw", RAISE_CASES)
def test_raise_parity(raw: str) -> None:
    """Malformed input is rejected by every registered parser, *each raising its
    OWN seam error type* — the intentional ``IntakeLLMError`` vs ``LLMParseError``
    divergence is preserved — and the messages are identical across parsers
    modulo that class.

    Each seam's error class lives in a disjoint hierarchy, so its
    ``pytest.raises(seam.error_cls)`` guard would FAIL if that parser ever
    started raising another seam's type.
    """
    messages: list[str] = []
    for seam in _SEAMS:
        with pytest.raises(seam.error_cls) as exc:
            seam.extract_json(raw)
        messages.append(str(exc.value))
    assert len(set(messages)) == 1, f"parser messages diverged: {messages}"


# --- §5.3 guard-message parity -------------------------------------------


def test_guard_empty_content_message_parity() -> None:
    """An empty ``response.content`` list raises the same message (modulo error
    class) from both ``_call_json`` and ``_call_claude`` (#16c)."""
    intake, da = _client_pair([])
    with pytest.raises(IntakeLLMError) as intake_exc:
        intake._call_json("system", "user")
    with pytest.raises(LLMParseError) as da_exc:
        da._call_claude("system", "user")
    assert str(intake_exc.value) == str(da_exc.value)
    assert str(intake_exc.value) == "Claude returned an empty content list"


def test_guard_non_text_block_message_parity() -> None:
    """A non-``TextBlock`` first content block raises the same message (modulo
    error class) from both guards (#16b)."""
    intake, da = _client_pair([_NotATextBlock()])
    with pytest.raises(IntakeLLMError) as intake_exc:
        intake._call_json("system", "user")
    with pytest.raises(LLMParseError) as da_exc:
        da._call_claude("system", "user")
    assert str(intake_exc.value) == str(da_exc.value)
    assert str(intake_exc.value) == "expected TextBlock from Claude, got _NotATextBlock"


def test_guard_max_tokens_truncation_message_parity() -> None:
    """A ``stop_reason='max_tokens'`` response raises the same message (modulo
    error class) from both ``_call_json`` and ``_call_claude`` (Session 167 /
    gap #3). The content is *valid, parseable* JSON, so the guard must fire on
    ``stop_reason`` alone — before parsing — in both clients; without the guard
    each would happily return the (truncated-in-reality) text. Both clients
    carry the default ``max_tokens`` (16384), so the cap in the message matches.
    """
    intake, da = _client_pair([TextBlock(text='{"a": 1}', type="text")], stop_reason="max_tokens")
    with pytest.raises(IntakeLLMError) as intake_exc:
        intake._call_json("system", "user")
    with pytest.raises(LLMParseError) as da_exc:
        da._call_claude("system", "user")
    assert str(intake_exc.value) == str(da_exc.value)
    assert str(intake_exc.value) == (
        "Claude response truncated at max_tokens=16384 (stop_reason='max_tokens'); "
        "the response is incomplete. Raise max_tokens for this client."
    )


# --- the OpenCode JSONL-event twins (spec §7.2) ---------------------------
#
# A SECOND twin pair was born with the ``opencode`` provider: each package's
# ``opencode_client.py`` carries its own copy of the JSONL event helpers, forced
# by the same C4 boundary that forced the ``_extract_json`` twins. Those drifted
# once and cost three sessions to repair (Sessions 98-100, traceable to a Session
# 51 live crash), so this battery lands in the same commit that creates the new
# copies rather than "later" — on the day they are born they have a guard.
#
# The battery is deliberately behavioural, not source-identity: an AST comparison
# trips on a benign one-sided reformat (the same reasoning that retired the plan's
# §5.4 backstop for the ``_extract_json`` twins).

_TEXT_EVENT = '{"type": "text", "part": {"type": "text", "text": %s}}'
_STEP_FINISH = '{"type": "step_finish", "part": {"reason": %s}}'
_ERROR_EVENT = (
    '{"type": "error", "error": {"name": "UnknownError", '
    '"data": {"message": "Unexpected server error.", "ref": "err_abc123"}}}'
)

#: The same input battery through both copies. Each case is a raw stdout string,
#: exercising the behaviours spec §7.2 enumerates: no text events, several text
#: events, non-JSON lines, error lines, unknown event types — plus the
#: final-step-wins rule (Appendix A.4 C4) and the no-``step_finish`` fallback.
EVENT_STREAM_CASES: list[tuple[str, str]] = [
    ("empty stream", ""),
    ("only whitespace", "\n   \n"),
    ("no text events", '{"type": "step_start", "part": {}}'),
    (
        "single text event, closed",
        "\n".join([_TEXT_EVENT % '"answer"', _STEP_FINISH % '"stop"']),
    ),
    (
        "several text events in one step",
        "\n".join([_TEXT_EVENT % '"one "', _TEXT_EVENT % '"two"', _STEP_FINISH % '"stop"']),
    ),
    (
        "final step wins over earlier narration",
        "\n".join(
            [
                _TEXT_EVENT % '"narration"',
                _STEP_FINISH % '"tool-calls"',
                _TEXT_EVENT % '"answer"',
                _STEP_FINISH % '"stop"',
            ]
        ),
    ),
    ("text with no step_finish at all", _TEXT_EVENT % '"unterminated"'),
    (
        "non-JSON preamble is skipped",
        "\n".join(["Loading config...", "[]", _TEXT_EVENT % '"answer"', _STEP_FINISH % '"stop"']),
    ),
    ("error event only", _ERROR_EVENT),
    (
        "error event alongside text",
        "\n".join([_TEXT_EVENT % '"answer"', _ERROR_EVENT, _STEP_FINISH % '"stop"']),
    ),
    (
        "unknown event types are ignored",
        "\n".join(
            [
                '{"type": "reasoning", "part": {"text": "thinking"}}',
                '{"type": "tool_use", "part": {"tool": "read"}}',
                '{"type": "brand_new_event_type", "part": {"text": "surprise"}}',
                _TEXT_EVENT % '"answer"',
                _STEP_FINISH % '"stop"',
            ]
        ),
    ),
    ("malformed part payloads", '{"type": "text", "part": null}\n{"type": "step_finish"}'),
    # Defensive shapes: the event schema is an implementation detail of a project
    # shipping releases daily (dragon 2), so both copies must degrade the same way
    # rather than one raising while the other shrugs.
    ("error payload is not an object", '{"type": "error", "error": "plain string"}'),
    ("error payload has no data", '{"type": "error", "error": {"name": "Boom"}}'),
    ("step_finish part is not an object", '{"type": "step_finish", "part": "surprise"}'),
    ("stream is a JSON array, not objects", "[1, 2, 3]"),
]


@pytest.mark.parametrize(
    ("label", "stdout"),
    EVENT_STREAM_CASES,
    ids=[case[0] for case in EVENT_STREAM_CASES],
)
def test_opencode_event_helper_parity(label: str, stdout: str) -> None:
    """Both copies of the JSONL event helpers agree on every input in the battery.

    Asserted as equality between the two copies rather than against a pinned
    expectation, because the property under guard is *sameness*: a one-sided edit
    to either package's copy fails here on the offending commit instead of
    surfacing as a live-run divergence between two providers of the same pipeline.
    """
    intake_events = intake_opencode._iter_events(stdout)
    da_events = da_opencode._iter_events(stdout)
    assert intake_events == da_events, label
    assert intake_opencode._extract_assistant_text(
        intake_events
    ) == da_opencode._extract_assistant_text(da_events), label
    assert intake_opencode._error_payloads(intake_events) == da_opencode._error_payloads(
        da_events
    ), label
    assert intake_opencode._final_step_summary(intake_events) == da_opencode._final_step_summary(
        da_events
    ), label
    assert intake_opencode._tail(stdout) == da_opencode._tail(stdout), label


def test_opencode_final_step_rule_is_pinned_not_just_mirrored() -> None:
    """Sameness is not enough on its own — two copies can be identically wrong.

    This pins the actual rule the twins implement (Appendix A.4 C4): the answer is
    the text of the last step whose ``reason`` is ``"stop"``, NOT the concatenation
    of every ``text`` event, which on a real 3-step run returned narration glued
    ahead of the answer.
    """
    stdout = "\n".join(
        [
            _TEXT_EVENT % '"narration"',
            _STEP_FINISH % '"tool-calls"',
            _TEXT_EVENT % '"answer"',
            _STEP_FINISH % '"stop"',
        ]
    )
    for module in (intake_opencode, da_opencode):
        assert module._extract_assistant_text(module._iter_events(stdout)) == "answer"


def test_opencode_shared_constants_are_identical() -> None:
    """The D2 fold separator and the locked-down agent definition are twins too.

    A divergence here would mean the two packages send differently-shaped prompts
    (silent quality drift, dragon 4) or run under **different tool permissions** —
    and the tool denial is a safety control, not a nicety (Appendix A.4 C1).
    """
    assert intake_opencode.SYSTEM_USER_SEPARATOR == da_opencode.SYSTEM_USER_SEPARATOR == "\n\n"
    assert intake_opencode.AGENT_DEFINITION == da_opencode.AGENT_DEFINITION
    assert intake_opencode.DEFAULT_AGENT_NAME == da_opencode.DEFAULT_AGENT_NAME
    assert intake_opencode.DEFAULT_MODEL is da_opencode.DEFAULT_MODEL is None
    for tool in ("edit", "write", "bash", "read", "webfetch"):
        assert f"  {tool}: deny" in intake_opencode.AGENT_DEFINITION


# --- §2.3 the intentional error-class divergence -------------------------


def test_error_classes_are_intentionally_distinct() -> None:
    """The divergence is intentional and load-bearing (plan §2.3): the two error
    classes share no ancestor below ``Exception``, which is *why* any shared
    helper would have to be error-class-parametrized. Pinning it makes a future
    "unify the errors" refactor trip here and read this rationale.

    (Distinctness is pinned via the subclass relationships rather than an
    ``is not`` identity check, which a strict type checker rejects as a
    statically non-overlapping comparison.)
    """
    assert issubclass(IntakeLLMError, RuntimeError)
    assert issubclass(LLMParseError, ValueError)
    assert not issubclass(IntakeLLMError, LLMParseError)
    assert not issubclass(LLMParseError, IntakeLLMError)
    # Generalised over the registry: every pair of distinct seam error classes
    # shares no ancestor below ``Exception``, so each seam's ``pytest.raises``
    # guard stays disjoint as Phase C adds providers.
    distinct_error_classes = {seam.error_cls for seam in _SEAMS}
    for left in distinct_error_classes:
        for right in distinct_error_classes:
            if left is not right:
                assert not issubclass(left, right)
