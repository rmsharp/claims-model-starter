"""Unit tests for the information_schema reference producer (Phase 2).

Covers ``probe_information_schema`` in
``packages/data-agent/src/model_project_constructor_data_agent/discovery.py``
per plan §9 Phase 2. Fake-DB coverage only — live-DB testing deferred.

Tests seed a transient SQLite database with known tables / views / FKs and
assert the probe's output against the data-source-inventory contract from
Phase 1.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import sqlalchemy as sa
from model_project_constructor_data_agent import (
    DataSourceInventory,
    ReadOnlyDB,
    TableRanking,
    probe_information_schema,
)
from model_project_constructor_data_agent.discovery import (
    PRODUCER_ID,
    PRODUCER_VERSION,
)
from model_project_constructor_data_agent.schemas import DataSourceEntry


@pytest.fixture
def seeded_sqlite(tmp_path: Path) -> str:
    """SQLite DB with 3 tables + 1 view + 1 FK for discovery tests."""
    db_path = tmp_path / "discover.db"
    engine = sa.create_engine(f"sqlite:///{db_path}")
    try:
        with engine.begin() as conn:
            conn.execute(
                sa.text(
                    "CREATE TABLE claims "
                    "(claim_id INTEGER PRIMARY KEY, loss_amount REAL NOT NULL)"
                )
            )
            conn.execute(
                sa.text(
                    "CREATE TABLE policies "
                    "(policy_id INTEGER PRIMARY KEY, state TEXT)"
                )
            )
            conn.execute(
                sa.text(
                    "CREATE TABLE outcomes ("
                    "claim_id INTEGER PRIMARY KEY, "
                    "recovered_amount REAL, "
                    "FOREIGN KEY (claim_id) REFERENCES claims(claim_id))"
                )
            )
            conn.execute(
                sa.text(
                    "CREATE VIEW v_claim_summary AS SELECT claim_id FROM claims"
                )
            )
    finally:
        engine.dispose()
    return f"sqlite:///{db_path}"


def _probe(url: str, **kwargs: Any) -> DataSourceInventory:
    """Helper: connect, probe, close."""
    db = ReadOnlyDB(url)
    db.connect()
    try:
        return probe_information_schema(db, **kwargs)
    finally:
        db.close()


class TestProbeHappyPath:
    def test_returns_inventory(self, seeded_sqlite: str) -> None:
        inv = _probe(seeded_sqlite)
        assert isinstance(inv, DataSourceInventory)

    def test_discovers_tables_and_view(self, seeded_sqlite: str) -> None:
        inv = _probe(seeded_sqlite)
        assert len(inv.entries) == 4
        fqns = {e.fully_qualified_name for e in inv.entries}
        assert fqns == {
            "main.claims",
            "main.outcomes",
            "main.policies",
            "main.v_claim_summary",
        }

    def test_producer_metadata(self, seeded_sqlite: str) -> None:
        inv = _probe(seeded_sqlite)
        assert len(inv.producers) == 1
        producer = inv.producers[0]
        assert producer.producer_id == PRODUCER_ID
        assert producer.producer_type == "automated"
        assert producer.producer_version == PRODUCER_VERSION
        assert producer.notes is None

    def test_entity_kind_table_vs_view(self, seeded_sqlite: str) -> None:
        inv = _probe(seeded_sqlite)
        by_fqn = {e.fully_qualified_name: e for e in inv.entries}
        assert by_fqn["main.claims"].entity_kind == "table"
        assert by_fqn["main.v_claim_summary"].entity_kind == "view"

    def test_primary_key_columns_detected(self, seeded_sqlite: str) -> None:
        inv = _probe(seeded_sqlite)
        by_fqn = {e.fully_qualified_name: e for e in inv.entries}
        claims = by_fqn["main.claims"]
        assert claims.primary_key_columns == ["claim_id"]
        pk_flag_cols = {c.name for c in claims.columns if c.is_primary_key}
        assert pk_flag_cols == {"claim_id"}

    def test_foreign_key_target_populated(self, seeded_sqlite: str) -> None:
        inv = _probe(seeded_sqlite)
        by_fqn = {e.fully_qualified_name: e for e in inv.entries}
        outcomes = by_fqn["main.outcomes"]
        fk_cols = [c for c in outcomes.columns if c.is_foreign_key]
        assert len(fk_cols) == 1
        assert fk_cols[0].name == "claim_id"
        assert fk_cols[0].foreign_key_target == "main.claims.claim_id"

    def test_every_entry_resolves_producer(self, seeded_sqlite: str) -> None:
        """Cross-field validator guarantees FK integrity at construction."""
        inv = _probe(seeded_sqlite)
        known = {p.producer_id for p in inv.producers}
        for entry in inv.entries:
            assert entry.producer_id in known

    def test_request_context_preserved(self, seeded_sqlite: str) -> None:
        inv = _probe(seeded_sqlite, request_context="subrogation recovery")
        assert inv.request_context == "subrogation recovery"

    def test_created_at_populated(self, seeded_sqlite: str) -> None:
        inv = _probe(seeded_sqlite)
        assert inv.created_at is not None
        assert inv.producers[0].produced_at == inv.created_at

    def test_columns_captured_with_types(self, seeded_sqlite: str) -> None:
        inv = _probe(seeded_sqlite)
        by_fqn = {e.fully_qualified_name: e for e in inv.entries}
        claims_cols = {c.name: c for c in by_fqn["main.claims"].columns}
        assert claims_cols["claim_id"].data_type == "INTEGER"
        assert claims_cols["loss_amount"].data_type == "REAL"
        assert claims_cols["loss_amount"].nullable is False


class TestProbeIncludeSchemas:
    def test_filter_matching_schema_returns_entries(self, seeded_sqlite: str) -> None:
        inv = _probe(seeded_sqlite, include_schemas=["main"])
        assert len(inv.entries) == 4

    def test_filter_matching_nothing_returns_empty_entries(
        self, seeded_sqlite: str
    ) -> None:
        inv = _probe(seeded_sqlite, include_schemas=["nonexistent"])
        assert inv.entries == []
        assert len(inv.producers) == 1


class TestProbeDegradation:
    def test_empty_database_returns_empty_inventory(self, tmp_path: Path) -> None:
        db_path = tmp_path / "empty.db"
        engine = sa.create_engine(f"sqlite:///{db_path}")
        try:
            with engine.connect():
                pass
        finally:
            engine.dispose()
        inv = _probe(f"sqlite:///{db_path}")
        assert inv.entries == []
        assert len(inv.producers) == 1
        assert inv.producers[0].notes is None

    def test_probe_before_connect_surfaces_as_empty_with_note(
        self, tmp_path: Path
    ) -> None:
        """RuntimeError from a not-connected DB is caught; inventory has notes."""
        db = ReadOnlyDB(f"sqlite:///{tmp_path / 'x.db'}")
        inv = probe_information_schema(db)
        assert inv.entries == []
        assert inv.producers[0].notes is not None
        assert "probe failed" in inv.producers[0].notes

    def test_sqlalchemy_error_caught(self) -> None:
        """A fake ReadOnlyDB that raises SQLAlchemyError becomes empty-with-note."""

        class FailingDB:
            def get_information_schema(
                self, schemas: list[str] | None = None
            ) -> list[dict[str, Any]]:
                raise sa.exc.OperationalError(
                    statement="", params={}, orig=Exception("permission denied")
                )

        inv = probe_information_schema(FailingDB())  # type: ignore[arg-type]
        assert inv.entries == []
        assert len(inv.producers) == 1
        assert inv.producers[0].notes is not None
        assert "probe failed" in inv.producers[0].notes

    def test_not_implemented_error_caught(self) -> None:
        class UnsupportedDB:
            def get_information_schema(
                self, schemas: list[str] | None = None
            ) -> list[dict[str, Any]]:
                raise NotImplementedError("dialect 'fake_dialect' not supported")

        inv = probe_information_schema(UnsupportedDB())  # type: ignore[arg-type]
        assert inv.entries == []
        assert "probe failed" in (inv.producers[0].notes or "")


class TestProbeRoundTrip:
    def test_serializes_and_reloads_as_equal_inventory(
        self, seeded_sqlite: str
    ) -> None:
        original = _probe(seeded_sqlite, request_context="claims-domain")
        blob = original.model_dump_json()
        restored = DataSourceInventory.model_validate_json(blob)
        assert restored == original


class TestProbeWithLLMRanking:
    def test_llm_without_ranking_method_is_ignored(self, seeded_sqlite: str) -> None:
        """LLM object lacking rank_candidate_tables: relevance fields stay None."""

        class NoRankingLLM:
            pass

        inv = _probe(seeded_sqlite, llm=NoRankingLLM(), request_context="claims")
        for entry in inv.entries:
            assert entry.relevance_score is None
            assert entry.relevance_reason is None

    def test_llm_ranking_populates_relevance(self, seeded_sqlite: str) -> None:
        class AllSameRankingLLM:
            def rank_candidate_tables(
                self,
                entries: list[DataSourceEntry],
                request_context: str | None,
            ) -> list[TableRanking]:
                assert request_context == "claims domain"
                return [
                    TableRanking(
                        fully_qualified_name=e.fully_qualified_name,
                        relevance_score=0.5,
                        relevance_reason=f"fake rank for {e.name}",
                    )
                    for e in entries
                ]

        inv = _probe(
            seeded_sqlite, llm=AllSameRankingLLM(), request_context="claims domain"
        )
        for entry in inv.entries:
            assert entry.relevance_score == pytest.approx(0.5)
            assert entry.relevance_reason is not None
            assert "fake rank" in entry.relevance_reason

    def test_partial_ranking_leaves_unranked_entries_none(
        self, seeded_sqlite: str
    ) -> None:
        """Entries the LLM does not return stay at relevance_score=None."""

        class PartialRankingLLM:
            def rank_candidate_tables(
                self,
                entries: list[DataSourceEntry],
                request_context: str | None,
            ) -> list[TableRanking]:
                return [
                    TableRanking(
                        fully_qualified_name=entries[0].fully_qualified_name,
                        relevance_score=0.95,
                        relevance_reason="top pick",
                    )
                ]

        inv = _probe(
            seeded_sqlite, llm=PartialRankingLLM(), request_context="claims"
        )
        scored = [e for e in inv.entries if e.relevance_score is not None]
        unscored = [e for e in inv.entries if e.relevance_score is None]
        assert len(scored) == 1
        assert scored[0].relevance_score == pytest.approx(0.95)
        assert len(unscored) == len(inv.entries) - 1

    def test_llm_ignored_when_entries_empty(self, tmp_path: Path) -> None:
        """LLM ranking is skipped when there are no entries (saves an LLM call)."""
        db_path = tmp_path / "empty.db"
        engine = sa.create_engine(f"sqlite:///{db_path}")
        try:
            with engine.connect():
                pass
        finally:
            engine.dispose()

        class ExplodingLLM:
            def rank_candidate_tables(
                self,
                entries: list[DataSourceEntry],
                request_context: str | None,
            ) -> list[TableRanking]:
                raise AssertionError("LLM should not be invoked on empty inventory")

        inv = _probe(
            f"sqlite:///{db_path}", llm=ExplodingLLM(), request_context="anything"
        )
        assert inv.entries == []
