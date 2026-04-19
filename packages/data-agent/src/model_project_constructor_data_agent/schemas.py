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

from pydantic import BaseModel, ConfigDict, Field, model_validator


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


class ColumnMetadata(StrictBase):
    name: str
    data_type: str
    nullable: bool | None = None
    description: str | None = None
    is_primary_key: bool = False
    is_foreign_key: bool = False
    foreign_key_target: str | None = None


class ProducerMetadata(StrictBase):
    producer_id: str
    producer_type: Literal["curated", "automated", "interview", "external_catalog"]
    produced_at: datetime
    producer_version: str | None = None
    notes: str | None = None


class DataSourceEntry(StrictBase):
    schema_version: Literal["1.0.0"] = "1.0.0"

    name: str
    namespace: str | None = None
    source_system: str | None = None
    fully_qualified_name: str

    entity_kind: Literal[
        "table", "view", "materialized_view", "file_dataset", "feature_view", "other"
    ]

    columns: list[ColumnMetadata] = Field(default_factory=list)
    primary_key_columns: list[str] = Field(default_factory=list)
    row_count_estimate: int | None = None

    description: str | None = None
    business_domain: str | None = None
    entity_types: list[str] = Field(default_factory=list)

    relevance_score: float | None = None
    relevance_reason: str | None = None

    last_updated_at: datetime | None = None
    refresh_cadence: str | None = None
    access_notes: str | None = None
    owning_team: str | None = None

    producer_id: str

    extra: dict[str, Any] = Field(default_factory=dict)


class DataSourceInventory(StrictBase):
    schema_version: Literal["1.0.0"] = "1.0.0"
    entries: list[DataSourceEntry] = Field(default_factory=list)
    producers: list[ProducerMetadata] = Field(default_factory=list)
    created_at: datetime
    request_context: str | None = None

    @model_validator(mode="after")
    def _producer_ids_resolve(self) -> DataSourceInventory:
        known = {p.producer_id for p in self.producers}
        dangling = sorted({e.producer_id for e in self.entries if e.producer_id not in known})
        if dangling:
            raise ValueError(
                f"DataSourceEntry.producer_id values do not resolve to any "
                f"ProducerMetadata.producer_id: {dangling}. "
                f"Known producers: {sorted(known)}."
            )
        return self


__all__ = [
    "StrictBase",
    "DataGranularity",
    "DataRequest",
    "QualityCheck",
    "Datasheet",
    "PrimaryQuery",
    "DataReport",
    "ColumnMetadata",
    "ProducerMetadata",
    "DataSourceEntry",
    "DataSourceInventory",
]
