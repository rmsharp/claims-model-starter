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
    ResumeInconsistent,
    determine_resume_point,
    run_pipeline,
)
from model_project_constructor.orchestrator.adapters import (
    intake_report_to_data_request,
)
from model_project_constructor.schemas.envelope import HandoffEnvelope
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


# --- Resume-point determination (resume-from-checkpoint-plan §5 truth table)


def _touch_checkpoint(
    base_dir: Path,
    run_id: str,
    *,
    intake: bool = False,
    data_request: bool = False,
    data_report: bool = False,
    repo_target: bool = False,
    result: bool = False,
) -> None:
    """Create empty files at the paths ``CheckpointStore.has`` / ``has_result``
    inspect, without constructing real envelopes.

    ``determine_resume_point`` only reads file existence, not envelope
    contents, so minimal ``touch`` calls are sufficient to exercise
    every row of the §5 truth table without the envelope-construction
    overhead of ``run_pipeline`` integration tests.
    """

    run_dir = base_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    if intake:
        (run_dir / "IntakeReport.json").write_text("{}")
    if data_request:
        (run_dir / "DataRequest.json").write_text("{}")
    if data_report:
        (run_dir / "DataReport.json").write_text("{}")
    if repo_target:
        (run_dir / "RepoTarget.json").write_text("{}")
    if result:
        (run_dir / "RepoProjectResult.result.json").write_text("{}")


