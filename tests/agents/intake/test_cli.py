"""CLI tests for the intake agent."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from typer.testing import CliRunner

from model_project_constructor.agents.intake.cli import app

runner = CliRunner()


def test_cli_help_shows_fixture_flag() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "--fixture" in result.stdout


def test_cli_happy_path_stdout(subrogation_fixture_path: Path) -> None:
    result = runner.invoke(app, ["--fixture", str(subrogation_fixture_path)])
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)
    assert payload["status"] == "COMPLETE"
    assert payload["governance"]["risk_tier"] == "tier_3_moderate"


def test_cli_happy_path_output_file(
    subrogation_fixture_path: Path, tmp_path: Path
) -> None:
    out = tmp_path / "report.json"
    result = runner.invoke(
        app,
        ["--fixture", str(subrogation_fixture_path), "--output", str(out)],
    )
    assert result.exit_code == 0, result.stdout
    assert out.exists()
    payload = json.loads(out.read_text())
    assert payload["status"] == "COMPLETE"
    assert f"Wrote {out}" in result.stdout


def test_cli_requires_fixture() -> None:
    result = runner.invoke(app, [])
    assert result.exit_code == 2
    assert "fixture" in result.stdout.lower() or "fixture" in (result.stderr or "").lower()


def test_cli_rejects_anthropic_for_now(subrogation_fixture_path: Path) -> None:
    result = runner.invoke(
        app,
        ["--fixture", str(subrogation_fixture_path), "--anthropic"],
    )
    assert result.exit_code == 2
    output = result.stdout + (result.stderr or "")
    assert "interactive terminal" in output.lower()


def test_cli_revision_cap_fixture_reports_incomplete(
    revision_cap_fixture_path: Path, tmp_path: Path
) -> None:
    out = tmp_path / "rev.json"
    result = runner.invoke(
        app,
        ["--fixture", str(revision_cap_fixture_path), "--output", str(out)],
    )
    assert result.exit_code == 0, result.stdout
    payload = json.loads(out.read_text())
    assert payload["status"] == "DRAFT_INCOMPLETE"
    assert "revision_cap_reached" in payload["missing_fields"]


def test_python_m_entry_point(subrogation_fixture_path: Path) -> None:
    """Run ``python -m model_project_constructor.agents.intake`` end-to-end.

    This matches the plan's §14 Phase 3A verification command literally.
    """

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "model_project_constructor.agents.intake",
            "--fixture",
            str(subrogation_fixture_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["status"] == "COMPLETE"
