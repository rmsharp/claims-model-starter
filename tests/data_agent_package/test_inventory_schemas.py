"""Unit tests for the data-source-inventory contract (Phase 1).

Covers the four new Pydantic types (``DataSourceInventory``,
``DataSourceEntry``, ``ProducerMetadata``, ``ColumnMetadata``) defined in
``docs/planning/data-source-inventory-contract-plan.md`` §4.

Phase 1 scope per plan §9: schema only. No producer or consumer behavior here.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from model_project_constructor_data_agent import (
    ColumnMetadata,
    DataSourceEntry,
    DataSourceInventory,
    ProducerMetadata,
)
from pydantic import ValidationError

REPO_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_CURATED_FIXTURE = REPO_ROOT / "tests" / "fixtures" / "sample_curated_inventory.json"

FIXED_TS = datetime(2026, 4, 19, 12, 0, 0, tzinfo=UTC)


def _make_producer(**overrides: Any) -> ProducerMetadata:
    defaults: dict[str, Any] = dict(
        producer_id="information_schema_probe_v1",
        producer_type="automated",
        produced_at=FIXED_TS,
        producer_version="1.0",
        notes=None,
    )
    defaults.update(overrides)
    return ProducerMetadata(**defaults)


def _make_entry(**overrides: Any) -> DataSourceEntry:
    defaults: dict[str, Any] = dict(
        name="claim_events",
        namespace="public",
        source_system="claims_warehouse",
        fully_qualified_name="public.claim_events",
        entity_kind="table",
        producer_id="information_schema_probe_v1",
    )
    defaults.update(overrides)
    return DataSourceEntry(**defaults)


def _make_inventory(**overrides: Any) -> DataSourceInventory:
    defaults: dict[str, Any] = dict(
        entries=[_make_entry()],
        producers=[_make_producer()],
        created_at=FIXED_TS,
        request_context="subrogation recovery model",
    )
    defaults.update(overrides)
    return DataSourceInventory(**defaults)


class TestColumnMetadata:
    def test_minimal(self) -> None:
        col = ColumnMetadata(name="claim_id", data_type="VARCHAR(36)")
        assert col.name == "claim_id"
        assert col.nullable is None
        assert col.is_primary_key is False
        assert col.is_foreign_key is False
        assert col.foreign_key_target is None

    def test_full(self) -> None:
        col = ColumnMetadata(
            name="policy_id",
            data_type="VARCHAR(36)",
            nullable=False,
            description="Foreign key into policy_admin.policies.",
            is_primary_key=False,
            is_foreign_key=True,
            foreign_key_target="policy_admin.policies.policy_id",
        )
        assert col.is_foreign_key is True
        assert col.foreign_key_target == "policy_admin.policies.policy_id"

    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            ColumnMetadata(name="x", data_type="INT", experimental="yes")  # type: ignore[call-arg]


class TestProducerMetadata:
    @pytest.mark.parametrize(
        "producer_type",
        ["curated", "automated", "interview", "external_catalog"],
    )
    def test_all_producer_types_accepted(self, producer_type: str) -> None:
        p = _make_producer(producer_type=producer_type)
        assert p.producer_type == producer_type

    def test_invalid_producer_type_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _make_producer(producer_type="manual")

    def test_optional_fields_default(self) -> None:
        p = _make_producer(producer_version=None, notes=None)
        assert p.producer_version is None
        assert p.notes is None

    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            _make_producer(confidence="high")


class TestDataSourceEntry:
    def test_minimal_happy_path(self) -> None:
        entry = _make_entry()
        assert entry.schema_version == "1.0.0"
        assert entry.entity_kind == "table"
        assert entry.columns == []
        assert entry.primary_key_columns == []
        assert entry.entity_types == []
        assert entry.extra == {}
        assert entry.relevance_score is None
        assert entry.row_count_estimate is None

    @pytest.mark.parametrize(
        "kind",
        ["table", "view", "materialized_view", "file_dataset", "feature_view", "other"],
    )
    def test_all_entity_kinds_accepted(self, kind: str) -> None:
        entry = _make_entry(entity_kind=kind)
        assert entry.entity_kind == kind

    def test_invalid_entity_kind_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _make_entry(entity_kind="stream")

    def test_with_columns_and_primary_key(self) -> None:
        entry = _make_entry(
            columns=[
                ColumnMetadata(name="claim_id", data_type="VARCHAR(36)", is_primary_key=True),
                ColumnMetadata(name="loss_date", data_type="DATE"),
            ],
            primary_key_columns=["claim_id"],
            row_count_estimate=1_200_000,
        )
        assert len(entry.columns) == 2
        assert entry.primary_key_columns == ["claim_id"]
        assert entry.row_count_estimate == 1_200_000

    def test_relevance_score_as_float(self) -> None:
        entry = _make_entry(relevance_score=0.87, relevance_reason="LLM ranked top-3")
        assert entry.relevance_score == pytest.approx(0.87)
        assert entry.relevance_reason == "LLM ranked top-3"

    def test_freshness_and_access_fields(self) -> None:
        entry = _make_entry(
            last_updated_at=FIXED_TS,
            refresh_cadence="daily",
            access_notes="read-only service account required",
            owning_team="claims_analytics",
        )
        assert entry.refresh_cadence == "daily"
        assert entry.owning_team == "claims_analytics"

    def test_extra_field_accepts_producer_specific_keys(self) -> None:
        """``extra: dict[str, Any]`` is a typed producer-extension point.

        Plan §3.2 / §4 rationale: producers embed vendor-specific metadata
        (DataHub lineage ids, Collibra asset urns, confidential-access flags)
        here without the contract needing to know about them. The ``extra``
        field is TYPED but content is unconstrained — ``extra="forbid"`` on
        the parent model only blocks unknown top-level keys, not the contents
        of this dict.
        """
        entry = _make_entry(
            extra={
                "datahub_urn": "urn:li:dataset:(urn:li:dataPlatform:postgres,claim_events,PROD)",
                "confidential": True,
                "custom_tags": ["pii", "high-value"],
            }
        )
        assert entry.extra["datahub_urn"].startswith("urn:li:")
        assert entry.extra["confidential"] is True
        assert entry.extra["custom_tags"] == ["pii", "high-value"]

    def test_top_level_extra_keys_still_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            _make_entry(confidential=True)

    def test_schema_version_is_literal(self) -> None:
        with pytest.raises(ValidationError):
            _make_entry(schema_version="2.0.0")


class TestDataSourceInventory:
    def test_happy_path(self) -> None:
        inv = _make_inventory()
        assert inv.schema_version == "1.0.0"
        assert len(inv.entries) == 1
        assert len(inv.producers) == 1
        assert inv.request_context == "subrogation recovery model"

    def test_empty_entries_valid(self) -> None:
        """Empty inventory is valid — consumer treats it identically to None (§4.3)."""
        inv = _make_inventory(entries=[], producers=[])
        assert inv.entries == []
        assert inv.producers == []

    def test_dangling_producer_id_rejected(self) -> None:
        """Cross-field validator: every entry.producer_id must resolve (§4.3)."""
        with pytest.raises(ValidationError) as exc_info:
            DataSourceInventory(
                entries=[_make_entry(producer_id="ghost_producer_v0")],
                producers=[_make_producer()],
                created_at=FIXED_TS,
            )
        msg = str(exc_info.value)
        assert "ghost_producer_v0" in msg

    def test_multiple_producers_and_entries(self) -> None:
        inv = _make_inventory(
            entries=[
                _make_entry(fully_qualified_name="public.claims", producer_id="prod_a"),
                _make_entry(fully_qualified_name="public.policies", producer_id="prod_b"),
            ],
            producers=[
                _make_producer(producer_id="prod_a", producer_type="curated"),
                _make_producer(producer_id="prod_b", producer_type="interview"),
            ],
        )
        assert len(inv.entries) == 2
        assert {e.producer_id for e in inv.entries} == {"prod_a", "prod_b"}

    def test_schema_version_is_literal(self) -> None:
        with pytest.raises(ValidationError):
            DataSourceInventory(
                schema_version="1.1.0",
                entries=[],
                producers=[],
                created_at=FIXED_TS,
            )

    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            DataSourceInventory(
                entries=[],
                producers=[],
                created_at=FIXED_TS,
                experimental="yes",  # type: ignore[call-arg]
            )

    def test_serialization_round_trip(self) -> None:
        original = _make_inventory(
            entries=[
                _make_entry(
                    columns=[
                        ColumnMetadata(
                            name="claim_id", data_type="VARCHAR(36)", is_primary_key=True
                        ),
                    ],
                    primary_key_columns=["claim_id"],
                    relevance_score=0.9,
                    extra={"urn": "abc"},
                )
            ]
        )
        blob = original.model_dump_json()
        restored = DataSourceInventory.model_validate_json(blob)
        assert restored == original

    def test_both_reexport_paths_import_same_class(self) -> None:
        from model_project_constructor.schemas.v1 import (
            DataSourceInventory as DSI_v1,
        )
        from model_project_constructor.schemas.v1.data import (
            DataSourceInventory as DSI_v1_data,
        )

        assert DSI_v1 is DataSourceInventory
        assert DSI_v1_data is DataSourceInventory


class TestSampleCuratedFixture:
    """Pin tests/fixtures/sample_curated_inventory.json against the schema.

    This fixture is a reference curated-producer payload that future phases
    (Phase 2 fake-producer input; Phase 3 consumer-integration test input)
    will rely on. If the schema drifts and the fixture stops validating,
    update BOTH together — do not delete or silently regenerate the fixture.
    """

    def test_fixture_validates(self) -> None:
        blob = json.loads(SAMPLE_CURATED_FIXTURE.read_text())
        inv = DataSourceInventory.model_validate(blob)
        assert len(inv.entries) >= 1
        assert len(inv.producers) >= 1
        assert all(e.producer_id in {p.producer_id for p in inv.producers} for e in inv.entries)
