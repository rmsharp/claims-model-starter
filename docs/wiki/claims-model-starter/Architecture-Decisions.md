# Architecture Decisions

Key design choices and their rationale. For the full architecture plan, see `docs/planning/architecture-plan.md`.

## AD-1: Sequential pipeline, not parallel agents

**Decision:** Agents run in strict sequence (Intake -> Data -> Website), not in parallel.

**Rationale:** Each agent's output is the next agent's input. There is no useful work the Data Agent can do without the IntakeReport, and the Website Agent needs both reports. A sequential pipeline is simpler to debug, checkpoint, and reason about. The orchestrator can be upgraded to support parallel branches later if new agents with independent inputs are added.

## AD-2: LangGraph for agent orchestration

**Decision:** Use LangGraph (v0.2) as the agent framework, with direct Anthropic SDK calls.

**Rationale:** LangGraph provides built-in checkpointing for long-lived conversations (essential for the intake interview, which may span multiple user sessions). The Anthropic SDK is used directly rather than through LangChain's model abstraction because the project only uses Claude -- the abstraction would add complexity without benefit.

## AD-3: Pydantic schemas, not JSON Schema or protobuf

**Decision:** All inter-agent schemas are Pydantic v2 models.

**Rationale:** The entire project is Python. Pydantic provides runtime validation, JSON Schema export (for documentation), and cross-field validators. Protobuf would add a build step and code generation. JSON Schema alone lacks runtime validation. The `HandoffEnvelope` pattern wraps every payload with version metadata for forward compatibility.

## AD-4: f-string templates, not Jinja2 or Mako

**Decision:** All generated project files use Python f-strings, not a template engine.

**Rationale:** The templates are straightforward string interpolation with no loops, conditionals, or inheritance. An f-string approach means: (1) no template engine dependency, (2) byte-for-byte reproducible output for a given input, (3) templates are testable as pure functions, (4) no template syntax errors at runtime. The tradeoff is that complex formatting requires string concatenation, but this hasn't been a problem in practice.

## AD-5: RepoClient protocol for host abstraction

**Decision:** Use a Python protocol (`RepoClient`) with adapter implementations (`PythonGitLabAdapter`, `PyGithubAdapter`, `FakeRepoClient`).

**Rationale:** The Website Agent should not know or care whether the target is GitLab or GitHub. The protocol defines two operations: `create_project()` and `commit_files()`. Each adapter wraps a host-specific library. `FakeRepoClient` enables testing without network calls. Adding a new host (e.g., Bitbucket) requires only a new adapter -- no changes to the agent.

## AD-6: Data Agent decoupled from Intake Agent

**Decision:** The Data Agent accepts a `DataRequest`, not an `IntakeReport`. The orchestrator performs the adaptation.

**Rationale:** The Data Agent is "potentially reusable" (per `initial_purpose.txt`) as a standalone query-writing tool for analyst teams. If it imported `IntakeReport`, it would be coupled to the pipeline. By defining its own input schema, it can serve CLI users, notebook users, and the pipeline equally. A CI test (`test_data_agent_decoupling.py`) uses AST analysis to verify zero imports of intake schemas.

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

**Rationale:** A single commit means the generated project is always in a consistent state. There is no window where the repository has a partial scaffold (e.g., source modules without tests, or tests without CI). The commit message (`feat: scaffold model project`) clearly marks the machine-generated baseline for the data science team.
