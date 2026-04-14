"""Data Agent request/report schemas — canonical definitions.

These schemas are the single source of truth for the Data Agent's public API.
The main ``model_project_constructor`` package re-exports them from
``schemas/v1/data.py`` for backward compatibility with pipeline code, but the
authoritative versions live here so the standalone distribution has zero
runtime dependency on the orchestrator.

This module has its own minimal ``StrictBase`` (three lines) so the standalone
wheel is independent of ``model_project_constructor.schemas.v1.common``.
``StrictBase`` in the main package and here are deliberately duplicated — the
coupling cost (two three-line classes) is cheaper than the coupling it would
introduce if either inherited from the other.

Per §7 of ``docs/planning/architecture-plan.md`` this module MUST NOT
reference ``IntakeReport`` or anything under ``schemas.v1.intake``. The
adapter that turns an intake report into a :class:`DataRequest` lives in the
orchestrator, not here.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictBase(BaseModel):
    """Base for every Data Agent schema.

    - ``extra="forbid"`` so typos in producer code fail loudly instead of
      silently dropping fields.
    - ``protected_namespaces=()`` disables Pydantic v2's warning on field names
      that start with ``model_``.
    """

    model_config = ConfigDict(extra="forbid", protected_namespaces=())


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


__all__ = [
    "StrictBase",
    "DataGranularity",
    "DataRequest",
    "QualityCheck",
    "Datasheet",
    "PrimaryQuery",
    "DataReport",
]
