# Architecture Overview

*Audience: chief architects and other technical decision-makers assessing this system for enterprise adoption. For agent-by-agent mechanics, see [Pipeline Overview](Pipeline-Overview). For the itemized decision log, see [Architecture Decisions](Architecture-Decisions).*

## What this system is, in architectural terms

Model Project Constructor is a three-agent pipeline that converts a claims-organization stakeholder's model idea into a governance-scaffolded GitLab or GitHub repository. Two of the three agents (Intake, Data) call an LLM — Claude via Anthropic's API or AWS Bedrock, or, on a third provider, whatever model the `opencode` CLI is configured to reach; the third agent (Website) is fully deterministic and template-driven and makes no model calls at all. A thin, plain-script orchestrator drives the three in sequence and persists every inter-agent handoff to disk. The output is a static repository — markdown, SQL, and Quarto files — with **zero AI runtime dependency**: once handed off, a data science team can build on it without ever calling an LLM again.

## System architecture at a glance

```
Stakeholder ──▶ Intake Agent ──▶ IntakeReport ──▶ adapter ──▶ DataRequest
                                                                   │
                                                                   ▼
                                                              Data Agent
                                                                   │
                                                                   ▼
                                                              DataReport
                                                                   │
                                                  IntakeReport + DataReport
                                                                   │
                                                                   ▼
                                                            Website Agent
                                                                   │
                                                                   ▼
                                                  GitLab/GitHub project (draft)
```

Every inter-agent boundary is mediated by a `HandoffEnvelope` — a versioned wrapper carrying routing, schema-version, and correlation metadata, resolved against a schema registry keyed on `(payload_type, schema_version)` (full field list in [Pipeline Overview](Pipeline-Overview)). Validation happens twice: the envelope first, then the payload. The orchestrator owns the single translation point between `IntakeReport` and `DataRequest` — agents never import each other's schemas directly (AD-6). Schema evolution itself is intentionally minimal today: every payload is at version `1.0.0` and no migration machinery exists yet — a future breaking change would need a version bump plus a purpose-built migrator that has not been built (see [Schema Reference](Schema-Reference) for the versioning policy).

Each agent internally runs its own LangGraph state machine — the Intake Agent's interview loop needs to pause for human review and resume across sessions, and the Data Agent's query/QC loop needs bounded retry branches — but the top-level orchestrator that chains the three agents is a plain sequential script, not a framework. This split is deliberate: LangGraph's checkpointing and interrupt/resume machinery earns its complexity *inside* an agent with genuine long-running, resumable state; the three-agent handoff itself has no such requirement, so a function-call chain is simpler to read, debug, and checkpoint at the top level. Every handoff and the terminal repository-creation result are persisted to a per-run checkpoint directory, which gives operators a plain filesystem-based trace of exactly how far a run progressed, and supports resuming a halted run from its last completed stage rather than restarting from scratch.

## Key architectural decisions and tradeoffs

The full itemized log lives in [Architecture Decisions](Architecture-Decisions) (ten entries, AD-1 through AD-10). The four most consequential for an adoption decision:

- **Sequential orchestration, not parallel or event-driven (AD-1).** Each agent strictly needs its predecessor's output, so a synchronous script minimizes debugging and operational surface. The tradeoff is explicit and accepted: if a future agent has an independent input (not derived from this chain), the orchestrator would need to grow into a real state machine or event broker — not a redesign, but a scoped upgrade.
- **The Data Agent is structurally decoupled from the Intake Agent (AD-6).** It accepts its own `DataRequest` schema, not `IntakeReport`, and ships as a separate installable package with its own CLI, so it can be reused standalone by analyst teams for ad-hoc query generation — not just as a pipeline stage. A CI test statically verifies (via AST inspection, not just convention) that no Data Agent source file imports an Intake schema.
- **Pydantic v2 over protobuf or bare JSON Schema (AD-3).** Chosen for zero-ceremony runtime validation in an all-Python codebase, automatic JSON Schema export, and cross-field validators — at the cost of enforcement being Python-only (a non-Python consumer of the schemas gets documentation, not a shared runtime contract).
- **A `RepoClient` protocol abstracts the git host (AD-5).** Two operations only — `create_project()` and `commit_files()` — implemented by `GitLabAdapter`, `GitHubAdapter`, and an in-memory `FakeRepoClient` for tests. Adding a new host is a registry entry plus one adapter module, not a change to Website Agent logic.

