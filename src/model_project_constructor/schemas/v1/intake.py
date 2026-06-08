"""Intake Agent output schemas (§5.1 of architecture-plan.md)."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field

from model_project_constructor.schemas.v1.common import (
    CycleTime,
    ModelType,
    RiskTier,
    StrictBase,
)

# Named aliases for the value-section vocabularies. These were inline
# ``Literal``s on the fields below; naming them lets the intake prompt DERIVE
# its enumerations from the same ``Literal`` the validator uses
# (``join_members`` — Overhaul O4 producer single-sourcing) instead of
# hand-listing the members in prose. Kept here in ``intake.py`` (deliberately
# NOT promoted to ``common.py``) — each is used by exactly this schema family,
# and single-sourcing is independent of where the ``Literal`` lives.
Confidence = Literal["low", "medium", "high"]
CounterfactualDesign = Literal[
    "champion_challenger",
    "ab_test",
    "geographic_split",
    "historical_baseline_with_detrending",
    "synthetic_control",
    "regression_discontinuity",
    "none_declared",
]
ReviewCadence = Literal["weekly", "monthly", "quarterly", "ad_hoc"]


class ModelSolution(StrictBase):
    target_variable: str | None
    target_definition: str
    candidate_features: list[str]
    model_type: ModelType
    evaluation_metrics: list[str]
    is_supervised: bool


class EstimatedValue(StrictBase):
    narrative: str
    annual_impact_usd_low: float | None
    annual_impact_usd_high: float | None
    confidence: Confidence
    assumptions: list[str]

    cost_of_inaction_narrative: str | None = None
    annual_cost_of_inaction_usd_low: float | None = None
    annual_cost_of_inaction_usd_high: float | None = None
    implementation_cost_band_usd_low: float | None = None
    implementation_cost_band_usd_high: float | None = None
    payback_months: int | None = None
    value_drivers: list[str] = Field(default_factory=list)


class ValueMeasurementPlan(StrictBase):
    baseline_metric_name: str | None = None
    baseline_metric_definition: str | None = None
    baseline_measurement_window: str | None = None

    counterfactual_design: CounterfactualDesign | None = None
    counterfactual_rationale: str | None = None
    attribution_method_narrative: str | None = None

    evaluation_horizon_months: int | None = None
    logging_requirements: list[str] = Field(default_factory=list)
    review_cadence: ReviewCadence | None = None
    success_criteria: list[str] = Field(default_factory=list)
    decision_rights: str | None = None


class GovernanceMetadata(StrictBase):
    cycle_time: CycleTime
    cycle_time_rationale: str
    risk_tier: RiskTier
    risk_tier_rationale: str
    regulatory_frameworks: list[str]
    affects_consumers: bool
    uses_protected_attributes: bool


class QAPair(StrictBase):
    """A single interview exchange. Published in :class:`IntakeReport.qa_pairs`
    so downstream consumers (e.g. the inventory converter) can scan the raw
    transcript rather than relying on the synthesized report prose."""

    question: str
    answer: str


class IntakeReport(StrictBase):
    schema_version: Literal["1.0.0"] = "1.0.0"
    status: Literal["COMPLETE", "DRAFT_INCOMPLETE"]
    missing_fields: list[str] = Field(default_factory=list)

    business_problem: str
    proposed_solution: str
    model_solution: ModelSolution
    estimated_value: EstimatedValue
    value_measurement_plan: ValueMeasurementPlan | None = None

    governance: GovernanceMetadata

    stakeholder_id: str
    session_id: str
    created_at: datetime
    questions_asked: int
    revision_cycles: int = 0

    qa_pairs: list[QAPair] = Field(default_factory=list)
