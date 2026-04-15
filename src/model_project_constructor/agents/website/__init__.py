"""Website Agent (architecture-plan §4.3, §10, §11).

Phase 4A public surface:

- :class:`WebsiteAgent` — high-level runner
- :class:`GitLabClient` — Protocol for GitLab-backed implementations
- :class:`FakeGitLabClient` — in-memory test double + CLI backend
- :func:`build_website_graph` — low-level compiled LangGraph
- :func:`initial_state`, :func:`build_gitlab_project_result` — state helpers
- Template helpers in :mod:`.templates` are exposed for tests
"""

from __future__ import annotations

from model_project_constructor.agents.website.agent import WebsiteAgent
from model_project_constructor.agents.website.fake_client import (
    FakeGitLabClient,
    FakeProject,
)
from model_project_constructor.agents.website.graph import build_website_graph
from model_project_constructor.agents.website.nodes import (
    build_gitlab_project_result,
    make_nodes,
    route_after_create,
)
from model_project_constructor.agents.website.protocol import (
    CommitInfo,
    GitLabClient,
    GitLabClientError,
    ProjectInfo,
    ProjectNameConflictError,
)
from model_project_constructor.agents.website.state import (
    MAX_NAME_CONFLICT_ATTEMPTS,
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
    "GitLabClient",
    "GitLabClientError",
    "ProjectNameConflictError",
    "ProjectInfo",
    "CommitInfo",
    "FakeGitLabClient",
    "FakeProject",
    "build_website_graph",
    "build_gitlab_project_result",
    "make_nodes",
    "route_after_create",
    "WebsiteState",
    "initial_state",
    "MAX_NAME_CONFLICT_ATTEMPTS",
    "build_base_files",
    "derive_project_name",
    "derive_project_slug",
]
