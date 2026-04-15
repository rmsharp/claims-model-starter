"""Tests for the website agent's CREATE_PROJECT / SCAFFOLD_BASE / INITIAL_COMMITS nodes."""

from __future__ import annotations

from typing import Any

import pytest

from model_project_constructor.agents.website.fake_client import FakeGitLabClient
from model_project_constructor.agents.website.nodes import (
    build_gitlab_project_result,
    make_nodes,
    route_after_create,
)
from model_project_constructor.agents.website.protocol import (
    GitLabClient,
    GitLabClientError,
    ProjectInfo,
    CommitInfo,
)
from model_project_constructor.agents.website.state import (
    MAX_NAME_CONFLICT_ATTEMPTS,
    initial_state,
)


class _FlakyClient:
    """Fake that always raises GitLabClientError on create_project."""

    def create_project(
        self, *, group_path: str, name: str, visibility: str
    ) -> ProjectInfo:
        raise GitLabClientError("simulated auth failure")

    def commit_files(
        self,
        *,
        project_id: int,
        branch: str,
        files: dict[str, str],
        message: str,
    ) -> CommitInfo:
        raise AssertionError("should not be called")


class _CommitFlakyClient:
    """Fake that succeeds on create but fails on commit."""

    def __init__(self) -> None:
        self._inner = FakeGitLabClient()

    def create_project(
        self, *, group_path: str, name: str, visibility: str
    ) -> ProjectInfo:
        return self._inner.create_project(
            group_path=group_path, name=name, visibility=visibility
        )

    def commit_files(
        self,
        *,
        project_id: int,
        branch: str,
        files: dict[str, str],
        message: str,
    ) -> CommitInfo:
        raise GitLabClientError("simulated commit failure")


class TestCreateProject:
    def test_happy_path(
        self, fake_client: FakeGitLabClient, intake_report: Any, data_report: Any, gitlab_target: Any
    ) -> None:
        nodes = make_nodes(fake_client)
        state = initial_state(
            intake_report=intake_report.model_dump(mode="json"),
            data_report=data_report.model_dump(mode="json"),
            gitlab_target=gitlab_target.model_dump(mode="json"),
        )

        delta = nodes["create_project"](state)

        assert delta["project_name"] == "subrogation-recovery-model"
        assert delta["project_slug"] == "subrogation_recovery_model"
        assert delta["project_id"] == 1000
        assert delta["project_url"].endswith("/subrogation-recovery-model")
        assert delta["default_branch"] == "main"
        assert delta["status"] == "PARTIAL"

    def test_suffix_on_single_conflict(
        self,
        intake_report: Any,
        data_report: Any,
        gitlab_target: Any,
    ) -> None:
        client = FakeGitLabClient(
            existing_names={"data-science/model-drafts/subrogation-recovery-model"}
        )
        nodes = make_nodes(client)
        state = initial_state(
            intake_report=intake_report.model_dump(mode="json"),
            data_report=data_report.model_dump(mode="json"),
            gitlab_target=gitlab_target.model_dump(mode="json"),
        )

        delta = nodes["create_project"](state)
        assert delta["project_name"] == "subrogation-recovery-model-v2"

    def test_suffix_chain_all_taken_fails(
        self,
        intake_report: Any,
        data_report: Any,
        gitlab_target: Any,
    ) -> None:
        existing = {
            "data-science/model-drafts/subrogation-recovery-model",
            "data-science/model-drafts/subrogation-recovery-model-v2",
            "data-science/model-drafts/subrogation-recovery-model-v3",
            "data-science/model-drafts/subrogation-recovery-model-v4",
            "data-science/model-drafts/subrogation-recovery-model-v5",
        }
        client = FakeGitLabClient(existing_names=existing)
        nodes = make_nodes(client)
        state = initial_state(
            intake_report=intake_report.model_dump(mode="json"),
            data_report=data_report.model_dump(mode="json"),
            gitlab_target=gitlab_target.model_dump(mode="json"),
        )

        delta = nodes["create_project"](state)
        assert delta["status"] == "FAILED"
        assert "project_name_conflict" in (delta.get("failure_reason") or "")
        assert f"{MAX_NAME_CONFLICT_ATTEMPTS}" in (delta.get("failure_reason") or "")

    def test_non_conflict_gitlab_error_halts(
        self,
        intake_report: Any,
        data_report: Any,
        gitlab_target: Any,
    ) -> None:
        nodes = make_nodes(_FlakyClient())
        state = initial_state(
            intake_report=intake_report.model_dump(mode="json"),
            data_report=data_report.model_dump(mode="json"),
            gitlab_target=gitlab_target.model_dump(mode="json"),
        )
        delta = nodes["create_project"](state)
        assert delta["status"] == "FAILED"
        assert "gitlab_error" in (delta.get("failure_reason") or "")


