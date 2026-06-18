# Phase E — provider shadow run + cutover agreement report

The production go/no-go for replacing the default LLM provider, per the
[multi-provider LLM plan](../../docs/planning/multi-provider-llm-plan.md) §5
Phase E and the §3.4 threshold gate. The factory seam makes *swapping* a provider
trivial; this report is the gate that decides whether a swap is *safe* — a
candidate reaches production **only if it meets every §3.4 threshold** measured
on the Phase B golden corpus, side-by-side with the incumbent.

- **Baseline (incumbent):** `anthropic` (first-party Claude) — the current
  production default.
- **Candidate:** `bedrock` (AWS Bedrock-hosted Claude, Phase C).

## Decision (Session 164): **NO-GO by default — keep `anthropic` primary**

**No live credentials were available this session** (`ANTHROPIC_API_KEY` unset; no
AWS credential chain), so **no threshold has a measured number** — every cell
below is `PENDING`. The §5 rule is that cutover requires the candidate to meet
*every* threshold; an unmeasured threshold cannot certify a GO, so the gate
resolves to **keep `anthropic` primary** until a shadow run fills the numbers.
This is a deferral of the *measurement*, not of the gate: the harness and the
decision logic are built, tested, and runnable (see "How to run" below).

This mirrors the Phase B (Session 161) and Phase C (Session 162) deferrals — the
live run is a logged follow-up, not a silent skip.

### Agreement table (reproduced from `eval_cutover.render_agreement_report`)

<!-- Regenerate with:
  uv run python -c "from tests.eval.eval_cutover import pending_decision, render_agreement_report, SHADOW_PROVIDERS as P; print(render_agreement_report({p: pending_decision(p) for p in P}))"
A live run replaces each PENDING cell with `<rate> (PASS|FAIL)`. -->

| Capability | Metric | Threshold | anthropic (baseline) | bedrock (candidate) |
| --- | --- | --- | --- | --- |
| Any JSON method | parse via both _extract_json copies (deterministic: test_llm_json_parity, not live tier) | ≥ 99% | — (PENDING) | — (PENDING) |
| generate_primary_queries | SQL parse-valid | ≥ 100% | — (PENDING) | — (PENDING) |
| generate_primary_queries | SQL executable on the seeded P&C schema | ≥ 95% | — (PENDING) | — (PENDING) |
| classify_governance | exact label agreement (cycle_time AND risk_tier) vs reference | ≥ 90% | — (PENDING) | — (PENDING) |
| classify_governance | laxer-tier misses (predicted strictly less strict than reference) | ≤ 0 | — (PENDING) | — (PENDING) |
| generate_quality_checks | outer array length == #primary queries | ≥ 100% | — (PENDING) | — (PENDING) |
| Intake interview | believe_enough_info within the 20-question cap | ≥ 95% | — (PENDING) | — (PENDING) |
| Intake interview | premature convergences | ≤ 0 | — (PENDING) | — (PENDING) |

- **bedrock: PENDING** — Undecided — keep anthropic primary until measured. bedrock unmeasured: json_parse, sql_parse, sql_exec, governance_agreement, governance_laxer_miss, qc_structural, interview_convergence, interview_premature.

The thresholds themselves are **proposed** (Phase B never measured a live
Anthropic baseline either); the baseline column is `PENDING` for the same reason.
See [`eval_thresholds.py`](eval_thresholds.py) and `README.md` §"Phase E".

## How to run the shadow run

Both providers are measured by a single live run; each provider's cases skip
automatically when its credentials are absent (`conftest.py` →
`eval_cutover.provider_creds_available`):

```bash
# Both halves of the shadow run (anthropic baseline + bedrock candidate):
ANTHROPIC_API_KEY=… AWS_PROFILE=… uv run pytest -m live tests/eval/ -rs

# One provider at a time is also valid — the other half just skips:
ANTHROPIC_API_KEY=…   uv run pytest -m live tests/eval/   # baseline only
AWS_PROFILE=…         uv run pytest -m live tests/eval/   # candidate only
```

Each capability is sampled N ≥ 5 times and judged on a pass-*rate* + structural
invariants (§3.4 non-determinism handling); `model=None` is passed so each
provider uses its native default id (Bedrock gets the `anthropic.`-prefixed
default — no cross-provider 400).

### Filling this report from a live run

The eight gate keys (`eval_cutover.CHECK_KEYS`) come from two sources:

- **Seven live-tier metrics** — `sql_parse`, `sql_exec`, `governance_agreement`,
  `governance_laxer_miss`, `qc_structural`, `interview_convergence`,
  `interview_premature`: read each provider's pass-rate / miss-count from the
  `test_eval_live.py` shadow-run output.
- **One deterministic metric** — `json_parse`: this is **not** a live-tier number.
  §3.4's oracle for it is the provider-parametrized parity battery. Run
  `uv run pytest tests/test_llm_json_parity.py -q` (it covers every registered
  `(seam, provider)` parser, incl. `bedrock`); a green run means each provider's
  `_extract_json` parsers handle the battery → record **`1.0`** for that provider.
  A real-output parse failure would instead surface as a failure in the live
  capability tests above (they raise on unparseable provider JSON).

Then build the decision and regenerate the table:

```python
from tests.eval.eval_cutover import evaluate_cutover, render_agreement_report
# Every CHECK_KEYS entry must be present (a missing key reads as PENDING):
measured = {
    "anthropic": {
        "json_parse": 1.0, "sql_parse": 1.0, "sql_exec": 0.97,
        "governance_agreement": 0.95, "governance_laxer_miss": 0,
        "qc_structural": 1.0, "interview_convergence": 0.96, "interview_premature": 0,
    },
    "bedrock": {
        "json_parse": 1.0, "sql_parse": 1.0, "sql_exec": 0.96,
        "governance_agreement": 0.92, "governance_laxer_miss": 0,
        "qc_structural": 1.0, "interview_convergence": 0.95, "interview_premature": 0,
    },
}
decisions = {p: evaluate_cutover(p, m) for p, m in measured.items()}
print(render_agreement_report(decisions))
```

Paste the regenerated table above, record the measured `(provider, model)`, and
update the decision line. If the **baseline** fails its own threshold, the
threshold is miscalibrated — fix `eval_thresholds.py` and note it (§3.4).

## Cutover procedure (only on a GO)

The plan says "flip the default provider via the Phase A config." That flips the
**intake web UI only** — the two CLIs hardcode their own `--provider` default, so
a real cutover touches three entrypoints:

| Entrypoint | How its default provider is chosen today | Cutover action |
| --- | --- | --- |
| Intake web UI | falls back to `DEFAULT_LLM_PROVIDER` (`config.py:165`) or `INTAKE_LLM_PROVIDER` env (Phase D) | set `DEFAULT_LLM_PROVIDER = "bedrock"`, or `INTAKE_LLM_PROVIDER=bedrock` per deployment |
| `scripts/run_pipeline.py` | `--provider` default is **hardcoded** `"anthropic"` (`:459`) | change the literal to `bedrock` **or** pass `--provider bedrock` |
| data-agent `cli.py` | `--provider` default is **hardcoded** `"anthropic"` (`:107`) | change the literal to `bedrock` **or** pass `--provider bedrock` |

**Prerequisite for a `run_pipeline.py` Bedrock cutover — the model-id gap.**
`run_pipeline.py --model` defaults to the first-party Opus id
(`PILOT_DEFAULT_MODEL`), which 400s on a Bedrock client without `--model`
(Trap-4-adjacent; documented at Phase C). Either pass
`--model anthropic.claude-…` or make the `--model` default provider-aware first
(the deferred follow-up). The intake web UI already avoids this (`model=None`,
Phase D); the data-agent CLI takes its own `--model`.

The cutover itself (editing the defaults) is **operator-gated** and may be its
own follow-up session (§5). Keep the shadow run as a periodic regression after
any cutover.

## Gap list (carried into a future session)

1. **No live measurement** — both providers' pass-rates are `PENDING` (no creds).
   The single largest follow-up; everything below depends on a live run.
2. **Thresholds still proposed** — never calibrated against a measured Anthropic
   baseline (Phase B deferral). Confirm/adjust on the first live run.
3. **Interview convergence robustness** — `test_live_interview_converges` counts
   a model asking for more answers than the script supplies as a non-convergence;
   a robust stakeholder-answer strategy is needed before its number is trusted
   (`README.md` §Caveats, `PROJECT_LEARNINGS` #21).
4. **`GDPR_ART_22` under-sampled** in the governance corpus (`README.md` §Caveats).
5. **CLI provider defaults are hardcoded** — `run_pipeline.py` / data-agent
   `cli.py` do not read `DEFAULT_LLM_PROVIDER`; a cleaner cutover would route both
   through it. Out of Phase E scope (no production edits); noted for a follow-up.
6. **The model-id gap** (row above) remains open for `run_pipeline.py`.
