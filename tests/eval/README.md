# Eval / parity harness (Phase B corpus + Phase E cutover gate)

The provider-quality gate for the [multi-provider LLM plan](../../docs/architecture-history/multi-provider-llm-plan.md)
(§5 Phase B). The factory seam makes *swapping* an LLM provider trivial; **all**
the risk is in **output quality**. This harness measures that quality so no
second provider reaches production until it clears the §3.4 thresholds (the
Phase E gate). It is deliberately the "here be dragons" phase.

## Two tiers

| Tier | Files | Marker | Credentials | Runs |
|------|-------|--------|-------------|------|
| **Deterministic** | `test_eval_corpus.py`, `test_eval_scoring.py`, `test_eval_cutover.py` | *(none)* | not needed | every PR / CI, offline |
| **Live** | `test_eval_live.py` | `@pytest.mark.live` | per provider (`anthropic` → `ANTHROPIC_API_KEY`; `bedrock` → AWS chain; `opencode` → binary on `PATH` **and** `OPENCODE_EVAL_MODEL`) | periodic / pre-cutover (Phase E shadow run) |

```bash
uv run pytest -m 'not live'                              # deterministic tier — explicit live-deselect
ANTHROPIC_API_KEY=… AWS_PROFILE=… uv run pytest -m live   # shadow run — every runnable provider
```

CI hermeticity is preserved **without** a `-m 'not live'` flag: the four
`.github/workflows/ci.yml` jobs run `uv run pytest -q` with **no** credentials,
and `tests/eval/conftest.py::pytest_collection_modifyitems` auto-skips each
`live`-marked case when *its provider's* credentials are absent
(`eval_cutover.provider_creds_available`: `anthropic` → `ANTHROPIC_API_KEY`,
`bedrock` → the AWS chain, `opencode` → see below). With no creds for any
provider, CI skips the whole tier; a Bedrock-only environment runs only the
Bedrock half. `-m 'not live'` is the explicit deselect (useful locally when creds
*are* present). The skip is keyed on the `live` marker only — non-eval tests are
unaffected.

