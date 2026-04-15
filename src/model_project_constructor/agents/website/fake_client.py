"""In-memory fake ``RepoClient`` for tests and the ``--fake`` CLI.

Mirrors the Phase 3A ``FixtureLLMClient`` pattern: a deterministic,
stateless-enough double that lets us exercise the whole graph end-to-end
without network or credentials. Every committed file is captured in
``FakeRepoClient.projects`` so tests can assert exact content.

SHA generation is deterministic (sha1 of message + sorted paths) so test
assertions are stable across runs.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

from model_project_constructor.agents.website.protocol import (
    CommitInfo,
    ProjectInfo,
    RepoClient,
    RepoNameConflictError,
)


@dataclass
class FakeProject:
    id: str
    name: str
    namespace: str
    url: str
    default_branch: str
    visibility: str
    files: dict[str, str] = field(default_factory=dict)
    commits: list[str] = field(default_factory=list)

    @property
    def full_path(self) -> str:
        return f"{self.namespace}/{self.name}"


class FakeRepoClient(RepoClient):
    """In-memory repo host stand-in.

    Pre-existing project names can be seeded via ``existing_names`` so
    tests can exercise the name-conflict suffix logic. The client tracks
    every created project in :attr:`projects` keyed by project id, and
    also exposes :meth:`get_files` for path→content lookups.
    """

    def __init__(
        self,
        *,
        existing_names: set[str] | None = None,
        base_url: str = "https://fake.host.test",
    ) -> None:
        self._existing: set[str] = set(existing_names or [])
        self._base_url = base_url
        self._next_id = 1000
        self.projects: dict[str, FakeProject] = {}

    # --- RepoClient protocol ----------------------------------------------

    def create_project(
        self,
        *,
        namespace: str,
        name: str,
        visibility: str,
    ) -> ProjectInfo:
        full = f"{namespace}/{name}"
        if full in self._existing:
            raise RepoNameConflictError(name)
        self._existing.add(full)

        project_id = str(self._next_id)
        project = FakeProject(
            id=project_id,
            name=name,
            namespace=namespace,
            url=f"{self._base_url}/{namespace}/{name}",
            default_branch="main",
            visibility=visibility,
        )
        self.projects[project_id] = project
        self._next_id += 1

        return ProjectInfo(
            id=project.id,
            url=project.url,
            default_branch=project.default_branch,
        )

    def commit_files(
        self,
        *,
        project_id: str,
        branch: str,
        files: dict[str, str],
        message: str,
    ) -> CommitInfo:
        project = self.projects[project_id]
        project.files.update(files)
        project.commits.append(message)

        digest_input = f"{message}|{branch}|" + "|".join(sorted(files))
        sha = hashlib.sha1(digest_input.encode("utf-8")).hexdigest()
        return CommitInfo(sha=sha, files_committed=sorted(files))

    # --- test helpers -----------------------------------------------------

    def get_files(self, project_id: str) -> dict[str, str]:
        """Return a copy of the files committed to ``project_id``."""
        return dict(self.projects[project_id].files)

    def get_project_by_name(self, name: str) -> FakeProject | None:
        for project in self.projects.values():
            if project.name == name:
                return project
        return None
