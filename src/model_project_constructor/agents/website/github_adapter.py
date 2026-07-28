"""Thin direct-``httpx`` adapter for :class:`RepoClient` (GitHub).

This is the production adapter for the Website Agent's GitHub path. It is
intentionally thin:

- The constructor builds an ``httpx.Client`` scoped to ``host_url``
  (default ``https://api.github.com``; pass a GitHub Enterprise API URL,
  e.g. ``https://github.example.com/api/v3``, for GHE) with a bearer-token
  ``Authorization`` header. No network call happens at construction time.
- ``create_project`` resolves the target owner (organization first, then
  the authenticated user — GitHub's API only allows creating a repo under
  an organization or the token's own account, never an arbitrary
  third-party user) and creates a repo under it, translating name
  collisions to :class:`RepoNameConflictError` and every other error to
  :class:`RepoClientError`.
- ``commit_files`` issues a single atomic multi-file commit by walking the
  git data API: ref -> parent commit -> blobs -> tree -> commit -> ref
  update. This mirrors ``gitlab_adapter.commit_files``'s "one commit per
  call" contract so the RETRY_BACKOFF loop in the LangGraph sees identical
  semantics on both platforms.

Per the Phase 4B handoff (architecture-plan §14): this module is **not**
unit-tested against a live GitHub. The test suite drives it against
``httpx.MockTransport`` and confirms it implements the protocol and maps
representative wire-level responses; anything stronger requires a test
GitHub account and is a Phase 5 concern.

Nested namespaces are **not** supported. GitLab allows arbitrary group
nesting ("org/sub/sub"); GitHub has a single owner level. If callers pass a
namespace containing ``"/"`` we fail loudly with :class:`RepoClientError`
rather than silently flattening.

Migrated off ``PyGithub`` (LGPL-3.0-only) to direct ``httpx`` calls per
``docs/planning/httpx-adapter-migration.md`` Phase 2 — the needed surface
is the standard git-database commit dance, so a full SDK adds licensing
weight without functional benefit.
"""

from __future__ import annotations

from typing import Any

import httpx

from model_project_constructor.agents.website.protocol import (
    CommitInfo,
    ProjectInfo,
    RepoClient,
    RepoClientError,
    RepoNameConflictError,
)


