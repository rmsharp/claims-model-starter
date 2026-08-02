"""Unit tests for the Data Agent's DB helpers — specifically dialect derivation.

``sql_dialect_from_url`` is what stops the generated SQL from being written for
the wrong database. Session 216 measured every SQL-execution failure on *every*
provider as an unsupported-function error (``DATEDIFF``,
``PERCENTILE_CONT … WITHIN GROUP``, ``MEDIAN``) against a SQLite target: the
model was writing warehouse SQL because nothing told it otherwise. These tests
pin the parse-only derivation that feeds the prompt.

No database is created and no driver is installed for the non-SQLite URLs —
that is the point: ``make_url`` parses the string, so the dialect is knowable
before connecting and without the DBAPI package being present.
"""

from __future__ import annotations

import pytest
from model_project_constructor_data_agent.db import ReadOnlyDB, sql_dialect_from_url


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("sqlite:///:memory:", "sqlite"),
        ("sqlite:////tmp/pc_eval.db", "sqlite"),
        ("postgresql://user:pw@host:5432/claims", "postgresql"),
        # ``get_backend_name`` strips the ``+driver`` suffix, so a prompt built
        # from this says "postgresql", not "postgresql+psycopg".
        ("postgresql+psycopg://user:pw@host/claims", "postgresql"),
        ("mysql+pymysql://user:pw@host/claims", "mysql"),
        ("mssql+pyodbc://user:pw@host/claims", "mssql"),
        # Dialects with no driver installed here still parse — derivation is
        # string-only, so an enterprise warehouse URL works without the package.
        ("snowflake://user:pw@account/claims/public", "snowflake"),
        ("duckdb:///warehouse.duckdb", "duckdb"),
    ],
)
def test_dialect_derived_from_url_without_connecting(url: str, expected: str) -> None:
    assert sql_dialect_from_url(url) == expected


@pytest.mark.parametrize(
    "url",
    [
        "",
        "not a url at all",
        "://missing-scheme",
    ],
)
def test_unparseable_url_degrades_to_none(url: str) -> None:
    """A malformed URL must not raise here.

    The dialect is an optional prompt enrichment; the URL's real failure belongs
    to ``connect()``, which callers already handle. Raising during prompt
    construction would turn a bad ``--db-url`` into a crash before the agent
    ever reports why.
    """
    assert sql_dialect_from_url(url) is None


def test_readonly_db_exposes_dialect_before_connect() -> None:
    """The accessor must work pre-``connect()``.

    ``generate_queries`` is the first node in the graph and the DB is not
    connected until ``execute_qc``, so a dialect that required a live connection
    would arrive too late to reach the prompt.
    """
    db = ReadOnlyDB("sqlite:///:memory:")
    assert db._engine is None  # not connected
    assert db.dialect == "sqlite"


def test_readonly_db_dialect_matches_module_function() -> None:
    db = ReadOnlyDB("postgresql://user:pw@host/claims")
    assert db.dialect == sql_dialect_from_url(db.url)
