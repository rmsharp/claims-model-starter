"""Deterministic tier — corpus integrity, SQL-oracle soundness, interview replay.

Proves (offline, no key) that:

* the governance corpus is well-formed and spans the full ``RiskTier`` vocabulary
  (so the laxer-tier-miss logic is exercised meaningfully);
* every reference SQL parses (100%) and executes (100%) against the seeded P&C
  schema — i.e. the corpus + the ``validate_sql`` / ``ReadOnlyDB`` oracle are
  sound, which is what the live tier measures GENERATED SQL against;
* the interview goldens converge within the question cap via deterministic
  fixture replay, and the question-cap fixture terminates at the cap.
"""

from __future__ import annotations

from typing import get_args

import pytest
from model_project_constructor_data_agent.db import ReadOnlyDB

from model_project_constructor.agents.intake import FixtureLLMClient, IntakeAgent
from model_project_constructor.agents.intake.anthropic_client import GOVERNANCE_FRAMEWORKS
from model_project_constructor.agents.intake.fixture import load_fixture
from model_project_constructor.agents.intake.state import MAX_QUESTIONS
from model_project_constructor.schemas.v1.common import CycleTime, RiskTier
from model_project_constructor.schemas.v1.intake import IntakeReport
from tests.eval import eval_thresholds as thresholds
from tests.eval.eval_corpus import (
    InterviewCase,
    load_governance_cases,
    load_interview_cases,
    load_sql_cases,
    pc_inventory_from_db,
)
from tests.eval.eval_scoring import (
    interview_converged,
    pass_rate,
    premature_convergence,
    sql_executes,
    sql_parse_valid,
)

_INTERVIEW_CASES = load_interview_cases()
_CONVERGING = [case for case in _INTERVIEW_CASES if case.expect_complete]
_CAPPED = [case for case in _INTERVIEW_CASES if not case.expect_complete]


def _run(case: InterviewCase) -> IntakeReport:
    fixture = load_fixture(case.fixture_path)
    agent = IntakeAgent(llm=FixtureLLMClient(fixture))
    return agent.run_with_fixture(str(case.fixture_path))


# --- governance corpus ----------------------------------------------------


def test_governance_corpus_is_well_formed() -> None:
    cases = load_governance_cases()
    assert len(cases) >= 4
    cycle_vocab = set(get_args(CycleTime))
    tier_vocab = set(get_args(RiskTier))
    frameworks_vocab = set(GOVERNANCE_FRAMEWORKS)
    for case in cases:
        ref = case.reference
        assert ref.cycle_time in cycle_vocab
        assert ref.risk_tier in tier_vocab
        assert set(ref.regulatory_frameworks) <= frameworks_vocab


def test_governance_corpus_spans_all_risk_tiers() -> None:
    cases = load_governance_cases()
    tiers = {case.reference.risk_tier for case in cases}
    assert tiers == set(get_args(RiskTier))  # laxer-miss logic is exercised across tiers


# --- SQL oracle soundness -------------------------------------------------


def test_reference_sql_all_parse_valid() -> None:
    results = [sql_parse_valid(case.reference_sql) for case in load_sql_cases()]
    rate = pass_rate("sql_parse_valid", results)
    assert rate.rate == 1.0
    assert rate.meets(thresholds.SQL_PARSE_VALID_MIN)


def test_reference_sql_all_execute(seeded_pc_db: ReadOnlyDB) -> None:
    results = [sql_executes(seeded_pc_db, case.reference_sql) for case in load_sql_cases()]
    rate = pass_rate("sql_executable", results)
    assert rate.rate == 1.0
    assert rate.meets(thresholds.SQL_EXECUTABLE_MIN)


def test_pc_inventory_reflects_seeded_schema(seeded_pc_db: ReadOnlyDB) -> None:
    inventory = pc_inventory_from_db(seeded_pc_db)
    names = {entry.name for entry in inventory.entries}
    assert {"claims", "policies"} <= names
    claims = next(entry for entry in inventory.entries if entry.name == "claims")
    assert {"claim_id", "policy_id", "subro_recovered"} <= {c.name for c in claims.columns}


# --- interview convergence (deterministic fixture replay) -----------------


@pytest.mark.parametrize("case", _CONVERGING, ids=[c.case_id for c in _CONVERGING])
def test_interview_golden_converges(case: InterviewCase) -> None:
    report = _run(case)
    assert interview_converged(report)
    assert not premature_convergence(report)


def test_interview_goldens_meet_convergence_threshold() -> None:
    results = [interview_converged(_run(case)) for case in _CONVERGING]
    rate = pass_rate("interview_convergence", results)
    assert rate.meets(thresholds.INTERVIEW_CONVERGENCE_MIN)


@pytest.mark.parametrize("case", _CAPPED, ids=[c.case_id for c in _CAPPED])
def test_interview_question_cap_terminates(case: InterviewCase) -> None:
    report = _run(case)
    assert not interview_converged(report)
    assert report.status == "DRAFT_INCOMPLETE"
    assert "questions_cap_reached" in report.missing_fields
    assert report.questions_asked == MAX_QUESTIONS
