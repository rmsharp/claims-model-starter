# Pilot Readiness Audit

**Date:** 2026-04-15
**Session:** 17
**Scope:** All Phase 1–6 deliverables vs. `architecture-plan.md` §14 acceptance criteria + `initial_purpose.txt` requirements
**Baseline:** 422 tests, 97.18% coverage, mypy strict clean (48 files), master clean

---

## Summary

| Phase | Criteria | Pass | Fail | Notes |
|-------|----------|------|------|-------|
| 1 — Repo Skeleton + Schemas | 5 | 5 | 0 | |
| 2 — Data Agent | 10 | 10 | 0 | |
| 3 — Intake Agent + Web UI | 9 | 9 | 0 | |
| 4 — Website Agent | 11 | 11 | 0 | |
| 5 — Orchestrator | 6 | 5 | 1 | `tests/e2e/` not created (tests live in `tests/orchestrator/`) |
| 6 — Production Hardening | 5 | 4 | 1 | CI fails on push (62 pre-existing ruff errors) |
| **Total** | **46** | **44** | **2** | |

**Verdict: NOT YET PILOT-READY.** Two issues must be resolved: CI must pass on push, and the `tests/e2e/` gap should be documented or addressed.

---

## Phase 1: Repo Skeleton + Schemas

### 1.1 `pyproject.toml` with dependencies and package layout — PASS

- Package: `model-project-constructor` v0.1.0
- Layout: `src/model_project_constructor` with workspace member `packages/*`
- Dependencies: `pydantic>=2.6,<3`, `pyyaml>=6`, `model-project-constructor-data-agent`
- Extras: `agents`, `ui`, `dev`
- Coverage floor: 94%

### 1.2 All Pydantic models from §5 present in `schemas/v1/` — PASS

All 13 models present:
- `intake.py`: IntakeReport, ModelSolution, EstimatedValue, GovernanceMetadata
- `repo.py`: RepoTarget, RepoProjectResult, GovernanceManifest
- `data.py`: Re-exports from standalone data-agent (DataRequest, DataReport, DataGranularity, QualityCheck, PrimaryQuery, Datasheet)
- `common.py`: CycleTime, RiskTier, ModelType, StrictBase, SCHEMA_VERSION

### 1.3 Registry with `load_payload()` — PASS

- `REGISTRY`: 5 entries keyed by `(payload_type, schema_version)`
- `load_payload(envelope)`: validates and returns typed model
- `UnknownPayloadError` for unregistered types/versions

### 1.4 `HandoffEnvelope` defined — PASS

- Fields: `envelope_version`, `run_id`, `source_agent`, `target_agent`, `payload_type`, `payload_schema_version`, `payload`, `created_at`, `correlation_id`
- `target_agent` excludes "orchestrator" (enforced by Literal constraint)
- `extra="forbid"` on `ConfigDict`

### 1.5 Schema tests: required/optional/literal/round-trip — PASS

- 88 tests in `tests/schemas/` (4 test files + fixtures.py)
- Coverage: required field validation, optional defaults, Literal enum rejection, JSON round-trip, extra field rejection

**§14 verification commands:**

| Command | Result |
|---------|--------|
| `uv run pytest tests/schemas/ -v` | 88 passed |
| `from model_project_constructor.schemas.v1 import IntakeReport` | OK |
| `REGISTRY` count | 5 keys: IntakeReport, DataRequest, DataReport, RepoTarget, RepoProjectResult |

---

## Phase 2: Data Agent

### 2A.1 LangGraph flow in agents/data/ — PASS

- `packages/data-agent/.../graph.py`: StateGraph with 7 nodes (GENERATE_QUERIES, RETRY_ONCE, FAIL_EXECUTION, GENERATE_QC, EXECUTE_QC, SUMMARIZE, DATASHEET)
- Conditional routing per §10.2

### 2A.2 `DataAgent.run(DataRequest) -> DataReport` end-to-end — PASS

- Three status paths: COMPLETE, INCOMPLETE_REQUEST, EXECUTION_FAILED
- Tests cover happy path, retry loop, DB-down, incomplete requests

### 2A.3 SQL parse validation uses `sqlparse` — PASS

- `sql_validation.py` imports `sqlparse`; `pyproject.toml` declares `sqlparse>=0.5`

### 2A.4 Datasheet generation — PASS

- `make_datasheet()` node in `nodes.py` calls `llm.generate_datasheet()` per query
- CLI test exercises with SQLite fixture

### 2A.5 Decoupling test passes — PASS

