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
    confidence: Literal["low", "medium", "high"]
    assumptions: list[str]


class GovernanceMetadata(StrictBase):
    cycle_time: CycleTime
    cycle_time_rationale: str
    risk_tier: RiskTier
    risk_tier_rationale: str
    regulatory_frameworks: list[str]
    affects_consumers: bool
    uses_protected_attributes: bool


class IntakeReport(StrictBase):
    schema_version: Literal["1.0.0"] = "1.0.0"
    status: Literal["COMPLETE", "DRAFT_INCOMPLETE"]
    missing_fields: list[str] = Field(default_factory=list)

    business_problem: str
    proposed_solution: str
    model_solution: ModelSolution
    estimated_value: EstimatedValue

    governance: GovernanceMetadata

    stakeholder_id: str
    session_id: str
    created_at: datetime
    questions_asked: int
    revision_cycles: int = 0
