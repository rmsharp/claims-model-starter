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

### Agreement table

Measured single-run baseline (governance sampled N=5; the rest one pass) via
[`tests/eval/shadow_run.py`](shadow_run.py); `bedrock` PENDING (no AWS creds).

<!-- Regenerate after a live run: feed the per-capability rates to
  eval_cutover.evaluate_cutover and render_agreement_report — see §"Filling this report". -->

| Capability | Metric | Threshold | anthropic (baseline) | bedrock (candidate) |
| --- | --- | --- | --- | --- |
| Any JSON method | parse via both _extract_json copies (deterministic: test_llm_json_parity, not live tier) | ≥ 99% | 100.0% (PASS) | — (PENDING) |
| generate_primary_queries | SQL parse-valid | ≥ 100% | 100.0% (PASS) | — (PENDING) |
| generate_primary_queries | SQL executable on the seeded P&C schema | ≥ 95% | 60.0% (FAIL) | — (PENDING) |
| classify_governance | exact label agreement (cycle_time AND risk_tier) vs reference | ≥ 90% | 0.0% (FAIL) | — (PENDING) |
| classify_governance | laxer-tier misses (predicted strictly less strict than reference) | ≤ 0 | 5 (FAIL) | — (PENDING) |
| generate_quality_checks | outer array length == #primary queries | ≥ 100% | 66.7% (FAIL) | — (PENDING) |
| Intake interview | believe_enough_info within the 20-question cap | ≥ 95% | 0.0% (FAIL) | — (PENDING) |
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
| governance_agreement | 0% FAIL | **artifact** | `risk_tier` mismatched on all 4 cases, `cycle_time` on 2/4 → exact-both = 0. The rule-derived reference labels (single-SME-ratified, S161) **systematically disagree with live-model output**; the "exact match of *both* closed-vocab labels ≥ 90%" metric is unachievable even by the incumbent. Needs SME re-validation of the references against live output and/or a less brittle metric (score the two labels separately; credit stricter-direction mismatches). |
| governance_laxer_miss | 5 FAIL | mixed | Driven by **one** case — `fraud_triage`: model `tier_2_high` vs ref `tier_1_critical` (laxer) × 5 samples. Either the model under-rates a critical case (genuine, concerning) or the reference is too strict — an SME call. The other 3 cases erred *stricter* (allowed). |
| qc_structural | 66.7% FAIL | signal (fixable) | One case (`tx_auto_training`) hit `max_tokens=4096` → truncated, non-JSON, no retry (Trap 5). Raise/handle max_tokens for large QC output, or chunk it. |
| interview_convergence | 0% FAIL | **artifact (fixed S166)** | S165: all four raised "model asked for more answers than the script supplies" — the scripted-replay caveat (`PROJECT_LEARNINGS` #21). **Session 166 fixed it** (a robust stakeholder simulator answers whatever the live model asks; verified live — the interviewer asks 9–10 questions vs the 7–10 recorded, no exhaustion). Still 0% live, but now for *downstream* reasons, not the replay artifact: (a) the draft JSON truncates at `max_tokens` (the same root cause as qc_structural / gap #3 — `stop_reason=max_tokens` at 4096); (b) at adequate `max_tokens`, the rigorous live interviewer drafts a non-empty `missing_fields` list the fixtures don't pre-answer → `DRAFT_INCOMPLETE`. See Gap list #1. |
| interview_premature | 0 PASS | — | Trivially clean — none converged (so none converged *prematurely*). Only meaningful once convergence works. |

**Bottom line:** before the §3.4 gate can drive a real cutover decision, the
harness needs (in rough priority) a robust interview-answer strategy, SME
re-validation of the governance references + a less brittle governance metric, a
max_tokens fix for QC generation, and a look at the 2 non-executing SQL queries.
Until then the baseline numbers measure the *harness*, not the *providers*.

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

Each capability is sampled N ≥ 5 times (governance) and judged on a pass-*rate* +
structural invariants (§3.4 non-determinism handling); `model=None` is passed so
each provider uses its native default id (Bedrock gets the `anthropic.`-prefixed
default — no cross-provider 400).

### Filling this report from a live run

`shadow_run.py` prints the measured rates **and** the rendered agreement table —
paste its table into "Agreement table" above and record the measured
`(provider, model)`. The eight gate keys (`eval_cutover.CHECK_KEYS`) come from two
sources, which the driver already handles:

- **Seven live-tier metrics** — `sql_parse`, `sql_exec`, `governance_agreement`,
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
   **Convergence is still 0%**, now blocked by two *new* (separately-tracked)
   follow-ups surfaced by the fix — neither an answer-robustness gap:
   - **1a. Draft `max_tokens` truncation** — see #3 (it hits the intake
     `draft_report` JSON, not only QC).
   - **1b. Live-interviewer rigor vs. fixture depth / metric semantics** — at
     adequate `max_tokens` the model conducts a thorough ~10-question interview but
     drafts a populated `missing_fields` list (formal governance review, fairness
     scope, exact baseline figures, implementation cost, IT feasibility, privacy
     retention, EDW availability) the fixtures don't pre-answer → `DRAFT_INCOMPLETE`.
     Note the scorer requires `status==COMPLETE`, **stricter** than the §3.4 metric
     text ("`believe_enough_info` within the cap", which the model *did* satisfy at
     q=10). Resolving the rate needs an SME/operator calibration call (richer
     fixtures, simulator forthcomingness, and/or the convergence metric) — **do not
     loosen the scorer to chase a number** (Candidate #129).
2. **Governance references + metric** — the rule-derived reference labels
   disagree with live-model output (0% exact agreement). SME-re-validate the
   references against live output, and reconsider the brittle "exact-both-labels"
   metric (score `cycle_time`/`risk_tier` separately; credit stricter-direction
   mismatches). The `fraud_triage` laxer-miss (`tier_2_high` vs ref
   `tier_1_critical`) needs an explicit SME ruling.
3. **`max_tokens` truncation on large JSON output** — broader than first thought.
   `generate_quality_checks` truncates for the large `tx_auto_training` case
   (S165); and (Session 166) the intake `draft_report` truncates too — at
   `max_tokens=4096` the draft hit `stop_reason=max_tokens` (`output_tokens=4096`),
   leaving an unclosed ```json fence → `IntakeLLMError`, blocking every interview
   from a parseable draft. Same root cause (no retry — Trap 5). Raise/handle
   `max_tokens`, add a continuation/retry on truncation, or chunk the output. This
   is now on the critical path for interview convergence (#1a).
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
