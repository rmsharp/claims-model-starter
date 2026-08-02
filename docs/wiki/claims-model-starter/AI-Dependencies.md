# AI Dependencies

This page is for architects, security reviewers, compliance officers, and operators who need to understand the Model Project Constructor's reliance on artificial intelligence: **which** AI dependencies it has, **how** each one is used, and **what risks** they introduce. It is the AI-focused companion to the [Software Bill of Materials](Software-Bill-of-Materials) (full dependency tables) and [Security Considerations](Security-Considerations) (credentials, network boundaries, and what the LLM sees).

**Claim standard:** as with the [Security Considerations](Security-Considerations) page, every factual statement names a grep-locatable code symbol (class, function, method, or module constant) in its full-path defining file. Where something is *documented or proposed* rather than enforced in code, the page says so explicitly.

Three facts frame everything below:

1. The AI surface is **small and confined to two of the three agents** — the Intake Agent and the Data Agent. The Website Agent is fully deterministic.
2. There are **three AI providers, of which the two measured ones are a single model family**. `anthropic` (the default — first-party Claude, `claude-sonnet-4-6`) and `bedrock` (AWS Bedrock-hosted Claude) both reach Anthropic's Claude through the same `anthropic` SDK. A third, `opencode`, shells out to the `opencode` command-line agent instead of calling an SDK, and can therefore reach many vendors' models through the *operator's* own OpenCode configuration — but it is **shipped and unmeasured**, so it does not yet discharge the concentration risk in [§6.7](#67-provider-concentration). The provider is chosen per run; there is no automatic failover between them.
3. The **generated downstream project has zero AI runtime dependency.** All AI-produced content is materialised as static markdown, SQL, and Quarto narratives at construction time. The data-science team runs the output with no API key.

---

## 1. The AI surface at a glance

| Agent | Calls an LLM? | Uses LangGraph? | `ANTHROPIC_API_KEY` required? |
|---|---|---|---|
| **Intake Agent** | **Yes** — `AnthropicLLMClient`, `BedrockLLMClient`, or `OpenCodeLLMClient` | Yes — stateful interview + checkpointing | **Only on the `anthropic` provider** — `bedrock` authenticates from the AWS credential chain, and `opencode` from whatever the operator's own OpenCode config uses |
| **Data Agent** | **Yes** — `AnthropicLLMClient`, `BedrockLLMClient`, or `OpenCodeLLMClient` | Yes — query → QC → summary graph | **Only on the `anthropic` provider** — `bedrock` authenticates from the AWS credential chain, and `opencode` from whatever the operator's own OpenCode config uses |
| **Website Agent** | **No** — deterministic f-string templates | Yes — commit-retry state machine, **no LLM** | **No** |

Three things this table makes explicit:

- The Website Agent uses LangGraph for orchestration (its bounded commit-retry loop) but makes **no LLM calls**. Its modules (`src/model_project_constructor/agents/website/templates.py`, `src/model_project_constructor/agents/website/governance_templates.py`) contain no import of `anthropic` or any LLM client. AI is *not* on its critical path.
- `ANTHROPIC_API_KEY` is **not** required for website-only runs. The `agents` optional-dependency group installs `anthropic` for the whole pipeline, but installing a package is not the same as calling it. See [Security Considerations §2.1](Security-Considerations).
- **On the `opencode` provider the LLM call is a subprocess, not an SDK call.** `OpenCodeLLMClient` spawns the `opencode` binary per call and parses its JSON event stream. That moves one dependency out of the Python tree and into the host ([§2](#2-the-ai-software-dependencies)) and introduces an agentic intermediary between this project and the model ([§6.9](#69-the-opencode-provider-a-subprocess-agent-in-the-call-path)).

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

**One AI dependency is not a Python package.** The `opencode` provider adds **zero** rows to the table above — `OpenCodeLLMClient` is stdlib-only (`subprocess`, `json`, `shutil`, `tempfile`) and `pyproject.toml` is unchanged by it. What it adds instead is a **new class** of dependency: the `opencode` executable must be on `PATH` (installed from npm as `opencode-ai`), which means a Node.js runtime and, per the vendor's own behaviour, **npm-registry reachability at run time** — OpenCode materialises a `node_modules` tree inside the adapter's sandbox on first use, not at image-build time. Three consequences the other providers do not have: `uv.lock` does not pin it, so version drift is unmanaged by this project's own tooling (the client records the observed version in its error messages for exactly that reason); vulnerability scanning of the Python tree will not see it; and an air-gapped runtime needs the sandbox pre-seeded or the registry mirrored. The client fails fast at construction when the binary is absent rather than mid-interview.

---

## 3. The model as a dependency

The Claude model is itself a dependency — an external, versioned service, not a pinned wheel.

| Property | Value | Defined at |
|---|---|---|
| Default model (`anthropic` provider) | `claude-sonnet-4-6` | `DEFAULT_MODEL` in `src/model_project_constructor/agents/intake/anthropic_client.py` and `packages/data-agent/src/model_project_constructor_data_agent/anthropic_client.py` |
| Default model (`bedrock` provider) | `anthropic.claude-opus-4-8` — Bedrock model ids carry an `anthropic.` provider prefix | `DEFAULT_MODEL` in `src/model_project_constructor/agents/intake/bedrock_client.py` and `packages/data-agent/src/model_project_constructor_data_agent/bedrock_client.py`. The two provider defaults are deliberately independent — the Bedrock mantle catalog offers no Sonnet tier, so the Bedrock default is Opus while the first-party default stays Sonnet |
| Default model (`opencode` provider) | **None** — no model is pinned | `DEFAULT_MODEL` in both `opencode_client.py` modules is `None` on purpose: OpenCode model ids are `provider/model` strings, so naming one here would put the vendor choice back into *this* repository, which is the opposite of the adapter's purpose. `--model` is then omitted and the operator's own `opencode.json` decides. The cost is reproducibility, so an evaluated or production run must pass an explicit model — the eval tier reads one from `OPENCODE_EVAL_MODEL` and refuses to run without it |
| Max tokens per call | 16384 | `DEFAULT_MAX_TOKENS` in both `anthropic_client.py` modules — raised from 4096 in Session 167 because the large `draft_report` / `revise_report` JSON and the Data Agent's quality-check arrays overran 4096 and stopped with `stop_reason='max_tokens'` mid-JSON. Overridable per client via `max_tokens=`. **Inert on the `opencode` provider** — `opencode run` exposes no flag for it; the output ceiling lives in the operator's OpenCode model config, and the client raises an actionable error if a response comes back truncated |
| Endpoint (`anthropic`) | `https://api.anthropic.com` | Anthropic SDK default; no `base_url` override is exposed through the first-party constructor |
| Endpoint (`bedrock`) | The `bedrock-mantle` endpoint, resolved by the SDK from `aws_region` or, when unset, the environment's AWS region | Constructed in `bedrock_client.py`; region and credentials self-discover from the AWS credential chain — a set `AWS_BEARER_TOKEN_BEDROCK` silently replaces SigV4 with bearer auth unless `require_sigv4=True` is passed (default `False`, so unguarded by default — see [Security Considerations §1.2](Security-Considerations)). The client also accepts `base_url` / `http_client` keyword args for PrivateLink, GovCloud, and corporate-proxy deployments — see `docs/deployment/bedrock-enterprise.md`. |
| Endpoint (`opencode`) | **No endpoint of this project's choosing** — the local `opencode` process picks it | `OpenCodeLLMClient` spawns `opencode run --format json`. Which vendor and endpoint that reaches is entirely the operator's OpenCode configuration, so **the network destination is not determinable from this repository** — a fact security review needs stated plainly rather than inferred |
| Model override | `--model` CLI flag / `model=` factory arg | `make_llm_client(provider, *, model)` in both `factory.py` modules |

**The provider seam.** LLM client construction is routed through factory functions so the provider is named explicitly and each backend is a localised change, not a call-site rewrite:

- `make_llm_client` in `src/model_project_constructor/agents/intake/factory.py` (returns an `IntakeLLMClient`) and in `packages/data-agent/src/model_project_constructor_data_agent/factory.py` (returns an `LLMClient`).
- The known-provider list is single-sourced: `LLMProvider = Literal["anthropic", "bedrock", "opencode"]` with `KNOWN_PROVIDERS = get_args(LLMProvider)` in both factories, so an unknown-provider `ValueError` cannot drift from reality. The orchestrator keeps a parallel registry, `LLM_PROVIDERS` in `src/model_project_constructor/orchestrator/config.py`, carrying each provider's credential env var — `ANTHROPIC_API_KEY` for `anthropic`, and `None` for both `bedrock` (which authenticates from the AWS credential chain) and `opencode` (whose credential lives in the operator's own OpenCode configuration and is never read by this project). The three lists are kept in lockstep by convention, not by a parity test (the factories live in decoupled packages).
- Three providers are implemented today: `"anthropic"` (first-party API, `ANTHROPIC_API_KEY`), `"bedrock"` (AWS Bedrock-hosted Claude, credentials self-discovered from the AWS credential chain), and `"opencode"` (the `opencode` CLI as a subprocess transport). `make_llm_client` has a live branch for each, and the intake web UI resolves the provider from `INTAKE_LLM_PROVIDER` (`_resolve_provider` in `src/model_project_constructor/ui/intake/app.py`). The seam (the E4 overhaul, see [Architecture Decisions AD-2](Architecture-Decisions)) has therefore been exercised twice — but it remains a per-run *choice*, not an automatic multi-provider fallback, and **neither non-default branch has been exercised live**: `bedrock` for want of an eligible AWS account, `opencode` because its quality has not been measured (see [§6.7](#67-provider-concentration) and [§6.9](#69-the-opencode-provider-a-subprocess-agent-in-the-call-path)).
- **`BedrockLLMClient` and `OpenCodeLLMClient` both subclass `AnthropicLLMClient` and override only the transport.** Every prompt, every JSON-shape instruction, the report/governance dataclass builders and the `_extract_json` parser are inherited unchanged, which is what makes prompt drift between providers structurally impossible rather than merely discouraged. The consequence worth naming: the class a run uses is called `AnthropicLLMClient` in its base even when no Anthropic model is involved — the base class is the *prompt-and-parse* layer, not a vendor claim.

---

## 4. How each AI dependency is used

### 4.1 Intake Agent

- **Client.** `AnthropicLLMClient` in `src/model_project_constructor/agents/intake/anthropic_client.py` constructs `anthropic.Anthropic()` (SDK reads `ANTHROPIC_API_KEY` from the environment) and accepts an injected `client` for testing. Four methods make LLM calls — `next_question`, `draft_report`, `classify_governance`, `revise_report` — all routed through the `_call_json` helper. On the `bedrock` provider the factory returns `BedrockLLMClient` (`src/model_project_constructor/agents/intake/bedrock_client.py`), a subclass that overrides only construction and `DEFAULT_MODEL` and inherits all four methods unchanged. On `opencode` it returns `OpenCodeLLMClient` (`src/model_project_constructor/agents/intake/opencode_client.py`), the same pattern taken one step further: it overrides construction and `_call_json` itself — the single transport method — so the four interview methods are again inherited untouched, but the call underneath is a subprocess rather than an SDK request.
- **Prompts.** Two system prompts: `SYSTEM_INTERVIEWER` (the multi-turn interviewer) and `SYSTEM_GOVERNANCE` (risk-tier / framework classification), both in `anthropic_client.py`. The draft-report JSON shape is single-sourced from the Pydantic `Literal` schema members via `join_members()` in `_DRAFT_REPORT_INSTRUCTIONS`, so the prompt's enumerations cannot drift from the schema.
- **Graph.** `build_intake_graph` in `src/model_project_constructor/agents/intake/graph.py` wires an 8-node `IntakeState` graph and uses `langgraph.types.interrupt()` for human-in-the-loop at the `ask_user` and `await_review` nodes.
- **Bounded loops.** `MAX_QUESTIONS = 20` and `MAX_REVISIONS = 3` in `src/model_project_constructor/agents/intake/state.py` cap interview length and review cycles — the LLM cannot loop unboundedly.
- **Checkpointing.** Default `MemorySaver()`; the live web UI swaps in `SqliteSaver` (`IntakeSessionRunner` in `src/model_project_constructor/ui/intake/runner.py`) so an interview survives a process restart.

### 4.2 Data Agent

- **Client.** `AnthropicLLMClient` in `packages/data-agent/src/model_project_constructor_data_agent/anthropic_client.py`, same construction and injection pattern. Six methods call Claude: `generate_primary_queries`, `generate_quality_checks`, `summarize`, `generate_datasheet`, `generate_baseline_query`, and the optional `rank_candidate_tables` (dispatched via `hasattr`). All go through `_call_claude`. The `bedrock` provider swaps in `BedrockLLMClient` (`packages/data-agent/.../bedrock_client.py`) by the same subclass-only-the-constructor pattern; `opencode` swaps in `OpenCodeLLMClient` (`packages/data-agent/.../opencode_client.py`), which overrides construction plus `_call_claude` — the wheel's transport method — and inherits the six generation methods. The two packages' OpenCode clients are deliberate twins (the standalone wheel cannot import the orchestrator), kept honest by a behavioural parity battery in `tests/test_llm_json_parity.py` rather than by convention.
- **Graph and SQL retry.** `build_graph` in `packages/data-agent/src/model_project_constructor_data_agent/graph.py`. Generated SQL is checked by `validate_sql` and, on failure, retried exactly once — `MAX_SQL_RETRIES = 1` in `nodes.py` — before the graph takes the `fail_execution` off-ramp (`status="EXECUTION_FAILED"`).
- **What the LLM does and does not see.** The Data Agent asks Claude to *generate* SQL; it never feeds executed query rows back to the model. See [Security Considerations §3.2](Security-Considerations) for the verified data-flow.

### 4.3 What goes to the LLM

Stakeholder interview answers and the `DataRequest` JSON (target description, features, filters, `database_hint`) are forwarded to the selected provider — Anthropic on `anthropic`, AWS Bedrock on `bedrock`, and **whichever vendor the operator's OpenCode config routes to** on `opencode`. There is no redaction or PII filter. The full inventory of what each agent transmits is in [Security Considerations §3](Security-Considerations) — that analysis is not repeated here.

**On `opencode` the same text is also written to disk locally.** OpenCode persists each session's prompt and response text in a SQLite database under the invoking user's home directory (`~/.local/share/opencode/`). That store is **global to the machine and outlives the adapter's own ephemeral sandbox** — deleting the sandbox does not remove it. So on this provider, interview transcripts and `DataRequest` text land in a second at-rest location that neither this project's checkpoints nor its interview database account for. Verified by direct observation during the adapter's Phase 1 spike, not inferred from documentation. Operators subject to a data-retention policy should treat that path as in scope for it ([§7](#7-operator-checklist)).

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

Three providers are implemented (`anthropic`, `bedrock`, `opencode`), but the two that have ever produced a measured result serve the same model family (Claude) through the same `anthropic` SDK, and the provider is fixed for the duration of a run. There is no automatic failover.

- **Containment.** The provider seam ([§3](#3-the-model-as-a-dependency)) is designed so that adding a backend is one new client module plus one factory branch — no changes at the call sites ([Architecture Decisions AD-2](Architecture-Decisions)). `bedrock` is that seam exercised once, letting an operator move the trust boundary to an AWS account they control. `opencode` ([§9](#9-cli-adapter-portability-the-opencode-provider-shipped-2026-08-01)) is it exercised a second time and in a genuinely different direction: it does not use the `anthropic` SDK at all, so it is the first branch capable of reaching a different model family.
- **Residual — and read this before treating the third provider as a fix.** Neither non-default branch is live-validated. Every governance and evaluation result recorded in this project was produced on `anthropic`; the live-evaluation tier skips `bedrock` for want of credentials and skips `opencode` unless an operator explicitly opts in with a named model. **Shipping the `opencode` adapter did not by itself diversify anything**, for two independent reasons. First, capability: it reaches another vendor only if the operator's OpenCode configuration *points it at one* — configured against Claude, it is a third route to the same model family. Second, and more important, evidence: its output quality is entirely unmeasured, and it carries a specific, known degradation risk that the SDK providers do not ([§6.9](#69-the-opencode-provider-a-subprocess-agent-in-the-call-path)). Until the cutover gate has measured numbers, the honest status is *a built path, not a tested redundancy*. Provider choice also remains fixed per run, so an in-flight outage still has no fallback, and a defect in a shared SDK or model family is diversified away only by a switch that has actually been validated. Treating multi-provider resilience as "available" would still be over-claiming.

### 6.8 AI supply-chain surface

The AI integration pulls a transitive stack — `langchain-core`, `langsmith`, `tenacity`, plus the AWS SDK subtree (`boto3`, `botocore`) — behind the two directly-declared packages, and pins `langgraph` to a pre-1.0 line (`>=0.2,<0.3`).

- **The AWS SDK is installed whether or not Bedrock is used.** The `agents` extra declares `anthropic[bedrock]`, so `boto3` and `botocore` are in the locked tree on every install — `botocore` alone is the largest package in it. **Residual:** an `anthropic`-only deployment still carries, and must still patch, the AWS SDK's vulnerability surface. Dropping the extra would remove the `bedrock` provider entirely, so this is a deliberate trade, not an oversight.
- **LangSmith telemetry is dormant by default.** A `grep` for `langsmith|LANGCHAIN_TRACING|tracing_v2|LANGCHAIN_API_KEY` across `src/`, `packages/`, and `scripts/` returns **zero hits** — the tracing SDK ships in the dependency tree but the project never imports or activates it. It only begins egressing trace data if an **operator** sets the LangSmith environment variables (e.g. `LANGCHAIN_TRACING_V2`, `LANGSMITH_API_KEY`). **Residual / operator action:** do **not** set those variables in a production environment unless you intend to send interview and query metadata to LangSmith, and have cleared that egress with your data-handling policy.
- **Pre-1.0 framework churn.** The `langgraph<0.3` pin is deliberate — its API is not yet stable. **Residual:** a future LangGraph upgrade may require code changes; all versions are pinned in `uv.lock` so upgrades are explicit, not automatic. See the [SBOM](Software-Bill-of-Materials) for the full locked tree and the [Content Recommendations](Content-Recommendations) note on adding vulnerability scanning.

### 6.9 The `opencode` provider: a subprocess agent in the call path

This risk is specific to the third provider and has no analogue in the two SDK-backed ones. On `anthropic` and `bedrock` the project calls a completion API. On `opencode` it invokes an **autonomous coding agent** that happens to be able to answer a question — one that can take steps, use tools, and decide to do something other than reply. Four distinct exposures follow, each with what the adapter does about it and what remains.

- **The system prompt is demoted to user text, inside someone else's framing.** `opencode run` has no `--system` flag, so each call sends the system instructions and the user message concatenated as a single message. Worse for reasoning about it: a measurement during the adapter's verification spike found that a custom agent definition replaces roughly 4,720 tokens of OpenCode's built-in persona but leaves a **constant ~4,830-token scaffold in place that cannot be removed** — so this project's prompts are never the only instruction the model sees. **Containment:** the prompts, the JSON-shape instructions, and the parser are all inherited from the base client, so nothing was reworded for this provider, and one real payload was verified end-to-end to produce schema-valid, on-domain output. **Residual — the main one on this page:** that is a smoke test (one method, one model, a handful of runs), not a quality measurement. The failure mode to expect here is not breakage, which is loud and cheap, but **output that parses perfectly and is subtly worse** — a mis-tiered governance classification, a plausible-but-wrong value estimate. The cutover gate (`tests/eval/`, and `PHASE_E_AGREEMENT_REPORT.md` for the standing verdict) exists to catch exactly this, and against `opencode` every one of its thresholds is currently unmeasured.
- **The agent can touch the filesystem, and its default is not safe.** The adapter's design initially assumed OpenCode's permission prompts would auto-reject tool use in non-interactive mode. Live verification **disproved that**: without `--auto`, a run listed a directory, read a file, and disclosed its contents, exiting cleanly. **Containment:** the client therefore always writes an agent definition that denies `edit`, `write`, `bash`, `read`, and `webfetch`, always selects it, and runs with the working directory set to an ephemeral sandbox it owns; `--auto` is never passed, and a test pins that. There is deliberately **no** constructor option to run without the tool denial. **Residual:** those are two controls, not a proof — an operator who invokes `opencode` by other means, or configures permissions globally, is outside them.
- **Prompt content crosses a process boundary.** The prompt is written to the child's **stdin**, never passed as a command-line argument, so interview text cannot leak to any other user via the process table. Standard input is a pipe this project opens and closes rather than an inherited terminal (an inherited one hung a verification probe for its full timeout with no output). **Residual:** the child process still holds the text in its own memory and writes it to OpenCode's session database ([§4.3](#43-what-goes-to-the-llm)).
- **The event schema is an implementation detail, not a contract.** The client parses OpenCode's JSON event stream, and OpenCode ships releases daily. **Containment:** the parsing is pinned by verbatim captured fixtures from a known version, and the client reports the observed binary version in its error text so a schema break reads as "you are on a version we have not validated" rather than a mystery. **Residual:** an upgrade can break parsing at any time; treat a post-upgrade failure as a schema change until proven otherwise, and re-capture the fixtures rather than editing them.

---

## 7. Operator checklist

- [ ] Confirm whether interview content may contain PII, and either constrain it or clear the selected provider's data-handling terms — Anthropic's or AWS's ([§6.3](#63-third-party-data-exposure-and-pii)).
- [ ] Confirm the Data Agent's validation DB role is `SELECT`-only — the code does not block destructive SQL ([§6.2](#62-incorrect-or-hallucinated-output)).
- [ ] Ensure a human reviews the **risk-tier classification** and the generated SQL before either is trusted ([§6.2](#62-incorrect-or-hallucinated-output)).
- [ ] Confirm `LANGCHAIN_TRACING_V2` / `LANGSMITH_API_KEY` are **unset** unless LangSmith egress is intended ([§6.8](#68-ai-supply-chain-surface)).
- [ ] Decide how `429`/outage/cost is monitored — the project ships no limiter, backoff, or token budget ([§6.6](#66-availability-rate-limits-and-cost)).
- [ ] Re-validate the `DEFAULT_MODEL` pin against the selected provider's currently-available models before a production cutover ([§6.5](#65-model-and-version-drift)).
- [ ] Decide which provider a deployment runs on, and record who the data processor therefore is — Anthropic, AWS, or (on `opencode`) whichever vendor your OpenCode configuration selects. Neither non-default provider is live-validated here, so run your own verification before depending on either ([§6.7](#67-provider-concentration)).
- [ ] Treat all AI-generated SQL, narratives, and value estimates as drafts requiring review ([§6.1](#61-non-determinism-and-non-reproducibility)).

**If — and only if — a deployment selects the `opencode` provider, five more items apply** ([§6.9](#69-the-opencode-provider-a-subprocess-agent-in-the-call-path)). They are listed separately because they are inert on the two SDK providers:

- [ ] **Pin the `opencode` binary version** and record it. `uv.lock` does not cover it, the vendor ships releases daily, and the client's event parsing is validated against captured fixtures from one known version ([§2](#2-the-ai-software-dependencies)).
- [ ] **Pin the model explicitly on every run.** This provider deliberately ships no default model, so an unpinned run silently uses whatever the machine's `opencode.json` selects — which makes results non-reproducible and cost unpredictable ([§3](#3-the-model-as-a-dependency)).
- [ ] **Add `~/.local/share/opencode/` to your data-retention scope.** OpenCode persists prompt and response text — i.e. interview transcripts and request metadata — in a machine-global SQLite database that survives the adapter's own sandbox cleanup ([§4.3](#43-what-goes-to-the-llm)).
- [ ] **Confirm npm-registry reachability from wherever the pipeline runs**, not just from the image build. OpenCode materialises a `node_modules` tree into the sandbox at run time; an air-gapped runtime needs it pre-seeded or the registry mirrored ([§2](#2-the-ai-software-dependencies)).
- [ ] **Do not treat "it runs" as "it is good."** Measure it against the cutover gate before pointing production at it; the specific risk is silent quality degradation, not failure ([§6.9](#69-the-opencode-provider-a-subprocess-agent-in-the-call-path)).

---

## 8. Key files

| File | AI surface |
|---|---|
| `src/model_project_constructor/agents/intake/anthropic_client.py` | Intake LLM client, prompts, JSON parsing, model/token constants |
| `src/model_project_constructor/agents/intake/factory.py` | Intake provider seam (`make_llm_client`, `LLMProvider`) |
| `src/model_project_constructor/agents/intake/bedrock_client.py` | Intake Bedrock client (`BedrockLLMClient`) — subclasses `AnthropicLLMClient`, overriding only construction and the `anthropic.`-prefixed `DEFAULT_MODEL`; all four interview methods and the JSON parsing are inherited |
| `src/model_project_constructor/agents/intake/opencode_client.py` | Intake OpenCode client (`OpenCodeLLMClient`) — subprocess transport; overrides construction and `_call_json` only. Carries `AGENT_DEFINITION`, the tool-denying agent written into every sandbox, and the module docstring holds the safety rationale |
| `src/model_project_constructor/agents/intake/graph.py` / `state.py` | Intake LangGraph + `MAX_QUESTIONS` / `MAX_REVISIONS` |
| `src/model_project_constructor/agents/intake/fixture.py` | Deterministic `FixtureLLMClient` for tests |
| `src/model_project_constructor/ui/intake/runner.py` | `SqliteSaver` checkpointing for live interviews |
| `packages/data-agent/.../anthropic_client.py` | Data Agent LLM client, prompts, `_sanitize_prompt_field` |
| `packages/data-agent/.../factory.py` | Data Agent provider seam |
| `packages/data-agent/.../bedrock_client.py` | Data Agent Bedrock client — same subclassing pattern, kept inside the standalone wheel for the C4 decoupling boundary |
| `packages/data-agent/.../opencode_client.py` | Data Agent OpenCode client — the intake client's twin (the wheel cannot import the orchestrator); overrides `_call_claude`, the wheel's transport method |
| `tests/eval/eval_cutover.py` / `PHASE_E_AGREEMENT_REPORT.md` | The provider cutover gate and its standing verdict — what stops an unmeasured provider becoming the default |
| `packages/data-agent/.../graph.py` / `nodes.py` | Data Agent LangGraph + `MAX_SQL_RETRIES`, `validate_sql` |
| `packages/data-agent/.../sql_validation.py` | Coarse SQL well-formedness check (not a security filter) |
| `src/model_project_constructor/agents/website/templates.py` / `governance_templates.py` | Deterministic templating — **no LLM** |
| `pyproject.toml` / `packages/data-agent/pyproject.toml` / `uv.lock` | AI dependency declarations and locked versions |

---

## 9. CLI-adapter portability: the `opencode` provider (shipped 2026-08-01)

**Status: built, wired, and unmeasured.** The adapter this section originally *proposed* now exists — `"opencode"` is a live branch in both factories, with a client module per agent and a hermetic test tier. What has **not** happened is any measurement of its output quality, and until that lands the provider is a capability, not a recommendation ([§6.9](#69-the-opencode-provider-a-subprocess-agent-in-the-call-path)). The date on this heading matters more than usual: agentic CLI tooling moves fast (see the Gemini CLI finding below, and note that OpenCode itself ships releases daily), so re-verify the comparison below against current vendor docs rather than trusting this snapshot.

**Why this exists.** [§6.7](#67-provider-concentration) named the core gap: `anthropic` and `bedrock` were the only wired providers, and both serve the same model family through the same SDK. The provider seam ([§3](#3-the-model-as-a-dependency), [Architecture Decisions AD-2](Architecture-Decisions)) was built to make adding a real, differently-sourced backend cheap — but nothing had exercised that design goal. On 2026-08-01, prompted by an operator question about whether this pipeline could target enterprise environments standardized on a different AI CLI, four candidate agentic CLIs were researched as potential subprocess-driven `LLMClient`/`IntakeLLMClient` implementations, and the operator accepted a recommendation. This section records that research, the decision, and what was subsequently built — see also [Architecture Decisions AD-11](Architecture-Decisions#ad-11-cli-adapter-portability-opencode-selected-as-the-first-non-anthropic-provider-seam).

### 9.1 The decision

**Build the `OpenCodeLLMClient` adapter first.** Accepted by the operator on 2026-08-01 and since executed: a full design specification (`docs/planning/opencode-adapter-spec.md`), a live verification spike against the real binary, and the implementation itself. The research below is what led to the choice.

### 9.2 Candidates evaluated

| Tool | Headless mode | Structured output | Underlying model | Auth for automation | Verdict |
|---|---|---|---|---|---|
| **OpenCode** (`anomalyco/opencode`, formerly `sst/opencode`) | `opencode run "..." --format json`; `opencode serve` for a long-lived server | `--format json` emits a JSON event stream (exact schema not yet published — verify empirically) | **Vendor-agnostic multiplexer** — Vercel AI SDK + Models.dev, 75+ providers (Anthropic, OpenAI, Gemini, Bedrock, Azure, OpenRouter, local/self-hosted) | API-key env vars (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, etc.) for most providers; a few (GitHub Copilot, ChatGPT-Plus login) need interactive OAuth and are not CI-clean | **Selected.** One adapter unlocks many vendors via OpenCode's own config — matches the portability goal directly. |
| **Codex CLI** (`openai/codex`) | `codex exec "..."` — `--json` (JSONL event stream) or `--output-schema <file>` (schema-constrained final answer) | Yes — clean stdout/stderr separation even without `--json` | OpenAI's own models by default; `model_providers` config can reach other backends, but only ones speaking the OpenAI Responses/Chat-Completions wire format (a translation proxy like LiteLLM is needed for Anthropic-shaped backends) | `CODEX_API_KEY` / `codex login --with-api-key` — fully CI-viable; docs explicitly cover CI/scheduled-job use and ship an official `codex-action` GitHub Action | Good second candidate for a pure OpenAI *capability* comparison; doesn't advance portability the way OpenCode does — it's welded to OpenAI's wire protocol. |
| **Gemini CLI** (`google-gemini/gemini-cli`) | `gemini -p "..."` (also auto-triggers when stdin/stdout isn't a TTY) | `--output-format json` / `stream-json`; documented exit codes (0/1/42/53) for CI branching | Google/Gemini family only (Gemini API or Vertex AI backend, not swappable to another vendor) | `GEMINI_API_KEY` or Vertex AI service-account JSON — both CI-viable; "Login with Google" OAuth is explicitly documented as unusable headless | **Deprioritized.** Google discontinued Gemini CLI for free/personal accounts on **2026-06-18**, redirecting new investment to a separate closed-source "Antigravity CLI." Paid API-key/Vertex access still works, but this is a live maintenance-parity risk for a build meant to outlast this migration. |
| **GitHub Copilot CLI** (`github/copilot-cli`, npm `@github/copilot`) | `copilot -p "..." --allow-all-tools --no-ask-user` | `--output-format json` (JSONL event stream) | **Already a multiplexer** — routes among Anthropic Claude, OpenAI GPT, and Google Gemini per GitHub's own entitlement/routing policy | Requires a fine-grained PAT (`Copilot Requests` permission) or GitHub App token tied to a **paid, seat-assigned Copilot subscription** — not a portable API key; GitHub's Acceptable Use Policy flags "excessive automated/scripted use" as an abuse-detection trigger (soft risk, not a hard ban) | **Rejected as a provider target.** Wrapping it trades single-vendor lock-in for GitHub subscription/seat/policy lock-in — a lateral move, not a portability win, for this specific goal. |

*One caveat in the table above has since been resolved.* The OpenCode row's "exact schema not yet published — verify empirically" was treated as a hard prerequisite rather than a footnote: the event schema was first pinned from the vendor's own emitter source at a recorded commit, then confirmed against the running binary, and verbatim captures are committed as test fixtures. It is JSON Lines, one object per line, each carrying a `type` (`text`, `reasoning`, `tool_use`, `step_start`, `step_finish`, `error`) alongside session metadata.

### 9.3 What was built

**Shipped.** A new `LLMProvider` member (`"opencode"`) in both `factory.py` modules, one entry in the orchestrator's `LLM_PROVIDERS` registry, and one client module per agent (`agents/intake/opencode_client.py`, `packages/data-agent/.../opencode_client.py`), each spawning `opencode run --format json` per call and parsing its event stream.

**The design differs from the original sketch in one way worth recording.** The sketch above anticipated implementing `IntakeLLMClient`/`LLMClient` afresh, since no subprocess-driven client existed to subclass. What was built instead subclasses each package's `AnthropicLLMClient` and **overrides only the single transport method** — `_call_json` for intake, `_call_claude` for the data agent. The consequence is the reason for the choice: every prompt, every JSON-shape instruction, the dataclass builders, and the JSON parser are inherited rather than reimplemented, so the prompt text cannot drift between providers. The base class's name is then a slight misnomer on this provider — it is the prompt-and-parse layer, not a vendor claim.

**Verification, and its limits.** The spike ran seven probes against the real binary before any client code was written, and it corrected the specification in seven places, one of them a safety defect: the assumption that OpenCode's permission defaults were already safe in non-interactive mode proved **false** (a run read a file and disclosed its contents), which is why the tool-denying agent definition is mandatory rather than defence-in-depth ([§6.9](#69-the-opencode-provider-a-subprocess-agent-in-the-call-path)). The implementation ships with a hermetic test tier — no test spawns the binary, every fixture is a verbatim capture — plus a behavioural parity battery over the two packages' twin helpers. **None of that is a quality measurement.** No pipeline output has been produced through this provider and none of the eight cutover thresholds has a number against it; see `tests/eval/PHASE_E_AGREEMENT_REPORT.md` for the standing verdict, which remains "keep `anthropic` primary".

### 9.4 What would make this a genuine diversification

Two things, in order. **First, point it at a non-Anthropic model.** Configured against Claude, the adapter is a third route to the same model family — a transport change, not a vendor change. Choosing a different vendor is what §6.7's residual is actually asking for; choosing Claude isolates the transport change and makes a cleaner comparison. That trade-off is a measurement-design decision the operator owns, and it is still open. **Second, measure it.** The eval tier will run this provider only when an operator both installs the binary and names a model in `OPENCODE_EVAL_MODEL` — deliberately two signals, so that the tier can never start making billable calls simply because a developer happens to have the binary installed. Alongside quality, that run should report **cost per interview**: the provider carries a constant multi-thousand-token scaffold on every call that no quality threshold can see.

---

## Related pages

- [Security Considerations](Security-Considerations) — credential handling, network boundaries, exactly what the LLM sees, read-only DB contract.
- [Software Bill of Materials](Software-Bill-of-Materials) — full dependency tables, transitive tree, and locked versions.
- [Architecture Decisions](Architecture-Decisions) — AD-2 (LangGraph + provider seam), AD-9 (no LLM-generated SQL executes against production), AD-11 (CLI-adapter portability decision, OpenCode selected).
- [Agent Reference](Agent-Reference) — per-agent inputs, outputs, and failure modes.
- [Governance Framework](Governance-Framework) — what the LLM's governance classification drives.
