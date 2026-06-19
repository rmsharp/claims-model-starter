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

## Decision (Session 165): **NO-GO — keep `anthropic` primary; harness not yet trustworthy**

The **Anthropic baseline was measured for the first time** this session
(`ANTHROPIC_API_KEY` from `.env`; `bedrock` skipped — no AWS creds). The decision
is still **NO-GO**, for two reasons: (1) `bedrock` is unmeasured, so the candidate
cannot be certified; and (2) more importantly, **the incumbent `anthropic` itself
fails 5 of 8 thresholds** — and the failures are dominated by *harness/corpus*
artifacts, not model quality. A first baseline whose own incumbent fails is the
calibration signal doing its job: **the gate is structurally complete but not yet
operationally trustworthy.** Thresholds therefore stay **proposed** — they were
**not** lowered to match a broken harness (that would be calibrating to noise).
See "Baseline findings" below for the per-metric diagnosis and the harness-fix
follow-ups that must land before a real cutover decision is meaningful.

**Update — Session 170 (2026-06-18): live re-measurement after the S167/S168/S169 fixes.**
The Anthropic baseline was re-measured live this session. Two capabilities that
were harness/corpus artifacts at S165 now measure **PASS**: `qc_structural`
**66.7%→100%** (the gap #3 `max_tokens` truncation fix, S167) and
`interview_convergence` **0%→100% (20/20)** (the gap #1b scorer fix S168 + the
gap #1c N≥5-sampling fix S169) — convergence was confirmed twice, by `shadow_run`
(100%, 0 premature) and by a clean `test_live_interview_converges` pass. The
incumbent now fails **3/8** (was 5/8): `sql_exec` 60% (gap #4) and the two
governance rows (gap #2). **The decision stays NO-GO** — `bedrock` is still
unmeasured (no AWS creds) and the governance + SQL-exec gaps remain open.
*Robustness residual surfaced (S170) → **RESOLVED (Session 171)**:* one of three
S170 gate runs aborted on a network `anthropic.APITimeoutError` — a
transport-timeout transient the gap #1c sweep did **not** classify
(`_TRANSIENT_ERRORS` then covered only `IntakeLLMError`/`StakeholderSimError`);
the convergence rate was unaffected (a clean re-run passed). **Session 171 added
`anthropic.APITimeoutError`/`APIConnectionError` to `_TRANSIENT_ERRORS`** so a
network blip is retried-then-excluded like any seam blip rather than aborting the
gate; `APIStatusError` (4xx/5xx) is a sibling, not a subclass, so a real API
error (bad model id, auth, rate limit) still propagates loudly. Pinned by 4
deterministic tests (no live run).

**Update — Session 174 (2026-06-19): governance re-measured under the faithful (S173) metric; references SME-ratified UNCHANGED.**
A governance-only live re-measure (anthropic, N=5/case, n=20) under the faithful
per-label metric: **cycle_time agreement 50% (FAIL ≥ 90%), risk_tier acceptable
75%, laxer misses 5 (FAIL).** The faithfulness fix worked — it cleared the 3
stricter-direction false-failures and isolated **two genuine signals**, which the
operator (blessing authority) ruled on: (1) **`fraud_triage` laxer miss = a
model-quality signal, NOT a reference defect** — the live model rates a
consumer-facing fraud-routing model `tier_2_high` (citing the human-in-the-loop
SIU gate) where the governance-correct tier is `tier_1_critical`; the reference is
**kept** (the prompt's own "be conservative, pick the stricter tier" rule favours
tier_1), so the model is **under-rating a critical case**. (2) **cycle_time 50% =
a prompt-definition gap** — both misses (`fraud_triage` `operational` vs ref
`continuous`; `reserving_adequacy` `tactical` vs ref `operational`) stem from
`SYSTEM_GOVERNANCE` listing the bare `cycle_time` vocabulary with **no
definitions**; the references are **kept** and a prompt-vocab-definition change is
queued (`BACKLOG.md`, a separate `src/` deliverable). The systematic
stricter-`risk_tier` disagreements (subrog/pricing/reserving) are credited by the
faithful metric (informational; references kept). **All 4 references ratified
unchanged; no corpus change.** Decision stays NO-GO.

**Update — Session 175 (2026-06-19): `cycle_time` cadence vocabulary defined in `SYSTEM_GOVERNANCE` → governance now PASSES both metrics.**
The S174 prompt-definition gap (BACKLOG item 1) is closed: four boundary
definitions (`strategic`/`tactical`/`operational`/`continuous`), grounded in the
ratified reference rationales, were added O4-compliantly (a `CYCLE_TIME_DEFINITIONS`
dict derived-in-order from the `CycleTime` `Literal` + an import-time parity guard;
the verbatim-enumeration pin preserved). **Live re-measure (anthropic, N=5/case,
n=20): cycle_time agreement 50%→100%, risk_tier acceptable 75%→100%, laxer 5→0.**
All four cases now classify their reference cadence exactly (`fraud_triage`→
`continuous`, `reserving_adequacy`→`operational` both corrected); no regression on
the others. **Side effect:** defining `continuous` as "real-time/streaming per-event
at first notice of loss" also flipped `fraud_triage`'s `risk_tier`
`tier_2_high`→`tier_1_critical` (laxer miss resolved) — the richer cadence context
heightened the model's risk perception, **incidentally closing the S174
model-under-rating signal (BACKLOG item 2) in this run** (5/5; a single N=5 run —
confirm stability before formally closing item 2). **The governance capability now
passes both §3.4 metrics; the incumbent fails 1/8** (only `sql_exec` 60%, gap #4).
Decision stays NO-GO (`sql_exec` + `bedrock` unmeasured). *Validation scope (S175
adversarial review): the definitions are confirmed on the 4 corpus cases, where
cadence is co-linear with frequency — so the intended `tactical`/`operational`
role-distinction is not yet exercised by a role≠frequency case, and there is no
member for event-driven (episodic) cadences. Queued to harden (`BACKLOG.md`).*

### Agreement table

Re-measured live **2026-06-18 (Session 170)** via [`tests/eval/shadow_run.py`](shadow_run.py)
(governance and interview sampled N≥5 and pooled; SQL/QC one pass per case);
`bedrock` PENDING (no AWS creds). This run lands the §3.4 numbers after the
S167 (gap #3), S168 (gap #1b) and S169 (gap #1c) fixes: **`qc_structural`
66.7%→100% and `interview_convergence` 0%→100% both flipped to PASS**, so the
incumbent now fails **3/8** (was 5/8) — the three remaining failures are the
pre-existing governance (gap #2) and SQL-exec (gap #4) gaps. (The prior S165
single-pass baseline is preserved in "Baseline findings" below.)

<!-- Regenerate after a live run: feed the per-capability rates to
  eval_cutover.evaluate_cutover and render_agreement_report — see §"Filling this report". -->

| Capability | Metric | Threshold | anthropic (baseline) | bedrock (candidate) |
| --- | --- | --- | --- | --- |
| Any JSON method | parse via both _extract_json copies (deterministic: test_llm_json_parity, not live tier) | ≥ 99% | 100.0% (PASS) | — (PENDING) |
| generate_primary_queries | SQL parse-valid | ≥ 100% | 100.0% (PASS) | — (PENDING) |
| generate_primary_queries | SQL executable on the seeded P&C schema | ≥ 95% | 60.0% (FAIL) | — (PENDING) |
| classify_governance | cycle_time exact agreement vs reference (S173: scored per-label) | ≥ 90% | 100% (PASS, S175) | — (PENDING) |
| classify_governance | risk_tier laxer-tier misses (less strict than ref; stricter allowed) | ≤ 0 | 0 (PASS, S175) | — (PENDING) |
| generate_quality_checks | outer array length == #primary queries | ≥ 100% | 100.0% (PASS) | — (PENDING) |
| Intake interview | believe_enough_info within the 20-question cap | ≥ 95% | 100.0% (PASS) | — (PENDING) |
| Intake interview | premature convergences | ≤ 0 | 0 (PASS) | — (PENDING) |

- **bedrock: PENDING** — Undecided — keep anthropic primary until measured.

## Baseline findings (Session 165) — artifact vs signal

The incumbent fails 5/8. Each failure is classified as a **harness/corpus
artifact** (must be fixed before the metric is meaningful) or a **genuine signal**:

| Metric | Result | Class | Diagnosis |
| --- | --- | --- | --- |
| json_parse | 100% PASS | — | Deterministic parity battery; the shared `_extract_json` parsers handle the corpus. Genuine pass. |
| sql_parse | 100% PASS | — | All generated primary SQL parses. Genuine pass. |
| sql_exec | 60% FAIL | signal (needs diagnosis) | 3/5 generated queries execute on the seeded schema; 2 reference unavailable columns / shape. Could be model SQL *or* an incomplete seed schema — inspect which queries failed before judging. |
| governance_cycle_time_agreement | 0%→50%→**100% PASS** (S173 fix → S174 re-measure → S175 vocab) | **FIXED (S175)** | The former exact-*both* metric scored 0% (an artifact: it counted prompt-instructed stricter `risk_tier` as disagreement). **S173** made the metric faithful; **S174** re-measured (50%) and traced the two misses (`fraud_triage`→`continuous`, `reserving_adequacy`→`operational`) to a **prompt-definition gap** (`SYSTEM_GOVERNANCE` listed the bare `cycle_time` vocab with no definitions; references ratified unchanged). **S175 defined the cadence vocab** (O4-compliant glossary + parity guard) → re-measure **100%** (all 4 cases classify their reference cadence exactly). |
| governance_laxer_miss | 5→**0 PASS** (S175) | **FIXED (side effect, S175)** | Was driven by **one** case — `fraud_triage`: model `tier_2_high` vs ref `tier_1_critical` (laxer) × 5; **S174 SME ruling: reference correct (kept `tier_1_critical`), the model under-rates a consumer-facing fraud model** — a model-quality signal. **S175 resolved it as a side effect:** defining `continuous` = real-time/streaming per-event at FNOL flipped `fraud_triage`'s tier `tier_2`→`tier_1` (laxer → 0) — the richer cadence context heightened the model's risk perception. Single N=5 run; confirm before formally closing BACKLOG item 2. The other 3 cases erred *stricter* — credited by the S173 fix. |
| qc_structural | 66.7% FAIL → fixed (S167) | signal (FIXED) | One case (`tx_auto_training`) hit `max_tokens=4096` → truncated, non-JSON, no retry (Trap 5). **Session 167 fixed it** (gap #3): the default cap is raised to 16384 and a `stop_reason='max_tokens'` guard raises an actionable error instead of a cryptic parse failure. Verified live — `tx_auto_training` returns 3 groups / 29 checks, no truncation. **Confirmed live S170: 100% PASS** (re-measured shadow run). |
| interview_convergence | 0% FAIL | **artifact (fixed S166)** | S165: all four raised "model asked for more answers than the script supplies" — the scripted-replay caveat (`PROJECT_LEARNINGS` #21). **Session 166 fixed it** (a robust stakeholder simulator answers whatever the live model asks; verified live — the interviewer asks 9–10 questions vs the 7–10 recorded, no exhaustion). Still 0% live, but now for *downstream* reasons, not the replay artifact: (a) ~~the draft JSON truncates at `max_tokens`~~ **fixed S167 (gap #3)** — the draft now completes at the 16384 default (verified live, no truncation); (b) ~~at adequate `max_tokens`, the rigorous live interviewer drafts a non-empty `missing_fields` list the fixtures don't pre-answer → `DRAFT_INCOMPLETE`~~ **fixed S168 (gap #1b)** — the root cause was a scorer/metric mismatch (the scorer keyed on `status==COMPLETE`/report-finalization, stricter than the §3.4 text "`believe_enough_info` within the cap"); the scorer is now aligned to the metric text (`interview_converged` = `questions_cap_reached not in missing_fields`), a faithfulness fix, **not** a #129 loosening. **Measured live S168: 0% → 75%** (`[T,T,T,F]`, 3/4) — the fix unblocks convergence but the gate is **still RED** (3/4 < 95%); the one miss (`reserving_adequacy`) converges in isolation (q=9, no cap) so the residual is **gate fragility** (4 samples @ 95% needs 4/4; stochastic model + transient-seam-as-False), not a scorer/capability defect. **Session 169 fixed the fragility** (gap #1c: N≥5 sampling + transient-seam retry/exclude) and **Session 170 confirmed it live: 100% (20/20)** — both `shadow_run` and a clean `test_live_interview_converges` pass. See Gap list #1b/#1c. |
| interview_premature | 0 PASS | — | Trivially clean — none converged (so none converged *prematurely*). Only meaningful once convergence works. |

**Bottom line:** before the §3.4 gate can drive a real cutover decision, the
harness needs (in rough priority) the interview convergence-metric calibration
(gap #1b), SME re-validation of the governance references (the governance *metric*
was made faithful S173 — score per-label, credit stricter `risk_tier`), and a look
at the 2 non-executing SQL queries.
(Interview-answer robustness landed S166; the `max_tokens` truncation landed
S167.) A fresh baseline run will re-measure `qc_structural` now that its
truncation is fixed. Until then the baseline numbers measure the *harness*, not
the *providers*.

## How to run the shadow run

The **driver** [`tests/eval/shadow_run.py`](shadow_run.py) is the way to produce
this report: it measures every provider whose credentials are present (the others
skip), prints each provider's per-capability rates, and renders the agreement
table directly. It *records* failures (a parse error counts as a missed rate)
rather than asserting, so a sub-threshold result is data, not a crash:

```bash
# Measures whichever providers have creds; prints rates + the agreement table:
ANTHROPIC_API_KEY=… AWS_PROFILE=… uv run python tests/eval/shadow_run.py   # both
ANTHROPIC_API_KEY=…                uv run python tests/eval/shadow_run.py   # baseline only
```

The **assert-based** tier (`uv run pytest -m live tests/eval/ -rs`) is the
same corpus with the §3.4 thresholds enforced as test assertions — useful as a
pass/fail gate once the harness is trustworthy, but it does not emit the rates
this report needs (use the driver for those).

Each capability is sampled N ≥ 5 times (governance and interview; gap #1c) and
judged on a pass-*rate* + structural invariants (§3.4 non-determinism handling);
the interview sweep also retries/excludes a transient API/sim error rather than
scoring it a non-convergence (`interview_sweep.py`). `model=None` is passed so
each provider uses its native default id (Bedrock gets the `anthropic.`-prefixed
default — no cross-provider 400).

### Filling this report from a live run

`shadow_run.py` prints the measured rates **and** the rendered agreement table —
paste its table into "Agreement table" above and record the measured
`(provider, model)`. The eight gate keys (`eval_cutover.CHECK_KEYS`) come from two
sources, which the driver already handles:

- **Seven live-tier metrics** — `sql_parse`, `sql_exec`, `governance_cycle_time_agreement`,
  `governance_laxer_miss`, `qc_structural`, `interview_convergence`,
  `interview_premature`: measured by the driver against the live provider.
- **One deterministic metric** — `json_parse`: **not** a live rate. §3.4's oracle
  is the provider-parametrized parity battery (`test_llm_json_parity.py`, which
  covers every registered `(seam, provider)` parser incl. `bedrock`); the driver
  records **`1.0`** since both providers reuse the shared `_extract_json` parsers
  (confirm with `uv run pytest tests/test_llm_json_parity.py -q`). A real-output
  parse failure surfaces instead as a *live-capability* miss (they raise on
  unparseable provider JSON — and the driver counts that as a failed rate).

If the **baseline** fails a threshold, do **not** reflexively lower it — first
decide whether the failure is a harness/corpus artifact (see "Baseline findings")
or a genuine signal. To assemble a decision from partial/edited numbers manually:

```python
from tests.eval.eval_cutover import evaluate_cutover, render_agreement_report
# Every CHECK_KEYS entry must be present (a missing key reads as PENDING):
measured = {
    "anthropic": {
        "json_parse": 1.0, "sql_parse": 1.0, "sql_exec": 0.97,
        "governance_cycle_time_agreement": 0.95, "governance_laxer_miss": 0,
        "qc_structural": 1.0, "interview_convergence": 0.96, "interview_premature": 0,
    },
    "bedrock": {
        "json_parse": 1.0, "sql_parse": 1.0, "sql_exec": 0.96,
        "governance_cycle_time_agreement": 0.92, "governance_laxer_miss": 0,
        "qc_structural": 1.0, "interview_convergence": 0.95, "interview_premature": 0,
    },
}
decisions = {p: evaluate_cutover(p, m) for p, m in measured.items()}
print(render_agreement_report(decisions))
```

Paste the rendered table above and update the decision line. **Only** adjust a
threshold in `eval_thresholds.py` once you've confirmed the baseline miss is a
genuine "threshold too strict" (not a harness/corpus artifact per "Baseline
findings") — and note the change and its rationale here.

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

**Harness-trustworthiness fixes (must land before the gate can decide a cutover —
see "Baseline findings" for the diagnosis), in rough priority:**

1. **Interview-answer robustness — DONE (Session 166).** The scripted-replay
   `StopIteration` artifact (#21) is fixed: `IntakeAgent.run_scripted` gained an
   `answer_provider` seam, and `tests/eval/stakeholder_sim.py` answers whatever the
   live model asks from the fixture's full knowledge. Verified live (anthropic):
   the interviewer asks 9–10 questions vs the 7–10 recorded and never runs out.
   **Convergence was still 0% after this fix (at S166)**, then blocked by two
   *new* (separately-tracked) follow-ups surfaced by the fix — neither an
   answer-robustness gap, **both since RESOLVED (see 1a/1b); convergence is now
   live-GREEN at 100% (20/20), Session 170**:
   - **1a. Draft `max_tokens` truncation — DONE (Session 167, gap #3).** The
     intake `draft_report` JSON now completes at the 16384 default (verified
     live, no truncation). Only 1b remains on the convergence critical path.
   - **1b. Scorer/metric faithfulness — RESOLVED (Session 168); live gate GREEN (Session 170, via gap #1c).** Diagnosis (three
     independent reads + an adversarial check) found the root cause was *not*
     fixture depth but a **scorer/metric mismatch**: `interview_converged` keyed on
     `report.status == "COMPLETE"` — i.e. *report finalization* (`finalize` sets
     `COMPLETE` only when review is `accepted` **and** `missing_fields` is empty,
     `nodes.py:154`) — while the §3.4 row is *defined* as "`believe_enough_info`
     within the 20-question cap" (`eval_cutover.py:132`, `README.md:117`). The model
     satisfied the metric (believed enough at q≈10) yet the report stayed
     `DRAFT_INCOMPLETE` because it honestly drafted a populated `missing_fields` list
     (formal governance review, fairness scope, exact baseline figures, cost, IT
     feasibility, privacy retention, EDW availability) the fixtures don't pre-answer.
     **Operator-chosen fix (AskUserQuestion): align the scorer to the metric text** —
     `interview_converged` now returns `"questions_cap_reached" not in missing_fields`
     (which exactly encodes "believed enough within the cap", since `finalize`
     appends that marker iff the cap was hit *without* `believe_enough_info`), and
     `premature_convergence` is reconciled to the **same** convergence signal so a
     q=1 converge-and-bail can't slip past the guard. This is a **faithfulness fix,
     not a #129 loosening** — the adversarial verdict confirmed the scorer was
     *stricter than its own documented metric*; #129 forbids loosening a *faithful*
     scorer, which this was not. The §3.4 metric text was already correct, so no
     doc-text change was needed; report finalization remains a distinct concern (it
     could become its own future §3.4 row). Pinned by 6 new deterministic scorer
     tests (`test_eval_scoring.py`). *Note:* `accepted` defaults to `True` in
     shadow/live runs (`review_sequence_from_fixture` → `["ACCEPT"]`,
     `fixture.py:139`), so the prior handoff's "fixture enrichment" lever would also
     have been viable, but the faithfulness fix is surgical and provider-independent.
     **Measured live (anthropic, S168):** `test_live_interview_converges` moved
     **0% → 75%** (`[T,T,T,F]`, 3/4) — the fix is confirmed to be what unblocks
     convergence, but 3/4 < the 95% threshold so the gate is **still RED**. A
     one-fixture diagnostic on the failing case (`reserving_adequacy`, the 4th)
     showed it **converges in isolation** (`status=DRAFT_INCOMPLETE`,
     `questions_asked=9`, `questions_cap_reached` absent → scorer `True`), so the
     residual is **not** that case being a hard non-converger. **gap #1c — live
     gate fragility — RESOLVED (harness fix; Session 169):** the convergence gate
     used to run each of the 4 fixtures *once* and `pass_rate` over 4 booleans at a
     95% bar (so passing required **4/4**), and a transient seam `RuntimeError` was
     scored as a non-convergence — so one stochastic miss or API blip failed the
     gate. **Fix (operator chose A+B via `AskUserQuestion`):** a shared helper
     `interview_sweep.sweep_interview_convergence` now (a) samples each converging
     fixture `N_SAMPLES`≥5 times and pools the pass-rate, matching the governance
     tier, and (b) classifies a transient API/sim error (`IntakeLLMError`,
     `StakeholderSimError`) as retry-bounded/excluded rather than a non-convergence,
     while a genuine non-convergence (a returned report carrying
     `questions_cap_reached`) is still scored `False` and any other `RuntimeError`
     (a real harness/graph bug) propagates loudly. Both call sites
     (`test_eval_live.py`, `shadow_run.py`) go through the one helper; the **95%
     threshold is unchanged** — a harness-statistics fix, **not** a #129 loosening
     (4 adversarial read-only lenses confirmed). Pinned by 12 deterministic tests
     (`test_interview_sweep.py`, no API key). **Measured live — RESOLVED (Session
     170):** `interview_convergence` clears the 95% bar at **100% (20/20)**,
     confirmed twice — by `shadow_run.py` (100%, 0 premature) and by a clean
     `test_live_interview_converges` pass. The 3 transient `IntakeLLMError` blips in
     the shadow run were retried and recovered (0 exclusions), exactly as the fix
     intends. **Transport-timeout residual — RESOLVED (Session 171):** one of three
     S170 gate runs aborted on a network `anthropic.APITimeoutError` — a
     transport-timeout transient the sweep's `_TRANSIENT_ERRORS` (`IntakeLLMError`,
     `StakeholderSimError`) did **not** classify, so it propagated raw (un-wrapped
     by `_call_json`, `anthropic_client.py:286`) and aborted the gate. The
     convergence rate was unaffected (a clean re-run passed). **Fix (Session 171,
     tuple-add):** `anthropic.APITimeoutError`/`APIConnectionError` are now in
     `_TRANSIENT_ERRORS`, so a network blip is retried (bounded) then **excluded**
     with a note like any seam blip — it no longer aborts the gate. `APIStatusError`
     (4xx/5xx — bad model id, auth, rate limit) is a *sibling* of
     `APIConnectionError`, **not** a subclass, so a real API error still propagates
     loudly (FM #18). The `_call_json` seam-wrap alternative was rejected: it would
     conflate a transport error (no response) with `IntakeLLMError` (a response that
     could not be parsed) and only helps the data agent if its separate client is
     also touched (out of scope). Pinned by 4 new deterministic tests in
     `test_interview_sweep.py` (`_MAX_TRANSIENT_RETRIES`/threshold unchanged, #129).
2. **Governance references + metric + vocab — RESOLVED (S173 → S174 → S175); governance now PASSES.**
   **S173** made the agreement metric faithful (per-label; credit stricter
   `risk_tier`; thresholds unchanged — not a #129 loosening). **S174** re-measured
   (cycle_time 50%, laxer 5), ratified all 4 references unchanged, and routed the
   two residuals to their owners: a `cycle_time` prompt-definition gap + a
   `fraud_triage` model-under-rating. **S175** defined the `cycle_time` cadence
   vocabulary in `SYSTEM_GOVERNANCE` (O4-compliant glossary + parity guard) →
   re-measure **cycle_time 100%, laxer 0** (the `continuous` definition incidentally
   flipped `fraud_triage` `tier_2`→`tier_1`, closing the under-rating too). The
   governance capability now passes both §3.4 metrics in the N=5 re-measure.
   **Residual:** confirm the `fraud_triage` `tier_1` result is stable across a
   larger sample before formally closing (BACKLOG item 2). The overall Phase E
   decision is still NO-GO on `sql_exec` (#4) + unmeasured `bedrock`.
3. **`max_tokens` truncation on large JSON output — DONE (Session 167).**
   `generate_quality_checks` truncated for the large `tx_auto_training` case
   (S165), and (Session 166) the intake `draft_report` truncated too — at
   `max_tokens=4096` the draft hit `stop_reason=max_tokens` (`output_tokens=4096`),
   leaving an unclosed ```json fence → `IntakeLLMError`, blocking every interview
   from a parseable draft (same root cause; no retry — Trap 5). **Fixed:**
   `DEFAULT_MAX_TOKENS` raised 4096→16384 in both `AnthropicLLMClient`s (bedrock
   inherits) and an explicit `stop_reason=='max_tokens'` guard now raises an
   actionable error *before* parsing — no silent partial-JSON parse, no retry,
   and the prefill-continuation option is ruled out (`claude-sonnet-4-6` 400s on
   last-assistant-turn prefills). Verified live at the new default: `draft_report`
   completes (no truncation) and `generate_quality_checks` on `tx_auto_training`
   returns 3 groups / 29 checks. Unblocked both `qc_structural` and the
   interview-convergence Layer 2 (#1a).
4. **SQL executability** — 2/5 generated queries don't execute on the seeded
   schema; inspect which (model SQL vs incomplete seed schema).

**Still open from earlier phases:**

5. **`bedrock` candidate unmeasured** — no AWS creds; run the Bedrock half to
   complete the comparison (the `anthropic` baseline is now measured).
6. **Thresholds remain proposed** — the baseline did **not** calibrate them
   (failures were harness artifacts, not too-strict thresholds). Re-run once the
   harness fixes above land; only then is "Anthropic clears its own bar" a valid
   calibration check.
7. **`GDPR_ART_22` under-sampled** in the governance corpus (`README.md` §Caveats).
8. **CLI provider defaults are hardcoded** — `run_pipeline.py` / data-agent
   `cli.py` do not read `DEFAULT_LLM_PROVIDER`; a cleaner cutover would route both
   through it. Out of scope here (no production edits); noted for a follow-up.
9. **The model-id gap** (cutover table) remains open for `run_pipeline.py`.
