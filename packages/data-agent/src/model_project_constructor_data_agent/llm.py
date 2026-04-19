"""LLM client protocol and intermediate shapes used by Data Agent nodes.

The Data Agent is LLM-provider agnostic: it accepts any object implementing
:class:`LLMClient`. This module defines only the Protocol and intermediate
dataclasses. A concrete ``AnthropicLLMClient`` lives in
:mod:`model_project_constructor_data_agent.anthropic_client`. Tests may
substitute a ``FakeLLMClient`` that returns deterministic responses.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from model_project_constructor_data_agent.schemas import (
    DataRequest,
    Datasheet,
    QualityCheck,
)


@dataclass(frozen=True)
class PrimaryQuerySpec:
    """LLM output shape for a primary data-collection query.

    The ``expected_row_count_order`` value must be one of the four literals
    accepted by
    :attr:`model_project_constructor_data_agent.schemas.PrimaryQuery.expected_row_count_order`
    (``"tens"``, ``"hundreds"``, ``"thousands"``, ``"millions"``). It is typed
    as ``str`` here to keep the intermediate shape simple; the downstream
    pydantic model is the enforcer.
    """

    name: str
    sql: str
    purpose: str
    expected_row_count_order: str


@dataclass(frozen=True)
class QualityCheckSpec:
    """LLM output shape for a single quality check before execution."""

    check_name: str
    check_sql: str
    expectation: str


@dataclass(frozen=True)
class SummaryResult:
    """LLM output shape for the SUMMARIZE node."""

    summary: str
    confirmed_expectations: list[str]
    unconfirmed_expectations: list[str]
    data_quality_concerns: list[str]


@dataclass(frozen=True)
class TableRanking:
    """LLM output shape for one ranked entry from ``rank_candidate_tables``.

    Emitted by LLM clients that implement the optional
    ``rank_candidate_tables`` method (hasattr-dispatched by
    ``discovery.probe_information_schema``). Not every ``LLMClient`` is
    required to support ranking — query-generation-only clients can omit
    the method.
    """

    fully_qualified_name: str
    relevance_score: float
    relevance_reason: str


@runtime_checkable
class LLMClient(Protocol):
    """Protocol every concrete LLM integration must satisfy.

    Implementations are responsible for serialising/deserialising prompts and
    parsing structured output; nodes treat these methods as typed oracles.
    """

    def generate_primary_queries(
        self, request: DataRequest, previous_error: str | None = None
    ) -> list[PrimaryQuerySpec]:
        """Return candidate primary queries for the request.

        ``previous_error`` is populated on the RETRY_ONCE branch so the
        implementation can ask the LLM to correct an earlier parse failure.
        """

    def generate_quality_checks(
        self, request: DataRequest, primary_queries: list[PrimaryQuerySpec]
    ) -> list[list[QualityCheckSpec]]:
        """Return one list of quality checks per primary query, in order."""

    def summarize(
        self,
        request: DataRequest,
        primary_queries: list[PrimaryQuerySpec],
        quality_checks: list[list[QualityCheck]],
        db_executed: bool,
    ) -> SummaryResult:
        """Produce the narrative summary block of the DataReport."""

    def generate_datasheet(
        self, request: DataRequest, primary_query: PrimaryQuerySpec
    ) -> Datasheet:
        """Produce a Gebru-2021 datasheet for a single primary query."""
