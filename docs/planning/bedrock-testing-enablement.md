# Bedrock Testing Enablement — Operator Runbook & Cost Estimate

**Originally Session 178 (2026-06-19). Substantially revised Session 180 (2026-07-18):**
the mantle migration **landed** and live enablement was **attempted end-to-end**. The
pre-mantle IAM/SigV4 guidance in the original revision was **wrong for the current code**
and has been corrected below. The real blocker is now **identified and confirmed live**.

---

## ⛔ Current status (Session 180) — READ FIRST

**The code migration is COMPLETE and unit-verified. Live bedrock testing is BLOCKED on an
AWS-side action — not on code, not on anything the operator can self-serve.**

- **Code (done):** the Bedrock client is now `AnthropicBedrockMantle` (commit `dadf514`),
  default model `anthropic.claude-opus-4-8` (`9e3f19b`), authenticated by a **Bedrock API
  key** (`AWS_BEARER_TOKEN_BEDROCK`) against the mantle Messages endpoint (SigV4 fallback if
  the token is unset). Baseline **916 unit tests + ruff + mypy green**.
- **The blocker (confirmed live — account `868785635769`, `us-east-1`, 2026-07-18):** every
  current-generation Claude model returns
  `403 permission_error: "anthropic.<model> is not available for this account. … contact AWS
  Sales"` **at runtime** — reproduced in the console **Workbench** for both
  `anthropic.claude-opus-4-8` **and** `anthropic.claude-haiku-4-5`. Non-Anthropic models
  (GPT-5.5, Gemma) invoke fine in the same account/region.
- **This is NOT** the Anthropic use-case form, NOT missing IAM/creds/payment, NOT a missing
  model agreement, NOT the wrong region, NOT the inference-profile-id issue. All of those
  are ruled out (see the diagnostic below).
- **What it IS — the control-plane-vs-runtime split.**
  `aws bedrock get-foundation-model-availability --model-id anthropic.claude-opus-4-8
  --region us-east-1` returns **all green**
  (`agreementAvailability=AVAILABLE`, `authorizationStatus=AUTHORIZED`,
  `entitlementAvailability=AVAILABLE`, `regionAvailability=AVAILABLE`) — yet runtime 403s,
  and the console model panel shows **Input TPM 0 (default 20M)**. AWS has **not provisioned
  the backend per-model TPM (tokens-per-minute) runtime quota** for current-gen Claude on
  this account. It is a **usage-history-gated gradual rollout** of the newest Claude models;
  low-Bedrock-usage accounts get it last.
- **The fix — an AWS-side request is the ONLY lever.** Open an AWS technical Support case, or
  use the **"contact AWS Sales"** link the error itself gives
  (`https://aws.amazon.com/contact-us/sales-support/`, accessible on any support plan), and
  ask AWS to **provision the backend runtime entitlement / per-model TPM quota** for the
  current-gen Anthropic Claude models in `us-east-1` on both the `bedrock-mantle` and
  `bedrock-runtime` endpoints. Access also **auto-expands with Bedrock usage** over time.
  **Do NOT run `create-foundation-model-agreement`** — the agreement already shows
  `AVAILABLE`, so it is a no-op and will not clear the runtime gate.
- **Status: `ready-for-human`.** The instant AWS provisions the quota, the existing code
  works with **no further change** — nothing else to build or configure.

### Ready-to-paste AWS request

> **Account:** 868785635769 · **Region:** us-east-1
> **Issue:** Amazon Bedrock returns `403 permission_error: "anthropic.claude-opus-4-8 is not
> available for this account"` at **runtime** (console Workbench, SDK, and the mantle
> endpoint), even though `get-foundation-model-availability` returns
> `agreementAvailability=AVAILABLE, authorizationStatus=AUTHORIZED,
> entitlementAvailability=AVAILABLE, regionAvailability=AVAILABLE`, and the model panel shows
> **Input TPM = 0 (default 20M)**. Non-Anthropic models (GPT-5.5, Gemma) invoke fine.
> **Request:** Please **provision the backend runtime entitlement / per-model TPM quota** for
> the current-generation Anthropic Claude models (`anthropic.claude-opus-4-8`, and
> `claude-sonnet-5` / `claude-opus-4-7` / `claude-haiku-4-5` if possible) for this account in
> us-east-1, on both the **bedrock-mantle** and **bedrock-runtime** endpoints.

> ⚠️ AWS Support's first auto-reply often says to "sign the Anthropic use-case form." That is
> a **red herring** here — the agreement is already `AVAILABLE`. Push for **backend
> TPM/runtime provisioning**.

### The 2-minute diagnostic (how the above was established)

