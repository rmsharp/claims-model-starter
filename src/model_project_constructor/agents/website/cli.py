"""typer CLI for the Website Agent (architecture-plan §14 Phase 4A).

The plan's literal verification command is::

    uv run python -m model_project_constructor.agents.website \\
        --intake tests/fixtures/subrogation_intake.json \\
        --data tests/fixtures/sample_datareport.json \\
        --fake-gitlab

The ``--fake-gitlab`` flag is the only supported mode in Phase 4A — a
real ``python-gitlab`` client lands later alongside the retry/backoff
node in Sub-phase 4B.

As with the Phase 3A intake CLI, this is a single-command typer app (no
``@app.callback``) so the module literal matches the plan's flags.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Optional

import typer

from model_project_constructor.agents.website.agent import WebsiteAgent
from model_project_constructor.agents.website.fake_client import FakeGitLabClient
from model_project_constructor.schemas.v1.data import DataReport
from model_project_constructor.schemas.v1.gitlab import GitLabTarget
from model_project_constructor.schemas.v1.intake import IntakeReport

app = typer.Typer(add_completion=False, help="Website Agent CLI (Phase 4A)")

DEFAULT_GROUP = "data-science/model-drafts"
DEFAULT_GITLAB_URL = "https://gitlab.example.com"


@app.command()
def run(
    intake: Annotated[
        Path,
        typer.Option(
            "--intake",
            help="Path to an IntakeReport JSON file (schemas.v1.intake).",
            exists=True,
            dir_okay=False,
            readable=True,
        ),
    ],
    data: Annotated[
        Path,
        typer.Option(
            "--data",
            help="Path to a DataReport JSON file (schemas.v1.data).",
            exists=True,
            dir_okay=False,
            readable=True,
        ),
    ],
    fake_gitlab: Annotated[
        bool,
        typer.Option(
            "--fake-gitlab",
            help="Use the in-memory FakeGitLabClient (Phase 4A only mode).",
        ),
    ] = False,
    group_path: Annotated[
        str,
        typer.Option("--group-path", help="GitLab group path."),
    ] = DEFAULT_GROUP,
    gitlab_url: Annotated[
        str,
        typer.Option("--gitlab-url", help="GitLab base URL."),
    ] = DEFAULT_GITLAB_URL,
    output: Annotated[
        Optional[Path],
        typer.Option(
            "--output",
            "-o",
            help="Path to write the GitLabProjectResult JSON. Default: stdout.",
        ),
    ] = None,
) -> None:
    """Run the website agent against a seeded intake + data report pair."""

    if not fake_gitlab:
        typer.echo(
            "ERROR: Phase 4A only supports --fake-gitlab. A real python-gitlab "
            "client lands in Sub-phase 4B.",
            err=True,
        )
        raise typer.Exit(code=2)

    intake_report = IntakeReport.model_validate_json(intake.read_text())
    data_report = DataReport.model_validate_json(data.read_text())
    target = GitLabTarget(
        gitlab_url=gitlab_url,
        group_path=group_path,
        project_name_hint=intake_report.session_id,
        visibility="private",
    )

    client = FakeGitLabClient()
    agent = WebsiteAgent(client)
    result = agent.run(intake_report, data_report, target)

    tree = _render_file_tree(sorted(result.files_created))
    typer.echo(f"Project: {result.project_url}")
    typer.echo(f"Status:  {result.status}")
    typer.echo(f"Commit:  {result.initial_commit_sha}")
    typer.echo("Files that would have been committed:")
    typer.echo(tree)

    payload = result.model_dump(mode="json")
    text = json.dumps(payload, indent=2)
    if output is None:
        typer.echo(text)
    else:
        output.write_text(text)
        typer.echo(f"Wrote {output} (status={result.status})")


def _render_file_tree(paths: list[str]) -> str:
    """Render a sorted list of paths as an indented tree for CLI display."""

    lines: list[str] = []
    for p in paths:
        parts = p.split("/")
        indent = "  " * (len(parts) - 1)
        lines.append(f"{indent}{parts[-1]}")
    return "\n".join(lines)


__all__ = ["app", "run"]
