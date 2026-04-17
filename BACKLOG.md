# Backlog

## Completed

### Architecture Plan (Milestone 1) — Phase 1
- [x] **Define agent boundaries** — Agent responsibilities, inputs, outputs, and failure modes defined in `docs/planning/architecture-plan.md` §4, §13.
- [x] **Design inter-agent handoff protocol** — `HandoffEnvelope` with versioning in `src/model_project_constructor/schemas/envelope.py`; registry in `schemas/registry.py`. See §6.
- [x] **Define output document schemas** — Pydantic models in `src/model_project_constructor/schemas/v1/`. See §5.
- [x] **Choose technology stack** — LangGraph + Claude + python-gitlab/PyGithub + Pydantic. See §9.

### Data Agent (Milestone 2 — Step 3) — Phases 2A, 2B
- [x] **Build query generation agent** — LangGraph flow in `packages/data-agent/`.
- [x] **Implement quality-check query generation** — SQL parse validation via `sqlparse`.
- [x] **Implement data expectation confirmation** — Datasheet generation from seeded queries.
- [x] **Generate data summary report** — `DataAgent.run(DataRequest) -> DataReport`.
- [x] **Standalone package + CLI** — `packages/data-agent/` with its own `pyproject.toml` and CLI.

### Intake Agent (Milestone 3 — Step 2) — Phases 3A, 3B
- [x] **Design interview flow** — One-question-at-a-time, max 10 questions, P&C claims domain.
- [x] **Build intake agent system prompt** — Expert data scientist / business analyst / consultant persona.
- [x] **Implement document generation** — Produces structured `IntakeReport` with `GovernanceMetadata`.
- [x] **Add review loop** — Draft review with 3-revision cap.
- [x] **Web UI** — FastAPI + SSE + HTMX frontend with SQLite session persistence.

### Website Agent (Milestone 4 — Steps 4-5) — Phases 4A, 4B, plus GitHub/GitLab abstraction (Phases A-D)
- [x] **Build website section generator** — LangGraph flow in `src/model_project_constructor/agents/website/`.
- [x] **Implement initial model build** — `.qmd` files and `src/` module stubs generated.
- [x] **GitLab/GitHub project scaffolding** — Dual-host support via `RepoClient` protocol, `PythonGitLabAdapter`, `PyGithubAdapter`.
- [x] **Package extension ideas** — Extension suggestions included in generated project.
- [x] **Governance scaffolding** — Artifacts proportional to `risk_tier` and `cycle_time` per §8.

### Orchestrator + Production Hardening (Milestone 5) — Phases 5, 6
- [x] **Wire pipeline end-to-end** — `orchestrator/pipeline.py` with `run_pipeline` + callable runners.
- [x] **Error handling between steps** — `FAILED_AT_*` halt paths with checkpoint persistence.
- [x] **End-to-end test suite** — 422 tests at 97.18% coverage; both GitLab and GitHub paths tested.
- [x] **Observability** — Structured logging (`make_logged_runner`) + metrics (`MetricsRegistry` + `make_measured_runner`).
- [x] **Configuration** — `OrchestratorSettings.from_env()` with env-var validation; `.env.example` template.
- [x] **CI** — `.github/workflows/ci.yml` (lint + test + typecheck + decoupling).
- [x] **Documentation** — `OPERATIONS.md` runbook, `TROUBLESHOOTING.md` diagnostics.

## Up Next

*All 6 planned phases of `docs/planning/architecture-plan.md` §14 are complete. The pilot readiness audit (Session 17) and ruff cleanup sweep (Session 17) previously listed here are done — see `CHANGELOG.md` for details. Session 22 completed Scope A of "First live end-to-end run" (live repo-creation smoke test); Scope B (real LLM-backed intake + data) remains open. Potential next steps:*

- [ ] **First live end-to-end run (Scope B) — real LLM-backed intake + data agents** — Scope A (Session 22), B-1 (Session 24), B-2 wiring (Session 26) complete. Plan: `docs/planning/scope-b-plan.md`. Remaining:
  - [x] **B-1: real data agent wired** — Session 24 added `--llm data` to `scripts/run_pipeline.py`. See `CHANGELOG.md`.
  - [x] **B-2: scripted-answers intake wiring** — Session 26 added `--llm both --intake-fixture PATH` with `IntakeAgent.run_scripted(...)` + inline `_draft_incomplete_from_exception` adapter + 5 new unit tests. See `CHANGELOG.md`. Adapter verified live on two failure paths.
  - [ ] **B-2 follow-up: verify end-to-end `COMPLETE` with `--llm both`** — Session 26's live happy-path run produced `DRAFT_INCOMPLETE` because the real LLM hit `MAX_QUESTIONS=10` before flipping `believe_enough_info=true` (+ `nodes.py:131` auto-appends `questions_cap_reached`). Next session: bump `MAX_QUESTIONS` to 20 in `src/model_project_constructor/agents/intake/state.py:57`; grep for tests asserting the old value (`MAX_QUESTIONS == 10` or `== 10` near intake state); extend `tests/fixtures/subrogation_b2.yaml` to ~15 qa_pairs pre-answering the 3 gaps Claude flagged in Session 26 (latency SLA, per-claim recovery $, fairness/bias testing plan); re-run `--llm both` and verify `status: COMPLETE`. One session. Out-of-scope items in Session 26 per plan §14 anti-scope #2 (agent code untouched).
  - [ ] **B-3 (optional): Web UI bridge** — Per plan §7.3. `--resume-intake <session_id>` reads completed `IntakeReport` from the intake UI's SQLite store. Plan §8.3 recommends deferring unless user wants a production-shape demo; "Automated resume-from-checkpoint" item below may supersede.
