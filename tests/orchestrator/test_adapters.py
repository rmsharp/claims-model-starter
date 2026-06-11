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
    intake_qa_pairs_to_inventory,
    intake_report_to_data_request,
)
from model_project_constructor.schemas.v1.common import ModelType
from model_project_constructor.schemas.v1.data import (
    DataSourceEntry,
    DataSourceInventory,
    ProducerMetadata,
)
from model_project_constructor.schemas.v1.intake import (
    EstimatedValue,
    GovernanceMetadata,
    IntakeReport,
    ModelSolution,
    QAPair,
    ValueMeasurementPlan,
)


def _make_intake(
    *,
    model_type: ModelType = "supervised_classification",
    candidate_features: list[str] | None = None,
    target_definition: str = "Binary outcome: did the claim recover?",
    status: str = "COMPLETE",
    qa_pairs: list[QAPair] | None = None,
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
            regulatory_frameworks=["SR_26_2"],
            affects_consumers=True,
            uses_protected_attributes=False,
        ),
        stakeholder_id="stake_001",
        session_id="session_001",
        created_at=datetime.now(UTC),
        questions_asked=7,
        revision_cycles=0,
        qa_pairs=qa_pairs or [],
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


class TestIntakeReportToDataRequestInventory:
    """Phase 3 adapter extension: optional ``data_source_inventory`` kwarg."""

    def _inventory(self) -> DataSourceInventory:
        produced_at = datetime.now(UTC)
        return DataSourceInventory(
            entries=[
                DataSourceEntry(
                    name="claim_events",
                    namespace="public",
                    fully_qualified_name="public.claim_events",
                    entity_kind="table",
                    producer_id="curated:team",
                )
            ],
            producers=[
                ProducerMetadata(
                    producer_id="curated:team",
                    producer_type="curated",
                    produced_at=produced_at,
                )
            ],
            created_at=produced_at,
        )

    def test_default_none_preserves_pre_phase_3_behaviour(self) -> None:
        intake = _make_intake()
        request = intake_report_to_data_request(intake, run_id="run_001")
        assert request.data_source_inventory is None

    def test_inventory_passed_through(self) -> None:
        intake = _make_intake()
        inventory = self._inventory()
        request = intake_report_to_data_request(
            intake, run_id="run_001", data_source_inventory=inventory
        )
        assert request.data_source_inventory is inventory
        assert request.data_source_inventory.entries[0].fully_qualified_name == (
            "public.claim_events"
        )

    def test_empty_inventory_roundtrips(self) -> None:
        empty = DataSourceInventory(
            entries=[], producers=[], created_at=datetime.now(UTC)
        )
        intake = _make_intake()
        request = intake_report_to_data_request(
            intake, run_id="run_001", data_source_inventory=empty
        )
        assert request.data_source_inventory is not None
        assert request.data_source_inventory.entries == []


class TestIntakeReportToDataRequestBaseline:
    """Phase 3 (business-value-capture-plan §5): ``value_measurement_plan``
    projects into ``DataRequest.baseline_metric_*`` fields."""

    def test_no_plan_leaves_baseline_fields_none(self) -> None:
        intake = _make_intake()
        assert intake.value_measurement_plan is None
        request = intake_report_to_data_request(intake, run_id="run_001")
        assert request.baseline_metric_name is None
        assert request.baseline_metric_definition is None
        assert request.baseline_measurement_window is None

    def test_plan_projects_into_baseline_fields(self) -> None:
        plan = ValueMeasurementPlan(
            baseline_metric_name="subro_recovery_rate",
            baseline_metric_definition=(
                "subro_recovered_amount / paid_amount across closed claims"
            ),
            baseline_measurement_window="trailing 12 months",
            counterfactual_design="champion_challenger",
            evaluation_horizon_months=6,
        )
        intake = _make_intake()
        intake_with_plan = intake.model_copy(update={"value_measurement_plan": plan})
        request = intake_report_to_data_request(intake_with_plan, run_id="run_001")
        assert request.baseline_metric_name == "subro_recovery_rate"
        assert request.baseline_metric_definition == (
            "subro_recovered_amount / paid_amount across closed claims"
        )
        assert request.baseline_measurement_window == "trailing 12 months"


