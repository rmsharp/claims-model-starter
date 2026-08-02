"""SQL-capability sweep — robust §3.4 sampling for the live tier.

The §3.4 SQL capabilities (``sql_parse``, ``sql_exec``, ``qc_structural``) are
measured by asking a live data-agent client for primary queries over the corpus,
parsing and executing what comes back, and asking for quality checks over those
queries. This module owns the *statistics* of that measurement so the assertion
gate (``test_eval_live``) and the report-number producer
(``shadow_run.measure_provider``) stay in lock-step on one definition — the same
role :mod:`tests.eval.interview_sweep` plays for the interview capability, and
for the same reason (gap #1c's duplicated-loop drift, Session 169).

It exists to fix the SQL block's **single-shot** measurement (Session 218). The
governance loop samples each case ``N_SAMPLES`` (>=5) times and pools; the
interview sweep does the same; the SQL block did neither — it ran each of the 3
``kind: primary`` cases exactly once. The consequences were structural, not
stylistic:

* ``sql_exec``'s denominator was ~5 model-chosen queries. Against a 95% bar that
  is effectively pass-only-if-perfect, and one stochastic miss reads as a 20%
  quality drop. Sessions 216 and 217 both measured this metric and both had to
  write "do not quote this as a rate" caveats around the result — S216 recorded
  ``anthropic`` 3/5 and ``opencode`` 3/7 in one run and 2/4 / 4/7 in another,
  with the provider ordering *reversing* between them.
* ``qc_structural`` was a pass-rate over **3 booleans** against a 100% bar, so a
  single miss scored 66.7%.

Sampling ``n_samples`` times per case and pooling raises the denominator by 5x
without touching a threshold. **This is a harness-statistics fix, not a
threshold loosening** — ``SQL_EXECUTABLE_MIN`` stays 0.95, exactly as it stayed
through the interview equivalent.

The sweep calls **no LLM directly**: it receives a client-shaped ``runner``, so
the sampling + error-classification logic is deterministically unit-testable
with a fake (``test_sql_sweep``), mirroring how ``interview_sweep`` takes a
``run_one`` callable and how ``eval_scoring`` keeps scoring testable without an
API key.

**Failure classification.** A ``LLMParseError`` from either seam is a *measured
miss*, not a crash — the same call the pre-existing loops made, preserved
deliberately: a model that cannot emit parseable JSON for a SQL request has
failed that sample. Anything else propagates, so a real harness/transport bug
surfaces loudly instead of being laundered into a rate (the ``interview_sweep``
docstring's argument, applied here).
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from typing import Any, Protocol

from model_project_constructor_data_agent.anthropic_client import LLMParseError
from model_project_constructor_data_agent.db import ReadOnlyDB
from model_project_constructor_data_agent.llm import PrimaryQuerySpec
from model_project_constructor_data_agent.schemas import DataRequest, DataSourceInventory

from tests.eval.eval_corpus import SqlCase
from tests.eval.eval_scoring import (
    quality_checks_structural_ok,
    sql_execution_error,
    sql_parse_valid,
)
from tests.eval.interview_sweep import N_SAMPLES, OnEvent

__all__ = ["SqlCapabilityRunner", "SqlSweepResult", "sweep_sql_capabilities"]


class SqlCapabilityRunner(Protocol):
    """The two data-agent seams this sweep measures.

    Structural, not nominal: the real ``AnthropicLLMClient`` (and its ``bedrock``
    and ``opencode`` subclasses) satisfy it as-is, and a test fake satisfies it
    without importing an SDK or holding a key.
    """

    def generate_primary_queries(
        self,
        request: DataRequest,
        previous_error: str | None = None,
        *,
        data_source_inventory: DataSourceInventory | None = None,
    ) -> list[PrimaryQuerySpec]: ...

    def generate_quality_checks(
        self, request: DataRequest, primary_queries: list[PrimaryQuerySpec]
    ) -> list[list[Any]]: ...


@dataclass(frozen=True)
class SqlSweepResult:
    """Pooled outcome of sweeping the SQL corpus ``n_samples`` times per case.

    The three lists are what ``pass_rate`` consumes, pooled across every case and
    every sample exactly as ``interview_sweep`` pools its per-sample booleans.
    ``exec_errors`` carries no weight in any gate — it is the diagnostic channel
    Session 216 had to rebuild from scratch because ``sql_executes`` collapsed
    every failure to one bit (its gotcha 3).
    """

    parse_results: list[bool]
    exec_results: list[bool]
    qc_results: list[bool]
    #: ``(case name, error text)`` for each query that failed to execute.
    exec_errors: list[tuple[str, str]] = field(default_factory=list)
    #: Samples whose primary-query call raised ``LLMParseError`` (scored a miss).
    parse_failures: int = 0


def sweep_sql_capabilities(
    cases: Iterable[SqlCase],
    runner: SqlCapabilityRunner,
    db: ReadOnlyDB,
    *,
    inventory: DataSourceInventory | None = None,
    n_samples: int = N_SAMPLES,
    on_event: OnEvent | None = None,
) -> SqlSweepResult:
    """Sample each ``kind == "primary"`` SQL case ``n_samples`` times and pool.

    Non-primary cases are skipped — ``kind: baseline`` maps to
    ``generate_baseline_query``, which no §3.4 threshold scores (it has no gate
    key), so feeding it here would spend calls the gate cannot read.

    A ``LLMParseError`` on the primary-query call costs that *sample*, not the
    whole case: it records one parse miss, one exec miss and one QC miss, then
    moves to the next sample. Before this module the equivalent ``continue``
    abandoned the entire case.
    """
    notify = on_event or (lambda _msg: None)
    parse_results: list[bool] = []
    exec_results: list[bool] = []
    qc_results: list[bool] = []
    exec_errors: list[tuple[str, str]] = []
    parse_failures = 0

    for case in cases:
        if case.kind != "primary":
            continue
        for sample in range(n_samples):
            try:
                specs = runner.generate_primary_queries(
                    case.request, data_source_inventory=inventory
                )
            except LLMParseError as exc:
                notify(
                    f"sql/{case.name}[{sample + 1}/{n_samples}]: "
                    f"{type(exc).__name__} on primary queries -> parse+exec+qc fail"
                )
                parse_failures += 1
                parse_results.append(False)
                exec_results.append(False)
                qc_results.append(False)
                continue

            for spec in specs:
                parse_results.append(sql_parse_valid(spec.sql))
                error = sql_execution_error(db, spec.sql)
                exec_results.append(error is None)
                if error is not None:
                    exec_errors.append((case.name, error))
                    notify(f"sql/{case.name}[{sample + 1}/{n_samples}]: not executable -> {error}")

            try:
                qc_lists = runner.generate_quality_checks(case.request, specs)
                qc_results.append(quality_checks_structural_ok(len(specs), qc_lists))
            except LLMParseError as exc:
                notify(
                    f"qc/{case.name}[{sample + 1}/{n_samples}]: "
                    f"{type(exc).__name__} on quality checks -> structural fail"
                )
                qc_results.append(False)

    return SqlSweepResult(
        parse_results=parse_results,
        exec_results=exec_results,
        qc_results=qc_results,
        exec_errors=exec_errors,
        parse_failures=parse_failures,
    )


def sql_sweep_summary(result: SqlSweepResult) -> str:
    """A one-line numerator/denominator summary — never a bare rate.

    Session 216's gotcha 2: ``sql_exec``'s denominator is model-chosen, so a bare
    percentage is not comparable across providers or runs. Every surface that
    reports this metric must show both numbers.
    """
    def frac(results: Sequence[bool]) -> str:
        return f"{sum(results)}/{len(results)}"

    return (
        f"sql_parse {frac(result.parse_results)} | "
        f"sql_exec {frac(result.exec_results)} | "
        f"qc_structural {frac(result.qc_results)} | "
        f"parse_failures {result.parse_failures}"
    )
