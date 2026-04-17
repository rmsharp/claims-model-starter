"""Intake Agent state.

The interview is a LangGraph ``StateGraph`` whose state is a plain
``TypedDict``. We deliberately avoid reducers (``Annotated[list, add]`` etc.):
nodes return *deltas* only and overwrite list fields wholesale. This keeps the
state semantics obvious and avoids the duplication trap you hit if a later
node returns the full state back through a list reducer.

Architecture plan: §4.1, §5.1, §10.
"""

from __future__ import annotations

from typing import Any, TypedDict


class QAPair(TypedDict):
    question: str
    answer: str


class IntakeState(TypedDict, total=False):
    """State passed between intake graph nodes.

    All fields are optional at the type level so nodes can return deltas
    without having to restate every key. In practice every field is set by
    ``initial_state()`` before the graph runs.
    """

    # Session identity
    stakeholder_id: str
    session_id: str
    domain: str
    initial_problem: str | None

    # Interview rollout
    qa_pairs: list[QAPair]
    pending_question: str | None   # set by plan_next_question, cleared by ask_user
    questions_asked: int
    believe_enough_info: bool      # LLM's judgement that it has enough to draft
    interview_complete: bool       # set when we decide to stop interviewing

    # Draft + governance
    draft_fields: dict[str, Any] | None      # dict-shaped draft (business_problem, ...)
    governance_fields: dict[str, Any] | None  # dict-shaped GovernanceMetadata

    # Review loop
    review_response: str | None    # the stakeholder's last review reply
    revision_cycles: int
    review_accepted: bool

    # Terminal
    status: str                    # "COMPLETE" or "DRAFT_INCOMPLETE"
    missing_fields: list[str]


MAX_QUESTIONS = 20
MAX_REVISIONS = 3


def initial_state(
    *,
    stakeholder_id: str,
    session_id: str,
    domain: str = "pc_claims",
    initial_problem: str | None = None,
) -> IntakeState:
    return IntakeState(
        stakeholder_id=stakeholder_id,
        session_id=session_id,
        domain=domain,
        initial_problem=initial_problem,
        qa_pairs=[],
        pending_question=None,
        questions_asked=0,
        believe_enough_info=False,
        interview_complete=False,
        draft_fields=None,
        governance_fields=None,
        review_response=None,
        revision_cycles=0,
        review_accepted=False,
        status="DRAFT_INCOMPLETE",
        missing_fields=[],
    )
