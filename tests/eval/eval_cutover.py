"""Phase E — shadow-run cutover gate (multi-provider LLM plan §5 Phase E).

Pure, deterministic decision logic + a markdown renderer for the provider
cutover gate. Given the per-capability pass-rates a *shadow run* measures for
each provider (``pytest -m live`` over the Phase B corpus, one run per provider),
this module decides whether a candidate provider may replace the production
default and renders the agreement report.

It calls **no LLM and reads no key** — live measurement is the ``live`` tier's
job (``test_eval_live.py``); gating and rendering are kept separate from scoring
(mirroring ``eval_scoring``) so the gate is fully unit-tested offline. The §5
rule is the whole point: **production cutover only if the candidate meets EVERY
§3.4 threshold** — an unmet *or unmeasured* threshold keeps Anthropic primary.

**Status (Session 164): no live credentials → every measured cell is PENDING.**
The committed agreement report (``PHASE_E_AGREEMENT_REPORT.md``) is therefore a
no-go-by-default (keep Anthropic primary) until a shadow run fills the numbers;
see that file and ``README.md`` §"Phase E — shadow run + cutover gate".
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from tests.eval import eval_thresholds as thresholds

# --- Provider roles in the shadow run ---------------------------------------

#: The incumbent production default (orchestrator ``DEFAULT_LLM_PROVIDER``).
BASELINE_PROVIDER = "anthropic"
#: Providers evaluated as cutover candidates against the baseline.
CANDIDATE_PROVIDERS: tuple[str, ...] = ("bedrock",)
#: Every provider the shadow run measures, baseline first.
SHADOW_PROVIDERS: tuple[str, ...] = (BASELINE_PROVIDER, *CANDIDATE_PROVIDERS)


def provider_creds_available(provider: str) -> bool:
    """Best-effort, side-effect-free probe of whether ``provider`` is runnable.

    Used by the live-tier collection hook (``conftest``) to skip a provider's
    shadow run when its credentials are absent — so CI (no creds for any
    provider) skips the whole tier and stays hermetic, while a Bedrock-only
    environment can still run the Bedrock half. It deliberately does **not** walk
    boto3's full credential chain (no IMDS lookup at collection time, which would
    slow every ``-m 'not live'`` run); an operator whose creds arrive via a
    mechanism this misses can set ``AWS_PROFILE`` or run the module directly.
    """
    if provider == "anthropic":
        return bool(os.environ.get("ANTHROPIC_API_KEY"))
    if provider == "bedrock":
        return bool(
            os.environ.get("AWS_ACCESS_KEY_ID")
            or os.environ.get("AWS_PROFILE")
            or (Path.home() / ".aws" / "credentials").exists()
        )
    return False


# --- The §3.4 threshold gate ------------------------------------------------

#: ``"min"``: PASS iff measured ``>=`` threshold (rates). ``"max"``: PASS iff
#: measured ``<=`` threshold (the zero-tolerance counts).
Direction = Literal["min", "max"]
Status = Literal["PASS", "FAIL", "PENDING"]
Verdict = Literal["GO", "NO-GO", "PENDING"]


@dataclass(frozen=True)
class _CheckSpec:
    """One row of the §3.4 gate: a capability metric and its pass threshold."""

    key: str
    capability: str
    metric: str
    threshold: float
    direction: Direction


#: The §3.4 gate, one row per measurable threshold. Order = report row order.
#: Each threshold is sourced from :mod:`eval_thresholds` (single source of truth);
#: ``test_eval_cutover`` guards this registry against drift from that module.
_CHECK_SPECS: tuple[_CheckSpec, ...] = (
    _CheckSpec(
        "json_parse",
        "Any JSON method",
        "parse via both _extract_json copies (deterministic: test_llm_json_parity, not live tier)",
        thresholds.JSON_PARSE_MIN,
        "min",
    ),
    _CheckSpec(
        "sql_parse",
        "generate_primary_queries",
        "SQL parse-valid",
        thresholds.SQL_PARSE_VALID_MIN,
        "min",
    ),
    _CheckSpec(
        "sql_exec",
        "generate_primary_queries",
        "SQL executable on the seeded P&C schema",
        thresholds.SQL_EXECUTABLE_MIN,
        "min",
    ),
    _CheckSpec(
        "governance_cycle_time_agreement",
        "classify_governance",
        "cycle_time exact agreement vs reference",
        thresholds.GOVERNANCE_CYCLE_TIME_AGREEMENT_MIN,
        "min",
    ),
    _CheckSpec(
        "governance_laxer_miss",
        "classify_governance",
        "risk_tier laxer-tier misses (less strict than reference; stricter is allowed)",
        float(thresholds.GOVERNANCE_LAXER_MISSES_MAX),
        "max",
    ),
    _CheckSpec(
        "qc_structural",
        "generate_quality_checks",
        "outer array length == #primary queries",
        thresholds.QUALITY_CHECKS_STRUCTURAL_MIN,
        "min",
    ),
    _CheckSpec(
        "interview_convergence",
        "Intake interview",
        "believe_enough_info within the 20-question cap",
        thresholds.INTERVIEW_CONVERGENCE_MIN,
        "min",
    ),
    _CheckSpec(
        "interview_premature",
        "Intake interview",
        "premature convergences",
        float(thresholds.INTERVIEW_PREMATURE_MAX),
        "max",
    ),
)

#: The check keys, in report order — the contract a measurement mapping fills.
CHECK_KEYS: tuple[str, ...] = tuple(spec.key for spec in _CHECK_SPECS)


@dataclass(frozen=True)
class ThresholdCheck:
    """A single §3.4 threshold paired with one provider's measured value."""

    key: str
    capability: str
    metric: str
    threshold: float
    direction: Direction
    measured: float | None  # None = not measured this run (PENDING)

    @property
    def status(self) -> Status:
        if self.measured is None:
            return "PENDING"
        if self.direction == "min":
            return "PASS" if self.measured >= self.threshold else "FAIL"
        return "PASS" if self.measured <= self.threshold else "FAIL"

    @property
    def passed(self) -> bool | None:
        """``True``/``False`` once measured; ``None`` while PENDING."""
        return None if self.measured is None else self.status == "PASS"


