# Architecture Decisions

Key design choices and their rationale. For the full architecture plan, see `docs/architecture-history/architecture-plan.md` (archived concept-era plan). For a higher-altitude synthesis (tradeoffs, vendor posture, enterprise-readiness status), see [Architecture Overview](Architecture-Overview).

## AD-1: Sequential pipeline, not parallel agents

**Decision:** Agents run in strict sequence (Intake -> Data -> Website), not in parallel.

**Rationale:** Each agent's output is the next agent's input. There is no useful work the Data Agent can do without the IntakeReport, and the Website Agent needs both reports. A sequential pipeline is simpler to debug, checkpoint, and reason about. The orchestrator can be upgraded to support parallel branches later if new agents with independent inputs are added.

## AD-2: LangGraph for agent orchestration

**Decision:** Use LangGraph (v0.2) as the agent framework, with direct Anthropic SDK calls.

**Rationale:** LangGraph provides built-in checkpointing for long-lived conversations (essential for the intake interview, which may span multiple user sessions). The Anthropic SDK is used directly rather than through LangChain's model abstraction. As of E4 (Sessions 132-133), LLM client construction is abstracted via provider factories in both agents (src/.../agents/intake/factory.py and packages/data-agent/.../factory.py), each wired to a LangGraph-agnostic protocol (`IntakeLLMClient` and `LLMClient`). This allows backend swapping via the CLI `--provider` flag without modifying the agent logic. Three providers are wired: `anthropic` (the first-party API, keyed by `ANTHROPIC_API_KEY`), `bedrock` (AWS Bedrock-hosted Claude, Session 162), and `opencode` (the `opencode` CLI as a subprocess transport, Session 213 — see AD-11). Bedrock is why the orchestrator's `LLM_PROVIDERS` registry makes the credential env var *optional* — it authenticates through the AWS credential chain (IAM role, SSO, shared profile, or instance metadata) plus a region rather than an API key, so its `LLMProviderSpec.api_key_env_var` is `None` and `require_llm_api_key` refuses it with a pointed message instead of inventing a variable name; `opencode` registers the same way, because its credential lives in the operator's own OpenCode configuration and this project never reads it. **Neither non-default path has been exercised live**: `bedrock` is wired and unit-tested but has never reached a live endpoint, and `opencode` is wired and unit-tested but entirely unmeasured for output quality. The live evaluation tier auto-skips both, so every live result recorded in this project is `anthropic`-only.

## AD-3: Pydantic schemas, not JSON Schema or protobuf

**Decision:** All inter-agent schemas are Pydantic v2 models.

**Rationale:** The entire project is Python. Pydantic provides runtime validation, JSON Schema export (for documentation), and cross-field validators. Protobuf would add a build step and code generation. JSON Schema alone lacks runtime validation. The `HandoffEnvelope` pattern wraps every payload with version metadata for forward compatibility.

## AD-4: f-string templates, not Jinja2 or Mako

**Decision:** All generated project files use Python f-strings, not a template engine.

**Rationale:** The templates are straightforward string interpolation with no loops, conditionals, or inheritance. An f-string approach means: (1) no template engine dependency, (2) byte-for-byte reproducible output for a given input, (3) templates are testable as pure functions, (4) no template syntax errors at runtime. The tradeoff is that complex formatting requires string concatenation, but this hasn't been a problem in practice.

## AD-5: RepoClient protocol for host abstraction

**Decision:** Use a Python protocol (`RepoClient`) with adapter implementations (`GitLabAdapter`, `GitHubAdapter`, `FakeRepoClient`).

**Rationale:** The Website Agent should not know or care whether the target is GitLab or GitHub. The protocol defines two operations: `create_project()` and `commit_files()`. Each adapter wraps a host-specific library. `FakeRepoClient` enables testing without network calls. Adding a new host (e.g., Bitbucket) requires a new `PlatformSpec` entry in the `REPO_PLATFORMS` registry (with `default_api_url`, `token_env_var`, and `adapter_factory`), plus a member in the `HostLiteral` type alias — the adapter factory and registry dispatch handle the rest.

## AD-6: Data Agent decoupled from Intake Agent

**Decision:** The Data Agent accepts a `DataRequest`, not an `IntakeReport`. The orchestrator performs the adaptation.

**Rationale:** The Data Agent is "potentially reusable" (per `docs/architecture-history/initial_purpose.txt`) as a standalone query-writing tool for analyst teams. If it imported `IntakeReport`, it would be coupled to the pipeline. By defining its own input schema, it can serve CLI users, notebook users, and the pipeline equally. A CI test (`test_data_agent_decoupling.py`) uses AST analysis to verify zero imports of intake schemas.

## AD-7: Governance proportional to risk tier

**Decision:** Governance artifacts are emitted proportionally to `risk_tier` x `cycle_time` x `affects_consumers` x `uses_protected_attributes`, not as a fixed checklist.

**Rationale:** A low-risk internal dashboard does not need EU AI Act compliance documentation. A critical consumer-facing pricing model does. Emitting all artifacts for every project would create governance fatigue and reduce compliance quality. The tier-gated approach ensures each project gets exactly the governance depth appropriate to its risk.

## AD-8: Quarto for analysis narratives, not Jupyter

**Decision:** Generated analysis notebooks use Quarto (`.qmd`) format, not Jupyter (`.ipynb`).

