"""GitLab client boundary for the Website Agent.

Per architecture-plan §4.3 the agent talks to GitLab via ``python-gitlab``
in production, but nodes must be unit-testable without a live GitLab. This
``Protocol`` is the boundary: tests pass a ``FakeGitLabClient``, production
passes a thin wrapper around ``python-gitlab``.

The Phase 4A CLI (`--fake-gitlab`) uses the fake client so it can show a
file tree of what *would* have been committed without needing credentials.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class ProjectInfo:
    """Information returned by :meth:`GitLabClient.create_project`."""

    id: int
    url: str
    default_branch: str


@dataclass
class CommitInfo:
    """Information returned by :meth:`GitLabClient.commit_files`."""

    sha: str
    files_committed: list[str]


class GitLabClient(Protocol):
    """Strategy for the website agent's GitLab operations.

    Implementations MUST raise :class:`ProjectNameConflictError` when a
    create-project call collides with an existing project name in the
    target group. Any other GitLab failure should raise
    :class:`GitLabClientError`.
    """

    def create_project(
        self,
        *,
        group_path: str,
        name: str,
        visibility: str,
    ) -> ProjectInfo: ...

    def commit_files(
        self,
        *,
        project_id: int,
        branch: str,
        files: dict[str, str],
        message: str,
    ) -> CommitInfo: ...


class GitLabClientError(RuntimeError):
    """Base class for all GitLabClient failures the agent handles."""


class ProjectNameConflictError(GitLabClientError):
    """Raised when the requested project name already exists."""

    def __init__(self, name: str):
        super().__init__(f"Project name already exists: {name!r}")
        self.name = name
