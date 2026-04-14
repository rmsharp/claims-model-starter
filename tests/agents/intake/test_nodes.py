"""Unit tests for intake graph nodes and routing functions."""

from __future__ import annotations

from typing import Any

from model_project_constructor.agents.intake.nodes import (
    build_intake_report,
    make_nodes,
    route_after_evaluate,
    route_after_review,
)
from model_project_constructor.agents.intake.protocol import (
    DraftReportResult,
    GovernanceClassification,
    NextQuestionResult,
)
from model_project_constructor.agents.intake.state import (
    MAX_QUESTIONS,
    MAX_REVISIONS,
    initial_state,
)


class _StaticLLM:
    def __init__(
        self,
        next_q: NextQuestionResult,
        draft: DraftReportResult,
        governance: GovernanceClassification,
    ) -> None:
        self._next = next_q
        self._draft = draft
        self._gov = governance
        self.revise_calls: list[tuple[Any, str]] = []

    def next_question(self, context):
        return self._next

    def draft_report(self, context):
        return self._draft

    def classify_governance(self, draft):
        return self._gov

    def revise_report(self, draft, feedback):
        self.revise_calls.append((draft, feedback))
        return self._draft


def _sample_draft() -> DraftReportResult:
    return DraftReportResult(
        business_problem="bp",
        proposed_solution="ps",
        model_solution={
            "target_variable": "t",
            "target_definition": "td",
            "candidate_features": ["f1"],
            "model_type": "supervised_classification",
            "evaluation_metrics": ["AUC"],
            "is_supervised": True,
        },
        estimated_value={
            "narrative": "n",
            "annual_impact_usd_low": 100.0,
            "annual_impact_usd_high": 200.0,
            "confidence": "medium",
            "assumptions": ["a1"],
        },
    )


def _sample_governance() -> GovernanceClassification:
    return GovernanceClassification(
        cycle_time="tactical",
        cycle_time_rationale="r",
        risk_tier="tier_3_moderate",
        risk_tier_rationale="r",
        regulatory_frameworks=["SR_11_7"],
        affects_consumers=True,
        uses_protected_attributes=False,
    )


def _state(**overrides: Any):
    s = initial_state(stakeholder_id="s", session_id="sess")
    s.update(overrides)  # type: ignore[typeddict-item]
    return s


def test_plan_next_question_stores_pending_and_enough_flag() -> None:
    llm = _StaticLLM(
        NextQuestionResult(question="Q1?", believe_enough_info=False),
        _sample_draft(),
        _sample_governance(),
    )
    nodes = make_nodes(llm)
    delta = nodes["plan_next_question"](_state())
    assert delta["pending_question"] == "Q1?"
    assert delta["believe_enough_info"] is False


def test_evaluate_interview_stops_on_enough_info() -> None:
    llm = _StaticLLM(
        NextQuestionResult(question="", believe_enough_info=True),
        _sample_draft(),
        _sample_governance(),
    )
    nodes = make_nodes(llm)
    delta = nodes["evaluate_interview"](_state(questions_asked=3, believe_enough_info=True))
    assert delta["interview_complete"] is True


def test_evaluate_interview_stops_on_cap() -> None:
    llm = _StaticLLM(
        NextQuestionResult(question="Q?", believe_enough_info=False),
        _sample_draft(),
        _sample_governance(),
    )
    nodes = make_nodes(llm)
    delta = nodes["evaluate_interview"](_state(questions_asked=MAX_QUESTIONS))
    assert delta["interview_complete"] is True


def test_draft_report_stores_dict_shape() -> None:
    llm = _StaticLLM(
        NextQuestionResult(question="Q?", believe_enough_info=True),
        _sample_draft(),
        _sample_governance(),
    )
    nodes = make_nodes(llm)
    delta = nodes["draft_report"](_state())
    assert delta["draft_fields"]["business_problem"] == "bp"
    assert delta["draft_fields"]["model_solution"]["target_variable"] == "t"


def test_classify_governance_merges_into_state() -> None:
    llm = _StaticLLM(
        NextQuestionResult(question="Q?", believe_enough_info=True),
        _sample_draft(),
        _sample_governance(),
    )
    nodes = make_nodes(llm)
    draft_state = _state(draft_fields=nodes["draft_report"](_state())["draft_fields"])
    delta = nodes["classify_governance"](draft_state)
    assert delta["governance_fields"]["risk_tier"] == "tier_3_moderate"
    assert delta["governance_fields"]["regulatory_frameworks"] == ["SR_11_7"]