- `tests/test_data_agent_decoupling.py`: 2 tests pass
- AST-walks all data-agent modules; zero references to IntakeReport

### 2B.1 Standalone `pyproject.toml` — PASS

- `packages/data-agent/pyproject.toml` with independent dependencies

### 2B.2 Typer CLI — PASS

- Entry point: `model-data-agent` → `cli:app`
- `__main__.py` supports `python -m` invocation

### 2B.3 USAGE.md with examples — PASS

- 227 lines; three usage modes: CLI, Python script, Python notebook
- Public API reference section

### 2B.4 Standalone install — PASS

- No circular dependencies; decoupling test proves independence

**§14 verification commands:**

| Command | Result |
|---------|--------|
| `uv run pytest tests/agents/data/ -v` | 12 passed |
| `uv run pytest tests/test_data_agent_decoupling.py` | 2 passed |

---

## Phase 3: Intake Agent + Web UI

### 3A.1 LangGraph flow in agents/intake/ — PASS

- `graph.py`: `build_intake_graph()` with 8 nodes (plan_next_question, ask_user, evaluate_interview, draft_report, classify_governance, await_review, revise, finalize)
- Uses MemorySaver (tests) or SqliteSaver (Web UI)

### 3A.2 CLI with synthetic stakeholder responses — PASS

- `cli.py`: `--fixture tests/fixtures/subrogation.yaml`
- `FixtureLLMClient` replays deterministic Q&A from YAML

### 3A.3 Valid IntakeReport with GovernanceMetadata — PASS

- `build_intake_report()` in `nodes.py` constructs full IntakeReport
- GovernanceMetadata includes: cycle_time, risk_tier, rationales, regulatory_frameworks, affects_consumers, uses_protected_attributes
- 5 test fixtures produce valid reports

### 3A.4 10-question cap + 3-revision cap — PASS

- `state.py`: `MAX_QUESTIONS=10`, `MAX_REVISIONS=3`
- Routing enforced in `nodes.py`
- Tests: `test_question_cap_produces_draft_incomplete`, `test_revision_cap_produces_draft_incomplete`

### 3A.5 Governance classifications for 3 scenarios — PASS

| Fixture | cycle_time | risk_tier |
|---------|-----------|-----------|
| Subrogation | tactical | tier_3_moderate |
| Fraud Triage | continuous | tier_1_critical |
| Pricing Optimization | strategic | tier_2_high |

### 3B.1 FastAPI with SSE endpoint — PASS

- `app.py`: `GET /sessions/{session_id}/events` → EventSourceResponse
- `test_sse.py` verifies SSE emits "snapshot" events

### 3B.2 HTMX frontend — PASS

- `templates.py`: renders question/answer/review pages with HTMX attributes

### 3B.3 SQLite session persistence — PASS

- `runner.py`: `IntakeSessionStore` with `SqliteSaver`

### 3B.4 Resume by session_id across restart — PASS

- `test_sqlite_resume.py`: creates app1 → answers Q1-Q2 → tears down → creates app2 with same DB → resumes at Q3 → completes

**§14 verification commands:**

| Command | Result |
|---------|--------|
| `uv run pytest tests/agents/intake/ -v` | 56 passed |
| `uv run pytest tests/ui/intake/ -v` | 22 passed |
| Intake CLI `--help` | Shows `--fixture`, `--output`, `--anthropic` options |

---

## Phase 4: Website Agent

### 4A.1 LangGraph flow — PASS

- `graph.py`: 7-node graph (create_project, scaffold_base, scaffold_governance, initial_commits, retry_backoff, build_result, end)
- Conditional routing for retry logic

### 4A.2 End-to-end with seeded inputs — PASS

- `WebsiteAgent.run(intake, data, repo_target)` with `FakeRepoClient` or real adapters
- `test_agent.py` exercises happy path

### 4A.3 All file types generated — PASS

- 7 `.qmd` files (business_understanding, data, eda, feature_engineering, initial_models, implementation_plan, extensions)
- 5 `src/` modules with function stubs
- Test files generated
- Verified in `test_templates.py::TestBuildBaseFiles::test_returns_expected_file_set`

### 4A.4 RepoProjectResult returned — PASS

- `build_repo_project_result()` returns result with `project_url`, `initial_commit_sha`, `files_created`, `status`

### 4B.1 Governance proportional to risk_tier + cycle_time — PASS

- Tier 1: all artifacts (lcp_integration, audit_log, three_pillar_validation, etc.)
- Tier 2: impact_assessment, regulatory_mapping, monitoring (no lcp/audit)
- Tier 3: model_card, change_log, CI files (always-emit only)
- `affects_consumers=True` → eu_ai_act_compliance
- `uses_protected_attributes=True` → fairness_audit + test_fairness

