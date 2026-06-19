# Bedrock Testing Enablement — Operator Runbook & Cost Estimate

**Session 178 · 2026-06-19 · Status: planning doc (no code change)**

## Why this exists

Every "GREEN" in this project's Phase E evaluation is **anthropic-only**. The eval
harness is parametrized over two providers — `("anthropic", "bedrock")`
(`tests/eval/eval_cutover.py:34-38`) — but the `bedrock` half has been **unmeasured
since Session 161** because no AWS credentials are present. When creds are absent the
live-tier collection hook (`tests/eval/conftest.py:47-60` →
`eval_cutover.provider_creds_available("bedrock")`) **silently skips** every bedrock
test. `PHASE_E_AGREEMENT_REPORT.md:413` records it: *"bedrock candidate unmeasured —
no AWS creds; run the Bedrock half to complete the comparison."*

Phase E stays **NO-GO** partly because of this gap. This doc is what the **operator**
must do to close it, and what it will cost.

> ⚠️ **Everything below is an a-priori estimate.** Bedrock has *never* run live in this
> project, so there is no measured bedrock bill to anchor on. Numbers are modeled from
> the code's call graph + current list pricing, with ranges.

---

## How the project reaches Bedrock (verified from code)

| Fact | Value | Evidence |
|------|-------|----------|
| Bedrock client | `anthropic.AnthropicBedrock()` wrapper | `src/.../agents/intake/bedrock_client.py:83-86` |
| Default model (bedrock) | **`anthropic.claude-sonnet-4-6`** ($3 in / $15 out per M tok) | `bedrock_client.py:56` |
| Provider selection | explicit: `make_llm_client(provider="bedrock")` / `--provider bedrock` / `INTAKE_LLM_PROVIDER=bedrock`; default is `anthropic` | `factory.py:37-76` |
| Env vars read | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION` (+ `AWS_PROFILE` alt) | `bedrock_client.py:36,40` |
| Region fallback | client falls back to `AWS_REGION`; boto3 itself reads `AWS_DEFAULT_REGION` | `bedrock_client.py:40` |
| Why skipped today | creds absent → `provider_creds_available("bedrock")` false → live tests auto-skip | `conftest.py:47-60`, `eval_cutover.py:52-59` |

---

## What you (the operator) must do

These are **one-time** unless noted. Steps 1–4 are yours; step 5 is a verification you
run before trusting any test result.

### 1. Pick a region (one-time)
Choose a US region where Sonnet 4.x is offered — **`us-east-1`** is the safe default.
This becomes `AWS_REGION` / `AWS_DEFAULT_REGION`. Model availability differs by region;
confirm on the model's detail page in the Bedrock console.

### 2. Request **model access** for Anthropic Claude (one-time, per region)
Bedrock console **in that region** → *Bedrock configurations → Model access → Modify
model access* → select the Anthropic Claude models → Next.
- **First Anthropic use requires a one-time "use case details" form** (company name,
  website, intended users, industry, use case). The console prompts for it. This is the
  step you must not skip.
- Current AWS docs say access is granted **immediately** on form submission, but it has
  historically sometimes shown *"In progress"* for minutes–hours. **Don't schedule the
  test run assuming instant** — verify with step 5 first.

### 3. Create an IAM identity + access keys (one-time)
IAM → Users → create a programmatic-only user (e.g. `mpc-bedrock-invoker`). Attach the
minimal policy below. Then *Security credentials → Create access key →* "Application
running outside AWS". **Copy the secret immediately — it's shown once.**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "InvokeClaudeOnBedrock",
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": [
        "arn:aws:bedrock:*::foundation-model/anthropic.claude-*",
        "arn:aws:bedrock:*:ACCOUNT_ID:inference-profile/us.anthropic.claude-*",
        "arn:aws:bedrock:*:ACCOUNT_ID:inference-profile/global.anthropic.claude-*"
      ]
    }
  ]
}
```
*(Replace `ACCOUNT_ID`. If scoping fights you, widen `Resource` to `"*"` for the two
actions as a first step, then tighten. The first invocation may need the model enabled
in the account via the console (step 2) — the minimal policy omits
`aws-marketplace:Subscribe` on purpose.)*

### 4. Put the creds in the project `.env` (per machine)
Copy `.env.example` → `.env` (git-ignored) and add:
```
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1
AWS_DEFAULT_REGION=us-east-1
```
**Critical:** this project does **not** auto-load `.env` into pytest. Export it first:
```
set -a; . ./.env; set +a
```
If you skip this, every bedrock live test **silently skips** — a green run can mean
"never ran," not "passed."

### 5. Verify access *before* running the suite (each session)
```
set -a; . ./.env; set +a
aws sts get-caller-identity                     # keys load?
aws bedrock get-foundation-model-availability \  # access granted in region?
  --model-id anthropic.claude-sonnet-4-6 --region us-east-1
# real invocation (prefer the inference-profile id):
aws bedrock-runtime converse --region us-east-1 \
  --model-id us.anthropic.claude-sonnet-4-6 \
  --messages '[{"role":"user","content":[{"text":"ping"}]}]'
```
Only once a real invocation returns text should you run the eval suite.

---

## 💥 Here be dragons (read before spending)

