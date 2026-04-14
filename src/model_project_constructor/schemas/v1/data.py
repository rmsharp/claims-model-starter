"""Data Agent request/report schemas (§5.2 and §5.3 of architecture-plan.md).

This module MUST NOT import from :mod:`model_project_constructor.schemas.v1.intake`.
The Data Agent is reusable standalone (constraint C4) and knows nothing about
``IntakeReport``. The orchestrator-owned adapter in ``orchestrator/adapters.py``
is the only place that converts intake output into a :class:`DataRequest`.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import Field

from model_project_constructor.schemas.v1.common import StrictBase


class DataGranularity(StrictBase):
    unit: str
    time_grain: Literal["event", "daily", "weekly", "monthly", "quarterly", "annual"]


class DataRequest(StrictBase):
    schema_version: Literal["1.0.0"] = "1.0.0"

    target_description: str
    target_granularity: DataGranularity
    required_features: list[str]
    population_filter: str
    time_range: str

    database_hint: str | None = None
    data_quality_concerns: list[str] = Field(default_factory=list)

    source: Literal["pipeline", "standalone"]
    source_ref: str


class QualityCheck(StrictBase):
    check_name: str
    check_sql: str
    expectation: str
    execution_status: Literal["PASSED", "FAILED", "ERROR", "NOT_EXECUTED"]
    result_summary: str
    raw_result: dict[str, Any] | None = None


class Datasheet(StrictBase):
    """Per Gebru et al. 2021, 'Datasheets for Datasets'."""

    motivation: str
    composition: str
    collection_process: str
    preprocessing: str
    uses: str
    known_biases: list[str]
    maintenance: str


class PrimaryQuery(StrictBase):
    name: str
    sql: str
    purpose: str
    expected_row_count_order: Literal["tens", "hundreds", "thousands", "millions"]
    quality_checks: list[QualityCheck]
    datasheet: Datasheet


class DataReport(StrictBase):
    schema_version: Literal["1.0.0"] = "1.0.0"
    status: Literal["COMPLETE", "INCOMPLETE_REQUEST", "EXECUTION_FAILED"]
    request: DataRequest
    primary_queries: list[PrimaryQuery]
    summary: str
    confirmed_expectations: list[str]
    unconfirmed_expectations: list[str]
    data_quality_concerns: list[str]
    created_at: datetime
