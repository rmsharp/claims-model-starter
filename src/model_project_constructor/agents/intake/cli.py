"""typer CLI for the Intake Agent (architecture-plan §14 Phase 3A).

Matches the verification command in §14 literally::

    uv run python -m model_project_constructor.agents.intake \\
        --fixture tests/fixtures/subrogation.yaml

This is a single-command typer app — no ``run`` subcommand — so typer
auto-collapses the command onto the top-level app. That is deliberate:
the data agent's CLI uses ``run`` because it is expected to grow more
subcommands (``execute-qc``, ``datasheet``, ...); the intake agent in
Phase 3A is single-purpose and its plan literal is top-level flags.
Phase 3B (web UI) will add a ``serve`` subcommand if and only if it needs
to share the app, at which point this can be promoted via ``@app.callback``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Optional

import typer

from model_project_constructor.agents.intake.agent import IntakeAgent

app = typer.Typer(add_completion=False, help="Intake Agent CLI (Phase 3A)")


@app.command()
def run(
    fixture: Annotated[
        Optional[Path],
        typer.Option(
            "--fixture",
            help="Path to an intake_fixture/v1 YAML file.",
            exists=True,
            dir_okay=False,
            readable=True,
        ),
    ] = None,
    output: Annotated[
        Optional[Path],
        typer.Option(
            "--output",
            "-o",
            help="Path to write the validated IntakeReport JSON. Default: stdout.",
        ),
    ] = None,
    anthropic: Annotated[
        bool,
        typer.Option(
            "--anthropic",
            help=(
                "Run against a live Anthropic LLM. Not yet wired to an "
                "interactive terminal interviewer in Phase 3A — use --fixture."
            ),
        ),
    ] = False,
) -> None:
    """Run the intake agent (Phase 3A: fixture-driven only)."""

    if anthropic:
        typer.echo(
            "ERROR: --anthropic requires an interactive terminal interviewer "
            "which is not shipped in Phase 3A. Use --fixture for now; the "
            "Phase 3B web UI will provide the interactive path.",
            err=True,
        )
        raise typer.Exit(code=2)

    if fixture is None:
        typer.echo("ERROR: --fixture is required in Phase 3A.", err=True)
        raise typer.Exit(code=2)

    agent = IntakeAgent(llm=_DummyLLM())  # type: ignore[arg-type]
    report = agent.run_with_fixture(str(fixture))

    payload = report.model_dump(mode="json")
    text = json.dumps(payload, indent=2)

    if output is None:
        typer.echo(text)
    else:
        output.write_text(text)
        typer.echo(f"Wrote {output} (status={report.status})")


class _DummyLLM:
    """Placeholder replaced by :meth:`IntakeAgent.run_with_fixture`."""

    def next_question(self, context: object) -> object:  # pragma: no cover
        raise RuntimeError("_DummyLLM should be replaced before use")

    def draft_report(self, context: object) -> object:  # pragma: no cover
        raise RuntimeError("_DummyLLM should be replaced before use")

    def classify_governance(self, draft: object) -> object:  # pragma: no cover
        raise RuntimeError("_DummyLLM should be replaced before use")

    def revise_report(self, draft: object, feedback: str) -> object:  # pragma: no cover
        raise RuntimeError("_DummyLLM should be replaced before use")


__all__ = ["app", "run"]
