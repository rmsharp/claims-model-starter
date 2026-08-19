"""Deterministic tests for the governance-agreement sweep's *statistics*.

Mirrors ``test_sql_sweep`` and ``test_interview_sweep``: a fake classifier stands
in for the live client, so the sampling, pooling and failure-classification logic
is exercised with zero API calls.

The load-bearing assertions are the ones the two pre-sweep call sites disagreed
about (Session 225):

* each case is sampled ``n_samples`` times and pooled — the discipline
  ``shadow_run`` and ``test_eval_live`` both already had, now single-sourced;
* a transient is retried up to the bound and, on recovery, costs nothing —
  ``shadow_run`` scored the first blip immediately and ``test_eval_live`` died
  on it;
* an exhausted ``IntakeLLMError`` is **scored** a non-agreement, so the pooled
  denominator never shrinks;
* an exhausted ``IntakeLLMError`` does **not** fabricate a laxer-tier miss —
  the zero-tolerance ``GOVERNANCE_LAXER_MISSES_MAX = 0`` bar must never be fed
  by a seam failure, which is the Session 219 shape that cost a cutover verdict;
* an exhausted **transport** error is **excluded** and counted, because no model
  output exists to judge and ``classify_governance``'s seam does not wrap SDK
  transport errors at all (``anthropic_client._call_json`` calls
  ``messages.create`` bare) — before this module one such error aborted the whole
  ~2.5-hour shadow run;
* a non-transient still propagates on the first attempt, unretried;
* every counter reaches the summary line, and every note carries ``str(exc)``.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import anthropic
import httpx
import pytest

from model_project_constructor.agents.intake.protocol import (
    DraftReportResult,
    GovernanceClassification,
    IntakeLLMError,
)
from tests.eval.eval_corpus import GovernanceCase, load_governance_cases
from tests.eval.eval_scoring import pass_rate
from tests.eval.eval_thresholds import GOVERNANCE_CYCLE_TIME_AGREEMENT_MIN
from tests.eval.governance_sweep import (
    GovernanceSweepResult,
    governance_sweep_summary,
    sweep_governance_agreement,
)
from tests.eval.interview_sweep import N_SAMPLES


def _draft(marker: str) -> DraftReportResult:
    return DraftReportResult(
        business_problem=marker,
        proposed_solution="s",
        model_solution={},
        estimated_value={},
    )


def _classification(
    *, cycle_time: str = "tactical", risk_tier: str = "tier_2_high"
) -> GovernanceClassification:
    return GovernanceClassification(
        cycle_time=cycle_time,
        cycle_time_rationale="",
        risk_tier=risk_tier,
        risk_tier_rationale="",
        regulatory_frameworks=[],
        affects_consumers=False,
        uses_protected_attributes=False,
    )


def _case(
    case_id: str = "c1", *, cycle_time: str = "tactical", risk_tier: str = "tier_2_high"
) -> GovernanceCase:
    """One authored case whose reference is exactly ``_classification()``'s default."""
    return GovernanceCase(
        case_id=case_id,
        draft=_draft(case_id),
        reference=_classification(cycle_time=cycle_time, risk_tier=risk_tier),
        provenance="authored for eval",
    )


# Constructed with a throwaway httpx request so the deterministic suite needs no
# API key — the same pattern ``test_sql_sweep`` uses. ``APITimeoutError`` is a
# subclass of ``APIConnectionError``.
def _req() -> httpx.Request:
    return httpx.Request("POST", "https://api.anthropic.com/v1/messages")


def _timeout() -> anthropic.APITimeoutError:
    return anthropic.APITimeoutError(request=_req())


def _conn_error() -> anthropic.APIConnectionError:
    return anthropic.APIConnectionError(message="dropped", request=_req())


@dataclass
class _FakeClassifier:
    """A ``classify_governance``-shaped double recording every call it receives.

    ``error_times`` bounds how many *calls* raise: ``None`` means every call,
    ``1`` means only the first (so the retry recovers), ``0`` means none.
    ``error_sequence`` is the per-call form, needed to mix transient classes
    within one sample: entry *i* is raised on call *i*, ``None`` succeeds, and
    running off the end succeeds.
    """

    predicted: GovernanceClassification | None = None
    error: Exception | None = None
    error_times: int | None = None
    error_sequence: list[Exception | None] | None = None
    calls: list[str] = field(default_factory=list)

    def __call__(self, draft: DraftReportResult) -> GovernanceClassification:
        self.calls.append(draft.business_problem)
        if self.error_sequence is not None:
            idx = len(self.calls) - 1
            if idx < len(self.error_sequence):
                queued = self.error_sequence[idx]
                if queued is not None:
                    raise queued
        if self.error is not None and (
            self.error_times is None or len(self.calls) <= self.error_times
        ):
            raise self.error
        return self.predicted if self.predicted is not None else _classification()


