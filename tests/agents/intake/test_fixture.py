"""Tests for the intake fixture loader and :class:`FixtureLLMClient`."""

from __future__ import annotations

from pathlib import Path

import pytest

from model_project_constructor.agents.intake.fixture import (
    FIXTURE_SCHEMA,
    FixtureLLMClient,
    answers_from_fixture,
    load_fixture,
    review_sequence_from_fixture,
)
from model_project_constructor.agents.intake.protocol import (
    InterviewContext,
    IntakeLLMError,
    NextQuestionResult,
)


def test_load_fixture_happy_path(subrogation_fixture_path: Path) -> None:
    data = load_fixture(subrogation_fixture_path)
    assert data["schema"] == FIXTURE_SCHEMA
    assert data["stakeholder_id"] == "stakeholder_claims_001"
    assert len(data["qa_pairs"]) == 7
    assert data["draft_after"] == 7


def test_load_fixture_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_fixture(tmp_path / "nope.yaml")


def test_load_fixture_wrong_schema(tmp_path: Path) -> None:
    p = tmp_path / "bad.yaml"
    p.write_text("schema: other/v1\nstakeholder_id: x\nsession_id: y\nqa_pairs: []\ndraft: {}\ngovernance: {}\n")
    with pytest.raises(IntakeLLMError, match="schema="):
        load_fixture(p)


def test_load_fixture_not_a_mapping(tmp_path: Path) -> None:
    p = tmp_path / "list.yaml"
    p.write_text("- one\n- two\n")
    with pytest.raises(IntakeLLMError, match="not a YAML mapping"):
        load_fixture(p)


def test_load_fixture_missing_required_field(tmp_path: Path) -> None:
    p = tmp_path / "missing.yaml"
    p.write_text(
        f"schema: {FIXTURE_SCHEMA}\nstakeholder_id: x\nsession_id: y\nqa_pairs: []\ndraft: {{}}\n"
    )
    with pytest.raises(IntakeLLMError, match="missing required field: governance"):
        load_fixture(p)


def test_fixture_llm_client_dispenses_questions_in_order(subrogation_fixture: dict) -> None:
    # The fixture client is stateless: it keys off ``context.questions_asked``
    # so that it is resume-safe across process restarts. The graph advances
    # ``questions_asked`` after each ``ask_user`` interrupt, so the test
    # constructs fresh contexts with the appropriate counter.
    client = FixtureLLMClient(subrogation_fixture)
    total = len(subrogation_fixture["qa_pairs"])

    def _ctx(q_asked: int) -> InterviewContext:
        return InterviewContext(
            stakeholder_id="x",
            session_id="y",
            domain="pc_claims",
            initial_problem=None,
            qa_pairs=[],
            questions_asked=q_asked,
        )

    r1 = client.next_question(_ctx(0))
    assert r1.question == subrogation_fixture["qa_pairs"][0]["question"]
    assert r1.believe_enough_info is False

    r2 = client.next_question(_ctx(1))
    assert r2.question == subrogation_fixture["qa_pairs"][1]["question"]

    # The last pre-recorded question should flip enough_info to True.
    last = client.next_question(_ctx(total - 1))
    assert last.question == subrogation_fixture["qa_pairs"][-1]["question"]
    assert last.believe_enough_info is True

    # Past the end: filler + enough_info.
    filler = client.next_question(_ctx(total))
    assert filler.believe_enough_info is True
    assert filler.question == "(no more questions)"

    # Calling twice with the same context is idempotent (resume-safe).
    again = client.next_question(_ctx(0))
    assert again.question == r1.question


def test_fixture_llm_client_draft_and_governance(subrogation_fixture: dict) -> None:
    client = FixtureLLMClient(subrogation_fixture)
    ctx = InterviewContext(
        stakeholder_id="x",
        session_id="y",
        domain="pc_claims",
        initial_problem=None,
        qa_pairs=[],
        questions_asked=0,
    )
    draft = client.draft_report(ctx)
    assert draft.business_problem.startswith("Subrogation")
    assert draft.model_solution["model_type"] == "supervised_classification"
    gov = client.classify_governance(draft)
    assert gov.risk_tier == "tier_3_moderate"
    assert gov.cycle_time == "tactical"


def test_fixture_llm_client_revise_returns_draft_by_default(
    subrogation_fixture: dict,
) -> None:
    client = FixtureLLMClient(subrogation_fixture)
    ctx = InterviewContext(
        stakeholder_id="x", session_id="y", domain="pc_claims",
        initial_problem=None, qa_pairs=[], questions_asked=0,
    )
    draft = client.draft_report(ctx)
    revised = client.revise_report(draft, feedback="please update")
    # Without revised_draft in fixture, revise echoes the draft
    assert revised.business_problem == draft.business_problem


