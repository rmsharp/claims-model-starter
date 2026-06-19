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

from model_project_constructor.agents.intake.state import MAX_QUESTIONS
from tests.eval import eval_thresholds as thresholds
from tests.eval.eval_corpus import load_governance_cases
from tests.eval.eval_scoring import (
    interview_converged,
    is_laxer_tier,
    pass_rate,
    premature_convergence,
    quality_checks_structural_ok,
    score_governance,
    sql_executes,
    sql_parse_valid,
)
from tests.schemas.fixtures import make_intake_report

_CASES = {case.case_id: case for case in load_governance_cases()}


# --- governance scorer (S173: labels scored separately; risk_tier credits stricter) ---
#
# Governance is scored per-label, each by the metric its nature warrants (§3.4):
# cycle_time (descriptive cadence) on EXACT agreement — the gated calibration
# metric — and risk_tier (ordered severity) on match-or-stricter, with the
# dangerous laxer direction caught at zero-tolerance by laxer_tier_miss. This
# replaces the former exact-BOTH ``exact_label_match``, which penalised the
# prompt-instructed stricter direction (the gap #2 "0% is an artifact" finding).


def test_governance_perfect_agreement_scores_one() -> None:
    for case in _CASES.values():
        score = score_governance(case.case_id, case.reference, case.reference)
        assert score.cycle_time_match is True
        assert score.risk_tier_match is True
        assert score.risk_tier_acceptable is True
        assert score.laxer_tier_miss is False
        assert score.field_agreement == 1.0


def test_governance_laxer_tier_prediction_is_a_miss() -> None:
    ref = _CASES["fraud_triage"].reference  # tier_1_critical
    assert ref.risk_tier == "tier_1_critical"
    predicted = replace(ref, risk_tier="tier_4_low")
    score = score_governance("fraud_triage", ref, predicted)
    assert score.risk_tier_match is False
    assert score.risk_tier_acceptable is False  # laxer is NOT acceptable agreement
    assert score.laxer_tier_miss is True
    assert score.cycle_time_match is True  # cycle_time is scored independently


def test_governance_stricter_tier_counts_as_agreement() -> None:
    # The faithfulness fix (gap #2): a stricter-than-reference risk_tier is the
    # prompt-instructed direction ("pick the stricter tier if in doubt"), so it
    # is ACCEPTABLE agreement — not a disagreement. The former exact-both metric
    # scored this case 0; this test pins the corrected behaviour against reversion.
    ref = _CASES["subrogation"].reference  # tier_3_moderate
    assert ref.risk_tier == "tier_3_moderate"
    predicted = replace(ref, risk_tier="tier_1_critical")  # stricter than reference
    score = score_governance("subrogation", ref, predicted)
    assert score.risk_tier_match is False  # not an EXACT match...
    assert score.risk_tier_acceptable is True  # ...but match-or-stricter agrees
    assert score.laxer_tier_miss is False  # erring stricter is allowed by the rule
    assert score.cycle_time_match is True


def test_governance_cycle_time_scored_independently_of_risk_tier() -> None:
    # No exact-BOTH conflation: a cycle_time miss does not depend on risk_tier and
    # a stricter risk_tier does not drop the cycle_time agreement.
    ref = _CASES["pricing_optimization"].reference  # strategic / tier_2_high
    cycle_wrong = replace(ref, cycle_time="operational")  # cycle wrong, tier exact
    s1 = score_governance("pricing_optimization", ref, cycle_wrong)
    assert s1.cycle_time_match is False
    assert s1.risk_tier_acceptable is True
    tier_stricter = replace(ref, risk_tier="tier_1_critical")  # cycle exact, tier stricter
    s2 = score_governance("pricing_optimization", ref, tier_stricter)
    assert s2.cycle_time_match is True
    assert s2.risk_tier_acceptable is True
    assert s2.laxer_tier_miss is False