class TestDetermineResumePoint:
    """One test per row of `resume-from-checkpoint-plan.md` §5 truth table.

    Six valid rows (S0–S5) plus three INVALID rows (successor present
    without its predecessor). S1–S5 seed real envelopes with
    ``status="COMPLETE"`` payloads because ``determine_resume_point``
    consults saved status to distinguish a completed handoff from a
    FAILED halt artifact (§11 risk #8). S0 and the INVALID rows fire
    before any payload load, so ``touch``-style creation is sufficient
    for those cases.
    """

    def test_s0_empty_dir_returns_intake(self, tmp_path: Path) -> None:
        store = CheckpointStore(tmp_path)
        assert determine_resume_point(store, "run_s0") == "intake"

    def test_s1_only_intake_returns_intake_to_data_adapter(
        self, tmp_path: Path
    ) -> None:
        store = CheckpointStore(tmp_path)
        _seed_envelope(store, "run_s1", "IntakeReport", _load_intake())
        assert determine_resume_point(store, "run_s1") == "intake_to_data_adapter"

    def test_s2_intake_and_data_request_returns_data(self, tmp_path: Path) -> None:
        store = CheckpointStore(tmp_path)
        intake = _load_intake()
        _seed_envelope(store, "run_s2", "IntakeReport", intake)
        _seed_envelope(
            store,
            "run_s2",
            "DataRequest",
            intake_report_to_data_request(intake, "run_s2"),
        )
        assert determine_resume_point(store, "run_s2") == "data"

    def test_s3_through_data_report_returns_website(self, tmp_path: Path) -> None:
        store = CheckpointStore(tmp_path)
        intake = _load_intake()
        _seed_envelope(store, "run_s3", "IntakeReport", intake)
        _seed_envelope(
            store,
            "run_s3",
            "DataRequest",
            intake_report_to_data_request(intake, "run_s3"),
        )
        _seed_envelope(store, "run_s3", "DataReport", _load_data())
        assert determine_resume_point(store, "run_s3") == "website"

    def test_s4_with_saved_repo_target_returns_website(self, tmp_path: Path) -> None:
        """``RepoTarget`` existing does not change the resume point — §6.4's
        ``config wins`` decision means the saved envelope is ignored on
        resume. Same resume point as S3."""

        store = CheckpointStore(tmp_path)
        intake = _load_intake()
        _seed_envelope(store, "run_s4", "IntakeReport", intake)
        _seed_envelope(
            store,
            "run_s4",
            "DataRequest",
            intake_report_to_data_request(intake, "run_s4"),
        )
        _seed_envelope(store, "run_s4", "DataReport", _load_data())
        # RepoTarget is a touch — determine_resume_point never inspects it.
        (tmp_path / "run_s4" / "RepoTarget.json").write_text("{}")
        assert determine_resume_point(store, "run_s4") == "website"

    def test_s5_terminal_result_present_returns_already_complete(
        self, tmp_path: Path
    ) -> None:
        store = CheckpointStore(tmp_path)
        intake = _load_intake()
        _seed_envelope(store, "run_s5", "IntakeReport", intake)
        _seed_envelope(
            store,
            "run_s5",
            "DataRequest",
            intake_report_to_data_request(intake, "run_s5"),
        )
        _seed_envelope(store, "run_s5", "DataReport", _load_data())
        (tmp_path / "run_s5" / "RepoTarget.json").write_text("{}")
        (tmp_path / "run_s5" / "RepoProjectResult.result.json").write_text("{}")
        assert determine_resume_point(store, "run_s5") == "already_complete"

    def test_invalid_result_without_data_report_raises(self, tmp_path: Path) -> None:
        """Truth-table INVALID row: ``R=✓, D=✗``."""

        _touch_checkpoint(tmp_path, "run_invalid_a", result=True)
        store = CheckpointStore(tmp_path)
        with pytest.raises(ResumeInconsistent, match="RepoProjectResult"):
            determine_resume_point(store, "run_invalid_a")

    def test_invalid_data_report_without_data_request_raises(
        self, tmp_path: Path
    ) -> None:
        """Truth-table INVALID row: ``D=✓, Q=✗``."""

        _touch_checkpoint(tmp_path, "run_invalid_b", intake=True, data_report=True)
        store = CheckpointStore(tmp_path)
        with pytest.raises(ResumeInconsistent, match="DataReport"):
            determine_resume_point(store, "run_invalid_b")

    def test_invalid_data_request_without_intake_raises(
        self, tmp_path: Path
    ) -> None:
        """Truth-table INVALID row: ``I=✗`` with successor present
        (``Q=✓``)."""

        _touch_checkpoint(tmp_path, "run_invalid_c", data_request=True)
        store = CheckpointStore(tmp_path)
        with pytest.raises(ResumeInconsistent, match="IntakeReport"):
            determine_resume_point(store, "run_invalid_c")

    def test_failed_data_report_demotes_to_data(self, tmp_path: Path) -> None:
        """§11 risk #8: a ``DataReport`` on disk with ``status="EXECUTION_FAILED"``
        is the halt artifact of a prior ``FAILED_AT_DATA`` run, not a
        completed handoff. The resume point must demote to ``"data"`` so
        the data agent re-executes. Without this, the FAILED report would
        be handed to the website agent — the bug filed as BACKLOG item #1
        from Session 51's live-LLM round-trip (run_id
        ``run_b1_resume_live_1776570556``)."""

        store = CheckpointStore(tmp_path)
        intake = _load_intake()
        request = intake_report_to_data_request(intake, "run_failed_data")
        _seed_envelope(store, "run_failed_data", "IntakeReport", intake)
        _seed_envelope(store, "run_failed_data", "DataRequest", request)
        _seed_envelope(
            store,
            "run_failed_data",
            "DataReport",
            _incomplete_data_report(request),
        )
        assert determine_resume_point(store, "run_failed_data") == "data"

    def test_draft_incomplete_intake_demotes_to_intake(
        self, tmp_path: Path
    ) -> None:
        """§11 risk #8: an ``IntakeReport`` on disk with
        ``status="DRAFT_INCOMPLETE"`` is the halt artifact of a prior
        ``FAILED_AT_INTAKE`` run. The resume point must demote to
        ``"intake"`` so the interview re-executes. Without this, the
        DRAFT_INCOMPLETE report would be adapted to a DataRequest and
        handed to the data agent."""

        store = CheckpointStore(tmp_path)
        _seed_envelope(
            store,
            "run_draft_intake",
            "IntakeReport",
            _draft_incomplete_intake(),
        )
        assert determine_resume_point(store, "run_draft_intake") == "intake"


# --- Resume execution (resume-from-checkpoint-plan §7.2) ----------------


def _seed_envelope(
    store: CheckpointStore,
    run_id: str,
    payload_type: str,
    payload_model: IntakeReport | DataRequest | DataReport,
    *,
    source: Literal["intake", "data", "website", "orchestrator"] = "orchestrator",
    target: Literal["intake", "data", "website"] = "data",
) -> None:
    """Write a real ``HandoffEnvelope`` to the store for resume-execution tests.

    Unlike :func:`_touch_checkpoint` (used by the pure-function tests that
    only read existence), these tests call ``load_payload``, which resolves
    the payload through the schema registry — so the envelope must contain
    a valid payload for the named type.
    """

    envelope = HandoffEnvelope(
        run_id=run_id,
        source_agent=source,
        target_agent=target,
        payload_type=payload_type,
        payload_schema_version="1.0.0",
        payload=payload_model.model_dump(mode="json"),
        created_at=datetime.now(UTC),
        correlation_id=run_id,
    )
    store.save(envelope)


