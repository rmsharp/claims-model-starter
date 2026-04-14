"""Data Agent — generates SQL, runs QC, produces DataReport.

This package MUST NOT import from ``model_project_constructor.schemas.v1.intake``
or reference ``IntakeReport``. The Data Agent is reusable standalone
(constraint C4, see ``docs/planning/architecture-plan.md`` §7). Coupling is
enforced at CI time by ``tests/test_data_agent_decoupling.py``, which
AST-walks every module in this package and fails the build on any import
that mentions the intake schema.
"""

from model_project_constructor.agents.data.agent import DataAgent
from model_project_constructor.agents.data.db import DBConnectionError, ReadOnlyDB
from model_project_constructor.agents.data.llm import (
    LLMClient,
    PrimaryQuerySpec,
    QualityCheckSpec,
    SummaryResult,
)

__all__ = [
    "DataAgent",
    "DBConnectionError",
    "LLMClient",
    "PrimaryQuerySpec",
    "QualityCheckSpec",
    "ReadOnlyDB",
    "SummaryResult",
]
