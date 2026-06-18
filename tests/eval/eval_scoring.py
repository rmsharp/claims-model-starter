"""Phase B eval scorers (multi-provider LLM plan §3.4).

Pure, deterministic functions that turn a provider's output into the capability
metrics the §3.4 gate is defined over. They are provider-agnostic: the
deterministic tier feeds them reference/perturbed data to prove they MEASURE
correctly with no API key; the ``live`` tier feeds them a real provider's output.

Nothing here calls an LLM or asserts a threshold — scoring and gating are kept
separate so the same scorer serves both tiers.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from model_project_constructor_data_agent.db import ReadOnlyDB
from model_project_constructor_data_agent.sql_validation import validate_sql

from model_project_constructor.agents.intake.protocol import GovernanceClassification
from model_project_constructor.schemas.v1.intake import IntakeReport
from tests.eval.eval_thresholds import RISK_TIER_STRICTNESS


@dataclass(frozen=True)
class GovernanceScore:
    """Field-by-field agreement of a predicted governance label vs reference."""

    case_id: str
    cycle_time_match: bool
    risk_tier_match: bool
    frameworks_match: bool
    affects_consumers_match: bool
    protected_match: bool
    exact_label_match: bool  # both closed-vocab labels (cycle_time AND risk_tier)
    laxer_tier_miss: bool  # predicted risk_tier strictly laxer than reference
    field_agreement: float  # fraction of the 5 compared fields that match


def is_laxer_tier(reference: str, predicted: str) -> bool:
    """True iff ``predicted`` is a strictly laxer risk tier than ``reference``."""
    return RISK_TIER_STRICTNESS[predicted] > RISK_TIER_STRICTNESS[reference]


def score_governance(
    case_id: str,
    reference: GovernanceClassification,
    predicted: GovernanceClassification,
) -> GovernanceScore:
    """Score one predicted governance label against its reference."""
    cycle = reference.cycle_time == predicted.cycle_time
    tier = reference.risk_tier == predicted.risk_tier
    frameworks = set(reference.regulatory_frameworks) == set(predicted.regulatory_frameworks)
    consumers = reference.affects_consumers == predicted.affects_consumers
    protected = reference.uses_protected_attributes == predicted.uses_protected_attributes
    fields = [cycle, tier, frameworks, consumers, protected]
    return GovernanceScore(
        case_id=case_id,
        cycle_time_match=cycle,
        risk_tier_match=tier,
        frameworks_match=frameworks,
        affects_consumers_match=consumers,
        protected_match=protected,
        exact_label_match=cycle and tier,
        laxer_tier_miss=is_laxer_tier(reference.risk_tier, predicted.risk_tier),
        field_agreement=sum(fields) / len(fields),
    )


def sql_parse_valid(sql: str) -> bool:
    """Whether ``sql`` passes the data agent's parse-level validator."""
    ok, _ = validate_sql(sql)
    return ok


def sql_executes(db: ReadOnlyDB, sql: str) -> bool:
    """Whether ``sql`` executes against the seeded DB without raising."""
    try:
        db.execute(sql)
    except Exception:
        # Any DB-level error (bad column, type mismatch, dialect) = not executable.
        return False
    return True


def quality_checks_structural_ok(n_primary_queries: int, qc_lists: Sequence[Any]) -> bool:
    """The §3.4 hard structural contract: one QC list per primary query."""
    return len(qc_lists) == n_primary_queries


def interview_converged(report: IntakeReport) -> bool:
    """Whether an interview converged within the question cap (§3.4 metric).

    The §3.4 intake metric is "``believe_enough_info`` within the 20-question
    cap" — convergence is the model judging it had enough information *before*
    the cap, NOT the report reaching a fully-finalized ``COMPLETE`` status.
    ``finalize`` appends ``"questions_cap_reached"`` to ``missing_fields`` iff
    the cap was hit *without* ``believe_enough_info`` (see intake ``nodes.py``),
    so its absence is exactly "believed enough within the cap". Report
    finalization (review accepted + zero missing fields) is a *separate*
    concern: gating this capability metric on ``status == "COMPLETE"`` measured
    report completeness, not interview convergence — the scorer was stricter
    than its own §3.4 metric text (gap #1b). See :func:`premature_convergence`
    for the same-signal early-convergence guard.
    """
    return "questions_cap_reached" not in report.missing_fields


def premature_convergence(report: IntakeReport, min_questions: int = 2) -> bool:
    """Whether an interview converged suspiciously early.

    The §3.4 interview metric requires "0 premature convergence". We flag an
    interview that converged (``believe_enough_info`` within the cap — i.e.
    ``"questions_cap_reached"`` absent, the *same* signal
    :func:`interview_converged` uses) after fewer than ``min_questions``
    answered questions: it claimed enough information before gathering a
    plausible minimum. Keying this guard on the convergence signal rather than
    ``status == "COMPLETE"`` is what keeps it honest — otherwise an interview
    could converge at q=1 yet never finalize and slip past the premature check.
    (A heuristic floor; the live tier may tune it against the measured baseline.)
    """
    return (
        "questions_cap_reached" not in report.missing_fields
        and report.questions_asked < min_questions
    )


@dataclass(frozen=True)
class CapabilityRate:
    """Pass count over a capability's corpus, with a threshold check."""

    capability: str
    passed: int
    total: int

    @property
    def rate(self) -> float:
        return self.passed / self.total if self.total else 0.0

    def meets(self, threshold: float) -> bool:
        return self.rate >= threshold


def pass_rate(capability: str, results: Sequence[bool]) -> CapabilityRate:
    """Aggregate a list of per-case pass/fail booleans into a CapabilityRate."""
    return CapabilityRate(capability, sum(1 for r in results if r), len(results))
