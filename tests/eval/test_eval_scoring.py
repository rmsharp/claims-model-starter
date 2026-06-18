"""Deterministic tier — prove the Phase B scorers measure correctly (no key).

These tests feed the scorers reference and deliberately-perturbed data to assert
they compute agreement, the laxer-tier miss, SQL parse/executability, structural
QC, and pass-rates correctly. They do NOT call any LLM and do NOT assert that a
provider meets a threshold — that is the ``live`` tier's job (test_eval_live.py).
"""

from __future__ import annotations

from dataclasses import replace

import pytest
from model_project_constructor_data_agent.db import ReadOnlyDB

from tests.eval import eval_thresholds as thresholds
from tests.eval.eval_corpus import load_governance_cases
from tests.eval.eval_scoring import (
    is_laxer_tier,
    pass_rate,
    quality_checks_structural_ok,
    score_governance,
    sql_executes,
    sql_parse_valid,
)

_CASES = {case.case_id: case for case in load_governance_cases()}


# --- governance scorer ----------------------------------------------------


def test_governance_perfect_agreement_scores_one() -> None:
    for case in _CASES.values():
        score = score_governance(case.case_id, case.reference, case.reference)
        assert score.exact_label_match is True
        assert score.laxer_tier_miss is False
        assert score.field_agreement == 1.0


def test_governance_laxer_tier_prediction_is_a_miss() -> None:
    ref = _CASES["fraud_triage"].reference  # tier_1_critical
    assert ref.risk_tier == "tier_1_critical"
    predicted = replace(ref, risk_tier="tier_4_low")
    score = score_governance("fraud_triage", ref, predicted)
    assert score.risk_tier_match is False
    assert score.exact_label_match is False
    assert score.laxer_tier_miss is True


def test_governance_stricter_tier_prediction_is_not_a_miss() -> None:
    ref = _CASES["subrogation"].reference  # tier_3_moderate
    assert ref.risk_tier == "tier_3_moderate"
    predicted = replace(ref, risk_tier="tier_1_critical")  # stricter than reference
    score = score_governance("subrogation", ref, predicted)
    assert score.risk_tier_match is False
    assert score.laxer_tier_miss is False  # erring stricter is allowed by the rule


def test_governance_single_field_diff_drops_agreement() -> None:
    ref = _CASES["pricing_optimization"].reference
    predicted = replace(ref, regulatory_frameworks=[*ref.regulatory_frameworks, "ASOP_56"])
    score = score_governance("pricing_optimization", ref, predicted)
    assert score.frameworks_match is False
    assert score.exact_label_match is True  # the two tier labels still match
    assert score.field_agreement == pytest.approx(0.8)  # 4 of 5 fields match


@pytest.mark.parametrize(
    ("reference", "predicted", "expected"),
    [
        ("tier_1_critical", "tier_4_low", True),
        ("tier_3_moderate", "tier_4_low", True),
        ("tier_4_low", "tier_1_critical", False),
        ("tier_2_high", "tier_2_high", False),
    ],
)
def test_is_laxer_tier_ordering(reference: str, predicted: str, expected: bool) -> None:
    assert is_laxer_tier(reference, predicted) is expected


def test_governance_corpus_self_agreement_meets_thresholds() -> None:
    scores = [score_governance(c.case_id, c.reference, c.reference) for c in _CASES.values()]
    agreement = pass_rate("governance", [s.exact_label_match for s in scores])
    laxer_misses = sum(1 for s in scores if s.laxer_tier_miss)
    assert agreement.meets(thresholds.GOVERNANCE_AGREEMENT_MIN)
    assert agreement.rate == 1.0
    assert laxer_misses <= thresholds.GOVERNANCE_LAXER_MISSES_MAX


# --- SQL scorers ----------------------------------------------------------


def test_sql_parse_valid_accepts_select_rejects_empty() -> None:
    assert sql_parse_valid("SELECT 1") is True
    assert sql_parse_valid("") is False


def test_sql_executes_against_seeded_schema(seeded_pc_db: ReadOnlyDB) -> None:
    assert sql_executes(seeded_pc_db, "SELECT claim_id FROM claims") is True
    assert sql_executes(seeded_pc_db, "SELECT no_such_col FROM claims") is False
    assert sql_executes(seeded_pc_db, "SELECT * FROM ghost_table") is False


# --- structural QC + aggregation -----------------------------------------


def test_quality_checks_structural_contract() -> None:
    assert quality_checks_structural_ok(2, [["qc"], ["qc"]]) is True
    assert quality_checks_structural_ok(2, [["qc"]]) is False


def test_pass_rate_and_threshold_check() -> None:
    rate = pass_rate("demo", [True, True, False])
    assert rate.rate == pytest.approx(2 / 3)
    assert rate.meets(0.5) is True
    assert rate.meets(0.9) is False
