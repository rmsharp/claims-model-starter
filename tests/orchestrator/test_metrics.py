"""Tests for :mod:`model_project_constructor.orchestrator.metrics`.

Phase 6 scope: counts of runs, status distribution, per-agent latency.
These tests exercise the registry directly and via
:func:`make_measured_runner`, and include one end-to-end integration
with :func:`run_pipeline` to demonstrate that wrapped runners compose
cleanly with the Phase 5 orchestrator surface.
"""

from __future__ import annotations

import time
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from model_project_constructor.agents.website.agent import WebsiteAgent
from model_project_constructor.agents.website.fake_client import FakeRepoClient
from model_project_constructor.orchestrator import (
    LatencySamples,
    MetricsRegistry,
    MetricsSnapshot,
    PipelineConfig,
    make_logged_runner,
    make_measured_runner,
    run_pipeline,
)
from model_project_constructor.schemas.v1.data import DataReport
from model_project_constructor.schemas.v1.intake import IntakeReport
from model_project_constructor.schemas.v1.repo import RepoTarget

FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures"


def _load_intake() -> IntakeReport:
    return IntakeReport.model_validate_json(
        (FIXTURE_DIR / "subrogation_intake.json").read_text()
    )


def _load_data() -> DataReport:
    return DataReport.model_validate_json(
        (FIXTURE_DIR / "sample_datareport.json").read_text()
    )


def _make_config(tmp_path: Path, run_id: str = "run_metrics") -> PipelineConfig:
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


class TestLatencySamples:
    def test_fresh_sample_is_empty(self) -> None:
        s = LatencySamples()
        assert s.count == 0
        assert s.total_ms == 0.0
        assert s.max_ms == 0.0
        assert s.mean_ms == 0.0

    def test_record_updates_aggregates(self) -> None:
        s = LatencySamples()
        s.record(10.0)
        s.record(30.0)
        assert s.count == 2
        assert s.total_ms == 40.0
        assert s.max_ms == 30.0
        assert s.mean_ms == 20.0

    def test_max_tracks_largest_sample(self) -> None:
        s = LatencySamples()
        for value in (5.0, 100.0, 1.0, 50.0):
            s.record(value)
        assert s.max_ms == 100.0
        assert s.count == 4


class TestMetricsRegistryBasics:
    def test_fresh_registry_snapshot(self) -> None:
        snap = MetricsRegistry().snapshot()
        assert snap.run_count == 0
        assert snap.status_counts == {}
        assert snap.agent_latency == {}

    def test_record_run_accumulates_status_counts(self) -> None:
        r = MetricsRegistry()
        r.record_run("COMPLETE")
        r.record_run("COMPLETE")
        r.record_run("FAILED_AT_DATA")
        snap = r.snapshot()
        assert snap.run_count == 3
        assert snap.status_counts == {"COMPLETE": 2, "FAILED_AT_DATA": 1}

    def test_record_agent_latency_accumulates(self) -> None:
        r = MetricsRegistry()
        r.record_agent_latency("intake", 12.5)
        r.record_agent_latency("intake", 7.5)
        r.record_agent_latency("data", 100.0)
        snap = r.snapshot()
        assert set(snap.agent_latency.keys()) == {"intake", "data"}
        assert snap.agent_latency["intake"].count == 2
        assert snap.agent_latency["intake"].total_ms == 20.0
        assert snap.agent_latency["intake"].mean_ms == 10.0
        assert snap.agent_latency["data"].count == 1
        assert snap.agent_latency["data"].max_ms == 100.0

    def test_reset_clears_state(self) -> None:
        r = MetricsRegistry()
        r.record_run("COMPLETE")
        r.record_agent_latency("intake", 5.0)
        r.reset()
        snap = r.snapshot()
        assert snap.run_count == 0
        assert snap.status_counts == {}
        assert snap.agent_latency == {}

    def test_snapshot_is_decoupled_from_registry(self) -> None:
        r = MetricsRegistry()
        r.record_run("COMPLETE")
        r.record_agent_latency("intake", 5.0)
        snap = r.snapshot()

        r.record_run("FAILED_AT_DATA")
        r.record_agent_latency("intake", 10.0)

        assert snap.run_count == 1
        assert snap.status_counts == {"COMPLETE": 1}
        assert snap.agent_latency["intake"].count == 1
        assert snap.agent_latency["intake"].total_ms == 5.0

    def test_snapshot_is_frozen_dataclass(self) -> None:
        snap = MetricsRegistry().snapshot()
        assert isinstance(snap, MetricsSnapshot)
        with pytest.raises(FrozenInstanceError):
            snap.run_count = 99  # type: ignore[misc]


