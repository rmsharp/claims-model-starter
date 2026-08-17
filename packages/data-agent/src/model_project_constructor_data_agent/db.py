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


def sql_dialect_from_url(url: str) -> str | None:
    """Return the SQLAlchemy backend name for ``url`` (e.g. ``"sqlite"``).

    The generated SQL has to run on *this* database, so the LLM needs to know
    which dialect it is writing for. ``make_url`` parses the URL string only —
    it neither connects nor requires the driver package to be installed, so the
    dialect is knowable before the first node runs (and even when the DB is
    unreachable). ``get_backend_name()`` strips any ``+driver`` suffix, so
    ``postgresql+psycopg://…`` yields ``"postgresql"``, not ``"postgresql+psycopg"``.

    Returns ``None`` for a URL SQLAlchemy cannot parse, so a malformed
    ``--db-url`` degrades to today's dialect-silent prompt rather than raising
    here — the URL's real failure surfaces at :meth:`ReadOnlyDB.connect`, which
    is the error path callers already handle.

    ⚠ **That last clause overstates what callers currently do, and Session 223
    verified it rather than repeating it.** :meth:`ReadOnlyDB.connect` does build
    a message naming the exact cause (``DBConnectionError: cannot connect to
    '…:$DB_PORT/claims': invalid literal for int() with base 10: '$DB_PORT'``),
    but the only caller on the run path — ``nodes.py``'s ``execute_qc`` — catches
    ``DBConnectionError`` without binding it and returns ``db_executed=False``,
    and ``agent.py`` then substitutes the fixed string "database unreachable at
    QC execution time" and reports ``status="COMPLETE"``. So a bad URL is
    *degraded* but not *reported*: it is indistinguishable from a database that
    is genuinely down. That is a pre-existing property of the DB error path, not
    of this function, and it applies equally to every malformed URL — this fix
    makes the non-numeric-port case consistent with the rest rather than
    uniquely fatal. It is filed in ``BACKLOG.md``; do not read the sentence
    above as a promise that the operator finds out.

    **Both** exception types are required to honour that contract, and neither
    subsumes the other: ``ArgumentError`` derives from ``SQLAlchemyError``, not
    from ``ValueError``. ``make_url`` reports a structurally unparseable URL
    (and a non-string argument) as ``ArgumentError``, but it coerces the port
    segment with a bare ``int()``, so a *non-numeric port* escapes as the raw
    ``ValueError`` that ``int()`` raises. Measured against SQLAlchemy 2.0.49,
    five inputs take that second path: an unexpanded environment variable
    (``@host:$DB_PORT/``), an alphabetic port, an **empty** port (``@host:/``),
    a float port, and an IPv6 host with either of those. The first is the one
    that bites in practice — a ``--db-url`` templated from a shell environment
    where the port variable was never exported. Catching only ``ArgumentError``
    made the paragraph above false for exactly those cases (fixed Session 223;
    filed Session 218).

    The catch is bounded on the other side too: only *parse* failures degrade.
    An unexpected exception propagates, because silently returning ``None`` for
    a genuine defect would drop the dialect from the prompt and reintroduce the
    wrong-database SQL this function exists to prevent.

    Note this deliberately does *not* validate the port's range or meaning: a
    negative or absurdly large port parses fine here, because ``int()`` accepts
    it and dialect derivation is not URL validation. Judging the URL remains
    :meth:`ReadOnlyDB.connect`'s job.
    """
    try:
        return str(sa.make_url(url).get_backend_name())
    except (sa.exc.ArgumentError, ValueError):
        return None