class PyGithubAdapter(RepoClient):
    """``RepoClient`` implementation backed by direct calls to the GitHub
    REST API.

    Usage::

        from model_project_constructor.agents.website import (
            PyGithubAdapter, WebsiteAgent,
        )
        client = PyGithubAdapter(
            host_url="https://api.github.com",
            private_token=os.environ["GITHUB_TOKEN"],
        )
        agent = WebsiteAgent(client, ci_platform="github")

    For GitHub Enterprise, pass the enterprise API URL as ``host_url``
    (e.g. ``"https://github.example.com/api/v3"``).
    """

    def __init__(
        self,
        *,
        private_token: str,
        host_url: str = "https://api.github.com",
    ) -> None:
        self._client = httpx.Client(
            base_url=host_url.rstrip("/"),
            headers={
                "Authorization": f"Bearer {private_token}",
                "Accept": "application/vnd.github+json",
            },
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
        if "/" in namespace:
            raise RepoClientError(
                f"nested namespace {namespace!r} not supported by GitHub adapter "
                "— flatten before passing"
            )

        create_path = self._resolve_owner_create_path(namespace)

        private = visibility != "public"
        try:
            response = self._client.post(
                create_path, json={"name": name, "private": private}
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
        repo = _parse_json(response, f"create_project failed for {name!r}")

        return ProjectInfo(
            id=str(repo["full_name"]),
            url=str(repo["html_url"]),
            default_branch=str(repo.get("default_branch") or "main"),
        )

    def _resolve_owner_create_path(self, namespace: str) -> str:
        """Return the repo-creation path for ``namespace``.

        Tries organization first (``GET /orgs/{namespace}``); a 404 falls
        back to treating ``namespace`` as a user account. GitHub's API only
        allows creating a repo under an organization or the *authenticated*
        user's own account (never an arbitrary third-party user), so the
        user branch still confirms the account exists (preserving the old
        adapter's "owner lookup failed" failure mode) but creates via
        ``POST /user/repos`` rather than a namespace-scoped path.
        """

        try:
            response = self._client.get(f"/orgs/{namespace}")
        except httpx.HTTPError as exc:
            raise RepoClientError(
                f"owner lookup failed for {namespace!r}: {exc}"
            ) from exc
        if response.status_code == 200:
            return f"/orgs/{namespace}/repos"
        if response.status_code != 404:
            raise RepoClientError(
                f"owner lookup failed for {namespace!r}: "
                f"{response.status_code} {response.text}"
            )

        try:
            response = self._client.get(f"/users/{namespace}")
        except httpx.HTTPError as exc:
            raise RepoClientError(
                f"owner lookup failed for {namespace!r}: {exc}"
            ) from exc
        _ok_or_raise(response, f"owner lookup failed for {namespace!r}")
        return "/user/repos"

    def commit_files(
        self,
        *,
        project_id: str,
        branch: str,
        files: dict[str, str],
        message: str,
    ) -> CommitInfo:
        try:
            response = self._client.get(f"/repos/{project_id}")
        except httpx.HTTPError as exc:
            raise RepoClientError(
                f"project lookup failed for id={project_id!r}: {exc}"
            ) from exc
        _ok_or_raise(response, f"project lookup failed for id={project_id!r}")

        context = f"commit_files failed (project={project_id!r}, branch={branch!r})"

        try:
            response = self._client.get(f"/repos/{project_id}/git/ref/heads/{branch}")
        except httpx.HTTPError as exc:
            raise RepoClientError(f"{context}: {exc}") from exc
        _ok_or_raise(response, context)
        parent_sha = _parse_json(response, context)["object"]["sha"]

        try:
            response = self._client.get(
                f"/repos/{project_id}/git/commits/{parent_sha}"
            )
        except httpx.HTTPError as exc:
            raise RepoClientError(f"{context}: {exc}") from exc
        _ok_or_raise(response, context)
        base_tree_sha = _parse_json(response, context)["tree"]["sha"]

        sorted_items = sorted(files.items())
        tree_elements: list[dict[str, str]] = []
        for path, content in sorted_items:
            try:
                response = self._client.post(
                    f"/repos/{project_id}/git/blobs",
                    json={"content": content, "encoding": "utf-8"},
                )
            except httpx.HTTPError as exc:
                raise RepoClientError(f"{context}: {exc}") from exc
            _ok_or_raise(response, context)
            blob_sha = _parse_json(response, context)["sha"]
            tree_elements.append(
                {"path": path, "mode": "100644", "type": "blob", "sha": blob_sha}
            )

        try:
            response = self._client.post(
                f"/repos/{project_id}/git/trees",
                json={"base_tree": base_tree_sha, "tree": tree_elements},
            )
        except httpx.HTTPError as exc:
            raise RepoClientError(f"{context}: {exc}") from exc
        _ok_or_raise(response, context)
        new_tree_sha = _parse_json(response, context)["sha"]

        try:
            response = self._client.post(
                f"/repos/{project_id}/git/commits",
                json={
                    "message": message,
                    "tree": new_tree_sha,
                    "parents": [parent_sha],
                },
            )
        except httpx.HTTPError as exc:
            raise RepoClientError(f"{context}: {exc}") from exc
        _ok_or_raise(response, context)
        commit_sha = _parse_json(response, context)["sha"]

        try:
            response = self._client.patch(
                f"/repos/{project_id}/git/refs/heads/{branch}",
                json={"sha": commit_sha},
            )
        except httpx.HTTPError as exc:
            raise RepoClientError(f"{context}: {exc}") from exc
        _ok_or_raise(response, context)

        return CommitInfo(
            sha=commit_sha,
            files_committed=sorted(files),
        )


def _is_2xx(response: httpx.Response) -> bool:
    return 200 <= response.status_code < 300


def _ok_or_raise(response: httpx.Response, context: str) -> None:
    """Raise :class:`RepoClientError` if ``response`` is not a 2xx.

    Deliberately stricter than "not >= 400": ``httpx.Client`` does not
    follow redirects by default (unlike the ``requests``-based transport
    the old ``PyGithub`` adapter used), so a 3xx must also be treated as a
    failure rather than silently falling through to a body parse.
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
    """Detect a GitHub "name already exists" error from a create-repo response.

    GitHub returns a 422 Unprocessable Entity with a body of the form
    ``{"errors": [{"message": "name already exists on this account"}]}``.
    We match loosely (any 422 whose body mentions "already exists"
    anywhere, not just in the ``errors`` list) so minor wording changes
    don't break the adapter.
    """

    if response.status_code != 422:
        return False
    try:
        body: Any = response.json()
    except ValueError:
        body = None
    if isinstance(body, dict):
        for err in body.get("errors", []) or []:
            if isinstance(err, dict):
                message = str(err.get("message", "")).lower()
                if "already exists" in message:
                    return True
    text = str(body) if body is not None else response.text
    return "already exists" in text.lower()


__all__ = ["PyGithubAdapter"]
