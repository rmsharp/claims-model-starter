"""End-to-end CLI tests for the standalone Data Agent.

Uses Typer's CliRunner to invoke the ``model-data-agent run`` command with
the ``--fake-llm`` flag so no real API key is required. The fake client
returns a deterministic primary query + QC pair that exercises the full
flow; the output JSON is parsed as a DataReport and inspected.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import sqlalchemy as sa
from model_project_constructor_data_agent.cli import app
from model_project_constructor_data_agent.schemas import DataReport, DataSourceInventory
from typer.testing import CliRunner

FIXTURE_REQUEST = (
    Path(__file__).resolve().parents[1] / "fixtures" / "sample_request.json"
)


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


def test_cli_smoke_fake_llm_no_db(runner: CliRunner, tmp_path: Path) -> None:
    """Fake LLM + no --db-url → COMPLETE report with DB-unreachable concern."""
    out = tmp_path / "report.json"
    result = runner.invoke(
        app,
        [
            "run",
            "--request",
            str(FIXTURE_REQUEST),
            "--output",
            str(out),
            "--fake-llm",
        ],
    )
    assert result.exit_code == 0, result.output
    assert "COMPLETE" in result.output

    report = DataReport.model_validate(json.loads(out.read_text()))
    assert report.status == "COMPLETE"
    assert len(report.primary_queries) == 1
    assert report.primary_queries[0].name == "fake_primary"
    assert any("database unreachable" in c for c in report.data_quality_concerns)
    for qc in report.primary_queries[0].quality_checks:
        assert qc.execution_status == "NOT_EXECUTED"


def test_cli_smoke_fake_llm_with_sqlite(runner: CliRunner, tmp_path: Path) -> None:
    """Fake LLM + live SQLite → QC checks execute against the real DB."""
    import sqlalchemy as sa

    db_path = tmp_path / "smoke.db"
    engine = sa.create_engine(f"sqlite:///{db_path}")
    try:
        with engine.begin() as conn:
            conn.execute(sa.text("CREATE TABLE claims (id INTEGER PRIMARY KEY)"))
            conn.execute(sa.text("INSERT INTO claims (id) VALUES (1), (2), (3)"))
    finally:
        engine.dispose()

    out = tmp_path / "report.json"
    result = runner.invoke(
        app,
        [
            "run",
            "--request",
            str(FIXTURE_REQUEST),
            "--output",
            str(out),
            "--fake-llm",
            "--db-url",
            f"sqlite:///{db_path}",
        ],
    )
    assert result.exit_code == 0, result.output

    report = DataReport.model_validate(json.loads(out.read_text()))
    assert report.status == "COMPLETE"
    assert not any(
        "database unreachable" in c for c in report.data_quality_concerns
    )
    # Fake client asks for SELECT 1 — always passes, one row ⇒ PASSED.
    for qc in report.primary_queries[0].quality_checks:
        assert qc.execution_status == "PASSED"


def test_cli_missing_request_file_errors(runner: CliRunner, tmp_path: Path) -> None:
    out = tmp_path / "report.json"
    result = runner.invoke(
        app,
        [
            "run",
            "--request",
            str(tmp_path / "does_not_exist.json"),
            "--output",
            str(out),
            "--fake-llm",
        ],
    )
    assert result.exit_code != 0
    assert not out.exists()


def test_cli_no_args_shows_help(runner: CliRunner) -> None:
    result = runner.invoke(app, [])
    assert "model-data-agent" in result.output.lower() or "usage" in result.output.lower()


def test_python_dash_m_entrypoint_works() -> None:
    """`python -m model_project_constructor_data_agent --help` should not crash."""
    import subprocess
    import sys

    result = subprocess.run(
        [sys.executable, "-m", "model_project_constructor_data_agent", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "run" in result.stdout.lower()
    assert "discover" in result.stdout.lower()


def _seed_discover_db(db_path: Path, *, with_policies: bool = True) -> str:
    engine = sa.create_engine(f"sqlite:///{db_path}")
    try:
        with engine.begin() as conn:
            conn.execute(
                sa.text("CREATE TABLE claims (claim_id INTEGER PRIMARY KEY, amount REAL)")
            )
            if with_policies:
                conn.execute(
                    sa.text(
                        "CREATE TABLE policies (policy_id INTEGER PRIMARY KEY, state TEXT)"
                    )
                )
    finally:
        engine.dispose()
    return f"sqlite:///{db_path}"


def test_cli_discover_smoke(runner: CliRunner, tmp_path: Path) -> None:
    """``discover`` writes a valid DataSourceInventory JSON."""
    db_url = _seed_discover_db(tmp_path / "discover.db")

    out = tmp_path / "inv.json"
    result = runner.invoke(
        app,
        [
            "discover",
            "--db-url",
            db_url,
            "--output",
            str(out),
        ],
    )
    assert result.exit_code == 0, result.output
    assert "2 entries" in result.output

    inv = DataSourceInventory.model_validate(json.loads(out.read_text()))
    fqns = {e.fully_qualified_name for e in inv.entries}
    assert fqns == {"main.claims", "main.policies"}
    assert inv.producers[0].producer_type == "automated"


def test_cli_discover_rank_with_fake_llm(runner: CliRunner, tmp_path: Path) -> None:
    """``discover --rank-with-llm --fake-llm`` populates relevance_score deterministically."""
    db_url = _seed_discover_db(tmp_path / "discover.db", with_policies=False)

    out = tmp_path / "inv.json"
    result = runner.invoke(
        app,
        [
            "discover",
            "--db-url",
            db_url,
            "--output",
            str(out),
            "--rank-with-llm",
            "--fake-llm",
            "--request-context",
            "subrogation recovery",
        ],
    )
    assert result.exit_code == 0, result.output

    inv = DataSourceInventory.model_validate(json.loads(out.read_text()))
    assert len(inv.entries) == 1
    entry = inv.entries[0]
    assert entry.relevance_score == pytest.approx(0.9)
    assert "fake-llm" in (entry.relevance_reason or "")


def test_cli_discover_include_schemas_filter(
    runner: CliRunner, tmp_path: Path
) -> None:
    """``--include-schemas`` filters discovery to the named schemas."""
    db_url = _seed_discover_db(tmp_path / "discover.db")

    out_main = tmp_path / "inv_main.json"
    result_main = runner.invoke(
        app,
        [
            "discover",
            "--db-url",
            db_url,
            "--output",
            str(out_main),
            "--include-schemas",
            "main",
        ],
    )
    assert result_main.exit_code == 0, result_main.output
    inv_main = DataSourceInventory.model_validate(json.loads(out_main.read_text()))
    assert len(inv_main.entries) == 2

    out_empty = tmp_path / "inv_empty.json"
    result_empty = runner.invoke(
        app,
        [
            "discover",
            "--db-url",
            db_url,
            "--output",
            str(out_empty),
            "--include-schemas",
            "nonexistent",
        ],
    )
    assert result_empty.exit_code == 0, result_empty.output
    inv_empty = DataSourceInventory.model_validate(json.loads(out_empty.read_text()))
    assert inv_empty.entries == []
    assert len(inv_empty.producers) == 1


def test_cli_discover_unreachable_db_errors(runner: CliRunner, tmp_path: Path) -> None:
    """discover against an unreachable DB exits non-zero (connect failure)."""
    out = tmp_path / "inv.json"
    result = runner.invoke(
        app,
        [
            "discover",
            "--db-url",
            "postgresql://nobody:nobody@127.0.0.1:1/none",
            "--output",
            str(out),
        ],
    )
    assert result.exit_code != 0
    assert not out.exists()
