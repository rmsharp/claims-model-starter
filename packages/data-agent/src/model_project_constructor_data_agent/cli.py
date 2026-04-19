"""Typer CLI for the standalone Data Agent.

Usage::

    model-data-agent run --request request.json --output report.json \\
        --db-url sqlite:///claims.db

``--db-url`` is optional; when omitted, quality checks are still generated
but execution is skipped and every check is marked ``NOT_EXECUTED``. The
resulting DataReport still has ``status="COMPLETE"`` with a data-quality
concern noting the unreachable database (matches the pipeline-mode behavior
described in architecture-plan.md §4.2).

``--model`` overrides the default Claude model
(:data:`anthropic_client.DEFAULT_MODEL`).

``--fake-llm`` substitutes a deterministic fake client. It exists so CI can
exercise the CLI end-to-end without a real API key; analyst users should
leave it off and set ``ANTHROPIC_API_KEY`` in their environment.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import typer

from model_project_constructor_data_agent.agent import DataAgent
from model_project_constructor_data_agent.anthropic_client import (
    DEFAULT_MODEL,
    AnthropicLLMClient,
)
from model_project_constructor_data_agent.db import ReadOnlyDB
from model_project_constructor_data_agent.discovery import probe_information_schema
from model_project_constructor_data_agent.llm import (
    LLMClient,
    PrimaryQuerySpec,
    QualityCheckSpec,
    SummaryResult,
    TableRanking,
)
from model_project_constructor_data_agent.schemas import (
    DataRequest,
    Datasheet,
    DataSourceEntry,
    QualityCheck,
)

app = typer.Typer(
    name="model-data-agent",
    help="Standalone Data Agent — generate SQL, run QC, produce DataReport.",
    no_args_is_help=True,
)


@app.callback()
def _main() -> None:
    """Standalone Data Agent CLI — see ``run --help`` for options."""


@app.command()
def run(
    request: Path = typer.Option(
        ...,
        "--request",
        "-r",
        exists=True,
        dir_okay=False,
        readable=True,
        help="Path to a DataRequest JSON file.",
    ),
    output: Path = typer.Option(
        ...,
        "--output",
        "-o",
        dir_okay=False,
        writable=True,
        help="Path to write the DataReport JSON output.",
    ),
    db_url: str | None = typer.Option(
        None,
        "--db-url",
        help=(
            "SQLAlchemy URL for the read-only database. If omitted, quality "
            "checks are generated but not executed."
        ),
    ),
    model: str = typer.Option(
        DEFAULT_MODEL,
        "--model",
        help="Claude model name for the Anthropic client.",
    ),
    fake_llm: bool = typer.Option(
        False,
        "--fake-llm",
        help="Use a deterministic fake LLM client (CI / smoke-test only).",
        hidden=False,
    ),
) -> None:
    """Run the Data Agent end-to-end on a request and write a DataReport."""
    request_obj = _load_request(request)
    llm = _build_llm(fake_llm=fake_llm, model=model)
    db = ReadOnlyDB(db_url) if db_url else None

    try:
        agent = DataAgent(llm=llm, db=db)
        report = agent.run(request_obj)
    finally:
        if db is not None:
            db.close()

    output.write_text(json.dumps(report.model_dump(mode="json"), indent=2))
    typer.echo(f"wrote {output} ({report.status})")


@app.command()
def discover(
    db_url: str = typer.Option(
        ...,
        "--db-url",
        help="SQLAlchemy URL for the database to probe (read-only role recommended).",
    ),
    output: Path = typer.Option(
        ...,
        "--output",
        "-o",
        dir_okay=False,
        writable=True,
        help="Path to write the DataSourceInventory JSON.",
    ),
    include_schemas: list[str] = typer.Option(
        [],
        "--include-schemas",
        help=(
            "Repeatable: limit discovery to these schemas. Default: every "
            "accessible schema except information_schema / pg_catalog."
        ),
    ),
    rank_with_llm: bool = typer.Option(
        False,
        "--rank-with-llm",
        help="Ask the LLM to rank each table's relevance to --request-context.",
    ),
    request_context: str | None = typer.Option(
        None,
        "--request-context",
        help=(
            "Free-text description of the downstream request; fed to the "
            "LLM when --rank-with-llm is set."
        ),
    ),
    model: str = typer.Option(
        DEFAULT_MODEL,
        "--model",
        help="Claude model for --rank-with-llm.",
    ),
    fake_llm: bool = typer.Option(
        False,
        "--fake-llm",
        help="Use a deterministic fake LLM client (CI / smoke-test only).",
    ),
) -> None:
    """Probe a database's information_schema and write a DataSourceInventory JSON file."""
    db = ReadOnlyDB(db_url)
    db.connect()
    try:
        llm = (
            _build_llm(fake_llm=fake_llm, model=model) if rank_with_llm else None
        )
        inventory = probe_information_schema(
            db,
            include_schemas=list(include_schemas) if include_schemas else None,
            llm=llm,
            request_context=request_context,
        )
    finally:
        db.close()

    output.write_text(json.dumps(inventory.model_dump(mode="json"), indent=2))
    typer.echo(f"wrote {output} ({len(inventory.entries)} entries)")


