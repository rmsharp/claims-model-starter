"""Standalone Data Agent package — canonical location for DataAgent code.

This package MUST NOT import from anything under
``model_project_constructor.schemas.v1.intake`` or reference
``IntakeReport``. The Data Agent is reusable standalone (constraint C4, see
``docs/planning/architecture-plan.md`` §7). Coupling is enforced at CI time
by ``tests/test_data_agent_decoupling.py``, which AST-walks every module in
this package and fails the build on any import that mentions the intake
schema.

The main ``model_project_constructor`` package re-exports ``DataAgent`` and
the data schemas from this package so existing pipeline code can still write
``from model_project_constructor.agents.data import DataAgent``.
"""

from model_project_constructor_data_agent.agent import DataAgent
from model_project_constructor_data_agent.db import DBConnectionError, ReadOnlyDB
from model_project_constructor_data_agent.llm import (
    LLMClient,
    PrimaryQuerySpec,
    QualityCheckSpec,
    SummaryResult,
)
from model_project_constructor_data_agent.schemas import (
    ColumnMetadata,
    DataGranularity,
    DataReport,
    DataRequest,
    Datasheet,
    DataSourceEntry,
    DataSourceInventory,
    PrimaryQuery,
    ProducerMetadata,
    QualityCheck,
)

__all__ = [
    "ColumnMetadata",
    "DataAgent",
    "DataGranularity",
    "DataReport",
    "DataRequest",
    "DataSourceEntry",
    "DataSourceInventory",
    "Datasheet",
    "DBConnectionError",
    "LLMClient",
    "PrimaryQuery",
    "PrimaryQuerySpec",
    "ProducerMetadata",
    "QualityCheck",
    "QualityCheckSpec",
    "ReadOnlyDB",
    "SummaryResult",
]
