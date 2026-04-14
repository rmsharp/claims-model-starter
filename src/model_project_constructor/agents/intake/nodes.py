"""Intake Agent graph nodes.

Each node is a pure function over ``IntakeState`` and returns a delta dict.
Nodes that call ``interrupt()`` MUST NOT also call the LLM: on resume the
whole node re-executes from the top, so any pre-interrupt side effects fire
twice. We split plan-a-question (LLM, one-shot) from ask-user (interrupt only).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from langgraph.types import interrupt

from model_project_constructor.agents.intake.protocol import (
    DraftReportResult,
    GovernanceClassification,
    InterviewContext,
    IntakeLLMClient,
    IntakeLLMError,
)
from model_project_constructor.agents.intake.state import (
    MAX_QUESTIONS,
    MAX_REVISIONS,
    IntakeState,
)
from model_project_constructor.schemas.v1.intake import (
    EstimatedValue,
    GovernanceMetadata,
    IntakeReport,
    ModelSolution,
)

REVIEW_ACCEPT_TOKENS = {"accept", "yes", "approve", "approved", "ok", "looks good"}


def _context(state: IntakeState) -> InterviewContext:
    return InterviewContext(
        stakeholder_id=state["stakeholder_id"],
        session_id=state["session_id"],
        domain=state.get("domain", "pc_claims"),
        initial_problem=state.get("initial_problem"),
        qa_pairs=list(state.get("qa_pairs", [])),
        questions_asked=state.get("questions_asked", 0),
    )


def make_nodes(llm: IntakeLLMClient) -> dict[str, Any]:
    """Build the callable nodes bound to a given LLM client."""

    def plan_next_question(state: IntakeState) -> dict[str, Any]:
        result = llm.next_question(_context(state))
        return {
            "pending_question": result.question,
            "believe_enough_info": result.believe_enough_info,
        }

    def ask_user(state: IntakeState) -> dict[str, Any]:
        question = state.get("pending_question") or ""
        answer = interrupt(
            {
                "kind": "question",
                "question": question,
                "question_number": state.get("questions_asked", 0) + 1,
            }
        )
        if not isinstance(answer, str):
            answer = str(answer)
        qa_pairs = list(state.get("qa_pairs", []))
        qa_pairs.append({"question": question, "answer": answer})
        return {
            "qa_pairs": qa_pairs,
            "pending_question": None,
            "questions_asked": state.get("questions_asked", 0) + 1,
        }

    def evaluate_interview(state: IntakeState) -> dict[str, Any]:
        asked = state.get("questions_asked", 0)
        enough = state.get("believe_enough_info", False)
        complete = enough or asked >= MAX_QUESTIONS
        return {"interview_complete": complete}

    def draft_report_node(state: IntakeState) -> dict[str, Any]:
        draft = llm.draft_report(_context(state))
        return {"draft_fields": _draft_to_dict(draft)}

    def classify_governance_node(state: IntakeState) -> dict[str, Any]:
        draft_fields = state.get("draft_fields") or {}
        draft = _dict_to_draft(draft_fields)
        gov = llm.classify_governance(draft)
        return {"governance_fields": _governance_to_dict(gov)}

    def await_review(state: IntakeState) -> dict[str, Any]:
        response = interrupt(
            {
                "kind": "review",
                "draft_fields": state.get("draft_fields"),
                "governance_fields": state.get("governance_fields"),
                "revision_cycles": state.get("revision_cycles", 0),
            }
        )
        if not isinstance(response, str):
            response = str(response)
        accepted = response.strip().lower() in REVIEW_ACCEPT_TOKENS
        return {"review_response": response, "review_accepted": accepted}

    def revise_node(state: IntakeState) -> dict[str, Any]:
        draft_fields = state.get("draft_fields") or {}
        draft = _dict_to_draft(draft_fields)
        feedback = state.get("review_response") or ""
        revised = llm.revise_report(draft, feedback)
        # Governance must be re-derived from the revised draft.
        gov = llm.classify_governance(revised)
        return {
            "draft_fields": _draft_to_dict(revised),
            "governance_fields": _governance_to_dict(gov),
            "revision_cycles": state.get("revision_cycles", 0) + 1,
        }

    def finalize_node(state: IntakeState) -> dict[str, Any]:
        asked = state.get("questions_asked", 0)
        accepted = state.get("review_accepted", False)
        revisions = state.get("revision_cycles", 0)

        draft_fields = state.get("draft_fields") or {}
        governance_fields = state.get("governance_fields") or {}

        missing: list[str] = list(draft_fields.get("missing_fields") or [])
        if asked >= MAX_QUESTIONS and not state.get("believe_enough_info", False):
            if "questions_cap_reached" not in missing:
                missing.append("questions_cap_reached")
        if not accepted and revisions >= MAX_REVISIONS:
            if "revision_cap_reached" not in missing:
                missing.append("revision_cap_reached")

        status = "COMPLETE" if accepted and not missing else "DRAFT_INCOMPLETE"

        # Validate through Pydantic so downstream receivers can trust the
        # shape. We keep the validated report *out* of state (LangGraph
        # checkpointers serialize dicts cleanly; IntakeReport would need
        # custom codec support), and instead store the dicts and
        # reconstruct the report on demand via :func:`build_intake_report`.
        build_intake_report(state, status=status, missing=missing)

        return {"status": status, "missing_fields": missing}

    return {
        "plan_next_question": plan_next_question,
        "ask_user": ask_user,
        "evaluate_interview": evaluate_interview,
        "draft_report": draft_report_node,
        "classify_governance": classify_governance_node,
        "await_review": await_review,
        "revise": revise_node,
        "finalize": finalize_node,
    }


def route_after_evaluate(state: IntakeState) -> str:
    return "draft_report" if state.get("interview_complete") else "plan_next_question"


def route_after_review(state: IntakeState) -> str:
    if state.get("review_accepted", False):
        return "finalize"
    if state.get("revision_cycles", 0) >= MAX_REVISIONS:
        return "finalize"
    return "revise"


# --- helpers: dataclass ↔ dict round trips ------------------------------------


def _draft_to_dict(draft: DraftReportResult) -> dict[str, Any]:
    return {
        "business_problem": draft.business_problem,
        "proposed_solution": draft.proposed_solution,
        "model_solution": dict(draft.model_solution),
        "estimated_value": dict(draft.estimated_value),
        "missing_fields": list(draft.missing_fields),
    }


def _dict_to_draft(d: dict[str, Any]) -> DraftReportResult:
    return DraftReportResult(
        business_problem=d["business_problem"],
        proposed_solution=d["proposed_solution"],
        model_solution=dict(d["model_solution"]),
        estimated_value=dict(d["estimated_value"]),
        missing_fields=list(d.get("missing_fields") or []),
    )


def _governance_to_dict(gov: GovernanceClassification) -> dict[str, Any]:
    return {
        "cycle_time": gov.cycle_time,
        "cycle_time_rationale": gov.cycle_time_rationale,
        "risk_tier": gov.risk_tier,
        "risk_tier_rationale": gov.risk_tier_rationale,
        "regulatory_frameworks": list(gov.regulatory_frameworks),
        "affects_consumers": gov.affects_consumers,
        "uses_protected_attributes": gov.uses_protected_attributes,
    }


def build_intake_report(
    state: IntakeState,
    *,
    status: str,
    missing: list[str],
) -> IntakeReport:
    """Assemble + validate an ``IntakeReport`` from the final state.

    Raises :class:`IntakeLLMError` if the draft/governance produced by the
    LLM doesn't conform to the v1 schema — this preserves the
    fail-loud-at-boundary contract of §12.
    """

    draft_fields = state.get("draft_fields") or {}
    governance_fields = state.get("governance_fields") or {}
    try:
        model_solution = ModelSolution(**draft_fields["model_solution"])
        estimated_value = EstimatedValue(**draft_fields["estimated_value"])
        governance = GovernanceMetadata(**governance_fields)
        return IntakeReport(
            status=status,  # type: ignore[arg-type]
            missing_fields=list(missing),
            business_problem=draft_fields["business_problem"],
            proposed_solution=draft_fields["proposed_solution"],
            model_solution=model_solution,
            estimated_value=estimated_value,
            governance=governance,
            stakeholder_id=state["stakeholder_id"],
            session_id=state["session_id"],
            created_at=datetime.now(timezone.utc),
            questions_asked=state.get("questions_asked", 0),
            revision_cycles=state.get("revision_cycles", 0),
        )
    except Exception as exc:  # pragma: no cover - exercised via tests
        raise IntakeLLMError(
            f"Failed to build IntakeReport from draft/governance: {exc}"
        ) from exc
