"""Website Agent LangGraph wiring (architecture-plan §10).

Phase 4B topology:

    START ─▶ CREATE_PROJECT ─▶ SCAFFOLD_BASE ─▶ SCAFFOLD_GOVERNANCE ─▶
             SCAFFOLD_ANALYSIS ─▶ SCAFFOLD_TESTS ─▶ INITIAL_COMMITS ─▶ END
                    │                                     │
                    └── FAILED ──▶ END                    │ repo error
                                                           ▼
                                                      RETRY_BACKOFF
                                                           │
                                                           └──▶ INITIAL_COMMITS

The retry self-loop is bounded by ``MAX_COMMIT_ATTEMPTS`` in the node itself;
the graph topology trusts the node's routing decision.
"""

from __future__ import annotations

from typing import Any, Callable

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from model_project_constructor.agents.website.nodes import (
    make_nodes,
    route_after_commit,
    route_after_create,
)
from model_project_constructor.agents.website.protocol import RepoClient
from model_project_constructor.agents.website.state import WebsiteState


def build_website_graph(
    client: RepoClient,
    *,
    checkpointer: Any | None = None,
    sleep: Callable[[float], None] | None = None,
) -> Any:
    """Compile the website agent graph.

    Mirrors ``build_intake_graph`` in Phase 3A: the checkpointer kwarg
    defaults to an in-memory saver for the CLI / fixture path. A future
    long-running driver (e.g. an orchestrator that persists website
    agent runs across restarts) can pass a ``SqliteSaver`` here.

    ``sleep`` is an optional test hook that overrides the default
    ``time.sleep`` used by ``retry_backoff``. Production leaves it at the
    default so transient errors yield real 1s/2s/4s delays.
    """

    if sleep is None:
        nodes = make_nodes(client)
    else:
        nodes = make_nodes(client, sleep=sleep)

    g = StateGraph(WebsiteState)
    g.add_node("create_project", nodes["create_project"])
    g.add_node("scaffold_base", nodes["scaffold_base"])
    g.add_node("scaffold_governance", nodes["scaffold_governance"])
    g.add_node("scaffold_analysis", nodes["scaffold_analysis"])
    g.add_node("scaffold_tests", nodes["scaffold_tests"])
    g.add_node("initial_commits", nodes["initial_commits"])
    g.add_node("retry_backoff", nodes["retry_backoff"])

    g.add_edge(START, "create_project")
    g.add_conditional_edges(
        "create_project",
        route_after_create,
        {"scaffold_base": "scaffold_base", "end": END},
    )
    g.add_edge("scaffold_base", "scaffold_governance")
    g.add_edge("scaffold_governance", "scaffold_analysis")
    g.add_edge("scaffold_analysis", "scaffold_tests")
    g.add_edge("scaffold_tests", "initial_commits")
    g.add_conditional_edges(
        "initial_commits",
        route_after_commit,
        {"retry_backoff": "retry_backoff", "end": END},
    )
    g.add_edge("retry_backoff", "initial_commits")

    return g.compile(checkpointer=checkpointer or MemorySaver())