class TestIntakeQAPairsToInventory:
    """Phase 4: heuristic converter from interview transcript to inventory."""

    def test_no_mentions_returns_empty_entries_with_producer_recorded(self) -> None:
        intake = _make_intake(
            qa_pairs=[
                QAPair(
                    question="What's the business problem?",
                    answer="We need to score outcomes better.",
                ),
            ],
        )
        inv = intake_qa_pairs_to_inventory(intake)
        assert inv.entries == []
        assert len(inv.producers) == 1
        assert inv.producers[0].producer_type == "interview"
        assert inv.producers[0].producer_id == "intake-interview"

    def test_empty_qa_pairs_returns_empty_entries(self) -> None:
        intake = _make_intake(qa_pairs=[])
        inv = intake_qa_pairs_to_inventory(intake)
        assert inv.entries == []
        assert inv.producers[0].producer_type == "interview"

    def test_single_system_mention_emits_one_entry(self) -> None:
        intake = _make_intake(
            qa_pairs=[
                QAPair(
                    question="Which claims system do you use?",
                    answer="We're on Guidewire ClaimCenter for all auto claims.",
                ),
            ],
        )
        inv = intake_qa_pairs_to_inventory(intake)
        assert len(inv.entries) == 1
        entry = inv.entries[0]
        assert entry.name == "Guidewire ClaimCenter"
        assert entry.fully_qualified_name == "Guidewire ClaimCenter"
        assert entry.entity_kind == "other"
        assert entry.source_system == "Guidewire ClaimCenter"
        assert entry.producer_id == "intake-interview"
        assert "auto claims" in (entry.description or "")

    def test_multiple_systems_across_qa_pairs(self) -> None:
        intake = _make_intake(
            qa_pairs=[
                QAPair(
                    question="Where does claims data live?",
                    answer="Guidewire ClaimCenter is the claims admin.",
                ),
                QAPair(
                    question="What about fraud signals?",
                    answer="SIU scores come from the fraud platform.",
                ),
                QAPair(
                    question="Any warehousing?",
                    answer="We ship into the enterprise data warehouse nightly.",
                ),
            ],
        )
        inv = intake_qa_pairs_to_inventory(intake)
        names = {e.name for e in inv.entries}
        assert "Guidewire ClaimCenter" in names
        assert "Fraud / SIU" in names
        assert "Enterprise Data Warehouse" in names

    def test_case_insensitive_substring_match(self) -> None:
        intake = _make_intake(
            qa_pairs=[
                QAPair(
                    question="Q",
                    answer="we use DUCK CREEK for some legacy lines.",
                ),
            ],
        )
        inv = intake_qa_pairs_to_inventory(intake)
        assert [e.name for e in inv.entries] == ["Duck Creek Claims"]

    def test_repeated_mentions_concatenate_into_description(self) -> None:
        intake = _make_intake(
            qa_pairs=[
                QAPair(question="Q1", answer="Subrogation pipeline broke last quarter."),
                QAPair(question="Q2", answer="The subrogation team is rebuilding it."),
            ],
        )
        inv = intake_qa_pairs_to_inventory(intake)
        assert len(inv.entries) == 1
        assert inv.entries[0].name == "Subrogation Recovery"
        assert " | " in (inv.entries[0].description or "")

    def test_producer_id_consistency(self) -> None:
        """Validator at DataSourceInventory:_producer_ids_resolve must accept."""
        intake = _make_intake(
            qa_pairs=[QAPair(question="Q", answer="Guidewire ClaimCenter")],
        )
        inv = intake_qa_pairs_to_inventory(intake)
        producer_ids = {p.producer_id for p in inv.producers}
        for entry in inv.entries:
            assert entry.producer_id in producer_ids

    def test_request_context_cites_stakeholder_and_session(self) -> None:
        intake = _make_intake(
            qa_pairs=[QAPair(question="Q", answer="data lake")],
        )
        inv = intake_qa_pairs_to_inventory(intake)
        assert inv.request_context is not None
        assert intake.stakeholder_id in inv.request_context
        assert intake.session_id in inv.request_context

    def test_round_trips_via_model_dump(self) -> None:
        intake = _make_intake(
            qa_pairs=[
                QAPair(question="Q", answer="Guidewire ClaimCenter + data lake"),
            ],
        )
        inv = intake_qa_pairs_to_inventory(intake)
        round_tripped = DataSourceInventory.model_validate(
            inv.model_dump(mode="json")
        )
        assert round_tripped == inv

    def test_more_specific_alias_wins_over_generic(self) -> None:
        """'guidewire claimcenter' must match the ClaimCenter entry,
        not be diluted by the generic 'claims admin' wording. Order in
        ``_CANONICAL_PC_SYSTEMS`` places specific aliases before generic
        ones; this test pins that contract."""

        intake = _make_intake(
            qa_pairs=[
                QAPair(
                    question="Q",
                    answer="Guidewire ClaimCenter is our claims admin system.",
                ),
            ],
        )
        inv = intake_qa_pairs_to_inventory(intake)
        names = [e.name for e in inv.entries]
        assert "Guidewire ClaimCenter" in names
