"""Re-export of the Data Agent from the standalone package.

The canonical Data Agent implementation lives in the standalone
``model_project_constructor_data_agent`` package under ``packages/data-agent/``.
This shim exists so pipeline code can still write
``from model_project_constructor.agents.data import DataAgent`` and the
decoupling guarantee is preserved: the real source is physically separated
and has zero dependency on the orchestrator package.
"""

from model_project_constructor_data_agent import (
    DataAgent,
    DBConnectionError,
    LLMClient,
    PrimaryQuerySpec,
    QualityCheckSpec,
    ReadOnlyDB,
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
