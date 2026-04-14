"""Read-only database access for the EXECUTE_QC node.

Read-only enforcement is a database-credential concern in production (§9.1).
This wrapper deliberately does not attempt to parse or reject mutating SQL —
the Data Agent's LLM is prompted to emit SELECTs, and the pipeline is
configured with a SELECT-only role at deployment time. The wrapper's sole
job is to surface a clean :class:`DBConnectionError` on connect failure so
the graph can take the SKIP_EXECUTION off-ramp described in §10.
"""

from __future__ import annotations

from typing import Any

import sqlalchemy as sa


class DBConnectionError(Exception):
    """Raised when the Data Agent cannot reach its database."""


class ReadOnlyDB:
    """Thin SQLAlchemy wrapper used by EXECUTE_QC."""

    def __init__(self, url: str) -> None:
        self.url = url
        self._engine: sa.Engine | None = None

    def connect(self) -> None:
        """Open the engine and round-trip ``SELECT 1`` to prove reachability."""
        try:
            engine = sa.create_engine(self.url)
            with engine.connect() as conn:
                conn.execute(sa.text("SELECT 1"))
        except Exception as e:
            raise DBConnectionError(f"cannot connect to {self.url!r}: {e}") from e
        self._engine = engine

    def execute(self, sql: str) -> list[dict[str, Any]]:
        """Execute a SELECT and return a list of row dicts."""
        if self._engine is None:
            raise RuntimeError("ReadOnlyDB.execute called before connect()")
        with self._engine.connect() as conn:
            result = conn.execute(sa.text(sql))
            return [dict(row) for row in result.mappings().all()]
