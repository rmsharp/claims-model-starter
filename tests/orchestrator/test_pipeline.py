"""End-to-end tests for the orchestrator pipeline (architecture-plan §12, §14 Phase 5).

These tests pin:

- **Happy path, both CI platforms**: a real ``WebsiteAgent`` running
  against a ``FakeRepoClient`` under both ``ci_platform="gitlab"`` and
  ``ci_platform="github"`` emits the correct CI file (``.gitlab-ci.yml``
  vs ``.github/workflows/ci.yml``) and NOT the other. Intake and Data
  are stubbed with pre-baked fixtures loaded from disk so the pipeline
  does not need LLMs or databases.
- **Halt behavior for each ``FAILED_AT_*`` path**: intake returns
  ``DRAFT_INCOMPLETE``, data returns ``EXECUTION_FAILED``, website
  returns ``FAILED``. The orchestrator must stop at the right stage,
  set the correct ``PipelineStatus``, and retain the reports produced
  so far.
- **Checkpoints are persisted at every stage** so a crashed run can be
  inspected.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

import pytest

from model_project_constructor.agents.website.agent import WebsiteAgent
from model_project_constructor.agents.website.fake_client import FakeRepoClient
from model_project_constructor.orchestrator import (
    CheckpointStore,
    PipelineConfig,
    PipelineResult,
    run_pipeline,
)
from model_project_constructor.schemas.v1.data import DataReport, DataRequest
from model_project_constructor.schemas.v1.intake import IntakeReport
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


def _load_data() -> DataReport:
    return DataReport.model_validate_json(
        (FIXTURE_DIR / "sample_datareport.json").read_text()
    )


def _make_config(
    tmp_path: Path,
    *,
    run_id: str = "run_orch_001",
) -> PipelineConfig:
    target = RepoTarget(
        host_url="https://fake.host.test",
        namespace="data-science/model-drafts",
        project_name_hint="subrogation_pilot",
        visibility="private",
    )
    return PipelineConfig(
        run_id=run_id,
        repo_target=target,
        checkpoint_dir=tmp_path / "checkpoints",
    )


def _failed_repo_project_result(reason: str) -> RepoProjectResult:
    return RepoProjectResult(
        status="FAILED",
        project_url="",
        project_id="",
        initial_commit_sha="",
        files_created=[],
        governance_manifest=GovernanceManifest(
            model_registry_entry={},
            artifacts_created=[],
            risk_tier="tier_4_low",
            cycle_time="tactical",
            regulatory_mapping={},
        ),
        failure_reason=reason,
    )


def _incomplete_data_report(request: DataRequest) -> DataReport:
    return DataReport(
        status="EXECUTION_FAILED",
        request=request,
        primary_queries=[],
        summary="stub failure",
        confirmed_expectations=[],
        unconfirmed_expectations=[],
        data_quality_concerns=["stub_failure"],
        created_at=datetime.now(UTC),
    )


def _draft_incomplete_intake() -> IntakeReport:
    base = _load_intake()
    data = base.model_dump(mode="json")
    data["status"] = "DRAFT_INCOMPLETE"
    data["missing_fields"] = ["estimated_value.annual_impact_usd_low"]
    return IntakeReport.model_validate(data)


# --- Happy path tests for both CI platforms ------------------------------


class TestHappyPath:
    @pytest.mark.parametrize(
        ("ci_platform", "expected_ci_file", "forbidden_ci_file"),
        [
            ("gitlab", ".gitlab-ci.yml", ".github/workflows/ci.yml"),
            ("github", ".github/workflows/ci.yml", ".gitlab-ci.yml"),
        ],
    )
    def test_run_pipeline_happy_path_emits_correct_ci_file(
        self,
        tmp_path: Path,
        ci_platform: Literal["gitlab", "github"],
        expected_ci_file: str,
        forbidden_ci_file: str,
    ) -> None:
        intake = _load_intake()
        data = _load_data()
        client = FakeRepoClient()
        agent = WebsiteAgent(client, ci_platform=ci_platform)
        config = _make_config(tmp_path, run_id=f"run_{ci_platform}")

        result: PipelineResult = run_pipeline(
            config,
            intake_runner=lambda: intake,
            data_runner=lambda _req: data,
            website_runner=agent.run,
        )

        assert result.status == "COMPLETE", (
            f"expected COMPLETE, got {result.status}: {result.failure_reason}"
        )
        assert result.project_result is not None
        assert result.project_result.status == "COMPLETE"
        assert expected_ci_file in result.project_result.files_created
        assert forbidden_ci_file not in result.project_result.files_created
        assert result.project_url is not None
        assert result.project_url.startswith("https://fake.host.test/")

    def test_happy_path_persists_all_checkpoints(self, tmp_path: Path) -> None:
        intake = _load_intake()
        data = _load_data()
        client = FakeRepoClient()
        agent = WebsiteAgent(client, ci_platform="gitlab")
        config = _make_config(tmp_path, run_id="run_chk_001")

        result = run_pipeline(
            config,
            intake_runner=lambda: intake,
            data_runner=lambda _req: data,
            website_runner=agent.run,
        )
        assert result.status == "COMPLETE"

        store = CheckpointStore(config.checkpoint_dir)
        # Every inter-agent handoff is an envelope.
        assert store.has("run_chk_001", "IntakeReport")
        assert store.has("run_chk_001", "DataRequest")
        assert store.has("run_chk_001", "DataReport")
        assert store.has("run_chk_001", "RepoTarget")
        # The terminal website output is a plain (non-envelope) result.
        assert store.has_result("run_chk_001", "RepoProjectResult")
        assert store.list_payload_types("run_chk_001") == [
            "DataReport",
            "DataRequest",
            "IntakeReport",
            "RepoTarget",
        ]
        assert store.list_result_names("run_chk_001") == ["RepoProjectResult"]

    def test_happy_path_data_request_copies_candidate_features(
        self, tmp_path: Path
    ) -> None:
        """The adapter is transparent on the happy path — the DataRequest
        persisted to the checkpoint store should carry the intake's
        candidate_features verbatim. This pins that future orchestrator
        refactors do not silently drop features."""

        intake = _load_intake()
        data = _load_data()
        client = FakeRepoClient()
        agent = WebsiteAgent(client, ci_platform="gitlab")
        config = _make_config(tmp_path, run_id="run_features")

        run_pipeline(
            config,
            intake_runner=lambda: intake,
            data_runner=lambda _req: data,
            website_runner=agent.run,
        )
        store = CheckpointStore(config.checkpoint_dir)
        request = store.load_payload("run_features", "DataRequest")
        assert isinstance(request, DataRequest)
        assert request.required_features == list(
            intake.model_solution.candidate_features
        )
        assert request.source == "pipeline"
        assert request.source_ref == "run_features"

    def test_happy_path_terminal_result_file_is_valid_repo_project_result(
        self, tmp_path: Path
    ) -> None:
        intake = _load_intake()
        data = _load_data()
        client = FakeRepoClient()
        agent = WebsiteAgent(client, ci_platform="github")
        config = _make_config(tmp_path, run_id="run_terminal")

        run_pipeline(
            config,
            intake_runner=lambda: intake,
            data_runner=lambda _req: data,
            website_runner=agent.run,
        )

        terminal_path = (
            config.checkpoint_dir / "run_terminal" / "RepoProjectResult.result.json"
        )
        assert terminal_path.exists()
        parsed = json.loads(terminal_path.read_text())
        reloaded = RepoProjectResult.model_validate(parsed)
        assert reloaded.status == "COMPLETE"
        assert ".github/workflows/ci.yml" in reloaded.files_created


# --- Halt behavior tests (one per FAILED_AT_* path) ----------------------


class TestHaltPaths:
    def test_halt_at_intake_when_draft_incomplete(self, tmp_path: Path) -> None:
        draft_intake = _draft_incomplete_intake()
        data = _load_data()
        client = FakeRepoClient()
        agent = WebsiteAgent(client, ci_platform="gitlab")
        config = _make_config(tmp_path, run_id="run_halt_intake")

        result = run_pipeline(
            config,
            intake_runner=lambda: draft_intake,
            data_runner=lambda _req: data,
            website_runner=agent.run,
        )
        assert result.status == "FAILED_AT_INTAKE"
        assert result.intake_report is not None
        assert result.intake_report.status == "DRAFT_INCOMPLETE"
        assert result.data_request is None
        assert result.data_report is None
        assert result.project_result is None
        assert result.failure_reason is not None
        assert "DRAFT_INCOMPLETE" in result.failure_reason

        # The intake envelope must still be persisted even on halt —
        # the operator needs to inspect the partial report.
        store = CheckpointStore(config.checkpoint_dir)
        assert store.has("run_halt_intake", "IntakeReport")
        assert not store.has("run_halt_intake", "DataRequest")

    def test_halt_at_data_when_execution_failed(self, tmp_path: Path) -> None:
        intake = _load_intake()
        failing_data_runner = lambda req: _incomplete_data_report(req)  # noqa: E731
        client = FakeRepoClient()
        agent = WebsiteAgent(client, ci_platform="github")
        config = _make_config(tmp_path, run_id="run_halt_data")

        result = run_pipeline(
            config,
            intake_runner=lambda: intake,
            data_runner=failing_data_runner,
            website_runner=agent.run,
        )
        assert result.status == "FAILED_AT_DATA"
        assert result.intake_report is not None
        assert result.data_request is not None
        assert result.data_report is not None
        assert result.data_report.status == "EXECUTION_FAILED"
        assert result.project_result is None
        assert "EXECUTION_FAILED" in (result.failure_reason or "")

        store = CheckpointStore(config.checkpoint_dir)
        assert store.has("run_halt_data", "IntakeReport")
        assert store.has("run_halt_data", "DataRequest")
        assert store.has("run_halt_data", "DataReport")
        # Halt before the RepoTarget envelope is written.
        assert not store.has("run_halt_data", "RepoTarget")
        assert not store.has_result("run_halt_data", "RepoProjectResult")

    def test_halt_at_website_when_project_failed(self, tmp_path: Path) -> None:
        intake = _load_intake()
        data = _load_data()
        config = _make_config(tmp_path, run_id="run_halt_website")

        def failing_website(
            _intake: IntakeReport,
            _data: DataReport,
            _target: RepoTarget,
        ) -> RepoProjectResult:
            return _failed_repo_project_result("stub website failure")

        result = run_pipeline(
            config,
            intake_runner=lambda: intake,
            data_runner=lambda _req: data,
            website_runner=failing_website,
        )
        assert result.status == "FAILED_AT_WEBSITE"
        assert result.project_result is not None
        assert result.project_result.status == "FAILED"
        assert result.failure_reason == "stub website failure"

        store = CheckpointStore(config.checkpoint_dir)
        assert store.has("run_halt_website", "RepoTarget")
        # Terminal result is still persisted even on website failure —
        # the operator wants to inspect the failed project_result.
        assert store.has_result("run_halt_website", "RepoProjectResult")

    def test_halt_at_intake_does_not_call_downstream_agents(
        self, tmp_path: Path
    ) -> None:
        draft_intake = _draft_incomplete_intake()
        config = _make_config(tmp_path, run_id="run_halt_guard")

        data_called = {"count": 0}
        website_called = {"count": 0}

        def data_runner(_req: DataRequest) -> DataReport:
            data_called["count"] += 1
            return _load_data()

        def website_runner(
            _intake: IntakeReport,
            _data: DataReport,
            _target: RepoTarget,
        ) -> RepoProjectResult:
            website_called["count"] += 1
            return _failed_repo_project_result("should not be called")

        result = run_pipeline(
            config,
            intake_runner=lambda: draft_intake,
            data_runner=data_runner,
            website_runner=website_runner,
        )
        assert result.status == "FAILED_AT_INTAKE"
        assert data_called["count"] == 0
        assert website_called["count"] == 0

    def test_halt_at_data_does_not_call_website(self, tmp_path: Path) -> None:
        intake = _load_intake()
        config = _make_config(tmp_path, run_id="run_halt_guard2")

        website_called = {"count": 0}

        def website_runner(
            _intake: IntakeReport,
            _data: DataReport,
            _target: RepoTarget,
        ) -> RepoProjectResult:
            website_called["count"] += 1
            return _failed_repo_project_result("should not be called")

        result = run_pipeline(
            config,
            intake_runner=lambda: intake,
            data_runner=lambda req: _incomplete_data_report(req),
            website_runner=website_runner,
        )
        assert result.status == "FAILED_AT_DATA"
        assert website_called["count"] == 0


class TestPipelineConfig:
    def test_correlation_id_defaults_to_run_id(self, tmp_path: Path) -> None:
        config = _make_config(tmp_path, run_id="run_corr")
        assert config.correlation_id == "run_corr"

    def test_correlation_id_can_be_overridden(self, tmp_path: Path) -> None:
        target = RepoTarget(
            host_url="https://fake.host.test",
            namespace="ns",
            project_name_hint="hint",
            visibility="private",
        )
        config = PipelineConfig(
            run_id="run_corr2",
            repo_target=target,
            checkpoint_dir=tmp_path / "chk",
            correlation_id="trace-abc",
        )
        assert config.correlation_id == "trace-abc"

    def test_project_url_property_returns_none_when_no_result(
        self, tmp_path: Path
    ) -> None:
        draft = _draft_incomplete_intake()
        config = _make_config(tmp_path, run_id="run_url_none")
        result = run_pipeline(
            config,
            intake_runner=lambda: draft,
            data_runner=lambda _req: _load_data(),
            website_runner=lambda _i, _d, _t: _failed_repo_project_result("n/a"),
        )
        assert result.project_url is None
