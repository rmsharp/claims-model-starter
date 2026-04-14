"""Intake Agent (architecture-plan §4.1, §10).

Public API:

- :class:`IntakeAgent` — high-level runner (fixture or scripted mode)
- :class:`IntakeLLMClient` — Protocol for LLM-backed implementations
- :class:`FixtureLLMClient` — deterministic replay for tests / CLI
- :func:`build_intake_graph` — low-level compiled LangGraph (Web UI will use this)
- :func:`initial_state`, :func:`build_intake_report` — state helpers
"""

from __future__ import annotations

from model_project_constructor.agents.intake.agent import IntakeAgent
from model_project_constructor.agents.intake.fixture import (
    FIXTURE_SCHEMA,
    FixtureLLMClient,
    load_fixture,
)
from model_project_constructor.agents.intake.graph import build_intake_graph
from model_project_constructor.agents.intake.nodes import build_intake_report
from model_project_constructor.agents.intake.protocol import (
    DraftReportResult,
    GovernanceClassification,
    InterviewContext,
    IntakeLLMClient,
    IntakeLLMError,
    NextQuestionResult,
)
from model_project_constructor.agents.intake.state import (
    MAX_QUESTIONS,
    MAX_REVISIONS,
    IntakeState,
    initial_state,
)

__all__ = [
    "IntakeAgent",
    "IntakeLLMClient",
    "IntakeLLMError",
    "InterviewContext",
    "NextQuestionResult",
    "DraftReportResult",
    "GovernanceClassification",
    "FixtureLLMClient",
    "FIXTURE_SCHEMA",
    "load_fixture",
    "build_intake_graph",
    "build_intake_report",
    "IntakeState",
    "initial_state",
    "MAX_QUESTIONS",
    "MAX_REVISIONS",
]
