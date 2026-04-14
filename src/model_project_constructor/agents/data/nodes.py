"""Pure-function nodes for the Data Agent LangGraph flow (§10.2).

Each ``make_*`` factory returns a callable that takes :class:`DataAgentState`
and returns a partial-update dict — the shape LangGraph merges into state.
Side effects (LLM and database access) are captured by closure rather than
read from state, so the node bodies stay trivially unit-testable.

Flow (from architecture-plan.md §10.2)::

    START ─▶ GENERATE_QUERIES ─▶ GENERATE_QC ─▶ EXECUTE_QC ─▶ SUMMARIZE ─▶ DATASHEET ─▶ END
                   │                              │
                   │ SQL invalid                  │ DB down
                   ▼                              ▼
              RETRY_ONCE                     SKIP_EXECUTION

``RETRY_ONCE`` re-enters ``GENERATE_QUERIES`` with ``previous_error`` set.
``SKIP_EXECUTION`` is handled inside ``execute_qc`` itself: on DB-down it
returns ``db_executed=False`` and leaves every ``QualityCheck`` at
``execution_status="NOT_EXECUTED"``.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from model_project_constructor.agents.data.db import DBConnectionError, ReadOnlyDB
from model_project_constructor.agents.data.llm import LLMClient
from model_project_constructor.agents.data.sql_validation import validate_sql
from model_project_constructor.agents.data.state import DataAgentState
from model_project_constructor.schemas.v1.data import QualityCheck

MAX_SQL_RETRIES = 1


def make_generate_queries(
    llm: LLMClient,
) -> Callable[[DataAgentState], dict[str, Any]]:
    def generate_queries(state: DataAgentState) -> dict[str, Any]:
        request = state["request"]
        previous_error = state.get("invalid_sql_error")
        specs = llm.generate_primary_queries(request, previous_error=previous_error)
        for spec in specs:
            ok, err = validate_sql(spec.sql)
            if not ok:
                return {
                    "primary_query_specs": [],
                    "invalid_sql_error": f"{spec.name}: {err}",
                }
        return {
            "primary_query_specs": list(specs),
            "invalid_sql_error": None,
        }

    return generate_queries


def route_after_generate_queries(state: DataAgentState) -> str:
    if state.get("invalid_sql_error"):
        if state.get("sql_retry_count", 0) < MAX_SQL_RETRIES:
            return "retry_once"
        return "fail_execution"
    return "generate_qc"


def retry_once(state: DataAgentState) -> dict[str, Any]:
    return {"sql_retry_count": state.get("sql_retry_count", 0) + 1}


def fail_execution_invalid_sql(state: DataAgentState) -> dict[str, Any]:
    return {
        "status": "EXECUTION_FAILED",
        "failure_reason": (
            f"invalid SQL after {MAX_SQL_RETRIES} retry attempt(s): "
            f"{state.get('invalid_sql_error', 'unknown')}"
        ),
    }


def make_generate_qc(
    llm: LLMClient,
) -> Callable[[DataAgentState], dict[str, Any]]:
    def generate_qc(state: DataAgentState) -> dict[str, Any]:
        request = state["request"]
        specs = state["primary_query_specs"]
        qc_specs_per_primary = llm.generate_quality_checks(request, specs)
        quality_checks: list[list[QualityCheck]] = []
        for qc_specs in qc_specs_per_primary:
            checks = [
                QualityCheck(
                    check_name=qc.check_name,
                    check_sql=qc.check_sql,
                    expectation=qc.expectation,
                    execution_status="NOT_EXECUTED",
                    result_summary="not yet executed",
                    raw_result=None,
                )
                for qc in qc_specs
            ]
            quality_checks.append(checks)
        return {"quality_checks": quality_checks}

    return generate_qc


def make_execute_qc(
    db: ReadOnlyDB | None,
) -> Callable[[DataAgentState], dict[str, Any]]:
    def execute_qc(state: DataAgentState) -> dict[str, Any]:
        quality_checks = state["quality_checks"]
        if db is None:
            return {"db_executed": False}
        try:
            db.connect()
        except DBConnectionError:
            return {"db_executed": False}

        updated: list[list[QualityCheck]] = []
        for group in quality_checks:
            new_group: list[QualityCheck] = []
            for qc in group:
                try:
                    rows = db.execute(qc.check_sql)
                except Exception as e:
                    new_group.append(
                        QualityCheck(
                            check_name=qc.check_name,
                            check_sql=qc.check_sql,
                            expectation=qc.expectation,
                            execution_status="ERROR",
                            result_summary=f"execution error: {e}",
                            raw_result=None,
                        )
                    )
                    continue
                # Phase 2A interpretation: ≥1 row ⇒ PASSED, 0 rows ⇒ FAILED.
                # This is a coarse proxy for "did the data-presence expectation
                # hold" and is sufficient to exercise all four execution_status
                # values end-to-end. A richer expectation evaluator is future work.
                status = "PASSED" if rows else "FAILED"
                new_group.append(
                    QualityCheck(
                        check_name=qc.check_name,
                        check_sql=qc.check_sql,
                        expectation=qc.expectation,
                        execution_status=status,
                        result_summary=f"{len(rows)} row(s) returned",
                        raw_result={"row_count": len(rows), "sample_rows": rows[:5]},
                    )
                )
            updated.append(new_group)
        return {"quality_checks": updated, "db_executed": True}

    return execute_qc


def make_summarize(
    llm: LLMClient,
) -> Callable[[DataAgentState], dict[str, Any]]:
    def summarize(state: DataAgentState) -> dict[str, Any]:
        request = state["request"]
        specs = state["primary_query_specs"]
        checks = state["quality_checks"]
        db_executed = state.get("db_executed", False)
        result = llm.summarize(
            request,
            specs,
            checks,
            db_executed=db_executed,
        )
        return {"summary_result": result}

    return summarize


def make_datasheet(
    llm: LLMClient,
) -> Callable[[DataAgentState], dict[str, Any]]:
    def datasheet(state: DataAgentState) -> dict[str, Any]:
        request = state["request"]
        specs = state["primary_query_specs"]
        sheets = [llm.generate_datasheet(request, spec) for spec in specs]
        return {"datasheets": sheets, "status": "COMPLETE"}

    return datasheet
