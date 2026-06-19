"""Deterministic tier — prove the Phase E cutover gate decides correctly.

No API key: these feed the gate synthetic per-capability rates and assert the
go/no-go logic, the credential probe, the threshold-registry/`eval_thresholds`
parity, and the agreement-report renderer. The *live* measurement of real
providers is ``test_eval_live.py``'s job; this tier proves the gate that turns
those measurements into a cutover decision (mirroring how ``test_eval_scoring``
proves the scorers).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.eval import eval_thresholds as thresholds
from tests.eval.eval_cutover import (
    BASELINE_PROVIDER,
    CANDIDATE_PROVIDERS,
    CHECK_KEYS,
    SHADOW_PROVIDERS,
    evaluate_cutover,
    pending_decision,
    provider_creds_available,
    render_agreement_report,
)

# A measurement mapping where every §3.4 threshold is cleared.
_ALL_PASS: dict[str, float] = {
    "json_parse": 1.0,
    "sql_parse": 1.0,
    "sql_exec": 0.97,
    "governance_cycle_time_agreement": 0.95,
    "governance_laxer_miss": 0,
    "qc_structural": 1.0,
    "interview_convergence": 0.96,
    "interview_premature": 0,
}


def test_check_keys_match_all_threshold_constants() -> None:
    # Drift guard: the gate registry must cover exactly the §3.4 thresholds and
    # source each value from eval_thresholds (no second hardcoded copy).
    assert set(CHECK_KEYS) == {
        "json_parse",
        "sql_parse",
        "sql_exec",
        "governance_cycle_time_agreement",
        "governance_laxer_miss",
        "qc_structural",
        "interview_convergence",
        "interview_premature",
    }
    decision = pending_decision("bedrock")
    by_key = {c.key: c for c in decision.checks}
    assert by_key["json_parse"].threshold == thresholds.JSON_PARSE_MIN
    assert by_key["sql_parse"].threshold == thresholds.SQL_PARSE_VALID_MIN
    assert by_key["sql_exec"].threshold == thresholds.SQL_EXECUTABLE_MIN
    assert (
        by_key["governance_cycle_time_agreement"].threshold
        == thresholds.GOVERNANCE_CYCLE_TIME_AGREEMENT_MIN
    )
    assert by_key["governance_laxer_miss"].threshold == thresholds.GOVERNANCE_LAXER_MISSES_MAX
    assert by_key["qc_structural"].threshold == thresholds.QUALITY_CHECKS_STRUCTURAL_MIN
    assert by_key["interview_convergence"].threshold == thresholds.INTERVIEW_CONVERGENCE_MIN
    assert by_key["interview_premature"].threshold == thresholds.INTERVIEW_PREMATURE_MAX


def test_all_thresholds_met_is_go() -> None:
    decision = evaluate_cutover("bedrock", _ALL_PASS)
    assert decision.decision == "GO"
    assert decision.failing == ()
    assert decision.pending == ()
    assert all(c.passed for c in decision.checks)
    assert "meets every" in decision.recommendation


def test_one_subthreshold_rate_is_no_go() -> None:
    measured = {**_ALL_PASS, "governance_cycle_time_agreement": 0.80}  # below 0.90
    decision = evaluate_cutover("bedrock", measured)
    assert decision.decision == "NO-GO"
    assert [c.key for c in decision.failing] == ["governance_cycle_time_agreement"]
    # Every other check still passes — only the one below threshold fails.
    assert all(
        c.status == "PASS"
        for c in decision.checks
        if c.key != "governance_cycle_time_agreement"
    )
    assert BASELINE_PROVIDER in decision.recommendation
    assert "governance_cycle_time_agreement" in decision.recommendation


def test_laxer_tier_miss_is_zero_tolerance_no_go() -> None:
    # A single laxer-tier miss is the §3.4 zero-tolerance failure (≤ 0).
    decision = evaluate_cutover("bedrock", {**_ALL_PASS, "governance_laxer_miss": 1})
    assert decision.decision == "NO-GO"
    assert [c.key for c in decision.failing] == ["governance_laxer_miss"]


def test_premature_convergence_is_zero_tolerance_no_go() -> None:
    decision = evaluate_cutover("bedrock", {**_ALL_PASS, "interview_premature": 2})
    assert decision.decision == "NO-GO"
    assert [c.key for c in decision.failing] == ["interview_premature"]


def test_max_check_exactly_at_threshold_passes() -> None:
    # A "max" check passes at the boundary (0 misses == ≤ 0).
    decision = evaluate_cutover("bedrock", {**_ALL_PASS, "governance_laxer_miss": 0})
    assert decision.decision == "GO"


def test_min_check_exactly_at_threshold_passes() -> None:
    # A "min" check passes at the boundary (0.90 == ≥ 0.90).
    decision = evaluate_cutover("bedrock", {**_ALL_PASS, "governance_cycle_time_agreement": 0.90})
    by_key = {c.key: c for c in decision.checks}
    assert by_key["governance_cycle_time_agreement"].status == "PASS"


def test_missing_or_none_measurement_is_pending_not_go() -> None:
    # An unmeasured threshold cannot certify GO — it resolves to PENDING (the
    # no-go-by-default rule), even when every measured value passes.
    partial = {k: v for k, v in _ALL_PASS.items() if k != "sql_exec"}
    decision = evaluate_cutover("bedrock", partial)
    assert decision.decision == "PENDING"
    assert [c.key for c in decision.pending] == ["sql_exec"]
    assert decision.failing == ()
    assert "keep anthropic primary" in decision.recommendation.lower()


def test_fail_beats_pending_in_decision() -> None:
    # A hard FAIL outranks any PENDING — the verdict is NO-GO, not PENDING.
    measured = {"governance_cycle_time_agreement": 0.10}  # one fail, the rest unmeasured
    decision = evaluate_cutover("bedrock", measured)
    assert decision.decision == "NO-GO"


def test_pending_decision_is_all_pending() -> None:
    decision = pending_decision("bedrock")
    assert decision.decision == "PENDING"
    assert len(decision.pending) == len(CHECK_KEYS)
    assert all(c.measured is None and c.passed is None for c in decision.checks)


@pytest.mark.parametrize("provider", SHADOW_PROVIDERS)
def test_shadow_providers_have_baseline_and_candidate(provider: str) -> None:
    # Sanity: the baseline is the incumbent; the candidate set is non-empty and
    # disjoint from the baseline (so a shadow run actually compares something).
    assert BASELINE_PROVIDER == "anthropic"
    assert CANDIDATE_PROVIDERS
    assert BASELINE_PROVIDER not in CANDIDATE_PROVIDERS
    assert provider in SHADOW_PROVIDERS


def test_creds_probe_anthropic_keyed_on_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert provider_creds_available("anthropic") is False
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    assert provider_creds_available("anthropic") is True


def test_creds_probe_bedrock_keyed_on_aws_signals(monkeypatch: pytest.MonkeyPatch) -> None:
    # Either AWS env signal makes Bedrock runnable; the ``or`` short-circuits
    # before the ~/.aws/credentials file, so these need no home neutralisation.
    for var in ("AWS_ACCESS_KEY_ID", "AWS_PROFILE"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "AKIA-test")
    assert provider_creds_available("bedrock") is True
    monkeypatch.delenv("AWS_ACCESS_KEY_ID", raising=False)
    monkeypatch.setenv("AWS_PROFILE", "default")
    assert provider_creds_available("bedrock") is True


def test_creds_probe_bedrock_false_when_no_signals(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    for var in ("AWS_ACCESS_KEY_ID", "AWS_PROFILE"):
        monkeypatch.delenv(var, raising=False)
    # Point HOME at an empty dir so ~/.aws/credentials does not exist.
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    assert provider_creds_available("bedrock") is False


def test_creds_probe_unknown_provider_is_false() -> None:
    assert provider_creds_available("openai") is False


def test_render_agreement_report_pending_state() -> None:
    decisions = {p: pending_decision(p) for p in SHADOW_PROVIDERS}
    report = render_agreement_report(decisions)
    assert "anthropic (baseline)" in report
    assert "bedrock (candidate)" in report
    assert "PENDING" in report
    # No candidate verdict line should claim GO/NO-GO while unmeasured.
    assert "bedrock: PENDING" in report
    # The baseline never gets its own verdict line (it is the incumbent).
    assert "anthropic: " not in report


def test_render_agreement_report_shows_pass_and_fail() -> None:
    decisions = {
        "anthropic": evaluate_cutover("anthropic", _ALL_PASS),
        "bedrock": evaluate_cutover(
            "bedrock", {**_ALL_PASS, "governance_cycle_time_agreement": 0.50}
        ),
    }
    report = render_agreement_report(decisions)
    assert "(PASS)" in report
    assert "(FAIL)" in report
    assert "bedrock: NO-GO" in report
