"""Tests for :class:`AnthropicLLMClient` (intake agent).

All tests mock the Anthropic SDK at the ``client.messages.create`` boundary.
No real API calls are made.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, get_args

import pytest
from anthropic.types import TextBlock

from model_project_constructor._vocab_guard import join_members
from model_project_constructor.agents.intake.anthropic_client import (
    _DRAFT_REPORT_INSTRUCTIONS,
    DEFAULT_MAX_TOKENS,
    DEFAULT_MODEL,
    SYSTEM_GOVERNANCE,
    SYSTEM_INTERVIEWER,
    AnthropicLLMClient,
    _extract_json,
)
from model_project_constructor.agents.intake.protocol import (
    DraftReportResult,
    IntakeLLMError,
    InterviewContext,
)
from model_project_constructor.schemas.v1.common import CycleTime, ModelType, RiskTier
from model_project_constructor.schemas.v1.intake import (
    Confidence,
    CounterfactualDesign,
    ReviewCadence,
)


@dataclass
class _Response:
    # ``content`` holds real ``anthropic.types.TextBlock`` instances on the
    # happy path (so the production ``isinstance(block, TextBlock)`` guard
    # accepts them); typed ``list[Any]`` so the guard-rejection test can
    # inject a non-text block (see ``test_call_json_rejects_non_text_block``).
    content: list[Any]
    # Mirrors the real ``anthropic.types.Message.stop_reason``. Defaults to
    # ``None`` so the happy-path tests are unaffected; the max_tokens-truncation
    # guard test (Session 167) sets it to ``"max_tokens"``.
    stop_reason: str | None = None


class _FakeMessages:
    def __init__(self, responses: list[str]):
        self._responses = list(responses)
        self.calls: list[dict[str, Any]] = []

    def create(self, **kwargs: Any) -> _Response:
        self.calls.append(kwargs)
        text = self._responses.pop(0)
        return _Response(content=[TextBlock(text=text, type="text")])


class _FakeAnthropic:
    def __init__(self, responses: list[str]):
        self.messages = _FakeMessages(responses)


def _ctx(**overrides: Any) -> InterviewContext:
    base = {
        "stakeholder_id": "s",
        "session_id": "sess",
        "domain": "pc_claims",
        "initial_problem": "Problem.",
        "qa_pairs": [{"question": "Q1", "answer": "A1"}],
        "questions_asked": 1,
    }
    base.update(overrides)
    return InterviewContext(**base)  # type: ignore[arg-type]


def _draft_payload() -> dict[str, Any]:
    return {
        "business_problem": "bp",
        "proposed_solution": "ps",
        "model_solution": {
            "target_variable": "t",
            "target_definition": "td",
            "candidate_features": ["f"],
            "model_type": "supervised_classification",
            "evaluation_metrics": ["AUC"],
            "is_supervised": True,
        },
        "estimated_value": {
            "narrative": "n",
            "annual_impact_usd_low": 1.0,
            "annual_impact_usd_high": 2.0,
            "confidence": "medium",
            "assumptions": ["a"],
        },
        "value_measurement_plan": {
            "baseline_metric_name": "bm",
            "baseline_metric_definition": "bm_def",
            "baseline_measurement_window": "trailing 12 months",
            "counterfactual_design": "champion_challenger",
            "counterfactual_rationale": "rationale",
            "attribution_method_narrative": "attribution",
            "evaluation_horizon_months": 6,
            "logging_requirements": ["score", "outcome"],
            "review_cadence": "monthly",
            "success_criteria": ["+5pp at 6mo"],
            "decision_rights": "VP + DS lead",
        },
        "missing_fields": [],
    }


def _gov_payload() -> dict[str, Any]:
    return {
        "cycle_time": "tactical",
        "cycle_time_rationale": "r",
        "risk_tier": "tier_3_moderate",
        "risk_tier_rationale": "r",
        "regulatory_frameworks": ["SR_26_2"],
        "affects_consumers": True,
        "uses_protected_attributes": False,
    }


# --- next_question --------------------------------------------------------


def test_next_question_parses_ok() -> None:
    fake = _FakeAnthropic([json.dumps({"question": "Q?", "believe_enough_info": False})])
    client = AnthropicLLMClient(client=fake)
    r = client.next_question(_ctx())
    assert r.question == "Q?"
    assert r.believe_enough_info is False
    assert fake.messages.calls[0]["model"] == DEFAULT_MODEL
    assert fake.messages.calls[0]["max_tokens"] == DEFAULT_MAX_TOKENS


def test_next_question_code_fenced_json() -> None:
    fake = _FakeAnthropic(
        ["```json\n" + json.dumps({"question": "Q", "believe_enough_info": True}) + "\n```"]
    )
    client = AnthropicLLMClient(client=fake)
    r = client.next_question(_ctx())
    assert r.believe_enough_info is True


def test_next_question_rejects_non_object() -> None:
    fake = _FakeAnthropic(["[1, 2, 3]"])
    client = AnthropicLLMClient(client=fake)
    with pytest.raises(IntakeLLMError, match="next_question"):
        client.next_question(_ctx())


# --- draft_report ---------------------------------------------------------


def test_draft_report_parses_ok() -> None:
    fake = _FakeAnthropic([json.dumps(_draft_payload())])
    client = AnthropicLLMClient(client=fake)
    draft = client.draft_report(_ctx())
    assert draft.business_problem == "bp"
    assert draft.model_solution["model_type"] == "supervised_classification"
    assert draft.value_measurement_plan["baseline_metric_name"] == "bm"
    assert draft.value_measurement_plan["evaluation_horizon_months"] == 6


def test_draft_report_value_measurement_plan_optional() -> None:
    """When the LLM omits value_measurement_plan, the draft parses with an
    empty plan dict — earlier interview cycles produce drafts that finalize
    later flags as ``value_measurement_plan_incomplete``.
    """

    payload = _draft_payload()
    del payload["value_measurement_plan"]
    fake = _FakeAnthropic([json.dumps(payload)])
    client = AnthropicLLMClient(client=fake)
    draft = client.draft_report(_ctx())
    assert draft.value_measurement_plan == {}


def test_draft_report_missing_key_raises() -> None:
    payload = _draft_payload()
    del payload["model_solution"]
    fake = _FakeAnthropic([json.dumps(payload)])
    client = AnthropicLLMClient(client=fake)
    with pytest.raises(IntakeLLMError, match="missing key"):
        client.draft_report(_ctx())


def test_draft_report_rejects_non_object() -> None:
    fake = _FakeAnthropic(['"not an object"'])
    client = AnthropicLLMClient(client=fake)
    with pytest.raises(IntakeLLMError, match="draft_report"):
        client.draft_report(_ctx())


# --- classify_governance --------------------------------------------------


def test_classify_governance_parses_ok() -> None:
    fake = _FakeAnthropic([json.dumps(_gov_payload())])
    client = AnthropicLLMClient(client=fake)
    draft = DraftReportResult(**_draft_payload())
    gov = client.classify_governance(draft)
    assert gov.risk_tier == "tier_3_moderate"
    assert gov.regulatory_frameworks == ["SR_26_2"]


def test_classify_governance_missing_key_raises() -> None:
    payload = _gov_payload()
    del payload["risk_tier"]
    fake = _FakeAnthropic([json.dumps(payload)])
    client = AnthropicLLMClient(client=fake)
    draft = DraftReportResult(**_draft_payload())
    with pytest.raises(IntakeLLMError, match="missing key"):
        client.classify_governance(draft)


def test_classify_governance_rejects_non_object() -> None:
    fake = _FakeAnthropic(["42"])
    client = AnthropicLLMClient(client=fake)
    draft = DraftReportResult(**_draft_payload())
    with pytest.raises(IntakeLLMError, match="classify_governance"):
        client.classify_governance(draft)


# --- revise_report --------------------------------------------------------


def test_revise_report_parses_ok() -> None:
    revised = _draft_payload()
    revised["business_problem"] = "REVISED"
    fake = _FakeAnthropic([json.dumps(revised)])
    client = AnthropicLLMClient(client=fake)
    draft = DraftReportResult(**_draft_payload())
    new = client.revise_report(draft, feedback="please revise")
    assert new.business_problem == "REVISED"


def test_revise_report_rejects_non_object() -> None:
    fake = _FakeAnthropic(["null"])
    client = AnthropicLLMClient(client=fake)
    draft = DraftReportResult(**_draft_payload())
    with pytest.raises(IntakeLLMError, match="revise_report"):
        client.revise_report(draft, feedback="x")


# --- _call_json content-block guard --------------------------------------


def test_call_json_rejects_non_text_block() -> None:
    """#16b (Session 99): a non-text first content block (e.g. tool_use /
    thinking) must raise ``IntakeLLMError``, not ``AttributeError``.

    Ports the guard the data agent's ``_call_claude`` has always had
    (``test_call_claude_rejects_non_text_block``) into intake, whose
    ``_call_json`` previously read ``.text`` off ``content[0]`` unguarded.
    Surfaced by Session 98's adversarial verification workflow.
    """

    class _NotATextBlock:
        pass

    fake = _FakeAnthropic([])  # canned responses unused; create is overridden

    def create(**kwargs: Any) -> _Response:
        fake.messages.calls.append(kwargs)
        return _Response(content=[_NotATextBlock()])

    fake.messages.create = create  # type: ignore[method-assign]
    client = AnthropicLLMClient(client=fake)
    with pytest.raises(IntakeLLMError, match="expected TextBlock"):
        client.next_question(_ctx())


def test_call_json_rejects_empty_content() -> None:
    """#16c (Session 100): an empty ``response.content`` list must raise
    ``IntakeLLMError``, not ``IndexError``.

    A live response could come back with no content blocks; ``_call_json``
    indexed ``content[0]`` unguarded. Shared gap with the data agent's
    ``_call_claude`` (``test_call_claude_rejects_empty_content``) — surfaced
    by Session 99's adversarial completeness lens.
    """
    fake = _FakeAnthropic([])  # canned responses unused; create is overridden

    def create(**kwargs: Any) -> _Response:
        fake.messages.calls.append(kwargs)
        return _Response(content=[])

    fake.messages.create = create  # type: ignore[method-assign]
    client = AnthropicLLMClient(client=fake)
    with pytest.raises(IntakeLLMError, match="empty content"):
        client.next_question(_ctx())


def test_call_json_detects_max_tokens_truncation() -> None:
    """gap #3 (Session 167): a response that stopped at ``max_tokens`` is
    truncated mid-JSON. Detect it via ``stop_reason`` and raise an actionable
    ``IntakeLLMError`` naming the cap, instead of letting ``_extract_json`` fail
    downstream with a generic "non-JSON" error that hides the real cause. The
    content is valid JSON, so the guard must fire on ``stop_reason`` alone,
    before parsing — proving it is the truncation, not the body, that trips it.
    """
    fake = _FakeAnthropic([])  # canned responses unused; create is overridden

    def create(**kwargs: Any) -> _Response:
        fake.messages.calls.append(kwargs)
        body = '{"question": "Q", "believe_enough_info": false}'
        return _Response(
            content=[TextBlock(text=body, type="text")],
            stop_reason="max_tokens",
        )

    fake.messages.create = create  # type: ignore[method-assign]
    client = AnthropicLLMClient(client=fake)
    with pytest.raises(IntakeLLMError, match="truncated at max_tokens"):
        client.next_question(_ctx())


# --- _extract_json edge cases --------------------------------------------


def test_extract_json_strips_code_fences() -> None:
    assert _extract_json("```json\n{\"a\": 1}\n```") == {"a": 1}
    assert _extract_json("```\n{\"a\": 1}\n```") == {"a": 1}


def test_extract_json_raises_on_garbage() -> None:
    with pytest.raises(IntakeLLMError, match="non-JSON"):
        _extract_json("this is not json")


def test_extract_json_plain_object() -> None:
    assert _extract_json('{"a": 1}') == {"a": 1}


def test_extract_json_prose_before_fence() -> None:
    """Regression for run_id=run_b1_resume_live_1776570556 (Session 51).

    The intake parser was a stale pre-hardening copy until Session 98 ported
    the data agent's bare-parse-then-fence-search logic (audit finding #16):
    a real ``claude-sonnet-4-6`` response that prefixes the fence with prose
    used to crash with ``IntakeLLMError: non-JSON``.
    """
    raw = 'Here is the JSON:\n```json\n{"a": 1}\n```'
    assert _extract_json(raw) == {"a": 1}


def test_extract_json_prose_after_fence() -> None:
    """Regression for run_id=run_b1_resume_live_1776570556 (Session 51)."""
    raw = '```json\n[{"k": "v"}]\n```\n\nExplanation: the array holds one item.'
    assert _extract_json(raw) == [{"k": "v"}]


def test_extract_json_prose_before_and_after_fence() -> None:
    raw = 'Response below:\n```json\n{"x": [1, 2]}\n```\nLet me know if...'
    assert _extract_json(raw) == {"x": [1, 2]}


def test_extract_json_fence_without_language_tag_and_prose() -> None:
    raw = 'Sure, here you go:\n```\n{"ok": true}\n```'
    assert _extract_json(raw) == {"ok": True}


def test_extract_json_fence_with_malformed_body_raises() -> None:
    """A fence is found but its body is not JSON: fall through to IntakeLLMError.

    Exercises the inner fence-parse failure path so the raise surfaces the
    original bare-parse error rather than masking it.
    """
    with pytest.raises(IntakeLLMError, match="non-JSON"):
        _extract_json("Here:\n```json\nnot valid json\n```")


def test_extract_json_bare_json_still_parses() -> None:
    """Fast path: bare JSON (no fence) must not regress after the fence rework."""
    assert _extract_json('  {"a": 1}  ') == {"a": 1}
    assert _extract_json("[1, 2, 3]") == [1, 2, 3]


# --- SYSTEM_INTERVIEWER data-source probe pinning ------------------------


def test_system_interviewer_pins_data_source_discovery_probes() -> None:
    """The intake system prompt must direct Claude to probe for concrete
    data sources and offer help identifying them — otherwise the agent
    accepts vague 'we have the data' answers at face value. Backs the
    BACKLOG 'data source discovery prompts' item filed by Session 18's
    fresh-clone user test and shipped in Session 56.
    """

    prompt = SYSTEM_INTERVIEWER

    assert "CONCRETE data sources" in prompt
    assert "offer to help identify" in prompt
    for system in (
        "Guidewire ClaimCenter",
        "Duck Creek Claims",
        "policy admin",
        "billing and collections",
        "subrogation recovery",
        "fraud / SIU",
        "CRM",
        "data warehouse",
        "data lake",
    ):
        assert system in prompt, f"missing P&C-claims probe topic: {system!r}"


# --- SYSTEM_INTERVIEWER statistical-terms-note pinning -------------------


def test_system_interviewer_pins_statistical_terms_note() -> None:
    """The intake system prompt must inject a curated subset of
    docs/style/statistical_terms.md so drafted reports use precise
    statistical terminology natively. BACKLOG: 'Statistical glossary —
    agent system prompt injection' (Session 62).
    """

    prompt = SYSTEM_INTERVIEWER

    assert "docs/style/statistical_terms.md" in prompt
    for token in (
        "probability",
        "likelihood",
        "statistical significance",
        "practical significance",
        "bias",
        "algorithmic",
        "precision",
        "overfitting",
        "class imbalance",
    ):
        assert token in prompt, f"missing statistical-terms token: {token!r}"


def test_system_interviewer_pins_value_measurement_plan_section() -> None:
    """Plan §3.3 + Phase 2: the intake prompt must drive toward FIVE required
    sections (the fifth is the value measurement plan), not four. This pins
    the contract so the prompt cannot regress to the four-section framing.
    """

    prompt = SYSTEM_INTERVIEWER

    assert "FIVE required sections" in prompt or "five required sections" in prompt
    assert "value measurement plan" in prompt
    for token in (
        "baseline metric",
        "counterfactual",
        "evaluation horizon",
        "logging requirements",
        "review cadence",
        "success criteria",
        "decision rights",
    ):
        assert token in prompt, f"missing value-plan token: {token!r}"


def test_system_governance_excludes_statistical_terms_note() -> None:
    """SYSTEM_GOVERNANCE emits regulatory labels (cycle_time, risk_tier),
    not statistical prose. Injecting the statistical-terms note there
    would waste tokens without improving classification. This test pins
    the deliberate omission.
    """

    assert "docs/style/statistical_terms.md" not in SYSTEM_GOVERNANCE


# --- controlled-vocabulary derivation pins (Overhaul O4-1) ----------------

# Each intake prompt enumeration must DERIVE from its schema ``Literal`` via
# ``join_members`` (so the producer prose cannot drift from the validator).
# These pins prove every Literal member appears in the prompt and that the
# full derived enumeration is present verbatim — a future hardcode that drops
# or reorders a member fails this build. The separator matters: ``confidence``
# joins with "/" (low/medium/high), the rest with ", ".
_VOCAB_PROMPT_PINS = [
    pytest.param(CycleTime, ", ", SYSTEM_GOVERNANCE, id="cycle_time"),
    pytest.param(RiskTier, ", ", SYSTEM_GOVERNANCE, id="risk_tier"),
    pytest.param(ModelType, ", ", _DRAFT_REPORT_INSTRUCTIONS, id="model_type"),
    pytest.param(Confidence, "/", _DRAFT_REPORT_INSTRUCTIONS, id="confidence"),
    pytest.param(
        CounterfactualDesign,
        ", ",
        _DRAFT_REPORT_INSTRUCTIONS,
        id="counterfactual_design",
    ),
    pytest.param(ReviewCadence, ", ", _DRAFT_REPORT_INSTRUCTIONS, id="review_cadence"),
]


@pytest.mark.parametrize(("literal", "sep", "prompt"), _VOCAB_PROMPT_PINS)
def test_prompt_enumerates_all_literal_members(
    literal: Any, sep: str, prompt: str
) -> None:
    members = get_args(literal)
    assert members, "Literal under test has no members (test would be vacuous)"
    # The full derived enumeration appears verbatim. This is the discriminating
    # assertion: dropping or reordering a member in the prompt (or re-hardcoding
    # a drifted list) makes this contiguous substring absent → RED. (A bare
    # per-member ``in`` check is vacuous for "low", which also occurs inside
    # "annual_impact_usd_low".)
    enumeration = join_members(literal, sep=sep)
    assert enumeration in prompt, (
        f"prompt does not contain the derived enumeration {enumeration!r}"
    )
    # Defense in depth: every member is individually present.
    for member in members:
        assert str(member) in prompt, f"member {member!r} missing from prompt"


# --- default construction path (monkeypatch on anthropic.Anthropic) ------


def test_default_constructor_lazy_imports_anthropic(monkeypatch: pytest.MonkeyPatch) -> None:
    import anthropic

    created: dict[str, Any] = {}

    class _FakeClass:
        def __init__(self) -> None:
            created["hit"] = True
            self.messages = _FakeMessages(
                [json.dumps({"question": "Q", "believe_enough_info": False})]
            )

    monkeypatch.setattr(anthropic, "Anthropic", _FakeClass)
    client = AnthropicLLMClient()
    assert created["hit"] is True
    r = client.next_question(_ctx())
    assert r.question == "Q"
