"""Data Agent public entry point.

Per §4.2 and §12 of the architecture plan, :meth:`DataAgent.run` must not
raise for expected failures. Every internal error path returns a
:class:`DataReport` whose ``status`` field tells the orchestrator what
happened. Exceptions are reserved for unexpected programming errors; even
those are caught at the outer boundary and surfaced as
``status="EXECUTION_FAILED"`` so a buggy node cannot take down the pipeline.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from model_project_constructor.agents.data.db import ReadOnlyDB
from model_project_constructor.agents.data.graph import build_graph
from model_project_constructor.agents.data.llm import (
    LLMClient,
    PrimaryQuerySpec,
    SummaryResult,
)
from model_project_constructor.schemas.v1.data import (
    DataReport,
    DataRequest,
    Datasheet,
    PrimaryQuery,
    QualityCheck,
)


class DataAgent:
    """Single public entry point for the Data Agent pipeline."""

    def __init__(self, llm: LLMClient, db: ReadOnlyDB | None = None) -> None:
        self._llm = llm
        self._db = db
        self._app = build_graph(llm, db)

    def run(self, request: DataRequest) -> DataReport:
        missing = _missing_semantics(request)
        if missing:
            return _incomplete_report(request, missing)

        initial_state: dict[str, Any] = {
            "request": request,
            "sql_retry_count": 0,
            "db_executed": False,
        }
        try:
            final_state = self._app.invoke(initial_state)
        except Exception as e:
            return _execution_failed_report(request, f"graph crashed: {e}")

        status = final_state.get("status", "EXECUTION_FAILED")
        if status == "EXECUTION_FAILED":
            return _execution_failed_report(
                request,
                final_state.get("failure_reason", "unknown failure"),
            )
        return _assemble_complete_report(request, final_state)


def _missing_semantics(request: DataRequest) -> list[str]:
    """Catch vacuous-but-schema-valid requests.

    Pydantic already rejects absent required fields; this layer catches
    empty strings and empty lists, which the schema accepts but which leave
    the LLM nothing to work from. Returning a non-empty list triggers the
    INCOMPLETE_REQUEST path described in §4.2.
    """
    missing: list[str] = []
    if not request.target_description.strip():
        missing.append("target_description")
    if not request.required_features:
        missing.append("required_features")
    if not request.population_filter.strip():
        missing.append("population_filter")
    if not request.time_range.strip():
        missing.append("time_range")
    return missing


def _incomplete_report(request: DataRequest, missing: list[str]) -> DataReport:
    return DataReport(
        status="INCOMPLETE_REQUEST",
        request=request,
        primary_queries=[],
        summary=(
            "DataRequest is missing or vacuous in required fields: "
            + ", ".join(missing)
        ),
        confirmed_expectations=[],
        unconfirmed_expectations=[],
        data_quality_concerns=[f"missing_field:{m}" for m in missing],
        created_at=datetime.now(timezone.utc),
    )


def _execution_failed_report(request: DataRequest, reason: str) -> DataReport:
    return DataReport(
        status="EXECUTION_FAILED",
        request=request,
        primary_queries=[],
        summary=f"Data Agent run failed: {reason}",
        confirmed_expectations=[],
        unconfirmed_expectations=[],
        data_quality_concerns=[reason],
        created_at=datetime.now(timezone.utc),
    )


def _assemble_complete_report(
    request: DataRequest, final_state: dict[str, Any]
) -> DataReport:
    specs: list[PrimaryQuerySpec] = final_state["primary_query_specs"]
    checks_per_primary: list[list[QualityCheck]] = final_state["quality_checks"]
    datasheets: list[Datasheet] = final_state["datasheets"]
    summary: SummaryResult = final_state["summary_result"]

    primary_queries = [
        PrimaryQuery(
            name=spec.name,
            sql=spec.sql,
            purpose=spec.purpose,
            expected_row_count_order=spec.expected_row_count_order,  # type: ignore[arg-type]
            quality_checks=checks,
            datasheet=sheet,
        )
        for spec, checks, sheet in zip(
            specs, checks_per_primary, datasheets, strict=True
        )
    ]

    data_quality_concerns = list(summary.data_quality_concerns)
    if not final_state.get("db_executed", False):
        data_quality_concerns.append(
            "database unreachable at QC execution time; "
            "quality checks not executed"
        )

    return DataReport(
        status="COMPLETE",
        request=request,
        primary_queries=primary_queries,
        summary=summary.summary,
        confirmed_expectations=list(summary.confirmed_expectations),
        unconfirmed_expectations=list(summary.unconfirmed_expectations),
        data_quality_concerns=data_quality_concerns,
        created_at=datetime.now(timezone.utc),
    )