@dataclass(frozen=True)
class CutoverDecision:
    """A provider's go/no-go against the full §3.4 gate."""

    provider: str
    checks: tuple[ThresholdCheck, ...]

    @property
    def failing(self) -> tuple[ThresholdCheck, ...]:
        return tuple(c for c in self.checks if c.status == "FAIL")

    @property
    def pending(self) -> tuple[ThresholdCheck, ...]:
        return tuple(c for c in self.checks if c.status == "PENDING")

    @property
    def decision(self) -> Verdict:
        """GO only if every threshold passed; a fail is NO-GO; else PENDING.

        The §5 rule — cutover only if the candidate meets *every* threshold —
        means an unmeasured threshold cannot certify GO: it resolves to PENDING,
        which the recommendation treats as "keep the baseline primary".
        """
        if self.failing:
            return "NO-GO"
        if self.pending:
            return "PENDING"
        return "GO"

    @property
    def recommendation(self) -> str:
        if self.decision == "GO":
            return f"Cut over: {self.provider} meets every §3.4 threshold."
        if self.decision == "NO-GO":
            failed = ", ".join(c.key for c in self.failing)
            return (
                f"Do NOT cut over — keep {BASELINE_PROVIDER} primary. "
                f"{self.provider} fails: {failed}."
            )
        unmeasured = ", ".join(c.key for c in self.pending)
        return (
            f"Undecided — keep {BASELINE_PROVIDER} primary until measured. "
            f"{self.provider} unmeasured: {unmeasured}."
        )


def evaluate_cutover(provider: str, measured: Mapping[str, float | None]) -> CutoverDecision:
    """Build a :class:`CutoverDecision` from a provider's measured pass-rates.

    ``measured`` maps a check key (:data:`CHECK_KEYS`) to its measured value; a
    missing key (or an explicit ``None``) is treated as PENDING (not measured).
    """
    checks = tuple(
        ThresholdCheck(
            key=spec.key,
            capability=spec.capability,
            metric=spec.metric,
            threshold=spec.threshold,
            direction=spec.direction,
            measured=measured.get(spec.key),
        )
        for spec in _CHECK_SPECS
    )
    return CutoverDecision(provider=provider, checks=checks)


def pending_decision(provider: str) -> CutoverDecision:
    """A cutover decision with every threshold PENDING (the no-creds state)."""
    return evaluate_cutover(provider, {})


# --- Agreement report renderer ----------------------------------------------


def _fmt_threshold(direction: Direction, threshold: float) -> str:
    op = "≥" if direction == "min" else "≤"
    # Rate minima render as percentages; the zero-tolerance maxima are counts.
    return f"{op} {threshold:g}" if direction == "max" else f"{op} {threshold:.0%}"


def _fmt_measured(check: ThresholdCheck) -> str:
    if check.measured is None:
        return "— (PENDING)"
    if check.direction == "max":
        return f"{check.measured:g} ({check.status})"
    return f"{check.measured:.1%} ({check.status})"


def render_agreement_report(
    decisions: Mapping[str, CutoverDecision],
    *,
    baseline: str = BASELINE_PROVIDER,
) -> str:
    """Render the per-capability agreement table + per-candidate go/no-go.

    One column per provider (baseline first); one row per §3.4 threshold showing
    each provider's measured value and PASS/FAIL/PENDING. A measured live run of
    both providers reproduces this exact table — that is the §5 verification.
    """
    providers = list(decisions)
    role = {p: "baseline" if p == baseline else "candidate" for p in providers}
    header = ["Capability", "Metric", "Threshold", *(f"{p} ({role[p]})" for p in providers)]
    rows: list[list[str]] = [header, ["---"] * len(header)]
    for spec in _CHECK_SPECS:
        cells = [spec.capability, spec.metric, _fmt_threshold(spec.direction, spec.threshold)]
        for p in providers:
            by_key = {c.key: c for c in decisions[p].checks}
            cells.append(_fmt_measured(by_key[spec.key]))
        rows.append(cells)
    table = "\n".join("| " + " | ".join(r) + " |" for r in rows)

    verdicts = [
        f"- **{p}: {decisions[p].decision}** — {decisions[p].recommendation}"
        for p in providers
        if p != baseline
    ]
    return table + "\n\n" + "\n".join(verdicts) + "\n"
