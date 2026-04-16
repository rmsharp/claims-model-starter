"""Tests for the Intake → Data handoff adapter (orchestrator/adapters.py).

These pin the §7 decoupling boundary: the adapter is the ONLY code in
the repo that imports both ``IntakeReport`` and ``DataRequest``, and
these tests lock down its inference rules so downstream refactors don't
silently reshape the DataRequest.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from model_project_constructor.orchestrator.adapters import (
    infer_target_granularity,
    intake_report_to_data_request,
)
from model_project_constructor.schemas.v1.common import ModelType
from model_project_constructor.schemas.v1.intake import (
    EstimatedValue,
    GovernanceMetadata,
    IntakeReport,
    ModelSolution,
)


def _make_intake(
    *,
    model_type: ModelType = "supervised_classification",
    candidate_features: list[str] | None = None,
    target_definition: str = "Binary outcome: did the claim recover?",
    status: str = "COMPLETE",
) -> IntakeReport:
    return IntakeReport(
        status=status,  # type: ignore[arg-type]
        missing_fields=[],
        business_problem="Subrogation recovery rates dropped post-migration.",
        proposed_solution="Score each claim for recovery probability.",
        model_solution=ModelSolution(
            target_variable="successful_subrogation",
            target_definition=target_definition,
            candidate_features=candidate_features
            or ["feature_a", "feature_b", "feature_c"],
            model_type=model_type,
            evaluation_metrics=["AUC"],
            is_supervised=True,
        ),
        estimated_value=EstimatedValue(
            narrative="≈$3M/year.",
            annual_impact_usd_low=2_000_000.0,
            annual_impact_usd_high=4_000_000.0,
            confidence="medium",
            assumptions=["baseline $30M recovery"],
        ),
        governance=GovernanceMetadata(
            cycle_time="tactical",
            cycle_time_rationale="monthly feedback loop",
            risk_tier="tier_3_moderate",
            risk_tier_rationale="advisory only",
            regulatory_frameworks=["SR_11_7"],
            affects_consumers=True,
            uses_protected_attributes=False,
        ),
        stakeholder_id="stake_001",
        session_id="session_001",
        created_at=datetime.now(UTC),
        questions_asked=7,
        revision_cycles=0,
    )


class TestInferTargetGranularity:
    def test_classification_maps_to_event(self) -> None:
        intake = _make_intake(model_type="supervised_classification")
        g = infer_target_granularity(intake)
        assert g.unit == "claim"
        assert g.time_grain == "event"

    def test_regression_maps_to_event(self) -> None:
        intake = _make_intake(model_type="supervised_regression")
        assert infer_target_granularity(intake).time_grain == "event"

    def test_time_series_maps_to_monthly(self) -> None:
        intake = _make_intake(model_type="time_series")
        assert infer_target_granularity(intake).time_grain == "monthly"

    def test_clustering_maps_to_event(self) -> None:
        intake = _make_intake(model_type="unsupervised_clustering")
        assert infer_target_granularity(intake).time_grain == "event"


class TestIntakeReportToDataRequest:
    def test_copies_candidate_features_verbatim(self) -> None:
        features = ["alpha", "beta", "gamma", "delta"]
        intake = _make_intake(candidate_features=features)
        request = intake_report_to_data_request(intake, run_id="run_001")
        assert request.required_features == features
        # Defensive copy — mutating the request should not affect the intake.
        request.required_features.append("epsilon")
        assert intake.model_solution.candidate_features == features

    def test_target_description_pulls_from_model_solution(self) -> None:
        intake = _make_intake(target_definition="recovery within 18 months")
        request = intake_report_to_data_request(intake, run_id="run_002")
        assert request.target_description == "recovery within 18 months"
        assert "recovery within 18 months" in request.population_filter

    def test_source_and_source_ref_are_pipeline(self) -> None:
        intake = _make_intake()
        request = intake_report_to_data_request(intake, run_id="run_abc123")
        assert request.source == "pipeline"
        assert request.source_ref == "run_abc123"

    def test_time_range_has_sensible_default(self) -> None:
        intake = _make_intake()
        request = intake_report_to_data_request(intake, run_id="run_001")
        assert request.time_range  # non-empty
        assert "year" in request.time_range.lower()

    def test_database_hint_is_none_unless_explicitly_set(self) -> None:
        intake = _make_intake()
        request = intake_report_to_data_request(intake, run_id="run_001")
        assert request.database_hint is None

    def test_data_quality_concerns_start_empty(self) -> None:
        intake = _make_intake()
        request = intake_report_to_data_request(intake, run_id="run_001")
        assert request.data_quality_concerns == []

    def test_round_trip_produces_valid_data_request(self) -> None:
        intake = _make_intake()
        request = intake_report_to_data_request(intake, run_id="run_001")
        # Re-validating the dumped dict should succeed — proves the adapter
        # produces Pydantic-strict output.
        from model_project_constructor.schemas.v1.data import DataRequest

        round_tripped = DataRequest.model_validate(request.model_dump(mode="json"))
        assert round_tripped == request

    def test_time_series_intake_produces_monthly_grain(self) -> None:
        intake = _make_intake(model_type="time_series")
        request = intake_report_to_data_request(intake, run_id="run_ts")
        assert request.target_granularity.time_grain == "monthly"

    @pytest.mark.parametrize("status", ["COMPLETE", "DRAFT_INCOMPLETE"])
    def test_adapter_accepts_both_statuses(self, status: str) -> None:
        """§12 halts on DRAFT_INCOMPLETE before the adapter runs, but the
        adapter itself must still produce a valid DataRequest so the Data
        Agent's INCOMPLETE_REQUEST diagnostic path stays reachable in
        future flows that call the adapter directly."""

        intake = _make_intake(status=status)
        request = intake_report_to_data_request(intake, run_id="run_001")
        assert request.source == "pipeline"