### 4B.2 Three tier fixtures — PASS

- `tier1_intake.json`, `tier2_intake.json`, `subrogation_intake.json` (tier 3)
- Test classes: `TestTier1Critical`, `TestTier2High`, `TestTier3Moderate`

### 4B.3 GovernanceManifest completeness — PASS

- `artifacts_created` filtered by `is_governance_artifact()` classifier
- `regulatory_mapping` populated per frameworks
- `model_registry_entry` with risk_tier, cycle_time, etc.

### 4B.4 Regulatory mapping — PASS

- Framework → artifact bindings (SR_11_7, NAIC_AIS, EU_AI_ACT_ART_9, ASOP_56)

### GitHub/GitLab Abstraction (Phases A-D)

### 4D.1 RepoClient protocol + dual adapters — PASS

- `protocol.py`: `RepoClient` Protocol with `create_project()`, `commit_files()`
- `PythonGitLabAdapter` (python-gitlab), `PyGithubAdapter` (PyGithub), `FakeRepoClient`

### 4D.2 CI platform branching — PASS

- `.gitlab-ci.yml` for gitlab; `.github/workflows/ci.yml` for github
- Parametrized tests in `test_governance.py`

### 4D.3 CLI `--host` flag — PASS

- `--host gitlab` → PythonGitLabAdapter; `--host github` → PyGithubAdapter
- `--ci-platform` overrides independently
- Invalid host → exit code 2

**§14 verification commands:**

| Command | Result |
|---------|--------|
| `uv run pytest tests/agents/website/ -v` | 122 passed |
| `uv run pytest tests/agents/website/test_governance.py -v` | 18 passed |

---

## Phase 5: Orchestrator

### 5.1 `pipeline.py` with `run_pipeline` — PASS

- `run_pipeline(config, *, intake_runner, data_runner, website_runner, store=None)`
- Sequential: Intake → Data → Website with halt on non-COMPLETE
- Returns `PipelineResult` with status ∈ {COMPLETE, FAILED_AT_INTAKE, FAILED_AT_DATA, FAILED_AT_WEBSITE}

### 5.2 `adapters.py` with `intake_report_to_data_request()` — PASS

- Infers `DataGranularity` from `model_type`
- Builds `DataRequest` from IntakeReport fields

### 5.3 `checkpoints.py` for envelope persistence — PASS

- `CheckpointStore`: saves `HandoffEnvelope` as `<run_id>/<payload_type>.json`
- Terminal result: `save_result()` → `.result.json`

### 5.4 End-to-end test — PASS (functional), FAIL (location)

- Happy-path tests exist in `tests/orchestrator/test_pipeline.py` with real `WebsiteAgent` + `FakeRepoClient`
- Both GitLab and GitHub CI paths tested
- **However: `tests/e2e/` directory does not exist.** §14 Phase 5 specifies `uv run pytest tests/e2e/ -v` as a verification command. The end-to-end tests were implemented in `tests/orchestrator/test_pipeline.py` instead.

### 5.5 Halt behavior for each `FAILED_AT_*` — PASS

- `FAILED_AT_INTAKE`: test verifies halt + no downstream calls
- `FAILED_AT_DATA`: test verifies halt + no website call
- `FAILED_AT_WEBSITE`: test verifies halt
- Guard tests: downstream agents not called on upstream failure

### 5.6 Checkpoint persistence verified — PASS

- `test_happy_path_persists_all_checkpoints`: verifies envelope files on disk
- `test_happy_path_terminal_result_file_is_valid_repo_project_result`: validates `.result.json`

**§14 verification commands:**

| Command | Result |
|---------|--------|
| `uv run pytest tests/orchestrator/ -v` | 99 passed |
| `uv run pytest tests/e2e/ -v` | **FAIL: directory does not exist** |

---

## Phase 6: Production Hardening

### 6.1 Structured logging with run_id + correlation_id — PASS

- `logging.py`: `make_logged_runner(runner, *, agent_name, run_id, correlation_id)`
- Events: `agent.start`, `agent.end`, `agent.error` with context dict
- Duration measured; status extracted from result
- `pipeline.py` does NOT import `logging.py` — observability is opt-in via runner composition

### 6.2 Metrics: counts, status, per-agent latency — PASS

- `metrics.py`: `MetricsRegistry` (thread-safe) with `run_count`, `status_counts`, `agent_latency`
- `make_measured_runner()` wraps runners; records latency even on exception
- `.snapshot()` returns immutable `MetricsSnapshot`
- `pipeline.py` does NOT import `metrics.py`

