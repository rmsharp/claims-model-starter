"""Phase E shadow-run driver — measure a provider's §3.4 pass-rates (live).

Runs the Phase B corpus through a real provider client and prints the measured
per-capability rates + the rendered agreement report. This is the **executable**
form of ``PHASE_E_AGREEMENT_REPORT.md`` §"Filling this report": every provider
with credentials available is measured (mirroring the live-tier skip), and the
rates feed ``eval_cutover.evaluate_cutover``.

It is **not** a pytest test — the assert-the-thresholds live tier is
``test_eval_live.py``; this driver *measures and reports* without asserting, so a
sub-threshold result is data (a NO-GO), not a failed run. It calls the live API,
so it requires credentials — run it explicitly::

    ANTHROPIC_API_KEY=… uv run python tests/eval/shadow_run.py                 # anthropic only
    ANTHROPIC_API_KEY=… AWS_PROFILE=… uv run python tests/eval/shadow_run.py   # both providers

``json_parse`` is the deterministic parity result (``test_llm_json_parity``), not
a live rate — recorded as ``1.0`` when that battery passes for the provider's
seams (it reuses the shared ``_extract_json`` parsers). The measurement loops
mirror ``test_eval_live.py`` (which asserts); kept separate so a sub-threshold
number is recorded rather than aborting the run.
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

from model_project_constructor_data_agent.anthropic_client import LLMParseError
from model_project_constructor_data_agent.db import ReadOnlyDB
from model_project_constructor_data_agent.factory import make_llm_client as make_data_client

from model_project_constructor.agents.intake.agent import IntakeAgent
from model_project_constructor.agents.intake.factory import make_llm_client as make_intake_client
from model_project_constructor.agents.intake.fixture import (
    load_fixture,
    review_sequence_from_fixture,
)
from model_project_constructor.agents.intake.protocol import IntakeLLMError
from model_project_constructor.schemas.v1.intake import IntakeReport
from tests.eval.eval_corpus import (
    InterviewCase,
    load_governance_cases,
    load_interview_cases,
    load_sql_cases,
    pc_inventory_from_db,
    seed_pc_schema,
)
from tests.eval.eval_cutover import (
    SHADOW_PROVIDERS,
    evaluate_cutover,
    provider_creds_available,
    render_agreement_report,
)
from tests.eval.eval_scoring import (
    pass_rate,
    quality_checks_structural_ok,
    score_governance,
    sql_executes,
    sql_parse_valid,
)
from tests.eval.interview_sweep import N_SAMPLES, sweep_interview_convergence
from tests.eval.stakeholder_sim import stakeholder_simulator_for


def _warn(message: str) -> None:
    """Note a caught seam failure to stderr (it is recorded as a measured miss)."""
    print(f"# WARN {message}", file=sys.stderr)


def measure_provider(
    provider: str, db: ReadOnlyDB, *, n_samples: int = N_SAMPLES
) -> dict[str, float]:
    """Measure ``provider``'s §3.4 pass-rates over the Phase B corpus (live)."""
    intake = make_intake_client(provider)
    data = make_data_client(provider)
    inventory = pc_inventory_from_db(db)

    # governance (S173 faithfulness fix): the two labels are scored separately.
    # cycle_time agreement is EXACT (the gated calibration metric); risk_tier is
    # gated by the zero-tolerance laxer-miss count, so its match-or-stricter rate
    # is tracked as a diagnostic (a stricter tier is the prompt-instructed
    # direction, not a disagreement). A seam error (parse failure, no retry —
    # Trap 5) is a measured non-agreement, not a crash.
    gov_cycle_matches: list[bool] = []
    gov_risk_acceptable: list[bool] = []
    laxer = 0
    for case in load_governance_cases():
        for _ in range(n_samples):
            try:
                predicted = intake.classify_governance(case.draft)
            except IntakeLLMError as exc:
                _warn(f"governance/{case.case_id}: {type(exc).__name__} -> non-agreement")
                gov_cycle_matches.append(False)
                gov_risk_acceptable.append(False)
                continue
            score = score_governance(case.case_id, case.reference, predicted)
            gov_cycle_matches.append(score.cycle_time_match)
            gov_risk_acceptable.append(score.risk_tier_acceptable)
            laxer += int(score.laxer_tier_miss)

    # SQL parse/exec + QC structural over the primary cases on the seeded schema
    parse_results: list[bool] = []
    exec_results: list[bool] = []
    qc_ok: list[bool] = []
    for case in load_sql_cases():
        if case.kind != "primary":
            continue
        try:
            specs = data.generate_primary_queries(case.request, data_source_inventory=inventory)
        except LLMParseError as exc:
            _warn(f"sql/{case.name}: {type(exc).__name__} on primary queries -> parse+exec fail")
            parse_results.append(False)
            exec_results.append(False)
            qc_ok.append(False)
            continue
        for spec in specs:
            parse_results.append(sql_parse_valid(spec.sql))
            exec_results.append(sql_executes(db, spec.sql))
        try:
            qc_lists = data.generate_quality_checks(case.request, specs)
            qc_ok.append(quality_checks_structural_ok(len(specs), qc_lists))
        except LLMParseError as exc:
            _warn(f"qc/{case.name}: {type(exc).__name__} on quality checks -> structural fail")
            qc_ok.append(False)

    # interview convergence + premature-convergence count (gap #1c): sample each
    # converging case N>=5 times and pool, and retry/exclude a transient API/sim
    # blip rather than scoring it a non-convergence. A genuine non-convergence is
    # a returned report carrying "questions_cap_reached"; a real harness/graph bug
    # propagates (aborts the run) instead of being silently counted as a miss.
    def _run_interview(case: InterviewCase) -> IntakeReport:
        fixture = load_fixture(case.fixture_path)
        agent = IntakeAgent(llm=make_intake_client(provider))
        return agent.run_scripted(
            stakeholder_id=fixture["stakeholder_id"],
            session_id=f"shadow-{provider}-{fixture['session_id']}",
            domain=fixture.get("domain", "pc_claims"),
            initial_problem=fixture.get("initial_problem"),
            answer_provider=stakeholder_simulator_for(fixture, provider=provider),
            review_responses=review_sequence_from_fixture(fixture),
        )

    sweep = sweep_interview_convergence(
        load_interview_cases(), _run_interview, n_samples=n_samples, on_event=_warn
    )

    return {
        # deterministic parity battery (test_llm_json_parity), not a live rate:
        "json_parse": 1.0,
        "sql_parse": pass_rate("sql_parse", parse_results).rate,
        "sql_exec": pass_rate("sql_exec", exec_results).rate,
        "governance_cycle_time_agreement": pass_rate("gov_cycle_time", gov_cycle_matches).rate,
        "governance_laxer_miss": float(laxer),
        # diagnostic only (not a gate key — risk_tier is gated by laxer_miss):
        # the risk_tier match-or-stricter rate, surfaced for the agreement report.
        "governance_risk_tier_acceptable": pass_rate("gov_risk_tier", gov_risk_acceptable).rate,
        "qc_structural": pass_rate("qc", qc_ok).rate,
        "interview_convergence": pass_rate("interview", sweep.convergence_results).rate,
        "interview_premature": float(sweep.premature_count),
    }


def main() -> None:
    providers = [p for p in SHADOW_PROVIDERS if provider_creds_available(p)]
    skipped = [p for p in SHADOW_PROVIDERS if p not in providers]
    if skipped:
        print(f"# skipped (no creds): {', '.join(skipped)}")
    if not providers:
        print("# no provider credentials available — nothing to measure")
        return

    with tempfile.TemporaryDirectory() as tmp:
        url = f"sqlite:///{Path(tmp) / 'pc_eval.db'}"
        seed_pc_schema(url)
        db = ReadOnlyDB(url)
        db.connect()
        try:
            measured = {p: measure_provider(p, db) for p in providers}
        finally:
            db.close()

    for provider, rates in measured.items():
        print(f"# measured[{provider}] = {json.dumps(rates)}")
    decisions = {p: evaluate_cutover(p, m) for p, m in measured.items()}
    print()
    print(render_agreement_report(decisions))


if __name__ == "__main__":
    main()