# --- sampling -------------------------------------------------------------


def test_each_case_is_sampled_n_times() -> None:
    """The real corpus, sampled — 5 cases x N samples, pooled into one rate."""
    cases = load_governance_cases()
    classifier = _FakeClassifier()

    result = sweep_governance_agreement(cases, classifier, n_samples=5)

    assert len(classifier.calls) == len(cases) * 5
    assert len(result.cycle_matches) == len(cases) * 5


def test_n_samples_is_honoured_per_case() -> None:
    cases = [_case("a"), _case("b")]
    classifier = _FakeClassifier()

    sweep_governance_agreement(cases, classifier, n_samples=3)

    assert classifier.calls == ["a", "a", "a", "b", "b", "b"]


def test_a_matching_prediction_scores_agreement_and_no_laxer_miss() -> None:
    result = sweep_governance_agreement([_case()], _FakeClassifier(), n_samples=2)

    assert result.cycle_matches == [True, True]
    assert result.risk_acceptable == [True, True]
    assert result.laxer_misses == 0
    assert result.seam_failures == 0
    assert result.excluded_transient == 0


def test_a_disagreeing_cycle_time_scores_a_miss() -> None:
    classifier = _FakeClassifier(predicted=_classification(cycle_time="operational"))

    result = sweep_governance_agreement([_case()], classifier, n_samples=2)

    assert result.cycle_matches == [False, False]
    # risk_tier still agrees, so the diagnostic and the zero-tolerance count hold.
    assert result.risk_acceptable == [True, True]
    assert result.laxer_misses == 0


def test_a_laxer_tier_prediction_is_counted() -> None:
    """tier_3_moderate against a tier_2_high reference is strictly laxer."""
    classifier = _FakeClassifier(predicted=_classification(risk_tier="tier_3_moderate"))

    result = sweep_governance_agreement([_case()], classifier, n_samples=2)

    assert result.laxer_misses == 2
    assert result.risk_acceptable == [False, False]


def test_a_stricter_tier_prediction_is_not_a_miss() -> None:
    """The prompt instructs "pick the stricter tier if in doubt" (S173)."""
    classifier = _FakeClassifier(predicted=_classification(risk_tier="tier_1_critical"))

    result = sweep_governance_agreement([_case()], classifier, n_samples=2)

    assert result.laxer_misses == 0
    assert result.risk_acceptable == [True, True]


# --- transient policy -----------------------------------------------------


@pytest.mark.parametrize("exc_factory", [lambda: IntakeLLMError("blip"), _timeout, _conn_error])
def test_a_recovered_transient_costs_nothing(exc_factory: object) -> None:
    """One blip, then success: scored clean, with the retry visible."""
    classifier = _FakeClassifier(error=exc_factory(), error_times=1)  # type: ignore[operator]
    notes: list[str] = []

    result = sweep_governance_agreement(
        [_case()], classifier, n_samples=1, on_event=notes.append
    )

    assert result.cycle_matches == [True]
    assert result.seam_failures == 0
    assert result.excluded_transient == 0
    assert result.transient_retries == 1
    assert len(classifier.calls) == 2
    assert any("retrying" in note for note in notes)


def test_an_exhausted_seam_error_is_scored_not_excluded() -> None:
    """The denominator must not shrink — see the module docstring's argument."""
    classifier = _FakeClassifier(error=IntakeLLMError("unparseable"))
    notes: list[str] = []

    result = sweep_governance_agreement(
        [_case()], classifier, n_samples=2, on_event=notes.append
    )

    assert result.cycle_matches == [False, False]
    assert result.risk_acceptable == [False, False]
    assert result.seam_failures == 2
    assert result.excluded_transient == 0
    # 2 samples x (1 attempt + 2 retries)
    assert len(classifier.calls) == 6
    assert result.transient_retries == 4
    assert any("non-agreement" in note for note in notes)


def test_an_exhausted_seam_error_does_not_fabricate_a_laxer_miss() -> None:
    """The zero-tolerance bar must never be fed by a seam failure (S219).

    A sample that produced no classification produced no *tier*, so counting it
    a laxer miss would convert one blip into a NO-GO on a bar whose maximum is 0
    — precisely the pathology this whole item exists to remove.
    """
    classifier = _FakeClassifier(error=IntakeLLMError("unparseable"))

    result = sweep_governance_agreement([_case()], classifier, n_samples=5)

    assert result.seam_failures == 5
    assert result.laxer_misses == 0


