# Enterprise Bedrock Deployment Guide

**Audience:** the platform / security / cloud team standing up this project's AWS Bedrock
Claude integration in an enterprise AWS account with complex security controls.
**Status (2026-07-29):** the app code is **mantle-migrated and enterprise-*capable* as-is** —
the two hardest requirements (role-based SigV4 auth, AWS PrivateLink) already work with **zero
code change**, and the §7 punch-list's config pass-throughs (`base_url`, `http_client`,
`require_sigv4`) have since shipped (`56dc700`). **D13 resolved (Session 200):** `require_sigv4`
now rejects a stray key in *either* SDK-recognized bearer-token env var
(`AWS_BEARER_TOKEN_BEDROCK` **or** `ANTHROPIC_AWS_API_KEY` — the guard previously checked only
the first), and it defaults from `BEDROCK_REQUIRE_SIGV4` when not passed explicitly, so
`INTAKE_LLM_PROVIDER=bedrock` can enforce it purely through env config. **§0's three security
questions answered (2026-07-29, operator):** Guardrails and FIPS are both **not** mandated, so the
mantle path is confirmed correct — see §0 for the full answers, including the one still-open
verification item (runtime quota). What remains open is confirming `aws_profile` support (§7 item
5) and — per D13's own recommendation — wiring `http_client` from env, deferred until
TLS-inspection is confirmed. All facts below are verified against official AWS + Anthropic docs
(see *Sources*).

> **Why this exists.** The original testing account was a personal account that hit the
> current-gen-Claude **account-eligibility gate** (AWS denied the runtime-quota request — see
> `docs/architecture-history/bedrock-testing-enablement.md`). The plan is to deploy into an enterprise
> account that already has the eligibility *and* the security controls. This guide is what to
> provision there.

---

## 0. Mantle vs. bedrock-runtime — RESOLVED (2026-07-29, operator)

The app uses **Claude in Amazon Bedrock via the `bedrock-mantle` endpoint** (the
`AnthropicBedrockMantle` client, native Anthropic Messages API). Two enterprise-security
mandates, if present, would have forced the *other* Bedrock path (classic `bedrock-runtime`,
`InvokeModel`/`Converse`, the `AnthropicBedrock` client) — a larger change. **Answered by the
operator, 2026-07-29:**

1. **Do you mandate Bedrock Guardrails on model input/output? → No.** Guardrails are documented
   for `bedrock-runtime` (InvokeModel/Converse) and the OpenAI-compat path — **not confirmed** for
   the native Anthropic Messages path on mantle, and one AWS source lists Guardrails as *not
   supported* on mantle. Answered "no," so this does **not** force `bedrock-runtime`.
2. **Do you mandate a FIPS 140-2/3 endpoint? → No.** There is `bedrock-fips` /
   `bedrock-runtime-fips` but **no `bedrock-mantle-fips`.** Answered "no," so this does **not**
   force `bedrock-runtime`.
3. **Does the target account already have current-gen Claude runtime quota? → Expected yes**
   (established enterprise account), **but not independently verified.** The operator has not yet
   confirmed Opus 4.8 (or the chosen model) shows non-zero applied TPM in Service Quotas, nor run a
   successful Workbench `ping` — this repository has no access to the target account to check
   either. Unlike Q1/Q2, a "no" here would not redirect to `bedrock-runtime` — it's the
   prerequisite for running *either* path, not a path-choice branch. **Still open: verify with a
   live Service Quotas check or Workbench `ping` once the enterprise account is actually
   accessible** (naturally falls at or after Phase C4, account provisioning — not yet a listed
   verification step there; flagged for whoever runs it or first connects live).

**Resolution: the mantle path is confirmed correct** (Q1 & Q2 = no). §2/§4/§5 below apply as
written; the client class, IAM actions, and model-id form do **not** need to change. Q3 (runtime
quota) remains open as a standalone verification item — see the note above, not a re-plan
trigger.

---

## 1. Division of responsibility

| Concern | Owned by | Notes |
|---|---|---|
| IAM execution role + permissions policy | Platform team | §3 — the app assumes a role; it stores no keys |
| VPC interface endpoint (PrivateLink) + DNS | Platform team | §4 — zero app change when Private DNS is on |
| Model access / runtime quota (account eligibility) | Platform team | §0 Q3; Appendix B (quota codes) |
| Model-invocation logging, KMS, SCP geo guardrails | Platform team | §6 — transparent to the app |
| Region / model-id / provider selection (config) | App config | §5, §7 — env vars only |
| The Bedrock client + Messages calls | This repo | already built (mantle) |