- [ ] **Clearer `MPC_NAMESPACE` validation and docs** (Session 22 finding) — `.env.example`, `OPERATIONS.md` §1, and `docs/tutorial.md` §5 don't state that `MPC_NAMESPACE` is a group path, not a URL. Users set the full URL and hit a generic `"group lookup failed: 404"`. Add a validator to `OrchestratorSettings.from_env()` (or the adapter) that detects a leading `http://` / `https://` and raises `ConfigError("MPC_NAMESPACE must be a group path, not a URL; got '...'")`. Also add a one-line note to the three docs.
- [ ] **CI typecheck coverage extension to `packages/`** (Session 22 finding) — `pyproject.toml` declares `[tool.mypy] packages = ["model_project_constructor", "model_project_constructor_data_agent"]` but CI runs `mypy src/` which skips `packages/data-agent/`. Running mypy with the declared packages surfaces 13 errors. The largest cluster is `packages/data-agent/.../anthropic_client.py:218` where `block.text` is called on a union that has grown ~8 variants in the Anthropic SDK since Phase 2. Add a type-guard (`if isinstance(block, TextBlock)`) and extend the CI typecheck command.
- [ ] **Self-hosted GitHub URL override** (Session 22 finding, code-read only) — `docs/tutorial.md` §5c claims `MPC_HOST_URL="https://github.mycompany.com/api/v3"` works for GHE, but `scripts/run_pipeline.py:109-113` constructs `PyGithubAdapter(token=token)` with no URL argument. Fix parallels the `host_url=` signature; pass `base_url=os.environ.get("MPC_HOST_URL")` (after verifying `PyGithubAdapter` accepts it).
- [ ] **Reconcile `OPERATIONS.md` §4.2/4.3 live-run recipes with `scripts/run_pipeline.py --live`** (Session 22 finding) — Two distinct user-facing live paths documented. Confirm whether `python -m model_project_constructor.agents.website ...` is still an intended entry point; if not, remove from OPERATIONS. If yes, add a test and a cross-reference from the tutorial.
- [ ] **Automated resume-from-checkpoint** — CLI or orchestrator logic to resume a failed pipeline run from the last successful checkpoint.
- [ ] **Add `scripts/render_tutorial.sh`** — Wrap the pandoc invocation with inline CSS (body width, hr margins, table borders) so rendering the tutorial to HTML is a one-liner.
- [ ] **Tutorial UX: split code blocks** — Split multi-command code blocks in `docs/tutorial.md` into individual blocks so each command is independently copyable. Pandoc/GitHub rendering doesn't provide per-block copy buttons, so also consider rendering to a format that does (e.g. MkDocs, Docusaurus).
- [ ] **Intake agent: data source discovery prompts** — Enhance the intake agent's system prompt to ask whether the stakeholder wants help identifying data sources, and if so, probe about existing systems (data warehouses, claims systems, policy admin). Currently the agent accepts whatever the stakeholder says about available data at face value.
- [ ] **Data agent: metadata discovery mode** — Add a discovery mode to the data agent that queries database metadata (`information_schema`, catalog tables) to identify relevant tables before generating training set queries. The data agent was designed to be reusable as a standalone query tool (per `initial_purpose.txt`); discovery mode extends that to data exploration.
- [ ] **Statistical terminology glossary** — Create `docs/style/statistical_terms.md` defining terms like probability vs likelihood, and inject it into agent system prompts so LLM-generated content uses correct statistical terminology instead of reproducing common conflations from training data.
- [ ] **Fix unclosed SQLite connection warnings** — ~20 `ResourceWarning: unclosed database` warnings from `tests/agents/data/test_data_agent.py` and one from `tests/agents/intake/test_anthropic_client.py`. Source is `ReadOnlyDB` / LangGraph checkpoint SQLite not closing connections. Surfaced by Python 3.13's stricter GC. Not a correctness issue but noisy.
- [ ] **Wiki freshness sweep** — Update `docs/wiki/claims-model-starter/` pages so each reads as a description of the current tool rather than a record of how it evolved. Specifically: walk every "Recommended additions" / "Future enhancements" / "Planned" list and (a) delete items that have already been implemented, (b) rewrite items that are only partially implemented to describe the remaining gap (not the original ask). Audit trigger: Session 19's wiki expansion and Sessions 20A/20B added surface area the "Content Recommendations" page hasn't been reconciled against; Scope B-1 (Session 24) now ships real LLM-backed data runs that some pages still describe as future work. Start with `Content-Recommendations.md`, `Home.md`, `Pipeline-Overview.md`, `Getting-Started.md`, and `Agent-Reference.md` which are the likely drift hotspots.