def test_governance_single_field_diff_drops_field_agreement() -> None:
    ref = _CASES["pricing_optimization"].reference
    predicted = replace(ref, regulatory_frameworks=[*ref.regulatory_frameworks, "ASOP_56"])
    score = score_governance("pricing_optimization", ref, predicted)
    assert score.frameworks_match is False
    assert score.cycle_time_match is True  # the gated label is unaffected
    assert score.risk_tier_acceptable is True
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
    # The reference labels agree with themselves: cycle_time exact-agreement is
    # 100% (>= 90%) and there are zero laxer misses. Gates the per-label metric,
    # not the former exact-both aggregate.
    scores = [score_governance(c.case_id, c.reference, c.reference) for c in _CASES.values()]
    cycle_agreement = pass_rate("gov_cycle_time", [s.cycle_time_match for s in scores])
    laxer_misses = sum(1 for s in scores if s.laxer_tier_miss)
    assert cycle_agreement.meets(thresholds.GOVERNANCE_CYCLE_TIME_AGREEMENT_MIN)
    assert cycle_agreement.rate == 1.0
    assert laxer_misses <= thresholds.GOVERNANCE_LAXER_MISSES_MAX


def test_governance_all_stricter_risk_tiers_clear_the_gate() -> None:
    # Whole-gate reversion test: if every case predicts the STRICTEST risk_tier
    # (cycle_time unchanged), cycle_time agreement stays 100% and there are zero
    # laxer misses, so the governance gate passes. Under the former exact-both
    # metric every non-critical case scored 0 and the gate failed — this pins the
    # artifact fix at the gate level, not just the per-score level.
    scores = [
        score_governance(
            case.case_id, case.reference, replace(case.reference, risk_tier="tier_1_critical")
        )
        for case in _CASES.values()
    ]
    cycle_agreement = pass_rate("gov_cycle_time", [s.cycle_time_match for s in scores])
    laxer_misses = sum(1 for s in scores if s.laxer_tier_miss)
    assert cycle_agreement.rate == 1.0  # cycle_time untouched by the tier change
    assert laxer_misses == 0  # stricter (or exact) is never a laxer miss
    assert all(s.risk_tier_acceptable for s in scores)


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


# --- interview convergence scorers (§3.4: believe_enough_info within cap) -----
#
# Convergence is "the model believed it had enough info within the 20-question
# cap" — NOT "the report finalized COMPLETE". ``finalize`` marks
# ``questions_cap_reached`` iff the cap was hit without that belief, so its
# absence is the convergence signal. These tests pin that the scorer measures
# the §3.4 metric text and not report finalization (gap #1b).


def test_interview_converged_complete_report() -> None:
    # The fully-finalized happy path still converges.
    report = make_intake_report(status="COMPLETE", missing_fields=[], questions_asked=7)
    assert interview_converged(report) is True


def test_interview_converged_when_draft_incomplete_but_within_cap() -> None:
    # gap #1b: the model believed it had enough (no cap marker) and drafted a
    # report listing genuine missing_fields the fixtures don't pre-answer. Per
    # the §3.4 metric text this DID converge — finalization is a separate metric.
    report = make_intake_report(
        status="DRAFT_INCOMPLETE",
        missing_fields=["formal_governance_review", "exact_baseline_figures"],
        questions_asked=10,
    )
    assert interview_converged(report) is True


def test_interview_not_converged_when_cap_reached() -> None:
    # Hitting the cap without believing enough is the one true non-convergence.
    report = make_intake_report(
        status="DRAFT_INCOMPLETE",
        missing_fields=["questions_cap_reached"],
        questions_asked=MAX_QUESTIONS,
    )
    assert interview_converged(report) is False


def test_premature_convergence_flags_early_within_cap() -> None:
    # Converged (no cap marker) after a single question → premature, even though
    # the draft is incomplete: the guard tracks the same convergence signal so a
    # q=1 converge-and-bail cannot slip past it.
    report = make_intake_report(
        status="DRAFT_INCOMPLETE", missing_fields=["x"], questions_asked=1
    )
    assert premature_convergence(report) is True


def test_premature_convergence_not_flagged_at_cap() -> None:
    # Hitting the cap is non-convergence, so it is never premature.
    report = make_intake_report(
        status="DRAFT_INCOMPLETE",
        missing_fields=["questions_cap_reached"],
        questions_asked=MAX_QUESTIONS,
    )
    assert premature_convergence(report) is False


def test_premature_convergence_not_flagged_with_enough_questions() -> None:
    report = make_intake_report(status="COMPLETE", missing_fields=[], questions_asked=7)
    assert premature_convergence(report) is False
