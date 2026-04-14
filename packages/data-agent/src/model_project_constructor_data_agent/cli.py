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
from model_project_constructor_data_agent.llm import (
    LLMClient,
    PrimaryQuerySpec,
    QualityCheckSpec,
    SummaryResult,
)
from model_project_constructor_data_agent.schemas import (
    DataRequest,
    Datasheet,
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

    agent = DataAgent(llm=llm, db=db)
    report = agent.run(request_obj)

    output.write_text(json.dumps(report.model_dump(mode="json"), indent=2))
    typer.echo(f"wrote {output} ({report.status})")


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


def main() -> Any:
    return app()


if __name__ == "__main__":
    main()
