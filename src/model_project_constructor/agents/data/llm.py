"""Shim: re-export LLM protocol + specs from the standalone package.

Exists so ``from model_project_constructor.agents.data.llm import ...``
still works after the Phase 2B restructure. Canonical source:
``packages/data-agent/src/model_project_constructor_data_agent/llm.py``.
"""

from model_project_constructor_data_agent.llm import (
    LLMClient,
    PrimaryQuerySpec,
    QualityCheckSpec,
    SummaryResult,
)

__all__ = [
    "LLMClient",
    "PrimaryQuerySpec",
    "QualityCheckSpec",
    "SummaryResult",
]
