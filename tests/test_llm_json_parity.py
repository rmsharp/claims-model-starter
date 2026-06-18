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
from model_project_constructor_data_agent import anthropic_client as da_client
from model_project_constructor_data_agent.anthropic_client import LLMParseError

from model_project_constructor.agents.intake import anthropic_client as intake_client
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


class _FakeMessages:
    def __init__(self, content: list[Any]) -> None:
        self._content = content
        self.calls: list[dict[str, Any]] = []

    def create(self, **kwargs: Any) -> _FakeResponse:
        self.calls.append(kwargs)
        return _FakeResponse(content=self._content)


class _FakeAnthropic:
    def __init__(self, content: list[Any]) -> None:
        self.messages = _FakeMessages(content)


class _NotATextBlock:
    """A non-``TextBlock`` first content block, to trip the type guard."""


def _client_pair(
    content: list[Any],
) -> tuple[intake_client.AnthropicLLMClient, da_client.AnthropicLLMClient]:
    """Build one intake + one data-agent client, each over a fake returning
    ``content`` as ``response.content``."""
    return (
        intake_client.AnthropicLLMClient(client=_FakeAnthropic(content)),
        da_client.AnthropicLLMClient(client=_FakeAnthropic(content)),
    )


# --- provider registry (the cross-PROVIDER extension point) --------------
#
# Each seam carries its OWN ``_extract_json`` copy and its OWN error class
# (constraint C4 — see the module docstring); today both seams run a single
# provider (``anthropic``). Phase C of the multi-provider LLM plan
# (``docs/planning/multi-provider-llm-plan.md`` §5) adds a second provider by
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
    # package's ``AnthropicLLMClient`` (the SDK's ``AnthropicBedrock`` is a
    # drop-in with an identical Messages API), so it reuses that package's
    # ``_extract_json`` and seam error class — there is no separate parser copy
    # to drift. These rows document the (seam, provider) matrix and pin that the
    # Bedrock provider parses + raises through its seam's error class.
    _Seam("intake", "bedrock", intake_client._extract_json, IntakeLLMError),
    _Seam("data_agent", "bedrock", da_client._extract_json, LLMParseError),
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
