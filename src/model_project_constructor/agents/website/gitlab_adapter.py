"""Thin direct-``httpx`` adapter for :class:`RepoClient` (GitLab).

This is the production adapter for the Website Agent's GitLab path. It is
intentionally thin:

- The constructor builds an ``httpx.Client`` scoped to ``{host_url}/api/v4``
  with a ``PRIVATE-TOKEN`` auth header. No network call happens at
  construction time.
- ``create_project`` resolves the target group, creates a project inside
  it, and translates name collisions to :class:`RepoNameConflictError` and
  every other GitLab error to :class:`RepoClientError`.
- ``commit_files`` issues a single multi-file commit through the GitLab
  commits API.

Per the Phase 4B handoff (architecture-plan §14): this module is **not**
unit-tested against a live GitLab. The test suite drives it against
``httpx.MockTransport`` and confirms it implements the protocol and maps
representative wire-level responses; anything stronger requires a test
GitLab instance and is a Phase 5 concern.

Migrated off ``python-gitlab`` (LGPL-3.0-or-later) to direct ``httpx``
calls per ``docs/planning/httpx-adapter-migration.md`` Phase 1 — the
needed surface is 4 REST calls, so a full SDK adds licensing weight
without functional benefit.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

import httpx

from model_project_constructor.agents.website.protocol import (
    CommitInfo,
    ProjectInfo,
    RepoClient,
    RepoClientError,
    RepoNameConflictError,
)


class GitLabAdapter(RepoClient):
    """``RepoClient`` implementation backed by direct calls to the GitLab
    REST API (``/api/v4``).

    Usage::

        from model_project_constructor.agents.website import (
            GitLabAdapter, WebsiteAgent,
        )
        client = GitLabAdapter(
            host_url="https://gitlab.example.com",
            private_token=os.environ["GITLAB_TOKEN"],
        )
        agent = WebsiteAgent(client)
    """

    def __init__(
        self,
        *,
        host_url: str,
        private_token: str,
        ssl_verify: bool = True,
    ) -> None:
        self._client = httpx.Client(
            base_url=f"{host_url.rstrip('/')}/api/v4",
            headers={"PRIVATE-TOKEN": private_token},
            verify=ssl_verify,
        )

    # ------------------------------------------------------------------
    # RepoClient protocol
    # ------------------------------------------------------------------

    def create_project(
        self,
        *,
        namespace: str,
        name: str,
        visibility: str,
    ) -> ProjectInfo:
        try:
            response = self._client.get(f"/groups/{quote(namespace, safe='')}")
        except httpx.HTTPError as exc:
            raise RepoClientError(
                f"group lookup failed for {namespace!r}: {exc}"
            ) from exc
        _ok_or_raise(response, f"group lookup failed for {namespace!r}")
        group = _parse_json(response, f"group lookup failed for {namespace!r}")

        try:
            response = self._client.post(
                "/projects",
                json={
                    "name": name,
                    "path": name,
                    "namespace_id": group["id"],
                    "visibility": visibility,
                },
            )
        except httpx.HTTPError as exc:
            raise RepoClientError(f"create_project failed for {name!r}: {exc}") from exc
        if not _is_2xx(response):
            if _is_name_conflict(response):
                raise RepoNameConflictError(name)
            raise RepoClientError(
                f"create_project failed for {name!r}: "
                f"{response.status_code} {response.text}"
            )
        project = _parse_json(response, f"create_project failed for {name!r}")

        return ProjectInfo(
            id=str(project["id"]),
            url=str(project["web_url"]),
            default_branch=str(project.get("default_branch") or "main"),
        )

    def commit_files(
        self,
        *,
        project_id: str,
        branch: str,
        files: dict[str, str],
        message: str,
    ) -> CommitInfo:
        try:
            response = self._client.get(f"/projects/{project_id}")
        except httpx.HTTPError as exc:
            raise RepoClientError(
                f"project lookup failed for id={project_id}: {exc}"
            ) from exc
        _ok_or_raise(response, f"project lookup failed for id={project_id}")

        actions = [
            {
                "action": "create",
                "file_path": path,
                "content": content,
            }
            for path, content in sorted(files.items())
        ]
        try:
            response = self._client.post(
                f"/projects/{project_id}/repository/commits",
                json={
                    "branch": branch,
                    "commit_message": message,
                    "actions": actions,
                },
            )
        except httpx.HTTPError as exc:
            raise RepoClientError(
                f"commit_files failed (project={project_id}, branch={branch}): {exc}"
            ) from exc
        _ok_or_raise(
            response, f"commit_files failed (project={project_id}, branch={branch})"
        )
        commit = _parse_json(
            response, f"commit_files failed (project={project_id}, branch={branch})"
        )

        return CommitInfo(
            sha=str(commit["id"]),
            files_committed=sorted(files),
        )


def _is_2xx(response: httpx.Response) -> bool:
    return 200 <= response.status_code < 300


def _ok_or_raise(response: httpx.Response, context: str) -> None:
    """Raise :class:`RepoClientError` if ``response`` is not a 2xx.

    Deliberately stricter than "not >= 400": ``httpx.Client`` does not
    follow redirects by default (unlike the ``requests``-based transport
    the old ``python-gitlab`` adapter used), so a 3xx must also be treated
    as a failure rather than silently falling through to a body parse.
    """

    if not _is_2xx(response):
        raise RepoClientError(f"{context}: {response.status_code} {response.text}")


def _parse_json(response: httpx.Response, context: str) -> dict[str, Any]:
    """Parse a 2xx response body, raising :class:`RepoClientError` on
    malformed JSON instead of letting a raw ``ValueError`` escape."""

    try:
        body: dict[str, Any] = response.json()
    except ValueError as exc:
        raise RepoClientError(f"{context}: invalid JSON body: {exc}") from exc
    return body


def _is_name_conflict(response: httpx.Response) -> bool:
    """Detect a GitLab "name already taken" error from a create-project response.

    GitLab returns a 400/409 with a body that looks like
    ``{"name":["has already been taken"],"path":["has already been taken"]}``.
    We match loosely so minor wording changes don't break the adapter.
    """

    if response.status_code not in (400, 409):
        return False
    try:
        body: Any = response.json()
    except ValueError:
        body = None
    text = str(body) if body is not None else response.text
    lowered = text.lower()
    return "already been taken" in lowered or "already exists" in lowered


__all__ = ["GitLabAdapter"]
