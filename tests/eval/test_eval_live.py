"""Live tier — shadow run: eval each provider against the Phase B corpus (§3.4).

This is the **Phase E shadow run** (multi-provider LLM plan §5 Phase E): every
test is parametrized over :data:`SHADOW_PROVIDERS` (``anthropic`` baseline +
``bedrock`` candidate), so a single ``pytest -m live`` measures both providers
side-by-side on the same corpus. The per-provider measurements feed the cutover
gate (``eval_cutover``); the committed go/no-go is ``PHASE_E_AGREEMENT_REPORT.md``.

**Per-provider skip (``tests/eval/conftest``).** Each provider's cases are
auto-skipped when *that* provider's credentials are absent
(``eval_cutover.provider_creds_available``): ``anthropic`` needs
``ANTHROPIC_API_KEY``; ``bedrock`` needs the AWS credential chain. CI (no creds
for any provider) skips the whole tier, staying hermetic; a Bedrock-only
environment runs only the Bedrock half. ``-m 'not live'`` deselects the tier
anywhere.

**DEFERRED (Sessions 161–164).** No credentials available, so every case is
skipped; the measured baseline + candidate pass-rates and the threshold
calibration are a logged follow-up — see ``README.md`` §"Phase E" and
``PHASE_E_AGREEMENT_REPORT.md``. The battery is fully wired and runnable:
``ANTHROPIC_API_KEY=… AWS_PROFILE=… uv run pytest -m live``.

**Non-determinism (§3.4).** Each governed case is sampled ``N_SAMPLES`` (≥5)
times and judged on a pass-RATE plus structural/semantic invariants, never exact
text. Claude-family models reject ``temperature``, so we sample and rely on the
invariants rather than pinning ``temperature=0``. ``model=None`` is passed to
every factory so each provider uses its own native default id (a ``bedrock``
client gets the ``anthropic.``-prefixed default, never a bare first-party id).

**Interview answers — robust stakeholder simulator.** ``test_live_interview_
converges`` drives the live interviewer with a :class:`StakeholderSimulator`
(``stakeholder_sim.py``) rather than a fixed recorded list: the simulator answers
whatever question the model actually asks, from the fixture's full knowledge, so
the script can no longer "run out" (the ``interview_convergence`` artifact in
``PHASE_E_AGREEMENT_REPORT.md`` / ``PROJECT_LEARNINGS`` #21). A sub-convergence
now reflects the model's own interview behaviour, not a starved script.

**Convergence-gate robustness (gap #1c).** The interview test samples each
converging fixture ``N_SAMPLES`` times (like governance) via
``interview_sweep.sweep_interview_convergence``, which also retries/excludes a
transient API/sim blip rather than scoring it a non-convergence — so one
stochastic miss no longer drops the pooled rate below the 95% bar. The 95%
threshold itself is unchanged (a harness-statistics fix, not a #129 loosening).
"""

from __future__ import annotations

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
from tests.eval.eval_cutover import SHADOW_PROVIDERS
from tests.eval.eval_scoring import (
    pass_rate,
    quality_checks_structural_ok,
    score_governance,
    sql_executes,
    sql_parse_valid,
)
from tests.eval.interview_sweep import N_SAMPLES, sweep_interview_convergence
from tests.eval.stakeholder_sim import stakeholder_simulator_for

pytestmark = pytest.mark.live


@pytest.mark.parametrize("provider", SHADOW_PROVIDERS)
def test_live_governance_agreement_and_no_laxer_miss(provider: str) -> None:
    client = make_intake_client(provider)
    exact_matches: list[bool] = []
    laxer_misses = 0
    for case in load_governance_cases():
        for _ in range(N_SAMPLES):
            predicted = client.classify_governance(case.draft)
            score = score_governance(case.case_id, case.reference, predicted)
            exact_matches.append(score.exact_label_match)
            laxer_misses += int(score.laxer_tier_miss)
    rate = pass_rate("governance", exact_matches)
    # The zero-tolerance laxer-tier check is the load-bearing assertion.
    assert laxer_misses <= thresholds.GOVERNANCE_LAXER_MISSES_MAX, (
        f"{laxer_misses} laxer-tier miss(es): a prediction was less strict than the reference"
    )
    assert rate.meets(thresholds.GOVERNANCE_AGREEMENT_MIN), (
        f"governance exact-label agreement {rate.rate:.1%} "
        f"< {thresholds.GOVERNANCE_AGREEMENT_MIN:.0%}"
    )


@pytest.mark.parametrize("provider", SHADOW_PROVIDERS)
def test_live_primary_sql_parses_and_executes(provider: str, seeded_pc_db: ReadOnlyDB) -> None:
    client = make_data_client(provider)
    inventory = pc_inventory_from_db(seeded_pc_db)
    parse_results: list[bool] = []
    exec_results: list[bool] = []
    for case in load_sql_cases():
        if case.kind != "primary":
            continue
        specs = client.generate_primary_queries(case.request, data_source_inventory=inventory)
        for spec in specs:
            parse_results.append(sql_parse_valid(spec.sql))
            exec_results.append(sql_executes(seeded_pc_db, spec.sql))
    assert pass_rate("sql_parse", parse_results).meets(thresholds.SQL_PARSE_VALID_MIN)
    assert pass_rate("sql_exec", exec_results).meets(thresholds.SQL_EXECUTABLE_MIN)


@pytest.mark.parametrize("provider", SHADOW_PROVIDERS)
def test_live_quality_checks_structural(provider: str) -> None:
    client = make_data_client(provider)
    ok: list[bool] = []
    for case in load_sql_cases():
        if case.kind != "primary":
            continue
        specs = client.generate_primary_queries(case.request)
        qc_lists = client.generate_quality_checks(case.request, specs)
        ok.append(quality_checks_structural_ok(len(specs), qc_lists))
    assert pass_rate("qc_structural", ok).meets(thresholds.QUALITY_CHECKS_STRUCTURAL_MIN)


@pytest.mark.parametrize("provider", SHADOW_PROVIDERS)
def test_live_interview_converges(provider: str) -> None:
    # gap #1c: sample each converging fixture N>=5 times and pool the pass-rate
    # (matching the governance tier above), and let the sweep retry/exclude a
    # transient API/sim blip instead of scoring it a non-convergence — so one
    # stochastic miss no longer drops the gate below the 95% bar. The bar itself
    # is unchanged. See ``interview_sweep``.
    def run_one(case: InterviewCase) -> IntakeReport:
        fixture = load_fixture(case.fixture_path)
        agent = IntakeAgent(llm=make_intake_client(provider))
        return agent.run_scripted(
            stakeholder_id=fixture["stakeholder_id"],
            session_id=f"live-{fixture['session_id']}",
            domain=fixture.get("domain", "pc_claims"),
            initial_problem=fixture.get("initial_problem"),
            answer_provider=stakeholder_simulator_for(fixture, provider=provider),
            review_responses=review_sequence_from_fixture(fixture),
        )

    sweep = sweep_interview_convergence(load_interview_cases(), run_one)
    rate = pass_rate("interview", sweep.convergence_results)
    assert rate.meets(thresholds.INTERVIEW_CONVERGENCE_MIN), (
        f"interview convergence {rate.rate:.1%} < {thresholds.INTERVIEW_CONVERGENCE_MIN:.0%} "
        f"(n={rate.total}, excluded_transient={sweep.excluded_transient})"
    )
