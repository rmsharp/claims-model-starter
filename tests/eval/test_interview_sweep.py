"""Deterministic tests for the interview-convergence sweep (gap #1c).

The live tier exercises :func:`sweep_interview_convergence` against a real
provider; here we prove its *statistics* — N-sampling, the transient-vs-genuine
error classification, retry/exclude, and premature counting — with a fake
``run_one`` and no API key, mirroring how ``test_eval_scoring`` pins the scorers.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest

from model_project_constructor.agents.intake.protocol import IntakeLLMError
from model_project_constructor.schemas.v1.intake import IntakeReport
from tests.eval.eval_corpus import InterviewCase
from tests.eval.interview_sweep import (
    N_SAMPLES,
    InterviewSweepResult,
    sweep_interview_convergence,
)
from tests.eval.stakeholder_sim import StakeholderSimError
from tests.schemas.fixtures import make_intake_report

# --- report fixtures --------------------------------------------------------

#: A converged report: no "questions_cap_reached" marker, enough questions asked.
CONVERGED: IntakeReport = make_intake_report(missing_fields=[], questions_asked=9)
#: A genuine non-convergence: the graph hit the cap without believing it had
#: enough — the marker is present (the agent *returns* this, it does not raise).
NOT_CONVERGED: IntakeReport = make_intake_report(
    status="DRAFT_INCOMPLETE", missing_fields=["questions_cap_reached"], questions_asked=20
)
#: Converged, but suspiciously early (< the premature floor of 2 questions).
PREMATURE: IntakeReport = make_intake_report(missing_fields=[], questions_asked=1)


def _case(case_id: str, *, expect: bool = True) -> InterviewCase:
    # fixture_path is never loaded — run_one is faked.
    return InterviewCase(case_id=case_id, fixture_path=Path("/unused"), expect_complete=expect)


def _always(report: IntakeReport) -> Callable[[], IntakeReport]:
    def behavior() -> IntakeReport:
        return report

    return behavior


def _always_raise(exc: Callable[[], Exception]) -> Callable[[], IntakeReport]:
    def behavior() -> IntakeReport:
        raise exc()

    return behavior


def _raise_then(
    exc: Callable[[], Exception], report: IntakeReport, *, times: int
) -> Callable[[], IntakeReport]:
    state = {"n": 0}

    def behavior() -> IntakeReport:
        if state["n"] < times:
            state["n"] += 1
            raise exc()
        return report

    return behavior


class _Runner:
    """A fake ``run_one`` whose outcome depends only on the case id."""

    def __init__(self, behaviors: dict[str, Callable[[], IntakeReport]]) -> None:
        self._behaviors = behaviors
        self.calls: list[str] = []

    def __call__(self, case: InterviewCase) -> IntakeReport:
        self.calls.append(case.case_id)
        return self._behaviors[case.case_id]()


def _sweep(
    behaviors: dict[str, Callable[[], IntakeReport]],
    cases: list[InterviewCase],
    **kw: object,
) -> tuple[InterviewSweepResult, _Runner]:
    runner = _Runner(behaviors)
    result = sweep_interview_convergence(cases, runner, **kw)  # type: ignore[arg-type]
    return result, runner


# --- sampling ---------------------------------------------------------------


def test_default_samples_each_case_n_times() -> None:
    result, runner = _sweep({"a": _always(CONVERGED)}, [_case("a")])
    assert len(result.convergence_results) == N_SAMPLES
    assert runner.calls == ["a"] * N_SAMPLES
    assert result.convergence_results == [True] * N_SAMPLES
    assert result.excluded_transient == 0
    assert result.premature_count == 0


def test_pools_all_cases_into_one_result_list() -> None:
    behaviors = {"a": _always(CONVERGED), "b": _always(CONVERGED)}
    result, _ = _sweep(behaviors, [_case("a"), _case("b")], n_samples=3)
    assert len(result.convergence_results) == 6
    assert all(result.convergence_results)


def test_non_expect_complete_cases_are_skipped() -> None:
    behaviors = {"a": _always(CONVERGED), "cap": _always(NOT_CONVERGED)}
    result, runner = _sweep(
        behaviors, [_case("a"), _case("cap", expect=False)], n_samples=2
    )
    assert runner.calls == ["a", "a"]  # the question-cap golden never runs
    assert len(result.convergence_results) == 2


# --- genuine non-convergence (a returned report, not an exception) ----------


def test_genuine_non_convergence_scored_false_not_excluded() -> None:
    result, _ = _sweep({"a": _always(NOT_CONVERGED)}, [_case("a")], n_samples=4)
    assert result.convergence_results == [False] * 4
    assert result.excluded_transient == 0  # a real miss is counted, not dropped


def test_premature_convergence_counted() -> None:
    result, _ = _sweep({"a": _always(PREMATURE)}, [_case("a")], n_samples=3)
    assert result.convergence_results == [True] * 3  # premature is still converged
    assert result.premature_count == 3


# --- transient errors: retried, then excluded (not scored False) ------------


def test_transient_intake_error_retried_then_recovers() -> None:
    # raises once, then returns a converged report → recovered within the bound.
    behaviors = {"a": _raise_then(lambda: IntakeLLMError("blip"), CONVERGED, times=1)}
    result, runner = _sweep(behaviors, [_case("a")], n_samples=1, max_transient_retries=2)
    assert result.convergence_results == [True]
    assert result.excluded_transient == 0
    assert runner.calls == ["a", "a"]  # one failed attempt + one success


def test_persistent_transient_intake_error_excluded() -> None:
    behaviors = {"a": _always_raise(lambda: IntakeLLMError("down"))}
    result, runner = _sweep(behaviors, [_case("a")], n_samples=2, max_transient_retries=1)
    assert result.convergence_results == []  # nothing scored
    assert result.excluded_transient == 2  # both samples dropped
    assert runner.calls == ["a"] * 4  # 2 samples × (1 try + 1 retry)


def test_stakeholder_sim_error_is_transient() -> None:
    behaviors = {"a": _always_raise(lambda: StakeholderSimError("empty"))}
    result, _ = _sweep(behaviors, [_case("a")], n_samples=2, max_transient_retries=0)
    assert result.convergence_results == []
    assert result.excluded_transient == 2


def test_transient_on_one_case_does_not_poison_another() -> None:
    behaviors = {
        "flaky": _always_raise(lambda: IntakeLLMError("down")),
        "ok": _always(CONVERGED),
    }
    result, _ = _sweep(
        behaviors, [_case("flaky"), _case("ok")], n_samples=2, max_transient_retries=0
    )
    assert result.convergence_results == [True, True]  # only "ok" contributes
    assert result.excluded_transient == 2


def test_on_event_receives_transient_notes() -> None:
    notes: list[str] = []
    behaviors = {"a": _always_raise(lambda: IntakeLLMError("x"))}
    _sweep(
        behaviors,
        [_case("a")],
        n_samples=1,
        max_transient_retries=0,
        on_event=notes.append,
    )
    assert any("transient" in n for n in notes)
    assert any("excluded" in n for n in notes)


# --- a genuine harness/graph bug propagates (must not be masked as a miss) ---


def test_non_transient_runtime_error_propagates() -> None:
    # e.g. an "Unknown interrupt kind" / max-turns backstop from the agent seam.
    behaviors = {"a": _always_raise(lambda: RuntimeError("Unknown interrupt kind"))}
    with pytest.raises(RuntimeError, match="Unknown interrupt"):
        _sweep(behaviors, [_case("a")], n_samples=1)


def test_non_runtime_exception_propagates() -> None:
    behaviors = {"a": _always_raise(lambda: ValueError("boom"))}
    with pytest.raises(ValueError, match="boom"):
        _sweep(behaviors, [_case("a")], n_samples=1)
