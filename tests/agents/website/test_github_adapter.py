"""Import-level + mocked-client tests for the PyGithub adapter (Phase C).

The real adapter is never unit-tested against a network GitHub in this
repo — that's a Phase 5 / CI-with-credentials concern. This module just
verifies:

- The adapter module imports without side effects.
- ``PyGithubAdapter`` exposes ``create_project`` and ``commit_files`` as
  callables (satisfying :class:`RepoClient`'s structural contract).
- Constructor is non-network (PyGithub defers until first API call).
- ``_is_name_conflict`` classifies representative GitHub error shapes.
- The nested-namespace guard rejects ``"a/b"`` style inputs.
- ``MagicMock``-based exception translation for ``create_project`` covers
  the org-then-user resolution fallback and the 422/non-422 branches.
- ``MagicMock``-based ``commit_files`` happy path exercises the full
  blob → tree → commit → ref.edit git dance and returns ``CommitInfo``.
- Each failure point in the git dance (blob, tree, commit, ref.edit) maps
  to ``RepoClientError`` so the RETRY_BACKOFF loop sees identical
  semantics across GitLab and GitHub adapters.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from github import GithubException, UnknownObjectException

from model_project_constructor.agents.website import PyGithubAdapter
from model_project_constructor.agents.website.github_adapter import _is_name_conflict
from model_project_constructor.agents.website.protocol import (
    RepoClientError,
    RepoNameConflictError,
)


def _make_github_exc(status: int, data: object) -> GithubException:
    return GithubException(status, data=data, headers={})


class TestImport:
    def test_adapter_has_protocol_methods(self) -> None:
        # ``RepoClient`` is not runtime_checkable (structural only), so a
        # duck-type check mirrors the gitlab-adapter pattern. mypy strict
        # on the production module enforces the real contract.
        adapter = PyGithubAdapter(
            host_url="https://api.github.com", private_token="dummy"
        )
        assert callable(getattr(adapter, "create_project"))
        assert callable(getattr(adapter, "commit_files"))

    def test_constructor_does_not_make_network_call(self) -> None:
        """Creating an adapter with a dummy token must not reach the network.

        PyGithub defers authentication until the first API call, so
        instantiating with junk credentials should succeed silently.
        """

        PyGithubAdapter(
            host_url="https://invalid.example.invalid",
            private_token="not-a-real-token",
        )


class TestNameConflictSniffing:
    def test_422_with_already_exists_message_is_conflict(self) -> None:
        exc = _make_github_exc(
            422, {"errors": [{"message": "name already exists on this account"}]}
        )
        assert _is_name_conflict(exc) is True

    def test_422_with_generic_already_exists_fallback_is_conflict(self) -> None:
        # Wording drift: message is elsewhere in the payload, but the
        # stringified exception still mentions "already exists".
        exc = _make_github_exc(422, {"message": "Repository already exists"})
        assert _is_name_conflict(exc) is True

    def test_500_is_not_conflict(self) -> None:
        exc = _make_github_exc(500, {"message": "server error"})
        assert _is_name_conflict(exc) is False

    def test_422_with_unrelated_message_is_not_conflict(self) -> None:
        exc = _make_github_exc(
            422, {"errors": [{"message": "visibility is invalid"}]}
        )
        assert _is_name_conflict(exc) is False


class TestExceptionTranslation:
    """The adapter must translate PyGithub errors into the protocol's
    exception hierarchy. We stub the underlying ``_gh`` attribute so no
    network call happens.
    """

    def _build_adapter_with_fake_gh(self) -> tuple[PyGithubAdapter, MagicMock]:
        adapter = PyGithubAdapter(
            host_url="https://api.github.com", private_token="t"
        )
        fake_gh = MagicMock()
        adapter._gh = fake_gh
        return adapter, fake_gh

    def test_nested_namespace_raises_client_error(self) -> None:
        adapter, _ = self._build_adapter_with_fake_gh()
        with pytest.raises(RepoClientError) as excinfo:
            adapter.create_project(
                namespace="acme/sub", name="foo", visibility="private"
            )
        assert "nested namespace" in str(excinfo.value)

    def test_create_project_name_conflict_raises_repo_name_conflict(self) -> None:
        adapter, fake_gh = self._build_adapter_with_fake_gh()
        fake_org = MagicMock()
        fake_gh.get_organization.return_value = fake_org
        fake_org.create_repo.side_effect = _make_github_exc(
            422, {"errors": [{"message": "name already exists on this account"}]}
        )

        with pytest.raises(RepoNameConflictError) as excinfo:
            adapter.create_project(namespace="acme", name="foo", visibility="private")
        assert excinfo.value.name == "foo"

    def test_create_project_generic_error_raises_client_error(self) -> None:
        adapter, fake_gh = self._build_adapter_with_fake_gh()
        fake_org = MagicMock()
        fake_gh.get_organization.return_value = fake_org
        fake_org.create_repo.side_effect = _make_github_exc(
            500, {"message": "boom"}
        )

        with pytest.raises(RepoClientError) as excinfo:
            adapter.create_project(namespace="acme", name="foo", visibility="private")
        assert "create_project failed" in str(excinfo.value)

    def test_create_project_org_missing_falls_back_to_user(self) -> None:
        adapter, fake_gh = self._build_adapter_with_fake_gh()
        fake_gh.get_organization.side_effect = UnknownObjectException(
            404, data={"message": "Not Found"}, headers={}
        )
        fake_user = MagicMock()
        fake_gh.get_user.return_value = fake_user
        fake_repo = MagicMock()
        fake_repo.full_name = "alice/foo"
        fake_repo.html_url = "https://github.com/alice/foo"
        fake_repo.default_branch = "main"
        fake_user.create_repo.return_value = fake_repo

        info = adapter.create_project(
            namespace="alice", name="foo", visibility="public"
        )

        fake_gh.get_organization.assert_called_once_with("alice")
        fake_gh.get_user.assert_called_once_with("alice")
        fake_user.create_repo.assert_called_once_with(name="foo", private=False)
        assert info.id == "alice/foo"
        assert info.url == "https://github.com/alice/foo"
        assert info.default_branch == "main"

    def test_create_project_user_lookup_failure_raises_client_error(self) -> None:
        adapter, fake_gh = self._build_adapter_with_fake_gh()
        fake_gh.get_organization.side_effect = UnknownObjectException(
            404, data={"message": "Not Found"}, headers={}
        )
        fake_gh.get_user.side_effect = _make_github_exc(500, {"message": "boom"})

        with pytest.raises(RepoClientError) as excinfo:
            adapter.create_project(
                namespace="alice", name="foo", visibility="private"
            )
        assert "owner lookup failed" in str(excinfo.value)

    def test_create_project_org_lookup_non_404_raises_client_error(self) -> None:
        adapter, fake_gh = self._build_adapter_with_fake_gh()
        fake_gh.get_organization.side_effect = _make_github_exc(
            500, {"message": "boom"}
        )

        with pytest.raises(RepoClientError) as excinfo:
            adapter.create_project(
                namespace="acme", name="foo", visibility="private"
            )
        assert "owner lookup failed" in str(excinfo.value)

    def test_create_project_visibility_private_passes_private_true(self) -> None:
        adapter, fake_gh = self._build_adapter_with_fake_gh()
        fake_org = MagicMock()
        fake_gh.get_organization.return_value = fake_org
        fake_repo = MagicMock()
        fake_repo.full_name = "acme/foo"
        fake_repo.html_url = "https://github.com/acme/foo"
        fake_repo.default_branch = "main"
        fake_org.create_repo.return_value = fake_repo

        adapter.create_project(namespace="acme", name="foo", visibility="internal")

        fake_org.create_repo.assert_called_once_with(name="foo", private=True)


class TestCommitFiles:
    """Drive the blob → tree → commit → ref.edit dance against mocks."""

    def _build_adapter_with_fake_gh(self) -> tuple[PyGithubAdapter, MagicMock]:
        adapter = PyGithubAdapter(
            host_url="https://api.github.com", private_token="t"
        )
        fake_gh = MagicMock()
        adapter._gh = fake_gh
        return adapter, fake_gh

    def _wire_happy_path(self, fake_gh: MagicMock) -> tuple[MagicMock, MagicMock]:
        fake_repo = MagicMock()
        fake_gh.get_repo.return_value = fake_repo

        fake_ref = MagicMock()
        fake_ref.object.sha = "parent-sha"
        fake_repo.get_git_ref.return_value = fake_ref

        fake_parent_commit = MagicMock()
        fake_parent_commit.tree = MagicMock(name="parent-tree")
        fake_repo.get_git_commit.return_value = fake_parent_commit

        def _make_blob(content: str, _encoding: str) -> MagicMock:
            blob = MagicMock()
            blob.sha = f"blob-{content}"
            return blob

        fake_repo.create_git_blob.side_effect = _make_blob

        fake_tree = MagicMock(name="new-tree")
        fake_repo.create_git_tree.return_value = fake_tree

        fake_commit = MagicMock()
        fake_commit.sha = "commit-sha"
        fake_repo.create_git_commit.return_value = fake_commit

        return fake_repo, fake_ref

    def test_commit_files_happy_path_returns_commit_info(self) -> None:
        adapter, fake_gh = self._build_adapter_with_fake_gh()
        fake_repo, fake_ref = self._wire_happy_path(fake_gh)

        info = adapter.commit_files(
            project_id="acme/foo",
            branch="main",
            files={"b.txt": "y", "a.txt": "x"},
            message="initial commit",
        )

        fake_gh.get_repo.assert_called_once_with("acme/foo")
        fake_repo.get_git_ref.assert_called_once_with("heads/main")
        fake_repo.get_git_commit.assert_called_once_with("parent-sha")
        # Sorted by path — a.txt before b.txt.
        assert [call.args[0] for call in fake_repo.create_git_blob.call_args_list] == [
            "x",
            "y",
        ]
        # create_git_tree called once with 2 elements, base_tree kwarg set.
        tree_call = fake_repo.create_git_tree.call_args
        tree_elements = tree_call.args[0]
        assert len(tree_elements) == 2
        assert tree_call.kwargs["base_tree"] is fake_repo.get_git_commit.return_value.tree
        fake_repo.create_git_commit.assert_called_once()
        commit_args = fake_repo.create_git_commit.call_args.args
        assert commit_args[0] == "initial commit"
        assert commit_args[2] == [fake_repo.get_git_commit.return_value]
        fake_ref.edit.assert_called_once_with(sha="commit-sha")

        assert info.sha == "commit-sha"
        assert info.files_committed == ["a.txt", "b.txt"]

    def test_commit_files_repo_lookup_error_raises_client_error(self) -> None:
        adapter, fake_gh = self._build_adapter_with_fake_gh()
        fake_gh.get_repo.side_effect = _make_github_exc(404, {"message": "nope"})

        with pytest.raises(RepoClientError) as excinfo:
            adapter.commit_files(
                project_id="acme/foo",
                branch="main",
                files={"a.txt": "x"},
                message="init",
            )
        assert "project lookup failed" in str(excinfo.value)

    def test_commit_files_blob_error_raises_client_error(self) -> None:
        adapter, fake_gh = self._build_adapter_with_fake_gh()
        fake_repo, _ = self._wire_happy_path(fake_gh)
        fake_repo.create_git_blob.side_effect = _make_github_exc(
            500, {"message": "blob boom"}
        )

        with pytest.raises(RepoClientError) as excinfo:
            adapter.commit_files(
                project_id="acme/foo",
                branch="main",
                files={"a.txt": "x"},
                message="init",
            )
        assert "commit_files failed" in str(excinfo.value)

    def test_commit_files_tree_error_raises_client_error(self) -> None:
        adapter, fake_gh = self._build_adapter_with_fake_gh()
        fake_repo, _ = self._wire_happy_path(fake_gh)
        fake_repo.create_git_tree.side_effect = _make_github_exc(
            500, {"message": "tree boom"}
        )

        with pytest.raises(RepoClientError) as excinfo:
            adapter.commit_files(
                project_id="acme/foo",
                branch="main",
                files={"a.txt": "x"},
                message="init",
            )
        assert "commit_files failed" in str(excinfo.value)

    def test_commit_files_ref_edit_error_raises_client_error(self) -> None:
        adapter, fake_gh = self._build_adapter_with_fake_gh()
        fake_repo, fake_ref = self._wire_happy_path(fake_gh)
        fake_ref.edit.side_effect = _make_github_exc(
            500, {"message": "ref boom"}
        )

        with pytest.raises(RepoClientError) as excinfo:
            adapter.commit_files(
                project_id="acme/foo",
                branch="main",
                files={"a.txt": "x"},
                message="init",
            )
        assert "commit_files failed" in str(excinfo.value)
