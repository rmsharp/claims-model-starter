# AI Dependencies

This page is for architects, security reviewers, compliance officers, and operators who need to understand the Model Project Constructor's reliance on artificial intelligence: **which** AI dependencies it has, **how** each one is used, and **what risks** they introduce. It is the AI-focused companion to the [Software Bill of Materials](Software-Bill-of-Materials) (full dependency tables) and [Security Considerations](Security-Considerations) (credentials, network boundaries, and what the LLM sees).

**Claim standard:** as with the [Security Considerations](Security-Considerations) page, every factual statement names a grep-locatable code symbol (class, function, method, or module constant) in its full-path defining file. Where something is *documented or proposed* rather than enforced in code, the page says so explicitly.

Three facts frame everything below:

1. The AI surface is **small and confined to two of the three agents** — the Intake Agent and the Data Agent. The Website Agent is fully deterministic.
2. There are **two AI providers but one model family**: Anthropic's Claude, reached either through the first-party Anthropic API (provider `anthropic`, the default — `claude-sonnet-4-6`) or through AWS Bedrock-hosted Claude (provider `bedrock`). Both go through the same `anthropic` SDK. The provider is chosen per run; there is no automatic failover between them.
3. The **generated downstream project has zero AI runtime dependency.** All AI-produced content is materialised as static markdown, SQL, and Quarto narratives at construction time. The data-science team runs the output with no API key.

---

## 1. The AI surface at a glance

| Agent | Calls an LLM? | Uses LangGraph? | `ANTHROPIC_API_KEY` required? |
|---|---|---|---|
| **Intake Agent** | **Yes** — `AnthropicLLMClient` or `BedrockLLMClient` | Yes — stateful interview + checkpointing | **Only on the `anthropic` provider** — `bedrock` authenticates from the AWS credential chain instead |
| **Data Agent** | **Yes** — `AnthropicLLMClient` or `BedrockLLMClient` | Yes — query → QC → summary graph | **Only on the `anthropic` provider** — `bedrock` authenticates from the AWS credential chain instead |
| **Website Agent** | **No** — deterministic f-string templates | Yes — commit-retry state machine, **no LLM** | **No** |

Two things this table makes explicit:

- The Website Agent uses LangGraph for orchestration (its bounded commit-retry loop) but makes **no LLM calls**. Its modules (`src/model_project_constructor/agents/website/templates.py`, `src/model_project_constructor/agents/website/governance_templates.py`) contain no import of `anthropic` or any LLM client. AI is *not* on its critical path.
- `ANTHROPIC_API_KEY` is **not** required for website-only runs. The `agents` optional-dependency group installs `anthropic` for the whole pipeline, but installing a package is not the same as calling it. See [Security Considerations §2.1](Security-Considerations).

---

## 2. The AI software dependencies

These are the packages that exist in the tree *because of* the AI integration. Version constraints are from `pyproject.toml` (root) and `packages/data-agent/pyproject.toml`; locked versions are from `uv.lock`.