def _load_request(path: Path) -> DataRequest:
    data = json.loads(path.read_text())
    return DataRequest.model_validate(data)


def _build_llm(*, fake_llm: bool, model: str) -> LLMClient:
    if fake_llm:
        return _FakeCLIClient()
    return AnthropicLLMClient(model=model)


class _FakeCLIClient:
    """Deterministic LLM stand-in for ``--fake-llm`` CLI smoke tests.

    Returns a single primary query with simple SQL against a ``claims``
    table plus two canned quality checks. Designed to work against the
    seeded SQLite fixture used in CI and to produce a structurally valid
    DataReport even when the database is unreachable.
    """

    def generate_primary_queries(
        self, request: DataRequest, previous_error: str | None = None
    ) -> list[PrimaryQuerySpec]:
        return [
            PrimaryQuerySpec(
                name="fake_primary",
                sql="SELECT 1 AS placeholder",
                purpose="Placeholder query emitted by --fake-llm mode.",
                expected_row_count_order="tens",
            )
        ]

    def generate_quality_checks(
        self, request: DataRequest, primary_queries: list[PrimaryQuerySpec]
    ) -> list[list[QualityCheckSpec]]:
        return [
            [
                QualityCheckSpec(
                    check_name="fake_nonempty",
                    check_sql="SELECT 1",
                    expectation="Placeholder: query returns at least one row.",
                ),
            ]
            for _ in primary_queries
        ]

    def summarize(
        self,
        request: DataRequest,
        primary_queries: list[PrimaryQuerySpec],
        quality_checks: list[list[QualityCheck]],
        db_executed: bool,
    ) -> SummaryResult:
        return SummaryResult(
            summary=(
                "Fake-LLM mode produced a deterministic placeholder report. "
                f"db_executed={db_executed}. No real analysis performed."
            ),
            confirmed_expectations=["fake placeholder satisfied"],
            unconfirmed_expectations=[],
            data_quality_concerns=[],
        )

    def generate_datasheet(
        self, request: DataRequest, primary_query: PrimaryQuerySpec
    ) -> Datasheet:
        return Datasheet(
            motivation="Smoke-test datasheet — not a real analysis.",
            composition="One placeholder row.",
            collection_process="Fake LLM client.",
            preprocessing="None.",
            uses="Smoke test only.",
            known_biases=["placeholder values are not representative"],
            maintenance="Not applicable.",
        )

    def rank_candidate_tables(
        self,
        entries: list[DataSourceEntry],
        request_context: str | None,
    ) -> list[TableRanking]:
        """Deterministic fake ranking: first entry 0.9, each next 0.1 less (floor 0.0)."""
        rankings: list[TableRanking] = []
        for i, entry in enumerate(entries):
            score = max(0.0, 0.9 - 0.1 * i)
            rankings.append(
                TableRanking(
                    fully_qualified_name=entry.fully_qualified_name,
                    relevance_score=score,
                    relevance_reason=f"fake-llm deterministic rank #{i + 1}",
                )
            )
        return rankings


def main() -> Any:
    return app()


if __name__ == "__main__":
    main()