def test_fixture_llm_client_revised_draft_override(tmp_path: Path) -> None:
    p = tmp_path / "rev.yaml"
    p.write_text(
        f"""schema: {FIXTURE_SCHEMA}
stakeholder_id: x
session_id: y
qa_pairs: [{{question: q, answer: a}}]
draft:
  business_problem: before
  proposed_solution: s
  model_solution: {{target_variable: t, target_definition: td, candidate_features: [], model_type: other, evaluation_metrics: [], is_supervised: false}}
  estimated_value: {{narrative: n, annual_impact_usd_low: null, annual_impact_usd_high: null, confidence: low, assumptions: []}}
revised_draft:
  business_problem: AFTER
  proposed_solution: s2
  model_solution: {{target_variable: t, target_definition: td, candidate_features: [], model_type: other, evaluation_metrics: [], is_supervised: false}}
  estimated_value: {{narrative: n, annual_impact_usd_low: null, annual_impact_usd_high: null, confidence: low, assumptions: []}}
governance:
  cycle_time: tactical
  cycle_time_rationale: r
  risk_tier: tier_4_low
  risk_tier_rationale: r
  regulatory_frameworks: []
  affects_consumers: false
  uses_protected_attributes: false
review_sequence: [ACCEPT]
"""
    )
    fx = load_fixture(p)
    client = FixtureLLMClient(fx)
    ctx = InterviewContext(
        stakeholder_id="x", session_id="y", domain="pc_claims",
        initial_problem=None, qa_pairs=[], questions_asked=0,
    )
    draft = client.draft_report(ctx)
    revised = client.revise_report(draft, feedback="bad")
    assert revised.business_problem == "AFTER"


def test_answers_and_review_helpers(subrogation_fixture: dict) -> None:
    answers = answers_from_fixture(subrogation_fixture)
    assert len(answers) == 7
    assert answers[0].startswith("Since we deployed")
    reviews = review_sequence_from_fixture(subrogation_fixture)
    assert reviews == ["ACCEPT"]


def test_review_sequence_default_when_missing() -> None:
    fx = {"review_sequence": None}
    assert review_sequence_from_fixture(fx) == ["ACCEPT"]


def test_review_sequence_rejects_empty() -> None:
    with pytest.raises(IntakeLLMError):
        review_sequence_from_fixture({"review_sequence": []})


def test_build_draft_missing_field_raises(tmp_path: Path) -> None:
    p = tmp_path / "bad_draft.yaml"
    p.write_text(
        f"""schema: {FIXTURE_SCHEMA}
stakeholder_id: x
session_id: y
qa_pairs: [{{question: q, answer: a}}]
draft:
  business_problem: bp
  model_solution: {{target_variable: t, target_definition: td, candidate_features: [], model_type: other, evaluation_metrics: [], is_supervised: false}}
  estimated_value: {{narrative: n, annual_impact_usd_low: null, annual_impact_usd_high: null, confidence: low, assumptions: []}}
governance:
  cycle_time: tactical
  cycle_time_rationale: r
  risk_tier: tier_4_low
  risk_tier_rationale: r
  regulatory_frameworks: []
  affects_consumers: false
  uses_protected_attributes: false
"""
    )
    fx = load_fixture(p)
    client = FixtureLLMClient(fx)
    ctx = InterviewContext(
        stakeholder_id="x", session_id="y", domain="pc_claims",
        initial_problem=None, qa_pairs=[], questions_asked=0,
    )
    with pytest.raises(IntakeLLMError, match="missing field"):
        client.draft_report(ctx)


def test_build_governance_missing_field_raises(tmp_path: Path) -> None:
    p = tmp_path / "bad_gov.yaml"
    p.write_text(
        f"""schema: {FIXTURE_SCHEMA}
stakeholder_id: x
session_id: y
qa_pairs: [{{question: q, answer: a}}]
draft:
  business_problem: bp
  proposed_solution: s
  model_solution: {{target_variable: t, target_definition: td, candidate_features: [], model_type: other, evaluation_metrics: [], is_supervised: false}}
  estimated_value: {{narrative: n, annual_impact_usd_low: null, annual_impact_usd_high: null, confidence: low, assumptions: []}}
governance:
  cycle_time: tactical
  risk_tier: tier_4_low
  regulatory_frameworks: []
  affects_consumers: false
  uses_protected_attributes: false
"""
    )
    fx = load_fixture(p)
    client = FixtureLLMClient(fx)
    draft = client.draft_report(InterviewContext(
        stakeholder_id="x", session_id="y", domain="pc_claims",
        initial_problem=None, qa_pairs=[], questions_asked=0,
    ))
    with pytest.raises(IntakeLLMError, match="governance missing field"):
        client.classify_governance(draft)
