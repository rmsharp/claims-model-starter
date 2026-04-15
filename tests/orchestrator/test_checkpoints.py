"""Tests for ``orchestrator.checkpoints.CheckpointStore``.

The store is a filesystem-backed envelope persistence layer with a
second channel for terminal (non-envelope) results. These tests pin:

- Envelope save/load round-trip.
- Registry resolution via ``load_payload``.
- Terminal result persistence via ``save_result`` (the phase-5 bespoke
  path for the final ``RepoProjectResult``).
- Run isolation — two runs in the same base_dir do not collide.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from model_project_constructor.orchestrator.checkpoints import CheckpointStore
from model_project_constructor.schemas.envelope import HandoffEnvelope
from model_project_constructor.schemas.v1.data import DataGranularity, DataRequest
from model_project_constructor.schemas.v1.repo import (
    GovernanceManifest,
    RepoProjectResult,
    RepoTarget,
)


def _make_data_request_envelope(run_id: str = "run_001") -> HandoffEnvelope:
    request = DataRequest(
        target_description="something",
        target_granularity=DataGranularity(unit="claim", time_grain="event"),
        required_features=["a", "b"],
        population_filter="all claims",
        time_range="last 5 years",
        source="pipeline",
        source_ref=run_id,
    )
    return HandoffEnvelope(
        run_id=run_id,
        source_agent="orchestrator",
        target_agent="data",
        payload_type="DataRequest",
        payload_schema_version="1.0.0",
        payload=request.model_dump(mode="json"),
        created_at=datetime.now(timezone.utc),
        correlation_id=run_id,
    )


def _make_repo_project_result() -> RepoProjectResult:
    return RepoProjectResult(
        status="COMPLETE",
        project_url="https://fake.host.test/acme/foo",
        project_id="1000",
        initial_commit_sha="abc123",
        files_created=["README.md", ".gitlab-ci.yml"],
        governance_manifest=GovernanceManifest(
            model_registry_entry={"name": "foo"},
            artifacts_created=["README.md"],
            risk_tier="tier_3_moderate",
            cycle_time="tactical",
            regulatory_mapping={},
        ),
        failure_reason=None,
    )


class TestEnvelopeRoundTrip:
    def test_save_and_load_round_trip(self, tmp_path: Path) -> None:
        store = CheckpointStore(tmp_path)
        env = _make_data_request_envelope()
        path = store.save(env)
        assert path.exists()
        assert path.name == "DataRequest.json"
        loaded = store.load("run_001", "DataRequest")
        assert loaded == env

    def test_save_creates_run_directory(self, tmp_path: Path) -> None:
        store = CheckpointStore(tmp_path)
        env = _make_data_request_envelope(run_id="run_xyz")
        store.save(env)
        assert (tmp_path / "run_xyz").is_dir()

    def test_has_returns_false_before_save(self, tmp_path: Path) -> None:
        store = CheckpointStore(tmp_path)
        assert store.has("run_001", "DataRequest") is False

    def test_has_returns_true_after_save(self, tmp_path: Path) -> None:
        store = CheckpointStore(tmp_path)
        store.save(_make_data_request_envelope())
        assert store.has("run_001", "DataRequest") is True

    def test_load_payload_resolves_via_registry(self, tmp_path: Path) -> None:
        store = CheckpointStore(tmp_path)
        store.save(_make_data_request_envelope())
        payload = store.load_payload("run_001", "DataRequest")
        assert isinstance(payload, DataRequest)
        assert payload.required_features == ["a", "b"]

    def test_load_missing_raises_file_not_found(self, tmp_path: Path) -> None:
        store = CheckpointStore(tmp_path)
        with pytest.raises(FileNotFoundError):
            store.load("nonexistent", "DataRequest")

    def test_overwrites_on_resave(self, tmp_path: Path) -> None:
        store = CheckpointStore(tmp_path)
        store.save(_make_data_request_envelope())
        # Re-save with a different correlation_id to prove the file is
        # overwritten rather than suffixed.
        env2 = _make_data_request_envelope()
        env2_dict = env2.model_dump()
        env2_dict["correlation_id"] = "new-correlation-id"
        env2_updated = HandoffEnvelope.model_validate(env2_dict)
        store.save(env2_updated)
        loaded = store.load("run_001", "DataRequest")
        assert loaded.correlation_id == "new-correlation-id"


class TestListing:
    def test_list_payload_types_empty_for_missing_run(self, tmp_path: Path) -> None:
        store = CheckpointStore(tmp_path)
        assert store.list_payload_types("nope") == []

    def test_list_payload_types_after_saves(self, tmp_path: Path) -> None:
        store = CheckpointStore(tmp_path)
        store.save(_make_data_request_envelope())
        # Save a second envelope with a different payload_type.
        env = _make_data_request_envelope()
        env_dict = env.model_dump()
        env_dict["payload_type"] = "IntakeReport"
        store.save(HandoffEnvelope.model_validate(env_dict))
        types = store.list_payload_types("run_001")
        assert types == ["DataRequest", "IntakeReport"]

    def test_list_excludes_terminal_results(self, tmp_path: Path) -> None:
        store = CheckpointStore(tmp_path)
        store.save(_make_data_request_envelope())
        store.save_result("run_001", "RepoProjectResult", _make_repo_project_result())
        assert store.list_payload_types("run_001") == ["DataRequest"]
        assert store.list_result_names("run_001") == ["RepoProjectResult"]

    def test_list_result_names_empty_for_missing_run(self, tmp_path: Path) -> None:
        store = CheckpointStore(tmp_path)
        assert store.list_result_names("nope") == []


class TestTerminalResults:
    def test_save_result_writes_suffix_json(self, tmp_path: Path) -> None:
        store = CheckpointStore(tmp_path)
        result = _make_repo_project_result()
        path = store.save_result("run_001", "RepoProjectResult", result)
        assert path.exists()
        assert path.name == "RepoProjectResult.result.json"

    def test_save_result_creates_run_directory(self, tmp_path: Path) -> None:
        store = CheckpointStore(tmp_path)
        store.save_result("run_xyz", "RepoProjectResult", _make_repo_project_result())
        assert (tmp_path / "run_xyz").is_dir()

    def test_has_result_reports_existence(self, tmp_path: Path) -> None:
        store = CheckpointStore(tmp_path)
        assert store.has_result("run_001", "RepoProjectResult") is False
        store.save_result("run_001", "RepoProjectResult", _make_repo_project_result())
        assert store.has_result("run_001", "RepoProjectResult") is True

    def test_result_and_envelope_do_not_collide(self, tmp_path: Path) -> None:
        store = CheckpointStore(tmp_path)
        # Save an envelope AND a terminal result with the same logical name;
        # they must live in different files and neither should overwrite the other.
        env = _make_data_request_envelope()
        env_dict = env.model_dump()
        env_dict["payload_type"] = "RepoProjectResult"
        store.save(HandoffEnvelope.model_validate(env_dict))
        store.save_result("run_001", "RepoProjectResult", _make_repo_project_result())
        assert store.has("run_001", "RepoProjectResult")
        assert store.has_result("run_001", "RepoProjectResult")
        assert store.list_payload_types("run_001") == ["RepoProjectResult"]
        assert store.list_result_names("run_001") == ["RepoProjectResult"]


class TestRunIsolation:
    def test_two_runs_do_not_share_files(self, tmp_path: Path) -> None:
        store = CheckpointStore(tmp_path)
        store.save(_make_data_request_envelope(run_id="run_A"))
        store.save(_make_data_request_envelope(run_id="run_B"))
        assert store.has("run_A", "DataRequest")
        assert store.has("run_B", "DataRequest")
        assert store.list_payload_types("run_A") == ["DataRequest"]
        assert store.list_payload_types("run_B") == ["DataRequest"]

    def test_base_dir_accepts_str_or_path(self, tmp_path: Path) -> None:
        store_str = CheckpointStore(str(tmp_path))
        store_path = CheckpointStore(tmp_path)
        assert store_str.base_dir == store_path.base_dir

    def test_repo_target_envelope_round_trip(self, tmp_path: Path) -> None:
        """RepoTarget is persisted as an orchestrator→website handoff so
        resumption knows which host the pipeline was configured for."""

        store = CheckpointStore(tmp_path)
        target = RepoTarget(
            host_url="https://api.github.com",
            namespace="acme",
            project_name_hint="subrogation_pilot",
            visibility="private",
        )
        env = HandoffEnvelope(
            run_id="run_001",
            source_agent="orchestrator",
            target_agent="website",
            payload_type="RepoTarget",
            payload_schema_version="1.0.0",
            payload=target.model_dump(mode="json"),
            created_at=datetime.now(timezone.utc),
            correlation_id="run_001",
        )
        store.save(env)
        loaded = store.load_payload("run_001", "RepoTarget")
        assert isinstance(loaded, RepoTarget)
        assert loaded.host_url == "https://api.github.com"