### 6.3 Configuration via environment — PASS

- `config.py`: `OrchestratorSettings.from_env()` with validation
- Secrets: `GITLAB_TOKEN`, `GITHUB_TOKEN`, `ANTHROPIC_API_KEY` — all via env
- Guard methods: `require_host_token()`, `require_anthropic_api_key()`
- `.env.example` templates all 8 configurable variables
- No hardcoded credentials found

### 6.4 Documentation — PASS

- `README.md`: updated with Phase 5/6 sections, test counts, orchestrator diagram
- `OPERATIONS.md`: env-var matrix, checkpoint layout, resume procedure, observability integration
- `TROUBLESHOOTING.md`: diagnostic walkthroughs per `FAILED_AT_*` path with pasteable code

### 6.5 CI pipeline: lint + tests + typecheck + decoupling — FAIL

- `.github/workflows/ci.yml` exists with 4 jobs: Lint (ruff), Type check (mypy), Tests (pytest), Data Agent decoupling
- **CI failed on first push** (run ID 24491174142, status: failure)
- **Root cause:** Lint job runs `uv run ruff check src/ tests/ packages/` which catches **62 pre-existing ruff errors** across 31 files
- Error breakdown: I001 (17 import-order), E501 (11 line-length), UP017 (8 datetime.UTC), UP045 (6), F401 (5 unused-import), B009 (4), F841 (2 unused-var), B008 (2 typer.Option), UP035 (2), SIM102 (2), SIM103 (1), SIM108 (1), F541 (1)
- **43 of 62 are auto-fixable** with `uv run ruff check --fix`
- These errors predate Phases 5-6; they exist in `ui/intake/`, `agents/intake/`, `agents/website/`, `packages/data-agent/`, `schemas/`, and test files

**§14 verification commands:**

| Command | Result |
|---------|--------|
| `uv run mypy src/` | Success: 48 files clean |
| CI pipeline green on push | **FAIL: lint job failed** |

---

## Original Requirements Alignment (`initial_purpose.txt`)

| Requirement | Status | Evidence |
|------------|--------|----------|
| Guided discussion at go/modelintake | Implemented | FastAPI Web UI with SSE (`ui/intake/app.py`) |
| Agent asks questions to get: business problem, proposed solution, model solution, estimated value | Implemented | IntakeReport schema with all 4 sections (`schemas/v1/intake.py`) |
| Agent writes report and hands off to data agent | Implemented | HandoffEnvelope + registry + orchestrator pipeline |
| Data agent creates queries + quality checks + confirms expectations | Implemented | DataAgent with PrimaryQuery, QualityCheck, Datasheet generation |
| Website agent creates draft sections | Implemented | 7 `.qmd` files + `src/` modules generated by `templates.py` |
| Delivered as GitLab project | Implemented | PythonGitLabAdapter + PyGithubAdapter (dual-host support exceeds original requirement) |
| Contains website + results from Steps 2-4 + extension ideas | Implemented | `build_base_files()` includes `reports/intake_report.json`, `reports/data_report.json`, `extensions.qmd` |
| One question at a time, max 10 | Implemented | `MAX_QUESTIONS=10` in `state.py`, enforced in routing |
| Data agent reusable as standalone query tool | Implemented | `packages/data-agent/` with independent `pyproject.toml`, CLI, USAGE.md |
| Expert data scientist / business analyst persona | Implemented | System prompt in `anthropic_client.py`, fixture-driven testing |

---

## Blocking Issues

### 1. CI lint failure (BLOCKING)

**Severity:** Blocks pilot. §14 Phase 6 requires "CI pipeline green on a PR."

**Fix:** Run `uv run ruff check --fix src/ tests/ packages/` to auto-fix 43 errors. Manually resolve remaining 19 (mostly E501 line-length and B008 typer.Option suppressions). Commit and push.

**Estimated scope:** 31 files across all packages. Zero behavioral changes — all fixes are style-only.

### 2. `tests/e2e/` directory gap (NON-BLOCKING)

**Severity:** Low. The end-to-end tests exist in `tests/orchestrator/test_pipeline.py` and cover the same criteria. The `tests/e2e/` path in §14 Phase 5 was aspirational — the implementation chose a different (equally valid) location.

**Fix:** Either create `tests/e2e/` as a symlink/re-export, or document the deviation in the plan. No functional gap.

---

## Recommendation

Fix the 62 ruff errors (priority 1), push, confirm CI passes, then declare pilot-ready.
