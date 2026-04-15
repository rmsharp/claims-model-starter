"""RETRY_BACKOFF self-loop coverage (architecture-plan §4.3, §10, §14 Phase 4B).

The retry path is bounded at ``MAX_COMMIT_ATTEMPTS`` and uses an
exponential delay (1s, 2s, 4s by default). Tests inject a no-op sleep so
the suite runs at wall-clock speed.

Covered scenarios:
- First call fails → RETRYING, commit_attempts=1 (node-level)
- End-to-end: commit flakes twice, third attempt succeeds → COMPLETE
- End-to-end: commit flakes every time → FAILED with retry-exhausted reason
- retry_backoff node invokes the injected sleep with doubling delay
"""

from __future__ import annotations

from typing import Any

from model_project_constructor.agents.website.agent import WebsiteAgent
from model_project_constructor.agents.website.fake_client import FakeRepoClient
from model_project_constructor.agents.website.graph import build_website_graph
from model_project_constructor.agents.website.nodes import make_nodes
from model_project_constructor.agents.website.protocol import (
    CommitInfo,
    ProjectInfo,
    RepoClient,
    RepoClientError,
)
from model_project_constructor.agents.website.state import (
    MAX_COMMIT_ATTEMPTS,
    RETRY_BASE_DELAY_SECONDS,
    initial_state,
)
from model_project_constructor.schemas.v1.data import DataReport
from model_project_constructor.schemas.v1.intake import IntakeReport
from model_project_constructor.schemas.v1.repo import RepoTarget


class _TransientCommitClient:
    """Commit fails the first ``fail_count`` times, then succeeds.

    Uses ``FakeRepoClient`` for create_project + state tracking so the
    happy-path assertions still work after retries finish.
    """

    def __init__(self, *, fail_count: int) -> None:
        self._inner = FakeRepoClient()
        self._fails_remaining = fail_count
        self.commit_call_count = 0

    def create_project(
        self, *, namespace: str, name: str, visibility: str
    ) -> ProjectInfo:
        return self._inner.create_project(
            namespace=namespace, name=name, visibility=visibility
        )

    def commit_files(
        self,
        *,
        project_id: str,
        branch: str,
        files: dict[str, str],
        message: str,
    ) -> CommitInfo:
        self.commit_call_count += 1
        if self._fails_remaining > 0:
            self._fails_remaining -= 1
            raise RepoClientError(
                f"simulated transient failure ({self._fails_remaining} fails left)"
            )
        return self._inner.commit_files(
            project_id=project_id,
            branch=branch,
            files=files,
            message=message,
        )

    def get_files(self, project_id: str) -> dict[str, str]:
        return self._inner.get_files(project_id)

    @property
    def projects(self) -> dict[str, Any]:
        return self._inner.projects


class _AlwaysFailingCommitClient(_TransientCommitClient):
    def __init__(self) -> None:
        super().__init__(fail_count=10**6)


class TestRetryBackoffNode:
    def test_retry_backoff_sleeps_with_doubling_delay(
        self,
        intake_report: Any,
        data_report: Any,
        repo_target: Any,
    ) -> None:
        delays: list[float] = []
        nodes = make_nodes(
            FakeRepoClient(), sleep=lambda s: delays.append(s)
        )
        state = initial_state(
            intake_report=intake_report.model_dump(mode="json"),
            data_report=data_report.model_dump(mode="json"),
            repo_target=repo_target.model_dump(mode="json"),
        )

        # Attempt 1 → base delay
        state["commit_attempts"] = 1
        nodes["retry_backoff"](state)
        # Attempt 2 → 2× base
        state["commit_attempts"] = 2
        nodes["retry_backoff"](state)
        # Attempt 3 → 4× base
        state["commit_attempts"] = 3
        nodes["retry_backoff"](state)

        assert delays == [
            RETRY_BASE_DELAY_SECONDS * 1,
            RETRY_BASE_DELAY_SECONDS * 2,
            RETRY_BASE_DELAY_SECONDS * 4,
        ]

    def test_retry_backoff_resets_status_to_partial(
        self,
        intake_report: Any,
        data_report: Any,
        repo_target: Any,
    ) -> None:
        nodes = make_nodes(FakeRepoClient(), sleep=lambda _s: None)
        state = initial_state(
            intake_report=intake_report.model_dump(mode="json"),
            data_report=data_report.model_dump(mode="json"),
            repo_target=repo_target.model_dump(mode="json"),
        )
        state["commit_attempts"] = 1
        state["status"] = "RETRYING"

        delta = nodes["retry_backoff"](state)
        assert delta["status"] == "PARTIAL"


class TestRetryEndToEnd:
    def _run_with_client(
        self,
        client: RepoClient,
        intake_report: IntakeReport,
        data_report: DataReport,
        repo_target: RepoTarget,
    ) -> Any:
        agent = WebsiteAgent.__new__(WebsiteAgent)
        agent.client = client
        agent.graph = build_website_graph(client, sleep=lambda _s: None)
        return agent.run(intake_report, data_report, repo_target)

    def test_commit_flakes_twice_then_succeeds(
        self,
        intake_report: IntakeReport,
        data_report: DataReport,
        repo_target: RepoTarget,
    ) -> None:
        """Third attempt under MAX_COMMIT_ATTEMPTS=3 should still succeed."""

        client = _TransientCommitClient(fail_count=2)
        result = self._run_with_client(
            client, intake_report, data_report, repo_target
        )

        assert result.status == "COMPLETE"
        assert result.failure_reason is None
        assert len(result.initial_commit_sha) == 40
        assert client.commit_call_count == 3

    def test_commit_flakes_once_then_succeeds(
        self,
        intake_report: IntakeReport,
        data_report: DataReport,
        repo_target: RepoTarget,
    ) -> None:
        client = _TransientCommitClient(fail_count=1)
        result = self._run_with_client(
            client, intake_report, data_report, repo_target
        )

        assert result.status == "COMPLETE"
        assert client.commit_call_count == 2

    def test_exhausted_retries_fail_with_retry_exhausted_reason(
        self,
        intake_report: IntakeReport,
        data_report: DataReport,
        repo_target: RepoTarget,
    ) -> None:
        """MAX_COMMIT_ATTEMPTS attempts, all failing, should yield FAILED
        with a ``repo_error_retry_exhausted`` failure reason.
        """

        client = _AlwaysFailingCommitClient()
        result = self._run_with_client(
            client, intake_report, data_report, repo_target
        )

        assert result.status == "FAILED"
        assert "repo_error_retry_exhausted" in (result.failure_reason or "")
        # Exactly MAX_COMMIT_ATTEMPTS calls to commit
        assert client.commit_call_count == MAX_COMMIT_ATTEMPTS
        # No commit sha set
        assert result.initial_commit_sha == ""
