"""typer CLI for the Website Agent (architecture-plan §14 Phase 4A/4B).

The plan's literal verification command is::

    uv run python -m model_project_constructor.agents.website \\
        --intake tests/fixtures/subrogation_intake.json \\
        --data tests/fixtures/sample_datareport.json \\
        --fake

Phase 4B adds a real ``python-gitlab`` path: pass ``--private-token``
(and omit ``--fake``) to create an actual project on a GitLab instance.
The default verification mode remains ``--fake`` — no credentials required.

As with the Phase 3A intake CLI, this is a single-command typer app (no
``@app.callback``) so the module literal matches the plan's flags.

``--fake-gitlab``, ``--gitlab-url``, and ``--group-path`` are kept as
hidden deprecated aliases for the Phase A rename window; Phase D removes
them.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Optional

import typer

from model_project_constructor.agents.website.agent import WebsiteAgent
from model_project_constructor.agents.website.fake_client import FakeRepoClient
from model_project_constructor.agents.website.protocol import RepoClient
from model_project_constructor.schemas.v1.data import DataReport
from model_project_constructor.schemas.v1.intake import IntakeReport
from model_project_constructor.schemas.v1.repo import RepoTarget

app = typer.Typer(add_completion=False, help="Website Agent CLI (Phase 4A/4B)")

DEFAULT_NAMESPACE = "data-science/model-drafts"
DEFAULT_HOST_URL = "https://gitlab.example.com"


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
    fake: Annotated[
        bool,
        typer.Option(
            "--fake",
            "--fake-gitlab",
            help="Use the in-memory FakeRepoClient (no credentials required).",
        ),
    ] = False,
    private_token: Annotated[
        Optional[str],
        typer.Option(
            "--private-token",
            help="Host personal access token (required without --fake).",
        ),
    ] = None,
    namespace: Annotated[
        str,
        typer.Option(
            "--namespace",
            "--group-path",
            help="Target namespace (GitLab group path or GitHub owner).",
        ),
    ] = DEFAULT_NAMESPACE,
    host_url: Annotated[
        str,
        typer.Option(
            "--host-url",
            "--gitlab-url",
            help="Repository host base URL.",
        ),
    ] = DEFAULT_HOST_URL,
    output: Annotated[
        Optional[Path],
        typer.Option(
            "--output",
            "-o",
            help="Path to write the RepoProjectResult JSON. Default: stdout.",
        ),
    ] = None,
) -> None:
    """Run the website agent against a seeded intake + data report pair."""

    if not fake and not private_token:
        typer.echo(
            "ERROR: pass either --fake (in-memory) or --private-token "
            "(real host via python-gitlab).",
            err=True,
        )
        raise typer.Exit(code=2)

    intake_report = IntakeReport.model_validate_json(intake.read_text())
    data_report = DataReport.model_validate_json(data.read_text())
    target = RepoTarget(
        host_url=host_url,
        namespace=namespace,
        project_name_hint=intake_report.session_id,
        visibility="private",
    )

    client: RepoClient
    if fake:
        client = FakeRepoClient()
    else:
        # Real adapter. Imported lazily so the fake path stays free of the
        # python-gitlab dependency at import time.
        from model_project_constructor.agents.website.gitlab_adapter import (
            PythonGitLabAdapter,
        )

        assert private_token is not None  # narrowed by the guard above
        client = PythonGitLabAdapter(
            host_url=host_url, private_token=private_token
        )
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
