"""Website Agent LangGraph wiring (architecture-plan §10).

Phase 4A topology:

    START ─▶ CREATE_PROJECT ─▶ SCAFFOLD_BASE ─▶ INITIAL_COMMITS ─▶ END
                    │
                    └── FAILED ──▶ END

Phase 4B will insert SCAFFOLD_GOVERNANCE / SCAFFOLD_ANALYSIS /
SCAFFOLD_TESTS between SCAFFOLD_BASE and INITIAL_COMMITS, plus a
RETRY_BACKOFF loop off INITIAL_COMMITS for transient GitLab errors.
"""

from __future__ import annotations

from typing import Any

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from model_project_constructor.agents.website.nodes import (
    make_nodes,
    route_after_create,
)
from model_project_constructor.agents.website.protocol import GitLabClient
from model_project_constructor.agents.website.state import WebsiteState


def build_website_graph(
    client: GitLabClient,
    *,
    checkpointer: Any | None = None,
) -> Any:
    """Compile the website agent graph.

    Mirrors ``build_intake_graph`` in Phase 3A: the checkpointer kwarg
    defaults to an in-memory saver for the CLI / fixture path. A future
    long-running driver (e.g. an orchestrator that persists website
    agent runs across restarts) can pass a ``SqliteSaver`` here.
    """

    nodes = make_nodes(client)

    g = StateGraph(WebsiteState)
    g.add_node("create_project", nodes["create_project"])
    g.add_node("scaffold_base", nodes["scaffold_base"])
    g.add_node("initial_commits", nodes["initial_commits"])

    g.add_edge(START, "create_project")
    g.add_conditional_edges(
        "create_project",
        route_after_create,
        {"scaffold_base": "scaffold_base", "end": END},
    )
    g.add_edge("scaffold_base", "initial_commits")
    g.add_edge("initial_commits", END)

    return g.compile(checkpointer=checkpointer or MemorySaver())
