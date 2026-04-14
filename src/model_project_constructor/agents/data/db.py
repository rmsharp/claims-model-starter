"""Shim: re-export ReadOnlyDB / DBConnectionError from the standalone package.

Exists so ``from model_project_constructor.agents.data.db import ReadOnlyDB``
still works after the Phase 2B restructure. Canonical source:
``packages/data-agent/src/model_project_constructor_data_agent/db.py``.
"""

from model_project_constructor_data_agent.db import DBConnectionError, ReadOnlyDB

__all__ = ["DBConnectionError", "ReadOnlyDB"]
