"""Automated data-source discovery via ``information_schema`` reflection.

Reference producer for the data-source-inventory contract (plan §5.2). Given
a :class:`ReadOnlyDB`, walks the database's ``information_schema`` (via
SQLAlchemy's dialect-agnostic Inspector) and builds a
:class:`DataSourceInventory` with one :class:`DataSourceEntry` per
discovered table or view. The resulting JSON is a valid input for any
downstream consumer that accepts the contract.

Phase 2 scope per ``docs/planning/data-source-inventory-contract-plan.md``:

- PostgreSQL + SQLite tested against fake DBs.
- Other dialects: SQLAlchemy inspector handles most; dialects that raise
  during reflection surface as an empty inventory with ``ProducerMetadata.notes``
  naming the error.
- Optional LLM ranking via the caller-supplied ``llm`` (opt-in through the
  ``--rank-with-llm`` CLI flag). When the ``llm`` object exposes a
  ``rank_candidate_tables`` method, discovery invokes it and assigns
  ``relevance_score`` / ``relevance_reason`` per entry; otherwise those
  fields stay ``None``.

The producer emits ``producer_type="automated"`` with a stable
``producer_id="information_schema_probe_v1"``.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy.exc import SQLAlchemyError

from model_project_constructor_data_agent.db import ReadOnlyDB
from model_project_constructor_data_agent.schemas import (
    ColumnMetadata,
    DataSourceEntry,
    DataSourceInventory,
    ProducerMetadata,
)

PRODUCER_ID = "information_schema_probe_v1"
PRODUCER_VERSION = "1.0"


def probe_information_schema(
    db: ReadOnlyDB,
    *,
    include_schemas: list[str] | None = None,
    llm: Any | None = None,
    request_context: str | None = None,
) -> DataSourceInventory:
    """Produce a :class:`DataSourceInventory` from a live database.

    Arguments:
        db: A connected :class:`ReadOnlyDB`. The caller owns the connection
            lifecycle — this function does not call ``connect`` or ``close``.
        include_schemas: Optional allow-list of schema names. When ``None``
            (default), every accessible schema except the system schemas
            (``information_schema``, ``pg_catalog``) is discovered.
        llm: Optional LLM client. If provided AND the object exposes a
            ``rank_candidate_tables`` method, the method is invoked with the
            candidate entries and ``request_context``; the returned rankings
            populate ``DataSourceEntry.relevance_score`` and
            ``relevance_reason``. Clients that do not support ranking are
            ignored here (no error).
        request_context: Free-text description of what the request is about,
            fed to the LLM for relevance ranking. Unused when ``llm`` is
            ``None`` or does not support ranking.

    Returns a valid :class:`DataSourceInventory` — never raises for probe
    failures. When the database rejects reflection (permission-denied,
    unsupported dialect, transient connection issue), the returned inventory
    has ``entries=[]`` and a single :class:`ProducerMetadata` whose
    ``notes`` names the error for downstream debugging.
    """
    produced_at = datetime.now(UTC)

    try:
        tables = db.get_information_schema(schemas=include_schemas)
    except (SQLAlchemyError, NotImplementedError, RuntimeError) as e:
        return DataSourceInventory(
            entries=[],
            producers=[
                ProducerMetadata(
                    producer_id=PRODUCER_ID,
                    producer_type="automated",
                    produced_at=produced_at,
                    producer_version=PRODUCER_VERSION,
                    notes=f"information_schema probe failed: {e}",
                )
            ],
            created_at=produced_at,
            request_context=request_context,
        )

    entries = [_entry_from_reflection(t) for t in tables]

    if llm is not None and entries and hasattr(llm, "rank_candidate_tables"):
        rankings = llm.rank_candidate_tables(
            entries=entries, request_context=request_context
        )
        ranking_map = {
            r.fully_qualified_name: (r.relevance_score, r.relevance_reason)
            for r in rankings
        }
        entries = [
            entry.model_copy(
                update={
                    "relevance_score": ranking_map.get(
                        entry.fully_qualified_name, (None, None)
                    )[0],
                    "relevance_reason": ranking_map.get(
                        entry.fully_qualified_name, (None, None)
                    )[1],
                }
            )
            for entry in entries
        ]

    producer = ProducerMetadata(
        producer_id=PRODUCER_ID,
        producer_type="automated",
        produced_at=produced_at,
        producer_version=PRODUCER_VERSION,
    )

    return DataSourceInventory(
        entries=entries,
        producers=[producer],
        created_at=produced_at,
        request_context=request_context,
    )


def _entry_from_reflection(table: dict[str, Any]) -> DataSourceEntry:
    namespace = table.get("namespace")
    name = table["name"]
    fqn = f"{namespace}.{name}" if namespace else name

    columns = [
        ColumnMetadata(
            name=c["name"],
            data_type=c["data_type"],
            nullable=c.get("nullable"),
            is_primary_key=bool(c.get("is_primary_key", False)),
            is_foreign_key=bool(c.get("is_foreign_key", False)),
            foreign_key_target=c.get("foreign_key_target"),
        )
        for c in table.get("columns", [])
    ]

    return DataSourceEntry(
        name=name,
        namespace=namespace,
        fully_qualified_name=fqn,
        entity_kind=table["entity_kind"],
        columns=columns,
        primary_key_columns=list(table.get("primary_key_columns", [])),
        producer_id=PRODUCER_ID,
    )
