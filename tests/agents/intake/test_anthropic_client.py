"""Tests for :class:`AnthropicLLMClient` (intake agent).

All tests mock the Anthropic SDK at the ``client.messages.create`` boundary.
No real API calls are made.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import pytest

from model_project_constructor.agents.intake.anthropic_client import (
    DEFAULT_MAX_TOKENS,
    DEFAULT_MODEL,
    AnthropicLLMClient,
    _extract_json,
)
from model_project_constructor.agents.intake.protocol import (
    DraftReportResult,
    IntakeLLMError,
    InterviewContext,
)


@dataclass
class _Block:
    text: str


@dataclass
class _Response:
    content: list[_Block]


class _FakeMessages:
    def __init__(self, responses: list[str]):
        self._responses = list(responses)
        self.calls: list[dict[str, Any]] = []

    def create(self, **kwargs: Any) -> _Response:
        self.calls.append(kwargs)
        text = self._responses.pop(0)
        return _Response(content=[_Block(text=text)])


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
        "missing_fields": [],
    }


def _gov_payload() -> dict[str, Any]:
    return {
        "cycle_time": "tactical",
        "cycle_time_rationale": "r",
        "risk_tier": "tier_3_moderate",
        "risk_tier_rationale": "r",
        "regulatory_frameworks": ["SR_11_7"],
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
    assert gov.regulatory_frameworks == ["SR_11_7"]


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


# --- _extract_json edge cases --------------------------------------------


def test_extract_json_strips_code_fences() -> None:
    assert _extract_json("```json\n{\"a\": 1}\n```") == {"a": 1}
    assert _extract_json("```\n{\"a\": 1}\n```") == {"a": 1}


def test_extract_json_raises_on_garbage() -> None:
    with pytest.raises(IntakeLLMError, match="non-JSON"):
        _extract_json("this is not json")


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
