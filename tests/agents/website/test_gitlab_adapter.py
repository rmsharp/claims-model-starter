"""Import-level smoke tests for the python-gitlab adapter (Phase 4B).

The real adapter is never unit-tested against a network GitLab in this
repo — that's a Phase 5 / CI-with-credentials concern. This module just
verifies:

- The adapter module imports without side effects.
- ``PythonGitLabAdapter`` satisfies the ``GitLabClient`` Protocol.
- The name-conflict sniff helper correctly classifies representative
  GitLab create-project errors.
- The constructor does not make network calls (no credentials needed).
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from model_project_constructor.agents.website import PythonGitLabAdapter
from model_project_constructor.agents.website.gitlab_adapter import _is_name_conflict
from model_project_constructor.agents.website.protocol import (
    GitLabClientError,
    ProjectNameConflictError,
)


class TestImport:
    def test_adapter_has_protocol_methods(self) -> None:
        # ``GitLabClient`` is not runtime_checkable (structural only), so
        # ``isinstance`` would raise. A duck-type check is sufficient
        # since mypy strict on the module enforces the real contract.
        adapter = PythonGitLabAdapter(
            gitlab_url="https://gitlab.example.com", private_token="dummy"
        )
        assert callable(getattr(adapter, "create_project"))
        assert callable(getattr(adapter, "commit_files"))

    def test_constructor_does_not_make_network_call(self) -> None:
        """Creating an adapter with a dummy token must not reach the network.

        python-gitlab defers authentication until the first API call, so
        instantiating with junk credentials should succeed silently.
        """

        PythonGitLabAdapter(
            gitlab_url="https://invalid.example.invalid",
            private_token="not-a-real-token",
        )


class TestNameConflictSniffing:
    def test_400_with_taken_message_is_conflict(self) -> None:
        exc = MagicMock()
        exc.response_code = 400
        exc.error_message = {"name": ["has already been taken"]}
        assert _is_name_conflict(exc) is True

    def test_409_with_exists_message_is_conflict(self) -> None:
        exc = MagicMock()
        exc.response_code = 409
        exc.error_message = "Project already exists"
        assert _is_name_conflict(exc) is True

    def test_500_is_not_conflict(self) -> None:
        exc = MagicMock()
        exc.response_code = 500
        exc.error_message = "Internal Server Error"
        assert _is_name_conflict(exc) is False

    def test_400_without_taken_message_is_not_conflict(self) -> None:
        exc = MagicMock()
        exc.response_code = 400
        exc.error_message = {"visibility": ["is invalid"]}
        assert _is_name_conflict(exc) is False


class TestExceptionTranslation:
    """The adapter must translate python-gitlab errors into the protocol's
    exception hierarchy. We stub the underlying ``_gl`` attribute so no
    network call happens.
    """

    def _build_adapter_with_fake_gl(self) -> tuple[PythonGitLabAdapter, MagicMock]:
        adapter = PythonGitLabAdapter(
            gitlab_url="https://gitlab.example.com", private_token="t"
        )
        fake_gl = MagicMock()
        adapter._gl = fake_gl
        return adapter, fake_gl

    def test_create_project_name_conflict_raises_project_name_conflict(self) -> None:
        from gitlab.exceptions import GitlabCreateError

        adapter, fake_gl = self._build_adapter_with_fake_gl()
        fake_gl.groups.get.return_value = MagicMock(id=42)
        conflict = GitlabCreateError(
            error_message={"name": ["has already been taken"]},
            response_code=400,
        )
        fake_gl.projects.create.side_effect = conflict

        with pytest.raises(ProjectNameConflictError) as excinfo:
            adapter.create_project(
                group_path="g", name="foo", visibility="private"
            )
        assert excinfo.value.name == "foo"

    def test_create_project_generic_error_raises_client_error(self) -> None:
        from gitlab.exceptions import GitlabCreateError

        adapter, fake_gl = self._build_adapter_with_fake_gl()
        fake_gl.groups.get.return_value = MagicMock(id=42)
        fake_gl.projects.create.side_effect = GitlabCreateError(
            error_message="Internal error", response_code=500
        )

        with pytest.raises(GitLabClientError) as excinfo:
            adapter.create_project(
                group_path="g", name="foo", visibility="private"
            )
        assert "create_project failed" in str(excinfo.value)

    def test_group_lookup_failure_raises_client_error(self) -> None:
        from gitlab.exceptions import GitlabGetError

        adapter, fake_gl = self._build_adapter_with_fake_gl()
        fake_gl.groups.get.side_effect = GitlabGetError(
            error_message="404 Group not found", response_code=404
        )

        with pytest.raises(GitLabClientError) as excinfo:
            adapter.create_project(
                group_path="missing", name="foo", visibility="private"
            )
        assert "group lookup failed" in str(excinfo.value)

    def test_commit_files_error_raises_client_error(self) -> None:
        from gitlab.exceptions import GitlabError

        adapter, fake_gl = self._build_adapter_with_fake_gl()
        fake_project = MagicMock()
        fake_project.commits.create.side_effect = GitlabError(
            error_message="rate limited"
        )
        fake_gl.projects.get.return_value = fake_project

        with pytest.raises(GitLabClientError) as excinfo:
            adapter.commit_files(
                project_id=1,
                branch="main",
                files={"a.txt": "x"},
                message="test",
            )
        assert "commit_files failed" in str(excinfo.value)

    def test_commit_files_happy_path_returns_commit_info(self) -> None:
        adapter, fake_gl = self._build_adapter_with_fake_gl()
        fake_project = MagicMock()
        fake_commit = MagicMock()
        fake_commit.id = "deadbeef"
        fake_project.commits.create.return_value = fake_commit
        fake_gl.projects.get.return_value = fake_project

        info = adapter.commit_files(
            project_id=1,
            branch="main",
            files={"a.txt": "x", "b.txt": "y"},
            message="init",
        )
        assert info.sha == "deadbeef"
        assert info.files_committed == ["a.txt", "b.txt"]
