# Changelog

> *Audience-facing release summary. For the maintainer commit-linked ledger, see `CHANGELOG.md` at the repository root. For the design-decision arc, see `Evolution` (sibling wiki page).*

This page records notable changes to the Model Project Constructor, grouped by implementation phase. Format loosely follows [Keep a Changelog](https://keepachangelog.com/). Dates are the commit dates on `master`; phases map to the structure in `docs/architecture-history/architecture-plan.md` §14.

The repository is at version `0.2.0` (pre-1.0, pilot-ready). Release tags `v0.1.0` (2026-05-12) and `v0.2.0` (2026-06-04) mark integration milestones on the `master` branch; the project is not yet published to an external package index.

---

## [Unreleased]

### LLM provider abstraction, stage-driver decomposition, host-vocabulary single-source, and prompt-enumeration derivation (Sessions 115-133)

Four architectural overhauls landed across Sessions 115-133: E4 decouples LLM-provider choice, O3 consolidates host configuration into a registry, O1 centralizes pipeline stage metadata, and O4 derives prompt enumerations from their schema Literals to prevent vocabulary drift.

#### E4 - LLM provider factory (Sessions 132-133)

- **Added:** `--provider` CLI flag (default `anthropic`) on both `scripts/run_pipeline.py` and the Data Agent; routes through `make_llm_client(provider)` factories in both the Intake and Data agents.
- **Added:** `IntakeLLMClient` and `LLMClient` protocols define the seam; `make_llm_client` factory in `src/model_project_constructor/agents/intake/factory.py` and `packages/data-agent/src/model_project_constructor_data_agent/factory.py`.
- **Added:** `LLMProvider = Literal["anthropic"]` (single-sourced via `typing.get_args()` in both agents); unknown-provider errors derive the list automatically, preventing drift.
- **Changed:** Every LLM-client construction now routes through the factory instead of hardwiring `AnthropicLLMClient()`. Lazy imports inside the factory keep both seams anthropic-free at import time.

#### O3 - Repository platform registry (Sessions 115-118)

- **Added:** `REPO_PLATFORMS` registry in `src/model_project_constructor/orchestrator/config.py` - single source of truth for host vocabulary, per-host API URLs, token env vars, and adapter factories.
- **Added:** `PlatformSpec` dataclass carrying `default_api_url`, `token_env_var`, and `adapter_factory: Callable[..., RepoClient]` for each host (GitLab, GitHub).
- **Added:** `adapter_factory` field to each platform spec - each host's factory lazy-imports its SDK (`python-gitlab` / `PyGithub`) only when an adapter is actually constructed, keeping the registry import-time SDK-free.
- **Changed:** Both live entry points (`scripts/run_pipeline.py` and `src/model_project_constructor/agents/website/cli.py`) now build the adapter via `REPO_PLATFORMS[host].adapter_factory(host_url=..., private_token=...)` - no hand-written `--host` branch dispatch.
- **Added:** Import-time drift guard `assert_vocab_parity(REPO_PLATFORMS.keys(), HostLiteral)` - fails the build if a host is added to one but not the other.
- **Changed:** `cli.VALID_HOSTS` and the pipeline argparse `choices` are now derived from `REPO_PLATFORMS.keys()`, so they auto-update when a host is registered.

#### O1 - Pipeline stage-order single-source (Sessions 120-122)

- **Added:** `STAGE_ORDER: tuple[Stage, ...]` descriptor in `src/model_project_constructor/orchestrator/pipeline.py` - the single source of truth for pipeline stage sequence, metadata, halt-condition mapping, and resume-point naming.
- **Added:** `Stage` dataclass with fields `name` (ResumePoint), `payload_type`, `target_agent`, `has_runner`, `halt_status`, `result_field`, `always_runs`, `terminal_result`.
- **Changed:** Resume gates, the CLI banner, and the decomposed helpers (`_save_stage`, `_run_or_load_stage`, `_halt`) all derive stage order from `STAGE_ORDER` instead of hand-threading stage names - impossible to drift.
- **Changed:** `run_pipeline` decomposed into four helpers: `_save_stage()`, `_run_or_load_stage()`, `_halt()`, and `_derive_data_request()` - the orchestrator is now readable and its control flow matches the architecture plan's design.

#### O4 - Prompt enumeration derivation (Sessions 127-130)

- **Added:** Six intake prompt enumerations derived at module load via `typing.get_args()` on their schema Literals: `CycleTime`, `RiskTier`, `ModelType` (from `src/model_project_constructor/schemas/v1/common.py`) and three others from intake-specific Literals.
- **Added:** Data Agent's `expected_row_count_order` prompt enumeration similarly derived from its Literal in the data-agent wheel (single-sourced, decoupling-safe).
- **Changed:** Prompt-enumeration values are no longer hand-listed in prose or system prompts - they are derived at runtime from the schema's Literal source of truth, so a vocabulary edit updates both the schema and the prompt in one place.

## [0.2.0] - 2026-06-04

### Documentation accuracy + v0.2.0 release (Session 111, 2026-06-04)

`v0.2.0` is the first minor release since `v0.1.0`. It bundles the work recorded below — most substantively the business-value-capture extension (Sessions 86–91) and the Audit #39 governance-framework reconciliation (Sessions 108–109). As a pre-release accuracy pass, a full wiki-wide audit re-verified every `file.py:N-M` code citation against the current source and corrected 43 that had drifted as the code evolved; citations embedded in historical narrative were deliberately left as-of-their-time.

### Business value capture — Sessions 86–91 (2026-05-22)

A cross-cutting extension threads value measurement through the pipeline (`docs/planning/business-value-capture-plan.md`):

- **Added:** `ValueMeasurementPlan` and `BaselineSnapshot` schemas, plus business-case fields (`cost_of_inaction`, `implementation_cost_band`, `payback_months`, `value_drivers`) on `EstimatedValue` (Session 86).
- **Changed:** the intake interview now drives toward **five** required sections — a value measurement plan joins business problem, proposed solution, model solution, and estimated value. A `COMPLETE` intake must declare a baseline metric and an evaluation horizon (Session 87).
- **Added:** the Data Agent collects a `BaselineSnapshot` of the current-state metric when the intake supplies a value measurement plan, recording it on `DataReport.baseline_snapshot` (Session 88).
- **Changed:** the generated `analysis/01_business_understanding.qmd` (and `reports/intake_report.md`) now render a coherent business case — impact band, cost of inaction, implementation cost, payback, value drivers, assumptions, decision rights (Session 89).
- **Changed:** the generated `analysis/06_implementation_plan.qmd` now carries a structured Production Measurement Plan — baseline, counterfactual design, attribution method, evaluation horizon, logging requirements, review cadence, success criteria, decision rights — replacing the previous placeholder TODO (Session 90).
- **Changed:** the wiki, the architecture plan, and the worked examples describe the extended value capture end-to-end (Session 91).

---

## [0.1.0] - 2026-05-12

First versioned release. The `v0.1.0` git tag was created in Session 74 on commit `b4c0dbb`; this audience-facing wiki section was re-dated to the tag-creation date in Session 80 to mirror the root `CHANGELOG.md` transition formalized in Session 78. The release was previously framed as "Pilot Ready" on 2026-04-15 (the date Phases 1-6 reached test-green + CI-green status); the 2026-05-12 date now reflects when the formal release tag was cut. All entries below — from Phase 1 schemas through the post-Phase-6 wiki expansion — constitute the v0.1.0 release content.

Phases 1 through 6 complete. 422 tests at 97.18% coverage. Both GitLab and GitHub adapters pass structural + integration tests. CI green across lint, typecheck, test, and decoupling jobs.

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
- **Added:** Six accept tokens for terminal review (`REVIEW_ACCEPT_TOKENS` in `src/model_project_constructor/agents/intake/nodes.py`).
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
| 2026-04-18 | `7d90885` | 94% → 95% | Session 47 |

Current floor: **95%**, enforced by `--cov-fail-under=95` in CI.

Pilot-readiness fixes (Session 17, `17f661d` + `d62efc2` + `b8d8d7e`):

- **Fixed:** 62 ruff errors across `src/`, `tests/`, `packages/` (all pre-existing).
- **Fixed:** 3 CI failures — missing `mypy` deps, decoupling job's missing `--no-cov`, ANSI color codes in CLI help assertions (resolved via `click.unstyle`).

---

## Versioning policy

The project is currently pre-1.0. Schema versioning is intentionally minimal — every payload is `1.0.0` and there is no migration machinery yet. The registry contract (`REGISTRY` in `src/model_project_constructor/schemas/registry.py`) keys on `(payload_type, schema_version)`, so multiple versions *can* coexist once a second is introduced:

- **Minor bump** (1.0.0 → 1.1.0, backwards-compatible additions): register the new class under its new version key; keep 1.0.0.
- **Major bump** (1.0.0 → 2.0.0): register v2 and keep v1 for at least two major releases; add whatever migration the change needs at that point. There is no `schemas/migrations/` package today.

The envelope version (`HandoffEnvelope.envelope_version`) is versioned independently from payload schemas so the transport can evolve without forcing every payload to rev.

---

## See also

- [Getting Started](Getting-Started) — current install and first-run steps
- [Architecture Decisions](Architecture-Decisions) — the design tradeoffs behind each phase
- [Contributing](Contributing) — commit convention, review process, and quality gates
- `BACKLOG.md` (in the repository) — open work items not yet started
- `CHANGELOG.md` (in the repository) — commit-level changes seen by repo contributors (this wiki page is the audience-facing summary)
