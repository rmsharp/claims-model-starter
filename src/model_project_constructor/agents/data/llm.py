"""LLM client protocol and intermediate shapes used by Data Agent nodes.

The Data Agent is LLM-provider agnostic: it accepts any object implementing
:class:`LLMClient`. Phase 2A ships only the Protocol and intermediate
dataclasses. A concrete ``AnthropicLLMClient`` is deferred to a later phase
(Phase 2B CLI or Phase 3 intake integration) so the agent can be exercised
end-to-end under tests with a deterministic fake.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from model_project_constructor.schemas.v1.data import (
    DataRequest,
    Datasheet,
    QualityCheck,
)


@dataclass(frozen=True)
class PrimaryQuerySpec:
    """LLM output shape for a primary data-collection query.

    The ``expected_row_count_order`` value must be one of the four literals
    accepted by
    :attr:`model_project_constructor.schemas.v1.data.PrimaryQuery.expected_row_count_order`
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