| Package | Constraint | Locked | Sourcing | Role |
|---|---|---|---|---|
| `anthropic[bedrock]` | `>=0.94` | 0.94.1 | Direct (`agents` extra; also a Data Agent core dep) | Official Claude API client — every LLM call goes through it. The `[bedrock]` extra pulls `boto3`/`botocore` in for the AWS Bedrock provider, on the release that ships `AnthropicBedrockMantle`. |
| `boto3` | (transitive) | 1.43.32 | Pulled in by the `anthropic[bedrock]` extra | AWS SDK — present only because of the Bedrock provider |
| `botocore` | (transitive) | 1.43.32 | Pulled in by `boto3` / the `anthropic[bedrock]` extra | AWS SigV4 request signing and credential-chain resolution; the largest package in the locked tree (~15 MB sdist) |
| `langgraph` | `>=0.2,<0.3` | 0.2.76 | Direct (`agents`) | Agent state-machine / graph execution for all three agents |
| `langgraph-checkpoint-sqlite` | `>=2.0,<3` | 2.0.11 | Direct (`ui` extra) | SQLite-backed checkpointing for resumable live interviews |
| `langchain-core` | (transitive) | 0.3.84 | Pulled in by `langgraph` | Base types and protocols LangGraph builds on |
| `langsmith` | (transitive) | 0.7.30 | Pulled in by `langchain-core` | Observability SDK — **dormant unless env-enabled** (see [§6.8](#68-ai-supply-chain-surface)) |
| `tenacity` | (transitive) | 9.1.4 | Pulled in by `langchain-core` | Retry primitives used internally by the LangChain stack |

The base project (no extras) depends only on `pydantic`, `pyyaml`, and the Data Agent subpackage — none of which is AI-specific. The AI surface is opt-in via the `agents` and `ui` extras. For the full transitive tree, see the [SBOM](Software-Bill-of-Materials).

---

## 3. The model as a dependency

The Claude model is itself a dependency — an external, versioned service, not a pinned wheel.

| Property | Value | Defined at |
|---|---|---|
| Default model (`anthropic` provider) | `claude-sonnet-4-6` | `DEFAULT_MODEL` in `src/model_project_constructor/agents/intake/anthropic_client.py` and `packages/data-agent/src/model_project_constructor_data_agent/anthropic_client.py` |
| Default model (`bedrock` provider) | `anthropic.claude-opus-4-8` — Bedrock model ids carry an `anthropic.` provider prefix | `DEFAULT_MODEL` in `src/model_project_constructor/agents/intake/bedrock_client.py` and `packages/data-agent/src/model_project_constructor_data_agent/bedrock_client.py`. The two provider defaults are deliberately independent — the Bedrock mantle catalog offers no Sonnet tier, so the Bedrock default is Opus while the first-party default stays Sonnet |
| Max tokens per call | 16384 | `DEFAULT_MAX_TOKENS` in both `anthropic_client.py` modules — raised from 4096 in Session 167 because the large `draft_report` / `revise_report` JSON and the Data Agent's quality-check arrays overran 4096 and stopped with `stop_reason='max_tokens'` mid-JSON. Overridable per client via `max_tokens=` |
| Endpoint (`anthropic`) | `https://api.anthropic.com` | Anthropic SDK default; no `base_url` override is exposed through the first-party constructor |
| Endpoint (`bedrock`) | The `bedrock-mantle` endpoint, resolved by the SDK from `aws_region` or, when unset, the environment's AWS region | Constructed in `bedrock_client.py`; region and credentials self-discover from the AWS credential chain — a set `AWS_BEARER_TOKEN_BEDROCK` silently replaces SigV4 with bearer auth unless `require_sigv4=True` is passed (default `False`, so unguarded by default — see [Security Considerations §1.2](Security-Considerations)). The client also accepts `base_url` / `http_client` keyword args for PrivateLink, GovCloud, and corporate-proxy deployments — see `docs/deployment/bedrock-enterprise.md`. |
| Model override | `--model` CLI flag / `model=` factory arg | `make_llm_client(provider, *, model)` in both `factory.py` modules |

**The provider seam.** LLM client construction is routed through factory functions so the provider is named explicitly and each backend is a localised change, not a call-site rewrite:

- `make_llm_client` in `src/model_project_constructor/agents/intake/factory.py` (returns an `IntakeLLMClient`) and in `packages/data-agent/src/model_project_constructor_data_agent/factory.py` (returns an `LLMClient`).
- The known-provider list is single-sourced: `LLMProvider = Literal["anthropic", "bedrock"]` with `KNOWN_PROVIDERS = get_args(LLMProvider)` in both factories, so an unknown-provider `ValueError` cannot drift from reality. The orchestrator keeps a parallel registry, `LLM_PROVIDERS` in `src/model_project_constructor/orchestrator/config.py`, carrying each provider's credential env var — `ANTHROPIC_API_KEY` for `anthropic`, and `None` for `bedrock`, which authenticates from the AWS credential chain rather than a single key. The two lists are kept in lockstep by convention, not by a parity test (the factories live in decoupled packages).
- Two providers are implemented today: `"anthropic"` (first-party API, `ANTHROPIC_API_KEY`) and `"bedrock"` (AWS Bedrock-hosted Claude, credentials self-discovered from the AWS credential chain). `make_llm_client` has a live branch for each, and the intake web UI resolves the provider from `INTAKE_LLM_PROVIDER` (`_resolve_provider` in `src/model_project_constructor/ui/intake/app.py`). The seam (the E4 overhaul, see [Architecture Decisions AD-2](Architecture-Decisions)) has therefore been exercised once — but it remains a per-run *choice*, not an automatic multi-provider fallback, and the `bedrock` branch has **not been exercised live** (see [§6.7](#67-provider-concentration)).

---

## 4. How each AI dependency is used

### 4.1 Intake Agent

- **Client.** `AnthropicLLMClient` in `src/model_project_constructor/agents/intake/anthropic_client.py` constructs `anthropic.Anthropic()` (SDK reads `ANTHROPIC_API_KEY` from the environment) and accepts an injected `client` for testing. Four methods make LLM calls — `next_question`, `draft_report`, `classify_governance`, `revise_report` — all routed through the `_call_json` helper. On the `bedrock` provider the factory returns `BedrockLLMClient` (`src/model_project_constructor/agents/intake/bedrock_client.py`), a subclass that overrides only construction and `DEFAULT_MODEL` and inherits all four methods unchanged.
- **Prompts.** Two system prompts: `SYSTEM_INTERVIEWER` (the multi-turn interviewer) and `SYSTEM_GOVERNANCE` (risk-tier / framework classification), both in `anthropic_client.py`. The draft-report JSON shape is single-sourced from the Pydantic `Literal` schema members via `join_members()` in `_DRAFT_REPORT_INSTRUCTIONS`, so the prompt's enumerations cannot drift from the schema.
- **Graph.** `build_intake_graph` in `src/model_project_constructor/agents/intake/graph.py` wires an 8-node `IntakeState` graph and uses `langgraph.types.interrupt()` for human-in-the-loop at the `ask_user` and `await_review` nodes.
- **Bounded loops.** `MAX_QUESTIONS = 20` and `MAX_REVISIONS = 3` in `src/model_project_constructor/agents/intake/state.py` cap interview length and review cycles — the LLM cannot loop unboundedly.
- **Checkpointing.** Default `MemorySaver()`; the live web UI swaps in `SqliteSaver` (`IntakeSessionRunner` in `src/model_project_constructor/ui/intake/runner.py`) so an interview survives a process restart.

### 4.2 Data Agent

- **Client.** `AnthropicLLMClient` in `packages/data-agent/src/model_project_constructor_data_agent/anthropic_client.py`, same construction and injection pattern. Six methods call Claude: `generate_primary_queries`, `generate_quality_checks`, `summarize`, `generate_datasheet`, `generate_baseline_query`, and the optional `rank_candidate_tables` (dispatched via `hasattr`). All go through `_call_claude`. The `bedrock` provider swaps in `BedrockLLMClient` (`packages/data-agent/.../bedrock_client.py`) by the same subclass-only-the-constructor pattern.
- **Graph and SQL retry.** `build_graph` in `packages/data-agent/src/model_project_constructor_data_agent/graph.py`. Generated SQL is checked by `validate_sql` and, on failure, retried exactly once — `MAX_SQL_RETRIES = 1` in `nodes.py` — before the graph takes the `fail_execution` off-ramp (`status="EXECUTION_FAILED"`).
- **What the LLM does and does not see.** The Data Agent asks Claude to *generate* SQL; it never feeds executed query rows back to the model. See [Security Considerations §3.2](Security-Considerations) for the verified data-flow.

### 4.3 What goes to the LLM

Stakeholder interview answers and the `DataRequest` JSON (target description, features, filters, `database_hint`) are forwarded to the selected provider — Anthropic on `anthropic`, AWS Bedrock on `bedrock`. There is no redaction or PII filter. The full inventory of what each agent transmits is in [Security Considerations §3](Security-Considerations) — that analysis is not repeated here.

---

## 5. What is **not** AI-dependent

- **The Website Agent** templates every file deterministically from the upstream reports (`templates.py`, `governance_templates.py`). Same inputs → byte-for-byte same output. See [Architecture Decisions AD-4](Architecture-Decisions).
- **The generated project.** Its dependency set is `pandas` + `scikit-learn` + `sqlalchemy` (see [SBOM Part 2](Software-Bill-of-Materials)). It carries **no `anthropic`, no `langgraph`, no API key**. AI participated in *constructing* it, but is absent at *runtime*. This is the single most important risk-containment property in the whole design: a flaw, outage, or cost spike in the AI provider cannot affect a model the data-science team has already received.

---

## 6. Risks

Each risk below states what it is, why it matters *here*, what the project does to contain it (with a cited symbol), and the residual exposure the operator owns.

### 6.1 Non-determinism and non-reproducibility

LLM output varies run to run. The same interview, replayed, can yield different questions, a differently-worded report, or different SQL.

- **Containment.** Every LLM response is parsed and validated against a Pydantic schema at the boundary (`_extract_json` in both `anthropic_client.py` modules; `StrictBase` with `extra="forbid"` on Data Agent schemas), so *malformed* output is rejected rather than silently accepted. Deterministic fixture clients (`FixtureLLMClient` in `src/model_project_constructor/agents/intake/fixture.py`; `_FakeCLIClient` in the Data Agent `cli.py`) make the test suite reproducible without the model.
- **Residual.** *Well-formed but different* output is expected and not an error. Treat all generated SQL, narratives, and value estimates as **drafts for human review**, never as final artifacts. Do not expect bit-identical re-runs.

### 6.2 Incorrect or hallucinated output

A schema-valid response can still be wrong. Three sub-cases matter:

- **Generated SQL.** `validate_sql` (`packages/data-agent/.../sql_validation.py`) is a coarse well-formedness check — it will not catch a well-formed `DROP TABLE` or a semantically wrong query. Containment is layered: the LLM is prompted for `SELECT`s, queries are **not executed against production** as part of the pipeline ([Architecture Decisions AD-9](Architecture-Decisions)), the optional validation DB must be a `SELECT`-only role ([Security Considerations §4](Security-Considerations)), and queries land in `queries/` for the data-science team to review. **Residual:** a wrong-but-runnable query that a reviewer misses; the DB role — not the code — is the backstop against a destructive statement.
- **Governance misclassification.** `classify_governance` assigns the risk tier, cycle time, and regulatory frameworks that drive which governance artifacts get emitted ([Governance Framework](Governance-Framework)). A tier set too low under-scopes compliance documentation. **Containment:** the stakeholder reviews the draft (`await_review`, up to `MAX_REVISIONS = 3`), and a CI parity test asserts the framework registry matches the artifact map. **Residual:** the human reviewer must actively confirm the risk tier — an unchallenged misclassification propagates into the scaffold.
- **Value estimates.** `EstimatedValue` figures are LLM-elicited from the interview. They carry an explicit `confidence` field (`low`/`medium`/`high`) and `assumptions` precisely because they are estimates. **Residual:** finance/actuarial review is required before any number is treated as a business commitment.

### 6.3 Third-party data exposure and PII

Stakeholder answers and request metadata are transmitted verbatim to the selected provider. A `grep` for `redact|pii|scrub|mask|sanitize` in `src/` returns zero hits — there is no PII filter.

- **Containment.** Query result **rows are never sent to the LLM** (Data Agent — see [Security Considerations §3.2](Security-Considerations)); checkpoints on disk carry payloads, not credentials ([Security Considerations §5.2](Security-Considerations)).
- **Residual.** Any policyholder-identifying detail a stakeholder types into the interview reaches the provider. The deployment must either constrain the interview to exclude PII or satisfy that provider's data-handling terms — **which provider is selected changes who the processor is**: `anthropic` sends the text to Anthropic, `bedrock` sends it to AWS in the configured region, and the two carry different contracts and different data-residency positions. This is a **policy decision the operator owns**, not something the code resolves.

### 6.4 Prompt injection

Untrusted text flows into prompts from two directions: stakeholder free-text answers, and database object descriptions surfaced by schema discovery.

- **Containment.** Discovered inventory fields are passed through `_sanitize_prompt_field` (`packages/data-agent/.../anthropic_client.py`), which strips control characters and truncates each field at `MAX_INVENTORY_FIELD_CHARS = 2000` before rendering them into the prompt. It is applied to `DataSourceEntry.description` and `DataSourceEntry.relevance_reason`. All agents request structured JSON output that is then schema-validated, which limits how far an injected instruction can propagate.
- **Residual.** That sanitizer covers **only discovery-sourced inventory fields** — interview answers and the `DataRequest` free-text fields are **not** put through the same filter. A crafted stakeholder answer could attempt to steer the interview or the governance classification. The human review gates ([§6.2](#62-incorrect-or-hallucinated-output)) are the practical backstop; there is no automated prompt-injection detector.

### 6.5 Model and version drift

`DEFAULT_MODEL` is pinned to a model chosen at authoring time. Providers retire models and ship behavior-changing new versions.

- **Containment.** The model is overridable per run (`--model` / factory `model=`), so an operator can move off a deprecated ID without a code change. An invalid ID fails fast at the first call ([Security Considerations §10.8](Security-Considerations)) rather than silently degrading.
- **Residual.** The default pin can go stale; a model retirement breaks live runs until the default is updated. There is **no model-version contract test** that would catch a silent behavioral change after a provider-side update — outputs should be spot-checked after any deliberate model change.

### 6.6 Availability, rate limits, and cost

The pipeline depends on one external API per run for its AI steps. An outage at the selected provider halts the Intake and Data agents.

- **Containment.** Website-only runs need no LLM, so the final scaffolding step is insulated. Failures surface cleanly as typed exceptions (`IntakeLLMError` in the intake `protocol.py`; `LLMParseError` in the Data Agent `anthropic_client.py`) at the LangGraph node boundary, and the interview's checkpoint allows resumption.
- **Residual.** The project adds **no rate-limiter, no backoff wrapper, and no token budget of its own** around LLM calls ([Security Considerations §10.4–10.5](Security-Considerations)); a per-run token cap and 429 backoff are *proposed in the architecture plan but not implemented*. Provider-side `429`/`5xx` responses, latency, and per-token cost are the operator's to monitor and absorb.

### 6.7 Provider concentration

Two providers are implemented (`anthropic`, `bedrock`), but both serve the same model family (Claude) through the same `anthropic` SDK, and the provider is fixed for the duration of a run. There is no automatic failover.

- **Containment.** The provider seam ([§3](#3-the-model-as-a-dependency)) is designed so that adding a backend is one new client module plus one factory branch — no changes at the call sites ([Architecture Decisions AD-2](Architecture-Decisions)). `bedrock` is that seam exercised once, and it lets an operator move the trust boundary to an AWS account they control.
- **Residual.** The `bedrock` backend is **implemented but not live-validated** — every governance and evaluation result recorded in this project was produced on the `anthropic` provider, and the live-evaluation test tier skips `bedrock` for want of credentials. Treat it as a documented migration path, not a tested redundancy: a cutover needs its own live verification first. Provider choice is also fixed per run, so an in-flight Anthropic outage still has no fallback path — and because both providers serve one model family through one SDK, a defect in that SDK or that model family is not diversified away by switching. Treating multi-provider resilience as "available" would be over-claiming.

### 6.8 AI supply-chain surface

The AI integration pulls a transitive stack — `langchain-core`, `langsmith`, `tenacity`, plus the AWS SDK subtree (`boto3`, `botocore`) — behind the two directly-declared packages, and pins `langgraph` to a pre-1.0 line (`>=0.2,<0.3`).

- **The AWS SDK is installed whether or not Bedrock is used.** The `agents` extra declares `anthropic[bedrock]`, so `boto3` and `botocore` are in the locked tree on every install — `botocore` alone is the largest package in it. **Residual:** an `anthropic`-only deployment still carries, and must still patch, the AWS SDK's vulnerability surface. Dropping the extra would remove the `bedrock` provider entirely, so this is a deliberate trade, not an oversight.
- **LangSmith telemetry is dormant by default.** A `grep` for `langsmith|LANGCHAIN_TRACING|tracing_v2|LANGCHAIN_API_KEY` across `src/`, `packages/`, and `scripts/` returns **zero hits** — the tracing SDK ships in the dependency tree but the project never imports or activates it. It only begins egressing trace data if an **operator** sets the LangSmith environment variables (e.g. `LANGCHAIN_TRACING_V2`, `LANGSMITH_API_KEY`). **Residual / operator action:** do **not** set those variables in a production environment unless you intend to send interview and query metadata to LangSmith, and have cleared that egress with your data-handling policy.
- **Pre-1.0 framework churn.** The `langgraph<0.3` pin is deliberate — its API is not yet stable. **Residual:** a future LangGraph upgrade may require code changes; all versions are pinned in `uv.lock` so upgrades are explicit, not automatic. See the [SBOM](Software-Bill-of-Materials) for the full locked tree and the [Content Recommendations](Content-Recommendations) note on adding vulnerability scanning.

---

## 7. Operator checklist

- [ ] Confirm whether interview content may contain PII, and either constrain it or clear the selected provider's data-handling terms — Anthropic's or AWS's ([§6.3](#63-third-party-data-exposure-and-pii)).
- [ ] Confirm the Data Agent's validation DB role is `SELECT`-only — the code does not block destructive SQL ([§6.2](#62-incorrect-or-hallucinated-output)).
- [ ] Ensure a human reviews the **risk-tier classification** and the generated SQL before either is trusted ([§6.2](#62-incorrect-or-hallucinated-output)).
- [ ] Confirm `LANGCHAIN_TRACING_V2` / `LANGSMITH_API_KEY` are **unset** unless LangSmith egress is intended ([§6.8](#68-ai-supply-chain-surface)).
- [ ] Decide how `429`/outage/cost is monitored — the project ships no limiter, backoff, or token budget ([§6.6](#66-availability-rate-limits-and-cost)).
- [ ] Re-validate the `DEFAULT_MODEL` pin against the selected provider's currently-available models before a production cutover ([§6.5](#65-model-and-version-drift)).
- [ ] Decide which provider a deployment runs on, and record who the data processor therefore is — Anthropic or AWS. If choosing `bedrock`, run your own live verification first: it is implemented but **not live-validated** here ([§6.7](#67-provider-concentration)).
- [ ] Treat all AI-generated SQL, narratives, and value estimates as drafts requiring review ([§6.1](#61-non-determinism-and-non-reproducibility)).

---

## 8. Key files

| File | AI surface |
|---|---|
| `src/model_project_constructor/agents/intake/anthropic_client.py` | Intake LLM client, prompts, JSON parsing, model/token constants |
| `src/model_project_constructor/agents/intake/factory.py` | Intake provider seam (`make_llm_client`, `LLMProvider`) |
| `src/model_project_constructor/agents/intake/bedrock_client.py` | Intake Bedrock client (`BedrockLLMClient`) — subclasses `AnthropicLLMClient`, overriding only construction and the `anthropic.`-prefixed `DEFAULT_MODEL`; all four interview methods and the JSON parsing are inherited |
| `src/model_project_constructor/agents/intake/graph.py` / `state.py` | Intake LangGraph + `MAX_QUESTIONS` / `MAX_REVISIONS` |
| `src/model_project_constructor/agents/intake/fixture.py` | Deterministic `FixtureLLMClient` for tests |
| `src/model_project_constructor/ui/intake/runner.py` | `SqliteSaver` checkpointing for live interviews |
| `packages/data-agent/.../anthropic_client.py` | Data Agent LLM client, prompts, `_sanitize_prompt_field` |
| `packages/data-agent/.../factory.py` | Data Agent provider seam |
| `packages/data-agent/.../bedrock_client.py` | Data Agent Bedrock client — same subclassing pattern, kept inside the standalone wheel for the C4 decoupling boundary |
| `packages/data-agent/.../graph.py` / `nodes.py` | Data Agent LangGraph + `MAX_SQL_RETRIES`, `validate_sql` |
| `packages/data-agent/.../sql_validation.py` | Coarse SQL well-formedness check (not a security filter) |
| `src/model_project_constructor/agents/website/templates.py` / `governance_templates.py` | Deterministic templating — **no LLM** |
| `pyproject.toml` / `packages/data-agent/pyproject.toml` / `uv.lock` | AI dependency declarations and locked versions |

---

## Related pages

- [Security Considerations](Security-Considerations) — credential handling, network boundaries, exactly what the LLM sees, read-only DB contract.
- [Software Bill of Materials](Software-Bill-of-Materials) — full dependency tables, transitive tree, and locked versions.
- [Architecture Decisions](Architecture-Decisions) — AD-2 (LangGraph + provider seam), AD-9 (no LLM-generated SQL executes against production).
- [Agent Reference](Agent-Reference) — per-agent inputs, outputs, and failure modes.
- [Governance Framework](Governance-Framework) — what the LLM's governance classification drives.
