"""Repo client boundary for the Website Agent.

Per architecture-plan §4.3 the agent talks to a repository host (GitLab in
production today, GitHub planned) via a thin adapter, but nodes must be
unit-testable without a live host. This ``Protocol`` is the boundary: tests
pass a ``FakeRepoClient``, production passes a thin wrapper around
``python-gitlab`` or ``PyGithub``.

The Phase 4A CLI (`--fake`) uses the fake client so it can show a file tree
of what *would* have been committed without needing credentials.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class ProjectInfo:
    """Information returned by :meth:`RepoClient.create_project`.

    ``id`` is a host-opaque string identifier: GitLab uses a stringified
    integer project ID, GitHub uses ``"owner/name"``. Callers should treat
    it as an opaque token and pass it back to :meth:`RepoClient.commit_files`
    unchanged.
    """

    id: str
    url: str
    default_branch: str


@dataclass
class CommitInfo:
    """Information returned by :meth:`RepoClient.commit_files`."""

    sha: str
    files_committed: list[str]


class RepoClient(Protocol):
    """Strategy for the website agent's repository host operations.

    Implementations MUST raise :class:`RepoNameConflictError` when a
    create-project call collides with an existing project name in the
    target namespace. Any other host failure should raise
    :class:`RepoClientError`.
    """

    def create_project(
        self,
        *,
        namespace: str,
        name: str,
        visibility: str,
    ) -> ProjectInfo: ...

    def commit_files(
        self,
        *,
        project_id: str,
        branch: str,
        files: dict[str, str],
        message: str,
    ) -> CommitInfo: ...


class RepoClientError(RuntimeError):
    """Base class for all RepoClient failures the agent handles."""


class RepoNameConflictError(RepoClientError):
    """Raised when the requested project name already exists."""

    def __init__(self, name: str):
        super().__init__(f"Project name already exists: {name!r}")
        self.name = name
