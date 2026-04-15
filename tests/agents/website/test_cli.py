"""Tests for the Phase 4A website agent CLI."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from model_project_constructor.agents.website.cli import app

runner = CliRunner()


def test_cli_requires_fake_flag(
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
    # JSON blob at the end parses as a RepoProjectResult dump
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
