"""typer CLI for the Website Agent (architecture-plan §14 Phase 4 + abstraction Phase D).

The plan's literal verification command is::

    uv run python -m model_project_constructor.agents.website \\
        --intake tests/fixtures/subrogation_intake.json \\
        --data tests/fixtures/sample_datareport.json \\
        --fake

Phase D of the GitHub/GitLab abstraction plan adds the ``--host`` flag
selecting between ``gitlab`` and ``github``. The ``--fake`` path uses the
in-memory :class:`FakeRepoClient`; passing ``--private-token`` drives the
real adapter for the chosen host (``python-gitlab`` for GitLab,
``PyGithub`` for GitHub). ``--ci-platform`` overrides the CI emission
platform independently of the repo host (useful for fake-path testing).

As with the Phase 3A intake CLI, this is a single-command typer app (no
``@app.callback``) so the module literal matches the plan's flags.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Literal, cast

import typer

from model_project_constructor.agents.website.agent import WebsiteAgent
from model_project_constructor.agents.website.fake_client import FakeRepoClient
from model_project_constructor.agents.website.protocol import RepoClient
from model_project_constructor.schemas.v1.data import DataReport
from model_project_constructor.schemas.v1.intake import IntakeReport
from model_project_constructor.schemas.v1.repo import RepoTarget

app = typer.Typer(add_completion=False, help="Website Agent CLI")

DEFAULT_NAMESPACE = "data-science/model-drafts"
GITLAB_DEFAULT_HOST_URL = "https://gitlab.com"
GITHUB_DEFAULT_HOST_URL = "https://api.github.com"

VALID_HOSTS: frozenset[str] = frozenset({"gitlab", "github"})
VALID_CI_PLATFORMS: frozenset[str] = frozenset({"gitlab", "github"})


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
    host: Annotated[
        str,
        typer.Option(
            "--host",
            help="Repository host: 'gitlab' or 'github'.",
        ),
    ] = "gitlab",
    fake: Annotated[
        bool,
        typer.Option(
            "--fake",
            help="Use the in-memory FakeRepoClient (no credentials required).",
        ),
    ] = False,
    private_token: Annotated[
        str | None,
        typer.Option(
            "--private-token",
            help="Host personal access token (required without --fake).",
        ),
    ] = None,
    namespace: Annotated[
        str,
        typer.Option(
            "--namespace",
            help="Target namespace (GitLab group path or GitHub owner).",
        ),
    ] = DEFAULT_NAMESPACE,
    host_url: Annotated[
        str | None,
        typer.Option(
            "--host-url",
            help=(
                "Repository host base URL. Defaults to "
                f"{GITLAB_DEFAULT_HOST_URL!r} for --host gitlab and "
                f"{GITHUB_DEFAULT_HOST_URL!r} for --host github."
            ),
        ),
    ] = None,
    ci_platform: Annotated[
        str | None,
        typer.Option(
            "--ci-platform",
            help=(
                "Override the emitted CI manifest platform "
                "('gitlab' or 'github'). Defaults to --host."
            ),
        ),
    ] = None,
    output: Annotated[
        Path | None,
        typer.Option(
            "--output",
            "-o",
            help="Path to write the RepoProjectResult JSON. Default: stdout.",
        ),
    ] = None,
) -> None:
    """Run the website agent against a seeded intake + data report pair."""

    if host not in VALID_HOSTS:
        typer.echo(
            f"ERROR: --host must be one of {sorted(VALID_HOSTS)} (got {host!r}).",
            err=True,
        )
        raise typer.Exit(code=2)

    if ci_platform is None:
        ci_platform = host
    elif ci_platform not in VALID_CI_PLATFORMS:
        typer.echo(
            f"ERROR: --ci-platform must be one of {sorted(VALID_CI_PLATFORMS)} "
            f"(got {ci_platform!r}).",
            err=True,
        )
        raise typer.Exit(code=2)

    if not fake and not private_token:
        typer.echo(
            "ERROR: pass either --fake (in-memory) or --private-token "
            "(real host adapter).",
            err=True,
        )
        raise typer.Exit(code=2)

    resolved_host_url: str = host_url if host_url is not None else (
        GITHUB_DEFAULT_HOST_URL if host == "github" else GITLAB_DEFAULT_HOST_URL
    )

    intake_report = IntakeReport.model_validate_json(intake.read_text())
    data_report = DataReport.model_validate_json(data.read_text())
    target = RepoTarget(
        host_url=resolved_host_url,
        namespace=namespace,
        project_name_hint=intake_report.session_id,
        visibility="private",
    )

    client: RepoClient
    if fake:
        client = FakeRepoClient()
    elif host == "gitlab":
        # Lazy-import so `--help` and the fake/github paths don't pull in
        # python-gitlab.
        from model_project_constructor.agents.website.gitlab_adapter import (
            PythonGitLabAdapter,
        )

        assert private_token is not None  # narrowed by the guard above
        client = PythonGitLabAdapter(
            host_url=resolved_host_url, private_token=private_token
        )
    else:  # host == "github" (validated above)
        # Lazy-import so `--help` and the fake/gitlab paths don't pull in
        # PyGithub.
        from model_project_constructor.agents.website.github_adapter import (
            PyGithubAdapter,
        )

        assert private_token is not None
        client = PyGithubAdapter(
            host_url=resolved_host_url, private_token=private_token
        )

    typed_ci_platform = cast(Literal["gitlab", "github"], ci_platform)
    agent = WebsiteAgent(client, ci_platform=typed_ci_platform)
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
