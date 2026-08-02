"""Deterministic tests for the SQL-capability sweep's *statistics*.

Mirrors ``test_interview_sweep``: a fake runner stands in for the live client, so
the sampling, pooling and failure-classification logic is exercised with zero API
calls. The load-bearing assertions are that each case is sampled ``n_samples``
times (the Session 218 fix) and that a parse failure costs one sample rather than
abandoning the whole case — the behaviour change hidden inside that re-indent.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest
from model_project_constructor_data_agent.anthropic_client import LLMParseError
from model_project_constructor_data_agent.db import ReadOnlyDB
from model_project_constructor_data_agent.llm import PrimaryQuerySpec
from model_project_constructor_data_agent.schemas import DataRequest, DataSourceInventory

from tests.eval.eval_corpus import SqlCase, load_sql_cases
from tests.eval.sql_sweep import sql_sweep_summary, sweep_sql_capabilities


def _spec(sql: str, name: str = "q") -> PrimaryQuerySpec:
    return PrimaryQuerySpec(
        name=name,
        sql=sql,
        purpose="test",
        expected_row_count_order="hundreds",
        inventory_entries_used=[],
    )


@dataclass
class _FakeRunner:
    """A client-shaped double recording every call it receives."""

    specs_per_call: list[list[PrimaryQuerySpec]] | None = None
    primary_error: Exception | None = None
    qc_error: Exception | None = None
    qc_outer_len: int | None = None

    def __post_init__(self) -> None:
        self.primary_calls: list[str] = []
        self.qc_calls: list[str] = []
        self._n = 0

    def generate_primary_queries(
        self,
        request: DataRequest,
        previous_error: str | None = None,
        *,
        data_source_inventory: DataSourceInventory | None = None,
    ) -> list[PrimaryQuerySpec]:
        self.primary_calls.append(request.source_ref or "?")
        if self.primary_error is not None:
            raise self.primary_error
        if self.specs_per_call is not None:
            out = self.specs_per_call[self._n % len(self.specs_per_call)]
            self._n += 1
            return out
        return [_spec("SELECT claim_id FROM claims")]

    def generate_quality_checks(
        self, request: DataRequest, primary_queries: list[PrimaryQuerySpec]
    ) -> list[list[Any]]:
        self.qc_calls.append(request.source_ref or "?")
        if self.qc_error is not None:
            raise self.qc_error
        n = self.qc_outer_len if self.qc_outer_len is not None else len(primary_queries)
        return [[] for _ in range(n)]


def _primary_cases() -> list[SqlCase]:
    return [c for c in load_sql_cases() if c.kind == "primary"]


def test_each_primary_case_is_sampled_n_times(seeded_pc_db: ReadOnlyDB) -> None:
    """The Session 218 fix itself: 3 cases x N samples, not 3 single shots."""
    cases = _primary_cases()
    runner = _FakeRunner()

    result = sweep_sql_capabilities(cases, runner, seeded_pc_db, n_samples=5)

    assert len(cases) == 3, "corpus shape changed — the call-count maths below assumes 3"
    assert len(runner.primary_calls) == 15
    assert len(runner.qc_calls) == 15
    # One spec per call here, so the pooled exec denominator is one per sample.
    assert len(result.exec_results) == 15
    assert len(result.qc_results) == 15


def test_baseline_kind_cases_are_never_sent_to_the_model(seeded_pc_db: ReadOnlyDB) -> None:
    """``kind: baseline`` maps to a method no §3.4 threshold scores.

    Sampling it would spend calls the gate cannot read. The corpus really does
    contain one, so this is a live guard rather than a hypothetical.
    """
    all_cases = load_sql_cases()
    assert any(c.kind == "baseline" for c in all_cases), "corpus lost its baseline case"
    runner = _FakeRunner()

    sweep_sql_capabilities(all_cases, runner, seeded_pc_db, n_samples=2)

    assert len(runner.primary_calls) == 3 * 2  # the baseline case contributed nothing


def test_parse_failure_costs_one_sample_not_the_whole_case(seeded_pc_db: ReadOnlyDB) -> None:
    """The behaviour change hidden in the re-indent, pinned explicitly.

    Before Session 218 an ``LLMParseError`` hit ``continue`` on the *case* loop,
    so one bad response discarded that case entirely. Now it discards one sample:
    the remaining samples still run and still count.
    """
    case = _primary_cases()[:1]

    class _FailsFirstOnly(_FakeRunner):
        def generate_primary_queries(self, *a: Any, **k: Any) -> list[PrimaryQuerySpec]:
            self.primary_calls.append("x")
            if len(self.primary_calls) == 1:
                raise LLMParseError("bad JSON")
            return [_spec("SELECT claim_id FROM claims")]

    runner = _FailsFirstOnly()
    result = sweep_sql_capabilities(case, runner, seeded_pc_db, n_samples=4)

    assert len(runner.primary_calls) == 4, "later samples must still run"
    assert result.parse_failures == 1
    # 1 miss from the failed sample + 3 successes from the rest.
    assert result.exec_results == [False, True, True, True]
    assert result.qc_results == [False, True, True, True]
    # A failed sample must not consume a QC call.
    assert len(runner.qc_calls) == 3


def test_qc_parse_failure_scores_only_the_qc_metric(seeded_pc_db: ReadOnlyDB) -> None:
    runner = _FakeRunner(qc_error=LLMParseError("bad JSON"))

    result = sweep_sql_capabilities(_primary_cases()[:1], runner, seeded_pc_db, n_samples=3)

    assert result.qc_results == [False, False, False]
    assert result.exec_results == [True, True, True], "SQL already succeeded; QC is separate"
    assert result.parse_failures == 0


def test_non_parse_errors_propagate(seeded_pc_db: ReadOnlyDB) -> None:
    """A transport/harness bug must surface, not be laundered into the rate."""
    runner = _FakeRunner(primary_error=RuntimeError("connection reset"))

    with pytest.raises(RuntimeError, match="connection reset"):
        sweep_sql_capabilities(_primary_cases()[:1], runner, seeded_pc_db, n_samples=2)


def test_execution_errors_are_captured_with_their_text(seeded_pc_db: ReadOnlyDB) -> None:
    """S216 gotcha 3: without the message the metric is one uninterpretable bit.

    Uses the real dialect-mismatch shape that caused the whole investigation —
    ``DATEDIFF`` is not a SQLite function.
    """
    runner = _FakeRunner(specs_per_call=[[_spec("SELECT DATEDIFF(day, a, b) FROM claims")]])

    result = sweep_sql_capabilities(_primary_cases()[:1], runner, seeded_pc_db, n_samples=1)

    assert result.exec_results == [False]
    assert len(result.exec_errors) == 1
    case_name, text = result.exec_errors[0]
    assert case_name == _primary_cases()[0].name
    assert "DATEDIFF" in text or "no such function" in text.lower()


def test_events_are_emitted_for_diagnosis(seeded_pc_db: ReadOnlyDB) -> None:
    events: list[str] = []
    runner = _FakeRunner(specs_per_call=[[_spec("SELECT DATEDIFF(day, a, b) FROM claims")]])

    sweep_sql_capabilities(
        _primary_cases()[:1], runner, seeded_pc_db, n_samples=1, on_event=events.append
    )

    assert any("not executable" in e for e in events)


def test_qc_structural_is_scored_against_the_sample_that_produced_it(
    seeded_pc_db: ReadOnlyDB,
) -> None:
    """The structural contract is per-sample: outer length == that sample's specs."""
    runner = _FakeRunner(
        specs_per_call=[[_spec("SELECT 1"), _spec("SELECT 2")]],
        qc_outer_len=1,  # one QC list for two queries — a structural miss
    )

    result = sweep_sql_capabilities(_primary_cases()[:1], runner, seeded_pc_db, n_samples=2)

    assert result.qc_results == [False, False]


def test_summary_reports_numerator_and_denominator_never_a_bare_rate() -> None:
    """S216 gotcha 2 encoded as a format contract, not a convention."""
    from tests.eval.sql_sweep import SqlSweepResult

    text = sql_sweep_summary(
        SqlSweepResult(
            parse_results=[True, True],
            exec_results=[True, False, True],
            qc_results=[True],
        )
    )

    assert "sql_exec 2/3" in text
    assert "%" not in text
