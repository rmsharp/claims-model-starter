# Changelog

This page records notable changes to the Model Project Constructor, grouped by implementation phase. Format loosely follows [Keep a Changelog](https://keepachangelog.com/). Dates are the commit dates on `master`; phases map to the structure in `docs/planning/architecture-plan.md` §14.

The repository is currently at version `0.1.0` (pre-1.0, pilot-ready). No external releases have been cut; the `master` branch is the sole integration target.

---

## [Unreleased]

Current scope: wiki expansion and pilot hardening.

### Wiki expansion — Sessions 19, 20A, 20B (2026-04-16)

- **Added:** 14 initial wiki pages for the `claims-model-starter` project including Home, Getting Started, Pipeline Overview, Generated Project Structure, Governance Framework, Development Workflow, Data Guide, Agent Reference, Monitoring and Operations, Software Bill of Materials, Architecture Decisions, Glossary, and Content Recommendations (Session 19).
- **Added:** Intake Interview Design, Schema Reference, and Security Considerations pages covering the two intake system prompts, the full Pydantic schema set field-by-field, the outbound-network boundaries, and the 9-item security review checklist (Session 20A).
- **Added:** Worked Examples, Extending the Pipeline, Changelog (this page), and Contributing pages (Session 20B).
- **Changed:** License updated from Proprietary to **MIT** across `LICENSE`, the two `pyproject.toml` files, and the SBOM wiki page (`f2f2a70`).

### End-to-end tutorial — Session 18 (2026-04-16)

- **Added:** `scripts/run_pipeline.py` — a 265-line driver that runs the full pipeline against fixture data and the `FakeRepoClient`, with `--live` for real GitLab/GitHub hosts (`4dc2f5d`).
- **Added:** `docs/tutorial.md` — six-step tutorial covering intake YAML authoring, `IntakeReport` generation, pipeline invocation, checkpoint inspection, live-host configuration, and the programmatic API (`4dc2f5d`, `1613d60`).
- **Fixed:** install command was missing `--extra ui` (`883935a`).
- **Changed:** project terminology — replaced conflated "likelihood" with "probability" in fixtures, tests, and `initial_purpose.txt` where referring to `P(event)` (`1613d60`).

---

## [0.1.0 — Pilot Ready] — 2026-04-15

Phases 1 through 6 complete. 422 tests at 97.18% coverage. Both GitLab and GitHub adapters pass structural + integration tests. CI green across lint, typecheck, test, and decoupling jobs.

### Phase 6 — Production hardening (Session 16)

- **Added:** Structured logging via `make_logged_runner` — binds `run_id` and `correlation_id` to every stage's log context (`2060d4a`).
- **Added:** Metrics registry and `make_measured_runner` — captures per-stage timing and outcomes without requiring a metrics backend (`2060d4a`).
- **Added:** `OrchestratorSettings.from_env()` — env-var-driven configuration with `require_*` guards that fail fast on missing credentials (`2060d4a`).
- **Added:** `.github/workflows/ci.yml` — four-job CI pipeline (`lint`, `typecheck`, `test`, `decoupling`) (`2060d4a`).
- **Added:** `OPERATIONS.md` production runbook and `TROUBLESHOOTING.md` diagnostics (`2060d4a`).
- **Changed:** Zero new dependencies despite plan suggesting `structlog` + `pydantic-settings` — stdlib `logging` with `extra={"context": ...}` and a plain `dataclass` + `os.environ` satisfied the requirements (per learning #13).

### Phase 5 — Orchestrator (Session 15)

- **Added:** `src/model_project_constructor/orchestrator/` package with `run_pipeline()`, `CheckpointStore`, and stage adapters (`b94cb47`).
- **Added:** `PipelineStatus` literal enum with `COMPLETE` / `FAILED_AT_INTAKE` / `FAILED_AT_DATA` / `FAILED_AT_WEBSITE` (`b94cb47`).
- **Added:** Per-stage checkpoint persistence — partial state is retained on halt so operators can inspect or resume (`b94cb47`).
- **Changed:** Coverage floor raised 93% → 94% (`c3943a8`).

### GitHub / GitLab abstraction — Phases A-D (Sessions 11-14)

Phased rename from a GitLab-specific Website Agent to a host-neutral one.

- **Phase A — Neutral rename (Session 11, `8c00e1a`):** `GitLabClient` → `RepoClient` protocol; `gitlab_target` state key → `repo_target`; `project_id` widened from `int` to `str` to accommodate GitHub's `"owner/name"` form.
- **Phase B — CI platform plumbing (Session 12, `9b2ab5e`):** `render_github_actions_ci()` sibling to `render_gitlab_ci()`; `ci_platform` kwarg threaded through `build_governance_files` to emit the correct CI config.
- **Phase C — PyGithub adapter (Session 13, `55745ed`):** `PyGithubAdapter` class implementing the `RepoClient` protocol; `PyGithub>=2,<3` added to the `agents` optional-dependency group.
- **Phase D — CLI `--host` (Session 14, `e9f0d10`):** Website-agent CLI gained `--host gitlab|github`; adapter is constructed from the flag and host-specific env vars.
- **Added:** GitHub mention in README tagline and architecture diagram (`9f20e95`).

### Phase 4B — Governance scaffolding (Session 9)

- **Added:** `src/model_project_constructor/agents/website/governance_templates.py` — tier-gated governance artifact renderers per architecture-plan §8 (`f97b530`).
- **Added:** `_FRAMEWORK_ARTIFACTS` registry for SR 11-7, NAIC AIS, EU AI Act (Article 9 and general), and ASOP 56 (`f97b530`).
- **Added:** `build_regulatory_mapping` — intersects declared frameworks with actually-emitted artifact paths (`f97b530`).
- **Added:** Fairness scaffolds (`analysis/fairness_audit.qmd`, `src/<slug>/fairness/`, `tests/test_fairness.py`) triggered by `uses_protected_attributes=true` (`f97b530`).
- **Added:** `is_governance_artifact(path)` classifier as the single source of truth for `GovernanceManifest.artifacts_created` (`f97b530`).
- **Added:** `PythonGitLabAdapter` — initial GitLab-specific adapter with retry/backoff (`f97b530`).

### Phase 4A — Website Agent core (Session 8)

- **Added:** `src/model_project_constructor/agents/website/` — LangGraph flow with `CREATE_PROJECT`, `SCAFFOLD_BASE`, and `INITIAL_COMMITS` nodes (`9887286`).
- **Added:** `build_base_files(...)` — composes the baseline 28-file generated-project skeleton (source module, seven `analysis/*.qmd` narratives, test stubs, reports, queries) (`9887286`).
- **Added:** `ProjectInfo`, `CommitInfo`, `RepoClient` protocol, `RepoNameConflictError` (`9887286`).

### Phase 3B — Intake Agent web UI (Session 7)

- **Added:** FastAPI + SSE + HTMX frontend at `src/model_project_constructor/ui/intake/` with SQLite session persistence (`1c1141a`).
- **Added:** Resumable interviews — interrupt and resume mid-interview without losing context.
- **Added:** Fixture statelessness guarantee — running against a fixture produces deterministic output regardless of previous state (`1c1141a`).

### Phase 3A — Intake Agent core (Session 6)

- **Added:** `src/model_project_constructor/agents/intake/` — LangGraph flow with eight nodes (draft question → ask → collect → evaluate → propose → review → revise → finalize) (`64b8a99`).
- **Added:** Two system prompts (interviewer + governance classifier) verbatim in `anthropic_client.py` (`64b8a99`).
- **Added:** `MAX_QUESTIONS=10` and `MAX_REVISIONS=3` budgets (`64b8a99`).
- **Added:** Six accept tokens for terminal review (`nodes.py:35`).
- **Added:** Fixture-driven CLI mode for test and replay scenarios (`64b8a99`).

### Phase 2B — Data Agent polish (Session 5)

- **Added:** `AnthropicLLMClient` — Anthropic API wrapper for query generation (`aca858a`).
- **Added:** `typer`-based CLI with Python API documentation (`aca858a`).
- **Changed:** Coverage floor raised 80% → 90% (`0b30014`).
- **Refactored:** Data agent extracted into its own `packages/data-agent/` workspace package with an independent `pyproject.toml` (`4982332`).

### Phase 2A — Data Agent core (Session 4)

- **Added:** `src/model_project_constructor/agents/data/` — LangGraph flow for query generation, quality-check query generation, and datasheet composition (`e526332`).
- **Added:** AST-based decoupling test — statically verifies the Data Agent has zero imports of `IntakeReport` or the intake schema (`e526332`).
- **Added:** `DataRequest` → `DataReport` shape including `PrimaryQuery`, `QualityCheck`, and Gebru-2021 `Datasheet`.

### Phase 1 — Schemas, envelope, registry (Session 3)

- **Added:** `src/model_project_constructor/schemas/v1/` — Pydantic v2 payload schemas for `IntakeReport`, `DataRequest`, `DataReport`, `RepoTarget`, `RepoProjectResult` (`f94e211`).
- **Added:** `HandoffEnvelope` — version-independent transport wrapper for inter-agent payloads (`f94e211`).
- **Added:** `REGISTRY` dict and `load_payload()` dispatch function (`f94e211`).
- **Added:** `StrictBase` contract — `extra="forbid"`, `protected_namespaces=()` across all payload schemas (`f94e211`).
- **Added:** `uv`-managed workspace with `pyproject.toml` + `uv.lock` (`530bff9`).

---

## [Architecture Plan] — 2026-04-10 to 2026-04-14

### Session 2 — Architecture plan

- **Added:** `docs/planning/architecture-plan.md` — 16-section plan covering agent boundaries, handoff protocol, schema versioning, governance framework, technology stack, and 6-phase implementation sequence (`5bf0d8a`).
- **Changed:** Rendering target clarified — Quarto `.qmd` narratives in `analysis/` rather than Jupyter `.ipynb` (cleanup, `5bf0d8a`).

### Session 1 — Architecture exploration

- **Added:** `docs/planning/` architecture approaches with pros/cons for four critical features (intake conversational style, data-agent reuse, governance artifact gating, host abstraction) (`4a9840c`).

### Session 0 — Project scaffolding

- **Added:** Initial commit with methodology framework (SESSION_RUNNER.md, SAFEGUARDS.md, SESSION_NOTES.md, CLAUDE.md, BACKLOG.md, ROADMAP.md, CHANGELOG.md) (`ff0228e`).
- **Added:** `initial_purpose.txt` — original project vision with the subrogation worked example.

---

## Quality-gate history

Coverage floor increases trace the maturation of the test suite:

| Date | Commit | Floor | Scope |
|---|---|---|---|
| 2026-04-14 | `0b30014` | 80% → 90% | Post Phase 2B |
| 2026-04-15 | `e91c9f2` | 90% → 93% | Post Phase 4B |
| 2026-04-15 | `c3943a8` | 93% → 94% | Post Phase 5 |

Current floor: **94%**, enforced by `--cov-fail-under=94` in CI.

Pilot-readiness fixes (Session 17, `17f661d` + `d62efc2` + `b8d8d7e`):

- **Fixed:** 62 ruff errors across `src/`, `tests/`, `packages/` (all pre-existing).
- **Fixed:** 3 CI failures — missing `mypy` deps, decoupling job's missing `--no-cov`, ANSI color codes in CLI help assertions (resolved via `click.unstyle`).

---

## Versioning policy

The project is currently pre-1.0. Schema versioning follows the registry contract at `src/model_project_constructor/schemas/registry.py:7-13`:

- **Minor bump** (1.0.0 → 1.1.0, backwards-compatible additions): register the new class under its new version key; keep 1.0.0.
- **Major bump** (1.0.0 → 2.0.0): register v2 and keep v1 for at least two major releases; provide a migration function in `schemas/migrations/`.

The envelope version (`HandoffEnvelope.envelope_version`) is versioned independently from payload schemas so the transport can evolve without forcing every payload to rev.

---

## See also

- [Getting Started](Getting-Started) — current install and first-run steps
- [Architecture Decisions](Architecture-Decisions) — the design tradeoffs behind each phase
- [Contributing](Contributing) — commit convention, review process, and quality gates
- `BACKLOG.md` (in the repository) — open work items not yet started
- `CHANGELOG.md` (in the repository) — commit-level changes seen by repo contributors (this wiki page is the audience-facing summary)
