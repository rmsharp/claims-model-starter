# Eval / parity harness (Phase B corpus + Phase E cutover gate)

The provider-quality gate for the [multi-provider LLM plan](../../docs/planning/multi-provider-llm-plan.md)
(§5 Phase B). The factory seam makes *swapping* an LLM provider trivial; **all**
the risk is in **output quality**. This harness measures that quality so no
second provider reaches production until it clears the §3.4 thresholds (the
Phase E gate). It is deliberately the "here be dragons" phase.

## Two tiers

| Tier | Files | Marker | Credentials | Runs |
|------|-------|--------|-------------|------|
| **Deterministic** | `test_eval_corpus.py`, `test_eval_scoring.py`, `test_eval_cutover.py` | *(none)* | not needed | every PR / CI, offline |
| **Live** | `test_eval_live.py` | `@pytest.mark.live` | per provider (`anthropic` → `ANTHROPIC_API_KEY`; `bedrock` → AWS chain) | periodic / pre-cutover (Phase E shadow run) |

```bash
uv run pytest -m 'not live'                              # deterministic tier — explicit live-deselect
ANTHROPIC_API_KEY=… AWS_PROFILE=… uv run pytest -m live   # shadow run — measures both providers
```

CI hermeticity is preserved **without** a `-m 'not live'` flag: the four
`.github/workflows/ci.yml` jobs run `uv run pytest -q` with **no** credentials,
and `tests/eval/conftest.py::pytest_collection_modifyitems` auto-skips each
`live`-marked case when *its provider's* credentials are absent
(`eval_cutover.provider_creds_available`: `anthropic` → `ANTHROPIC_API_KEY`,
`bedrock` → the AWS chain). With no creds for any provider, CI skips the whole
tier; a Bedrock-only environment runs only the Bedrock half. `-m 'not live'` is
the explicit deselect (useful locally when creds *are* present). The skip is
keyed on the `live` marker only — non-eval tests are unaffected.

**The deterministic tier proves the *harness* measures correctly** (the scorers
and oracles, fed reference / deliberately-perturbed data). **The live tier feeds
the same corpus + scorers a real provider's output** and checks the thresholds.
The split is what lets the gate exist without breaking CI hermeticity.

## Live baseline (measured — harness not yet trustworthy)

> **Status (Sessions 161–162):** the live Anthropic baseline and the Bedrock run
> were deferred (no credentials).
>
> **Status (Session 165) — the Anthropic baseline was measured** (`ANTHROPIC_API_KEY`
> from `.env`; Bedrock still deferred — no AWS creds). **Result: the incumbent
> `anthropic` fails 5 of 8 thresholds, dominated by harness/corpus artifacts** —
> all interviews hit the scripted-replay caveat (#21); the governance reference
> labels disagree with live output (0% exact agreement); one QC output truncates
> at `max_tokens`. See [`PHASE_E_AGREEMENT_REPORT.md`](PHASE_E_AGREEMENT_REPORT.md)
> §"Baseline findings" for the per-metric diagnosis and the harness-fix follow-ups.

The §3.4 thresholds below remain **proposed**: the first baseline measured the
*harness*, not the providers, so it does **not** calibrate them — and they were
deliberately **not** lowered to match a broken harness. Calibration becomes
meaningful only once the harness fixes land (interview-answer robustness,
governance-reference re-validation + a less brittle metric, QC `max_tokens`, SQL
executability). Run the baseline with `uv run python tests/eval/shadow_run.py`;
then, **only** for a genuine "threshold too strict" miss, adjust
`eval_thresholds.py` and note the change here.

## Phase E — shadow run + cutover gate

`test_eval_live.py` is parametrized over **both** providers
(`eval_cutover.SHADOW_PROVIDERS` — `anthropic` baseline + `bedrock` candidate), so
one `pytest -m live` runs the **shadow run**: the same corpus through each
provider, side-by-side. The per-provider pass-rates feed the **cutover gate** in
[`eval_cutover.py`](eval_cutover.py) — pure, deterministic logic
(`test_eval_cutover.py` proves it offline, no key) that decides go/no-go against
every §3.4 threshold. The §5 rule: **cutover only if the candidate meets every
threshold**; an unmet *or unmeasured* threshold keeps `anthropic` primary.

Seven of the eight gate metrics are live-tier pass-rates from `test_eval_live.py`;
the eighth, `json_parse`, is the **deterministic** parity result
(`test_llm_json_parity.py`, provider-parametrized in Phase B) — not a live-tier
number. `PHASE_E_AGREEMENT_REPORT.md` §"Filling this report" gives the exact
recipe for each.

The committed decision, the run procedure, and the per-entrypoint cutover steps
live in [`PHASE_E_AGREEMENT_REPORT.md`](PHASE_E_AGREEMENT_REPORT.md). **Current
decision: NO-GO** — the Anthropic baseline is measured (S165) but the incumbent
fails 5/8 thresholds on harness/corpus artifacts (see §"Live baseline" above), and
`bedrock` is still unmeasured; the gate keeps `anthropic` primary.

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