**Alternatives considered and rejected** (full rationale in `architecture-approaches.md`): a persistent-workflow state machine and an event/message-broker design were both rejected for the orchestrator as premature complexity for a linear three-agent flow. The OpenAI Agents SDK (GPT-4o) was rejected over vendor lock-in and because its main selling point — direct code execution against corporate databases for live EDA — is a security posture this project deliberately avoids anyway (see below). For exploratory data analysis, sandboxed-subprocess and full containerized execution were both rejected in favor of code-generation-only: the pipeline never executes analysis code itself, it only generates it for a human to run.

## Technology and vendor posture

Python 3.11+, managed as a `uv` workspace (two installable packages: the orchestrator and a standalone data-agent distribution), MIT-licensed throughout. LangGraph (pinned pre-1.0, deliberately, since its API is not yet stable) provides per-agent state-machine execution and checkpointing. Pydantic validates every schema boundary. Repo-host integration uses direct `httpx` REST calls rather than the official GitLab/GitHub SDKs — a deliberate replacement completed to eliminate LGPL exposure (see below). The optional intake web UI is FastAPI + Uvicorn with server-sent events for live interview streaming and SQLite-backed session resumability — no Node.js toolchain anywhere in the stack. Generated analysis narratives use Quarto (`.qmd`, plain text) rather than Jupyter notebooks, so they're diffable and PR-reviewable without binary-metadata merge conflicts.

**AI/LLM vendor posture.** Three backends are supported behind a single provider registry. Two are Claude: Anthropic's first-party API and AWS Bedrock (via `AnthropicBedrockMantle`). The third, added 2026-08-01, drives the `opencode` command-line agent as a subprocess and therefore reaches whichever vendor *that tool* is configured for — the intended answer to an enterprise environment standardized on a different AI CLI, and the first backend capable of reaching a non-Claude model family. Read its status precisely, though: it is shipped and unit-tested, but **no output-quality measurement exists for it**, so it is a built path rather than a validated alternative — and configured against Claude it is a third route to the same model family, not diversification. Selection is an explicit per-run choice, not automatic failover. This matters for an adoption decision in two ways: first, the choice of provider is also a choice of data processor, with distinct data-residency and contractual implications the deploying organization must own (see the security section below); second, and more materially for total cost of ownership — **the generated downstream project has no AI runtime dependency at all.** Its entire runtime dependency set is `pandas`, `scikit-learn`, and `sqlalchemy`. No API key, no LLM SDK, and no live network dependency on an AI vendor is baked into the deliverable itself — an outage or pricing change at the AI provider cannot affect a project that has already been handed off.

**Dependency and license hygiene.** 89 installed distributions as of the current lockfile, with **zero GPL-only, zero AGPL, and zero LGPL** dependencies — the two LGPL packages that previously existed (the GitLab and GitHub SDKs) were both removed and replaced with direct `httpx` calls. Three components remain MPL-2.0 (`certifi`, `orjson`, `pathspec` — all transitive, weak-copyleft, and low-friction under most enterprise open-source policies). Everything else is MIT, BSD, Apache-2.0, ISC, or PSF-2.0.

**Risks worth tracking, per the dependency audit:** the AWS SDK (`boto3`/`botocore`) installs unconditionally as part of the Anthropic extra even for Anthropic-only deployments, so its vulnerability surface needs patching regardless of which provider a deployment actually uses. LangSmith observability tooling ships in the tree but is dormant unless explicitly configured. There is no built-in rate limiter, backoff wrapper, or token-budget cap around LLM calls — a deploying organization wanting cost controls on interview/query generation would need to add this layer itself.

## Security, data, and governance posture

Full detail: [Security Considerations](Security-Considerations) and [Governance Framework](Governance-Framework).