def test_revise_increments_cycles_and_recomputes_governance() -> None:
    llm = _StaticLLM(
        NextQuestionResult(question="Q?", believe_enough_info=True),
        _sample_draft(),
        _sample_governance(),
    )
    nodes = make_nodes(llm)
    base = _state(
        draft_fields=nodes["draft_report"](_state())["draft_fields"],
        governance_fields=nodes["classify_governance"](
            _state(draft_fields=nodes["draft_report"](_state())["draft_fields"])
        )["governance_fields"],
        review_response="too thin",
        revision_cycles=1,
    )
    delta = nodes["revise"](base)
    assert delta["revision_cycles"] == 2
    assert delta["governance_fields"]["cycle_time"] == "tactical"
    assert llm.revise_calls and llm.revise_calls[-1][1] == "too thin"


def test_route_after_evaluate_loops_when_not_complete() -> None:
    assert route_after_evaluate(_state(interview_complete=False)) == "plan_next_question"
    assert route_after_evaluate(_state(interview_complete=True)) == "draft_report"


def test_route_after_review_accept_goes_to_finalize() -> None:
    assert route_after_review(_state(review_accepted=True)) == "finalize"


def test_route_after_review_reject_revises_when_under_cap() -> None:
    assert (
        route_after_review(_state(review_accepted=False, revision_cycles=1)) == "revise"
    )


def test_route_after_review_reject_finalizes_at_cap() -> None:
    assert (
        route_after_review(_state(review_accepted=False, revision_cycles=MAX_REVISIONS))
        == "finalize"
    )


def test_finalize_marks_complete_when_accepted() -> None:
    llm = _StaticLLM(
        NextQuestionResult(question="Q?", believe_enough_info=True),
        _sample_draft(),
        _sample_governance(),
    )
    nodes = make_nodes(llm)
    draft_fields = nodes["draft_report"](_state())["draft_fields"]
    gov_fields = nodes["classify_governance"](_state(draft_fields=draft_fields))[
        "governance_fields"
    ]
    state = _state(
        draft_fields=draft_fields,
        governance_fields=gov_fields,
        review_accepted=True,
        questions_asked=3,
        believe_enough_info=True,
    )
    delta = nodes["finalize"](state)
    assert delta["status"] == "COMPLETE"
    assert delta["missing_fields"] == []


def test_finalize_marks_incomplete_at_caps() -> None:
    llm = _StaticLLM(
        NextQuestionResult(question="Q?", believe_enough_info=False),
        _sample_draft(),
        _sample_governance(),
    )
    nodes = make_nodes(llm)
    draft_fields = nodes["draft_report"](_state())["draft_fields"]
    gov_fields = nodes["classify_governance"](_state(draft_fields=draft_fields))[
        "governance_fields"
    ]
    state = _state(
        draft_fields=draft_fields,
        governance_fields=gov_fields,
        review_accepted=False,
        revision_cycles=MAX_REVISIONS,
        questions_asked=MAX_QUESTIONS,
        believe_enough_info=False,
    )
    delta = nodes["finalize"](state)
    assert delta["status"] == "DRAFT_INCOMPLETE"
    assert "questions_cap_reached" in delta["missing_fields"]
    assert "revision_cap_reached" in delta["missing_fields"]


def test_build_intake_report_validates_and_returns_report() -> None:
    llm = _StaticLLM(
        NextQuestionResult(question="Q?", believe_enough_info=True),
        _sample_draft(),
        _sample_governance(),
    )
    nodes = make_nodes(llm)
    draft_fields = nodes["draft_report"](_state())["draft_fields"]
    gov_fields = nodes["classify_governance"](_state(draft_fields=draft_fields))[
        "governance_fields"
    ]
    state = _state(
        draft_fields=draft_fields,
        governance_fields=gov_fields,
        review_accepted=True,
        questions_asked=4,
    )
    report = build_intake_report(state, status="COMPLETE", missing=[])
    assert report.status == "COMPLETE"
    assert report.model_solution.is_supervised is True
    assert report.governance.risk_tier == "tier_3_moderate"
    assert report.questions_asked == 4
