# Evolution

> *Last updated: 2026-06-12 (commit `293a777`, after Session 147). This page is a full-rewrite synthesis — not continuously updated. For commits since this date, see `CHANGELOG.md` (maintainer) or `git log`.*

> *Design-decision arc from concept to current state. For the maintainer commit-linked ledger, see `CHANGELOG.md` at the repository root. For the user-facing release summary, see the [Changelog](Changelog) wiki page.*

This page answers **"why is it like this?"** — the narrative behind the decisions visible in the code today. The wiki's other pages describe current behavior; `CHANGELOG.md` lists what was committed; this page connects those two views by tracing how the project grew from a subrogation worked example into the multi-agent pipeline you see now.

The arc is organized thematically, not chronologically. Session numbers and dates anchor each claim so a reader can verify details against `CHANGELOG.md`, `SESSION_NOTES.md`, or `git log` — but the storyline follows the shape of the system, not the calendar. Operational work (genuine single-line maintenance fixes) is listed in the [Deliberately omitted](#deliberately-omitted) appendix at the end. Code references on this page name **grep-locatable symbols with full repository paths** rather than line numbers — a convention this page itself helped motivate (see §10's documentation-accuracy thread).

---

## 1. Concept origins

The project started as a short brief — what is now `docs/architecture-history/initial_purpose.txt` — describing a six-step pipeline that would walk a business stakeholder from idea to model-ready GitLab project. The brief opens with a role: *"an expert data scientist, business analyst, and consultant focused on a claims organization with a property and casualty insurance company that sells auto and property policies."* This is the domain the intake agent still carries as its persona today, and the six steps in the brief — intake interview, intake report, data collection, data report, initial model website, data science team handoff — map one-to-one onto the pipeline you see in the [Pipeline Overview](Pipeline-Overview).

The brief's worked example is subrogation recovery. A new claims system was capturing less information than its predecessor during the intake and investigation phases, and subrogation recovery rates had dropped. The root causes listed in the brief are concrete: *"inadequate adjuster training on the new system, a poorly designed user interface within the claims system which hinders efficient information capture, and a lack of performance metrics tied to subrogation success for adjusters."* The model solution is a supervised classifier predicting *the probability of successful subrogation* based on claim attributes — precisely the kind of outcome the generated project's initial notebooks explore, and precisely the domain the intake agent probes for when it interviews a stakeholder. A 10% improvement in recovery rates was the target order of magnitude, "likely in the hundreds of thousands or even millions of dollars, depending on the overall claim volume and average claim value."

Three pieces of that brief became architectural constraints that held throughout the project:

1. **"Ask one question at a time."** The brief says it explicitly; the intake agent's LangGraph cycles make it structurally impossible to advance more than one prompt per tick. This is what keeps the interview interview-shaped rather than form-shaped.
2. **"Up to 10 questions, whichever comes first."** The initial `MAX_QUESTIONS=10` cap came directly from the brief. It later rose to 20 (§3 below) when real-LLM runs needed more room to converge.
3. **Governance proportional to value.** The brief sizes the subrogation model at *"hundreds of thousands or even millions of dollars annually"* — a high-stakes recovery model. This is why the pipeline emits governance artifacts *proportional to risk tier and cycle time* (§5 below) rather than a flat checklist; a low-stakes internal tool does not need SR 26-2 paperwork, but a million-dollar-impact classifier does.

**Session 0 (2026-04-10)** adopted the Iterative Session Methodology framework (v2.1) — `SESSION_RUNNER.md`, `SAFEGUARDS.md`, `SESSION_NOTES.md`, the methodology dashboard, and the workstream reference documents under `docs/methodology/`. This is the operating procedure every subsequent session followed. The session also populated `ROADMAP.md` with five milestones (M1 Architecture & Pipeline Design through M5 Orchestrator + Hardening) and `BACKLOG.md` with granular tasks per milestone. `CLAUDE.md` was customized to point at the project's specific task-to-workstream mappings — agent building, prompt engineering, schema definition, pipeline integration.

**Session 1 (2026-04-10)** wrote `docs/architecture-history/architecture-approaches.md` — an exploration of four critical architecture questions (agent coordination, schema evolution, persistence, platform abstraction) with pros/cons for each option. This was pre-canonical-plan work: the choices narrowed later, but the document preserves the alternatives that were considered and rejected. It now lives in the archive as primary-source design archaeology. Reading it today, you can see which options were closed off early (shared-state agent coordination was rejected in favor of explicit handoffs; a single repo-host adapter was rejected in favor of a neutral protocol with per-platform implementations) and which only crystallized later (schema versioning took until Phase 1 to commit to `HandoffEnvelope`; persistence was prototyped in Phase 3B).

---

## 2. Foundational architecture

**Sessions 2–3 (2026-04-14)** produced `docs/architecture-history/architecture-plan.md` — the canonical 14-phase architecture plan — and the v1 payload schemas. Two of its sections became load-bearing invariants:

**§7 — Decoupling invariant.** *The data agent has zero imports from the intake agent. All cross-agent communication goes through the orchestrator adapter.* This is enforced by an AST-walk decoupling test (`tests/test_data_agent_decoupling.py`) that parses the standalone package under `packages/data-agent/` and fails the build if any import chain reaches the intake agent. The invariant exists because the data agent was explicitly designed to be reusable as a standalone query-writing tool (see §4 below), and coupling to intake-specific types would make that reuse impossible. The decoupling test is the structural guarantor — it catches drift that code review would miss — and it earned its own CI job (the `decoupling` job in `.github/workflows/ci.yml`).

**§8 — Governance artifact framework.** Artifacts are emitted proportional to `risk_tier` ∈ {tier_1_critical, tier_2_high, tier_3_moderate, tier_4_low} and `cycle_time` ∈ {strategic, tactical, operational, continuous}, with explicit regulatory mapping (SR 26-2, NAIC AIS). A 2026 note: the Federal Reserve superseded SR 11-7 with **SR 26-2** in 2026, with general intent unchanged for this pipeline; **Session 144 (2026-06-11) renamed the framework vocabulary token `SR_11_7` → `SR_26_2`** across the intake prompt enumeration, the website artifact map, the test fixtures, the tutorial, and the wiki — a citation-level change with no artifact-set or behavior change, the framework-parity guard (§5) holding the intake prompt and the artifact map byte-identical through the swap. Historical records (root `CHANGELOG.md`, the archived plans, the Session-22 live-run note in §6) retain the old name as a record of what shipped at the time. The most critical tier (`tier_1_critical`) produces the full artifact set — datasheets, model card, monitoring plan, risk register, regulator-facing summary — while `tier_4_low` produces only the minimal scaffolding. The tier derivation happens inside the intake agent (on every revision cycle, via `GovernanceMetadata`) so that what the website agent produces is a direct function of what the stakeholder described.

Schemas live under `src/model_project_constructor/schemas/`, each tagged with a `schema_version` field. The `HandoffEnvelope` in `src/model_project_constructor/schemas/envelope.py` wraps them with versioning metadata so future schema evolution can stay backwards-compatible: an envelope says "I'm carrying an `IntakeReport` at `schemas.v1.intake`," the consumer looks that up in `REGISTRY` in `src/model_project_constructor/schemas/registry.py`, and if the version is unknown the pipeline halts with a typed error rather than failing later with a validation mismatch. This matters because the three agents are deployed together today but the design allows them to evolve at different schema cadences tomorrow. (A dead `SCHEMA_VERSION` module constant and a docstring describing a migrations workflow that never existed were deleted in Session 113 — the honest-versioning cleanup; the per-payload `schema_version` fields are the real mechanism.)

**Phase 5 — Orchestrator (Session 15, 2026-04-15)** made the plan concrete. `src/model_project_constructor/orchestrator/pipeline.py` drives the pipeline sequentially — intake, then data, then website — with each stage's output serialized to a checkpoint before the next stage reads it. `src/model_project_constructor/orchestrator/adapters.py` is the sole `IntakeReport ↔ DataRequest` bridge; this is what the §7 decoupling invariant *allows*. `CheckpointStore` in `src/model_project_constructor/orchestrator/checkpoints.py` persists envelopes and terminal results per run. `PipelineStatus` is a `Literal` — `COMPLETE` / `FAILED_AT_INTAKE` / `FAILED_AT_DATA` / `FAILED_AT_WEBSITE` — and partial state is retained on halt so operators can inspect what went wrong. The `*_AT_*` naming is deliberate: a halt identifies *where* the failure happened, which tells an operator which checkpoint to resume from. That scaffolding paid off twice — first in the resume-from-checkpoint feature (§7 below), then in the stage-descriptor refactor that decomposed this module (§9).

**Phase 6 — Production hardening (Session 16, 2026-04-15)** added observability, configuration, and CI. Two design choices here are load-bearing and worth dwelling on:

1. **Observability via runner composition, not imports.** `make_logged_runner` in `src/model_project_constructor/orchestrator/logging.py` and `make_measured_runner` in `src/model_project_constructor/orchestrator/metrics.py` wrap an agent's callable without modifying the pipeline itself. `src/model_project_constructor/orchestrator/pipeline.py` has zero imports from the logging or metrics modules — you can grep for it. Observability is opt-in: you compose it at orchestrator construction time, not at pipeline-author time. This keeps the core pipeline trivially testable (no logger mocks needed) and lets different deployments choose different observability layers. The same runner-composition shape is what lets the intake agent's fixtures bypass the FastAPI session store.

2. **Zero new dependencies.** The hardening plan suggested `structlog` for structured logging and `pydantic-settings` for env-var-driven configuration. Both were rejected in favor of stdlib `logging` with `extra={"context": ...}` for structured fields and a plain `@dataclass` + `os.environ` pattern for config (`OrchestratorSettings.from_env` in `src/model_project_constructor/orchestrator/config.py`). The rationale: adding a dependency is a one-way door — future sessions must maintain it, CI must install it, version conflicts can surface. The zero-new-dep path was validated by 54 new tests + mypy strict + ruff clean on the first try.

The same session added four-job CI (`lint`, `typecheck`, `test`, `decoupling`), `OPERATIONS.md` as the production runbook, and `TROUBLESHOOTING.md` with one walkthrough per `FAILED_AT_*` path. Coverage floor raised 93% → 94%; later sessions raised it to 95% (Session 47), where it stands today.

---

## 3. Intake agent arc

**Phase 3A — Intake agent core (Session 6, 2026-04-14)** built the intake agent as a LangGraph flow. It interviews a stakeholder one question at a time, rebuilds `IntakeReport` + `GovernanceMetadata` on every revision cycle (so the risk tier reflects the latest answer set, not stale tier from an earlier draft), and stops when either the stakeholder accepts the draft or the budget runs out. Two budgets: `MAX_QUESTIONS` and `MAX_REVISIONS` in `src/model_project_constructor/agents/intake/state.py` (initially 10 and 3; the question cap is 20 today). A six-token accept vocabulary (`REVIEW_ACCEPT_TOKENS` in `src/model_project_constructor/agents/intake/nodes.py`) recognizes stakeholder confirmation across natural phrasings — "accept," "yes," "approve," "approved," "ok," "looks good" — so the stakeholder doesn't have to guess the magic word. The agent's fixture-driven CLI lets it run from canned answers for testing, which is what the entire test suite depends on.

The one-question-at-a-time shape is deliberate and traces directly to `docs/architecture-history/initial_purpose.txt`. The brief insisted on it. The LangGraph cycles enforce it structurally: the interview can only advance one prompt per tick, and the cycle boundary is where the revision logic runs. This is what makes the intake experience interview-shaped rather than form-shaped — the stakeholder is not filling out a form, they are having a conversation.

**Phase 3B — Intake agent web UI (Session 7, 2026-04-14)** added a FastAPI + Server-Sent Events + HTMX frontend. SSE was chosen over WebSockets because the interview is unidirectional (agent asks, stakeholder answers, one at a time); SSE needs only a one-line HTML fragment update per turn, which HTMX handles natively without client-side JavaScript. Sessions persist to SQLite (`IntakeSessionStore` in `src/model_project_constructor/ui/intake/runner.py`) so an interview can be paused and resumed. A subtle but important choice: fixtures bypass the database entirely — they test the agent's LangGraph flow without touching disk state — which preserved the testing patterns established in Phase 3A while adding a production-shape web surface.

**Scope B-2 — Real-Anthropic intake (Session 26, 2026-04-16)** extended the pipeline script with a third mode: `--llm both`. Previously the intake stage was always fixture-driven. Session 26 introduced `run_scripted` on the intake agent (`src/model_project_constructor/agents/intake/agent.py`), which calls real Anthropic for *questions* but consumes fixture-supplied *answers*. This lets you exercise the real LLM's question-generation path without needing a human in the loop. A subtle piece of this work is the `_draft_incomplete_from_exception` adapter (inline in `scripts/run_pipeline.py`). It converts exhausted-script errors, rate-limit errors, and pydantic validation failures into a typed `IntakeReport(status="DRAFT_INCOMPLETE")` so the orchestrator halts cleanly with `FAILED_AT_INTAKE` instead of crashing with an untyped exception. This pattern — *convert lower-level crashes into typed halt states at the boundary* — matches the orchestrator's overall shape, where `PipelineStatus` is always one of four known values and there is no "unknown error" state.

**Cap bump — `MAX_QUESTIONS` 10 → 20 (Session 27, 2026-04-17)** is the intake-agent arc's first substantive tuning, and the one whose story is worth telling in full because it illustrates a recurring pattern. Session 26's first live B-2 run against a 10-qa-pair subrogation fixture produced a rich Claude-drafted report but finished with `DRAFT_INCOMPLETE`. The status decision, inside `finalize_node` in `src/model_project_constructor/agents/intake/nodes.py`, is:

```python
status = "COMPLETE" if accepted and not missing else "DRAFT_INCOMPLETE"
```

And the auto-append in the same function fires `questions_cap_reached` whenever `questions_asked >= MAX_QUESTIONS` and `believe_enough_info` is still false. So the happy path to `COMPLETE` requires the LLM to flip `believe_enough_info=true` *before* hitting the cap. Against the 10-qa-pair fixture, Claude Opus 4.7 wanted more detail than 10 questions could supply — specifically, it flagged three gaps it could not resolve: latency SLA, average recovery per successful subrogation, and a fairness/bias plan. Claude kept asking; the fixture ran out; the cap fired; the status went to `DRAFT_INCOMPLETE`. The fix was two-part: raise the cap to 20 *and* extend the fixture to 15 qa_pairs pre-answering the three gaps. The live run after the fix reached `Status: COMPLETE` with ten questions asked — Claude converged inside the old cap *once the fixture answered the right questions*. The wider cap is not for padding; it is for fixtures (and real stakeholders) that don't pre-answer as thoroughly.

The bump also surfaced something structural: a production constant had leaked into test fixtures (via cap-plus-one sizing arithmetic), dict-literal exports (`CAPS` in `src/model_project_constructor/ui/intake/runner.py`), and prose across several wiki and ops surfaces. A plain grep for the constant name missed the indirect coupling paths. The prose drift took years of sessions to fully extinguish: wiki sweeps closed most of it (Sessions 40–42), but a "up to 10 questions" string hardcoded in the web UI's HTML templates survived until **Session 104 (2026-06-03)**, which converted the UI copy to interpolate `MAX_QUESTIONS` directly — so that surface can never lie again. The general lesson — *derive displayed values from the constant instead of restating them* — became a house pattern (§9).

**Data-source probing (Session 56, 2026-04-19)** taught the interviewer to ask *where the data lives*, not just what the problem is. The interviewer prompt (`_INTERVIEWER_BASE` in `src/model_project_constructor/agents/intake/anthropic_client.py`) probes for concrete named systems — claims platforms, policy admin, billing, subrogation, fraud/SIU, CRM, the enterprise data warehouse — plus owning teams and refresh cadence. This was the intake-side opening move of the data-source-inventory arc (§4): interview answers became one *producer* of the same inventory contract that database probing and curated files also feed.

**Value-measurement plan as a required section (Session 87, 2026-05-21)** extended the interview from four required output sections to five: business problem, proposed solution, model solution, estimated value, and now a value-measurement plan (baseline metric, counterfactual design, attribution, evaluation horizon, decision rights). `ValueMeasurementPlan` in `src/model_project_constructor/schemas/v1/intake.py` is wired through the draft-report protocol, the fixture parsers, and the `finalize_node` completion gate. The rationale comes from the business-value-capture arc (§8): a model whose value cannot be measured after deployment was specified incompletely before construction.

**Prompt enumerations derived from the schema (Session 127, 2026-06-08)** closed the intake agent's last vocabulary-drift class. Six places where the system prompts hand-listed legal values (risk tiers, cycle times, model types, confidence levels, counterfactual designs, review cadences) now derive their member lists from the corresponding schema `Literal` types via `join_members` in `src/model_project_constructor/_vocab_guard.py` — rendered prompts proven byte-identical before and after. Part of the O4 controlled-vocabulary overhaul (§9).

---

## 4. Data agent arc

**Phase 2A — Data agent core (Session 4, 2026-04-14)** built `DataAgent` as a LangGraph flow. It takes a `DataRequest`, generates SQL queries (via the LLM, with the prompt constrained by the request's schema), runs quality checks, and produces a `DataReport`. `validate_sql` in `packages/data-agent/src/model_project_constructor_data_agent/sql_validation.py` catches syntax errors via `sqlparse` before queries reach a database — the agent emits SQL that compiles, even if the semantics need review. The AST-walk decoupling test is the architectural guardrail; `DataAgent.run(DataRequest) -> DataReport` is the minimal entry point.

**Phase 2B — Standalone package (Session 5, 2026-04-14)** refactored the data agent into `packages/data-agent/` with its own `pyproject.toml`. The motivation is in `docs/architecture-history/initial_purpose.txt` verbatim — the brief noted that the data agent *"would likely be useful for just writing queries in general"* for analyst teams. *"Many analysts spend significant time writing queries; speeding this up would enable exploratory analysis that is currently infeasible."* A standalone package makes reuse possible in a way that a subpackage of the orchestrator does not: an analyst team can depend on `model_project_constructor_data_agent` without pulling in the orchestrator, the website agent, FastAPI, or LangGraph's intake-specific nodes. The package added `AnthropicLLMClient`, a Typer CLI, and Python API docs. The "reusable as analyst tool" principle is also why the data agent carries `--db-url` as a first-class CLI argument. The schema split that followed is worth noting: the canonical definitions of `DataRequest`, `DataReport`, and friends live **in the wheel** (`packages/data-agent/src/model_project_constructor_data_agent/schemas.py`), and the main package re-exports them through `src/model_project_constructor/schemas/v1/data.py` — the dependency points from orchestrator to wheel, never the reverse.

**Scope B-1 — Real Anthropic wiring (Session 24, 2026-04-16)** connected the real LLM path to the pipeline script: `--llm {none,data}`, `--model`, and `--db-url` on `scripts/run_pipeline.py`. The model-choice decision set a precedent. The plan recommended a cheaper model for the first live run to save cost. The user pushed back: if the output quality was poor, *"was it the model?"* would become a confounding variable. Pilot cost differences are trivial compared to the cost of a muddled conclusion, so the first-impression run used the top model; cheaper models are for iteration after the output shape is validated.

**Live-LLM hardening (Sessions 51–53, 2026-04-18/19).** The first live resume-era round-trip surfaced two real-world bugs that fixture-driven tests could not. First, `claude-sonnet-4-6` wrapped its JSON output in markdown fences with surrounding prose, which the anchored parser rejected — Session 53 restructured `_extract_json` in `packages/data-agent/src/model_project_constructor_data_agent/anthropic_client.py` into a bare-parse-first, fence-search-fallback shape (defensive parser-side fix, because no prompt phrasing reliably eliminates fences across model versions). Second, the resume logic treated a FAILED checkpoint as a completed handoff — Session 52's status-aware demotion (§7). Each fix carries regression tests citing the live run that exposed it. Notably, the intake agent had its own *stale copy* of the pre-hardening parser, which became a story of its own (§9).

**The data-source inventory contract (Sessions 57–60, 70, 81 — 2026-04-19 through 2026-05-13)** is the data-agent arc's biggest post-pilot design. The problem: an LLM writing SQL against a warehouse it cannot see will hallucinate table and column names. The insight that shaped the solution: *data-source discovery is a separate activity from query writing, with multiple possible producers* — a stakeholder interview, an automated `information_schema` probe, a curated file maintained by a data team, or future discovery tools. So the design is a **contract, not a feature**: `DataSourceInventory` / `DataSourceEntry` / `ColumnMetadata` / `ProducerMetadata` (canonical in `packages/data-agent/src/model_project_constructor_data_agent/schemas.py`) define the plug-in boundary; anything that can produce an inventory can inform query generation.

- **Phase 1 (Session 58)** shipped the contract schema itself.
- **Phase 2 (Session 59)** shipped the reference producer — `probe_information_schema` in `packages/data-agent/src/model_project_constructor_data_agent/discovery.py`, which reflects schemas/tables/columns via SQLAlchemy and emits a ranked inventory.
- **Phase 3 (Session 60)** wired the consumer side: `DataRequest` gained an optional `data_source_inventory` field; the LLM prompt renders a truncated, sanitized inventory block (top entries by `relevance_score`); and `PrimaryQuery.inventory_entries_used` records which entries each generated query actually drew on — a provenance trail from interview answer to SQL. Behavior with the field absent is byte-identical to pre-Phase-3, so adoption is strictly opt-in.
- **Phase 4 (Session 70)** coupled the intake side: `intake_qa_pairs_to_inventory` in `src/model_project_constructor/orchestrator/adapters.py` converts interview Q&A (`QAPair` entries on `IntakeReport`) into inventory entries for nine canonical P&C systems, exposed as `--inventory-from-intake` on the pipeline script. The converter lives in the orchestrator, preserving the §7 decoupling invariant — the data agent still knows nothing about intake types.
- **Curated merge (Session 81)** added the third producer: `load_curated_inventory` + `merge_inventories` in the same adapters module let an externally-maintained inventory file combine with the interview-derived one (curated entries win on duplicate fully-qualified names), exposed as `--curated-inventory`.

**Baseline collection (Session 88, 2026-05-21)** gave the data agent a second job beyond query writing: collect the *pre-model baseline* for the metric the intake interview said would prove value. `BaselineQuerySpec` on the LLM protocol (`packages/data-agent/src/model_project_constructor_data_agent/llm.py`) drives generation of a baseline-collection query, executed read-only, with the result recorded as `BaselineSnapshot` on the `DataReport`. Part of the business-value-capture arc (§8) — and deliberately placed in the data agent, not intake, because the data agent is the component with database access.

**In-wheel vocabulary derivation (Session 129, 2026-06-08)** applied the O4 single-sourcing pattern (§9) inside the wheel: the data-agent prompt's `expected_row_count_order` enumeration derives from its own schema `Literal` via `typing.get_args` — *without* importing the main package's helper, because the wheel must stay independently installable. The same pattern, implemented twice on purpose, is the decoupling invariant working as designed.

---

## 5. Website agent arc

**Phase 4A — Website agent core (Session 8, 2026-04-14)** built the website agent as a LangGraph flow with three nodes: `CREATE_PROJECT` (creates the repo), `SCAFFOLD_BASE` (writes the baseline file tree — `.qmd` analysis files, `src/` module stubs, README, CI config), `INITIAL_COMMITS` (groups the scaffold into meaningful commits — "scaffold", "governance artifacts", "CI setup" — so the git history is readable). The output is a draft repository with placeholders clearly marked where human judgment is required.

The brief called for a *"draft, not a finished product."* The scaffolding bias is toward making the data science team's first-day experience productive. Three small choices reflect this:

- Placeholders are `# TODO(data-science-team): ...` comments with specific prompts, not generic `FIXME`s. The comment tells the reader what decision to make and where to look for context.
- `.qmd` files (Quarto, not Jupyter notebooks) are chosen so the output renders as a website without a local Python kernel. A reviewer can read the draft analysis in a browser; only an implementer needs the runtime.
- The `src/` module stubs have type annotations and docstrings but raise `NotImplementedError` in their bodies. This gives mypy something to check and gives the implementer a clear signal that the stub has not been filled in yet.

**Phase 4B — Website agent governance (Session 9, 2026-04-14)** added governance artifact scaffolding proportional to `risk_tier` and `cycle_time` per architecture-plan §8 — the framework described in §2 above. Two design decisions from this session shaped the rest of the codebase:

1. **`is_governance_artifact` as the single source of truth** (in `src/model_project_constructor/agents/website/governance_templates.py`). A naive implementation would have accumulated a governance manifest in agent state as each node ran. Instead, the classifier function determines whether any given path *is* a governance artifact; the `GovernanceManifest` is *derived* by applying the classifier to the final file tree. This is the difference between storing a fact and recomputing it from ground truth. State bookkeeping drifts when new nodes are added — someone forgets to append to the manifest — but a classifier cannot drift because it is called on the file tree itself.

2. **Helper functions in a sibling module, not an expansion of the existing one.** `governance_templates.py` sits next to `templates.py` in `src/model_project_constructor/agents/website/`. The review-time diff stays local to the new governance concerns; the "before vs after" phase-split is visible in the file tree.

Session 9 also added the first repository adapter — `PythonGitLabAdapter` — implementing what was then called `GitLabClient`. Retry and exponential backoff wrap repo operations so transient network failures don't abort a live run, with visible seams (kwargs on the adapter constructor) so a test can pass a no-op sleep without monkeypatching the production backoff timer.

**Value-presentation templates (Sessions 89–90, 2026-05-22)** extended the generated site for the business-value arc (§8). Session 89 renders the pre-construction business case — annual impact band, cost of inaction, implementation cost, payback, value drivers, assumptions, decision rights — across three generated surfaces via a shared `_render_business_case_block` helper in `src/model_project_constructor/agents/website/templates.py` (one renderer, three call sites, so the surfaces cannot drift apart). Session 90 replaced the implementation plan's intentionally-sparse TODO with a structured production measurement plan (baseline, counterfactual, attribution, horizon, logging, review cadence, success criteria, decision rights), interpolating the baseline the data agent actually collected.

**Governance frameworks reconciled with the intake prompt (Sessions 108–109, 2026-06-04).** An audit finding revealed that the set of regulatory frameworks the intake agent *prompts for* and the set the website agent *maps to artifacts* had drifted: `GDPR_ART_22` was prompted but unmapped (silently yielding an empty artifact list), and an `EU_AI_ACT` alias in the map was dead code. Session 108 added the `GOVERNANCE_FRAMEWORKS` tuple to `src/model_project_constructor/agents/intake/anthropic_client.py` as the parseable producer constant, reconciled `_FRAMEWORK_ARTIFACTS` in `src/model_project_constructor/agents/website/governance_templates.py` against it, and added parity tests that fail on any future drift; Session 109 synchronized the wiki mirrors. **Session 113 (2026-06-05)** generalized the pattern: `_TIER_SEVERITY` and `_CYCLE_CADENCE` in the same `src/model_project_constructor/agents/website/governance_templates.py` previously re-listed the tier/cadence vocabularies with silent `.get(..., default)` fallbacks — a renamed tier would quietly rank least-severe and skip governance artifacts, a real compliance hazard in a P&C context. An import-time parity guard (a real `raise`, not a strippable `assert`) now pins both dicts to the schema `Literal` types.

---

## 6. Platform abstraction arc

The website agent initially assumed GitLab. Sessions 10–14 generalized it to a repo-host-agnostic design, with GitHub as the second supported platform. This was done as a four-phase plan (`docs/architecture-history/github-gitlab-abstraction-plan.md`) rather than a single refactor, because a rename mixed with a behavior change would have made the review diff impossible to read.

**Phase A — Neutral rename (Session 11).** `GitLabClient → RepoClient`, `GitLabTarget → RepoTarget`, `GitLabProjectResult → RepoProjectResult`. The `project_id` field widened from `int` (GitLab's numeric ID) to `str` (so GitHub's `owner/repo` form fits). This phase touched 26 files and was deliberately the only rename phase — the commit contains nothing but renames, no behavior changes.

**Phase B — GitHub Actions CI template (Session 12).** `render_github_actions_ci` as a sibling to the existing GitLab CI renderer in `src/model_project_constructor/agents/website/governance_templates.py`. A new `ci_platform` field flows through website agent state and the governance manifest, so the emitted CI manifest can differ from the repo host — and this separation turned out to be load-bearing three weeks later, when the O3 overhaul (below) had to decide which vocabulary was which.

**Phase C — PyGithub adapter (Session 13).** `PyGithubAdapter` implementing the neutral `RepoClient` protocol (`src/model_project_constructor/agents/website/protocol.py`). `PyGithub` became a dependency — LGPL-3.0 licensed, but usage is pure API, so LGPL compliance is automatic via Python's import mechanism.

**Phase D — Host selection CLI (Session 14).** `--host gitlab|github` on the website CLI. Dual-adapter selection at invocation time. Coverage floor raised 90% → 93%.

**Session 22 — First live end-to-end smoke (2026-04-16)** ran the full pipeline against a real GitLab project for the first time. The smoke test surfaced a bug that none of the structural tests had caught: the pipeline script passed a keyword argument the adapter constructor did not accept, so `--live --host gitlab` had never successfully run. A two-character fix unblocked the path, and a real project was created with 38 files, 10 tier-3-moderate governance artifacts, and regulatory mapping on `SR_11_7` + `NAIC_AIS` (that token became `SR_26_2` in Session 144 — §2; the April run shipped the old name). The session filed five additional findings covering CI scope gaps, namespace validation, GitHub host-url wiring, and operations-doc drift. *This is the session that revealed how much latent bit-rot accumulates in paths that are structurally tested but never exercised end-to-end.*

**Session 28 — `validate_namespace` fail-fast (2026-04-17)** closed one of those findings. `MPC_NAMESPACE` takes a group path, not a URL — but a URL-form value had surfaced as a generic "group lookup failed: 404" from the GitLab adapter. The module-level `validate_namespace` helper in `src/model_project_constructor/orchestrator/config.py` now raises a typed `ConfigError` on URL-prefixed values before any agent runs, naming the received value and the expected form. *Validate at the config boundary, halt with a typed message* — the same shape as the orchestrator's `FAILED_AT_*` states.

**Session 30 — GitHub branch parallel-fix completeness (2026-04-17)** fixed the GitHub sibling of Session 22's bug — and found the parallel ran deeper than expected: the GitHub branch had *two* defects (a wrong constructor kwarg *and* a missing host-URL read that silently sent GitHub Enterprise users to public `api.github.com`). `--live --host github` had never worked either. Reading both adapters' constructor signatures and both call sites side-by-side caught the whole class in one pass.

**Session 32 — GitLab default URL (2026-04-17)** changed the website CLI's GitLab default from an RFC-2606 placeholder that does not resolve to the real public `https://gitlab.com` API URL, bringing the CLI in line with the other surfaces declaring the same default. The constant that carried this default (`GITLAB_DEFAULT_HOST_URL`) no longer exists — it was absorbed into the platform registry by the O3 overhaul below, and its live successor is `REPO_PLATFORMS["gitlab"].default_api_url` in `src/model_project_constructor/orchestrator/config.py`. The accompanying test restructure also set a pattern: when two platform-symmetric tests live in one file and one asserts defaults while the other asserts overrides, the asymmetry is usually a test-design bug — restructure to default-path on both, then add explicit override tests.

**The O3 overhaul — `REPO_PLATFORMS` (Sessions 115–118, 2026-06-05).** By June, the host vocabulary existed in four hand-maintained copies (config, website CLI, pipeline script, and a type guard), and two must-agree ternaries selected the token environment variable — classic drift waiting to happen, flagged by the technical-debt audit (§9). The planning session's load-bearing discovery: **repo host and CI platform are two separable vocabularies** (you can scaffold GitHub-Actions CI into a GitLab-hosted repo for cross-platform preview), so only the host side should consolidate. Three phases followed, one session each:

- **O3-1** single-sourced host membership: every "which hosts exist?" site now derives from `REPO_PLATFORMS` (a registry of `PlatformSpec` entries in `src/model_project_constructor/orchestrator/config.py`), with an import-time guard — `assert_vocab_parity` in `src/model_project_constructor/_vocab_guard.py` — pinning the registry keys to the `HostLiteral` type.
- **O3-2** folded per-host configuration in: `PlatformSpec.default_api_url` and `PlatformSpec.token_env_var` replaced the duplicated URL branches and the two token ternaries. One registry field, one truth.
- **O3-3** routed adapter construction through `PlatformSpec.adapter_factory` (lazy imports inside the factory bodies keep the orchestrator SDK-free), collapsing the per-host `if/elif` dispatch — and eliminating a dangerous silent `else: # github` fall-through that would have routed any unknown host to GitHub.

Adding a third platform is now a one-entry change: register a `PlatformSpec`, and membership checks, token selection, URL defaults, CLI help text, and adapter dispatch all follow.

**The E4 factory — explicit LLM-provider choice (Sessions 132–133, 2026-06-09/10).** The same "make the vocabulary explicit" instinct, applied to the *other* external dependency: which LLM backs an agent was previously implicit in which `AnthropicLLMClient` you imported. E4 added `make_llm_client(provider, model)` factories — one in `src/model_project_constructor/agents/intake/factory.py`, a parallel one in `packages/data-agent/src/model_project_constructor_data_agent/factory.py` (parallel *by design*: the wheel cannot import main-package helpers) — plus `--provider` CLI flags, with the known-provider list derived from a `Literal` via `typing.get_args`. The adversarial review of this change caught a real regression before landing: an eager package-level export pulled the `anthropic` SDK at import time, breaking the documented lazy-construction property; the fix moved the import inside the factory body and added subprocess-based guards that prove the property in CI.

---

## 7. Resume-from-checkpoint

The orchestrator's halt states always *implied* resumability — `FAILED_AT_DATA` tells you the intake checkpoint is good — but resuming was a manual operation. **Sessions 48–51 (2026-04-18)** made it a feature, in three phases off a plan with an explicit resume truth table:

- **Phase 1 (Session 49):** `determine_resume_point` in `src/model_project_constructor/orchestrator/pipeline.py` — a pure function over checkpoint existence implementing the truth table, with `ResumeInconsistent` raised on impossible states (e.g., a data checkpoint with no intake predecessor). Pure first, wired second: the function was fully tested in isolation before anything consumed it.
- **Phase 2 (Session 50):** `run_pipeline` honors `resume_from` — stages before the resume point load their envelopes from disk; the resume point and after re-execute. Halt semantics preserved: `FAILED_AT_*` fires only when a stage actually ran.
- **Phase 3 (Session 51):** the `--resume <run_id>` flag on `scripts/run_pipeline.py`, plus operations-runbook and tutorial coverage. This closed the long-deferred "Scope B-3 web-UI bridge" idea by superseding it: once `--resume` exists, the UI-to-pipeline handoff is just "the UI writes an `IntakeReport` envelope; the operator resumes."

The first live LLM round-trip through this path immediately earned its keep — and exposed a design gap. The data stage failed (the markdown-fence parser bug, §4), leaving a `DataReport` checkpoint with a *failure* status on disk. The resume logic, which only checked checkpoint *existence*, would have resumed at the website stage — treating a failure artifact as a completed handoff. **Session 52's status-aware demotion** fixed the root cause: `determine_resume_point` now loads the saved payloads and demotes the resume point when a saved status is not `COMPLETE` (a failed data stage re-executes; an incomplete intake re-executes). The terminal `RepoProjectResult` is deliberately asymmetric — repo creation has irreversible side effects, so re-running the website stage is opt-in rather than automatic.

The stage machinery itself was later rebuilt on a descriptor table — the O1 overhaul, told in §9 — which is why resume gates, the CLI banner, and the driver loop can no longer disagree about what the stages *are*.

---

## 8. Business-value capture arc

**Sessions 85–93 (2026-05-21/22)** ran the largest post-pilot feature arc: making the pipeline capture *why the model is worth building* before construction and *how its value will be proven* after deployment. The observation driving it: the original four intake sections captured an estimate of value, but nothing that would let anyone verify the estimate after the model shipped — no baseline, no counterfactual, no agreed metric. Six phases, one session each:

1. **Schema (Session 86):** `EstimatedValue` gained pre-construction business-case fields (cost narratives, cost and payback bands, value drivers); a new `ValueMeasurementPlan` class captures baseline metric, counterfactual design, attribution, horizon, logging, review cadence, success criteria, and decision rights; `BaselineSnapshot` landed in the data-agent schemas. All optional at the schema level for backward compatibility — enforcement came downstream.
2. **Intake (Session 87):** the interview's required sections went from four to five (§3) — the value-measurement plan must exist before a report reaches `COMPLETE`.
3. **Data agent (Session 88):** baseline collection (§4) — generate the baseline query, execute read-only, record the snapshot. Placed in the data agent because that is the component with database access; intake never touches a warehouse.
4. **Website, pre-construction (Session 89):** the generated site presents the business case via one shared renderer (§5).
5. **Website, post-production (Session 90):** the implementation plan template renders a structured production measurement plan, interpolating the actually-collected baseline.
6. **Cross-doc consistency (Session 91):** the worked examples, pipeline overview, glossary, and remaining surfaces tell the same value story.

**Session 93** added an executive-facing Quarto summary (`docs/executive-summaries/`) for business stakeholders — rendered on demand, with the `.qmd` source tracked and the HTML/PDF artifacts deliberately not (the source is the truth; renders are reproducible).

The arc's design through-line matches the rest of the system: each phase kept the schema partition clean (intake specifies, data agent measures, website presents), and the cross-surface renderers are shared functions, not copied prose — the same "derive, don't restate" principle that governs the vocabulary work in §9.

---

## 9. The audit-and-overhaul program

By late May the project had shipped a pilot, a feature arc, and dozens of micro-fixes — a natural moment to ask what debt had accumulated. **Session 97 (2026-06-01)** ran a senior-architect technical-debt audit across the whole codebase (read-only, delivered as `docs/audits/2026-06-01-technical-debt-audit.md`): 44 findings — zero critical, 15 moderate, 29 minor — sorted into 37 quick wins and a handful of architectural overhauls. The headline theme: **vocabularies and twin implementations that bypass the type system.** Hand-listed enum members in prompts, duplicated host lists, parallel JSON parsers — each individually harmless, each a silent-drift channel. The program that followed executed essentially all of it:

**Quick wins — the twin-parser saga (Sessions 98–100).** The audit's sharpest find: the intake agent held a *stale copy* of the data agent's JSON parser — predating the Session 53 fence hardening (§4). Against a real model response wrapped in markdown fences, intake would have crashed. Session 98 ported the hardened `_extract_json`; the port's adversarial verification (diff the *whole* module, not just the patched function) then surfaced two more latent twins: a missing text-block type guard (Session 99) and a missing empty-response guard (Session 100) — each present in one client, absent in the other. The campaign ended only when a full-module diff found nothing left to port.

**O2 — parity guard, not a merge (Sessions 102–103).** The obvious fix for twin parsers is to share one implementation — but the wheel must not import the main package, and the main package should not depend on the wheel for intake parsing. The chosen design embraces the duplication and **guards it**: `tests/test_llm_json_parity.py` runs both parsers against the same adversarial inputs and fails if their behavior ever diverges (excepting the intentional difference — each raises its own package's error type). Zero new coupling; drift made loud. 

**O1 — the stage table (Sessions 119–122).** The pipeline driver had grown into a 250-plus-line function that hand-encoded the stage sequence in four places (execution, resume gates, CLI banner, checkpoint names). O1 introduced `STAGE_ORDER` in `src/model_project_constructor/orchestrator/pipeline.py` — a descriptor tuple naming each stage's checkpoint, runner, and halt status — first dormant with import-time drift guards and characterization tests (O1-1), then consumed by the resume gates and CLI banner (O1-2), then by the decomposed driver itself (O1-3: `_run_or_load_stage`, `_save`, `_halt`, `_derive_data_request` helpers extracted from the god-function). Zero behavior change, proven by the safety net built *before* the refactor.

**O3 — `REPO_PLATFORMS` (Sessions 115–118)** — the host registry, told in §6.

**O4 — controlled vocabularies (Sessions 123, 127–130).** The generalization of Session 108's framework-parity fix: wherever a prompt enumerates legal values for a schema field, derive the enumeration from the `Literal` type instead of hand-listing it. Six intake enumerations (O4-1, §3) and the data-agent's in-wheel derivation (O4-2, §4), every rendered prompt proven byte-identical. The supporting cast lives in `src/model_project_constructor/_vocab_guard.py`: `join_members` renders member lists; `assert_vocab_parity` pins dict keys to `Literal` members at import time — used by the host registry, the stage table, and the governance maps alike.

**E4 — the provider factory (Sessions 132–133)** — explicit LLM-provider selection, told in §6.

**Audit-adjacent guards (Sessions 104, 108–109, 113)** — the UI cap interpolation (§3), the governance-framework parity (§5), and the tier/cadence import-time guards (§5).

Two execution disciplines from this program are visible in the git history. First, every overhaul ran **plan-session-then-implementation-sessions**, one phase per session, each phase independently verified (byte-identical prompts, mutation-proven tests, characterization safety nets). Second, overhaul implementation moved to **feature branches with fast-forward landings** — O4-1, O4-2, and E4 each landed onto `master` as a verified, byte-identical fast-forward merge in its own session, with the full gate re-run on the landed tree before push.

---

## 10. Methodology arc

The methodology framework itself evolved across the project. Every session is governed by `SESSION_RUNNER.md` and `SAFEGUARDS.md`; failures teach the framework something the next session inherits. Project-specific institutional memory now lives in `PROJECT_LEARNINGS.md` at the repository root — 58 promoted learnings at the time of this rewrite — after **Sessions 124–126 (2026-06-07/08)** migrated the project's learnings table out of the synced framework file (so the upstream `SESSION_RUNNER.md` can be updated without merge conflicts) into a project-owned home. The promotion pipeline has its own discipline: a candidate learning must recur across three sessions before it hardens into a row, and **Session 112's** audit of the candidate roster found (and fixed the process behind) silently-reused candidate numbers.

**Session 17 — Pilot readiness (2026-04-15)** worked through every one of architecture-plan §14's 46 acceptance criteria and declared the pilot gate met. The `[0.1.0 — Pilot Ready]` tag in `CHANGELOG.md` dates from this session: 422 tests at the time, both platform adapters passing structural + integration tests, CI green across all four jobs.

**Session 18 — Tutorial (2026-04-16)** wrote `scripts/run_pipeline.py` and `docs/tutorial.md`. The session also made a small but durable content correction: *likelihood* replaced with *probability* wherever the context was `P(event)` — a common conflation in LLM-generated text with a real statistical distinction behind it. That preference later grew into the **statistical terminology glossary (Sessions 61–62, 2026-04-19/20)**: `docs/style/statistical_terms.md` curates ~30 commonly-conflated terms with an amendment process, and curated subsets are injected into the system prompts of the agents that emit prose — the intake interviewer and the data agent's summary/datasheet surfaces, with tests pinning both where the notes appear and where they deliberately do not (SQL generation, governance classification).

**Sessions 19, 20A, 20B — Wiki expansion (2026-04-16)** wrote the original wiki — the pages you are reading now. The same cluster changed the license from Proprietary to **MIT** across `LICENSE`, both `pyproject.toml` files, and the SBOM page — an explicit decision to make the project shareable.

**Releases.** The version story runs: `[0.1.0 — Pilot Ready]` as a changelog tag (Session 17); the first real release marker and annotated git tag `v0.1.0` (Session 74, 2026-05-12, after a six-session carry and an operator decision to align the README to the canonical PEP 440 literals); changelog formalization and the wiki mirror (Sessions 78/80); and **v0.2.0 (Session 111, 2026-06-04)** — tagged after a 118-citation wiki accuracy resync, capturing the business-value arc, the audit program's first wave, and the inventory work.

**The tutorial renderer (Sessions 54–55, 65–67).** The tutorial was first rendered to standalone HTML by a pandoc wrapper script (Session 54), with multi-command code blocks split for copy-paste ergonomics (Session 55). Sessions 65–67 replaced that with MkDocs + Material — chosen for its native per-block copy button, the exact UX gap the splits had worked around — building locally with a strict whitelist and publishing via a dedicated GitHub Actions workflow (`.github/workflows/publish-tutorial.yml`) to GitHub Pages. The pandoc script was retired.

### Documentation-accuracy thread (Sessions 38–45, 63–64, 84, 111, 134–148)

The methodology arc's largest sub-thread is the long campaign to make outward-facing documentation *stay* true, which ran from simple freshness sweeps to a CI-enforced citation convention.

**Wiki-freshness sweeps (Sessions 38, 40–42, 2026-04-18).** Three-pattern grep inventories plus per-page reads caught narrative drift (the question-cap story of §3), env-var names that had never existed, and stale test counts. The lesson that compounded: one constant bump can drift across six prose surfaces, and each sweep's grep patterns miss the forms the next sweep finds.

**The Evolution plan (Sessions 43–46, 2026-04-18).** Session 43 designed the documentation convention itself: the **inward/outward split** (the wiki is outward-facing; everything else in the repo root and `docs/` is internal to the methodology), the **three-surface "what changed" split** (`CHANGELOG.md` = maintainer ledger, wiki Changelog = audience summary, this page = decision arc), the **planning-doc archive** (`docs/architecture-history/` with in-file banners), and this page's **user-triggered full-rewrite discipline** with an explicit pre-commit review gate. Sessions 44–46 implemented it: `docs/methodology/PROJECT_CONVENTIONS.md`, the archive move, and this page's first edition.

**Publish parity (Sessions 63–64, 84).** Session 63 discovered the live GitHub Wiki was roughly forty sessions stale — the repo's wiki source had evolved continuously, but nothing pushed it. The root-cause fix came in two steps: `scripts/publish_wiki.sh` (Session 64), an idempotent rsync-mirror publisher with provenance-rich commit messages; then full automation (Session 84) via a tracked `.githooks/post-commit` hook that invokes the publisher whenever a commit touches the wiki source. Since then, source-edit equals publish.

**Parity is not accuracy (Sessions 111, 134).** Session 111's pre-release resync corrected 43 drifted code citations; **Session 134 (2026-06-10)** then formalized the distinction the project had been circling: *publish parity* (is the live wiki identical to the source?) and *content accuracy* (does the source still describe the code?) are different questions, and the auto-publish hook answers only the first. Its audit — delivered as `docs/audits/2026-06-10-wiki-vs-code-accuracy-audit.md` — found the wiki content frozen at Session 114's state, 39 commits stale, with 79 confirmed findings (16 high). Sessions 135–136 remediated all of them, live-published.

**Kill the citation drift class (Sessions 137–143).** The audit's recurrence-prevention analysis identified hardcoded `file:line` citations as the single largest drift channel — a citation goes stale the moment the cited file gains a line above it, and a fresh inventory found dozens already mis-pointing *days* after remediation. The chosen fix (over publish-time line-number generation, which would have broken the parity model): migrate every citation to **grep-locatable symbol references with full repository paths** — the convention this page now follows. Sessions 138–141 migrated the seven mechanically-migratable cited pages; **Session 142** added the CI recurrence guard, `tests/test_wiki_no_line_citations.py`, which fails the build if any fragile line-citation form reappears on any wiki page; and **Session 143** closed the campaign with this page's rewrite — the last allowlisted page, now clean, with the guard's allowlist empty and the invariant enforced wiki-wide.

**Post-campaign accuracy maintenance (Sessions 144–148).** With the citation drift class structurally closed, the documentation work shifted from building enforcement to routine upkeep. **Session 144 (2026-06-11)** executed the SR 11-7 → SR 26-2 regulatory-citation rename the §2 note had anticipated — a 26-file sole-writer change touching the governance vocabulary in code, nine test files and seven fixtures, the tutorial, and seven wiki pages, with the Session-108 framework-parity guard (§5) proving the intake prompt and the artifact map stayed byte-identical; the operator ruled it citation-level only, so the artifact sets and behavior are unchanged and the historical records keep the old name. The remaining sessions of this window were operational and are listed in the [Deliberately omitted](#deliberately-omitted) appendix: a wiki-accuracy micro-audit that worked the standing-corrections list down (Session 145), a `ROADMAP.md` staleness fix on the inward maintainer surface (Session 146), and another application of the planning-doc archive convention (designed in Sessions 43–46) — two delivered plans moved into `docs/architecture-history/` (Session 147, see [References](#references)). **Session 148** is this rewrite, which retired the SR-rename open thread and folded the window in.

---

## 11. Current state

Today (2026-06-12, 148 sessions in, version **v0.2.0**) the pipeline runs end-to-end in three modes: Scope A (all fixtures), Scope B-1 (real Anthropic data agent, fixture intake), Scope B-2 (real Anthropic on both intake and data, scripted answers) — plus `--resume <run_id>` recovery from any checkpoint, status-aware so failed stages re-execute. Live runs against real GitLab and real GitHub — including GitHub Enterprise — produce complete scaffolded projects with governance artifacts proportional to the risk tier the intake agent derived, business-case and value-measurement sections populated from the interview, and a collected pre-model baseline. 797 tests pass at 97.28% coverage against a 95% floor; CI is green across the `lint`, `typecheck`, `test`, and `decoupling` jobs; `BACKLOG.md` is empty.

The codebase is structured as:

- `src/model_project_constructor/orchestrator/` — stage-table-driven pipeline driver (`STAGE_ORDER`), resume logic (`determine_resume_point`), the `IntakeReport ↔ DataRequest` adapter plus inventory converters, checkpoints, observability composition helpers, and the `REPO_PLATFORMS` platform registry with env-var-driven settings.
- `src/model_project_constructor/agents/intake/` — intake agent LangGraph flow, five required report sections, schema-derived prompt enumerations, provider factory, fixture-driven CLI, `run_scripted` for scripted-answer live runs.
- `src/model_project_constructor/ui/intake/` — FastAPI/SSE/HTMX web UI with SQLite session persistence.
- `packages/data-agent/` — standalone data agent package: canonical pipeline schemas, `sqlparse` validation, the data-source-inventory contract with its `information_schema` reference producer, baseline collection, its own provider factory and Typer CLI. Reusable as a query-writing tool per `docs/architecture-history/initial_purpose.txt`.
- `src/model_project_constructor/agents/website/` — website agent LangGraph flow, dual platform adapters behind the neutral `RepoClient` protocol, governance templates with import-time vocabulary guards, business-case and measurement-plan renderers.
- `src/model_project_constructor/schemas/` — v1 payload schemas with `HandoffEnvelope` versioning and the registry; data-side schemas re-exported from the wheel.
- `src/model_project_constructor/_vocab_guard.py` — the shared single-source utilities (`assert_vocab_parity`, `join_members`) that keep every controlled vocabulary honest.
- `docs/wiki/claims-model-starter/` — 21 outward-facing wiki pages plus the sidebar, auto-published to the live GitHub Wiki by the tracked `post-commit` hook, with the no-line-citation invariant CI-enforced.
- `docs/methodology/` + `PROJECT_LEARNINGS.md` — the imported framework, project-local conventions, and 58 promoted learnings.
- `docs/architecture-history/` — archived plans (concept-era and recently-delivered) with dated banners; `docs/planning/` — plans still open or delivered-but-not-yet-archived; `docs/audits/` — the two 2026-06 audits.
- `scripts/` — `scripts/run_pipeline.py` (the end-to-end driver) and `scripts/publish_wiki.sh` (the idempotent wiki publisher).

Open threads at the time of this rewrite: the optional publish-hook citation warning (the CI guard is the primary mechanism), the `CHANGELOG.md` entry gap for Sessions 114 onward (session records for that range live in `SESSION_NOTES.md` and the per-session close-out commits), and a standing list of small code-and-doc maintenance items tracked in the session handoffs (a few governance/adapter refactors and doc-accuracy micros). The **SR 11-7 → SR 26-2 citation swap** that earlier editions carried as open is now closed — it landed in Session 144 (§2), so the governance-framework vocabulary and the wiki cite the current name.

---

## 12. Chronological index

The narrative above is thematic. This table is chronological for readers who want to cross-reference against `CHANGELOG.md`, `SESSION_NOTES.md`, or `git log`. Each row names the session(s), date, dominant theme, and a one-phrase summary. Sessions not listed are in the [Deliberately omitted](#deliberately-omitted) appendix.

| # | Date | Theme | Summary |
|---|---|---|---|
| 0 | 2026-04-10 | Concept origins | Iterative Session Methodology v2.1 adopted; `ROADMAP.md` / `BACKLOG.md` / `CLAUDE.md` populated |
| 1 | 2026-04-10 | Concept origins | `docs/architecture-history/architecture-approaches.md` — four architectural alternatives with pros/cons |
| 2–3 | 2026-04-14 | Foundational | Canonical `docs/architecture-history/architecture-plan.md` (14 phases); v1 payload schemas + `HandoffEnvelope` |
| 4 | 2026-04-14 | Data agent | Phase 2A core — LangGraph flow, AST-walk decoupling test, `sqlparse` validation |
| 5 | 2026-04-14 | Data agent | Phase 2B standalone package; `AnthropicLLMClient`; coverage floor 80% → 90% |
| 6 | 2026-04-14 | Intake agent | Phase 3A core — question/revision budgets, 6-token accept vocab |
| 7 | 2026-04-14 | Intake agent | Phase 3B web UI — FastAPI + SSE + HTMX, SQLite persistence, fixture statelessness |
| 8 | 2026-04-14 | Website agent | Phase 4A core — `CREATE_PROJECT` / `SCAFFOLD_BASE` / `INITIAL_COMMITS` nodes |
| 9 | 2026-04-14 | Website agent | Phase 4B governance — tier/cycle fan-out, `is_governance_artifact` classifier, `PythonGitLabAdapter`, retry/backoff |
| 10–14 | 2026-04-15 | Platform abstraction | Four-phase abstraction plan + Phases A–D — neutral rename, GitHub Actions CI, `PyGithubAdapter`, `--host` CLI |
| 15 | 2026-04-15 | Foundational | Phase 5 Orchestrator — sequential driver, adapters, checkpoints, `PipelineStatus` |
| 16 | 2026-04-15 | Foundational | Phase 6 hardening — observability via composition, zero new deps, four-job CI |
| 17 | 2026-04-15 | Methodology | Pilot readiness — all 46 §14 criteria verified; `[0.1.0 — Pilot Ready]` tag |
| 18 | 2026-04-16 | Methodology | `scripts/run_pipeline.py` + `docs/tutorial.md`; likelihood → probability |
| 19–20B | 2026-04-16 | Methodology | Wiki expansion (21 pages + sidebar); license → MIT |
| 21 | 2026-04-16 | Methodology (doc-reorg) | First documentation-hygiene session — `CHANGELOG.md` stub → authoritative history |
| 22 | 2026-04-16 | Platform abstraction | First live end-to-end smoke; adapter-kwarg fix; 5 latent findings filed |
| 23 | 2026-04-16 | Methodology (planning) | `docs/planning/scope-b-plan.md` written (Scope B real-LLM intake + data plan) |
| 24 | 2026-04-16 | Data agent | Scope B-1 real Anthropic data agent — `--llm {none,data}`, `--model`, `--db-url` |
| 25 | 2026-04-16 | Methodology | CI ruff scope extended to `scripts/` |
| 26 | 2026-04-16 | Intake agent | Scope B-2 — `--llm both`, `run_scripted`, `_draft_incomplete_from_exception` adapter |
| 27 | 2026-04-17 | Intake agent | `MAX_QUESTIONS` 10 → 20; fixture extended; B-2 happy path reaches COMPLETE |
| 28 | 2026-04-17 | Platform abstraction | `validate_namespace` fail-fast validator (URL-prefix rejection) |
| 29 | 2026-04-17 | Methodology | CI mypy scope extended to `packages/`; Anthropic `TextBlock` guard |
| 30 | 2026-04-17 | Platform abstraction | GitHub branch two-bug fix (constructor kwarg + missing host-URL read) |
| 31 | 2026-04-17 | Methodology | `OPERATIONS.md` live-recipe re-audit; six findings |
| 32 | 2026-04-17 | Platform abstraction | GitLab CLI default URL placeholder → `gitlab.com`; test symmetry restructure |
| 33 | 2026-04-17 | Methodology (doc-reorg) | BACKLOG/ROADMAP protocol-erosion sweep |
| 34–37 | 2026-04-17 | Methodology | Paste-and-verify F6; `ResourceWarning` cleanup; tutorial placement fix; test symmetry closure |
| 38 | 2026-04-18 | Methodology (doc-reorg) | Wiki freshness sweep (6 pages) |
| 40–42 | 2026-04-18 | Methodology (doc-reorg) | Wiki freshness sweep (14 pages); question-cap drift-class closure across wiki + source docstrings |
| 43–45 | 2026-04-18 | Methodology (doc-reorg) | Evolution/documentation-convention plan; `docs/methodology/PROJECT_CONVENTIONS.md`; `docs/architecture-history/` archive |
| 46 | 2026-04-18 | Methodology (doc-reorg) | This page's first edition |
| 47 | 2026-04-18 | CI / quality gates | Coverage floor 94% → 95% |
| 48–51 | 2026-04-18 | Orchestrator | Resume-from-checkpoint: plan, `determine_resume_point`, `run_pipeline` wiring, `--resume` CLI; supersedes B-3 |
| 52 | 2026-04-19 | Orchestrator | Status-aware resume demotion — FAILED envelopes re-execute their stage |
| 53 | 2026-04-19 | Data agent | JSON parser tolerates prose around markdown fences (live-LLM bug) |
| 54–55 | 2026-04-19 | Methodology | Pandoc tutorial renderer + per-command code-block splits (both superseded by MkDocs, below) |
| 56 | 2026-04-19 | Intake agent | Data-source probing prompts — named P&C systems, owners, refresh cadence |
| 57–60 | 2026-04-19 | Data agent | Data-source inventory: contract plan + schema + `information_schema` producer + consumer integration |
| 61–62 | 2026-04-19/20 | Methodology | Statistical terminology glossary + agent prompt injection |
| 63–64 | 2026-04-20 | Methodology (doc-reorg) | Live-wiki 40-session drift discovered + synced; `scripts/publish_wiki.sh` publisher |
| 65–67 | 2026-04-20 | Methodology | Tutorial renderer migrated to MkDocs + Material; CI publish to GitHub Pages |
| 69, 71–73 | 2026-05-12 | Methodology | Learnings promotions (structured-file edit discipline family) |
| 70 | 2026-05-12 | Data agent | Inventory Phase 4 — `intake_qa_pairs_to_inventory`, `--inventory-from-intake` |
| 74 | 2026-05-12 | Release | `v0.1.0` annotated tag; version markers aligned to canonical |
| 75–77 | 2026-05-12/13 | Methodology (doc-reorg) | Inventory-documentation delta: audit-first plan + two execution sessions |
| 78, 80 | 2026-05-13 | Release | CHANGELOG `[0.1.0]` transition + wiki Changelog mirror |
| 79, 82–83 | 2026-05-13 | Methodology | Learnings promotions (pre-grep recipes; open-contract-questions handoff pattern) |
| 81 | 2026-05-13 | Data agent | `--curated-inventory` flag + curated/interview merge logic |
| 84 | 2026-05-13 | Methodology (doc-reorg) | Auto-publish wiki via tracked `.githooks/post-commit` hook |
| 85–91 | 2026-05-21/22 | Business value | Business-value-capture plan + six phases: schema, intake, data baseline, website pre/post, cross-doc |
| 92 | 2026-05-22 | Methodology | Learning promotion (checkpoint-commit discipline) |
| 93 | 2026-05-22 | Business value | Executive summary (Quarto) for business stakeholders |
| 97 | 2026-06-01 | Audit / overhauls | Technical-debt audit — 44 findings, 37 quick wins + architectural overhauls; `docs/audits/` created |
| 98–100 | 2026-06-01/02 | Audit / overhauls | Twin-parser hardening campaign — fence parser port + text-block + empty-content guards |
| 101 | 2026-06-02 | Methodology | Learnings promotions (scope discipline; 4-lens port verification) |
| 102–103 | 2026-06-03 | Audit / overhauls | O2 — behavioral-parity drift guard for the twin JSON parsers (no merge) |
| 104 | 2026-06-03 | Intake agent | UI question-cap copy interpolates `MAX_QUESTIONS` (Audit #19) |
| 106–107, 110 | 2026-06-03/04 | Methodology | Learnings promotions (claim cross-checking; read-only subagent discipline) |
| 108–109 | 2026-06-04 | Website agent | Governance-framework parity — `GOVERNANCE_FRAMEWORKS` ↔ `_FRAMEWORK_ARTIFACTS` reconciled + wiki mirror |
| 111 | 2026-06-04 | Release | Wiki citation resync (43 corrections) + **v0.2.0** tagged |
| 112 | 2026-06-05 | Methodology | Candidate-roster audit — number-reuse process flaw found + fixed |
| 113 | 2026-06-05 | Website agent | Tier-2 drift guards — vocab parity raise + honest schema-versioning cleanup |
| 114 | 2026-06-05 | Methodology (doc-reorg) | Wiki resync to the schema-versioning cleanup |
| 115–118 | 2026-06-05 | Platform abstraction | O3 — `REPO_PLATFORMS` registry: plan + membership + URL/token + adapter-factory phases |
| 119–122 | 2026-06-06/07 | Orchestrator | O1 — stage-descriptor table: plan + `STAGE_ORDER` + single-sourced gates/banner + god-function decomposition |
| 123 | 2026-06-07 | Audit / overhauls | O4 controlled-vocabulary plan |
| 124–126 | 2026-06-07/08 | Methodology | Learnings table migrated to `PROJECT_LEARNINGS.md`; branch landed + cleaned |
| 127–128 | 2026-06-08 | Intake agent | O4-1 — six intake prompt enumerations derived from schema `Literal`s; landed |
| 129–130 | 2026-06-08 | Data agent | O4-2 — in-wheel `expected_row_count_order` derivation; landed; O4 complete |
| 131 | 2026-06-09 | Methodology | Five learnings promotions + roster reconciliation |
| 132–133 | 2026-06-09/10 | Audit / overhauls | E4 — `make_llm_client` provider factories + `--provider` flags; landed |
| 134 | 2026-06-10 | Methodology (doc-reorg) | Wiki-vs-code accuracy audit — parity ≠ accuracy; 79 confirmed findings |
| 135–136 | 2026-06-10 | Methodology (doc-reorg) | Audit remediation — 16 high + 63 medium/low findings fixed, live-published |
| 137 | 2026-06-10 | Methodology (doc-reorg) | Citation→symbol-reference migration plan (+ README test-count fix) |
| 138–141 | 2026-06-10/11 | Methodology (doc-reorg) | Citation migration Phases 1–4 — seven pages to symbol/anchor references, live-published |
| 142 | 2026-06-11 | CI / quality gates | Recurrence guard — `tests/test_wiki_no_line_citations.py` + stale-allowlist companion |
| 143 | 2026-06-11 | Methodology (doc-reorg) | This rewrite — citation campaign Phase 5; guard allowlist now empty |
| 144 | 2026-06-11 | Methodology (doc-reorg) | SR 11-7 → SR 26-2 regulatory-citation rename across vocab, tests, fixtures, tutorial, 7 wiki pages; parity guard held |
| 148 | 2026-06-12 | Methodology (doc-reorg) | This rewrite — Evolution refresh: SR-rename open thread retired; Sessions 144–147 accounted for |

---

## Deliberately omitted

The sessions below are intentionally excluded from the arc above. Each is operational — genuine maintenance work — and would not add arc-level context if narrated. The entry exists so a reader of the session record does not have to wonder *"was this session forgotten, or left out on purpose?"*

| Session | Date | Summary | Reason for omission |
|---|---|---|---|
| 39 | 2026-04-18 | Updated a single stale test-count row on the Monitoring-and-Operations wiki page | Single-row staleness fix; the freshness-sweep story is carried by Sessions 38 and 40–42 |
| 68 | 2026-05-12 | Added an interim `0.01` version marker to the README | Superseded two working days later by Session 74's canonical `v0.1.0` alignment and tag |
| 94 | 2026-05-26 | Gitignored executive-summary render artifacts; one stale "max 10" doc string fixed | Housekeeping; the render-artifact policy is narrated with Session 93 |
| 95 | 2026-05-26 | Backfilled two research-synthesis pieces (Claude-usage table, cost framing) into existing wiki pages | Targeted wiki backfill; no new design decision |
| 96 | 2026-06-01 | Refreshed the vendored `docs/methodology/` framework files to canonical parity | Framework sync; the methodology-ownership story is carried by Sessions 124–126 |
| 105 | 2026-06-03 | Fixed two stale "10-question" test docstrings | Tail end of the Session 27 drift class, narrated in §3 |
| 145 | 2026-06-11 | Wiki-accuracy micro-audit — 11 corrections across Contributing, Changelog, Security-Considerations | Operational upkeep; the wiki-accuracy campaign is carried by Sessions 134–136 and §10 |
| 146 | 2026-06-11 | `ROADMAP.md` staleness fix — test count, decoupling-invariant phrasing, `--llm` wiring, remaining-work block | Inward (maintainer-facing) doc accuracy; the outward documentation-accuracy thread is §10 |
| 147 | 2026-06-12 | Archived two delivered plans (`evolution-page-plan.md`, `wiki-citation-symbol-references-plan.md`) into `docs/architecture-history/` per the planning-doc archive convention | Operational archive move; the archive convention is narrated with Sessions 43–46, and the plans now appear in [References](#references) |

---

## References

Archived plans live at `docs/architecture-history/`:

- `docs/architecture-history/initial_purpose.txt` — Original brief. Subrogation worked example; 6-step pipeline vision; expert-data-scientist persona for the intake agent; value argument.
- `docs/architecture-history/architecture-approaches.md` — Session 1 exploration of four architectural alternatives with pros/cons.
- `docs/architecture-history/architecture-plan.md` — Session 2 canonical 14-phase plan. §7 decoupling invariant; §8 governance-artifact framework; §14 acceptance criteria (all verified in Session 17).
- `docs/architecture-history/github-gitlab-abstraction-plan.md` — Session 10 four-phase plan for platform abstraction.
- `docs/architecture-history/pilot-readiness-audit.md` — Session 17 verification of all §14 acceptance criteria, with PILOT-READY declaration.
- `docs/architecture-history/evolution-page-plan.md` — Session 43 design plan for this page and the documentation conventions (§10); delivered, archived in Session 147.
- `docs/architecture-history/wiki-citation-symbol-references-plan.md` — the citation→symbol-reference migration plan (§10); delivered, archived in Session 147.

Active-era plans (still in `docs/planning/`) referenced by this page: `docs/planning/resume-from-checkpoint-plan.md`, `docs/planning/data-source-inventory-contract-plan.md`, `docs/planning/business-value-capture-plan.md`, `docs/planning/o1-stage-driver-plan.md`, `docs/planning/o2-shared-llm-json-plan.md`, `docs/planning/o3-repo-platforms-plan.md`, `docs/planning/o4-controlled-vocabulary-plan.md`, `docs/planning/tutorial-renderer-migration-plan.md`. The citation-migration and Evolution-page plans moved to `docs/architecture-history/` in Session 147 (listed above).

Audits live at `docs/audits/`: the 2026-06-01 technical-debt audit (spawned the §9 program) and the 2026-06-10 wiki-vs-code accuracy audit (spawned the §10 citation campaign).

Current maintainer-facing sources:

- `CHANGELOG.md` (repo root) — per-session commit-linked ledger through Session 113; later sessions are recorded in `SESSION_NOTES.md` and per-session close-out commits in `git log`.
- `SESSION_NOTES.md` (repo root) — per-session narrative; the rationale source this page draws on.
- `PROJECT_LEARNINGS.md` (repo root) — the project's 58 promoted institutional learnings.
- `docs/methodology/PROJECT_CONVENTIONS.md` — inward/outward convention, three-surface split, archive convention, and this page's update discipline including the explicit review gate.

Related wiki pages:

- [Architecture Decisions](Architecture-Decisions) — focused rationale for specific current-code choices.
- [Changelog](Changelog) — audience-facing release summary.
- [Contributing](Contributing) — dev setup, code-quality gates, commit convention.
- [Content Recommendations](Content-Recommendations) — wiki gap list and maintenance notes.
