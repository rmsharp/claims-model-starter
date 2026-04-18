"""Tests for the website agent CLI (Phase 4A + abstraction Phase D)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from model_project_constructor.agents.website.cli import app
from model_project_constructor.agents.website.fake_client import FakeRepoClient

runner = CliRunner()


# ---------------------------------------------------------------------------
# Phase 4A baseline tests (still apply with the Phase D --host default).
# ---------------------------------------------------------------------------


def test_cli_requires_fake_or_token(
    intake_report_path: Path,
    data_report_path: Path,
) -> None:
    result = runner.invoke(
        app,
        [
            "--intake",
            str(intake_report_path),
            "--data",
            str(data_report_path),
        ],
    )
    assert result.exit_code == 2
    assert "--fake" in (result.stdout + result.stderr)


def test_cli_happy_path_prints_tree_and_result(
    intake_report_path: Path,
    data_report_path: Path,
) -> None:
    result = runner.invoke(
        app,
        [
            "--intake",
            str(intake_report_path),
            "--data",
            str(data_report_path),
            "--fake",
        ],
    )
    assert result.exit_code == 0, result.stdout
    assert "Status:  COMPLETE" in result.stdout
    assert "Files that would have been committed" in result.stdout
    assert "README.md" in result.stdout
    assert "01_business_understanding.qmd" in result.stdout
    json_start = result.stdout.find("{")
    payload = json.loads(result.stdout[json_start:])
    assert payload["status"] == "COMPLETE"
    assert "files_created" in payload


def test_cli_writes_output_file(
    intake_report_path: Path,
    data_report_path: Path,
    tmp_path: Path,
) -> None:
    out = tmp_path / "result.json"
    result = runner.invoke(
        app,
        [
            "--intake",
            str(intake_report_path),
            "--data",
            str(data_report_path),
            "--fake",
            "--output",
            str(out),
        ],
    )
    assert result.exit_code == 0, result.stdout
    assert out.exists()
    payload = json.loads(out.read_text())
    assert payload["status"] == "COMPLETE"
    assert payload["files_created"]


# ---------------------------------------------------------------------------
# Phase D: --host flag fan-out
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("host", "expected_ci", "forbidden_ci"),
    [
        ("gitlab", ".gitlab-ci.yml", ".github/workflows/ci.yml"),
        ("github", ".github/workflows/ci.yml", ".gitlab-ci.yml"),
    ],
)
def test_cli_host_fake_emits_correct_ci_file(
    intake_report_path: Path,
    data_report_path: Path,
    host: str,
    expected_ci: str,
    forbidden_ci: str,
) -> None:
    """`--host {gitlab,github} --fake` derives ci_platform from --host and
    emits the platform's CI file (and only that file)."""

    result = runner.invoke(
        app,
        [
            "--intake",
            str(intake_report_path),
            "--data",
            str(data_report_path),
            "--host",
            host,
            "--fake",
        ],
    )
    assert result.exit_code == 0, result.stdout
    assert "Status:  COMPLETE" in result.stdout

    json_start = result.stdout.find("{")
    payload = json.loads(result.stdout[json_start:])
    files = payload["files_created"]
    assert expected_ci in files
    assert forbidden_ci not in files


def test_cli_ci_platform_overrides_host(
    intake_report_path: Path,
    data_report_path: Path,
) -> None:
    """`--ci-platform github` against `--host gitlab --fake` emits the
    GitHub Actions CI file even though the (fake) repo host is GitLab."""

    result = runner.invoke(
        app,
        [
            "--intake",
            str(intake_report_path),
            "--data",
            str(data_report_path),
            "--host",
            "gitlab",
            "--fake",
            "--ci-platform",
            "github",
        ],
    )
    assert result.exit_code == 0, result.stdout
    json_start = result.stdout.find("{")
    payload = json.loads(result.stdout[json_start:])
    files = payload["files_created"]
    assert ".github/workflows/ci.yml" in files
    assert ".gitlab-ci.yml" not in files


def test_cli_host_bogus_exits_2(
    intake_report_path: Path,
    data_report_path: Path,
) -> None:
    result = runner.invoke(
        app,
        [
            "--intake",
            str(intake_report_path),
            "--data",
            str(data_report_path),
            "--host",
            "bogus",
            "--fake",
        ],
    )
    assert result.exit_code == 2
    assert "--host" in (result.stdout + result.stderr)


def test_cli_ci_platform_bogus_exits_2(
    intake_report_path: Path,
    data_report_path: Path,
) -> None:
    result = runner.invoke(
        app,
        [
            "--intake",
            str(intake_report_path),
            "--data",
            str(data_report_path),
            "--fake",
            "--ci-platform",
            "bogus",
        ],
    )
    assert result.exit_code == 2
    assert "--ci-platform" in (result.stdout + result.stderr)


# ---------------------------------------------------------------------------
# Phase D: real-adapter selection (monkeypatched so no network)
# ---------------------------------------------------------------------------


class _StandinAdapter(FakeRepoClient):
    """FakeRepoClient subclass that records the kwargs the CLI passed in.

    Used to monkeypatch ``PythonGitLabAdapter`` and ``PyGithubAdapter`` so
    the CLI's adapter-selection branch can be exercised end-to-end without
    a real network client. Each subclass keeps its own ``last_init_kwargs``
    class attribute so the two paths can be tested independently in the
    same suite run.
    """

    last_init_kwargs: dict[str, Any] = {}

    def __init__(self, **kwargs: Any) -> None:
        type(self).last_init_kwargs = dict(kwargs)
        super().__init__()


