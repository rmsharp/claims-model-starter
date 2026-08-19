"""Live tier — shadow run: eval each provider against the Phase B corpus (§3.4).

This is the **Phase E shadow run** (multi-provider LLM plan §5 Phase E): every
test is parametrized over :data:`SHADOW_PROVIDERS` (``anthropic`` baseline +
the ``bedrock`` and ``opencode`` candidates), so a single ``pytest -m live``
measures every runnable provider side-by-side on the same corpus. The
per-provider measurements feed the cutover gate (``eval_cutover``); the committed
go/no-go is ``PHASE_E_AGREEMENT_REPORT.md``.

**Per-provider skip (``tests/eval/conftest``).** Each provider's cases are
auto-skipped when *that* provider's credentials are absent
(``eval_cutover.provider_creds_available``): ``anthropic`` needs
``ANTHROPIC_API_KEY``; ``bedrock`` needs the AWS credential chain; ``opencode``
needs its binary on ``PATH`` **and** ``OPENCODE_EVAL_MODEL`` set — the model
variable is the deliberate opt-in, because the binary alone is present on any
machine that ran the adapter's Phase 1 spike. CI (no creds for any provider)
skips the whole tier, staying hermetic; a Bedrock-only environment runs only the
Bedrock half. ``-m 'not live'`` deselects the tier anywhere.

**DEFERRED (Sessions 161–164).** No credentials available, so every case is
skipped; the measured baseline + candidate pass-rates and the threshold
calibration are a logged follow-up — see ``README.md`` §"Phase E" and
``PHASE_E_AGREEMENT_REPORT.md``. The battery is fully wired and runnable:
``ANTHROPIC_API_KEY=… AWS_PROFILE=… uv run pytest -m live``.

**Non-determinism (§3.4).** Each governed case is sampled ``N_SAMPLES`` (≥5)
times and judged on a pass-RATE plus structural/semantic invariants, never exact
text. Claude-family models reject ``temperature``, so we sample and rely on the
invariants rather than pinning ``temperature=0``.

**Which model each provider runs (``provider_eval_model``).** The SDK providers
get ``None`` so each uses its own native default id (a ``bedrock`` client gets
the ``anthropic.``-prefixed default, never a bare first-party id). ``opencode``
gets the id in ``OPENCODE_EVAL_MODEL``, because it pins no default of its own —
the adapter deliberately leaves the vendor choice to the operator's OpenCode
config (spec D6), which means an unpinned run would measure an unrecorded model.

**Interview answers — robust stakeholder simulator.** ``test_live_interview_
converges`` drives the live interviewer with a :class:`StakeholderSimulator`
(``stakeholder_sim.py``) rather than a fixed recorded list: the simulator answers
whatever question the model actually asks, from the fixture's full knowledge, so
the script can no longer "run out" (the ``interview_convergence`` artifact in
``PHASE_E_AGREEMENT_REPORT.md`` / ``PROJECT_LEARNINGS`` #21). A sub-convergence
now reflects the model's own interview behaviour, not a starved script.

**No hand-written measurement loops left (Session 225).** Each of the three
measured capabilities now runs through a sweep module shared with ``shadow_run``
— ``governance_sweep`` (this file's first test), ``sql_sweep``,
``interview_sweep`` — so the assertion gate and the report-number producer can no
longer drift apart about what a transient means. That is the property this file
needs; it is **not** the same as all three applying one exhaustion rule, and they
do not. All three retry a bounded number of times and all three exclude an
exhausted *transport* error. They differ on an exhausted *seam* error:
``governance_sweep`` and ``sql_sweep`` **score** it (their catch-all classes are
the capability under measurement, and excluding would shrink the denominator
while every surviving sample is clean by construction), ``interview_sweep``
**excludes** it (a sample there is a whole multi-turn interview, and a seam
failure leaves no report to judge). Each module argues its own choice in its
docstring. The governance block was the last hand-written loop and the sharp one:
it had no handler at all, so a single blip aborted the gate, while its twin in
``shadow_run`` scored the same event. No threshold moved.

**Convergence-gate robustness (gap #1c).** The interview test samples each
converging fixture ``N_SAMPLES`` times (like governance) via
``interview_sweep.sweep_interview_convergence``, which also retries/excludes a
transient API/sim blip rather than scoring it a non-convergence — so one
stochastic miss no longer drops the pooled rate below the 95% bar. The 95%
threshold itself is unchanged (a harness-statistics fix, not a #129 loosening).
"""

