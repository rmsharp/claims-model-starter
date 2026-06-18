# Phase B eval / parity harness

The provider-quality gate for the [multi-provider LLM plan](../../docs/planning/multi-provider-llm-plan.md)
(§5 Phase B). The factory seam makes *swapping* an LLM provider trivial; **all**
the risk is in **output quality**. This harness measures that quality so no
second provider reaches production until it clears the §3.4 thresholds (the
Phase E gate). It is deliberately the "here be dragons" phase.

## Two tiers

| Tier | Files | Marker | Key | Runs |
|------|-------|--------|-----|------|
| **Deterministic** | `test_eval_corpus.py`, `test_eval_scoring.py` | *(none)* | not needed | every PR / CI, offline |
| **Live** | `test_eval_live.py` | `@pytest.mark.live` | `ANTHROPIC_API_KEY` | periodic / pre-cutover |

```bash
uv run pytest -m 'not live'                 # deterministic tier — explicit live-deselect
ANTHROPIC_API_KEY=… uv run pytest -m live    # live tier — measures a real provider
```

CI hermeticity is preserved **without** a `-m 'not live'` flag: the four
`.github/workflows/ci.yml` jobs run `uv run pytest -q` with **no** key, and
`tests/eval/conftest.py::pytest_collection_modifyitems` auto-skips every
`live`-marked test when `ANTHROPIC_API_KEY` is unset — so CI skips the live tier
via the no-key hook, and the tier is also safe to run locally without a key.
`-m 'not live'` is the explicit deselect (useful locally when a key *is* present).
The skip is keyed on the `live` marker only — non-eval tests are unaffected.

**The deterministic tier proves the *harness* measures correctly** (the scorers
and oracles, fed reference / deliberately-perturbed data). **The live tier feeds
the same corpus + scorers a real provider's output** and checks the thresholds.
The split is what lets the gate exist without breaking CI hermeticity.

## Live baseline (deferred)

> **Status (Session 161):** no `ANTHROPIC_API_KEY` was available, so the live
> Anthropic baseline run is **deferred** (operator decision). The live tier is
> wired and runnable; the measured Anthropic numbers and the resulting threshold
> calibration are a **logged follow-up**, not silently skipped.
>
> **Status (Session 162) — Phase C added the AWS Bedrock-hosted Claude provider
> (`"bedrock"`).** Its **live corpus run is also deferred** — no AWS credentials
> this session (the operator is preparing for a future deployment). The Bedrock
> client is constructible and unit-tested, and the deterministic tier proves the
> harness; the candidate's live pass-rates are part of the deferred live
> calibration. The live tier is currently keyed to first-party `ANTHROPIC_API_KEY`
> (`anthropic` provider) — running the corpus against `bedrock` additionally
> needs AWS credentials/region available to the boto3 chain and a provider-
> parametrized live eval (Phase E shadow-run territory: §5 Phase E + the §3.4
> threshold gate).

Until the live tier is run, the §3.4 thresholds below are **proposed targets**,
not yet confirmed against a measured Anthropic baseline. When a key is available:

1. `ANTHROPIC_API_KEY=… uv run pytest -m live` and record the per-capability
   pass-rates (Anthropic is expected to clear its own thresholds; if it does
   not, the thresholds are miscalibrated — fix them and note the change here).
2. Replace "proposed" with the measured numbers in `eval_thresholds.py` + this
   table, and note the model/tier measured (e.g. `claude-sonnet-4-6`).
3. Wire `test_live_interview_converges` to a robust stakeholder-answer strategy
   (see *Caveats* below) before trusting its convergence number.

## Thresholds (§3.4 — proposed)

Single-sourced in [`eval_thresholds.py`](eval_thresholds.py).