1. **Inference-profile-only models (highest risk).** Many Claude 4.x models on Bedrock
   **cannot be invoked by the bare id** `anthropic.claude-sonnet-4-6` — they return
   `ValidationException: ...on-demand throughput isn't supported. Retry with...an
   inference profile.` The fix is the cross-region profile id `us.anthropic.claude-sonnet-4-6`.
   **The project's `bedrock_client.py:56` uses the bare id.** If your region rejects it,
   the bedrock tests will fail until the model id is adjusted — that's a **one-line code
   change (a separate session)**, not an operator task. Step 5's `converse` probe tells
   you which form your account needs *before* you spend a session on it.
2. **Silent skip on missing export** (see step 4) — "all green" ≠ "ran."
3. **Model-access delay** — may not be instant; verify with step 5.
4. **Regional endpoint premium** — since the 4.5 generation, a *regional* endpoint
   (what `AWS_REGION` gives you) costs ~10% more than the *global* inference profile.
   Folded into the high-cost bounds below.

---

## Cost estimates

Three tiers, smallest to largest. **Point** = project default **Sonnet 4.6** ($3/$15
per M tok — same list price on Bedrock as the first-party API). **Low** = Haiku 4.5
($1/$5); **High** = Opus 4.8 ($5/$25) + regional premium + retries. All at the default
**N=5 samples/case**; cost scales ~linearly with N.

| Tier | What it does | Bedrock LLM calls | **Point (Sonnet)** | Range (low–high) |
|------|--------------|------------------:|-------------------:|------------------|
| **Smoke** | 1 classification round-trip — proves creds + model id work | 1 | **~$0.03** | $0.01 – $0.05 |
| **Governance gate** | The §3.4 metric: 5 cases × 5 samples | ~25 | **~$0.94** | $0.31 – $2.23 |
| **Full shadow_run sweep** | Whole corpus: interviews + governance + SQL/QC; the real Phase E comparison | **~731** | **~$25** | $4.76 – $89 |

**Commands**
- Smoke: `uv run pytest tests/agents/intake/test_bedrock_client.py -v` (after step 5 probe)
- Governance gate: `uv run pytest -m live tests/eval/test_eval_live.py::test_live_governance_cycle_time_agreement_and_no_laxer_miss --provider bedrock --no-cov`
- Full sweep: `uv run python tests/eval/shadow_run.py` (runs **both** providers; ~90 min wall-clock on anthropic — bedrock untested)

**Why the full sweep is ~$25, not the $/cents of the others:** it's dominated by
**~731 calls**, because each interview *turn* makes **two** LLM calls — the interviewer's
`next_question` **and** the stakeholder-simulator's reply — across 25 interviews of
~10 turns each, plus draft/revise/classify per interview. (The first-pass research
under-counted this at 175; the verify pass corrected it.) Per-turn token sizes are
**not logged** anywhere in the codebase, so the $25 point is an order-of-magnitude
estimate with a genuinely wide band, not an invoice.

---

## Recommended path

1. **Do steps 1–5** (one-time AWS setup, ~30–60 min of your time; ~$0 until you invoke).
2. **Run the smoke test (~$0.03).** This is the real gate on the *inference-profile-id*
   dragon. If it throws `ValidationException`, stop and open a session to switch
   `bedrock_client.py` to the `us.` profile id — don't burn a sweep on a broken id.
3. **Run the governance gate (~$1).** This alone closes the most-cited §3.4 bedrock gap
   and is the cheapest meaningful comparison.
4. **Run the full shadow_run sweep (~$25)** only when you want the complete Phase E
   provider comparison. Budget ~$25–30 for one clean run; re-runs at higher N scale up.

**Bottom line:** closing the headline bedrock gap costs **~$1 and an afternoon of AWS
setup**; the *complete* Phase E comparison costs **~$25–30 one-time**. The binding risk
is not money — it's the bare-vs-`us.`-prefixed model id (dragon #1), which the $0.03
smoke test flushes out before any real spend.

---

## Decision points for the operator

- **Provide AWS creds at all?** If bedrock is out of scope for the foreseeable future,
  rule it out explicitly so future sessions stop carrying it as an open gap.
- **Which tier to fund?** Smoke + governance (~$1) vs. full comparison (~$25–30).
- **Which model?** The default is Sonnet 4.6. If you want the bedrock comparison to
  mirror the anthropic baseline exactly, keep the default (it already matches).

## Sources
- Code: `bedrock_client.py`, `factory.py`, `conftest.py`, `eval_cutover.py`,
  `shadow_run.py`, `interview_sweep.py`, `stakeholder_sim.py`, `eval_corpus.py`,
  `PHASE_E_AGREEMENT_REPORT.md` (cited inline above).
- AWS: model-access, cross-region-inference, inference-profiles user-guide pages;
  Anthropic Claude on Bedrock model cards; `platform.claude.com/docs/.../pricing`
  (authoritative for the per-token rates — Bedrock on-demand list = first-party list).
- ⚠️ The AWS Bedrock pricing *page* did not render its 4.x rows to the research tool;
  the 4.x Bedrock $ figures are corroborated via model cards + the Anthropic price table
  + secondary trackers, **not** a direct quote from `aws.amazon.com/bedrock/pricing`.
  Confirm exact numbers in the AWS console before any large run.
