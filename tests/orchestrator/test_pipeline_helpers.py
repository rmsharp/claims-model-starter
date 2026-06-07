"""Unit tests for the ``run_pipeline`` decomposition helpers (O1 Phase O1-3).

``run_pipeline`` was decomposed into four private helpers
(``docs/planning/o1-stage-driver-plan.md`` §6.4 / §7.3):

- :func:`pipeline._save` — the four non-terminal envelope saves;
- :func:`pipeline._run_or_load_stage` — the execute-vs-load branch, returning
  ``(payload, executed)`` so the ``FAILED_AT_*`` halt check stays call-site-gated
  on ``executed`` (a LOADED FAILED/DRAFT envelope never re-halts — resume risk #5);
- :func:`pipeline._halt` — the single ``PipelineResult`` return, echoing
  ``resume_point`` on every path;
- :func:`pipeline._derive_data_request` — the inline adapter merge body.

End-to-end behavior is pinned by ``test_pipeline.py``; this file exercises each
helper in isolation so a refactor that subtly changes one (a mis-wired ``Stage``
envelope field, a dropped report on a halt path, a loaded envelope that wrongly
signals a halt) is caught at the unit level.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from model_project_constructor.orchestrator import (
    CheckpointStore,
    PipelineConfig,
    pipeline,
)
from model_project_constructor.orchestrator.adapters import (
    intake_report_to_data_request,
)
from model_project_constructor.schemas.v1.data import DataReport, DataRequest
from model_project_constructor.schemas.v1.intake import IntakeReport, QAPair
from model_project_constructor.schemas.v1.repo import (
    GovernanceManifest,
    RepoProjectResult,
    RepoTarget,
)

FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures"


def _load_intake() -> IntakeReport:
    return IntakeReport.model_validate_json(
        (FIXTURE_DIR / "subrogation_intake.json").read_text()
    )


def _load_datareport() -> DataReport:
    return DataReport.model_validate_json(
        (FIXTURE_DIR / "sample_datareport.json").read_text()
    )


def _repo_target() -> RepoTarget:
    return RepoTarget(
        host_url="https://fake.host.test",
        namespace="data-science/model-drafts",
        project_name_hint="subrogation_pilot",
        visibility="private",
    )


def _draft_incomplete_intake() -> IntakeReport:
    base = _load_intake()
    data = base.model_dump(mode="json")
    data["status"] = "DRAFT_INCOMPLETE"
    data["missing_fields"] = ["estimated_value.annual_impact_usd_low"]
    return IntakeReport.model_validate(data)


def _make_config(
    tmp_path: Path,
    *,
    run_id: str = "run_helpers",
    resume_from: pipeline.ResumePoint | None = None,
) -> PipelineConfig:
    return PipelineConfig(
        run_id=run_id,
        repo_target=_repo_target(),
        checkpoint_dir=tmp_path / "checkpoints",
        resume_from=resume_from,
    )


def _completed_project_result() -> RepoProjectResult:
    return RepoProjectResult(
        status="COMPLETE",
        project_url="https://fake.host.test/data-science/model-drafts/x",
        project_id="42",
        initial_commit_sha="abc123",
        files_created=[".gitlab-ci.yml"],
        governance_manifest=GovernanceManifest(
            model_registry_entry={},
            artifacts_created=[],
            risk_tier="tier_4_low",
            cycle_time="tactical",
            regulatory_mapping={},
        ),
    )


# --- _save -------------------------------------------------------------------


class TestSave:
    """``_save`` builds an orchestrator envelope whose ``target_agent`` and
    ``payload_type`` come from the ``Stage`` (``source_agent`` always
    ``orchestrator``). A mis-wired ``Stage`` row would surface here per stage."""

    def test_intake_envelope_shape(self, tmp_path: Path) -> None:
        store = CheckpointStore(tmp_path)
        config = _make_config(tmp_path, run_id="run_save_intake")
        pipeline._save(
            store, config, stage=pipeline._STAGE_INTAKE, payload=_load_intake()
        )
        env = store.load("run_save_intake", "IntakeReport")
        assert env.source_agent == "orchestrator"
        assert env.target_agent == "data"
        assert env.payload_type == "IntakeReport"
        assert env.correlation_id == "run_save_intake"

    def test_website_repo_target_envelope_shape(self, tmp_path: Path) -> None:
        store = CheckpointStore(tmp_path)
        config = _make_config(tmp_path, run_id="run_save_website")
        pipeline._save(
            store, config, stage=pipeline._STAGE_WEBSITE, payload=config.repo_target
        )
        env = store.load("run_save_website", "RepoTarget")
        assert env.source_agent == "orchestrator"
        assert env.target_agent == "website"
        assert env.payload_type == "RepoTarget"
        # The serialized payload round-trips config.repo_target verbatim.
        assert env.payload == config.repo_target.model_dump(mode="json")

    def test_every_stage_envelope_reflects_its_descriptor_row(
        self, tmp_path: Path
    ) -> None:
        """Driven directly off ``STAGE_ORDER``: each stage's saved envelope must
        carry that row's ``target_agent`` / ``payload_type``. Pins ``_save`` as
        the single source for all four (intake→data, adapter→data,
        data→website, website→website)."""

        store = CheckpointStore(tmp_path)
        config = _make_config(tmp_path, run_id="run_save_all")
        payloads = {
            "IntakeReport": _load_intake(),
            "DataRequest": intake_report_to_data_request(
                _load_intake(), "run_save_all"
            ),
            "DataReport": _load_datareport(),
            "RepoTarget": config.repo_target,
        }
        for stage in pipeline.STAGE_ORDER:
            pipeline._save(
                store, config, stage=stage, payload=payloads[stage.payload_type]
            )
            env = store.load("run_save_all", stage.payload_type)
            assert env.source_agent == "orchestrator"
            assert env.target_agent == stage.target_agent
            assert env.payload_type == stage.payload_type


# --- _halt -------------------------------------------------------------------


class TestHalt:
    """``_halt`` is the single ``PipelineResult`` return; it echoes
    ``resume_point`` and populates exactly the reports passed (others ``None``)."""

    def test_failed_at_intake_sets_only_intake_report(self, tmp_path: Path) -> None:
        config = _make_config(tmp_path, run_id="run_halt_i")
        intake = _draft_incomplete_intake()
        result = pipeline._halt(
            config, "FAILED_AT_INTAKE", failure_reason="boom", intake_report=intake
        )
        assert result.run_id == "run_halt_i"
        assert result.status == "FAILED_AT_INTAKE"
        assert result.failure_reason == "boom"
        assert result.intake_report is intake
        assert result.data_request is None
        assert result.data_report is None
        assert result.project_result is None
        assert result.resume_point is None

    def test_failed_at_data_sets_reports_through_data_only(
        self, tmp_path: Path
    ) -> None:
        config = _make_config(tmp_path, run_id="run_halt_d")
        intake = _load_intake()
        request = intake_report_to_data_request(intake, "run_halt_d")
        report = _load_datareport()
        result = pipeline._halt(
            config,
            "FAILED_AT_DATA",
            failure_reason="x",
            intake_report=intake,
            data_request=request,
            data_report=report,
        )
        assert result.status == "FAILED_AT_DATA"
        assert result.intake_report is intake
        assert result.data_request is request
        assert result.data_report is report
        assert result.project_result is None

    def test_complete_sets_all_reports_and_no_failure(self, tmp_path: Path) -> None:
        config = _make_config(tmp_path, run_id="run_halt_c")
        intake = _load_intake()
        request = intake_report_to_data_request(intake, "run_halt_c")
        report = _load_datareport()
        project = _completed_project_result()
        result = pipeline._halt(
            config,
            "COMPLETE",
            failure_reason=None,
            intake_report=intake,
            data_request=request,
            data_report=report,
            project_result=project,
        )
        assert result.status == "COMPLETE"
        assert result.failure_reason is None
        assert result.intake_report is intake
        assert result.data_request is request
        assert result.data_report is report
        assert result.project_result is project
        assert result.resume_point is None

    def test_resume_point_echoes_config_resume_from(self, tmp_path: Path) -> None:
        config = _make_config(tmp_path, run_id="run_halt_echo", resume_from="data")
        result = pipeline._halt(config, "COMPLETE", failure_reason=None)
        assert result.resume_point == "data"

    def test_resume_point_none_when_not_resuming(self, tmp_path: Path) -> None:
        config = _make_config(tmp_path, run_id="run_halt_echo2")
        result = pipeline._halt(config, "FAILED_AT_INTAKE", failure_reason="z")
        assert result.resume_point is None

    def test_unknown_report_key_raises_type_error(self, tmp_path: Path) -> None:
        """§6.4 key safety: ``PipelineResult`` is a dataclass, so an unknown
        kwarg raises ``TypeError`` at call time — a typo fails loudly rather
        than being silently dropped."""

        config = _make_config(tmp_path, run_id="run_halt_bad")
        with pytest.raises(TypeError):
            pipeline._halt(config, "COMPLETE", failure_reason=None, bogus_report=123)


# --- _run_or_load_stage ------------------------------------------------------


class TestRunOrLoadStage:
    """``_run_or_load_stage`` returns ``(payload, executed)``: executes + saves
    when the stage is at/before the resume point, else loads + ``executed=False``
    so the call-site halt check is skipped (resume risk #5)."""

    def test_executes_and_saves_when_should_run(self, tmp_path: Path) -> None:
        store = CheckpointStore(tmp_path)
        config = _make_config(tmp_path, run_id="run_rol_exec")  # resume_from=None
        intake = _load_intake()
        calls = {"n": 0}

        def execute() -> IntakeReport:
            calls["n"] += 1
            return intake

        payload, executed = pipeline._run_or_load_stage(
            store, config, stage=pipeline._STAGE_INTAKE, execute=execute
        )
        assert executed is True
        assert calls["n"] == 1
        assert payload is intake
        assert store.has("run_rol_exec", "IntakeReport")

    def test_loads_without_executing_when_resuming_past_stage(
        self, tmp_path: Path
    ) -> None:
        store = CheckpointStore(tmp_path)
        seed_config = _make_config(tmp_path, run_id="run_rol_load")
        pipeline._save(
            store, seed_config, stage=pipeline._STAGE_INTAKE, payload=_load_intake()
        )
        config = _make_config(tmp_path, run_id="run_rol_load", resume_from="data")

        def execute() -> IntakeReport:
            raise AssertionError("execute must not be called on the load path")

        payload, executed = pipeline._run_or_load_stage(
            store, config, stage=pipeline._STAGE_INTAKE, execute=execute
        )
        assert executed is False
        assert isinstance(payload, IntakeReport)
        assert payload.status == "COMPLETE"

    def test_loaded_failed_envelope_does_not_signal_halt(
        self, tmp_path: Path
    ) -> None:
        """Resume risk #5: a LOADED ``DRAFT_INCOMPLETE`` envelope returns
        ``executed=False`` so the call-site halt check never fires — it is
        trusted predecessor output. (The status demotion that prevents this
        state on a clean resume lives in ``determine_resume_point``; this pins
        that the helper itself does not re-halt a loaded artifact.)"""

        store = CheckpointStore(tmp_path)
        seed_config = _make_config(tmp_path, run_id="run_rol_failed")
        pipeline._save(
            store,
            seed_config,
            stage=pipeline._STAGE_INTAKE,
            payload=_draft_incomplete_intake(),
        )
        config = _make_config(tmp_path, run_id="run_rol_failed", resume_from="data")

        def execute() -> IntakeReport:
            raise AssertionError("execute must not be called on the load path")

        payload, executed = pipeline._run_or_load_stage(
            store, config, stage=pipeline._STAGE_INTAKE, execute=execute
        )
        assert executed is False
        assert isinstance(payload, IntakeReport)
        assert payload.status == "DRAFT_INCOMPLETE"


# --- _derive_data_request ----------------------------------------------------


class TestDeriveDataRequest:
    """``_derive_data_request`` is the extracted adapter body (kept inline,
    §6.5). The merge contract is pinned end-to-end by ``TestPipelineConfig``;
    these check the extraction is faithful at the unit level."""

    def test_no_inventory_flags_yields_request_without_inventory(
        self, tmp_path: Path
    ) -> None:
        config = _make_config(tmp_path, run_id="run_derive_plain")
        request = pipeline._derive_data_request(_load_intake(), config)
        assert isinstance(request, DataRequest)
        assert request.data_source_inventory is None
        assert request.source == "pipeline"
        assert request.source_ref == "run_derive_plain"

    def test_curated_path_populates_curated_inventory(self, tmp_path: Path) -> None:
        config = PipelineConfig(
            run_id="run_derive_curated",
            repo_target=_repo_target(),
            checkpoint_dir=tmp_path / "checkpoints",
            curated_inventory_path=FIXTURE_DIR / "sample_curated_inventory.json",
        )
        request = pipeline._derive_data_request(_load_intake(), config)
        assert request.data_source_inventory is not None
        producer_types = {
            p.producer_type for p in request.data_source_inventory.producers
        }
        assert producer_types == {"curated"}

    def test_interview_only_populates_inventory(self, tmp_path: Path) -> None:
        """``inventory_from_intake=True`` with no curated path → the interview
        derivation alone populates the inventory (the third merge branch:
        ``inventory = curated or interview`` with ``curated`` None)."""

        intake = _load_intake().model_copy(
            update={
                "qa_pairs": [
                    QAPair(
                        question="Which claims system?",
                        answer="Guidewire ClaimCenter for auto.",
                    ),
                ]
            }
        )
        config = PipelineConfig(
            run_id="run_derive_interview",
            repo_target=_repo_target(),
            checkpoint_dir=tmp_path / "checkpoints",
            inventory_from_intake=True,
        )
        request = pipeline._derive_data_request(intake, config)
        assert request.data_source_inventory is not None
        producer_types = {
            p.producer_type for p in request.data_source_inventory.producers
        }
        assert producer_types == {"interview"}
