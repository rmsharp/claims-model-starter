"""Thin ``PyGithub`` adapter for :class:`RepoClient`.

This is the production adapter for the Website Agent's GitHub path. It is
intentionally thin:

- The constructor wraps ``github.Github(auth=Auth.Token(...), base_url=...)``.
- ``create_project`` resolves the target owner (organization first, then
  user) and creates a repo under it, translating name collisions to
  :class:`RepoNameConflictError` and every other ``GithubException`` to
  :class:`RepoClientError`.
- ``commit_files`` issues a single atomic multi-file commit by walking the
  git data API: blob → tree → commit → ref.edit. This mirrors
  ``gitlab_adapter.commit_files``'s "one commit per call" contract so the
  RETRY_BACKOFF loop in the LangGraph sees identical semantics on both
  platforms.

Per the Phase 4B handoff (architecture-plan §14): this module is **not**
unit-tested against a live GitHub. The test suite confirms it imports,
implements the protocol, translates a few representative exceptions, and
drives the commit_files git-dance against mocks; anything stronger requires
a test GitHub account and is a Phase 5 concern.

The import of :mod:`github` is eager here (``PyGithub`` is in the
``agents`` optional extras). Callers that don't need GitHub should use
:class:`FakeRepoClient` and never construct this class.

Nested namespaces are **not** supported. GitLab allows arbitrary group
nesting ("org/sub/sub"); GitHub has a single owner level. If callers pass a
namespace containing ``"/"`` we fail loudly with :class:`RepoClientError`
rather than silently flattening.
"""

from __future__ import annotations

from typing import Any

from github import Auth, Github, GithubException, InputGitTreeElement, UnknownObjectException

from model_project_constructor.agents.website.protocol import (
    CommitInfo,
    ProjectInfo,
    RepoClient,
    RepoClientError,
    RepoNameConflictError,
)


class PyGithubAdapter(RepoClient):
    """``RepoClient`` implementation backed by ``PyGithub``.

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
        self._gh: Any = Github(auth=Auth.Token(private_token), base_url=host_url)

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

        owner: Any
        try:
            owner = self._gh.get_organization(namespace)
        except UnknownObjectException:
            try:
                owner = self._gh.get_user(namespace)
            except GithubException as exc:
                raise RepoClientError(
                    f"owner lookup failed for {namespace!r}: {exc}"
                ) from exc
        except GithubException as exc:
            raise RepoClientError(
                f"owner lookup failed for {namespace!r}: {exc}"
            ) from exc

        private = visibility != "public"
        try:
            repo = owner.create_repo(name=name, private=private)
        except GithubException as exc:
            if _is_name_conflict(exc):
                raise RepoNameConflictError(name) from exc
            raise RepoClientError(
                f"create_project failed for {name!r}: {exc}"
            ) from exc

        return ProjectInfo(
            id=str(repo.full_name),
            url=str(repo.html_url),
            default_branch=str(getattr(repo, "default_branch", None) or "main"),
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
            repo = self._gh.get_repo(project_id)
        except GithubException as exc:
            raise RepoClientError(
                f"project lookup failed for id={project_id!r}: {exc}"
            ) from exc

        sorted_items = sorted(files.items())
        try:
            ref = repo.get_git_ref(f"heads/{branch}")
            parent_commit = repo.get_git_commit(ref.object.sha)
            tree_elements = [
                InputGitTreeElement(
                    path=path,
                    mode="100644",
                    type="blob",
                    sha=repo.create_git_blob(content, "utf-8").sha,
                )
                for path, content in sorted_items
            ]
            tree = repo.create_git_tree(tree_elements, base_tree=parent_commit.tree)
            commit = repo.create_git_commit(message, tree, [parent_commit])
            ref.edit(sha=commit.sha)
        except GithubException as exc:
            raise RepoClientError(
                f"commit_files failed (project={project_id!r}, branch={branch!r}): {exc}"
            ) from exc

        return CommitInfo(
            sha=str(commit.sha),
            files_committed=[path for path, _ in sorted_items],
        )


def _is_name_conflict(exc: GithubException) -> bool:
    """Detect a GitHub "name already exists" error from PyGithub.

    GitHub returns a 422 Unprocessable Entity with a response body of the
    form ``{"errors": [{"message": "name already exists on this account"}]}``.
    We match loosely (any 422 whose body mentions "already exists") so minor
    wording changes don't break the adapter.
    """

    if getattr(exc, "status", None) != 422:
        return False
    data = getattr(exc, "data", None)
    if isinstance(data, dict):
        for err in data.get("errors", []) or []:
            if isinstance(err, dict):
                message = str(err.get("message", "")).lower()
                if "already exists" in message:
                    return True
    return "already exists" in str(exc).lower()


__all__ = ["PyGithubAdapter"]
