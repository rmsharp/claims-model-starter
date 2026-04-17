# Roadmap

## Current State

**All 5 planned build milestones complete** (per `docs/planning/architecture-plan.md` §14). Scope A of "First live end-to-end run" (Session 22) + Scope B-1 real data agent (Session 24) + Scope B-2 scripted-answers intake (Sessions 26-27) have shipped — real LLM-backed intake + data agents are wired into `scripts/run_pipeline.py --live`.

The codebase has **445 tests at 97.26% coverage**; CI gates lint (ruff), typecheck (mypy), test suite, and the 6 decoupling invariants.

Remaining work (tracked in `BACKLOG.md`):
- Optional Scope B-3 (Web UI bridge — deferred unless production-shape demo is wanted).
- Post-pilot operator-experience / doc-freshness improvements (wiki sweep, tutorial UX, terminology glossary, resume-from-checkpoint).

### Pipeline Overview (6 Steps)

| Step | Owner | Input | Output |
|------|-------|-------|--------|
| 1 | Business stakeholder | Model idea | Visits go/modelintake |
| 2 | **Intake Agent** | Guided interview (up to 20 questions) | Structured report: Business Problem, Proposed Solution, Model Solution, Estimated Value |
| 3 | **Data Agent** | Intake report | SQL queries for data collection + quality-check queries + data validation results |
| 4 | (handoff) | Data report + queries | Packaged handoff to website agent |
| 5 | **Website Agent** | Data report + queries + intake report | GitLab or GitHub project with draft model website (Business Understanding, Implementation Plans, Data section with EDA, Initial model build & evaluation) |
| 6 | Data science team | Repo project | Refined model (human-driven from here) |

### Domain Context

All agents operate within the context of a **claims organization in a property & casualty insurance company** selling auto and property policies. The intake agent acts as expert data scientist, business analyst, and consultant in this domain.

## Completed Milestones

### M1: Architecture & Pipeline Design — Phase 1
- Agent boundaries, responsibilities, inputs/outputs, failure modes defined in `docs/planning/architecture-plan.md` §4, §13.
- Inter-agent handoff protocol — `HandoffEnvelope` with versioning (`src/model_project_constructor/schemas/envelope.py`); registry in `schemas/registry.py`. See §6.
- Output document schemas — Pydantic models in `src/model_project_constructor/schemas/v1/`. See §5.
- Technology stack — LangGraph + Claude + python-gitlab/PyGithub + Pydantic. See §9.

### M2: Data Agent (pipeline Step 3) — Phases 2A, 2B
- LangGraph query-generation flow in `packages/data-agent/`.
- Quality-check SQL parse validation via `sqlparse`.
- Data expectation confirmation via datasheet generation from seeded queries.
- `DataAgent.run(DataRequest) -> DataReport`.
- Standalone package + CLI under `packages/data-agent/` with its own `pyproject.toml`.

### M3: Intake Agent (pipeline Step 2) — Phases 3A, 3B
- One-question-at-a-time interview flow (max 20 questions; P&C claims domain).
- Expert data scientist / business analyst / consultant persona in the system prompt.
- Structured `IntakeReport` output with `GovernanceMetadata`.
- Draft review loop with 3-revision cap.
- FastAPI + SSE + HTMX web UI with SQLite session persistence.

### M4: Website Agent (pipeline Steps 4-5) — Phases 4A, 4B + GitHub/GitLab abstraction Phases A-D
- LangGraph section-generation flow in `src/model_project_constructor/agents/website/`.
- `.qmd` files and `src/` module stubs generated for initial model build.
- Dual-host GitLab/GitHub project scaffolding via `RepoClient` protocol (`PythonGitLabAdapter`, `PyGithubAdapter`).
- Package-extension suggestions in generated projects.
- Governance scaffolding proportional to `risk_tier` and `cycle_time` per §8.

### M5: Orchestrator + Production Hardening — Phases 5, 6
- End-to-end pipeline wiring — `orchestrator/pipeline.py` with `run_pipeline` + callable runners.
- `FAILED_AT_*` halt paths with checkpoint persistence.
- Structured logging (`make_logged_runner`) + metrics (`MetricsRegistry` + `make_measured_runner`).
- `OrchestratorSettings.from_env()` with env-var validation; `.env.example` template.
- CI: `.github/workflows/ci.yml` (lint + test + typecheck + decoupling).
- `OPERATIONS.md` runbook + `TROUBLESHOOTING.md` diagnostics.

### First live end-to-end run
- **Scope A** (Session 22): live repo-creation smoke test against real GitLab.
- **Scope B-1** (Session 24): real data agent wired — `scripts/run_pipeline.py --llm data`.
- **Scope B-2** (Sessions 26-27): scripted-answers intake via `--llm both --intake-fixture PATH`; `run_b2_complete` reached `Status: COMPLETE` at `subrogation-pilot-v3` after Session 27 raised `MAX_QUESTIONS` 10→20.

## Methodology

- Iterative Session Methodology installed (SESSION_RUNNER, SAFEGUARDS, SESSION_NOTES).
- Three-file task tracking (BACKLOG — open work only, CHANGELOG — completed session history, ROADMAP — this file, milestone summary).
- Framework reference docs in `docs/methodology/`.

## Related Documents

- `BACKLOG.md` — Open work items (only).
- `CHANGELOG.md` — Chronological, session-numbered record of completed work.
- `docs/planning/architecture-plan.md` — Authoritative design document; §14 phase plan.
- `docs/planning/scope-b-plan.md` — Scope B (real LLM-backed pipeline) plan.
- `docs/planning/github-gitlab-abstraction-plan.md` — GitHub/GitLab abstraction plan (Phases A-D, complete).
- `SESSION_RUNNER.md` — Session operating procedure.
- `SAFEGUARDS.md` — Commit discipline, blast-radius limits, mode-switching rules.
