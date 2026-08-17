"""Deterministic tests for the SQL-capability sweep's *statistics*.

Mirrors ``test_interview_sweep``: a fake runner stands in for the live client, so
the sampling, pooling and failure-classification logic is exercised with zero API
calls.

The load-bearing assertions are that each case is sampled ``n_samples`` times
(the Session 218 fix), that a parse failure costs one sample rather than
abandoning the whole case (the behaviour change hidden inside that re-indent),
and — since Session 221 — the two-tier retry policy:

* a transient is retried up to the bound and, on recovery, costs nothing;
* an exhausted ``LLMParseError`` is still **scored a miss**, so the pooled
  denominator never shrinks (excluding it would let a provider failing 14 of 15
  samples score 1/1 and pass a 100% bar);
* an exhausted **transport** error is **excluded** and counted, because no model
  output exists to judge;
* a non-transient still propagates on the first attempt, unretried;
* every counter reaches the summary line, and every note carries ``str(exc)``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import anthropic
import httpx
import pytest
from model_project_constructor_data_agent.anthropic_client import LLMParseError
from model_project_constructor_data_agent.db import ReadOnlyDB
from model_project_constructor_data_agent.llm import PrimaryQuerySpec
from model_project_constructor_data_agent.schemas import DataRequest, DataSourceInventory

from tests.eval.eval_corpus import SqlCase, load_sql_cases
from tests.eval.eval_scoring import pass_rate
from tests.eval.eval_thresholds import SQL_PARSE_VALID_MIN
from tests.eval.sql_sweep import sql_sweep_summary, sweep_sql_capabilities


def _spec(sql: str, name: str = "q") -> PrimaryQuerySpec:
    return PrimaryQuerySpec(
        name=name,
        sql=sql,
        purpose="test",
        expected_row_count_order="hundreds",
        inventory_entries_used=[],
    )


# Constructed with a throwaway httpx request so the deterministic suite needs no
# API key — the same pattern ``test_interview_sweep`` uses for its transport
# errors. ``APITimeoutError`` is a subclass of ``APIConnectionError``.
def _req() -> httpx.Request:
    return httpx.Request("POST", "https://api.anthropic.com/v1/messages")


def _timeout() -> anthropic.APITimeoutError:
    return anthropic.APITimeoutError(request=_req())


def _conn_error() -> anthropic.APIConnectionError:
    return anthropic.APIConnectionError(message="dropped", request=_req())


@dataclass
class _FakeRunner:
    """A client-shaped double recording every call it receives.

    ``*_error_times`` bounds how many *calls* raise: ``None`` means every call,
    ``1`` means only the first (so the retry recovers), ``0`` means none.
    ``primary_error_sequence`` is the per-call form, needed to mix transient
    classes within one sample: entry *i* is raised on call *i*, ``None`` succeeds,
    and running off the end succeeds.
    """

    specs_per_call: list[list[PrimaryQuerySpec]] | None = None
    primary_error: Exception | None = None
    primary_error_times: int | None = None
    primary_error_sequence: list[Exception | None] | None = None
    qc_error: Exception | None = None
    qc_error_times: int | None = None
    qc_outer_len: int | None = None
    primary_calls: list[str] = field(default_factory=list)
    qc_calls: list[str] = field(default_factory=list)
    #: The ``previous_error`` argument seen on each primary call. Every entry
    #: must stay ``None`` — a retry that passed it would measure a *repaired*
    #: query rather than a first-shot one.
    previous_errors: list[str | None] = field(default_factory=list)

    def __post_init__(self) -> None:
        self._n = 0

    def generate_primary_queries(
        self,
        request: DataRequest,
        previous_error: str | None = None,
        *,
        data_source_inventory: DataSourceInventory | None = None,
    ) -> list[PrimaryQuerySpec]:
        self.primary_calls.append(request.source_ref or "?")
        self.previous_errors.append(previous_error)
        if self.primary_error_sequence is not None:
            idx = len(self.primary_calls) - 1
            if idx < len(self.primary_error_sequence):
                queued = self.primary_error_sequence[idx]
                if queued is not None:
                    raise queued
        if self.primary_error is not None and (
            self.primary_error_times is None or len(self.primary_calls) <= self.primary_error_times
        ):
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
        if self.qc_error is not None and (
            self.qc_error_times is None or len(self.qc_calls) <= self.qc_error_times
        ):
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
    # Nothing failed, so no attempt was spent on a retry.
    assert result.transient_retries == 0
    assert result.excluded_transient == 0


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


def test_exhausted_parse_failure_costs_one_sample_not_the_whole_case(
    seeded_pc_db: ReadOnlyDB,
) -> None:
    """The behaviour change hidden in the re-indent, pinned explicitly.

    Before Session 218 an ``LLMParseError`` hit ``continue`` on the *case* loop,
    so one bad response discarded that case entirely. Now it discards one sample:
    the remaining samples still run and still count. Session 221 added the retry,
    so the failing sample here burns all three attempts before it is scored.
    """
    case = _primary_cases()[:1]
    # 3 calls = one sample's full attempt budget, so sample 1 exhausts and the
    # rest succeed first try.
    runner = _FakeRunner(primary_error=LLMParseError("bad JSON"), primary_error_times=3)

    result = sweep_sql_capabilities(
        case, runner, seeded_pc_db, n_samples=4, max_transient_retries=2
    )

    assert len(runner.primary_calls) == 6, "3 attempts on the doomed sample + 3 later samples"
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
    assert result.excluded_transient == 0, "an exhausted LLMParseError is scored, never excluded"
    # 3 samples x 2 retries. The QC seam's retries must reach the counter too —
    # without this the whole seam's contribution is unobserved.
    assert result.transient_retries == 6
    assert len(runner.qc_calls) == 9


def test_non_parse_errors_propagate(seeded_pc_db: ReadOnlyDB) -> None:
    """A transport/harness bug must surface, not be laundered into the rate."""
    runner = _FakeRunner(primary_error=RuntimeError("connection reset"))

    with pytest.raises(RuntimeError, match="connection reset"):
        sweep_sql_capabilities(_primary_cases()[:1], runner, seeded_pc_db, n_samples=2)

    assert len(runner.primary_calls) == 1, "a non-transient is not retried — it propagates at once"


def test_api_status_error_propagates(seeded_pc_db: ReadOnlyDB) -> None:
    """FM #18: ``APIStatusError`` is a *sibling* of ``APIConnectionError``.

    4xx/5xx means bad model id, auth or rate limit — a real API error that must
    surface loudly rather than be retried and excluded as a network blip.
    """
    status_error = anthropic.APIStatusError(
        "bad request", response=httpx.Response(400, request=_req()), body=None
    )
    runner = _FakeRunner(primary_error=status_error)

    with pytest.raises(anthropic.APIStatusError):
        sweep_sql_capabilities(_primary_cases()[:1], runner, seeded_pc_db, n_samples=2)

    assert len(runner.primary_calls) == 1


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
    """S216 gotcha 2 encoded as a format contract, not a convention.

    The three-keyword construction is also the tripwire proving every field
    added since carries a default.
    """
    from tests.eval.sql_sweep import SqlSweepResult

    text = sql_sweep_summary(
        SqlSweepResult(
            parse_results=[True, True],
            exec_results=[True, False, True],
            qc_results=[True],
        )
    )

    assert "sql_exec 2/3" in text
    assert "transient_retries 0" in text
    assert "excluded_transient 0" in text
    assert "%" not in text


# --- Session 221: the two-tier retry policy (gap #1c, applied to this block) ---


def test_transient_parse_error_is_retried_and_recovers(seeded_pc_db: ReadOnlyDB) -> None:
    """The Session 219 defect, closed: one blip now costs nothing.

    A single first-attempt ``LLMParseError`` used to score three immediate
    misses against two 100% bars, which is how one ~1-in-60 event produced the
    ``opencode`` NO-GO.
    """
    runner = _FakeRunner(primary_error=LLMParseError("blip"), primary_error_times=1)

    result = sweep_sql_capabilities(
        _primary_cases()[:1], runner, seeded_pc_db, n_samples=3, max_transient_retries=2
    )

    assert result.parse_failures == 0
    assert result.exec_results == [True, True, True]
    assert result.qc_results == [True, True, True]
    assert result.excluded_transient == 0
    assert len(runner.primary_calls) == 4, "one retried sample + two clean ones"
    assert result.transient_retries == 1


def test_exhausted_parse_error_is_still_scored_a_miss(seeded_pc_db: ReadOnlyDB) -> None:
    """The core of the design: retry, but never shrink the denominator.

    Excluding here would let a provider that cannot emit JSON on most samples
    score 1/1 = 100% and PASS a bar it fails on the true rate.
    """
    runner = _FakeRunner(primary_error=LLMParseError("garbage"))

    result = sweep_sql_capabilities(
        _primary_cases()[:1], runner, seeded_pc_db, n_samples=3, max_transient_retries=2
    )

    assert result.parse_failures == 3
    assert result.parse_results == [False, False, False]
    assert result.exec_results == [False, False, False]
    assert result.qc_results == [False, False, False]
    assert result.excluded_transient == 0, "a scored miss is never also an exclusion"
    assert len(runner.primary_calls) == 9, "3 samples x 3 attempts — the denominator holds"
    # The exhaustion path spends retries too — pinned separately from the
    # recovery path, which is the only one the other counter assertions observe.
    assert result.transient_retries == 6
    assert pass_rate("sql_parse", result.parse_results).meets(SQL_PARSE_VALID_MIN) is False


def test_transient_is_retried_at_most_the_bound(seeded_pc_db: ReadOnlyDB) -> None:
    """``attempts == max_transient_retries + 1``, and no attempt beyond it."""
    runner = _FakeRunner(primary_error=LLMParseError("blip"), primary_error_times=2)

    result = sweep_sql_capabilities(
        _primary_cases()[:1], runner, seeded_pc_db, n_samples=1, max_transient_retries=2
    )

    assert len(runner.primary_calls) == 3, "two failures then the third attempt succeeds"
    assert result.transient_retries == 2
    assert result.parse_failures == 0
    assert result.exec_results == [True]


def test_max_transient_retries_zero_reproduces_the_pre_fix_behaviour(
    seeded_pc_db: ReadOnlyDB,
) -> None:
    """The bound is genuinely injectable, and 0 is the Session 218 semantics.

    This is the regression anchor for the old behaviour: with no retries, an
    ``LLMParseError`` scores exactly the three misses it scored before.
    """
    runner = _FakeRunner(primary_error=LLMParseError("bad JSON"))

    result = sweep_sql_capabilities(
        _primary_cases()[:1], runner, seeded_pc_db, n_samples=4, max_transient_retries=0
    )

    assert len(runner.primary_calls) == 4, "one attempt per sample — no retry"
    assert result.parse_failures == 4
    assert result.exec_results == [False, False, False, False]
    assert result.qc_results == [False, False, False, False]
    assert result.transient_retries == 0
    assert len(runner.qc_calls) == 0


def test_transport_error_is_retried_and_recovers(seeded_pc_db: ReadOnlyDB) -> None:
    """Before Session 221 this aborted the whole live run.

    The data-agent package wraps no SDK transport error, so an
    ``APITimeoutError`` propagated straight out of the sweep — the hole Session
    171 closed for ``interview_sweep`` and never applied here.
    """
    runner = _FakeRunner(primary_error=_timeout(), primary_error_times=1)

    result = sweep_sql_capabilities(
        _primary_cases()[:1], runner, seeded_pc_db, n_samples=1, max_transient_retries=2
    )

    assert result.exec_results == [True]
    assert result.excluded_transient == 0
    assert result.transient_retries == 1
    assert len(runner.primary_calls) == 2


def test_exhausted_transport_error_excludes_the_sample(seeded_pc_db: ReadOnlyDB) -> None:
    """A network outage is never recorded as model quality.

    No model output exists to judge, so the sample is dropped and counted —
    the one place this sweep does mirror ``interview_sweep`` exactly.
    """
    runner = _FakeRunner(primary_error=_conn_error())

    result = sweep_sql_capabilities(
        _primary_cases()[:1], runner, seeded_pc_db, n_samples=2, max_transient_retries=1
    )

    assert result.parse_results == []
    assert result.exec_results == []
    assert result.qc_results == []
    assert result.parse_failures == 0, "a transport failure is not a parse failure"
    assert result.excluded_transient == 2
    assert result.transient_retries == 2
    assert len(runner.primary_calls) == 4, "2 samples x (1 try + 1 retry)"


def test_transport_timeout_subclass_is_caught_as_connection_error(
    seeded_pc_db: ReadOnlyDB,
) -> None:
    """``APITimeoutError`` ⊂ ``APIConnectionError`` — both classify as transport."""
    runner = _FakeRunner(primary_error=_timeout())

    result = sweep_sql_capabilities(
        _primary_cases()[:1], runner, seeded_pc_db, n_samples=2, max_transient_retries=0
    )

    assert result.excluded_transient == 2
    assert result.parse_results == []


def test_qc_transport_exclusion_drops_only_the_qc_datum(seeded_pc_db: ReadOnlyDB) -> None:
    """Exclusion granularity is the QC observation, not the whole sample.

    Parse and exec were already recorded for that sample and are correct; only
    the QC datum is missing. Pinned so a later reader does not "fix" this into a
    whole-sample retraction.
    """
    runner = _FakeRunner(qc_error=_conn_error())

    result = sweep_sql_capabilities(
        _primary_cases()[:1], runner, seeded_pc_db, n_samples=2, max_transient_retries=1
    )

    assert result.parse_results == [True, True], "the SQL observations survive"
    assert result.exec_results == [True, True]
    assert result.qc_results == [], "only the QC datum is dropped"
    assert result.excluded_transient == 2
    assert result.transient_retries == 2
    assert len(runner.qc_calls) == 4


def test_retry_does_not_pass_previous_error(seeded_pc_db: ReadOnlyDB) -> None:
    """A retry must re-ask, not ask for a repair.

    ``generate_primary_queries``' ``previous_error`` injects "Return corrected
    SQL this time" into the prompt. Passing it on a retry would turn
    ``sql_parse`` into a *repaired-query* metric behind an unchanged 1.00 bar.
    """
    runner = _FakeRunner(primary_error=LLMParseError("blip"), primary_error_times=1)

    sweep_sql_capabilities(
        _primary_cases()[:1], runner, seeded_pc_db, n_samples=1, max_transient_retries=2
    )

    assert runner.previous_errors == [None, None]


def test_notes_carry_the_exception_text_and_the_retry_grammar(
    seeded_pc_db: ReadOnlyDB,
) -> None:
    """Session 220's attribution gap, closed.

    The pre-fix ``notify`` logged ``type(exc).__name__`` only, which is exactly
    why Session 219's verdict-deciding event could never be traced to one of the
    18 ``LLMParseError`` raise sites.
    """
    scored: list[str] = []
    sweep_sql_capabilities(
        _primary_cases()[:1],
        _FakeRunner(primary_error=LLMParseError("expected JSON array, got str")),
        seeded_pc_db,
        n_samples=1,
        max_transient_retries=2,
        on_event=scored.append,
    )

    assert any("transient" in n and "attempt 1/3" in n for n in scored)
    assert any("parse+exec+qc fail" in n for n in scored)
    assert all("expected JSON array, got str" in n for n in scored), "every note carries str(exc)"

    excluded: list[str] = []
    sweep_sql_capabilities(
        _primary_cases()[:1],
        _FakeRunner(primary_error=_conn_error()),
        seeded_pc_db,
        n_samples=1,
        max_transient_retries=1,
        on_event=excluded.append,
    )

    assert any("excluded" in n for n in excluded)
    assert any("dropped" in n for n in excluded), "the transport message text survives too"


def test_the_default_retry_bound_is_what_the_live_call_sites_get(
    seeded_pc_db: ReadOnlyDB,
) -> None:
    """The one number that governs the live gate, pinned.

    ``shadow_run`` and ``test_eval_live`` both call the sweep **without**
    ``max_transient_retries``, while every other retry test here injects it
    explicitly. So without this test ``_MAX_TRANSIENT_RETRIES = 0`` would silently
    revert the live gate to Session 218 best-of-1 — the exact semantics that let
    one blip decide the S219 verdict — with the whole suite green.
    """
    runner = _FakeRunner(primary_error=LLMParseError("blip"))

    result = sweep_sql_capabilities(_primary_cases()[:1], runner, seeded_pc_db, n_samples=1)

    assert len(runner.primary_calls) == 3, "the default bound is 2 retries => 3 attempts"
    assert result.transient_retries == 2


def test_mixed_class_exhaustion_is_scored_not_excluded(seeded_pc_db: ReadOnlyDB) -> None:
    """Any scored failure beats an exclusion, whatever landed last.

    A sample that emitted unparseable output twice and *then* timed out has
    produced judgeable output — twice. Reading only the final attempt's class
    would exclude it, dropping real model-quality evidence from the denominator:
    the precise failure the two-tier split exists to prevent. Measured before the
    fix: six observed parse failures across three samples scored **zero** misses
    and passed the 1.00 bar.
    """
    runner = _FakeRunner(
        primary_error_sequence=[LLMParseError("truncated"), LLMParseError("truncated"), _timeout()]
    )

    result = sweep_sql_capabilities(
        _primary_cases()[:1], runner, seeded_pc_db, n_samples=1, max_transient_retries=2
    )

    assert result.parse_failures == 1, "the parse evidence is scored, not discarded"
    assert result.excluded_transient == 0
    assert result.parse_results == [False]
    assert result.exec_results == [False]
    assert result.qc_results == [False]
    assert pass_rate("sql_parse", result.parse_results).meets(SQL_PARSE_VALID_MIN) is False


def test_mixed_class_exhaustion_is_scored_in_either_order(seeded_pc_db: ReadOnlyDB) -> None:
    """The rule is 'any scored failure', not 'the first' or 'the last' one.

    Transport first, parse in the middle, transport last — still scored, and the
    note names the *scored* exception rather than whichever error landed last.
    """
    notes: list[str] = []
    runner = _FakeRunner(
        primary_error_sequence=[_conn_error(), LLMParseError("non-JSON: 'Sure!'"), _timeout()]
    )

    result = sweep_sql_capabilities(
        _primary_cases()[:1],
        runner,
        seeded_pc_db,
        n_samples=1,
        max_transient_retries=2,
        on_event=notes.append,
    )

    assert result.parse_failures == 1
    assert result.excluded_transient == 0
    terminal = [n for n in notes if "parse+exec+qc fail" in n]
    assert len(terminal) == 1
    assert "LLMParseError" in terminal[0], "the note names the failure being scored"
    assert "non-JSON: 'Sure!'" in terminal[0]


def test_an_empty_capability_denominator_fails_its_bar() -> None:
    """Exclusion cannot manufacture a vacuous pass.

    ``CapabilityRate.rate`` returns 0.0 when ``total == 0``, so a sweep that
    excluded everything fails the 1.00 bar rather than passing on no evidence.
    Pinned because nothing else covers the empty case, and because it is the
    only thing standing between exclusion and a silent gate bypass.
    """
    assert pass_rate("sql_parse", []).meets(SQL_PARSE_VALID_MIN) is False
