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

**Failure classification (revised, Session 221).** Until Session 221 a single
``LLMParseError`` from either seam was scored an immediate miss with **no
retry**, while :mod:`tests.eval.interview_sweep` retried its own seam errors —
two blocks feeding one gate under opposite policies (gap #1c, half-applied).
Against the 100% ``sql_parse`` and ``qc_structural`` bars one blip therefore
decided a verdict, and in Session 219 one did: a single event produced the
``opencode`` NO-GO, and Session 220's 45-sample probe put that event's rate at
1 in 60. The class is now retried — but with **two exhaustion policies**, because
the one catch had to cover two different kinds of failure:

* ``_TRANSIENT_SCORED`` (``LLMParseError``) is retried, then **scored a miss**
  exactly as before. This class is the data agent's catch-all over 18 raise
  sites and only some of them are about JSON, so it is far too coarse to
  *exclude* on: excluding drops the sample from the denominator, and since every
  surviving sample is clean by construction, a provider failing 14 of 15 samples
  would score 1/1 = 100% and **pass** a bar it fails 6.7% of today. At the
  measured 1-in-60 rate, three failures running is a ~1-in-216,000 event, so an
  exhaustion is never a transient in practice — it is systematic, and systematic
  is exactly what the gate exists to catch. This path is also the live tier's
  **only** observation that a provider can emit parseable JSON at all
  (``shadow_run.py`` hardcodes ``json_parse`` to 1.0 — the parity battery is
  deterministic).
* ``_TRANSIENT_EXCLUDED`` (SDK transport errors) is retried, then **excluded**
  with a logged note and counted in ``excluded_transient``, mirroring
  ``interview_sweep``. No model output exists to judge, so scoring one a miss
  would convert a network outage into a model verdict — a new route to the very
  pathology this fix removes.
* **Anything else propagates**, so a real harness/transport bug surfaces loudly
  instead of being laundered into a rate (the ``interview_sweep`` docstring's
  argument, preserved). ``APIStatusError`` (4xx/5xx: bad model id, auth, rate
  limit) is a *sibling* of ``APIConnectionError``, not a subclass, and is
  therefore deliberately not caught (FM #18).

**What the retry costs, stated plainly.** Best-of-3 turns an effective
per-sample failure rate of ``p`` into ``p**3`` against unchanged bars. A provider
whose true rate is 20% goes from a 3.5% chance of clearing ``sql_parse`` to
88.6%. That is a real loss of detection power that no threshold diff will show,
which is why ``transient_retries`` is reported: the first-attempt rate stays
recoverable from it. **No threshold moved** — ``SQL_PARSE_VALID_MIN`` and
``QUALITY_CHECKS_STRUCTURAL_MIN`` are still 1.00 and ``SQL_EXECUTABLE_MIN`` still
0.95 (this is a policy/denominator fix, not a #129 loosening, exactly as the two
prior gap-#1c changes were). It also means **post-fix numbers are not comparable
with Sessions 219 and 220**: those measured best-of-1 on the same corpus.

Session 218's docstring argued the no-retry behaviour was correct *deliberately*,
and it was right about the half it defended — a model that cannot emit parseable
JSON has failed that sample. What it could not express is that the exception type
is too coarse to carry the policy, not that the reasoning was careless. Retrying
first, then scoring the miss, keeps that argument intact and applies it to "three
times running" instead of "once".
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field
from functools import partial
from typing import Any, Protocol, TypeVar

from anthropic import APIConnectionError, APITimeoutError
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

#: Bounded retries for a *transient* per-sample failure; ``attempts`` is this
#: plus one. Deliberately a local constant rather than an import of
#: ``interview_sweep._MAX_TRANSIENT_RETRIES``: learning #86 asks the two blocks
#: to share a *policy*, not a symbol, and the two transient tuples cannot be
#: shared at all (that module's members are ``RuntimeError`` subclasses from the
#: intake package; this one's is a ``ValueError`` from the data-agent wheel).
#: Keep the two values in lock-step by hand — they feed one gate.
_MAX_TRANSIENT_RETRIES = 2

#: Retried, then **scored a miss** on exhaustion (the denominator never shrinks).
#: See the module docstring for why this class must not be excluded on.
_TRANSIENT_SCORED: tuple[type[Exception], ...] = (LLMParseError,)

#: Retried, then **excluded** on exhaustion and counted in
#: ``excluded_transient``. These are raised by the Anthropic SDK only *after* it
#: exhausts its own retries — a network blip during a ~2.5-hour live sweep, with
#: no model output to judge. ``APITimeoutError`` is a subclass of
#: ``APIConnectionError``; ``APIStatusError`` is a sibling and is deliberately
#: NOT caught (FM #18). Before Session 221 neither was caught here at all, so one
#: blip aborted the whole live run — the hole Session 171 closed for the
#: interview block and never applied to this one.
_TRANSIENT_EXCLUDED: tuple[type[Exception], ...] = (APITimeoutError, APIConnectionError)

#: What the retry loop catches. Everything outside it propagates.
_TRANSIENT_ERRORS: tuple[type[Exception], ...] = (*_TRANSIENT_EXCLUDED, *_TRANSIENT_SCORED)

_T = TypeVar("_T")


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

    The three counters are diagnostics, never gate keys, and every surface that
    reports this sweep should carry them: ``parse_failures`` and
    ``transient_retries`` together make the pre-retry first-attempt rate
    recoverable, and ``excluded_transient`` is the only trace that the pooled
    denominator is smaller than ``n_samples * cases``. All four fields carry
    defaults so the three-list construction stays valid.
    """

    parse_results: list[bool]
    exec_results: list[bool]
    qc_results: list[bool]
    #: ``(case name, error text)`` for each query that failed to execute.
    exec_errors: list[tuple[str, str]] = field(default_factory=list)
    #: Samples whose primary-query call raised ``LLMParseError`` on **every**
    #: attempt and were therefore scored a miss (parse + exec + QC).
    parse_failures: int = 0
    #: Retry attempts spent on a transient, pooled over both seams. Diagnostic
    #: only — it is how the first-attempt rate stays recoverable after the fact.
    transient_retries: int = 0
    #: Samples dropped after exhausting retries on a *transport* transient
    #: (logged, not scored). Same name and meaning as
    #: ``InterviewSweepResult.excluded_transient``.
    excluded_transient: int = 0


def sweep_sql_capabilities(
    cases: Iterable[SqlCase],
    runner: SqlCapabilityRunner,
    db: ReadOnlyDB,
    *,
    inventory: DataSourceInventory | None = None,
    n_samples: int = N_SAMPLES,
    max_transient_retries: int = _MAX_TRANSIENT_RETRIES,
    on_event: OnEvent | None = None,
) -> SqlSweepResult:
    """Sample each ``kind == "primary"`` SQL case ``n_samples`` times and pool.

    Non-primary cases are skipped — ``kind: baseline`` maps to
    ``generate_baseline_query``, which no §3.4 threshold scores (it has no gate
    key), so feeding it here would spend calls the gate cannot read.

    Each seam call is retried up to ``max_transient_retries`` times. An
    ``LLMParseError`` that survives every attempt costs that *sample*, not the
    whole case: it records one parse miss, one exec miss and one QC miss, then
    moves to the next sample. (Before this module the equivalent ``continue``
    abandoned the entire case.) The quality-checks call is retried the same way
    and an exhausted ``LLMParseError`` there scores one QC miss, leaving that
    sample's parse and exec observations — already recorded — untouched. A
    transport transient that survives every attempt **excludes** the sample
    instead, which for the QC seam drops only that sample's QC datum. Anything
    that is not in ``_TRANSIENT_ERRORS`` propagates.
    """
    notify = on_event or (lambda _msg: None)
    parse_results: list[bool] = []
    exec_results: list[bool] = []
    qc_results: list[bool] = []
    exec_errors: list[tuple[str, str]] = []
    parse_failures = 0
    transient_retries = 0
    excluded_transient = 0

    for case in cases:
        if case.kind != "primary":
            continue
        for sample in range(n_samples):
            marker = f"{case.name}[{sample + 1}/{n_samples}]"
            # ``partial`` rather than a closure: it binds the loop variable
            # explicitly (no ruff B023), and it makes visible that no retry ever
            # passes ``previous_error`` — see ``_call_with_retries``.
            specs, excluded, retries = _call_with_retries(
                partial(
                    runner.generate_primary_queries, case.request, data_source_inventory=inventory
                ),
                label=f"sql/{marker}",
                scored_effect="parse+exec+qc fail",
                max_transient_retries=max_transient_retries,
                notify=notify,
            )
            transient_retries += retries
            if specs is None:
                if excluded:
                    excluded_transient += 1
                else:
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
                    notify(f"sql/{marker}: not executable -> {error}")

            qc_lists, qc_excluded, qc_retries = _call_with_retries(
                partial(runner.generate_quality_checks, case.request, specs),
                label=f"qc/{marker}",
                scored_effect="structural fail",
                max_transient_retries=max_transient_retries,
                notify=notify,
            )
            transient_retries += qc_retries
            if qc_lists is None:
                if qc_excluded:
                    excluded_transient += 1
                else:
                    qc_results.append(False)
            else:
                qc_results.append(quality_checks_structural_ok(len(specs), qc_lists))

    return SqlSweepResult(
        parse_results=parse_results,
        exec_results=exec_results,
        qc_results=qc_results,
        exec_errors=exec_errors,
        parse_failures=parse_failures,
        transient_retries=transient_retries,
        excluded_transient=excluded_transient,
    )


def _call_with_retries(
    call: Callable[[], _T],
    *,
    label: str,
    scored_effect: str,
    max_transient_retries: int,
    notify: OnEvent,
) -> tuple[_T | None, bool, int]:
    """Run one seam call, retrying a *transient* failure up to the bound.

    Returns ``(value, excluded, retries_spent)``. ``value is None`` means every
    attempt failed; ``excluded`` is then True only when **every** failure was a
    transport transient, in which case the caller drops the sample rather than
    scoring it. A non-transient error is not caught here — it propagates so a
    genuine harness bug surfaces loudly.

    **Any scored failure wins over an exclusion**, which is why this accumulates
    rather than reading the last attempt. A sample that raised ``LLMParseError``
    twice and then timed out has *produced judgeable output* — twice — so
    excluding it would drop a real model-quality observation from the
    denominator, which is precisely the failure mode the two-tier split exists
    to prevent. Reading only the last attempt made that reachable: six observed
    parse failures across three samples scored zero misses and passed the 1.00
    bar. The bias is deliberate and one-directional — mixed evidence is scored,
    never excluded.

    ``call`` is deliberately zero-argument. The primary-query seam accepts a
    ``previous_error`` that injects "Your previous response produced invalid SQL
    … Return corrected SQL this time" into the prompt; a retry that passed it
    would silently turn ``sql_parse`` from *can this model emit valid SQL
    unaided* into *can it emit valid SQL given a correction hint* — a different
    capability behind an unchanged 1.00 threshold. Binding the call at the call
    site keeps that impossible by construction.

    Every note carries ``str(exc)``, not just the type name. Session 219's
    verdict-deciding event could never be attributed to one of the 18
    ``LLMParseError`` raise sites because the message was discarded here.
    """
    attempts = max_transient_retries + 1
    last_exc: Exception | None = None
    # The exception the miss is attributed to, if any attempt produced one. Kept
    # separate from ``last_exc`` so a mixed sequence names the failure actually
    # being scored rather than whichever error happened to land last.
    scored_exc: Exception | None = None
    for attempt in range(attempts):
        try:
            return call(), False, attempt
        except _TRANSIENT_ERRORS as exc:
            last_exc = exc
            if isinstance(exc, _TRANSIENT_SCORED):
                scored_exc = exc
            if attempt + 1 < attempts:
                notify(
                    f"{label}: transient {type(exc).__name__} "
                    f"(attempt {attempt + 1}/{attempts}); retrying: {exc}"
                )
    if scored_exc is None:
        name = type(last_exc).__name__
        notify(f"{label}: excluded after {attempts} transient failures (last: {name}): {last_exc}")
        return None, True, max_transient_retries
    name = type(scored_exc).__name__
    notify(f"{label}: {name} after {attempts} attempts -> {scored_effect}: {scored_exc}")
    return None, False, max_transient_retries


def sql_sweep_summary(result: SqlSweepResult) -> str:
    """A one-line numerator/denominator summary — never a bare rate.

    Session 216's gotcha 2: ``sql_exec``'s denominator is model-chosen, so a bare
    percentage is not comparable across providers or runs. Every surface that
    reports this metric must show both numbers — and, since Session 221, the
    retry/exclusion counters too: without them a pooled denominator cannot be
    told apart from a shrunken one.
    """
    def frac(results: Sequence[bool]) -> str:
        return f"{sum(results)}/{len(results)}"

    return (
        f"sql_parse {frac(result.parse_results)} | "
        f"sql_exec {frac(result.exec_results)} | "
        f"qc_structural {frac(result.qc_results)} | "
        f"parse_failures {result.parse_failures} | "
        f"transient_retries {result.transient_retries} | "
        f"excluded_transient {result.excluded_transient}"
    )
