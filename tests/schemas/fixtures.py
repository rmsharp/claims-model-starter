"""Reusable valid-payload factories for schema tests.

Keep the happy-path constructors here so individual tests can build on them
(tweak one field, re-validate) without duplicating the full nested structure.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from model_project_constructor.schemas.v1 import (
    DataGranularity,
    DataReport,
    DataRequest,
    Datasheet,
    EstimatedValue,
    GitLabProjectResult,
    GitLabTarget,
    GovernanceManifest,
    GovernanceMetadata,
    IntakeReport,
    ModelSolution,
    PrimaryQuery,
    QualityCheck,
)

FIXED_TS = datetime(2026, 4, 14, 12, 0, 0, tzinfo=timezone.utc)


def make_model_solution(**overrides: Any) -> ModelSolution:
    defaults: dict[str, Any] = dict(
        target_variable="subrogation_success",
        target_definition="1 if claim recovered via subrogation within 365 days, else 0",
        candidate_features=["claim_type", "adjuster_tenure", "loss_state"],
        model_type="supervised_classification",
        evaluation_metrics=["AUC", "precision@k"],
        is_supervised=True,
    )
    defaults.update(overrides)
    return ModelSolution(**defaults)


def make_estimated_value(**overrides: Any) -> EstimatedValue:
    defaults: dict[str, Any] = dict(
        narrative="10% improvement in subrogation recovery across ~50k annual claims.",
        annual_impact_usd_low=500_000.0,
        annual_impact_usd_high=2_000_000.0,
        confidence="medium",
        assumptions=["recovery rate uplift holds under adjuster variation"],
    )
    defaults.update(overrides)
    return EstimatedValue(**defaults)


def make_governance_metadata(**overrides: Any) -> GovernanceMetadata:
    defaults: dict[str, Any] = dict(
        cycle_time="tactical",
        cycle_time_rationale="Quarterly adjuster retraining cadence.",
        risk_tier="tier_3_moderate",
        risk_tier_rationale="Adjuster-in-the-loop decision; reversible.",
        regulatory_frameworks=["SR_11_7", "NAIC_AIS"],
        affects_consumers=False,
        uses_protected_attributes=False,
    )
    defaults.update(overrides)
    return GovernanceMetadata(**defaults)


def make_intake_report(**overrides: Any) -> IntakeReport:
    defaults: dict[str, Any] = dict(
        status="COMPLETE",
        business_problem="Subrogation recovery is down 8% YoY under the new claims system.",
        proposed_solution="Prompt adjusters at intake when a claim is likely subrogatable.",
        model_solution=make_model_solution(),
        estimated_value=make_estimated_value(),
        governance=make_governance_metadata(),
        stakeholder_id="user_42",
        session_id="sess_abc",
        created_at=FIXED_TS,
        questions_asked=7,
    )
    defaults.update(overrides)
    return IntakeReport(**defaults)


def make_data_request(**overrides: Any) -> DataRequest:
    defaults: dict[str, Any] = dict(
        target_description="claim-level subrogation recovery outcome",
        target_granularity=DataGranularity(unit="claim", time_grain="event"),
        required_features=["claim_type", "adjuster_tenure", "loss_state"],
        population_filter="closed auto claims in 2022-2024",
        time_range="2022-01-01 to 2024-12-31",
        source="pipeline",
        source_ref="run_20260414_0001",
    )
    defaults.update(overrides)
    return DataRequest(**defaults)


def make_quality_check(**overrides: Any) -> QualityCheck:
    defaults: dict[str, Any] = dict(
        check_name="null_rate_target",
        check_sql="select count(*) from x where target is null",
        expectation="< 1% nulls",
        execution_status="PASSED",
        result_summary="0.2% null",
        raw_result={"null_count": 104, "total": 52000},
    )
    defaults.update(overrides)
    return QualityCheck(**defaults)


def make_datasheet(**overrides: Any) -> Datasheet:
    defaults: dict[str, Any] = dict(
        motivation="Support subrogation prediction model training.",
        composition="Closed auto claims with outcome labels.",
        collection_process="Extracted from claims warehouse via read-only service account.",
        preprocessing="Dates normalized, PII redacted.",
        uses="Model training and offline evaluation only.",
        known_biases=["geographic skew toward Midwest offices"],
        maintenance="Owned by claims analytics; refreshed monthly.",
    )
    defaults.update(overrides)
    return Datasheet(**defaults)


def make_primary_query(**overrides: Any) -> PrimaryQuery:
    defaults: dict[str, Any] = dict(
        name="subrogation_training_set",
        sql="select * from claims where closed = 1",
        purpose="Training set for subrogation outcome classifier.",
        expected_row_count_order="thousands",
        quality_checks=[make_quality_check()],
        datasheet=make_datasheet(),
    )
    defaults.update(overrides)
    return PrimaryQuery(**defaults)


def make_data_report(**overrides: Any) -> DataReport:
    defaults: dict[str, Any] = dict(
        status="COMPLETE",
        request=make_data_request(),
        primary_queries=[make_primary_query()],
        summary="One primary query, one QC, no execution errors.",
        confirmed_expectations=["target null rate < 1%"],
        unconfirmed_expectations=[],
        data_quality_concerns=[],
        created_at=FIXED_TS,
    )
    defaults.update(overrides)
    return DataReport(**defaults)


def make_gitlab_target(**overrides: Any) -> GitLabTarget:
    defaults: dict[str, Any] = dict(
        gitlab_url="https://gitlab.example.com",
        group_path="data-science/model-drafts",
        project_name_hint="subrogation-recovery",
    )
    defaults.update(overrides)
    return GitLabTarget(**defaults)


def make_governance_manifest(**overrides: Any) -> GovernanceManifest:
    defaults: dict[str, Any] = dict(
        model_registry_entry={"id": "subrogation-recovery", "owner": "claims_analytics"},
        artifacts_created=["governance/model_card.md", "governance/model_registry.json"],
        risk_tier="tier_3_moderate",
        cycle_time="tactical",
        regulatory_mapping={"SR_11_7": ["governance/model_card.md"]},
    )
    defaults.update(overrides)
    return GovernanceManifest(**defaults)


def make_gitlab_project_result(**overrides: Any) -> GitLabProjectResult:
    defaults: dict[str, Any] = dict(
        status="COMPLETE",
        project_url="https://gitlab.example.com/data-science/model-drafts/subrogation-recovery",
        project_id=12345,
        initial_commit_sha="a1b2c3d4e5",
        files_created=["README.md", "pyproject.toml"],
        governance_manifest=make_governance_manifest(),
    )
    defaults.update(overrides)
    return GitLabProjectResult(**defaults)