def test_an_exhausted_transport_error_is_excluded_not_scored() -> None:
    """No model output exists to judge, so scoring one would measure the network."""
    classifier = _FakeClassifier(error=_timeout())
    notes: list[str] = []

    result = sweep_governance_agreement(
        [_case()], classifier, n_samples=2, on_event=notes.append
    )

    assert result.cycle_matches == []
    assert result.risk_acceptable == []
    assert result.seam_failures == 0
    assert result.excluded_transient == 2
    assert result.laxer_misses == 0
    assert any("excluded" in note for note in notes)


def test_a_scored_failure_wins_over_an_exclusion_within_one_sample() -> None:
    """Mixed evidence is scored, never excluded (the ``sql_sweep`` rule).

    A sample that raised ``IntakeLLMError`` and then timed out has *produced
    judgeable output*, so excluding it would drop a real model-quality
    observation from the denominator.
    """
    classifier = _FakeClassifier(
        error_sequence=[IntakeLLMError("bad json"), _timeout(), _timeout()]
    )

    result = sweep_governance_agreement([_case()], classifier, n_samples=1)

    assert result.seam_failures == 1
    assert result.excluded_transient == 0
    assert result.cycle_matches == [False]


def test_a_scored_failure_wins_in_either_order() -> None:
    """The scored class landing *last* must win too, not just landing first.

    ``scored_exc`` is kept separate from ``last_exc`` precisely so a mixed
    sequence names the failure being scored rather than whichever error happened
    to land last. With the scored error in the middle, reading only the last
    attempt would excluded this sample instead of scoring it.
    """
    classifier = _FakeClassifier(
        error_sequence=[_timeout(), IntakeLLMError("bad json"), _timeout()]
    )
    notes: list[str] = []

    result = sweep_governance_agreement(
        [_case()], classifier, n_samples=1, on_event=notes.append
    )

    assert result.seam_failures == 1
    assert result.excluded_transient == 0
    assert result.cycle_matches == [False]
    # The terminal note names the scored exception, not the timeout that landed last.
    terminal = notes[-1]
    assert "IntakeLLMError" in terminal
    assert "bad json" in terminal
    assert "non-agreement" in terminal


def test_the_exclusion_path_spends_and_reports_its_retries() -> None:
    """``transient_retries`` was asserted on the scored and recovered paths only."""
    classifier = _FakeClassifier(error=_timeout())

    result = sweep_governance_agreement([_case()], classifier, n_samples=2)

    assert result.excluded_transient == 2
    # 2 samples x 2 retries each, and 2 x 3 attempts spent.
    assert result.transient_retries == 4
    assert len(classifier.calls) == 6


def test_the_default_sample_count_is_the_shared_n_samples() -> None:
    """The live gate passes no ``n_samples``, so this default *is* its denominator.

    ``N_SAMPLES`` is single-sourced in ``interview_sweep`` and is the §3.4 N>=5
    floor; pinning it here means a change to that constant cannot silently move
    the governance gate's sample size.
    """
    classifier = _FakeClassifier()

    result = sweep_governance_agreement([_case()], classifier)

    assert N_SAMPLES >= 5
    assert len(classifier.calls) == N_SAMPLES
    assert len(result.cycle_matches) == N_SAMPLES


def test_a_non_transient_propagates_unretried() -> None:
    """A real harness bug must surface loudly, not be laundered into a rate."""
    classifier = _FakeClassifier(error=ValueError("harness bug"))

    with pytest.raises(ValueError, match="harness bug"):
        sweep_governance_agreement([_case()], classifier, n_samples=3)

    assert len(classifier.calls) == 1


def test_an_api_status_error_is_not_treated_as_transient() -> None:
    """``APIStatusError`` (4xx/5xx) is a *sibling* of ``APIConnectionError``.

    Auth failures, bad model ids and rate limits must abort, not be retried into
    a measured miss (FM #18) — the same rule both sibling sweeps apply.
    """
    status = anthropic.APIStatusError(
        "bad request",
        response=httpx.Response(400, request=_req()),
        body=None,
    )
    classifier = _FakeClassifier(error=status)

    with pytest.raises(anthropic.APIStatusError):
        sweep_governance_agreement([_case()], classifier, n_samples=3)

    assert len(classifier.calls) == 1


# --- invariants and reporting ---------------------------------------------


