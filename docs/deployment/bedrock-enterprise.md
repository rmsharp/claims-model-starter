# Enterprise Bedrock Deployment Guide

**Audience:** the platform / security / cloud team standing up this project's AWS Bedrock
Claude integration in an enterprise AWS account with complex security controls.
**Status (2026-07-27):** the app code is **mantle-migrated and enterprise-*capable* as-is** —
the two hardest requirements (role-based SigV4 auth, AWS PrivateLink) already work with **zero
code change**, and the §7 punch-list's config pass-throughs (`base_url`, `http_client`,
`require_sigv4`) have since shipped (`56dc700`) — what remains open is *wiring* `require_sigv4`
to app/env and confirming `aws_profile` support (§7). All facts below are verified against
official AWS + Anthropic docs (see *Sources*).

> **Why this exists.** The original testing account was a personal account that hit the
> current-gen-Claude **account-eligibility gate** (AWS denied the runtime-quota request — see
> `docs/architecture-history/bedrock-testing-enablement.md`). The plan is to deploy into an enterprise
> account that already has the eligibility *and* the security controls. This guide is what to
> provision there.

---

## 0. Decide FIRST — mantle vs. bedrock-runtime (a fork your security team owns)

The app uses **Claude in Amazon Bedrock via the `bedrock-mantle` endpoint** (the
`AnthropicBedrockMantle` client, native Anthropic Messages API). Two enterprise-security
mandates, if present, would force the *other* Bedrock path (classic `bedrock-runtime`,
`InvokeModel`/`Converse`, the `AnthropicBedrock` client) — a larger change. **Confirm these
before building anything:**

1. **Do you mandate Bedrock Guardrails on model input/output?** Guardrails are documented for
   `bedrock-runtime` (InvokeModel/Converse) and the OpenAI-compat path — **not confirmed** for
   the native Anthropic Messages path on mantle, and one AWS source lists Guardrails as *not
   supported* on mantle. **If Guardrails are mandatory → use `bedrock-runtime`.**
2. **Do you mandate a FIPS 140-2/3 endpoint?** There is `bedrock-fips` / `bedrock-runtime-fips`
   but **no `bedrock-mantle-fips`.** **If FIPS is mandatory → use `bedrock-runtime`.**
3. **Does the target account already have current-gen Claude runtime quota?** Confirm Opus 4.8
   (or your chosen model) shows non-zero applied TPM in Service Quotas / a successful Workbench
   `ping` — established enterprise accounts usually do; a fresh one may hit the same eligibility
   gate we did. This is the prerequisite for *any* path.

The rest of this guide assumes the **mantle path** (Q1 & Q2 = no). If either is "yes," most of
§2/§4/§5 still applies but the client class, IAM actions, and model-id form change — flag it and
we re-plan.

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

Tightest policy for a **SigV4/role, mantle-only** deployment (replace `ACCOUNT` and the region):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "MantleInference",
      "Effect": "Allow",
      "Action": "bedrock-mantle:CreateInference",
      "Resource": "arn:aws:bedrock-mantle:us-east-1:ACCOUNT:project/*",
      "Condition": { "StringEquals": { "bedrock-mantle:Model": "anthropic.claude-opus-4-8" } }
    },
    {
      "Sid": "MarketplaceEntitlementCheck",
      "Effect": "Allow",
      "Action": "aws-marketplace:ViewSubscriptions",
      "Resource": "*",
      "Condition": { "StringEquals": { "aws:CalledViaLast": "bedrock-mantle.amazonaws.com" } }
    }
  ]
}
```

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
  (`https://{vpce-id}.bedrock-mantle.{region}.vpce.amazonaws.com/anthropic`). The repo does **not
  yet** expose a `base_url` override — that's the first item in the §7 punch-list. (`ANTHROPIC_BASE_URL`
  is also honored by the SDK.)
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
  mantle Messages path is **unconfirmed** (see §0 Q1). If Guardrails are required, plan for the
  `bedrock-runtime` path.

---

## 7. The app's config surface

The web UI (`go/modelintake`) resolves provider/model from env (`ui/intake/app.py`):

| Env var | Purpose | Enterprise value |
|---|---|---|
| `INTAKE_LLM_PROVIDER` | Select the LLM backend | `bedrock` |
| `INTAKE_LLM_MODEL` | Optional model-id override | unset → default `anthropic.claude-opus-4-8`, or pin/upgrade here (bare mantle id) |
| `AWS_REGION` (`AWS_DEFAULT_REGION`) | Region → endpoint host + residency geography | a mantle-supported region |
| `AWS_BEARER_TOKEN_BEDROCK` | Bearer token (dev only) | **UNSET in prod** — forces role SigV4 |

AWS credentials themselves are **never** app config — the IAM role supplies them via the chain.

**Punch-list — the small code changes to add (the "then code" phase, once §0 is settled):**
1. ✅ **DONE (`56dc700`).** Optional **`base_url`** pass-through on `BedrockLLMClient.__init__` →
   `AnthropicBedrockMantle(base_url=…)` (for PrivateLink without Private DNS, or a GovCloud host).
   Both client copies (intake + data-agent).
2. ✅ **DONE (`56dc700`).** Optional **`http_client`** pass-through →
   `AnthropicBedrockMantle(http_client=DefaultHttpxClient(proxy=…, verify=<CA>))` (for forward
   proxy / TLS-inspection CA / mTLS). Both client copies.
3. ✅ **DONE (`56dc700`).** **Invert the client docstrings** — now frame role SigV4 as primary and
   the bearer token as the dev-only fallback.
4. ✅ **DONE (`56dc700`), as a hard guard rather than a warning.** `require_sigv4=True` raises if
   `AWS_BEARER_TOKEN_BEDROCK` is set, so a stray token cannot silently bypass role auth. Not yet
   *wired* to app/env (`INTAKE_LLM_PROVIDER=bedrock` does not set it automatically) — that wiring is
   `docs/planning/enterprise-migration.md` Phase C1/D13, still open.
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

- [ ] **§0 answered** — Guardrails mandate? FIPS mandate? (either → `bedrock-runtime`, re-plan)
- [ ] Target account **has current-gen Claude runtime quota** (non-zero applied TPM / Workbench `ping` works)
- [ ] IAM execution role with the §3 policy, assumable via your IdP (IRSA / instance profile / SSO)
- [ ] `AWS_BEARER_TOKEN_BEDROCK` **unset** in the prod profile; `AWS_REGION` set to a mantle region
- [ ] Interface VPC endpoint `com.amazonaws.{region}.bedrock-mantle` with **Private DNS enabled** + endpoint policy
- [ ] Egress allowlist: `bedrock-mantle.{region}.api.aws:443`, STS, IMDS; `NO_PROXY` for intra-VPC
- [ ] Region/model-id chosen (bare id; Regional vs Global residency decision made; SCPs aligned)
- [ ] Model-invocation logging + KMS + geo SCPs provisioned per §6
- [ ] `INTAKE_LLM_PROVIDER=bedrock` set; smoke-test a live `messages.create`
- [ ] (if §7 punch-list needed) `base_url` / `http_client` pass-throughs merged

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
| Why the live eval tier skips bedrock today | no working access in the personal test account (see *Why this exists* above) → `provider_creds_available("bedrock")` fails / a live call fails → live tests auto-skip | `conftest.py:47-60`, `eval_cutover.py:52-59` |

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
