"""LangGraph assembly for the Data Agent (§10.2)."""

from __future__ import annotations

from typing import Any

from langgraph.graph import END, START, StateGraph

from model_project_constructor.agents.data.db import ReadOnlyDB
from model_project_constructor.agents.data.llm import LLMClient
from model_project_constructor.agents.data.nodes import (
    fail_execution_invalid_sql,
    make_datasheet,
    make_execute_qc,
    make_generate_qc,
    make_generate_queries,
    make_summarize,
    retry_once,
    route_after_generate_queries,
)
from model_project_constructor.agents.data.state import DataAgentState


def build_graph(llm: LLMClient, db: ReadOnlyDB | None) -> Any:
    """Build and compile the Data Agent StateGraph."""
    g: StateGraph = StateGraph(DataAgentState)
    g.add_node("generate_queries", make_generate_queries(llm))
    g.add_node("retry_once", retry_once)
    g.add_node("fail_execution", fail_execution_invalid_sql)
    g.add_node("generate_qc", make_generate_qc(llm))
    g.add_node("execute_qc", make_execute_qc(db))
    g.add_node("summarize", make_summarize(llm))
    g.add_node("datasheet", make_datasheet(llm))

    g.add_edge(START, "generate_queries")
    g.add_conditional_edges(
        "generate_queries",
        route_after_generate_queries,
        {
            "retry_once": "retry_once",
            "generate_qc": "generate_qc",
            "fail_execution": "fail_execution",
        },
    )
    g.add_edge("retry_once", "generate_queries")
    g.add_edge("fail_execution", END)
    g.add_edge("generate_qc", "execute_qc")
    g.add_edge("execute_qc", "summarize")
    g.add_edge("summarize", "datasheet")
    g.add_edge("datasheet", END)

    return g.compile()
