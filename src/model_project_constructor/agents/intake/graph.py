"""Intake Agent LangGraph wiring (architecture-plan §10)."""

from __future__ import annotations

from typing import Any

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from model_project_constructor.agents.intake.nodes import (
    make_nodes,
    route_after_evaluate,
    route_after_review,
)
from model_project_constructor.agents.intake.protocol import IntakeLLMClient
from model_project_constructor.agents.intake.state import IntakeState


def build_intake_graph(llm: IntakeLLMClient) -> Any:
    """Compile the intake graph with an in-memory checkpointer.

    The checkpointer is REQUIRED — LangGraph's ``interrupt`` mechanism
    assumes the graph is checkpointed so it can resume. For the CLI /
    fixture mode we use ``MemorySaver``; the Phase 3B Web UI will swap in a
    SQLite checkpointer.
    """

    nodes = make_nodes(llm)

    g = StateGraph(IntakeState)
    g.add_node("plan_next_question", nodes["plan_next_question"])
    g.add_node("ask_user", nodes["ask_user"])
    g.add_node("evaluate_interview", nodes["evaluate_interview"])
    g.add_node("draft_report", nodes["draft_report"])
    g.add_node("classify_governance", nodes["classify_governance"])
    g.add_node("await_review", nodes["await_review"])
    g.add_node("revise", nodes["revise"])
    g.add_node("finalize", nodes["finalize"])

    g.add_edge(START, "plan_next_question")
    g.add_edge("plan_next_question", "ask_user")
    g.add_edge("ask_user", "evaluate_interview")
    g.add_conditional_edges(
        "evaluate_interview",
        route_after_evaluate,
        {
            "plan_next_question": "plan_next_question",
            "draft_report": "draft_report",
        },
    )
    g.add_edge("draft_report", "classify_governance")
    g.add_edge("classify_governance", "await_review")
    g.add_conditional_edges(
        "await_review",
        route_after_review,
        {"revise": "revise", "finalize": "finalize"},
    )
    g.add_edge("revise", "await_review")
    g.add_edge("finalize", END)

    return g.compile(checkpointer=MemorySaver())