class _StandinGitLabAdapter(_StandinAdapter):
    last_init_kwargs: dict[str, Any] = {}


class _StandinGitHubAdapter(_StandinAdapter):
    last_init_kwargs: dict[str, Any] = {}


def test_cli_host_gitlab_with_token_invokes_python_gitlab_adapter(
    intake_report_path: Path,
    data_report_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _StandinGitLabAdapter.last_init_kwargs = {}
    monkeypatch.setattr(
        "model_project_constructor.agents.website.gitlab_adapter.PythonGitLabAdapter",
        _StandinGitLabAdapter,
    )

    result = runner.invoke(
        app,
        [
            "--intake",
            str(intake_report_path),
            "--data",
            str(data_report_path),
            "--host",
            "gitlab",
            "--private-token",
            "fake-gitlab-token",
        ],
    )
    assert result.exit_code == 0, result.stdout
    assert "Status:  COMPLETE" in result.stdout
    # --host-url omitted → CLI uses the GitLab default (public gitlab.com).
    assert _StandinGitLabAdapter.last_init_kwargs == {
        "host_url": "https://gitlab.com",
        "private_token": "fake-gitlab-token",
    }


def test_cli_host_gitlab_explicit_host_url_override(
    intake_report_path: Path,
    data_report_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Explicit ``--host-url`` (self-hosted GitLab) flows through to the
    adapter kwargs, overriding the public ``gitlab.com`` default."""

    _StandinGitLabAdapter.last_init_kwargs = {}
    monkeypatch.setattr(
        "model_project_constructor.agents.website.gitlab_adapter.PythonGitLabAdapter",
        _StandinGitLabAdapter,
    )

    result = runner.invoke(
        app,
        [
            "--intake",
            str(intake_report_path),
            "--data",
            str(data_report_path),
            "--host",
            "gitlab",
            "--private-token",
            "fake-gitlab-token",
            "--host-url",
            "https://gitlab.example.com",
        ],
    )
    assert result.exit_code == 0, result.stdout
    assert "Status:  COMPLETE" in result.stdout
    assert _StandinGitLabAdapter.last_init_kwargs == {
        "host_url": "https://gitlab.example.com",
        "private_token": "fake-gitlab-token",
    }


def test_cli_host_github_with_token_invokes_pygithub_adapter(
    intake_report_path: Path,
    data_report_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _StandinGitHubAdapter.last_init_kwargs = {}
    monkeypatch.setattr(
        "model_project_constructor.agents.website.github_adapter.PyGithubAdapter",
        _StandinGitHubAdapter,
    )

    result = runner.invoke(
        app,
        [
            "--intake",
            str(intake_report_path),
            "--data",
            str(data_report_path),
            "--host",
            "github",
            "--private-token",
            "fake-github-token",
        ],
    )
    assert result.exit_code == 0, result.stdout
    assert "Status:  COMPLETE" in result.stdout
    # --host-url omitted → CLI uses the GitHub default.
    assert _StandinGitHubAdapter.last_init_kwargs == {
        "host_url": "https://api.github.com",
        "private_token": "fake-github-token",
    }
    # Default ci_platform follows --host github.
    json_start = result.stdout.find("{")
    payload = json.loads(result.stdout[json_start:])
    assert ".github/workflows/ci.yml" in payload["files_created"]
    assert ".gitlab-ci.yml" not in payload["files_created"]


def test_cli_host_github_explicit_host_url_override(
    intake_report_path: Path,
    data_report_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Explicit ``--host-url`` (GitHub Enterprise) flows through to the
    adapter kwargs, overriding the public ``api.github.com`` default."""

    _StandinGitHubAdapter.last_init_kwargs = {}
    monkeypatch.setattr(
        "model_project_constructor.agents.website.github_adapter.PyGithubAdapter",
        _StandinGitHubAdapter,
    )

    result = runner.invoke(
        app,
        [
            "--intake",
            str(intake_report_path),
            "--data",
            str(data_report_path),
            "--host",
            "github",
            "--private-token",
            "fake-github-token",
            "--host-url",
            "https://github.example.com/api/v3",
        ],
    )
    assert result.exit_code == 0, result.stdout
    assert "Status:  COMPLETE" in result.stdout
    assert _StandinGitHubAdapter.last_init_kwargs == {
        "host_url": "https://github.example.com/api/v3",
        "private_token": "fake-github-token",
    }


# ---------------------------------------------------------------------------
# Phase D: removed deprecated aliases
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "removed_flag",
    ["--fake-gitlab", "--gitlab-url", "--group-path"],
)
def test_cli_removed_phase_a_aliases(
    intake_report_path: Path,
    data_report_path: Path,
    removed_flag: str,
) -> None:
    """The Phase A deprecated aliases are gone — typer should reject them
    with a 'No such option' error from click."""

    args = [
        "--intake",
        str(intake_report_path),
        "--data",
        str(data_report_path),
        removed_flag,
    ]
    if removed_flag != "--fake-gitlab":
        args.append("dummy-value")
    args.append("--fake")

    result = runner.invoke(app, args)
    assert result.exit_code != 0
    combined = (result.stdout + result.stderr).lower()
    assert "no such option" in combined or "unrecognized" in combined