| Capability | Metric | Threshold |
|------------|--------|-----------|
| Any JSON method | parse success via both `_extract_json` copies | ≥ 99% |
| `generate_primary_queries` / baseline | SQL parse-valid 100% **and** executable ≥ 95% on the seeded P&C schema | 100% / ≥ 95% |
| `classify_governance` | exact label agreement (cycle_time **and** risk_tier) vs reference; **0 laxer-tier misses** | ≥ 90% / 0 |
| `generate_quality_checks` | outer array length == #primary queries | 100% |
| Intake interview | `believe_enough_info` within the 20-question cap; 0 premature convergence | ≥ 95% / 0 |

**Laxer-tier miss** = a predicted `risk_tier` strictly *less strict* than the
reference. The prompt's rule is "if in doubt, pick the stricter tier", so erring
stricter is allowed; erring laxer is the zero-tolerance failure. Strictness order
(strictest → laxest): `tier_1_critical` → `tier_2_high` → `tier_3_moderate` →
`tier_4_low` (`eval_thresholds.RISK_TIER_STRICTNESS`).

**Non-determinism:** the live tier samples each governed case N ≥ 5 times and
judges a pass-*rate* + structural/semantic invariants — never exact text.
Claude-family models reject `temperature`, so we sample and rely on the
invariants rather than pinning `temperature=0`.

## Corpus

| Capability | Source | Cases |
|------------|--------|-------|
| Governance | 3 reused project intake fixtures + 1 authored | `subrogation`, `pricing_optimization`, `fraud_triage`, `reserving_adequacy` |
| SQL / baseline | [`corpus/sql_cases.yaml`](corpus/sql_cases.yaml) over [`corpus/pc_schema.sql`](corpus/pc_schema.sql) | 3 primary + 1 baseline |
| Interview | the 4 governance scenarios + the question-cap fixture | 5 |
| JSON parse | [`../test_llm_json_parity.py`](../test_llm_json_parity.py) battery (provider-parametrized `_SEAMS` registry) | 9 parse + 3 raise |

Loaders live in [`eval_corpus.py`](eval_corpus.py); scorers in
[`eval_scoring.py`](eval_scoring.py).

### Governance reference labels

The "human-blessed reference" the ≥ 90% agreement / 0-laxer-miss threshold is
measured against is agreed by **single SME reviewer** — the operator is the
blessing authority (a solo project; consensus presupposes a review panel that
does not exist). Methodology (operator decision, Session 161):

- **Three cases reuse the project's own human-authored intake fixtures**
  (`tests/fixtures/{subrogation,pricing_optimization,fraud_triage}.yaml`). Their
  `governance:` blocks are existing project goldens — the most defensible
  reference — and are single-sourced (not duplicated) into the corpus.
- **One case (`reserving_adequacy`) is authored for the eval** to complete the
  `RiskTier` vocabulary (a `tier_4_low` / `operational` example) and exercise the
  `ASOP_56` framework. It is labelled by applying the `SYSTEM_GOVERNANCE` rule
  ("be conservative; if in doubt, pick the stricter tier") to the scenario, with
  a per-field rationale in the fixture.
- **The operator may override any label.** The reference is rule-derived but
  operator-ratified; this file is the record of that methodology.

The four cases span all four `RiskTier` values
(`test_governance_corpus_spans_all_risk_tiers`), so the laxer-miss logic is
exercised meaningfully.

## Caveats / follow-ups (logged, not silent)

1. **Live baseline deferred** — see above. The single largest follow-up.
2. **Interview live test** — `test_live_interview_converges` feeds the recorded
   stakeholder answers to a real model that asks its own questions; if it asks
   for more answers than the script supplies, that counts as a non-convergence
   (`PROJECT_LEARNINGS` #21). A robust stakeholder-answer strategy (or padding)
   is part of the deferred live calibration.
3. **Framework coverage** — the corpus exercises `SR_26_2`, `NAIC_AIS`,
   `EU_AI_ACT_ART_9`, and `ASOP_56`; `GDPR_ART_22` is under-sampled. Add a
   GDPR-relevant scenario when the live baseline is calibrated.
4. **SQL executability fairness** — the live SQL test passes a
   `DataSourceInventory` introspected from the seeded schema
   (`pc_inventory_from_db`) so the model can name real tables; executability is
   meaningless without it.
