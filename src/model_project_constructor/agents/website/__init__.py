"""Website Agent (architecture-plan §4.3, §10, §11).

Phase 4A public surface:

- :class:`WebsiteAgent` — high-level runner
- :class:`RepoClient` — Protocol for repository-host-backed implementations
- :class:`FakeRepoClient` — in-memory test double + CLI backend
- :func:`build_website_graph` — low-level compiled LangGraph
- :func:`initial_state`, :func:`build_repo_project_result` — state helpers
- Template helpers in :mod:`.templates` are exposed for tests
"""

from __future__ import annotations

from model_project_constructor.agents.website.agent import WebsiteAgent
from model_project_constructor.agents.website.fake_client import (
    FakeProject,
    FakeRepoClient,
)
from model_project_constructor.agents.website.github_adapter import PyGithubAdapter
from model_project_constructor.agents.website.gitlab_adapter import PythonGitLabAdapter
from model_project_constructor.agents.website.governance_templates import (
    build_analysis_files,
    build_governance_files,
    build_model_registry_entry,
    build_regulatory_mapping,
    build_test_files,
    is_governance_artifact,
)
from model_project_constructor.agents.website.graph import build_website_graph
from model_project_constructor.agents.website.nodes import (
    build_repo_project_result,
    make_nodes,
    route_after_commit,
    route_after_create,
)
from model_project_constructor.agents.website.protocol import (
    CommitInfo,
    ProjectInfo,
    RepoClient,
    RepoClientError,
    RepoNameConflictError,
)
from model_project_constructor.agents.website.state import (
    MAX_COMMIT_ATTEMPTS,
    MAX_NAME_CONFLICT_ATTEMPTS,
    RETRY_BASE_DELAY_SECONDS,
    WebsiteState,
    initial_state,
)
from model_project_constructor.agents.website.templates import (
    build_base_files,
    derive_project_name,
    derive_project_slug,
)

__all__ = [
    "WebsiteAgent",
    "RepoClient",
    "RepoClientError",
    "RepoNameConflictError",
    "ProjectInfo",
    "CommitInfo",
    "FakeRepoClient",
    "FakeProject",
    "PyGithubAdapter",
    "PythonGitLabAdapter",
    "build_website_graph",
    "build_repo_project_result",
    "build_governance_files",
    "build_analysis_files",
    "build_test_files",
    "build_model_registry_entry",
    "build_regulatory_mapping",
    "is_governance_artifact",
    "make_nodes",
    "route_after_create",
    "route_after_commit",
    "WebsiteState",
    "initial_state",
    "MAX_NAME_CONFLICT_ATTEMPTS",
    "MAX_COMMIT_ATTEMPTS",
    "RETRY_BASE_DELAY_SECONDS",
    "build_base_files",
    "derive_project_name",
    "derive_project_slug",
]