from __future__ import annotations

import sys

import pytest
from model_project_constructor_data_agent.db import ReadOnlyDB
from model_project_constructor_data_agent.factory import make_llm_client as make_data_client

from model_project_constructor.agents.intake.agent import IntakeAgent
from model_project_constructor.agents.intake.factory import make_llm_client as make_intake_client
from model_project_constructor.agents.intake.fixture import (
    load_fixture,
    review_sequence_from_fixture,
)
from model_project_constructor.schemas.v1.intake import IntakeReport
from tests.eval import eval_thresholds as thresholds
from tests.eval.eval_corpus import (
    InterviewCase,
    load_governance_cases,
    load_interview_cases,
    load_sql_cases,
    pc_inventory_from_db,
)
from tests.eval.eval_cutover import SHADOW_PROVIDERS, provider_eval_model
from tests.eval.eval_scoring import pass_rate
from tests.eval.governance_sweep import sweep_governance_agreement
from tests.eval.interview_sweep import sweep_interview_convergence
from tests.eval.sql_sweep import sweep_sql_capabilities
from tests.eval.stakeholder_sim import stakeholder_simulator_for

pytestmark = pytest.mark.live


@pytest.mark.parametrize("provider", SHADOW_PROVIDERS)
def test_live_governance_cycle_time_agreement_and_no_laxer_miss(provider: str) -> None:
    # Governance is scored per-label (S173 faithfulness fix): cycle_time on EXACT
    # agreement (the gated calibration metric), risk_tier on the zero-tolerance
    # laxer-miss check — a stricter-than-reference tier is the prompt-instructed
    # direction ("pick the stricter tier if in doubt"), so it is not a miss. See
    # eval_scoring.GovernanceScore.
    client = make_intake_client(provider, model=provider_eval_model(provider))
    # Session 225: the hand-written loop this replaces had **no** exception
    # handler, so any seam or transport blip aborted the gate — while
    # ``shadow_run``'s twin loop scored the same event a non-agreement. The two
    # surfaces now share ``sweep_governance_agreement``, which retries a
    # transient, scores an exhausted seam error (the denominator must not shrink)
    # and excludes an exhausted transport one. ``on_event`` is not optional here
    # (the S221 lesson from the SQL test): without a sink every retry and
    # exclusion note — including the ``str(exc)`` that makes a failure
    # attributable at all — is discarded inside the gate that most needs it.
    sweep = sweep_governance_agreement(
        load_governance_cases(),
        client.classify_governance,
        on_event=lambda message: print(f"# WARN {message}", file=sys.stderr),
    )
    rate = pass_rate("governance_cycle_time", sweep.cycle_matches)
    # Every message carries the counters: a pooled denominator and one shrunk by
    # exclusions are otherwise indistinguishable, and ``transient_retries`` is
    # what makes the first-attempt rate recoverable after a best-of-3 run.
    counters = (
        f"seam_failures={sweep.seam_failures}, retries={sweep.transient_retries}, "
        f"excluded_transient={sweep.excluded_transient}"
    )
    # The zero-tolerance laxer-tier check is the load-bearing risk_tier assertion.
    # A seam failure never feeds it — no prediction means no tier, and fabricating
    # a miss here would turn one blip into a NO-GO (see ``governance_sweep``).
    assert sweep.laxer_misses <= thresholds.GOVERNANCE_LAXER_MISSES_MAX, (
        f"{sweep.laxer_misses} laxer-tier miss(es): a prediction was less strict "
        f"than the reference ({counters})"
    )
    assert rate.meets(thresholds.GOVERNANCE_CYCLE_TIME_AGREEMENT_MIN), (
        f"governance cycle_time agreement {rate.rate:.1%} "
        f"< {thresholds.GOVERNANCE_CYCLE_TIME_AGREEMENT_MIN:.0%} "
        f"(n={rate.total}, {counters})"
    )


