"""LangGraph state container for the Data Agent flow.

Keys are ``total=False`` because nodes populate the state incrementally.
``DataAgent.run`` seeds ``request`` and ``sql_retry_count`` before invoking
the compiled graph; every other key is written by a node.
"""

from __future__ import annotations

from typing import TypedDict

from model_project_constructor.agents.data.llm import (
    PrimaryQuerySpec,
    SummaryResult,
)
from model_project_constructor.schemas.v1.data import (
    DataRequest,
    Datasheet,
    QualityCheck,
)


class DataAgentState(TypedDict, total=False):
    """State dict threaded through every node in the Data Agent graph."""

    request: DataRequest
    primary_query_specs: list[PrimaryQuerySpec]
    sql_retry_count: int
    invalid_sql_error: str | None
    quality_checks: list[list[QualityCheck]]
    db_executed: bool
    summary_result: SummaryResult
    datasheets: list[Datasheet]
    status: str
    failure_reason: str