def _make_resume_config(
    tmp_path: Path,
    *,
    run_id: str,
    resume_from: Literal[
        "intake",
        "intake_to_data_adapter",
        "data",
        "website",
        "already_complete",
    ],
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
        resume_from=resume_from,
    )


class TestRunPipelineResume:
    """Phase 2 — ``run_pipeline`` honors ``PipelineConfig.resume_from``.

    Per ``docs/planning/resume-from-checkpoint-plan.md`` §7.2: stages
    earlier than the resume point load their envelopes from disk via
    ``CheckpointStore.load_payload``; the resume point and every stage
    after it re-executes. Halt logic (``FAILED_AT_*``) only fires when
    the stage actually ran — §11 risk #5.
    """

    def test_default_behavior_unchanged_when_resume_from_is_none(
        self, tmp_path: Path
    ) -> None:
        """Happy path with ``resume_from=None`` matches the pre-Phase-2
        contract: every runner is called once and ``resume_point`` is
        ``None`` on the result."""

        intake = _load_intake()
        data = _load_data()
        client = FakeRepoClient()
        agent = WebsiteAgent(client, ci_platform="gitlab")
        config = _make_config(tmp_path, run_id="run_resume_none")

        intake_calls = {"n": 0}
        data_calls = {"n": 0}

        def intake_runner() -> IntakeReport:
            intake_calls["n"] += 1
            return intake

        def data_runner(_req: DataRequest) -> DataReport:
            data_calls["n"] += 1
            return data

        result = run_pipeline(
            config,
            intake_runner=intake_runner,
            data_runner=data_runner,
            website_runner=agent.run,
        )

        assert result.status == "COMPLETE"
        assert result.resume_point is None
        assert intake_calls["n"] == 1
        assert data_calls["n"] == 1

    def test_s1_resume_intake_to_data_adapter_skips_intake_runner(
        self, tmp_path: Path
    ) -> None:
        """S1 — intake envelope on disk; resume at
        ``intake_to_data_adapter``. Intake loads; adapter + data +
        website re-execute."""

        intake = _load_intake()
        data = _load_data()
        run_id = "run_resume_s1"
        pre_store = CheckpointStore(tmp_path / "checkpoints")
        _seed_envelope(pre_store, run_id, "IntakeReport", intake)

        client = FakeRepoClient()
        agent = WebsiteAgent(client, ci_platform="gitlab")
        config = _make_resume_config(
            tmp_path, run_id=run_id, resume_from="intake_to_data_adapter"
        )

        intake_calls = {"n": 0}
        data_calls = {"n": 0}

        def intake_runner() -> IntakeReport:
            intake_calls["n"] += 1
            return intake

        def data_runner(_req: DataRequest) -> DataReport:
            data_calls["n"] += 1
            return data

        result = run_pipeline(
            config,
            intake_runner=intake_runner,
            data_runner=data_runner,
            website_runner=agent.run,
        )

        assert intake_calls["n"] == 0
        assert data_calls["n"] == 1
        assert result.status == "COMPLETE"
        assert result.resume_point == "intake_to_data_adapter"
        assert result.intake_report is not None
        assert result.data_request is not None

    def test_s2_resume_data_loads_request_from_disk_not_adapter(
        self, tmp_path: Path
    ) -> None:
        """S2 — §6.3 decision: on resume from ``data``, the saved
        ``DataRequest`` envelope is ground truth. The data runner sees
        the on-disk request, not a freshly-derived one."""

        intake = _load_intake()
        data = _load_data()
        run_id = "run_resume_s2"
        pre_store = CheckpointStore(tmp_path / "checkpoints")
        _seed_envelope(pre_store, run_id, "IntakeReport", intake)

        # Build a valid DataRequest, then mark it so we can prove the
        # loaded copy (not a fresh adapter output) reached the runner.
        seeded_request = intake_report_to_data_request(intake, run_id)
        tweaked = seeded_request.model_copy(
            update={"source_ref": "pre-seeded-for-s2-test"}
        )
        _seed_envelope(pre_store, run_id, "DataRequest", tweaked, target="data")

        client = FakeRepoClient()
        agent = WebsiteAgent(client, ci_platform="gitlab")
        config = _make_resume_config(tmp_path, run_id=run_id, resume_from="data")

        intake_calls = {"n": 0}
        observed: dict[str, DataRequest | None] = {"req": None}

        def intake_runner() -> IntakeReport:
            intake_calls["n"] += 1
            return intake

        def data_runner(req: DataRequest) -> DataReport:
            observed["req"] = req
            return data

        result = run_pipeline(
            config,
            intake_runner=intake_runner,
            data_runner=data_runner,
            website_runner=agent.run,
        )

        assert intake_calls["n"] == 0
        assert observed["req"] is not None
        assert observed["req"].source_ref == "pre-seeded-for-s2-test"
        assert result.status == "COMPLETE"
        assert result.resume_point == "data"

    def test_s3_resume_website_skips_intake_and_data_runners(
        self, tmp_path: Path
    ) -> None:
        """S3 — intake + request + report on disk; resume at
        ``website``. Only the website runner executes."""

        intake = _load_intake()
        data = _load_data()
        run_id = "run_resume_s3"
        pre_store = CheckpointStore(tmp_path / "checkpoints")
        _seed_envelope(pre_store, run_id, "IntakeReport", intake)
        request = intake_report_to_data_request(intake, run_id)
        _seed_envelope(pre_store, run_id, "DataRequest", request, target="data")
        _seed_envelope(pre_store, run_id, "DataReport", data, target="website")

        client = FakeRepoClient()
        agent = WebsiteAgent(client, ci_platform="gitlab")
        config = _make_resume_config(tmp_path, run_id=run_id, resume_from="website")

        intake_calls = {"n": 0}
        data_calls = {"n": 0}

        def intake_runner() -> IntakeReport:
            intake_calls["n"] += 1
            return intake

        def data_runner(_req: DataRequest) -> DataReport:
            data_calls["n"] += 1
            return data

        result = run_pipeline(
            config,
            intake_runner=intake_runner,
            data_runner=data_runner,
            website_runner=agent.run,
        )

        assert intake_calls["n"] == 0
        assert data_calls["n"] == 0
        assert result.status == "COMPLETE"
        assert result.resume_point == "website"
        assert result.project_result is not None

    def test_halt_under_resume_records_resume_point_on_failure(
        self, tmp_path: Path
    ) -> None:
        """Plan §11 risk #5 regression: a resumed run whose re-executed
        stage fails returns ``FAILED_AT_*`` AND populates
        ``resume_point`` so the operator sees the failure occurred
        inside a resumed invocation."""

        intake = _load_intake()
        run_id = "run_resume_halt_data"
        pre_store = CheckpointStore(tmp_path / "checkpoints")
        _seed_envelope(pre_store, run_id, "IntakeReport", intake)
        request = intake_report_to_data_request(intake, run_id)
        _seed_envelope(pre_store, run_id, "DataRequest", request, target="data")

        config = _make_resume_config(tmp_path, run_id=run_id, resume_from="data")

        website_calls = {"n": 0}

        def website_runner(
            _i: IntakeReport, _d: DataReport, _t: RepoTarget
        ) -> RepoProjectResult:
            website_calls["n"] += 1
            return _failed_repo_project_result("should not be called")

        result = run_pipeline(
            config,
            intake_runner=lambda: intake,
            data_runner=lambda req: _incomplete_data_report(req),
            website_runner=website_runner,
        )

        assert result.status == "FAILED_AT_DATA"
        assert result.resume_point == "data"
        assert result.data_report is not None
        assert result.data_report.status == "EXECUTION_FAILED"
        assert website_calls["n"] == 0

    def test_already_complete_raises_value_error(self, tmp_path: Path) -> None:
        """``resume_from="already_complete"`` is a CLI-layer signal, not
        an executable state. ``run_pipeline`` refuses before touching
        any stage; Phase 3 will translate this to an operator-facing
        exit code + message."""

        config = _make_resume_config(
            tmp_path, run_id="run_already_complete", resume_from="already_complete"
        )

        with pytest.raises(ValueError, match="already_complete"):
            run_pipeline(
                config,
                intake_runner=_load_intake,
                data_runner=lambda _req: _load_data(),
                website_runner=lambda _i, _d, _t: _failed_repo_project_result("n/a"),
            )