All secrets come from the environment — no hardcoded credentials anywhere, `.env` gitignored. The credential surface is small and purpose-scoped: one git-host token, plus one LLM credential — an Anthropic API key, or the standard AWS credential chain (no static key) for Bedrock, or, on the OpenCode provider, no credential read by this project at all (that one lives in the operator's own OpenCode configuration, which also means the network destination on that provider is set outside this codebase). Outbound network calls happen from exactly four places: the LLM provider, the GitLab adapter, the GitHub adapter, and an optional read-only database connection. The intake web UI itself (`go/modelintake`) ships with no built-in authentication or authorization — it is designed to sit behind a reverse proxy that handles that (corporate SSO or an OAuth proxy); deployed directly on an open network interface, it would expose the interview surface — including the unredacted content described next — to anyone who can reach it.

**What the LLM sees, precisely.** The Intake Agent forwards a stakeholder's interview answers to the configured provider verbatim — there is no PII redaction or scrubbing layer anywhere in the codebase. A deployment must either constrain the interview from eliciting protected/PII detail, or independently satisfy the chosen provider's data-handling terms for what it does receive. The Data Agent's exposure is narrower and structurally bounded: it sees the data request and the SQL it generates, but **query result rows are never sent to the LLM** — only quality-check pass/fail summaries are. This means the Data Agent can safely target sensitive production tables, because raw row data structurally cannot reach the model.

**Production database exposure.** If a database URL is configured, the generated SQL executes automatically — there is no human-in-the-loop gate before that happens, and no in-process statement-type filter rejects a malformed or destructive query. The documented, intentional design is that safety is enforced at the credential layer: the connecting database role must itself be provisioned SELECT-only. This is a **hard operational prerequisite for any live deployment**, not an optional hardening step, and it should be verified as part of any environment's readiness checklist, not assumed from the pipeline's own behavior. (Executed query results are capped at five rows per check and do land in checkpoint files on disk, so checkpoint storage should itself be treated as holding production data.)

**Governance framework.** Every generated project carries governance artifacts scaled to a `risk_tier` (critical through low) assessed during intake, plus two independent flags — whether the model affects consumers, and whether it uses protected attributes — that trigger EU AI Act and fairness-audit artifacts respectively regardless of tier. Regulatory mapping covers SR 26-2, NAIC AIS, EU AI Act Articles 9-15, GDPR Article 22, and ASOP 56, and only ever cites artifacts that were actually generated for that project's tier. One caveat worth flagging to a compliance stakeholder: a true immutable audit-log scaffold is generated only at the highest risk tier; elsewhere, structured application logging exists but is explicitly documented as observability, not a compliance-grade audit trail.

## Deployment and operations model

Full detail: [Monitoring and Operations](Monitoring-and-Operations).

Configuration is entirely environment-variable driven — no hardcoded hosts, URLs, or secrets. No database server is required to run the orchestrator itself (state is JSON checkpoint files on disk; SQLite is used only for the optional web UI's session store), and no Docker is required for development. Compute needs are modest: whatever runs the orchestrator process, plus outbound HTTPS to the chosen Claude provider and git host.

Runs are resumable from checkpoint (`--resume <run_id>`), which re-executes only from the first incomplete stage. **One operational trap worth knowing up front:** re-running the same `run_id` *without* the resume flag overwrites prior work rather than resuming it. Observability is currently opt-in and lightweight rather than a managed-platform integration — structured start/end/error events with correlation IDs, and an in-memory metrics registry for run counts and per-agent latency. A managed metrics exporter (e.g., Prometheus) is explicitly scoped as future work, not shipped today.

**Concurrency and capacity planning — an open question, stated honestly.** Structurally, distinct runs share no mutable state: each is keyed by its own `run_id` and checkpoints to a separate directory, and the codebase is explicit that there is no database, no migrations, and no locking beyond that per-run isolation. What is *not* yet documented or load-tested is throughput at enterprise scale — how many concurrent interviews or pipeline runs a shared Anthropic or AWS Bedrock account can sustain before hitting provider-side rate limits, and what concurrency ceiling a multi-team rollout should plan around. Treat this as an open capacity-planning question to resolve during a pilot, not an already-answered one. The same applies to two adjacent gaps: there is no established backup or retention policy for checkpoint directories (and since executed query results land there, per the production-database note above, checkpoint storage should be placed on backed-up, access-controlled storage under the same retention obligations as the source data), and there is no measured cost baseline yet for the LLM side of total cost of ownership (tokens or dollars per typical Intake + Data Agent run). Both are pilot-stage measurements to take, not assumptions to budget against.

## Ownership and support model

This is not yet defined, and a sponsoring architect should treat that as a real gap to close before adoption, not an oversight in this document. The project today is built and operated as a single-maintainer, session-by-session engineering effort (see [Evolution](Evolution)) — there is no named owning team, on-call rotation, or escalation path, and the `CODEOWNERS`-style artifacts this pipeline generates are for the *downstream* projects it scaffolds, not for the pipeline itself. Bringing this in-house should include deciding who operates it going forward (a central platform team, a self-service tool for analyst teams, or something else), what on-call/escalation looks like once it runs against real claims data, and how that changes once the enterprise-clone decisions described below are made.

## Enterprise-readiness status — current, honest state

This is the section most relevant to an adoption decision, so it is stated plainly rather than rounded up.

**Genuinely done:** the legal/licensing packet (attribution, third-party license file, security policy, code-ownership); import-readiness classification (secrets attestation, asset registry); complete removal of LGPL dependencies; Bedrock-specific correctness work (regional-endpoint resolution for data residency, IAM policy artifacts, a guard that hard-fails if a bearer-token credential is present instead of proper IAM-role SigV4 signing); and making the CI configuration *this pipeline generates for downstream projects* target enterprise-internal package/container/CI-marketplace hosts instead of public ones.

**Genuinely open:** provisioning an actual enterprise-owned clone of this repository (the next phase in the plan) is fully gated and ready to execute, but has not yet run — not because of any remaining engineering work, but because it requires five decisions only the adopting enterprise can make at that moment (destination host, import strategy, contributor-agreement approach, wiki destination, and disposition of existing public releases). Two further phases — hardening the clone's own CI/supply-chain posture, and verifying the clone is truly independent of this public repository — are gated on that provisioning step and have not started.

**What this means concretely:** this system has **not yet been run end-to-end inside a real enterprise AWS account.** The one live AWS account tested to date was personal, not enterprise-owned, and failed on an account-eligibility/quota check for current-generation Claude models on Bedrock — a data-plane gate unrelated to this project's code. No claims-organization stakeholder has yet gone through a live intake interview; every interview exercised to date has been fixture- or script-driven. Separately, and worth knowing as a data point on engineering discipline rather than a red flag: this project built a formal, deterministic go/no-go gate (not a subjective judgment call) for cutting the default LLM provider over to an alternative, and that gate's standing verdict is **NO-GO** for both candidates — Anthropic's direct API remains primary; Bedrock stays implemented and unit-tested but unmeasured against live traffic, and the OpenCode provider likewise entered the gate unmeasured rather than being adopted on the strength of running successfully.

## Extensibility model

Five extension surfaces exist, each gated by a protocol, registry, or tier function rather than requiring a full codebase read (full detail: [Extending the Pipeline](Extending-the-Pipeline)):

| Extension | Relative effort | Mechanism |
|---|---|---|
| New pipeline agent | Highest | New schema, registry entry, full LangGraph agent package, new orchestrator runner + halt state, mirrored tests |
| New repo-host adapter (e.g., Bitbucket) | Light | One module implementing the two-method `RepoClient` protocol, plus one registry entry |
| New governance artifact | Content-only | One renderer wired into the existing tier-gated emission function; no schema or envelope change |
| New regulatory framework | Smallest | One registry entry mapping the framework to required artifacts, parity-guarded against the intake prompt |
| New LLM provider | Proven three times | One client module, one factory branch, one registry entry — exercised for Anthropic, Bedrock, and OpenCode; the last of those proved the seam also absorbs a non-SDK, subprocess-driven backend |

## Maturity and adoption status

As of the most recent recorded session, the suite stands at 1,110 tests passing plus 12 credential-gated live-evaluation tests that skip without provider credentials (1,122 collected), at 97.79% coverage against a 95% floor, with lint and type-checking both clean. That is a substantial, current verification signal — but it measures engineering rigor, not field use. The furthest this system has been exercised to date is developer-run live smoke tests against real GitLab and GitHub (including GitHub Enterprise) producing genuine scaffolded repositories. No real claims-organization stakeholder has used it in production yet. In short: this is a heavily governed, extensively tested engineering artifact that has not yet met its first real user — an honest "pre-adoption, not yet production-proven" characterization, not "early implementation" in the sense of incomplete.

## Where to go deeper

- [Pipeline Overview](Pipeline-Overview) — agent-by-agent input/output/behavior and the handoff protocol in detail
- [Architecture Decisions](Architecture-Decisions) — the full itemized decision log
- [Security Considerations](Security-Considerations) — credentials, network boundaries, what the LLM sees
- [Governance Framework](Governance-Framework) — risk tiers, regulatory mapping, artifact inventory
- [Software Bill of Materials](Software-Bill-of-Materials) — full dependency and license tables
- [AI Dependencies](AI-Dependencies) — the AI/LLM dependency surface and its risks
- [Monitoring and Operations](Monitoring-and-Operations) — deployment, checkpoints, troubleshooting
- [Evolution](Evolution) — how the project reached its current state
