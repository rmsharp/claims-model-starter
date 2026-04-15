"""Tests for the in-memory FakeRepoClient."""

from __future__ import annotations

import pytest

from model_project_constructor.agents.website.fake_client import FakeRepoClient
from model_project_constructor.agents.website.protocol import (
    RepoNameConflictError,
)


class TestFakeRepoClient:
    def test_create_project_returns_info(self) -> None:
        client = FakeRepoClient()
        info = client.create_project(
            namespace="ds/drafts",
            name="my-model",
            visibility="private",
        )
        assert info.id == "1000"
        assert info.url == "https://fake.host.test/ds/drafts/my-model"
        assert info.default_branch == "main"

    def test_create_project_increments_ids(self) -> None:
        client = FakeRepoClient()
        a = client.create_project(
            namespace="ds/drafts", name="a", visibility="private"
        )
        b = client.create_project(
            namespace="ds/drafts", name="b", visibility="private"
        )
        assert int(b.id) == int(a.id) + 1

    def test_seeded_name_raises_conflict(self) -> None:
        client = FakeRepoClient(existing_names={"ds/drafts/my-model"})
        with pytest.raises(RepoNameConflictError):
            client.create_project(
                namespace="ds/drafts",
                name="my-model",
                visibility="private",
            )

    def test_creating_same_name_twice_raises(self) -> None:
        client = FakeRepoClient()
        client.create_project(
            namespace="ds/drafts", name="m", visibility="private"
        )
        with pytest.raises(RepoNameConflictError):
            client.create_project(
                namespace="ds/drafts", name="m", visibility="private"
            )

    def test_commit_files_stores_content(self) -> None:
        client = FakeRepoClient()
        info = client.create_project(
            namespace="ds/drafts", name="m", visibility="private"
        )
        commit = client.commit_files(
            project_id=info.id,
            branch="main",
            files={"README.md": "hi", "src/__init__.py": ""},
            message="feat: init",
        )
        assert len(commit.sha) == 40
        assert commit.files_committed == ["README.md", "src/__init__.py"]

        files = client.get_files(info.id)
        assert files["README.md"] == "hi"

    def test_commit_files_deterministic_sha(self) -> None:
        """Same (message, branch, paths) → same SHA across client instances."""
        c1 = FakeRepoClient()
        c2 = FakeRepoClient()
        p1 = c1.create_project(namespace="g", name="n", visibility="private")
        p2 = c2.create_project(namespace="g", name="n2", visibility="private")
        files = {"a": "x", "b": "y"}
        sha1 = c1.commit_files(
            project_id=p1.id, branch="main", files=files, message="m"
        ).sha
        sha2 = c2.commit_files(
            project_id=p2.id, branch="main", files=files, message="m"
        ).sha
        assert sha1 == sha2

    def test_get_project_by_name(self) -> None:
        client = FakeRepoClient()
        client.create_project(namespace="g", name="foo", visibility="private")
        found = client.get_project_by_name("foo")
        assert found is not None
        assert found.name == "foo"
        assert client.get_project_by_name("missing") is None

    def test_multiple_commits_tracked(self) -> None:
        client = FakeRepoClient()
        info = client.create_project(
            namespace="g", name="n", visibility="private"
        )
        client.commit_files(
            project_id=info.id, branch="main", files={"a": "1"}, message="m1"
        )
        client.commit_files(
            project_id=info.id, branch="main", files={"b": "2"}, message="m2"
        )
        project = client.projects[info.id]
        assert project.commits == ["m1", "m2"]
        assert project.files == {"a": "1", "b": "2"}
        assert project.full_path == "g/n"