The app **carries no static credentials** and passes **no** security parameters on the invoke
(except an optional guardrail header if you enable §6 guardrails). Everything security-relevant
is account/role/network config the platform team provisions.

---

## 2. Authentication — role-based SigV4, no static keys

`AnthropicBedrockMantle` resolves AWS credentials via the **standard AWS credential chain**
(constructor args → env vars → shared config → SSO / assumed roles / ECS task role / EKS IRSA /
IMDS) and signs requests with **SigV4**. The repo's `BedrockLLMClient` constructs it with no
credentials, so it inherits whatever the runtime IAM role provides — **the enterprise "no
long-term keys, IAM-role-only" model works with zero code change.**

**Production (recommended):**
- Run under an **IAM role** delivered as short-term STS credentials — EKS IRSA, EC2 instance
  profile, ECS task role, or IAM Identity Center / SSO. (Anthropic ranks a dedicated **Bedrock
  service role** #1 and **IAM assumed role** #2; both are SigV4.)
- **Leave `AWS_BEARER_TOKEN_BEDROCK` UNSET.** Set `AWS_REGION` to a mantle-supported region.
- The app carries no `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY`.

**Local dev only:** a **short-term** Bedrock API key from the `aws-bedrock-token-generator`
library (`provide_token()`, ≤12 h, inherits your session) exported as `AWS_BEARER_TOKEN_BEDROCK`.
Same client, no code branch. **Do not use long-term Bedrock API keys** (they create a standing
IAM user — AWS labels them exploration-only).

> ⚠️ **Bearer token silently beats SigV4.** If `AWS_BEARER_TOKEN_BEDROCK` (or an explicit
> `api_key`) is present, the SDK uses bearer mode and **skips SigV4 even when a valid IAM role is
> attached** — bypassing least-privilege. **Guarantee the var is unset in production.** An SCP
> that denies `iam:CreateServiceSpecificCredential` (bedrock) and `bedrock-mantle:CallWithBearerToken`
> when `bedrock-mantle:bearerTokenType = LONG_TERM` enforces this org-wide.

---

## 3. IAM — least-privilege execution-role policy (mantle path)

The mantle Messages endpoint authorizes on **`bedrock-mantle:CreateInference`** against a
**project** resource, with the model narrowed by the `bedrock-mantle:Model` condition key — this
is a **different action namespace** from classic `bedrock:InvokeModel`. A role scoped only to
`bedrock:*` will 403 the mantle client.

Tightest policy for a **SigV4/role, mantle-only** deployment (replace `ACCOUNT` and the region) is
templated at **`docs/deployment/bedrock-mantle-execution-role-permissions.json`** — a reviewable,
directly-applyable (`aws iam put-role-policy --policy-document file://...`) artifact, not a fenced
block a security team has to retype. It grants exactly `bedrock-mantle:CreateInference` (scoped by
the `bedrock-mantle:Model` condition key) plus the one-time Marketplace entitlement check.

The execution role also needs a **trust policy** (who may assume it — a `Principal`, which an
identity-based permissions policy like the one above can never contain). That shape depends on
**D14** (the runtime — EKS IRSA vs. EC2 instance profile vs. ECS task role vs. IAM Identity
Center/SSO), which is deferred post-fork per §1.3. **`docs/deployment/bedrock-mantle-execution-role-trust.json`**
templates the statement shape with `Principal` left as an explicit placeholder naming D14 — do not
fill it in without a confirmed runtime shape; guessing one to unblock this phase would silently
pick the wrong trust relationship.

Notes:
- **Do NOT add `bedrock-mantle:CallWithBearerToken`** on the pure SigV4/role path — it is only
  for the bearer-token path (dev). Omit it for least privilege.
- The one-time **Marketplace subscribe** (Anthropic is a Marketplace product) should be done by a
  *provisioning* role, not the steady-state execution role; the execution role needs only
  `ViewSubscriptions`. Keep the `aws:CalledViaLast` condition — it stops the Marketplace grant
  being usable outside a Bedrock call.
- If you use the **Bedrock service role** pattern (Anthropic's #1), the calling principal also
  needs `iam:PassRole` on the service-role ARN (`Condition iam:PassedToService = bedrock.amazonaws.com`).
- If your security review wants the model pinned by **project** as well, scope
  `arn:aws:bedrock-mantle:...:project/*` down to a specific `project/proj_...` ARN once you know
  it from a CloudTrail `bedrock-mantle` event.

*(If §0 forces the `bedrock-runtime` path instead, the policy is different: `bedrock:InvokeModel*`
/ `bedrock:Converse*` on the **inference-profile ARN** (`us.`/`global.anthropic.claude-opus-4-8`)
**plus** the underlying per-region **foundation-model ARNs** — including the region-less
`arn:aws:bedrock:::foundation-model/...` for a global profile — gated by `bedrock:InferenceProfileArn`.
Ask and I'll drop the full runtime policy in.)*

---

## 4. Network — AWS PrivateLink + egress

- **Interface VPC endpoint:** service name **`com.amazonaws.{region}.bedrock-mantle`** (PrivateLink
  for mantle launched 2026-02-12). Attach a VPC-endpoint policy allowing `bedrock-mantle:CreateInference`.
- **With Private DNS enabled → zero code change.** The app's default endpoint
  `https://bedrock-mantle.{region}.api.aws/anthropic` resolves to the private ENI automatically.
  **This is the recommended deployment shape.**
- **Without Private DNS →** the app must target the VPCE DNS name
  (`https://{vpce-id}.bedrock-mantle.{region}.vpce.amazonaws.com/anthropic`). **Two ways to set
  this, no code change needed either way:** (1) the **cheapest lever** — set
  **`ANTHROPIC_BEDROCK_MANTLE_BASE_URL`** in the environment; `AnthropicBedrockMantle` (SDK
  0.94.1, `lib/bedrock/_mantle.py`) reads it directly whenever `base_url` isn't passed to the
  constructor, and `BedrockLLMClient` only passes `base_url` when explicitly given one (see
  `bedrock_client.py`) — so the env var alone works today, purely inside the SDK. (2) pass
  `base_url=` to `BedrockLLMClient.__init__` (shipped `56dc700`, §7 punch-list item 1) when
  constructing the client programmatically. **This is not the same env var other Anthropic SDK
  clients read for the same purpose** — the plain `anthropic.Anthropic` client and
  `AnthropicVertex` each resolve `base_url` from their own, non-interchangeable env-var name
  (`_client.py` and `lib/vertex/_client.py` respectively); the mantle client (`_mantle.py`) honors
  only the name above. This doc previously named one of the *other* clients' env vars here and
  said the `base_url` override "does not yet" exist — both were
  stale/wrong; corrected 2026-07-29.
- **Egress allowlist** must permit outbound TLS to `bedrock-mantle.{region}.api.aws:443` (or the
  VPCE host). If SigV4/STS is used, **STS** (`sts.{region}.amazonaws.com`, ideally its own
  PrivateLink) and **IMDS** (`169.254.169.254`) must also be reachable. Set `NO_PROXY` so
  intra-VPC PrivateLink/IMDS/STS bypasses any forward proxy.
- **Corporate HTTPS proxy / TLS inspection / custom CA:** handled by a custom httpx client
  (`anthropic.DefaultHttpxClient(proxy=…, verify=<corp CA bundle>)`) — the repo does **not yet**
  pass one through (§7 punch-list item 2). `HTTPS_PROXY` env auto-detection is unreliable in the
  SDK, so an explicit client is preferred.
- **No FIPS mantle endpoint** (see §0 Q2). **SigV4 host must match `aws_region`** — if you override
  `base_url` to a VPCE host, keep the region consistent or signing 403s.

---

## 5. Region, model id, and data residency

- **Model id on mantle is the BARE id** — `anthropic.claude-opus-4-8`. **Do not prepend
  `us.`/`eu.`/`global.`** inference-profile prefixes; those are `bedrock-runtime`-only and are
  listed as *N/A* for mantle. Geography on mantle is selected by the **endpoint/region**, not the id.
- **Region** (`AWS_REGION`) selects the data-residency geography *and* must be in the mantle-supported
  set (us-east-1, us-east-2, us-west-2, ap-*, eu-*, sa-east-1, us-gov-west-1). us-east-1/2 and
  us-west-2 are the US in-region choices for Opus 4.8.
- **Regional vs Global (a residency/cost decision):** a **Regional** endpoint keeps data in one
  region (needed for residency) at a **~10% pricing premium**; the **Global** endpoint routes
  worldwide at no premium — a **residency violation** for regulated P&C/insurance data. Choose
  deliberately; Global routing sets `aws:RequestedRegion=unspecified`, which a region-restriction
  SCP must explicitly allow (or you can Deny it to hard-block global).
- **Decision (D10, operator-accepted 2026-07-29): Regional.** For P&C claims data, residency
  dominates the ~10% premium — see `docs/planning/enterprise-migration.md` Decision Register. The
  hard-block SCP is templated at `docs/deployment/bedrock-residency-scp.json` (Deny on
  `aws:RequestedRegion` outside an allowlist, which also catches Global's `unspecified` value).
  **The specific allowed region(s) in that file are a placeholder** (`us-east-1`/`us-east-2`/
  `us-west-2`, the three US in-region choices named above) — the platform team confirms/replaces
  them once the actual deployment region is known; that region choice itself is not part of D10 and
  remains open. Applying the SCP in AWS Organizations is platform-team work (§1), not this repo's.

---

## 6. Security config the platform team owns (transparent to the app)

The app passes **nothing** for these — they are account/role/network config:
- **Model-invocation logging** — off by default; enable at account+Region level
  (`put-model-invocation-logging-configuration`) to CloudWatch Logs and/or S3 (captures full
  request/response). This is the audit surface.
- **Encryption** — Bedrock encrypts at rest with AWS-owned keys by default. Customer-managed KMS
  keys are a per-resource option (custom models, KBs, eval jobs) and are transparent to inference;
  official docs do not document a CMK hook on the stateless mantle Messages path (flag for security
  if CMK-at-rest on inference I/O is mandated).
- **Data residency SCPs** — see §5 (`aws:RequestedRegion`); geographic profiles keep processing in
  a geography.
- **Guardrails** — **the one that may need the app.** If mandated, the invoke must carry
  `X-Amzn-Bedrock-GuardrailIdentifier` / `-GuardrailVersion` headers, and support on the native
  mantle Messages path is **unconfirmed**. **Answered "not mandated" (§0 Q1, 2026-07-29)** — if
  that ever changes, plan for the `bedrock-runtime` path instead.

---

## 7. The app's config surface

The web UI (`go/modelintake`) resolves provider/model from env (`ui/intake/app.py`):

| Env var | Purpose | Enterprise value |
|---|---|---|
| `INTAKE_LLM_PROVIDER` | Select the LLM backend | `bedrock` |
| `INTAKE_LLM_MODEL` | Optional model-id override | unset → default `anthropic.claude-opus-4-8`, or pin/upgrade here (bare mantle id) |
| `AWS_REGION` (`AWS_DEFAULT_REGION`) | Region → endpoint host + residency geography | a mantle-supported region |
| `AWS_BEARER_TOKEN_BEDROCK` | Bearer token (dev only) | **UNSET in prod** — forces role SigV4 |
| `ANTHROPIC_AWS_API_KEY` | Bearer token, alternate name the SDK also honors (dev only) | **UNSET in prod** — same override risk as `AWS_BEARER_TOKEN_BEDROCK` |
| `BEDROCK_REQUIRE_SIGV4` | Set (`1`) to make `BedrockLLMClient` reject construction if either bearer-token var above is set | **Set in prod** — turns a stray key into a hard `ValueError` instead of a silent SigV4 bypass (D13, Session 200) |
| `ANTHROPIC_BEDROCK_MANTLE_BASE_URL` | PrivateLink VPCE host override, read directly by the SDK's mantle client (`_mantle.py`) — **no app code involved**, works even though `BedrockLLMClient` has no env-driven wiring for it | set to the VPCE DNS name (§4) only when Private DNS is **off**; leave unset when Private DNS is on (the default endpoint already resolves to the private ENI) |

AWS credentials themselves are **never** app config — the IAM role supplies them via the chain.
Not app config either, but sourced the same way: `ANTHROPIC_BEDROCK_MANTLE_BASE_URL` is read
straight out of the environment by the SDK, not by anything in this repo — there is no
`BedrockLLMClient` parameter or factory wiring for it, and none is needed.

**Punch-list — the small code changes to add (the "then code" phase; §0 is now settled, 2026-07-29
— mantle confirmed):**
1. ✅ **DONE (`56dc700`).** Optional **`base_url`** pass-through on `BedrockLLMClient.__init__` →
   `AnthropicBedrockMantle(base_url=…)` (for PrivateLink without Private DNS, or a GovCloud host).
   Both client copies (intake + data-agent). **Cheaper still: no code needed at all** — leave
   `base_url` unpassed and set **`ANTHROPIC_BEDROCK_MANTLE_BASE_URL`** in the environment; the SDK
   reads it directly (§4, §7 table).
2. ✅ **DONE (`56dc700`).** Optional **`http_client`** pass-through →
   `AnthropicBedrockMantle(http_client=DefaultHttpxClient(proxy=…, verify=<CA>))` (for forward
   proxy / TLS-inspection CA / mTLS). Both client copies.
3. ✅ **DONE (`56dc700`).** **Invert the client docstrings** — now frame role SigV4 as primary and
   the bearer token as the dev-only fallback.
4. ✅ **DONE (`56dc700`), as a hard guard rather than a warning; extended and wired (Session
   200, D13).** `require_sigv4=True` raises if `AWS_BEARER_TOKEN_BEDROCK` **or**
   `ANTHROPIC_AWS_API_KEY` is set (the guard originally checked only the first — a stray key in
   the second silently bypassed it even with the guard enabled). `require_sigv4` now also
   defaults from `BEDROCK_REQUIRE_SIGV4` when not passed explicitly, so
   `INTAKE_LLM_PROVIDER=bedrock` can enforce it purely through env config — no code change at the
   call site. `http_client` wiring from env remains **not done**, per D13's own recommendation:
   deferred until TLS-inspection is confirmed as needed.
5. Confirm the SDK's `aws_profile` support if SSO named profiles are needed (SDK-version-specific).
   **Still open.**

---

## 8. Mantle capability gaps (does the repo hit any?)

The native Anthropic Messages path on mantle does **not** support: Message Batches, server-side
tools (web search/fetch, code execution), Agent Skills / MCP, the Files API / URL inputs,
server-side `fallbacks`, `output_config.format` structured outputs (400s), Bedrock Guardrails
(uncertain), and FIPS. **The repo relies on none of these** — it uses plain `messages.create`
with fenced-text JSON parsing — so the only real exposure is a **mandated** Guardrail/FIPS control
(§0). Also: Opus 4.8 is **Standard service tier only** (no Provisioned Throughput / Priority) —
capacity is TPM-quota-bound, which matters for enterprise capacity planning.

---

## 9. Pre-move readiness checklist

- [x] **§0 answered (2026-07-29, operator):** Guardrails **not** mandated, FIPS **not** mandated —
      mantle path confirmed, no re-plan needed
- [ ] Target account **has current-gen Claude runtime quota** (non-zero applied TPM / Workbench
      `ping` works) — **expected yes** (established enterprise account) but **not independently
      verified**; check once the account is accessible (§0 Q3)
- [ ] IAM execution role with the §3 permissions policy
      (`bedrock-mantle-execution-role-permissions.json`), assumable via your IdP (IRSA / instance
      profile / SSO) once the trust policy's D14-blocked `Principal` placeholder
      (`bedrock-mantle-execution-role-trust.json`) is filled in for the chosen runtime shape
- [ ] `AWS_BEARER_TOKEN_BEDROCK` / `ANTHROPIC_AWS_API_KEY` **unset** in the prod profile;
      `BEDROCK_REQUIRE_SIGV4=1` **set** so a stray key hard-fails instead of silently bypassing
      SigV4 (D13, Session 200); `AWS_REGION` set to a mantle region
- [ ] Interface VPC endpoint `com.amazonaws.{region}.bedrock-mantle` with **Private DNS enabled** + endpoint policy
- [ ] Egress allowlist: `bedrock-mantle.{region}.api.aws:443`, STS, IMDS; `NO_PROXY` for intra-VPC
- [ ] Region/model-id chosen (bare id; **Regional vs Global residency decision made — D10:
      Regional, 2026-07-29**; SCPs aligned — template at `bedrock-residency-scp.json`, specific
      region allowlist and AWS application still open)
- [ ] Model-invocation logging + KMS + geo SCPs provisioned per §6
- [ ] `INTAKE_LLM_PROVIDER=bedrock` set; smoke-test a live `messages.create`
- [x] `base_url` / `http_client` pass-throughs merged (`56dc700`) — and for the common
      PrivateLink-without-Private-DNS case, no merge is even required: set
      `ANTHROPIC_BEDROCK_MANTLE_BASE_URL` in the environment (§4, §7 table)

---

## Appendix A: How the project reaches Bedrock (verified facts, carried forward from the archived testing-enablement runbook)

| Fact | Value | Evidence |
|------|-------|----------|
| Bedrock client | **`anthropic.AnthropicBedrockMantle(aws_region=…)`** (mantle Messages endpoint) | `src/.../agents/intake/bedrock_client.py` (`dadf514`) |
| Default model (bedrock) | **`anthropic.claude-opus-4-8`** ($5 in / $25 out per M tok) — mantle catalog has no Sonnet | `bedrock_client.py` `DEFAULT_MODEL` (`9e3f19b`) |
| Auth | **Role-based SigV4** primary (via the standard AWS credential chain); **Bedrock API key** (`AWS_BEARER_TOKEN_BEDROCK`) is a dev-only fallback that overrides SigV4 when set | client docstring (post-`56dc700`); `AnthropicBedrockMantle` |
| Endpoint (automatic) | `https://bedrock-mantle.{region}.api.aws/anthropic/v1/messages` | AWS Opus 4.8 model card |
| Model-id format | bare `anthropic.` prefix, **no** version suffix, **no** `us.`/`global.` inference-profile prefix (mantle) | AWS model card |
| Provider selection | explicit: `make_llm_client(provider="bedrock")` / `--provider bedrock` / `INTAKE_LLM_PROVIDER=bedrock`; model override via `INTAKE_LLM_MODEL`; default provider is `anthropic` | `factory.py:37-76` |
| Why the live eval tier skips bedrock today | no working access in the personal test account (see *Why this exists* above) → `provider_creds_available("bedrock")` fails / a live call fails → live tests auto-skip | `conftest.py:56-69`, `eval_cutover.py:71-76` (re-cited Session 214, when a third provider shifted the ranges) |

## Appendix B: Bedrock TPM (tokens-per-minute) quota codes (reference)

Quota codes for current-generation Claude on Bedrock mantle, `us-east-1`, model `anthropic.claude-opus-4-8`. Useful for checking a **new** (e.g. enterprise) account's Service Quotas console before assuming access — a control-plane model-access grant (`get-foundation-model-availability` returning `AVAILABLE`/`AUTHORIZED`) does **not** guarantee a non-zero runtime quota; check the *Applied* value for each code below (§0 checklist item 3).

| Quota | Code | Default | Self-service adjustable |
|---|---|---|---|
| **[bedrock-mantle] Input TPM** | `L-8528F119` | 20,000,000 | Yes — Service Quotas console |
| **[bedrock-mantle] Output TPM** | `L-37491D63` | 2,000,000 | Yes — Service Quotas console |
| Cross-region TPM | `L-DB99DCDB` | 30,000,000 | Yes (not needed for mantle) |
| Global cross-region TPM | `L-4FCE27C7` | 30,000,000 | Yes (not needed for mantle) |
| Global cross-region tokens/day | `L-917CA0F1` | 43.2B | No — requires an AWS Support case |
| On-demand max tokens/day | `L-AFE3B2BE` | 21.6B | No — requires an AWS Support case |

The two **`[bedrock-mantle]`** TPM quotas are what gate this project's code (the mantle endpoint). If either shows `Applied = 0` on a target account, request an increase via Service Quotas first (self-service); the two `No` rows require an AWS Support case.

## Sources

Verified 2026-07-24/25 against: `platform.claude.com/docs/en/build-with-claude/claude-in-amazon-bedrock`
(auth paths, mantle client, model ids, Regional/Global); AWS Bedrock user guide —
`vpc-interface-endpoints.html` (PrivateLink service names + Private DNS), `api-keys-*.html`
(bearer vs SigV4), `security_iam_id-based-policy-examples.html` + `security-iam-projects.html` +
`AmazonBedrockMantleInferenceAccess` managed-policy ref (IAM actions/ARNs),
`model-card-anthropic-claude-opus-4-8.html` (bare-id-on-mantle, endpoints, tiers),
`model-invocation-logging.html` / `data-encryption.html` / `guardrails-permissions-id.html`
(logging/KMS/guardrails), `bedrock-mantle.html` (region list, quotas); the Anthropic Python SDK
`lib/bedrock/_mantle.py` (`base_url` + `http_client` constructor params); AWS what's-new
2026-02-12 (mantle PrivateLink). See the session's verification workflow for the full fact set.