No access keys needed — **AWS CloudShell** (the `>_` icon in the console top-nav) runs
pre-authenticated as your console identity, even as root:

```
aws bedrock get-foundation-model-availability --model-id anthropic.claude-opus-4-8 --region us-east-1
```
- **All four fields `AVAILABLE`/`AUTHORIZED` but Workbench/runtime still 403s** → the runtime
  TPM gate above → **AWS Support/Sales case** (self-service is exhausted).
- **Any field `NOT_AVAILABLE`/`NOT_AUTHORIZED`** → the account genuinely lacks the Anthropic
  agreement (a *different*, self-serviceable case) → run the agreement flow:
  `list-foundation-model-agreement-offers --offer-type ALL` → grab `offers[0].offerToken` →
  `create-foundation-model-agreement --model-id … --offer-token …` → re-check. **On this
  account it was all-green**, so we are in the first case.

*(Note: `get-foundation-model-availability` rejects the bare mantle id
`anthropic.claude-haiku-4-5` with `ValidationException: invalid model identifier` — that
classic control-plane API wants the version-suffixed runtime id; the bare form is mantle-only.
Use `anthropic.claude-opus-4-8` for the availability probe.)*

---

## Why this doc exists (unchanged)

Every "GREEN" in this project's Phase E evaluation is **anthropic-only**. The eval harness is
parametrized over two providers — `("anthropic", "bedrock")`
(`tests/eval/eval_cutover.py:34-38`) — but the `bedrock` half has been **unmeasured since
Session 161** because no working Bedrock access is present. When creds/access are absent the
live-tier collection hook (`tests/eval/conftest.py:47-60` →
`eval_cutover.provider_creds_available("bedrock")`) **silently skips** every bedrock test.
Phase E stays **NO-GO** partly because of this gap. As of Session 180 the gap's cause is
**identified** (the AWS runtime-quota gate above), not merely "no creds."

> ⚠️ **All cost numbers below are a-priori estimates.** Bedrock has *never* run live in this
> project, so there is no measured bill to anchor on.

---

## How the project reaches Bedrock (verified from code, Session 180)

| Fact | Value | Evidence |
|------|-------|----------|
| Bedrock client | **`anthropic.AnthropicBedrockMantle(aws_region=…)`** (mantle Messages endpoint) | `src/.../agents/intake/bedrock_client.py` (`dadf514`) |
| Default model (bedrock) | **`anthropic.claude-opus-4-8`** ($5 in / $25 out per M tok) — mantle catalog has no Sonnet | `bedrock_client.py:62` (`9e3f19b`) |
| Auth | **Bedrock API key** via `AWS_BEARER_TOKEN_BEDROCK`; **SigV4 fallback** from the AWS credential chain if unset | client docstring; `AnthropicBedrockMantle` |
| Endpoint (automatic) | `https://bedrock-mantle.{region}.api.aws/anthropic/v1/messages` | AWS Opus 4.8 model card |
| Model-id format | bare `anthropic.` prefix, **no** version suffix, **no** `us.`/`global.` inference-profile prefix (mantle) | AWS model card |
| Provider selection | explicit: `make_llm_client(provider="bedrock")` / `--provider bedrock` / `INTAKE_LLM_PROVIDER=bedrock`; model override via `INTAKE_LLM_MODEL`; default provider is `anthropic` | `factory.py:37-76` |
| Why skipped today | access gated (403) → `provider_creds_available("bedrock")` / a live call fails → live tests auto-skip | `conftest.py:47-60`, `eval_cutover.py:52-59` |

---

## Operator setup (the mantle + API-key path — matches the current code)

> Everything here is the path the code actually uses. The earlier revision's IAM-user /
> "do NOT create an API key" steps were for the **pre-mantle** `AnthropicBedrock` client and
> are **obsolete** — do not follow them.

**0. Region.** In the Bedrock console top-nav region dropdown, pick **US East (N. Virginia)
`us-east-1`** (mantle-supported, in-Region Claude, Opus 4.8 available). API keys are
Region-scoped.