@pytest.mark.parametrize("provider", SHADOW_PROVIDERS)
def test_live_sql_capabilities(provider: str, seeded_pc_db: ReadOnlyDB) -> None:
    """All three SQL thresholds off ONE sampled sweep (Session 218).

    Was two tests. They each paid for their own ``generate_primary_queries``
    calls over the same corpus — and the QC one built its client *without*
    ``sql_dialect`` (Session 217 fixed only the parse/exec test), so it measured
    the pre-fix prompt while its sibling measured the fixed one. Sharing
    ``sweep_sql_capabilities`` with ``shadow_run`` removes both the duplicated
    spend and the seam where the two loops disagreed.
    """
    # ``sql_dialect`` comes from the fixture DB, not a literal: the client must be
    # told the dialect its SQL is executed against, or this measures dialect
    # mismatch rather than SQL quality (Session 216 / Session 217).
    client = make_data_client(
        provider,
        model=provider_eval_model(provider),
        sql_dialect=seeded_pc_db.dialect,
    )
    # ``on_event`` is not optional here (Session 221): without a sink the sweep's
    # ``notify`` is a no-op, so every retry and exclusion note — including the
    # ``str(exc)`` that makes a failure attributable at all — is discarded inside
    # the gate that most needs it. ``shadow_run`` has passed ``_warn`` since
    # Session 218; this call site never did.
    sweep = sweep_sql_capabilities(
        load_sql_cases(),
        client,
        seeded_pc_db,
        inventory=pc_inventory_from_db(seeded_pc_db),
        on_event=lambda message: print(f"# WARN {message}", file=sys.stderr),
    )
    parse = pass_rate("sql_parse", sweep.parse_results)
    execs = pass_rate("sql_exec", sweep.exec_results)
    qc = pass_rate("qc_structural", sweep.qc_results)
    # Every message carries the retry/exclusion counters (Session 221): a pooled
    # denominator and a denominator shrunk by exclusions are otherwise
    # indistinguishable, and ``transient_retries`` is what makes the first-attempt
    # rate recoverable after a best-of-3 run. The thresholds are untouched.
    counters = f"retries={sweep.transient_retries}, excluded_transient={sweep.excluded_transient}"
    assert parse.meets(thresholds.SQL_PARSE_VALID_MIN), (
        f"sql_parse {sum(sweep.parse_results)}/{len(sweep.parse_results)} ({counters})"
    )
    # The denominator is model-chosen (S216 gotcha 2), so the failure message
    # carries numerator and denominator, plus *why* each query failed — without
    # which this rate is a single uninterpretable bit (S216 gotcha 3).
    assert execs.meets(thresholds.SQL_EXECUTABLE_MIN), (
        f"sql_exec {sum(sweep.exec_results)}/{len(sweep.exec_results)} ({counters}); "
        f"errors={sweep.exec_errors}"
    )
    assert qc.meets(thresholds.QUALITY_CHECKS_STRUCTURAL_MIN), (
        f"qc_structural {sum(sweep.qc_results)}/{len(sweep.qc_results)} ({counters})"
    )


@pytest.mark.parametrize("provider", SHADOW_PROVIDERS)
def test_live_interview_converges(provider: str) -> None:
    # gap #1c: sample each converging fixture N>=5 times and pool the pass-rate
    # (matching the governance tier above), and let the sweep retry/exclude a
    # transient API/sim blip instead of scoring it a non-convergence — so one
    # stochastic miss no longer drops the gate below the 95% bar. The bar itself
    # is unchanged. See ``interview_sweep``.
    def run_one(case: InterviewCase) -> IntakeReport:
        fixture = load_fixture(case.fixture_path)
        agent = IntakeAgent(llm=make_intake_client(provider, model=provider_eval_model(provider)))
        return agent.run_scripted(
            stakeholder_id=fixture["stakeholder_id"],
            session_id=f"live-{fixture['session_id']}",
            domain=fixture.get("domain", "pc_claims"),
            initial_problem=fixture.get("initial_problem"),
            # The pinned model goes to *both* halves of the interview: a provider
            # that pins no default of its own (opencode, spec D6) would otherwise
            # run the simulated stakeholder unpinned while the interviewer ran
            # pinned — two model tiers in one measured conversation.
            answer_provider=stakeholder_simulator_for(
                fixture, provider=provider, model=provider_eval_model(provider)
            ),
            review_responses=review_sequence_from_fixture(fixture),
        )

    sweep = sweep_interview_convergence(load_interview_cases(), run_one)
    rate = pass_rate("interview", sweep.convergence_results)
    assert rate.meets(thresholds.INTERVIEW_CONVERGENCE_MIN), (
        f"interview convergence {rate.rate:.1%} < {thresholds.INTERVIEW_CONVERGENCE_MIN:.0%} "
        f"(n={rate.total}, excluded_transient={sweep.excluded_transient})"
    )
