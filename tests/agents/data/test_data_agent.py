"""End-to-end tests for the Data Agent flow.

The FakeLLMClient is deterministic: ``primary_queries_sequence`` is a
list of responses returned in order on consecutive calls. Providing more
than one entry exercises the RETRY_ONCE branch (first call invalid,
second valid); providing two invalid entries exercises the
EXECUTION_FAILED branch.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from model_project_constructor.agents.data import DataAgent, LLMClient
from model_project_constructor.agents.data.db import ReadOnlyDB
from model_project_constructor.agents.data.llm import (
    PrimaryQuerySpec,
    QualityCheckSpec,
    SummaryResult,
)
from model_project_constructor.schemas.v1.data import (
    DataRequest,
    Datasheet,
    QualityCheck,
)


@dataclass
class FakeLLMClient:
    """Deterministic stand-in for a real LLM integration."""

    primary_queries_sequence: list[list[PrimaryQuerySpec]]
    qc_response: list[list[QualityCheckSpec]]
    summary_response: SummaryResult
    datasheet_response: Datasheet
    generate_primary_calls: int = field(default=0, init=False)
    summarize_calls: int = field(default=0, init=False)
    last_summarize_db_executed: bool | None = field(default=None, init=False)

    def generate_primary_queries(
        self, request: DataRequest, previous_error: str | None = None
    ) -> list[PrimaryQuerySpec]:
        idx = min(
            self.generate_primary_calls,
            len(self.primary_queries_sequence) - 1,
        )
        self.generate_primary_calls += 1
        return self.primary_queries_sequence[idx]

    def generate_quality_checks(
        self,
        request: DataRequest,
        primary_queries: list[PrimaryQuerySpec],
    ) -> list[list[QualityCheckSpec]]:
        if not self.qc_response:
            return [[] for _ in primary_queries]
        if len(self.qc_response) == len(primary_queries):
            return self.qc_response
        return [self.qc_response[0] for _ in primary_queries]

    def summarize(
        self,
        request: DataRequest,
        primary_queries: list[PrimaryQuerySpec],
        quality_checks: list[list[QualityCheck]],
        db_executed: bool,
    ) -> SummaryResult:
        self.summarize_calls += 1
        self.last_summarize_db_executed = db_executed
        return self.summary_response

    def generate_datasheet(
        self, request: DataRequest, primary_query: PrimaryQuerySpec
    ) -> Datasheet:
        return self.datasheet_response


def test_fake_llm_client_implements_protocol(
    primary_query_spec_valid: PrimaryQuerySpec,
    qc_specs_valid: list[QualityCheckSpec],
    summary_response: SummaryResult,
    datasheet_response: Datasheet,
) -> None:
    fake = FakeLLMClient(
        primary_queries_sequence=[[primary_query_spec_valid]],
        qc_response=[qc_specs_valid],
        summary_response=summary_response,
        datasheet_response=datasheet_response,
    )
    assert isinstance(fake, LLMClient)


def test_happy_path_against_seeded_sqlite(
    seeded_db: ReadOnlyDB,
    sample_request: DataRequest,
    primary_query_spec_valid: PrimaryQuerySpec,
    qc_specs_valid: list[QualityCheckSpec],
    summary_response: SummaryResult,
    datasheet_response: Datasheet,
) -> None:
    fake = FakeLLMClient(
        primary_queries_sequence=[[primary_query_spec_valid]],
        qc_response=[qc_specs_valid],
        summary_response=summary_response,
        datasheet_response=datasheet_response,
    )
    agent = DataAgent(llm=fake, db=seeded_db)

    report = agent.run(sample_request)

    assert report.status == "COMPLETE"
    assert report.request == sample_request
    assert len(report.primary_queries) == 1

    pq = report.primary_queries[0]
    assert pq.name == "tx_claims_2024"
    assert len(pq.quality_checks) == 2
    # row_count_nonempty should have returned one row with the count ⇒ PASSED
    row_count_check = next(
        c for c in pq.quality_checks if c.check_name == "row_count_nonempty"
    )
    assert row_count_check.execution_status == "PASSED"
    assert row_count_check.raw_result is not None
    assert row_count_check.raw_result["row_count"] == 1
    # no_negative_paid_amount returns zero rows ⇒ FAILED in our Phase 2A proxy
    neg_check = next(
        c for c in pq.quality_checks if c.check_name == "no_negative_paid_amount"
    )
    assert neg_check.execution_status == "FAILED"
    assert neg_check.raw_result is not None
    assert neg_check.raw_result["row_count"] == 0

    assert pq.datasheet == datasheet_response
    assert fake.summarize_calls == 1
    assert fake.last_summarize_db_executed is True
    assert "database unreachable" not in " ".join(report.data_quality_concerns)


def test_retry_once_then_success(
    seeded_db: ReadOnlyDB,
    sample_request: DataRequest,
    primary_query_spec_valid: PrimaryQuerySpec,
    qc_specs_valid: list[QualityCheckSpec],
    summary_response: SummaryResult,
    datasheet_response: Datasheet,
) -> None:
    bad = PrimaryQuerySpec(
        name="bad_first_attempt",
        sql="   ",
        purpose="intentionally invalid to exercise RETRY_ONCE",
        expected_row_count_order="thousands",
    )
    fake = FakeLLMClient(
        primary_queries_sequence=[[bad], [primary_query_spec_valid]],
        qc_response=[qc_specs_valid],
        summary_response=summary_response,
        datasheet_response=datasheet_response,
    )
    agent = DataAgent(llm=fake, db=seeded_db)

    report = agent.run(sample_request)

    assert report.status == "COMPLETE"
    assert fake.generate_primary_calls == 2
    assert report.primary_queries[0].name == "tx_claims_2024"


def test_fail_after_retry_exhausted(
    seeded_db: ReadOnlyDB,
    sample_request: DataRequest,
    summary_response: SummaryResult,
    datasheet_response: Datasheet,
) -> None:
    bad_a = PrimaryQuerySpec(
        name="still_bad_a",
        sql="",
        purpose="empty",
        expected_row_count_order="tens",
    )
    bad_b = PrimaryQuerySpec(
        name="still_bad_b",
        sql="   \n\t",
        purpose="whitespace-only",
        expected_row_count_order="tens",
    )
    fake = FakeLLMClient(
        primary_queries_sequence=[[bad_a], [bad_b]],
        qc_response=[],
        summary_response=summary_response,
        datasheet_response=datasheet_response,
    )
    agent = DataAgent(llm=fake, db=seeded_db)

    report = agent.run(sample_request)

    assert report.status == "EXECUTION_FAILED"
    assert report.primary_queries == []
    assert "invalid SQL" in report.summary
    assert fake.generate_primary_calls == 2  # original + one retry


def test_db_unreachable_sets_qc_not_executed(
    sample_request: DataRequest,
    primary_query_spec_valid: PrimaryQuerySpec,
    qc_specs_valid: list[QualityCheckSpec],
    summary_response: SummaryResult,
    datasheet_response: Datasheet,
) -> None:
    unreachable = ReadOnlyDB("sqlite:////nonexistent/path/does/not/exist.db")

    fake = FakeLLMClient(
        primary_queries_sequence=[[primary_query_spec_valid]],
        qc_response=[qc_specs_valid],
        summary_response=summary_response,
        datasheet_response=datasheet_response,
    )
    agent = DataAgent(llm=fake, db=unreachable)

    report = agent.run(sample_request)

    assert report.status == "COMPLETE"
    assert fake.last_summarize_db_executed is False
    assert any(
        "database unreachable" in c for c in report.data_quality_concerns
    )
    # Every QC should still be in NOT_EXECUTED state
    for qc in report.primary_queries[0].quality_checks:
        assert qc.execution_status == "NOT_EXECUTED"


def test_db_unreachable_when_db_is_none(
    sample_request: DataRequest,
    primary_query_spec_valid: PrimaryQuerySpec,
    qc_specs_valid: list[QualityCheckSpec],
    summary_response: SummaryResult,
    datasheet_response: Datasheet,
) -> None:
    fake = FakeLLMClient(
        primary_queries_sequence=[[primary_query_spec_valid]],
        qc_response=[qc_specs_valid],
        summary_response=summary_response,
        datasheet_response=datasheet_response,
    )
    agent = DataAgent(llm=fake, db=None)

    report = agent.run(sample_request)

    assert report.status == "COMPLETE"
    for qc in report.primary_queries[0].quality_checks:
        assert qc.execution_status == "NOT_EXECUTED"


def test_per_qc_error_is_isolated(
    seeded_db: ReadOnlyDB,
    sample_request: DataRequest,
    primary_query_spec_valid: PrimaryQuerySpec,
    summary_response: SummaryResult,
    datasheet_response: Datasheet,
) -> None:
    ok_check = QualityCheckSpec(
        check_name="ok_check",
        check_sql="SELECT COUNT(*) FROM claims",
        expectation="claims table has rows",
    )
    broken_check = QualityCheckSpec(
        check_name="broken_check",
        check_sql="SELECT * FROM no_such_table_at_all",
        expectation="will raise because table does not exist",
    )
    fake = FakeLLMClient(
        primary_queries_sequence=[[primary_query_spec_valid]],
        qc_response=[[ok_check, broken_check]],
        summary_response=summary_response,
        datasheet_response=datasheet_response,
    )
    agent = DataAgent(llm=fake, db=seeded_db)

    report = agent.run(sample_request)

    assert report.status == "COMPLETE"
    qcs = report.primary_queries[0].quality_checks
    ok = next(c for c in qcs if c.check_name == "ok_check")
    broken = next(c for c in qcs if c.check_name == "broken_check")
    assert ok.execution_status == "PASSED"
    assert broken.execution_status == "ERROR"
    assert "no_such_table_at_all" in broken.result_summary


@pytest.mark.parametrize(
    ("field_name", "replacement"),
    [
        ("target_description", ""),
        ("required_features", []),
        ("population_filter", "   "),
        ("time_range", ""),
    ],
)
def test_incomplete_request_short_circuits(
    field_name: str,
    replacement: object,
    sample_request: DataRequest,
    seeded_db: ReadOnlyDB,
    primary_query_spec_valid: PrimaryQuerySpec,
    qc_specs_valid: list[QualityCheckSpec],
    summary_response: SummaryResult,
    datasheet_response: Datasheet,
) -> None:
    bad_request = sample_request.model_copy(update={field_name: replacement})
    fake = FakeLLMClient(
        primary_queries_sequence=[[primary_query_spec_valid]],
        qc_response=[qc_specs_valid],
        summary_response=summary_response,
        datasheet_response=datasheet_response,
    )
    agent = DataAgent(llm=fake, db=seeded_db)

    report = agent.run(bad_request)

    assert report.status == "INCOMPLETE_REQUEST"
    assert report.primary_queries == []
    assert any(
        field_name in concern for concern in report.data_quality_concerns
    )
    # Short-circuit: LLM must never be invoked.
    assert fake.generate_primary_calls == 0


def test_unexpected_exception_surfaces_as_execution_failed(
    seeded_db: ReadOnlyDB,
    sample_request: DataRequest,
    primary_query_spec_valid: PrimaryQuerySpec,
    qc_specs_valid: list[QualityCheckSpec],
    summary_response: SummaryResult,
    datasheet_response: Datasheet,
) -> None:
    class ExplodingLLM(FakeLLMClient):
        def generate_primary_queries(
            self, request: DataRequest, previous_error: str | None = None
        ) -> list[PrimaryQuerySpec]:
            raise RuntimeError("simulated internal crash")

    fake = ExplodingLLM(
        primary_queries_sequence=[[primary_query_spec_valid]],
        qc_response=[qc_specs_valid],
        summary_response=summary_response,
        datasheet_response=datasheet_response,
    )
    agent = DataAgent(llm=fake, db=seeded_db)

    report = agent.run(sample_request)

    assert report.status == "EXECUTION_FAILED"
    assert "simulated internal crash" in report.summary
