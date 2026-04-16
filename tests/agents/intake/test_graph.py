"""End-to-end tests for the compiled intake graph + IntakeAgent driver.

These tests exercise the REAL LangGraph interrupt/resume loop on
langgraph 0.2.76 using fixtures. If these pass, the interrupt pattern
itself is verified.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from model_project_constructor.agents.intake import (
    MAX_QUESTIONS,
    MAX_REVISIONS,
    FixtureLLMClient,
    IntakeAgent,
)
from model_project_constructor.agents.intake.fixture import load_fixture


def _agent_from_fixture_path(path: Path) -> IntakeAgent:
    fixture = load_fixture(path)
    return IntakeAgent(llm=FixtureLLMClient(fixture))


def test_subrogation_happy_path(subrogation_fixture_path: Path) -> None:
    agent = _agent_from_fixture_path(subrogation_fixture_path)
    report = agent.run_with_fixture(str(subrogation_fixture_path))
    assert report.status == "COMPLETE"
    assert report.questions_asked == 7
    assert report.revision_cycles == 0
    assert report.governance.cycle_time == "tactical"
    assert report.governance.risk_tier == "tier_3_moderate"
    assert report.model_solution.target_variable == "successful_subrogation"
    assert report.estimated_value.annual_impact_usd_low == 2_000_000.0
    assert report.missing_fields == []


def test_pricing_strategic_tier_2(pricing_fixture_path: Path) -> None:
    agent = _agent_from_fixture_path(pricing_fixture_path)
    report = agent.run_with_fixture(str(pricing_fixture_path))
    assert report.status == "COMPLETE"
    assert report.governance.cycle_time == "strategic"
    assert report.governance.risk_tier == "tier_2_high"
    assert report.governance.affects_consumers is True
    assert report.model_solution.model_type == "supervised_regression"


def test_fraud_continuous_tier_1(fraud_fixture_path: Path) -> None:
    agent = _agent_from_fixture_path(fraud_fixture_path)
    report = agent.run_with_fixture(str(fraud_fixture_path))
    assert report.status == "COMPLETE"
    assert report.governance.cycle_time == "continuous"
    assert report.governance.risk_tier == "tier_1_critical"
    assert "EU_AI_ACT_ART_9" in report.governance.regulatory_frameworks
    assert report.questions_asked == 4


def test_question_cap_produces_draft_incomplete(question_cap_fixture_path: Path) -> None:
    agent = _agent_from_fixture_path(question_cap_fixture_path)
    report = agent.run_with_fixture(str(question_cap_fixture_path))
    assert report.status == "DRAFT_INCOMPLETE"
    assert report.questions_asked == MAX_QUESTIONS
    assert "questions_cap_reached" in report.missing_fields


def test_revision_cap_produces_draft_incomplete(revision_cap_fixture_path: Path) -> None:
    agent = _agent_from_fixture_path(revision_cap_fixture_path)
    report = agent.run_with_fixture(str(revision_cap_fixture_path))
    assert report.status == "DRAFT_INCOMPLETE"
    assert report.revision_cycles == MAX_REVISIONS
    assert "revision_cap_reached" in report.missing_fields


def test_run_scripted_rejects_short_answer_list(
    subrogation_fixture_path: Path,
) -> None:
    agent = _agent_from_fixture_path(subrogation_fixture_path)
    with pytest.raises(RuntimeError, match="ran out of interview answers"):
        agent.run_scripted(
            stakeholder_id="x",
            session_id="short-answers",
            interview_answers=["only one"],
            review_responses=["ACCEPT"],
        )


def test_run_scripted_rejects_short_review_list(
    subrogation_fixture_path: Path,
) -> None:
    fixture = load_fixture(subrogation_fixture_path)
    agent = IntakeAgent(llm=FixtureLLMClient(fixture))
    with pytest.raises(RuntimeError, match="ran out of review responses"):
        agent.run_scripted(
            stakeholder_id="x",
            session_id="no-reviews",
            interview_answers=[p["answer"] for p in fixture["qa_pairs"]],
            review_responses=[],
        )


def test_run_scripted_review_accept_tokens_variants(
    subrogation_fixture_path: Path,
) -> None:
    fixture = load_fixture(subrogation_fixture_path)
    for accept_word in ("yes", "OK", "Looks good", "Approved"):
        agent = IntakeAgent(llm=FixtureLLMClient(fixture))
        report = agent.run_scripted(
            stakeholder_id="x",
            session_id=f"session-{accept_word}",
            interview_answers=[p["answer"] for p in fixture["qa_pairs"]],
            review_responses=[accept_word],
        )
        assert report.status == "COMPLETE", accept_word