class TestScaffoldBase:
    def test_populates_pending(
        self,
        fake_client: FakeGitLabClient,
        intake_report: Any,
        data_report: Any,
        gitlab_target: Any,
    ) -> None:
        nodes = make_nodes(fake_client)
        state = initial_state(
            intake_report=intake_report.model_dump(mode="json"),
            data_report=data_report.model_dump(mode="json"),
            gitlab_target=gitlab_target.model_dump(mode="json"),
        )
        state["project_name"] = "my-model"
        state["project_slug"] = "my_model"

        delta = nodes["scaffold_base"](state)
        files = delta["files_pending"]

        assert "README.md" in files
        assert "src/my_model/__init__.py" in files
        assert "queries/primary/subrogation_training_set.sql" in files
        # governance artifacts MUST NOT appear in Phase 4A
        assert not any(p.startswith("governance/") for p in files)

    def test_preserves_pre_existing_pending(
        self,
        fake_client: FakeGitLabClient,
        intake_report: Any,
        data_report: Any,
        gitlab_target: Any,
    ) -> None:
        nodes = make_nodes(fake_client)
        state = initial_state(
            intake_report=intake_report.model_dump(mode="json"),
            data_report=data_report.model_dump(mode="json"),
            gitlab_target=gitlab_target.model_dump(mode="json"),
        )
        state["project_name"] = "m"
        state["project_slug"] = "m"
        state["files_pending"] = {"pre_existing.txt": "hi"}

        delta = nodes["scaffold_base"](state)
        assert "pre_existing.txt" in delta["files_pending"]
        assert "README.md" in delta["files_pending"]


class TestInitialCommits:
    def test_happy_path_flushes_pending(
        self,
        fake_client: FakeGitLabClient,
        intake_report: Any,
        data_report: Any,
        gitlab_target: Any,
    ) -> None:
        nodes = make_nodes(fake_client)
        info = fake_client.create_project(
            group_path="g", name="n", visibility="private"
        )
        state = initial_state(
            intake_report=intake_report.model_dump(mode="json"),
            data_report=data_report.model_dump(mode="json"),
            gitlab_target=gitlab_target.model_dump(mode="json"),
        )
        state["project_id"] = info.id
        state["default_branch"] = "main"
        state["files_pending"] = {"a.txt": "1", "b.txt": "2"}

        delta = nodes["initial_commits"](state)

        assert delta["status"] == "COMPLETE"
        assert delta["files_created"] == ["a.txt", "b.txt"]
        assert len(delta["initial_commit_sha"]) == 40
        assert delta["files_pending"] == {}

        stored = fake_client.get_files(info.id)
        assert stored == {"a.txt": "1", "b.txt": "2"}

    def test_empty_pending_fails(
        self,
        fake_client: FakeGitLabClient,
        intake_report: Any,
        data_report: Any,
        gitlab_target: Any,
    ) -> None:
        nodes = make_nodes(fake_client)
        state = initial_state(
            intake_report=intake_report.model_dump(mode="json"),
            data_report=data_report.model_dump(mode="json"),
            gitlab_target=gitlab_target.model_dump(mode="json"),
        )
        state["project_id"] = 1
        delta = nodes["initial_commits"](state)
        assert delta["status"] == "FAILED"
        assert delta["failure_reason"] == "no_files_scaffolded"

    def test_commit_failure_surfaces(
        self,
        intake_report: Any,
        data_report: Any,
        gitlab_target: Any,
    ) -> None:
        client = _CommitFlakyClient()
        nodes = make_nodes(client)
        info = client.create_project(
            group_path="g", name="n", visibility="private"
        )
        state = initial_state(
            intake_report=intake_report.model_dump(mode="json"),
            data_report=data_report.model_dump(mode="json"),
            gitlab_target=gitlab_target.model_dump(mode="json"),
        )
        state["project_id"] = info.id
        state["default_branch"] = "main"
        state["files_pending"] = {"a.txt": "1"}

        delta = nodes["initial_commits"](state)
        assert delta["status"] == "FAILED"
        assert "commit_failed" in (delta.get("failure_reason") or "")


class TestRouting:
    def test_route_after_create_failed_goes_to_end(self) -> None:
        assert route_after_create({"status": "FAILED"}) == "end"

    def test_route_after_create_partial_continues(self) -> None:
        assert route_after_create({"status": "PARTIAL"}) == "scaffold_base"


class TestBuildGitLabProjectResult:
    def test_complete_state_produces_valid_result(
        self, intake_report: Any
    ) -> None:
        state = {
            "intake_report": intake_report.model_dump(mode="json"),
            "project_id": 42,
            "project_url": "https://x/y",
            "initial_commit_sha": "abc",
            "files_created": ["README.md"],
            "status": "COMPLETE",
            "failure_reason": None,
        }
        result = build_gitlab_project_result(state)  # type: ignore[arg-type]
        assert result.status == "COMPLETE"
        assert result.project_id == 42
        assert result.governance_manifest.risk_tier == "tier_3_moderate"
        assert result.governance_manifest.cycle_time == "tactical"
        assert result.governance_manifest.artifacts_created == []

    def test_failed_state_defaults_governance(self) -> None:
        state = {
            "status": "FAILED",
            "failure_reason": "boom",
        }
        result = build_gitlab_project_result(state)  # type: ignore[arg-type]
        assert result.status == "FAILED"
        assert result.failure_reason == "boom"
        assert result.governance_manifest.risk_tier == "tier_4_low"
