"""Tests for the ``--resume`` CLI flag in scripts/run_pipeline.py.

Phase 3 of ``docs/planning/resume-from-checkpoint-plan.md`` (§7.3).
Exercises argparse parsing + the resume-resolution helpers
(``_resume_preflight``, ``_resolve_resume``, ``_handle_already_complete``)
+ the operator-facing exit codes / messages from §7.3.2. No live LLM
calls; ``run_pipeline`` is monkeypatched to capture the constructed
``PipelineConfig`` so the happy-path test can assert ``resume_from`` was
threaded correctly without driving the full Intake → Data → Website
sequence.

Loaded via importlib (matching ``test_run_pipeline_adapter.py``) so the
script's ``main()`` and helpers can be tested without promoting the
script to a package module.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from model_project_constructor.schemas.envelope import HandoffEnvelope

SCRIPT_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "run_pipeline.py"
)


@pytest.fixture(scope="module")
def run_pipeline_module():
    spec = importlib.util.spec_from_file_location(
        "_resume_run_pipeline_under_test", SCRIPT_PATH
    )
    assert spec is not None
    assert spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _envelope_dict(
    run_id: str,
    payload_type: str,
    payload: dict,
    *,
    source: str = "orchestrator",
    target: str = "data",
) -> dict:
    """Build a HandoffEnvelope JSON-able dict for a fixture write.

    Mirrors ``orchestrator.pipeline._envelope`` minus the datetime — we
    use a fixed ISO timestamp so the file content is deterministic.
    """
    env = HandoffEnvelope(
        run_id=run_id,
        source_agent=source,  # type: ignore[arg-type]
        target_agent=target,  # type: ignore[arg-type]
        payload_type=payload_type,
        payload_schema_version="1.0.0",
        payload=payload,
        created_at="2026-04-18T00:00:00Z",
        correlation_id=run_id,
    )
    return json.loads(env.model_dump_json())


def _seed_intake_envelope(run_dir: Path, run_id: str) -> None:
    """Write an IntakeReport envelope from the canonical fixture."""
    fixture = json.loads(
        (Path(__file__).resolve().parents[1] / "fixtures" / "subrogation_intake.json").read_text()
    )
    env = _envelope_dict(run_id, "IntakeReport", fixture)
    (run_dir / "IntakeReport.json").write_text(json.dumps(env))


def _seed_data_request_envelope(run_dir: Path, run_id: str) -> None:
    """Write a minimal DataRequest envelope.

    The schema requires several fields; we copy the request shape out of
    a real run rather than hand-roll it (keeps the test resilient to
    schema field additions).
    """
    payload = {
        "request_id": f"req_{run_id}",
        "source_intake_run_id": run_id,
        "target_variable": "successful_subrogation",
        "target_definition": "Binary outcome: 1 = subrogation succeeded.",
        "target_granularity": "claim",
        "feature_hints": [],
        "training_window_hint": None,
        "constraints": [],
        "context": {},
    }
    env = _envelope_dict(run_id, "DataRequest", payload)
    (run_dir / "DataRequest.json").write_text(json.dumps(env))


def test_argparse_accepts_resume_flag(run_pipeline_module, tmp_path, monkeypatch):
    """`--resume RUN_ID` parses; main() rejects missing dir before any
    pipeline construction. Exercises the argparse declaration + the
    pre-flight rejection in one shot.
    """
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "sys.argv",
        ["run_pipeline.py", "--resume", "smoke_run_id"],
    )
    with pytest.raises(SystemExit) as excinfo:
        run_pipeline_module.main()
    assert excinfo.value.code == 2


def test_resume_preflight_rejects_missing_run_dir(
    run_pipeline_module, tmp_path, capsys
):
    """Pre-flight: --resume on a run_id with no checkpoint dir → exit 2
    + "no checkpoints" message on stderr (plan §6.6 / §8.1).
    """
    with pytest.raises(SystemExit) as excinfo:
        run_pipeline_module._resume_preflight(tmp_path, "ghost_run_id")
    assert excinfo.value.code == 2
    captured = capsys.readouterr()
    assert "no checkpoints" in captured.err
    assert "ghost_run_id" in captured.err
    # Reject message tells operator how to start fresh.
    assert "without --resume" in captured.err


def test_resume_inconsistent_envelopes_exit_2(
    run_pipeline_module, tmp_path, capsys
):
    """A successor envelope without its predecessor (DataReport without
    DataRequest, etc.) should surface ResumeInconsistent and exit 2 with
    a message naming the run_id (plan §5 INVALID rows).
    """
    run_id = "inconsistent_run"
    run_dir = tmp_path / run_id
    run_dir.mkdir(parents=True)
    # DataReport present but DataRequest missing — INVALID per §5.
    (run_dir / "DataReport.json").write_text(
        json.dumps(_envelope_dict(run_id, "DataReport", {"status": "COMPLETE"}))
    )

    with pytest.raises(SystemExit) as excinfo:
        run_pipeline_module._resolve_resume(tmp_path, run_id)
    assert excinfo.value.code == 2
    captured = capsys.readouterr()
    assert "inconsistent envelopes" in captured.err
    assert run_id in captured.err


def test_resume_already_complete_status_complete_exit_0(
    run_pipeline_module, tmp_path, capsys
):
    """S5 case: terminal RepoProjectResult with status=COMPLETE means
    --resume is an idempotent no-op (plan §8.2 (a)). Exit 0 with a
    friendly message naming the project_url.
    """
    run_id = "completed_run"
    run_dir = tmp_path / run_id
    run_dir.mkdir(parents=True)
    # Seed all predecessors so determine_resume_point reaches "already_complete".
    _seed_intake_envelope(run_dir, run_id)
    _seed_data_request_envelope(run_dir, run_id)
    (run_dir / "DataReport.json").write_text(
        json.dumps(_envelope_dict(run_id, "DataReport", {"status": "COMPLETE"}))
    )
    (run_dir / "RepoProjectResult.result.json").write_text(
        json.dumps(
            {
                "status": "COMPLETE",
                "project_url": "https://gitlab.com/group/already-done",
            }
        )
    )

    with pytest.raises(SystemExit) as excinfo:
        run_pipeline_module._resolve_resume(tmp_path, run_id)
    assert excinfo.value.code == 0
    captured = capsys.readouterr()
    assert "already complete" in captured.out
    assert "already-done" in captured.out


def test_resume_already_complete_status_failed_exit_2(
    run_pipeline_module, tmp_path, capsys
):
    """S5 case with status=FAILED: --resume must NOT silently retry the
    website stage. Operator must opt in by deleting the result file
    (plan §8.2 (b)). Exit 2 with the retry recipe.
    """
    run_id = "failed_run"
    run_dir = tmp_path / run_id
    run_dir.mkdir(parents=True)
    _seed_intake_envelope(run_dir, run_id)
    _seed_data_request_envelope(run_dir, run_id)
    (run_dir / "DataReport.json").write_text(
        json.dumps(_envelope_dict(run_id, "DataReport", {"status": "COMPLETE"}))
    )
    (run_dir / "RepoProjectResult.result.json").write_text(
        json.dumps(
            {
                "status": "FAILED",
                "project_url": None,
                "failure_reason": "GitLab API 500",
            }
        )
    )

    with pytest.raises(SystemExit) as excinfo:
        run_pipeline_module._resolve_resume(tmp_path, run_id)
    assert excinfo.value.code == 2
    captured = capsys.readouterr()
    assert "FAILED" in captured.err
    assert "Delete" in captured.err
    assert "RepoProjectResult.result.json" in captured.err


def test_resolve_resume_returns_data_for_S2_seeding(
    run_pipeline_module, tmp_path
):
    """Plan §5 case S2: IntakeReport + DataRequest present, no DataReport
    → resume point is "data". This is the value that ``main()`` threads
    into ``PipelineConfig.resume_from``.
    """
    run_id = "s2_run"
    run_dir = tmp_path / run_id
    run_dir.mkdir(parents=True)
    _seed_intake_envelope(run_dir, run_id)
    _seed_data_request_envelope(run_dir, run_id)

    point = run_pipeline_module._resolve_resume(tmp_path, run_id)
    assert point == "data"


def test_main_threads_resume_from_into_pipeline_config(
    run_pipeline_module, tmp_path, monkeypatch, capsys
):
    """End-to-end: ``--resume <run_id>`` for a S2-seeded checkpoint dir
    constructs a PipelineConfig with ``resume_from="data"`` and the
    resumed run_id. We monkeypatch ``run_pipeline`` to capture the config
    and short-circuit so no live agents fire.
    """
    run_id = "happy_resume_run"
    checkpoint_root = tmp_path / "checkpoints"
    run_dir = checkpoint_root / run_id
    run_dir.mkdir(parents=True)
    _seed_intake_envelope(run_dir, run_id)
    _seed_data_request_envelope(run_dir, run_id)

    captured_calls: dict = {}

    def _fake_run_pipeline(config, **_kwargs):
        captured_calls["config"] = config
        # Return a minimal COMPLETE-shaped result so main() exits 0 cleanly.
        from model_project_constructor.orchestrator.pipeline import PipelineResult

        return PipelineResult(
            run_id=config.run_id,
            status="COMPLETE",
            resume_point=config.resume_from,
        )

    monkeypatch.setattr(run_pipeline_module, "run_pipeline", _fake_run_pipeline)
    monkeypatch.setattr(
        "sys.argv",
        [
            "run_pipeline.py",
            "--resume",
            run_id,
            "--checkpoint-dir",
            str(checkpoint_root),
        ],
    )

    with pytest.raises(SystemExit) as excinfo:
        run_pipeline_module.main()
    assert excinfo.value.code == 0  # COMPLETE → exit 0

    config = captured_calls["config"]
    assert config.run_id == run_id  # --resume overrode auto-generated
    assert config.resume_from == "data"  # S2 → "data"
    assert config.checkpoint_dir == checkpoint_root

    out = capsys.readouterr().out
    assert "RESUMED from: data" in out
    assert "Skipping: intake, intake_to_data_adapter" in out
