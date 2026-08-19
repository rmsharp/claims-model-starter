"""Governance-agreement sweep — one transient policy for both live surfaces.

The §3.4 governance capabilities (``governance_cycle_time_agreement``,
``governance_laxer_miss``) are measured by asking a live intake client to
classify each corpus draft and scoring the prediction against its reference.
This module owns the *statistics* of that measurement so the assertion gate
(``test_eval_live``) and the report-number producer
(``shadow_run.measure_provider``) stay in lock-step on one definition — the same
role :mod:`tests.eval.interview_sweep` plays for the interview capability and
:mod:`tests.eval.sql_sweep` for the SQL ones, and for the same reason (gap #1c's
duplicated-loop drift, Session 169).

It exists to close the **last** of the three-different-transient-policies gaps
(filed Session 221, fixed Session 225). Before it, the two governance call sites
were separate hand-written loops that disagreed with each other about what a
seam error means:

* ``shadow_run.measure_provider`` caught ``IntakeLLMError`` and scored it an
  immediate non-agreement, with **no retry** — the exact Session 219 shape that
  cost ``opencode`` a cutover verdict on a single event later measured at 1 in
  60. It also caught *only* that class.
* ``test_eval_live``'s governance test had **no handler at all**, so the same
  error aborted the gate outright.

Neither caught a transport error, and ``classify_governance`` does not wrap one:
``AnthropicLLMClient._call_json`` calls ``messages.create`` bare, so an
``APITimeoutError`` raised after the SDK exhausts its own retries propagated past
both sites — aborting a ~2.5-hour shadow run mid-measurement. That is the hole
Session 171 closed for the interview block and Session 221 closed for the SQL
block; this closes it for the third.

**Failure classification.** Two exhaustion tiers, mirroring
:mod:`tests.eval.sql_sweep` because the same argument applies to the same shape
of catch-all:

* ``_TRANSIENT_SCORED`` (``IntakeLLMError``) is retried, then **scored a
  non-agreement**. The class is the intake client's catch-all over its whole
  parse path (``max_tokens`` truncation, empty content list, a non-``TextBlock``
  first block, non-JSON text, a missing key), and every one of those *is* the
  model failing to produce a usable governance classification — the capability
  under measurement. Excluding instead would shrink the denominator, and since
  every surviving sample is clean by construction, a provider failing 24 of 25
  samples would score 1/1 = 100% and **pass** a bar it fails 4% of today.
* ``_TRANSIENT_EXCLUDED`` (SDK transport errors) is retried, then **excluded**
  with a logged note and counted in ``excluded_transient``, mirroring both
  sibling sweeps. No model output exists to judge, so scoring one a miss would
  convert a network outage into a model verdict.
* **Anything else propagates**, so a real harness/transport bug surfaces loudly
  instead of being laundered into a rate. ``APIStatusError`` (4xx/5xx: bad model
  id, auth, rate limit) is a *sibling* of ``APIConnectionError``, not a subclass,
  and is therefore deliberately not caught (FM #18).

**A seam failure never feeds the zero-tolerance bar.** A scored exhaustion
appends ``False`` to ``cycle_matches`` and ``risk_acceptable`` but leaves
``laxer_misses`` alone: the sample produced no risk tier, so counting it a
laxer-tier miss would fabricate a failure on a metric whose maximum is **0** —
turning one blip into a NO-GO, which is the pathology this item exists to
remove. ``shadow_run`` already behaved this way and the behaviour is preserved
verbatim; it is stated here because it is the one rule in this module that is
not inherited from a sibling.

The consequence is deliberate and worth naming: a provider that fails *every*
governance call reports ``governance_laxer_miss = 0`` and passes that row, while
failing ``governance_cycle_time_agreement`` at 0.0 — a rate of 0/0 is 0.0, not
1.0 (``CapabilityRate.rate``). Zero laxer predictions is the honest count for a
provider that made zero predictions; the gate still says NO-GO, on the row that
can actually see the failure.

**``risk_acceptable`` and ``laxer_misses`` therefore diverge on a seam failure**
— they are exact complements only for samples that produced a prediction. The
first is a diagnostic (``governance_risk_tier_acceptable``, no gate row); the
second is gated. Preserving ``shadow_run``'s existing ``False`` keeps the
diagnostic on the conservative side and keeps the two per-sample lists the same
length.

**What an exclusion costs the zero-tolerance row — a different shape.**
``governance_cycle_time_agreement`` is a *rate*, so an exclusion shrinks
numerator and denominator together and the measured value is unbiased.
``governance_laxer_miss`` is a *count* against a maximum of 0, so an exclusion
removes one chance to **observe** a laxer prediction and can only ever move that
row toward PASS. A provider whose transport is flaky is therefore judged on fewer
governance samples than one whose transport is clean. This is the accepted price
of not aborting the whole run on a network blip — the alternative both sibling
sweeps already rejected — and it is why ``excluded_transient`` is reported on
every surface: a shrunken denominator must be visible, not inferred. Read the
count row together with that counter, never alone.

**A cross-provider asymmetry this sweep inherits and does not fix.** The two-tier
split keys on exception *class*, and only the SDK providers (``anthropic``,
``bedrock``) raise the transport classes. The ``opencode`` adapter is a
subprocess client that maps spawn failure, non-zero exit and timeout onto
``IntakeLLMError``, so its transport failures land in the **scored** tier while
the same real-world event on an SDK provider lands in the excluded one. That
predates this module and applies identically to both sibling sweeps; it is filed,
not fixed here, because correcting it means changing the adapter's error mapping.

**What the retry costs, stated plainly.** Best-of-3 turns an effective
per-sample failure rate of ``p`` into ``p**3`` against unchanged bars, exactly as
in ``sql_sweep``. ``transient_retries`` is reported so the first-attempt rate
stays recoverable. **No threshold moved** — ``GOVERNANCE_CYCLE_TIME_AGREEMENT_MIN``
is still 0.90 and ``GOVERNANCE_LAXER_MISSES_MAX`` still 0 (a policy fix, not a
#129 loosening). It does mean **post-fix governance numbers are not comparable
with Sessions 216-220**, which measured best-of-1 on this capability.

The sweep calls **no LLM directly**: it receives a ``classify`` callable, so the
sampling + error-classification logic is deterministically unit-testable with a
fake (``test_governance_sweep``), mirroring how ``interview_sweep`` takes a
``run_one`` and ``sql_sweep`` takes a client-shaped ``runner``.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from functools import partial
from typing import TypeVar

from anthropic import APIConnectionError, APITimeoutError

from model_project_constructor.agents.intake.protocol import (
    DraftReportResult,
    GovernanceClassification,
    IntakeLLMError,
)
from tests.eval.eval_corpus import GovernanceCase
from tests.eval.eval_scoring import score_governance
from tests.eval.interview_sweep import N_SAMPLES, OnEvent

__all__ = [
    "ClassifyGovernance",
    "GovernanceSweepResult",
    "governance_sweep_summary",
    "sweep_governance_agreement",
]

#: Bounded retries for a *transient* per-sample failure; ``attempts`` is this
#: plus one. Deliberately a local constant rather than an import of either
#: sibling's private one: learning #86 asks the blocks to share a *policy*, not a
#: symbol, and the transient tuples cannot be shared at all (``sql_sweep``'s
#: scored member is a ``ValueError`` from the data-agent wheel; this one's is a
#: ``RuntimeError`` from the intake package). Keep the three values in lock-step
#: by hand — they feed one gate.
_MAX_TRANSIENT_RETRIES = 2

#: Retried, then **scored a non-agreement** on exhaustion (the denominator never
#: shrinks). See the module docstring for why this class must not be excluded on.
_TRANSIENT_SCORED: tuple[type[Exception], ...] = (IntakeLLMError,)

#: Retried, then **excluded** on exhaustion and counted in
#: ``excluded_transient``. Raised by the Anthropic SDK only *after* it exhausts
#: its own retries — a network blip during a ~2.5-hour live sweep, with no model
#: output to judge. ``APITimeoutError`` is a subclass of ``APIConnectionError``;
#: ``APIStatusError`` is a sibling and is deliberately NOT caught (FM #18).
#: Before this module neither was caught at either governance call site, so one
#: blip aborted the whole live run.
_TRANSIENT_EXCLUDED: tuple[type[Exception], ...] = (APITimeoutError, APIConnectionError)

#: What the retry loop catches. Everything outside it propagates.
_TRANSIENT_ERRORS: tuple[type[Exception], ...] = (*_TRANSIENT_EXCLUDED, *_TRANSIENT_SCORED)

_T = TypeVar("_T")

#: Classifies one draft. Injected so the sweep's statistics are testable without
#: an API key; both call sites pass a live client's bound ``classify_governance``.
ClassifyGovernance = Callable[[DraftReportResult], GovernanceClassification]


@dataclass(frozen=True)
class GovernanceSweepResult:
    """Pooled outcome of sweeping the governance corpus ``n_samples`` times per case.

    ``cycle_matches`` is what ``pass_rate`` consumes for the gated
    ``governance_cycle_time_agreement`` row; ``laxer_misses`` is the
    zero-tolerance ``governance_laxer_miss`` count; ``risk_acceptable`` is the
    ungated match-or-stricter diagnostic.

    The three counters are diagnostics, never gate keys, and every surface that
    reports this sweep should carry them: ``seam_failures`` and
    ``transient_retries`` together bound the pre-retry first-attempt rate, and
    ``excluded_transient`` is the only trace that the pooled denominator is
    smaller than ``n_samples * cases``. All four trailing fields carry defaults
    so the two-list construction stays valid.
    """

    cycle_matches: list[bool]
    risk_acceptable: list[bool]
    #: Predictions strictly laxer than their reference tier. **Never incremented
    #: by a seam failure** — see the module docstring.
    laxer_misses: int = 0
    #: Samples that exhausted every attempt and raised ``IntakeLLMError`` on at
    #: least one of them, and were therefore scored a non-agreement. **Not**
    #: "every attempt raised it": a sample that raised ``IntakeLLMError`` once
    #: and then timed out twice produced judgeable output, so it is scored, not
    #: excluded (``_call_with_retries``'s mixed-evidence rule).
    seam_failures: int = 0
    #: Retry attempts spent on a transient, pooled over every sample. Diagnostic
    #: only, and a **bound** rather than an inverse: it is enough to reconstruct
    #: how many first attempts failed in total, not which samples they fell on,
    #: so the pre-retry rate is recoverable only as an interval.
    transient_retries: int = 0
    #: Samples dropped after exhausting retries on a *transport* transient
    #: (logged, not scored). Same name and meaning as the two sibling sweeps'.
    excluded_transient: int = 0


def sweep_governance_agreement(
    cases: Iterable[GovernanceCase],
    classify: ClassifyGovernance,
    *,
    n_samples: int = N_SAMPLES,
    max_transient_retries: int = _MAX_TRANSIENT_RETRIES,
    on_event: OnEvent | None = None,
) -> GovernanceSweepResult:
    """Sample each governance case ``n_samples`` times and pool the scores.

    Every case is measured — unlike the sibling sweeps there is no ``kind``/
    ``expect_complete`` filter, because every governance corpus case carries a
    reference label the §3.4 rows are defined over.

    Each call is retried up to ``max_transient_retries`` times. An
    ``IntakeLLMError`` that survives every attempt costs that *sample*: one
    cycle_time miss and one risk-diagnostic miss, and **no** laxer-tier miss. A
    transport transient that survives every attempt **excludes** the sample
    instead. Anything not in ``_TRANSIENT_ERRORS`` propagates.
    """
    notify = on_event or (lambda _msg: None)
    cycle_matches: list[bool] = []
    risk_acceptable: list[bool] = []
    laxer_misses = 0
    seam_failures = 0
    transient_retries = 0
    excluded_transient = 0

    for case in cases:
        for sample in range(n_samples):
            marker = f"{case.case_id}[{sample + 1}/{n_samples}]"
            # ``partial`` rather than a closure: it binds the loop variable
            # explicitly (no ruff B023), matching ``sql_sweep``'s call sites.
            predicted, excluded, retries = _call_with_retries(
                partial(classify, case.draft),
                label=f"governance/{marker}",
                scored_effect="non-agreement",
                max_transient_retries=max_transient_retries,
                notify=notify,
            )
            transient_retries += retries
            if predicted is None:
                if excluded:
                    excluded_transient += 1
                else:
                    seam_failures += 1
                    cycle_matches.append(False)
                    # NOT a laxer miss: no tier was predicted. See the module
                    # docstring — this is the zero-tolerance row the whole item
                    # exists to keep clean.
                    risk_acceptable.append(False)
                continue

            score = score_governance(case.case_id, case.reference, predicted)
            cycle_matches.append(score.cycle_time_match)
            risk_acceptable.append(score.risk_tier_acceptable)
            laxer_misses += int(score.laxer_tier_miss)

    return GovernanceSweepResult(
        cycle_matches=cycle_matches,
        risk_acceptable=risk_acceptable,
        laxer_misses=laxer_misses,
        seam_failures=seam_failures,
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
    rather than reading the last attempt. A sample that raised ``IntakeLLMError``
    twice and then timed out has *produced judgeable output* — twice — so
    excluding it would drop a real model-quality observation from the
    denominator, which is precisely the failure mode the two-tier split exists to
    prevent. The bias is deliberate and one-directional: mixed evidence is
    scored, never excluded.

    Every note carries ``str(exc)``, not just the type name. Session 219's
    verdict-deciding event could never be attributed to a raise site because the
    message was discarded.

    A deliberate near-duplicate of ``sql_sweep._call_with_retries``: the two
    differ only in the module-level transient tuples they close over, and
    learning #86 asks these blocks to share a policy rather than a symbol.
    Hoisting one generic copy into a shared module is a cross-module refactor
    ``SAFEGUARDS.md`` gates behind plan mode — filed for a future session rather
    than smuggled into a fix.
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


def governance_sweep_summary(result: GovernanceSweepResult) -> str:
    """A one-line numerator/denominator summary — never a bare rate.

    Mirrors ``sql_sweep_summary``: without the counters a pooled denominator and
    a denominator shrunk by exclusions are indistinguishable, and
    ``transient_retries`` is what makes the first-attempt rate recoverable after
    a best-of-3 run.
    """

    def frac(results: Sequence[bool]) -> str:
        return f"{sum(results)}/{len(results)}"

    return (
        f"governance_cycle_time {frac(result.cycle_matches)} | "
        f"risk_tier_acceptable {frac(result.risk_acceptable)} | "
        f"laxer_misses {result.laxer_misses} | "
        f"seam_failures {result.seam_failures} | "
        f"transient_retries {result.transient_retries} | "
        f"excluded_transient {result.excluded_transient}"
    )
