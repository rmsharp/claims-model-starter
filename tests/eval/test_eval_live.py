"""Live tier — eval a real LLM provider against the Phase B corpus (§3.4 gate).

**DEFERRED THIS SESSION.** No ``ANTHROPIC_API_KEY`` was available (operator
decision, Session 161), so these tests are auto-skipped (``tests/eval/conftest``)
and deselected by default (``-m 'not live'``). The measured Anthropic baseline and
the threshold calibration are a logged follow-up — see
``tests/eval/README.md`` §"Live baseline (deferred)". The battery is fully wired
and runnable: ``ANTHROPIC_API_KEY=… uv run pytest -m live``.

**Non-determinism (§3.4).** Each governed case is sampled ``_N_SAMPLES`` (≥5)
times and judged on a pass-RATE plus structural/semantic invariants, never exact
text. Claude-family models reject ``temperature``, so we sample and rely on the
invariants rather than pinning ``temperature=0``.

**Caveat — interview answers.** ``test_live_interview_converges`` feeds the
recorded stakeholder answers to a real model that asks its own questions; if the
model asks for more answers than the script supplies, that counts as a
non-convergence. A more robust stakeholder-answer strategy (or padding) is part
of the deferred live calibration.
"""

from __future__ import annotations

import pytest
from model_project_constructor_data_agent.db import ReadOnlyDB
from model_project_constructor_data_agent.factory import make_llm_client as make_data_client

from model_project_constructor.agents.intake.agent import IntakeAgent
from model_project_constructor.agents.intake.factory import make_llm_client as make_intake_client
from model_project_constructor.agents.intake.fixture import (
    answers_from_fixture,
    load_fixture,
    review_sequence_from_fixture,
)
from tests.eval import eval_thresholds as thresholds
from tests.eval.eval_corpus import (
    load_governance_cases,
    load_interview_cases,
    load_sql_cases,
    pc_inventory_from_db,
)
from tests.eval.eval_scoring import (
    interview_converged,
    pass_rate,
    quality_checks_structural_ok,
    score_governance,
    sql_executes,
    sql_parse_valid,
)

pytestmark = pytest.mark.live

#: Samples per governed case — §3.4 requires N≥5 to judge a pass-rate.
_N_SAMPLES = 5


def test_live_governance_agreement_and_no_laxer_miss() -> None:
    client = make_intake_client("anthropic")
    exact_matches: list[bool] = []
    laxer_misses = 0
    for case in load_governance_cases():
        for _ in range(_N_SAMPLES):
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


def test_live_primary_sql_parses_and_executes(seeded_pc_db: ReadOnlyDB) -> None:
    client = make_data_client("anthropic")
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


def test_live_quality_checks_structural() -> None:
    client = make_data_client("anthropic")
    ok: list[bool] = []
    for case in load_sql_cases():
        if case.kind != "primary":
            continue
        specs = client.generate_primary_queries(case.request)
        qc_lists = client.generate_quality_checks(case.request, specs)
        ok.append(quality_checks_structural_ok(len(specs), qc_lists))
    assert pass_rate("qc_structural", ok).meets(thresholds.QUALITY_CHECKS_STRUCTURAL_MIN)


def test_live_interview_converges() -> None:
    results: list[bool] = []
    for case in load_interview_cases():
        if not case.expect_complete:
            continue
        fixture = load_fixture(case.fixture_path)
        agent = IntakeAgent(llm=make_intake_client("anthropic"))
        try:
            report = agent.run_scripted(
                stakeholder_id=fixture["stakeholder_id"],
                session_id=f"live-{fixture['session_id']}",
                domain=fixture.get("domain", "pc_claims"),
                initial_problem=fixture.get("initial_problem"),
                interview_answers=answers_from_fixture(fixture),
                review_responses=review_sequence_from_fixture(fixture),
            )
        except RuntimeError:
            # Model asked for more answers than the recorded script supplies —
            # counts as a non-convergence for this golden (see module caveat).
            results.append(False)
            continue
        results.append(interview_converged(report))
    assert pass_rate("interview", results).meets(thresholds.INTERVIEW_CONVERGENCE_MIN)