def test_the_two_per_sample_lists_stay_the_same_length() -> None:
    """``cycle_matches`` and ``risk_acceptable`` are both per-sample.

    They diverge from ``laxer_misses`` on a seam failure by design (see the
    module docstring), but never from each other. The sequence below **exhausts**
    the first sample (three consecutive seam errors) so the divergence is
    actually exercised: without a scored exhaustion in the run this test would
    pass on the clean path alone and prove nothing.
    """
    classifier = _FakeClassifier(
        error_sequence=[IntakeLLMError("x"), IntakeLLMError("x"), IntakeLLMError("x")]
    )

    result = sweep_governance_agreement([_case("a"), _case("b")], classifier, n_samples=2)

    assert result.seam_failures == 1
    assert len(result.cycle_matches) == len(result.risk_acceptable) == 4
    # The divergence itself: one sample is False in the diagnostic list while the
    # gated zero-tolerance count stays clean.
    assert result.risk_acceptable.count(False) == 1
    assert result.laxer_misses == 0


def test_total_exclusion_scores_zero_not_one() -> None:
    """An all-excluded sweep fails its bar rather than passing vacuously.

    ``CapabilityRate.rate`` is ``0.0`` when ``total`` is 0, so a provider whose
    every governance call timed out cannot clear the 0.90 gate on an empty
    denominator.
    """
    classifier = _FakeClassifier(error=_conn_error())

    result = sweep_governance_agreement([_case()], classifier, n_samples=3)

    rate = pass_rate("governance_cycle_time", result.cycle_matches)
    assert result.excluded_transient == 3
    assert not rate.meets(GOVERNANCE_CYCLE_TIME_AGREEMENT_MIN)


def test_summary_carries_every_counter_with_its_value() -> None:
    """Labels alone are not enough — a swapped or inverted value must fail here.

    Constructing the result directly (rather than running a sweep) does double
    duty: it is the tripwire proving every field added after the two lists still
    carries a default, which is what keeps this two-argument construction valid.
    """
    # The two fractions are deliberately DIFFERENT (2/3 vs 3/4). Giving them the
    # same value would make a swap of the two invisible — which is the exact
    # defect this test exists to catch, and which a mutation run caught here.
    # The unequal lengths are impossible for real sweep output and fine for a
    # directly-constructed result: this pins the formatter, not the invariant.
    result = GovernanceSweepResult(
        cycle_matches=[True, False, True],
        risk_acceptable=[True, True, True, False],
        laxer_misses=1,
        seam_failures=2,
        transient_retries=3,
        excluded_transient=4,
    )

    line = governance_sweep_summary(result)

    assert "governance_cycle_time 2/3" in line
    assert "risk_tier_acceptable 3/4" in line
    assert "laxer_misses 1" in line
    assert "seam_failures 2" in line
    assert "transient_retries 3" in line
    assert "excluded_transient 4" in line


def test_the_result_is_constructible_from_its_two_lists_alone() -> None:
    """Every counter carries a default; adding a required field would break this."""
    result = GovernanceSweepResult(cycle_matches=[True], risk_acceptable=[True])

    assert (result.laxer_misses, result.seam_failures) == (0, 0)
    assert (result.transient_retries, result.excluded_transient) == (0, 0)


def test_every_note_carries_the_exception_text_not_just_the_type() -> None:
    """Session 219's verdict-deciding event was unattributable without this.

    ``all``, not ``any``: the helper emits three distinct note kinds (retry,
    scored exhaustion, exclusion) and the docstring's rule is stated over every
    one of them. An ``any`` here would be satisfied by the terminal note alone
    and would not notice a retry note that dropped its message.
    """
    classifier = _FakeClassifier(error=IntakeLLMError("missing key 'risk_tier'"))
    notes: list[str] = []

    result = sweep_governance_agreement(
        [_case()], classifier, n_samples=1, on_event=notes.append
    )

    assert result.seam_failures == 1
    # 2 retry notes + 1 scored-exhaustion note, and every one names the message.
    assert len(notes) == 3
    assert all("missing key 'risk_tier'" in note for note in notes)


def test_the_exclusion_note_also_carries_the_exception_text() -> None:
    """The transport tier's terminal note is the other half of the same rule."""
    classifier = _FakeClassifier(error=_conn_error())
    notes: list[str] = []

    sweep_governance_agreement([_case()], classifier, n_samples=1, on_event=notes.append)

    excluded = [note for note in notes if "excluded" in note]
    assert len(excluded) == 1
    assert "dropped" in excluded[0]
    assert "APIConnectionError" in excluded[0]


def test_the_sweep_is_silent_without_an_event_sink() -> None:
    """``on_event`` defaults to a no-op, exactly as both sibling sweeps do."""
    classifier = _FakeClassifier(error=IntakeLLMError("bad"))

    result = sweep_governance_agreement([_case()], classifier, n_samples=1)

    assert result.seam_failures == 1
