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

*All 6 planned phases of `docs/planning/architecture-plan.md` §14 are complete. Potential next steps:*

- [ ] **Pilot readiness audit** — Review all Phase 1–6 deliverables against acceptance criteria in §14 and original requirements in `initial_purpose.txt`.
- [ ] **First live end-to-end run** — Real LLM-backed pipeline run against a live GitLab/GitHub host.
- [ ] **Automated resume-from-checkpoint** — CLI or orchestrator logic to resume a failed pipeline run from the last successful checkpoint.
- [ ] **Ruff cleanup sweep** — Fix 62 pre-existing ruff errors in `ui/intake/` and other non-orchestrator files (43 auto-fixable).