**Why `opencode` needs two signals.** Its binary is installed globally on any
machine that ran the adapter's Phase 1 spike, so gating on `shutil.which` alone
would make a bare `uv run pytest -q` *on a developer machine* run and bill the
live tier — while CI, which has no binary, still looked hermetic. So the probe
also requires `OPENCODE_EVAL_MODEL`, which is simultaneously the deliberate
opt-in and the model id the run pins: that provider deliberately pins no default
model of its own (adapter spec D6, so the vendor choice stays in the operator's
OpenCode config), which means an unpinned run would measure an unrecorded model.
`eval_cutover.provider_eval_model` reads the same variable and both the live tier
and `shadow_run.py` pass it to the factory; the SDK providers get `None` and stay
on their own native default ids.

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
>
> **Status (Session 166) — the interview scripted-replay artifact (#21) is fixed.**
> A robust [`StakeholderSimulator`](stakeholder_sim.py) now answers whatever the
> live model asks (verified live: the interviewer asked 9–10 questions vs the 7–10
> recorded; no more "ran out of answers"). `interview_convergence` now measures the
> live model/corpus interaction, not the replay artifact. It is **still 0%** live,
> now blocked by two *genuine* downstream factors: (a) a `max_tokens` truncation on
> the large draft JSON (gap #3 — `stop_reason=max_tokens` at 4096); and (b) at
> adequate `max_tokens`, the rigorous live interviewer drafts with a populated
> `missing_fields` list (governance/fairness/cost/baseline specifics the fixtures
> don't pre-answer) → `DRAFT_INCOMPLETE`. Both are handed-off follow-ups, not
> answer-robustness gaps. See `PHASE_E_AGREEMENT_REPORT.md` §"Gap list".
>
> **Status (Session 167) — the `max_tokens` truncation (gap #3) is fixed.**
> `DEFAULT_MAX_TOKENS` is raised 4096→16384 in both `AnthropicLLMClient`s and a
> `stop_reason='max_tokens'` guard now raises an actionable error instead of a
> cryptic parse failure. Verified live at the new default: the intake
> `draft_report` completes (no truncation — the draft is still `DRAFT_INCOMPLETE`
> for the **separate** gap #1b reason) and `generate_quality_checks` on the large
> `tx_auto_training` case returns 3 groups / 29 checks. This unblocks both
> `qc_structural` and interview-convergence **Layer 2** — but `interview_convergence`
> is **still not green**: gap #1b (the rigorous interviewer's populated
> `missing_fields` vs fixture depth / metric strictness) remains the convergence
> blocker. A fresh baseline run will re-measure `qc_structural`.

The §3.4 thresholds below remain **proposed**: the first baseline measured the
*harness*, not the providers, so it does **not** calibrate them — and they were
deliberately **not** lowered to match a broken harness. Calibration becomes
meaningful only once the remaining harness fixes land (interview convergence-metric
calibration (gap #1b), governance-reference re-validation + a less brittle metric,
SQL executability — interview-answer robustness landed S166 and the QC/draft
`max_tokens` truncation landed S167). Run the baseline with
`uv run python tests/eval/shadow_run.py`;
then, **only** for a genuine "threshold too strict" miss, adjust
`eval_thresholds.py` and note the change here.

## Phase E — shadow run + cutover gate

`test_eval_live.py` is parametrized over **every** shadow provider
(`eval_cutover.SHADOW_PROVIDERS` — `anthropic` baseline + the `bedrock` and
`opencode` candidates), so one `pytest -m live` runs the **shadow run**: the same
corpus through each provider, side-by-side. The per-provider pass-rates feed the **cutover gate** in
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
decision: NO-GO** — the Anthropic baseline is measured (S165, re-measured through
S177) but `sql_exec` still fails, and both candidates (`bedrock`, `opencode`) are
entirely unmeasured; the gate keeps `anthropic` primary.

**`opencode` is wired, not endorsed (Session 214).** It joined `CANDIDATE_PROVIDERS`
so the gate *can* judge it; every one of its cells is PENDING, and the §5 rule
("an unmeasured threshold cannot certify GO") is what keeps `anthropic` primary
until a shadow run fills them. Its specific quality risk is the adapter's D2
prompt-role change — the system prompt is folded into the user message, inside
OpenCode's own agent scaffold — which is exactly the "parses fine, quality
silently degrades" failure this gate exists to catch. Do not read "the provider
constructs and the tests skip cleanly" as evidence about its output.

## Thresholds (§3.4 — proposed)

Single-sourced in [`eval_thresholds.py`](eval_thresholds.py).

| Capability | Metric | Threshold |
|------------|--------|-----------|
| Any JSON method | parse success via both `_extract_json` copies | ≥ 99% |
| `generate_primary_queries` / baseline | SQL parse-valid 100% **and** executable ≥ 95% on the seeded P&C schema | 100% / ≥ 95% |
| `classify_governance` | per-label (S173): `cycle_time` exact agreement; `risk_tier` **0 laxer-tier misses** (stricter allowed) | ≥ 90% / 0 |
| `generate_quality_checks` | outer array length == #primary queries | 100% |
| Intake interview | `believe_enough_info` within the 20-question cap; 0 premature convergence | ≥ 95% / 0 |

**Laxer-tier miss** = a predicted `risk_tier` strictly *less strict* than the
reference. The prompt's rule is "if in doubt, pick the stricter tier", so erring
stricter is allowed; erring laxer is the zero-tolerance failure. Strictness order
(strictest → laxest): `tier_1_critical` → `tier_2_high` → `tier_3_moderate` →
`tier_4_low` (`eval_thresholds.RISK_TIER_STRICTNESS`).

**Per-label scoring (Session 173).** The two closed-vocab labels are scored
*separately*, each by the metric its nature warrants: `cycle_time` (a descriptive
cadence with no safe direction) on **exact** agreement, gated ≥ 90%; `risk_tier`
(ordered severity) on **match-or-stricter** — a stricter prediction is the
prompt-instructed direction, so its only gate is the zero-tolerance laxer-miss
above (`score_governance.risk_tier_acceptable == not laxer_tier_miss`). This
replaced a former exact-*both* agreement metric that counted the stricter
direction as a disagreement and so scored even the incumbent 0% (a gap #2
artifact). The 0.90 / 0 thresholds are unchanged — a faithfulness fix, not a
threshold loosening (the S168 convergence-scorer precedent).

**Non-determinism:** the live tier samples each governed case N ≥ 5 times and
judges a pass-*rate* + structural/semantic invariants — never exact text.
Claude-family models reject `temperature`, so we sample and rely on the
invariants rather than pinning `temperature=0`.

## Corpus

| Capability | Source | Cases |
|------------|--------|-------|
| Governance | 3 reused project intake fixtures + 2 authored | `subrogation`, `pricing_optimization`, `fraud_triage`, `reserving_adequacy`, `claim_workqueue_triage` |
| SQL / baseline | [`corpus/sql_cases.yaml`](corpus/sql_cases.yaml) over [`corpus/pc_schema.sql`](corpus/pc_schema.sql) | 3 primary + 1 baseline |
| Interview | the 4 governance scenarios + the question-cap fixture | 5 |
| JSON parse | [`../test_llm_json_parity.py`](../test_llm_json_parity.py) battery (provider-parametrized `_SEAMS` registry) | 9 parse + 3 raise |

Loaders live in [`eval_corpus.py`](eval_corpus.py); scorers in
[`eval_scoring.py`](eval_scoring.py).

### Governance reference labels

The "human-blessed reference" the ≥ 90% cycle_time-agreement / 0-laxer-miss
threshold is measured against is agreed by **single SME reviewer** — the operator is the
blessing authority (a solo project; consensus presupposes a review panel that
does not exist). Methodology (operator decision, Session 161):

- **Three cases reuse the project's own human-authored intake fixtures**
  (`tests/fixtures/{subrogation,pricing_optimization,fraud_triage}.yaml`). Their
  `governance:` blocks are existing project goldens — the most defensible
  reference — and are single-sourced (not duplicated) into the corpus.
- **Two cases are authored for the eval.** `reserving_adequacy` completes the
  `RiskTier` vocabulary (a `tier_4_low` / `operational` example) and exercises the
  `ASOP_56` framework. `claim_workqueue_triage` (Session 177) tests the
  `tactical`/`operational` boundary where **run frequency and output purpose
  diverge** — it runs as a fixed nightly batch (an operational frequency cue) yet
  is `tactical` because its output is per-case decision support; `reserving_adequacy`
  is its batch-cadence `operational` foil (a portfolio/close artifact). Both are
  labelled by applying the `SYSTEM_GOVERNANCE` rule ("be conservative; if in doubt,
  pick the stricter tier") to the scenario, with a per-field rationale in the
  fixture; `claim_workqueue_triage`'s `tactical` reference was operator-blessed.
- **The operator may override any label.** The reference is rule-derived but
  operator-ratified; this file is the record of that methodology.
- **Re-validated live against the model (Session 174): all 4 references kept
  unchanged.** A governance-only live re-measure under the faithful (S173) metric
  surfaced two genuine residuals, which the operator ruled are NOT reference
  errors: `fraud_triage` `tier_1_critical` is correct (the live model under-rates
  it `tier_2_high` — a model-quality signal), and the `cycle_time` disagreements
  are a prompt-definition gap (`SYSTEM_GOVERNANCE` lists the cadence vocab with no
  definitions). The references stand.
- **Session 175 closed the `cycle_time` gap** by defining the cadence vocabulary
  in `SYSTEM_GOVERNANCE` (still no reference change) → `cycle_time` agreement
  50%→100%. The `continuous` definition also lifted `fraud_triage` to
  `tier_1_critical` (laxer 0), so governance now passes both metrics.
- **Session 176 confirmed the `fraud_triage` `tier_1_critical` flip is stable**
  (N=20/case live re-measure: `fraud_triage` 20/20 `tier_1_critical`, laxer 0;
  whole gate `cycle_time` 80/80 = 100%, laxer 0; gate assert test PASS). Governance
  is now fully GREEN on the **anthropic baseline** (both §3.4 metrics, zero observed
  variance). Scope caveat: the 100% is corpus-validated — the `cycle_time`
  definitions' over-fit (a separate hardening item, `BACKLOG.md` — closed S177, see below)
  and `bedrock` (unmeasured) are unaffected; overall Phase E stays NO-GO (`sql_exec` 60%).
- **Session 177 hardened the `tactical`/`operational` boundary** to discriminate on
  **output purpose** (per-case decision support vs a periodic institutional artifact),
  not run frequency, and added the role≠frequency divergent case `claim_workqueue_triage`
  (a nightly batch that feeds a per-claim work-queue → `tactical`) that the original four
  never exercised (their cadence is co-linear with frequency, so a corpus green on them is
  not evidence the boundary generalises). Live re-measure
  (anthropic, N=12/case, n=60): `cycle_time` agreement **100%** across all 5 cases (the
  divergent case 12/12 `tactical`), laxer 0; the gate assert test PASSes. `strategic` was
  refined in the same pass to keep `pricing_optimization` correct (output feeds the rating
  engine per-renewal but is set on the quarterly filing calendar → `strategic`). Closes
  the over-fit item; still anthropic-only / corpus-validated, Phase E stays NO-GO.

The corpus spans all four `RiskTier` values
(`test_governance_corpus_spans_all_risk_tiers`), so the laxer-miss logic is
exercised meaningfully, and includes a role≠frequency pair
(`test_governance_corpus_exercises_role_not_frequency_boundary`) so the
`tactical`/`operational` boundary is tested where cadence and output purpose
diverge, not just where they are co-linear.

## Caveats / follow-ups (logged, not silent)

1. **Live baseline deferred** — see above. The single largest follow-up.
2. **Interview live test** — `test_live_interview_converges` now drives the live
   model with the [`StakeholderSimulator`](stakeholder_sim.py), which answers
   whatever it asks (the scripted-replay artifact #21 is fixed; Session 166).
   Remaining to reach a meaningful convergence *rate* (handed off): the gap-#3
   `max_tokens` truncation on the draft JSON, and a calibration call on the live
   interviewer's `missing_fields` rigor vs. fixture depth (and on the scorer,
   which requires `status==COMPLETE` — stricter than the §3.4 metric text
   "`believe_enough_info` within the cap"). Do **not** loosen the scorer to chase
   a number (Candidate #129).
3. **Framework coverage** — the corpus exercises `SR_26_2`, `NAIC_AIS`,
   `EU_AI_ACT_ART_9`, and `ASOP_56`; `GDPR_ART_22` is under-sampled. Add a
   GDPR-relevant scenario when the live baseline is calibrated.
4. **SQL executability fairness** — the live SQL test passes a
   `DataSourceInventory` introspected from the seeded schema
   (`pc_inventory_from_db`) so the model can name real tables; executability is
   meaningless without it.
