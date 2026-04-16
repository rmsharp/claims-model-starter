"""Unit tests for Data Agent schemas (§5.2 and §5.3)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from model_project_constructor.schemas.v1 import (
    DataGranularity,
    DataReport,
    DataRequest,
)
from tests.schemas.fixtures import (
    make_data_report,
    make_data_request,
    make_primary_query,
    make_quality_check,
)


class TestDataGranularity:
    @pytest.mark.parametrize(
        "grain",
        ["event", "daily", "weekly", "monthly", "quarterly", "annual"],
    )
    def test_all_grains_accepted(self, grain: str) -> None:
        assert DataGranularity(unit="claim", time_grain=grain).time_grain == grain

    def test_invalid_grain_rejected(self) -> None:
        with pytest.raises(ValidationError):
            DataGranularity(unit="claim", time_grain="hourly")


class TestDataRequest:
    def test_happy_path(self) -> None:
        dr = make_data_request()
        assert dr.schema_version == "1.0.0"
        assert dr.source == "pipeline"
        assert dr.database_hint is None
        assert dr.data_quality_concerns == []

    def test_standalone_mode(self) -> None:
        dr = make_data_request(source="standalone", source_ref="analyst_jdoe")
        assert dr.source == "standalone"

    def test_invalid_source_rejected(self) -> None:
        with pytest.raises(ValidationError):
            make_data_request(source="batch")

    def test_optional_context_defaults(self) -> None:
        dr = make_data_request()
        assert dr.database_hint is None
        assert dr.data_quality_concerns == []

    def test_database_hint_may_be_set(self) -> None:
        dr = make_data_request(database_hint="claims_warehouse")
        assert dr.database_hint == "claims_warehouse"

    def test_serialization_round_trip(self) -> None:
        original = make_data_request(database_hint="warehouse", data_quality_concerns=["stale"])
        restored = DataRequest.model_validate_json(original.model_dump_json())
        assert restored == original

    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            make_data_request(experimental_flag=True)


class TestQualityCheck:
    @pytest.mark.parametrize(
        "status",
        ["PASSED", "FAILED", "ERROR", "NOT_EXECUTED"],
    )
    def test_all_execution_statuses_accepted(self, status: str) -> None:
        qc = make_quality_check(execution_status=status)
        assert qc.execution_status == status

    def test_raw_result_may_be_none(self) -> None:
        qc = make_quality_check(raw_result=None)
        assert qc.raw_result is None

    def test_invalid_status_rejected(self) -> None:
        with pytest.raises(ValidationError):
            make_quality_check(execution_status="MAYBE")


class TestPrimaryQuery:
    def test_happy_path_with_nested_datasheet_and_qc(self) -> None:
        pq = make_primary_query()
        assert pq.name == "subrogation_training_set"
        assert pq.expected_row_count_order == "thousands"
        assert len(pq.quality_checks) == 1
        assert pq.datasheet.motivation

    def test_invalid_row_count_order_rejected(self) -> None:
        with pytest.raises(ValidationError):
            make_primary_query(expected_row_count_order="billions")


class TestDataReport:
    def test_happy_path(self) -> None:
        report = make_data_report()
        assert report.status == "COMPLETE"
        assert report.request.source == "pipeline"
        assert len(report.primary_queries) == 1

    def test_incomplete_request_status(self) -> None:
        report = make_data_report(
            status="INCOMPLETE_REQUEST",
            primary_queries=[],
            summary="Request missing target granularity",
            confirmed_expectations=[],
        )
        assert report.status == "INCOMPLETE_REQUEST"

    def test_invalid_status_rejected(self) -> None:
        with pytest.raises(ValidationError):
            make_data_report(status="OK")

    def test_serialization_round_trip(self) -> None:
        original = make_data_report()
        blob = original.model_dump_json()
        restored = DataReport.model_validate_json(blob)
        assert restored == original

    def test_request_echoed_in_report(self) -> None:
        req = make_data_request(source_ref="custom_ref")
        report = make_data_report(request=req)
        assert report.request.source_ref == "custom_ref"
