"""Unit tests for IntakeReport and its nested models (§5.1)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from model_project_constructor.schemas.v1 import (
    EstimatedValue,
    GovernanceMetadata,
    IntakeReport,
    ModelSolution,
)
from tests.schemas.fixtures import (
    make_estimated_value,
    make_governance_metadata,
    make_intake_report,
    make_model_solution,
)


class TestModelSolution:
    def test_happy_path(self) -> None:
        ms = make_model_solution()
        assert ms.is_supervised is True
        assert ms.model_type == "supervised_classification"

    def test_target_variable_may_be_none_for_unsupervised(self) -> None:
        ms = make_model_solution(
            target_variable=None,
            model_type="unsupervised_clustering",
            is_supervised=False,
        )
        assert ms.target_variable is None

    def test_target_variable_is_required(self) -> None:
        """``str | None`` without a default means the caller MUST pass it explicitly
        — even to say ``None``. This enforces a conscious choice for every intake."""
        with pytest.raises(ValidationError) as exc_info:
            ModelSolution(  # type: ignore[call-arg]
                target_definition="x",
                candidate_features=[],
                model_type="supervised_classification",
                evaluation_metrics=[],
                is_supervised=True,
            )
        assert "target_variable" in str(exc_info.value)

    def test_invalid_model_type_rejected(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            make_model_solution(model_type="deep_magic")
        assert "model_type" in str(exc_info.value)

    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            make_model_solution(extra_field="should_fail")
        assert "extra" in str(exc_info.value).lower()


class TestEstimatedValue:
    def test_happy_path(self) -> None:
        ev = make_estimated_value()
        assert ev.confidence == "medium"

    def test_nullable_bounds(self) -> None:
        ev = make_estimated_value(annual_impact_usd_low=None, annual_impact_usd_high=None)
        assert ev.annual_impact_usd_low is None
        assert ev.annual_impact_usd_high is None

    def test_invalid_confidence_rejected(self) -> None:
        with pytest.raises(ValidationError):
            make_estimated_value(confidence="certain")

    def test_assumptions_required(self) -> None:
        with pytest.raises(ValidationError):
            EstimatedValue(  # type: ignore[call-arg]
                narrative="x",
                annual_impact_usd_low=None,
                annual_impact_usd_high=None,
                confidence="low",
            )


class TestGovernanceMetadata:
    def test_happy_path(self) -> None:
        gm = make_governance_metadata()
        assert gm.risk_tier == "tier_3_moderate"
        assert gm.cycle_time == "tactical"

    @pytest.mark.parametrize(
        "tier",
        ["tier_1_critical", "tier_2_high", "tier_3_moderate", "tier_4_low"],
    )
    def test_all_risk_tiers_accepted(self, tier: str) -> None:
        gm = make_governance_metadata(risk_tier=tier)
        assert gm.risk_tier == tier

    @pytest.mark.parametrize(
        "cycle",
        ["strategic", "tactical", "operational", "continuous"],
    )
    def test_all_cycle_times_accepted(self, cycle: str) -> None:
        gm = make_governance_metadata(cycle_time=cycle)
        assert gm.cycle_time == cycle

    def test_invalid_tier_rejected(self) -> None:
        with pytest.raises(ValidationError):
            make_governance_metadata(risk_tier="tier_0_apocalyptic")

    def test_consumer_and_protected_attribute_flags_required(self) -> None:
        with pytest.raises(ValidationError):
            GovernanceMetadata(  # type: ignore[call-arg]
                cycle_time="tactical",
                cycle_time_rationale="x",
                risk_tier="tier_3_moderate",
                risk_tier_rationale="x",
                regulatory_frameworks=[],
            )


class TestIntakeReport:
    def test_happy_path(self) -> None:
        ir = make_intake_report()
        assert ir.schema_version == "1.0.0"
        assert ir.status == "COMPLETE"
        assert ir.missing_fields == []
        assert ir.revision_cycles == 0

    def test_draft_incomplete_with_missing_fields(self) -> None:
        ir = make_intake_report(
            status="DRAFT_INCOMPLETE",
            missing_fields=["estimated_value.annual_impact_usd_high"],
        )
        assert ir.status == "DRAFT_INCOMPLETE"
        assert len(ir.missing_fields) == 1

    def test_invalid_status_rejected(self) -> None:
        with pytest.raises(ValidationError):
            make_intake_report(status="IN_PROGRESS")

    def test_schema_version_is_locked_to_1_0_0(self) -> None:
        """A report built today must declare schema_version 1.0.0. Accepting any
        other value would break the registry lookup."""
        with pytest.raises(ValidationError):
            make_intake_report(schema_version="2.0.0")

    def test_serialization_round_trip(self) -> None:
        original = make_intake_report()
        blob = original.model_dump_json()
        restored = IntakeReport.model_validate_json(blob)
        assert restored == original

    def test_json_round_trip_via_dict(self) -> None:
        original = make_intake_report()
        restored = IntakeReport.model_validate(original.model_dump(mode="json"))
        assert restored == original

    def test_questions_asked_required(self) -> None:
        """The 10-question cap is enforced by the agent, but the *field* must
        be present so the cap can be verified post-hoc."""
        with pytest.raises(ValidationError):
            make_intake_report(questions_asked=None)

    def test_extra_top_level_field_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            make_intake_report(unexpected="nope")