class TestMakeMeasuredRunner:
    def test_records_latency_on_success(self) -> None:
        r = MetricsRegistry()

        def runner() -> str:
            time.sleep(0.001)
            return "ok"

        wrapped = make_measured_runner(runner, agent_name="intake", registry=r)
        assert wrapped() == "ok"

        snap = r.snapshot()
        assert snap.agent_latency["intake"].count == 1
        assert snap.agent_latency["intake"].total_ms > 0.0

    def test_records_latency_even_on_exception(self) -> None:
        r = MetricsRegistry()

        def runner() -> None:
            raise RuntimeError("boom")

        wrapped = make_measured_runner(runner, agent_name="data", registry=r)
        with pytest.raises(RuntimeError, match="boom"):
            wrapped()

        snap = r.snapshot()
        assert snap.agent_latency["data"].count == 1

    def test_multiple_calls_accumulate(self) -> None:
        r = MetricsRegistry()

        def runner() -> int:
            return 1

        wrapped = make_measured_runner(runner, agent_name="website", registry=r)
        for _ in range(5):
            wrapped()
        assert r.snapshot().agent_latency["website"].count == 5

    def test_args_passed_through(self) -> None:
        r = MetricsRegistry()

        def runner(a: int, b: int) -> int:
            return a + b

        wrapped = make_measured_runner(runner, agent_name="intake", registry=r)
        assert wrapped(2, 3) == 5


class TestInstrumentedPipelineEndToEnd:
    """Integration: wire both wrappers around real pipeline runners.

    Demonstrates that `make_logged_runner` + `make_measured_runner`
    compose with `run_pipeline` without any modification to pipeline.py
    itself — the observability layer is purely opt-in.
    """

    def test_instrumented_happy_path(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        intake = _load_intake()
        data = _load_data()
        client = FakeRepoClient()
        agent = WebsiteAgent(client, ci_platform="gitlab")
        config = _make_config(tmp_path, run_id="run_inst_ok")

        metrics = MetricsRegistry()

        intake_runner = make_logged_runner(
            make_measured_runner(
                lambda: intake, agent_name="intake", registry=metrics
            ),
            agent_name="intake",
            run_id=config.run_id,
            correlation_id=config.correlation_id,
        )
        data_runner = make_logged_runner(
            make_measured_runner(
                lambda _req: data, agent_name="data", registry=metrics
            ),
            agent_name="data",
            run_id=config.run_id,
            correlation_id=config.correlation_id,
        )
        website_runner = make_logged_runner(
            make_measured_runner(
                agent.run, agent_name="website", registry=metrics
            ),
            agent_name="website",
            run_id=config.run_id,
            correlation_id=config.correlation_id,
        )

        import logging

        with caplog.at_level(
            logging.INFO,
            logger="model_project_constructor.orchestrator",
        ):
            result = run_pipeline(
                config,
                intake_runner=intake_runner,
                data_runner=data_runner,
                website_runner=website_runner,
            )
        metrics.record_run(result.status)

        assert result.status == "COMPLETE"

        snap = metrics.snapshot()
        assert snap.run_count == 1
        assert snap.status_counts == {"COMPLETE": 1}
        assert set(snap.agent_latency.keys()) == {"intake", "data", "website"}
        for agent_name in ("intake", "data", "website"):
            assert snap.agent_latency[agent_name].count == 1
            assert snap.agent_latency[agent_name].total_ms >= 0.0

        # Six agent events: start/end for each of intake, data, website.
        orchestrator_events = [
            record.getMessage()
            for record in caplog.records
            if record.name == "model_project_constructor.orchestrator"
        ]
        assert orchestrator_events.count("agent.start") == 3
        assert orchestrator_events.count("agent.end") == 3
