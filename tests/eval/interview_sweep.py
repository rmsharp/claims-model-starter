"""Interview-convergence sweep — robust §3.4 sampling for the live tier.

The §3.4 interview-convergence capability is measured by driving the live
interviewer to a terminal report and asking :func:`interview_converged` whether
it believed it had enough information within the 20-question cap. This module
owns the *statistics* of that measurement so the assertion gate
(``test_eval_live.test_live_interview_converges``) and the report-number producer
(``shadow_run.measure_provider``) stay in lock-step on one definition.

It exists to fix **gap #1c** (live convergence-gate fragility, Session 168): the
two call sites used to run each fixture exactly *once* and ``pass_rate`` over the
4 booleans against a 95% bar — which mathematically requires 4/4, so a single
stochastic or transient miss dropped the gate to 75%. Two robustness fixes, the
95% threshold left untouched (this is a harness-statistics fix, **not** a #129
loosening):

* **Sample each converging case ``N_SAMPLES`` (>=5) times** and pool the results,
  matching the governance live test's existing N>=5 discipline (the design the
  module docstring of ``test_eval_live`` documents for "each governed case").
  One transient miss is then 1/20, not 1/4.
* **Disambiguate a transient LLM/seam/transport error from a genuine
  non-convergence.** A once-off truncated/empty/malformed response from the
  intake client (``IntakeLLMError``) or the stakeholder simulator
  (``StakeholderSimError``), or a network transport error from the Anthropic SDK
  (``APITimeoutError``/``APIConnectionError``, raised only *after* the SDK
  exhausts its own retries), is an API/seam/transport artifact — not the model
  declining to converge. It is retried a bounded number of times and, if still
  failing, **excluded** from the sample with a logged note rather than scored as
  a non-convergence. (A transient classifier is only complete if it covers BOTH
  application/seam errors AND transport errors: classifying the former but not
  the latter leaves a hole exactly where networks fail — a live gate run aborted
  on a raw ``APITimeoutError`` that propagated past this tuple; gap #1c residual,
  Session 171.) A *genuine* non-convergence is a returned report carrying
  ``"questions_cap_reached"`` (the intake graph self-terminates at the cap with a
  report — it does not raise), so it is scored ``False`` normally. Any *other*
  error — a non-transport ``APIStatusError`` (4xx/5xx: bad model id, auth, rate
  limit), or a non-seam ``RuntimeError`` (an unknown interrupt, a starved review
  script, the buggy-graph max-turns backstop) — is a real API/harness/graph bug
  and is left to propagate loudly; silently scoring it ``False`` is exactly what
  hid harness defects as model misses.

The sweep itself calls **no LLM**: it receives a ``run_one`` callable that
performs one live interview, so the sampling + classification logic is
deterministically unit-testable with a fake runner (``test_interview_sweep``),
mirroring how ``eval_scoring`` keeps scoring testable without an API key.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass

from anthropic import APIConnectionError, APITimeoutError

from model_project_constructor.agents.intake.protocol import IntakeLLMError
from model_project_constructor.schemas.v1.intake import IntakeReport
from tests.eval.eval_corpus import InterviewCase
from tests.eval.eval_scoring import interview_converged, premature_convergence
from tests.eval.stakeholder_sim import StakeholderSimError

#: Samples per governed interview case — §3.4 requires N>=5 to judge a pass-rate
#: (the same budget the governance live test uses). Single-sourced here so the
#: live assertion gate and the shadow-run measurement share one value.
N_SAMPLES = 5

#: Bounded retries for a *transient* per-sample failure before the sample is
#: excluded (with a logged note) rather than scored as a non-convergence.
_MAX_TRANSIENT_RETRIES = 2

#: Errors that are an LLM-call/seam/transport artifact, NOT the interviewed model
#: declining to converge. Two families: (1) application/seam errors
#: (``IntakeLLMError``, ``StakeholderSimError`` — both subclass ``RuntimeError``)
#: from a truncated/empty/malformed response or an empty simulated answer; and
#: (2) transport errors (``APITimeoutError`` is a subclass of
#: ``APIConnectionError``) raised by the Anthropic SDK after it exhausts its own
#: retries — a network blip (DNS, dropped connection, SSL-handshake timeout)
#: during a ~90-min live sweep, not a model miss. ``APIStatusError`` (4xx/5xx —
#: bad model id, auth, rate limit) is a *sibling* of ``APIConnectionError``, NOT
#: a subclass, so it is deliberately NOT caught here: a real API error still
#: surfaces loudly (FM #18). Everything else that raises is a genuine harness/
#: graph bug and must propagate (see the module docstring).
_TRANSIENT_ERRORS: tuple[type[Exception], ...] = (
    IntakeLLMError,
    StakeholderSimError,
    APITimeoutError,
    APIConnectionError,
)

#: Runs one live interview for a case to its terminal report. Injected so the
#: sweep's statistics are testable without an API key.
RunOne = Callable[[InterviewCase], IntakeReport]
#: Sink for a one-line progress/diagnostic note (e.g. ``shadow_run._warn``).
OnEvent = Callable[[str], None]


@dataclass(frozen=True)
class InterviewSweepResult:
    """Outcome of sweeping the interview corpus ``n_samples`` times per case.

    ``convergence_results`` is the pooled per-sample pass/fail list (feed it to
    ``pass_rate`` against ``INTERVIEW_CONVERGENCE_MIN``); ``premature_count`` is
    the §3.4 premature-convergence count; ``excluded_transient`` is how many
    samples were dropped after exhausting transient retries (logged, not scored).
    """

    convergence_results: list[bool]
    premature_count: int
    excluded_transient: int


def sweep_interview_convergence(
    cases: Iterable[InterviewCase],
    run_one: RunOne,
    *,
    n_samples: int = N_SAMPLES,
    max_transient_retries: int = _MAX_TRANSIENT_RETRIES,
    on_event: OnEvent | None = None,
) -> InterviewSweepResult:
    """Sample each ``expect_complete`` interview case ``n_samples`` times.

    Non-``expect_complete`` cases (the question-cap golden) are skipped — they
    are expected to terminate ``DRAFT_INCOMPLETE`` at the cap, not converge.
    Returns the pooled results; the caller asserts/records the pass-rate. A
    non-transient error from ``run_one`` propagates (a real bug must not be
    masked as a miss); a transient one is retried then excluded with a note.
    """
    notify = on_event or (lambda _msg: None)
    results: list[bool] = []
    premature = 0
    excluded = 0

    for case in cases:
        if not case.expect_complete:
            continue
        for _ in range(n_samples):
            report = _run_one_sample(
                case, run_one, max_transient_retries=max_transient_retries, notify=notify
            )
            if report is None:
                excluded += 1
                continue
            results.append(interview_converged(report))
            premature += int(premature_convergence(report))

    return InterviewSweepResult(
        convergence_results=results,
        premature_count=premature,
        excluded_transient=excluded,
    )


def _run_one_sample(
    case: InterviewCase,
    run_one: RunOne,
    *,
    max_transient_retries: int,
    notify: OnEvent,
) -> IntakeReport | None:
    """Run one interview sample, retrying a *transient* failure up to the bound.

    Returns the report, or ``None`` when every attempt hit a transient error (the
    sample is then excluded with a logged note). A non-transient error is **not**
    caught here — it propagates so a genuine harness/graph bug surfaces loudly.
    """
    attempts = max_transient_retries + 1
    last_exc: Exception | None = None
    for attempt in range(attempts):
        try:
            return run_one(case)
        except _TRANSIENT_ERRORS as exc:
            last_exc = exc
            notify(
                f"interview/{case.case_id}: transient {type(exc).__name__} "
                f"(attempt {attempt + 1}/{attempts})"
            )
    notify(
        f"interview/{case.case_id}: excluded after {attempts} transient "
        f"failures (last: {type(last_exc).__name__})"
    )
    return None
