"""Thin ``python-gitlab`` adapter for :class:`GitLabClient`.

This is the production adapter for the Website Agent. It is intentionally
thin:

- The constructor wraps ``gitlab.Gitlab(url, private_token=...)``.
- ``create_project`` resolves the target group and creates a project
  inside it, translating name collisions to
  :class:`ProjectNameConflictError` and every other GitLab error to
  :class:`GitLabClientError`.
- ``commit_files`` issues a single multi-file commit through the
  python-gitlab commits API.

Per the Phase 4B handoff (architecture-plan §14): this module is
**not** unit-tested against a live GitLab. The test suite confirms it
imports, implements the protocol, and maps a few representative
exceptions; anything stronger requires a test GitLab instance and is a
Phase 5 concern.

The import of :mod:`gitlab` is eager here (python-gitlab is already in
the ``agents`` optional extras). Callers that don't need GitLab should
use :class:`FakeGitLabClient` and never construct this class.
"""

from __future__ import annotations

from typing import Any

import gitlab
from gitlab.exceptions import GitlabCreateError, GitlabError, GitlabGetError

from model_project_constructor.agents.website.protocol import (
    CommitInfo,
    GitLabClient,
    GitLabClientError,
    ProjectInfo,
    ProjectNameConflictError,
)


class PythonGitLabAdapter(GitLabClient):
    """``GitLabClient`` implementation backed by ``python-gitlab``.

    Usage::

        from model_project_constructor.agents.website import (
            PythonGitLabAdapter, WebsiteAgent,
        )
        client = PythonGitLabAdapter(
            gitlab_url="https://gitlab.example.com",
            private_token=os.environ["GITLAB_TOKEN"],
        )
        agent = WebsiteAgent(client)
    """

    def __init__(
        self,
        *,
        gitlab_url: str,
        private_token: str,
        ssl_verify: bool = True,
    ) -> None:
        self._gl: Any = gitlab.Gitlab(
            gitlab_url, private_token=private_token, ssl_verify=ssl_verify
        )

    # ------------------------------------------------------------------
    # GitLabClient protocol
    # ------------------------------------------------------------------

    def create_project(
        self,
        *,
        group_path: str,
        name: str,
        visibility: str,
    ) -> ProjectInfo:
        try:
            group = self._gl.groups.get(group_path)
        except GitlabGetError as exc:
            raise GitLabClientError(
                f"group lookup failed for {group_path!r}: {exc}"
            ) from exc
        except GitlabError as exc:
            raise GitLabClientError(
                f"group lookup failed for {group_path!r}: {exc}"
            ) from exc

        try:
            project = self._gl.projects.create(
                {
                    "name": name,
                    "path": name,
                    "namespace_id": group.id,
                    "visibility": visibility,
                }
            )
        except GitlabCreateError as exc:
            message = str(exc)
            if _is_name_conflict(exc):
                raise ProjectNameConflictError(name) from exc
            raise GitLabClientError(
                f"create_project failed for {name!r}: {message}"
            ) from exc
        except GitlabError as exc:
            raise GitLabClientError(
                f"create_project failed for {name!r}: {exc}"
            ) from exc

        return ProjectInfo(
            id=int(project.id),
            url=str(project.web_url),
            default_branch=str(getattr(project, "default_branch", None) or "main"),
        )

    def commit_files(
        self,
        *,
        project_id: int,
        branch: str,
        files: dict[str, str],
        message: str,
    ) -> CommitInfo:
        try:
            project = self._gl.projects.get(project_id)
        except GitlabError as exc:
            raise GitLabClientError(
                f"project lookup failed for id={project_id}: {exc}"
            ) from exc

        actions = [
            {
                "action": "create",
                "file_path": path,
                "content": content,
            }
            for path, content in sorted(files.items())
        ]
        try:
            commit = project.commits.create(
                {
                    "branch": branch,
                    "commit_message": message,
                    "actions": actions,
                }
            )
        except GitlabError as exc:
            raise GitLabClientError(
                f"commit_files failed (project={project_id}, branch={branch}): {exc}"
            ) from exc

        return CommitInfo(
            sha=str(commit.id),
            files_committed=sorted(files),
        )


def _is_name_conflict(exc: GitlabCreateError) -> bool:
    """Detect a GitLab "name already taken" error from python-gitlab.

    GitLab returns a 400 with an error_message that looks like
    ``{"name":["has already been taken"],"path":["has already been taken"]}``.
    We match loosely so minor wording changes don't break the adapter.
    """

    response_code = getattr(exc, "response_code", None)
    text = str(getattr(exc, "error_message", "")) or str(exc)
    if response_code not in (400, 409):
        return False
    lowered = text.lower()
    return "already been taken" in lowered or "already exists" in lowered


__all__ = ["PythonGitLabAdapter"]
