"""LLM boundary for the Intake Agent.

Mirrors the shape of the Data Agent's ``LLMClient`` protocol but is kept
*separate* on purpose: the two agents have no method overlap and the Phase 2B
refactor relies on the standalone data agent not knowing anything about the
main package. See architecture-plan §7.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from model_project_constructor.agents.intake.state import QAPair


@dataclass
class InterviewContext:
    """Read-only snapshot of the interview passed to the LLM."""

    stakeholder_id: str
    session_id: str
    domain: str
    initial_problem: str | None
    qa_pairs: list[QAPair]
    questions_asked: int


@dataclass
class NextQuestionResult:
    """Returned by :meth:`IntakeLLMClient.next_question`.

    ``believe_enough_info`` is the LLM's own judgement that it has gathered
    enough to draft the report. The agent still enforces the hard 20-question
    cap from §4.1 independently.
    """

    question: str
    believe_enough_info: bool


@dataclass
class DraftReportResult:
    """Business-section draft returned by :meth:`IntakeLLMClient.draft_report`.

    These are the fields that go into ``IntakeReport`` minus governance,
    metadata, and identity. ``model_solution`` and ``estimated_value`` are
    dict-shaped here and validated later when we build the Pydantic model.
    """

    business_problem: str
    proposed_solution: str
    model_solution: dict[str, Any]
    estimated_value: dict[str, Any]
    missing_fields: list[str] = field(default_factory=list)


@dataclass
class GovernanceClassification:
    """Governance sub-prompt output — maps onto ``GovernanceMetadata``."""

    cycle_time: str
    cycle_time_rationale: str
    risk_tier: str
    risk_tier_rationale: str
    regulatory_frameworks: list[str]
    affects_consumers: bool
    uses_protected_attributes: bool


class IntakeLLMClient(Protocol):
    """Strategy for the intake agent's four LLM calls.

    Every call returns a fully-formed structured result. Parsing, retries, and
    error mapping live on the concrete side (``AnthropicLLMClient``); nodes
    treat this protocol as total.
    """

    def next_question(self, context: InterviewContext) -> NextQuestionResult: ...

    def draft_report(self, context: InterviewContext) -> DraftReportResult: ...

    def classify_governance(
        self, draft: DraftReportResult
    ) -> GovernanceClassification: ...

    def revise_report(
        self, draft: DraftReportResult, feedback: str
    ) -> DraftReportResult: ...


class IntakeLLMError(RuntimeError):
    """Raised by concrete LLM clients when a response cannot be parsed."""