**Rationale:** `.qmd` files are plain text (Markdown + code blocks), making them diffable, reviewable in PRs, and mergeable without conflict markers in binary metadata. Quarto supports Python and R, and renders to HTML, PDF, and presentation formats. The data science team renders the notebooks -- the pipeline only generates the scaffolds.

## AD-9: No LLM-generated code executes against databases

**Decision:** The Data Agent generates SQL and documentation. It does not execute queries against production databases as part of the pipeline.

**Rationale:** LLM-generated SQL is a draft. Running it against a production database without human review would be a safety risk. The queries are placed in `queries/` for the data science team to review, modify, and execute. The Data Agent can optionally validate queries against a read-only database, but this is not required.

## AD-10: Single atomic commit for generated projects

**Decision:** All generated files are committed in a single `commit_files()` call, not as a series of commits.

**Rationale:** A single commit means the generated project is always in a consistent state. There is no window where the repository has a partial scaffold (e.g., source modules without tests, or tests without CI). The commit message (`feat: scaffold model project (intake + data + governance)`) clearly marks the machine-generated baseline for the data science team.

## AD-11: CLI-adapter portability: OpenCode selected as the first non-Anthropic provider seam

**Decision:** The next extension to the provider seam (AD-2) targets **OpenCode** (`opencode run`, `github.com/anomalyco/opencode`, formerly `sst/opencode`) as a new `LLMProvider` branch in both agents' factories, ahead of a native OpenAI/Codex-CLI or Google/Gemini-CLI branch. GitHub Copilot CLI was evaluated and rejected as a provider target. Operator decision, 2026-08-01.

**Rationale:** Both agents' `make_llm_client(provider)` factories were designed for exactly this ("a second provider becomes one new client module plus one branch here"), but the two providers wired at that point — `anthropic` and `bedrock` — were the same model family through the same SDK ([AI Dependencies §6.7](AI-Dependencies#67-provider-concentration)), so real vendor diversification had not happened. A 2026-08-01 research pass compared four candidate agentic CLIs as subprocess-driven `LLMClient`/`IntakeLLMClient` implementations — Codex CLI (OpenAI), Gemini CLI (Google), GitHub Copilot CLI, and OpenCode — specifically for headless/scriptable invocation, structured-output support, and CI-viable auth. OpenCode is itself a vendor-agnostic multiplexer (Vercel AI SDK + Models.dev, 75+ providers including Anthropic, OpenAI, Gemini, Bedrock, and OpenRouter), with a genuine non-interactive mode (`opencode run --format json`) and API-key auth for the mainstream providers — one `OpenCodeLLMClient` adapter therefore unlocks many underlying vendors via OpenCode's own config, rather than requiring one bespoke adapter per vendor. GitHub Copilot CLI was rejected specifically for this portability goal: it is *already* a multiplexer gated by GitHub's own subscription/seat/policy layer, so wrapping it trades one form of vendor lock-in for a different (platform) lock-in rather than removing it, and its auth requires a paid, seat-assigned identity rather than a portable API key. Gemini CLI is deprioritized for now because Google discontinued it for free/personal accounts on 2026-06-18 in favor of a separate closed-source "Antigravity CLI" — a maintenance-parity risk for a build meant to last through an enterprise migration. Codex CLI remains a reasonable second candidate for a pure OpenAI capability comparison, but doesn't advance the portability goal the way OpenCode does. Full per-candidate findings (headless invocation syntax, structured-output support, auth mechanics, ToS/rate-limit notes, and citations) are recorded in [AI Dependencies §9](AI-Dependencies#9-cli-adapter-portability-the-opencode-provider-shipped-2026-08-01).

**As built (2026-08-01).** The decision was executed in four steps — specification, a live verification spike, implementation, and eval/documentation wiring — and the shipped design departs from the sketch above in one respect that is worth recording as a decision in its own right. Rather than implementing `IntakeLLMClient`/`LLMClient` from scratch, `OpenCodeLLMClient` **subclasses each package's `AnthropicLLMClient` and overrides only the transport method** (`_call_json` for intake, `_call_claude` for the data agent). Every prompt, JSON-shape instruction, dataclass builder, and the `_extract_json` parser is inherited, so prompt drift between providers is structurally impossible rather than merely discouraged — the same argument that justified `BedrockLLMClient`, applied to a subprocess transport. The cost is a naming oddity (the base class is named for a vendor it need not be talking to) and one real constraint: `opencode run` has no `--system` flag, so the system prompt is folded into the user message.

Two further as-built notes. **The tool-denying agent definition is a mandatory control, not defence-in-depth** — the specification originally assumed OpenCode's permission defaults were already safe in non-interactive mode, and the live spike disproved that (a run read a file and disclosed its contents, exiting cleanly), so the client always writes and selects a definition denying `edit`/`write`/`bash`/`read`/`webfetch`, with no constructor path that bypasses it. And **the provider ships with no default model**: OpenCode model ids name a vendor, so pinning one here would reintroduce into this repository exactly the vendor choice the adapter exists to remove.

**Status: wired, not validated.** No pipeline output has been produced through this provider, and the cutover gate records every threshold against it as unmeasured — which by the gate's own rule keeps `anthropic` primary. The decision this AD records is therefore *which* adapter to build, and that is settled; whether the adapter is good enough to use is an open measurement question, not a decided one.
