# Roadmap

## Current State

**All 5 planned build milestones complete** (per `docs/architecture-history/architecture-plan.md` §14). Scope A of "First live end-to-end run" (Session 22) + Scope B-1 real data agent (Session 24) + Scope B-2 scripted-answers intake (Sessions 26-27) have shipped — real LLM-backed intake + data agents are wired into `scripts/run_pipeline.py` via `--llm data|both` (`--live` separately selects a real repo host instead of the in-memory `FakeRepoClient`).

The codebase has **923 tests passing + 8 live-skipped at 97.41% coverage** (931 collected total; current as of Session 188); CI gates lint (ruff), typecheck (mypy), test suite, and the Data Agent decoupling test (2 AST tests enforcing the architecture plan's §7 decoupling invariant).

Remaining work (tracked in `BACKLOG.md`): the enterprise-migration effort (`docs/planning/enterprise-migration.md`) — landing the `feat/bedrock-mantle-migration` branch on `origin/master` and provisioning a one-time enterprise clone of the repo + wiki. See `BACKLOG.md` for the phase-by-phase breakdown. The original pilot-delivery backlog (post-pilot operator-experience / doc-freshness improvements) shipped in full (wiki + tutorial doc-freshness work, the terminology Glossary wiki page, resume-from-checkpoint via `scripts/run_pipeline.py --resume`); the optional Scope B-3 Web UI bridge was superseded by the resume flow (`docs/architecture-history/resume-from-checkpoint-plan.md` §1.3) — its optional Phase 4 (intake UI writes the `IntakeReport.json` envelope) remains deferred.

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
- Agent boundaries, responsibilities, inputs/outputs, failure modes defined in `docs/architecture-history/architecture-plan.md` §4, §13.
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

### M6: Multi-Provider LLM Support (AWS Bedrock) — Phases A-E
- Per-provider LLM key/config seam and a named pilot model default (Phase A); an eval/parity harness — a golden P&C-domain corpus per LLM capability with concrete pass thresholds and a `live` pytest marker that keeps CI hermetic (Phase B); AWS Bedrock-hosted Claude added as a second concrete provider behind the existing protocol/factory seam, no adapter layer (Phase C); the intake web UI parameterized for provider selection via `INTAKE_LLM_PROVIDER`/`INTAKE_LLM_MODEL` (Phase D); a shadow-run → cutover gate comparing providers on the golden corpus (Phase E).
- The Bedrock client has since migrated to the `AnthropicBedrockMantle` endpoint (Bedrock API key auth, `anthropic.claude-opus-4-8` default — the mantle catalog has no Sonnet tier) with enterprise-networking hooks (`base_url`, `http_client`, `require_sigv4`) — see `CHANGELOG.md`. Live Bedrock verification remains blocked on AWS account-side model-access provisioning, unrelated to this project's code; the `anthropic` provider is the only one exercised in CI/eval today (Phase E stays NO-GO pending a measured Bedrock run).
- Archived plan: `docs/architecture-history/multi-provider-llm-plan.md`.

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
- `docs/architecture-history/architecture-plan.md` — Authoritative design document (archived); §14 phase plan.
- `docs/architecture-history/scope-b-plan.md` — Scope B (real LLM-backed pipeline) plan (archived; B1+B2 shipped, B3 superseded).
- `docs/architecture-history/github-gitlab-abstraction-plan.md` — GitHub/GitLab abstraction plan (Phases A-D, complete; archived).
- `docs/architecture-history/multi-provider-llm-plan.md` — Multi-provider LLM (AWS Bedrock) plan (Phases A-E, complete; archived).
- `docs/planning/enterprise-migration.md` — Active plan: land the branch on `origin/master` and provision a one-time enterprise clone.
- `SESSION_RUNNER.md` — Session operating procedure.
- `SAFEGUARDS.md` — Commit discipline, blast-radius limits, mode-switching rules.