class ReadOnlyDB:
    """Thin SQLAlchemy wrapper used by EXECUTE_QC."""

    def __init__(self, url: str) -> None:
        self.url = url
        self._engine: sa.Engine | None = None

    @property
    def dialect(self) -> str | None:
        """The SQL dialect of this database, or ``None`` if the URL is unparseable.

        Available before :meth:`connect` — see :func:`sql_dialect_from_url`.
        """
        return sql_dialect_from_url(self.url)

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

    def get_information_schema(
        self, schemas: list[str] | None = None
    ) -> list[dict[str, Any]]:
        """Introspect the database and return table/view metadata.

        Delegates to SQLAlchemy's ``Inspector`` so the implementation is
        dialect-agnostic — PostgreSQL, SQLite, MySQL, and most other
        SQLAlchemy-supported dialects are handled transparently. System
        schemas (``information_schema``, ``pg_catalog``) are skipped by
        default; pass ``schemas=[...]`` to limit discovery to specific
        schemas (in which case no filtering is applied beyond the user's
        choice).

        Returns a list of dicts, one per discovered table or view. Each dict
        has keys: ``namespace`` (schema name), ``name`` (table name),
        ``entity_kind`` (``"table"`` or ``"view"``), ``columns`` (a list of
        per-column dicts with ``name``, ``data_type``, ``nullable``,
        ``is_primary_key``, ``is_foreign_key``, ``foreign_key_target``), and
        ``primary_key_columns`` (a list of PK column names).

        Raises :class:`RuntimeError` if called before :meth:`connect`. Any
        :class:`sqlalchemy.exc.SQLAlchemyError` raised by the inspector
        (permission-denied on a system view, dialect that does not support
        reflection, etc.) propagates — callers that need graceful
        degradation (``discovery.probe_information_schema``) catch it
        themselves.
        """
        if self._engine is None:
            raise RuntimeError(
                "ReadOnlyDB.get_information_schema called before connect()"
            )

        inspector = sa.inspect(self._engine)
        all_schemas = inspector.get_schema_names()
        if schemas is not None:
            target_schemas = [s for s in all_schemas if s in schemas]
        else:
            target_schemas = [
                s for s in all_schemas if s not in {"information_schema", "pg_catalog"}
            ]

        result: list[dict[str, Any]] = []
        for schema in target_schemas:
            for table_name in inspector.get_table_names(schema=schema):
                result.append(
                    self._reflect_entity(inspector, schema, table_name, "table")
                )
            for view_name in inspector.get_view_names(schema=schema):
                result.append(
                    self._reflect_entity(inspector, schema, view_name, "view")
                )
        return result

    @staticmethod
    def _reflect_entity(
        inspector: sa.Inspector,
        schema: str,
        name: str,
        entity_kind: str,
    ) -> dict[str, Any]:
        columns_info = inspector.get_columns(name, schema=schema)
        pk_columns: list[str]
        try:
            pk_info = inspector.get_pk_constraint(name, schema=schema)
            pk_columns = list(pk_info.get("constrained_columns") or [])
        except sa.exc.NoSuchTableError:
            pk_columns = []
        try:
            fk_info = inspector.get_foreign_keys(name, schema=schema)
        except sa.exc.NoSuchTableError:
            fk_info = []
        fk_map: dict[str, str] = {}
        for fk in fk_info:
            ref_schema = fk.get("referred_schema") or schema
            ref_table = fk["referred_table"]
            for local_col, ref_col in zip(
                fk["constrained_columns"], fk["referred_columns"], strict=False
            ):
                fk_map[local_col] = f"{ref_schema}.{ref_table}.{ref_col}"

        columns: list[dict[str, Any]] = []
        for col in columns_info:
            col_name = col["name"]
            columns.append(
                {
                    "name": col_name,
                    "data_type": str(col["type"]),
                    "nullable": col.get("nullable"),
                    "is_primary_key": col_name in pk_columns,
                    "is_foreign_key": col_name in fk_map,
                    "foreign_key_target": fk_map.get(col_name),
                }
            )

        return {
            "namespace": schema,
            "name": name,
            "entity_kind": entity_kind,
            "columns": columns,
            "primary_key_columns": pk_columns,
        }

    def close(self) -> None:
        """Dispose the SQLAlchemy engine, releasing pooled connections.

        Safe to call without a prior ``connect()`` and safe to call twice.
        """
        if self._engine is not None:
            self._engine.dispose()
            self._engine = None