**1. Generate a Bedrock API key.** Redesigned console → **ACCOUNT SCOPE → API keys**.
- **Long-term** (dev/testing): *Long-term API keys* tab → *Generate* → 30-day expiry → keep
  the default **`AmazonBedrockLimitedAccess`** policy (v8+ — it already grants
  `bedrock-mantle:*` and the `aws-marketplace:*` subscribe actions) → *Generate*. **Copy
  once.** (Long-term keys create an IAM user under the hood — that's the `MantleApiKey-*`
  users you'll see in IAM.)
- **Short-term** (production): *Short-term API keys* tab → *Generate* (≤12 h, inherits your
  IAM permissions).

**2. Wire it into `.env`** (git-ignored):
```
AWS_BEARER_TOKEN_BEDROCK=<key>
AWS_REGION=us-east-1
AWS_DEFAULT_REGION=us-east-1
```

**3. Export before pytest** — the project does **not** auto-load `.env`:
```
set -a; . ./.env; set +a
```
Skip this and every bedrock live test **silently skips** — a green run can mean "never ran."

**4. There is NO "Model access" page and NO use-case form on the mantle path.** Its absence
in the redesigned console is **expected**, not a bug — mantle is exempt from the Anthropic
First-Time-Use form. Account-level Claude access on mantle is governed by the runtime
entitlement/quota discussed in *Current status* above.

**5. Verify access before running the suite** (see the 2-minute diagnostic above, plus a real
invoke once AWS has provisioned the quota). Only once a real invoke returns text should you
run the eval suite.

---

## Cost estimates (moot until the AWS gate clears)

Three tiers, smallest to largest. **Point** figures below were modeled on the *old* Sonnet 4.6
default ($3/$15 per M tok). **The current default is Opus 4.8 ($5/$25) — multiply the Point
figures by ~1.7× for the real cost**, or override to a cheaper model with
`INTAKE_LLM_MODEL=anthropic.claude-haiku-4-5` ($1/$5) once access is granted. All at the
default **N=5 samples/case**; cost scales ~linearly with N.

| Tier | What it does | Bedrock LLM calls | **Point (Sonnet-modelled)** | Range (low–high) |
|------|--------------|------------------:|----------------------------:|------------------|
| **Smoke** | 1 classification round-trip — proves access + model id work | 1 | **~$0.03** | $0.01 – $0.05 |
| **Governance gate** | The §3.4 metric: 5 cases × 5 samples | ~25 | **~$0.94** | $0.31 – $2.23 |
| **Full shadow_run sweep** | Whole corpus: interviews + governance + SQL/QC; the real Phase E comparison | **~731** | **~$25** | $4.76 – $89 |

**Commands** (run only after the AWS quota is provisioned + `.env` exported):
- Smoke: `uv run pytest tests/agents/intake/test_bedrock_client.py -v`
- Governance gate: `uv run pytest -m live tests/eval/test_eval_live.py::test_live_governance_cycle_time_agreement_and_no_laxer_miss --provider bedrock --no-cov`
- Full sweep: `uv run python tests/eval/shadow_run.py` (runs **both** providers; ~90 min on anthropic — bedrock untested)

**Why the full sweep is ~$25:** ~731 calls, because each interview *turn* makes **two** LLM
calls (interviewer `next_question` + stakeholder-sim reply) across 25 interviews × ~10 turns,
plus draft/revise/classify per interview. Per-turn token sizes are **not logged**, so $25 is
an order-of-magnitude estimate with a wide band, not an invoice.

---

## Decision points for the operator

- **Auth path — DONE.** Mantle + Bedrock API key; the code migration landed (`dadf514`,
  `9e3f19b`). No further code needed.
- **The only open action is the AWS quota request** (*Current status* above) — a
  `ready-for-human` item. If bedrock is out of scope for now, rule it out explicitly so
  future sessions stop carrying it as an open gap.
- **Once access clears — which tier to fund?** Smoke + governance (~$1) vs. full comparison
  (~$25–30, ~1.7× if kept on the opus-4-8 default; cheaper on a haiku override).

## Sources

- Code: `bedrock_client.py`, `factory.py`, `conftest.py`, `eval_cutover.py`, `shadow_run.py`,
  `stakeholder_sim.py`, `PHASE_E_AGREEMENT_REPORT.md`.
- AWS (Session-180 live verification): `docs.aws.amazon.com/bedrock/.../model-access.html`,
  the Opus 4.8 model card, the redesigned-console announcement (June 2026), and AWS re:Post +
  an expert-authored Accepted Answer documenting the control-plane-vs-runtime TPM gate on
  current-gen Claude ("agreement AVAILABLE / authorization AUTHORIZED but runtime 403").
- Anthropic: `code.claude.com/docs/en/amazon-bedrock` ("A 403 from the Mantle endpoint with
  valid credentials means your AWS account has not been granted access… Contact your AWS
  account team"); `platform.claude.com/docs/.../claude-in-amazon-bedrock` (mantle client,
  model ids, pricing).
- ⚠️ Two directly-relevant AWS re:Post threads are Cloudflare-protected (403 to automated
  fetch); the "control-plane green / runtime gated → AWS Support case" resolution is drawn
  from their titles + an expert Accepted Answer synthesis, corroborated by Anthropic's own
  Bedrock docs — high substance-confidence, but confirm turnaround with AWS directly.
