# Changelog

All notable changes to this project are documented here.
Format loosely follows [Keep a Changelog](https://keepachangelog.com/).

When completing work, remove the item from `BACKLOG.md` and add an entry here.

This file is the **authoritative, contributor-facing record** of completed work. The wiki page `Changelog` (under `claims-model-starter/wiki`, mirrored at `docs/wiki/claims-model-starter/Changelog.md`) is an audience-facing summary whose tone and level of detail may evolve over time; this file stays stable and complete. When the two disagree, this file is canonical.

Dates are commit dates on `master`. Commit hashes are short-form as produced by `git log --oneline`. Session numbers refer to entries in `SESSION_NOTES.md`.

---

## [Unreleased]

### 2026-04-17 — `MPC_NAMESPACE` URL-prefix validator + docs (Session 28)

- **Added:** `validate_namespace(raw: str) -> str` module-level helper in `src/model_project_constructor/orchestrator/config.py`. Raises `ConfigError` when `MPC_NAMESPACE` starts with `http://` or `https://` (case-insensitive, whitespace-trimmed) with a message that names the received value and the expected path form. Closes a Session 22 operator-experience finding: before this, a URL-form namespace surfaced as a generic `group lookup failed: 404` from the GitLab adapter; now it fails at `[2/5] Building pipeline config...` in `scripts/run_pipeline.py` before any agent runs.
- **Added:** `OrchestratorSettings.namespace: str | None` field, populated from `MPC_NAMESPACE` and validated via `validate_namespace()` in `from_env()`. `None` when unset or whitespace-only. The pipeline script still applies host-specific defaults (`my-org` for GitHub, `data-science/model-drafts` for GitLab); the field lets future refactors thread the value through settings instead of re-reading `os.environ`.
- **Changed:** `scripts/run_pipeline.py` `build_repo_target` now calls `validate_namespace(os.environ.get("MPC_NAMESPACE", <default>))` so the error surfaces in fake mode as well as live mode — fail-fast for any mis-set namespace, not just ones that reach the adapter.
- **Added:** 13 new tests in `tests/orchestrator/test_config.py` (+13 total; 427 → 440). `TestValidateNamespace` direct-function tests (4 group-path acceptances + 4 URL-prefix rejections including mixed-case `HTTPS://` and leading/trailing whitespace). `TestFromEnvDefaults` gains `test_namespace_group_path`, `test_namespace_nested_group_path`, `test_namespace_empty_string_treated_as_unset`, and confirms `namespace is None` on empty env. `TestFromEnvValidation` gains `test_rejects_namespace_with_https_prefix` and `test_rejects_namespace_with_http_prefix`.
- **Changed:** Docs — `.env.example` now carries a `#MPC_NAMESPACE=rmsharp-modelpilot` template line with an inline comment explaining the path-not-URL invariant; `OPERATIONS.md` §1 env-var table gains a `MPC_NAMESPACE` row; `docs/tutorial.md` §5c expands the `MPC_NAMESPACE` section with the path-not-URL guidance + a worked example of the `ConfigError` message the validator raises.
- **Verified:** pytest 440/440 (coverage 97.25%), `uv run ruff check src/ tests/ packages/ scripts/` clean, `uv run mypy src/` clean. Sanity checks: `MPC_NAMESPACE=https://gitlab.com/rmsharp-modelpilot scripts/run_pipeline.py` now raises `ConfigError` at `[2/5]` with the clear message; `MPC_NAMESPACE=rmsharp-modelpilot scripts/run_pipeline.py` still produces `Status: COMPLETE` in fake mode.

### 2026-04-17 — Scope B-2 follow-up: `MAX_QUESTIONS` raised to 20, happy path reaches `COMPLETE` (Session 27)

- **Changed:** `MAX_QUESTIONS` in `src/model_project_constructor/agents/intake/state.py:57` raised from 10 to 20. Session 26's `run_b2_live` against `subrogation_b2.yaml` (10 qa_pairs) produced a rich Claude-drafted report but hit the cap before `believe_enough_info` flipped, forcing `DRAFT_INCOMPLETE` via `nodes.py:129-134`'s `questions_cap_reached` auto-append. Plan §7.2.3 criterion #1 (happy path → `COMPLETE`) therefore required both a higher cap AND a fuller fixture. All cap consumers (`agent.py:29,78`, `nodes.py:24,81,130`) import the constant — the single-line bump is sufficient.
- **Changed:** `tests/fixtures/subrogation_b2.yaml` extended from 10 to 15 qa_pairs. Pre-answers the three gaps Claude flagged in `run_b2_live`: **latency SLA** (250 ms p95 at intake completion; not real-time at FNOL), **average recovery per successful subrogation** (~$7,500 mean / $4,200 median; $30M/yr comes from ~4,000 recoveries), and **fairness / bias plan** (pre-launch disparate-impact audit + quarterly SR 11-7 fairness review; no protected attributes, tenure included as feature). Two padding entries cover retraining cadence (quarterly + PSI/AUC triggers) and incident response (feature-flag fallback + model-incident review). `draft_after` bumped to 15 for documentation consistency (no-op in `--llm both`).
- **Changed:** `tests/fixtures/intake_question_cap.yaml` expanded from 11 to 21 qa_pairs so `FixtureLLMClient` supplies `MAX_QUESTIONS+1` answers — the test's purpose (verify the hard cap stops the interview) requires more answers than the cap. Entry #21 is labeled "should never be asked" to document the invariant.
- **Changed:** `tests/ui/intake/test_runner.py:test_caps_constants_exposed` now references `MAX_QUESTIONS` + `MAX_REVISIONS` symbolically instead of the literal `{"max_questions": 10, ...}`. Future cap changes won't need a test edit.
- **Changed:** Doc references to the literal "10" updated — `README.md:101`, `OPERATIONS.md` §4.4.2, `docs/wiki/claims-model-starter/Intake-Interview-Design.md:63,220`, `docs/wiki/claims-model-starter/Worked-Examples.md:215`. Historical entries in `CHANGELOG.md` / wiki `Changelog.md` / planning docs kept as-is (they describe the state at the time of the change).
- **Verified:** live `run_b2_complete` (`--live --host gitlab --llm both --model claude-opus-4-7 --intake-fixture tests/fixtures/subrogation_b2.yaml`) produced `Status: COMPLETE` at `https://gitlab.com/rmsharp-modelpilot/subrogation-pilot-v3`, with `questions_asked=10`, `missing_fields=[]`, `tier_3_moderate` governance, `target_variable=subrogation_recovery_success`. End-to-end latencies: intake 63s, data 696s, website 5s. Claude flipped `believe_enough_info=true` exactly at turn 10 after receiving the pre-answers. Pytest 427/427 (coverage 97.24%), ruff clean on CI scope, mypy clean on `src/`.

### 2026-04-16 — Scope B-2: scripted-answers intake with real Anthropic (Session 26)

- **Added:** `scripts/run_pipeline.py` `--llm` flag gains a third value `both`, which drives `IntakeAgent.run_scripted(...)` with real Anthropic-generated questions + fixture-supplied answers + a real Anthropic data agent. New `--intake-fixture PATH` flag (required when `--llm=both`, ignored otherwise). `--model` now applies to BOTH intake and data agents (single flag, shared value across stages). New `build_intake_runner` helper mirrors `build_data_runner`'s shape.
- **Added:** Inline `_draft_incomplete_from_exception` adapter in `scripts/run_pipeline.py` (per scope-b-plan §8.4 (a)). Converts exhausted-script `RuntimeError`, rate-limit / parse errors, and pydantic validation failures into a typed `IntakeReport(status="DRAFT_INCOMPLETE")` so the orchestrator halts with `FAILED_AT_INTAKE` instead of crashing. Reason code is `exception_class_name`; full message goes into `missing_fields[0]`.
- **Added:** `tests/scripts/test_run_pipeline_adapter.py` (5 tests; +5 total). Covers the adapter's happy path (`RuntimeError` → `DRAFT_INCOMPLETE`), arbitrary-exception path (simulated rate-limit), the closure's `run_scripted` error path via monkeypatched `IntakeAgent`, `--llm none` fixture fallback, and the fail-fast `SystemExit` when `--llm both` is passed without `--intake-fixture`. Adapter is loaded via `importlib.util` since `scripts/` is not a package.
- **Added:** `tests/fixtures/_b2_failmode.yaml` — a deliberately under-specified fixture (1 `qa_pairs` entry + `draft_after: 99`) that forces `IntakeAgent.run_scripted` to raise the exhausted-answers `RuntimeError`. Consumed by the B2 failure-injection live run.
- **Added:** `OPERATIONS.md` §4.4 extended with the `--llm both` recipe (happy path + failure-injection). `docs/tutorial.md` §6 extended with a `--llm both --intake-fixture` subsection, cost delta vs B1 (~$0.15-0.75/run), and the `FAILED_AT_INTAKE` behavior contract.
- **Verified:** pre-flight (pytest 427/427 with +5 adapter tests, ruff on CI scope, mypy) stays green; the `--llm none` (Scope A) and `--llm data` (Scope B-1) invocations continue to produce their Scope-A / Scope-B-1 checkpoint envelopes (regression check). Plan: `docs/planning/scope-b-plan.md` §7.2 (Phase B2). Scope B-3 (Web UI bridge) remains optional and deferred.

### 2026-04-16 — CI ruff coverage extended to `scripts/` (Session 25)

- **Changed:** `.github/workflows/ci.yml` lint job now runs `uv run ruff check src/ tests/ packages/ scripts/` (previously `src/ tests/ packages/`). Closes a CI gap documented in Session 22: `scripts/` was outside CI's ruff scope, so 10 pre-existing errors (6 × `E402`, 4 × `F541`) never blocked merges.
- **Fixed:** `scripts/run_pipeline.py` — 6 × `E402` ("module level import not at top of file") resolved with per-line `# noqa: E402` on the imports that follow `sys.path.insert`. Kept the `sys.path` preamble intact so the module docstring's claim that the script runs "whether invoked via `uv run python scripts/run_pipeline.py` or directly" stays true. 4 × `F541` ("f-string without any placeholders") auto-fixed by `ruff check --fix`; the affected `print(f"...")` calls had no placeholders and are now plain `print("...")`.
- **Verified:** `uv run ruff check src/ tests/ packages/ scripts/` clean; `uv run python scripts/run_pipeline.py --help` renders; full fake-mode pipeline run (`--run-id run_s25_scripts_ruff`) completes with status `COMPLETE`; pytest 422/422 green.

### 2026-04-16 — Scope B-1: real Anthropic data agent wired into `run_pipeline` (Session 24)

- **Added:** `scripts/run_pipeline.py` now accepts `--llm {none,data}` (default `none`), `--model ID` (default `claude-opus-4-7`), and `--db-url URL` (default `None`). A new `build_data_runner` helper returns either a fixture-serving closure (`--llm none`, unchanged Scope A behavior) or `DataAgent(AnthropicLLMClient(model=...), db=...).run` (`--llm data`). The intake stage stays fixture-driven at this phase — Scope B-2 wires the real intake path.
- **Added:** `OPERATIONS.md` §4.4 documents the Scope B-1 invocation with a model-selection table and a checkpoint-inspection snippet for verifying the data side actually called Claude. `docs/tutorial.md` §6 "Real LLM-backed run" adds the same recipe with model tradeoffs and the optional `--db-url` path; the previous §6 becomes §7.
- **Verified:** pre-flight (pytest 422/422, ruff on CI scope, mypy) stays green; the live `run_b1_live` invocation produces `COMPLETE` against a real GitLab project with Claude-generated SQL distinct from the fixture. Plan: `docs/planning/scope-b-plan.md` §7.1 (Phase B1). Scope B-2 (scripted-answers intake) and optional Scope B-3 (Web UI bridge) remain open.
- **Deviation from plan:** §8.2 recommended `claude-sonnet-4-6`; user chose `claude-opus-4-7` for the first real run to remove "was it the model?" as a confounding variable if output quality is poor. `--model` flag added to the B1 surface (not in original §8.2); default is opus.

### 2026-04-16 — First live end-to-end smoke test (Session 22, Scope A)

- **Fixed:** `scripts/run_pipeline.py:119` passed `url=` to `PythonGitLabAdapter(...)` but the constructor's keyword-only parameter is `host_url=`. `--live --host gitlab` had never successfully run — it would have raised `TypeError: __init__() got an unexpected keyword argument 'url'` on the first keystroke. Phase 4B/5 tests only exercise the adapter's import + protocol conformance, not the script's wiring. Two-character fix: `url=host_url` → `host_url=host_url`.
- **Verified:** after the fix, `uv run python scripts/run_pipeline.py --live --host gitlab --run-id run_live_002` created a real project at `https://gitlab.com/rmsharp-modelpilot/subrogation-pilot` (project ID 81385820, initial commit `3dec542`). Website stage latency: 3,501 ms live vs ~4 ms fake-mode (~875× expected network overhead). All 38 files present, all 10 tier-3-moderate governance artifacts created, regulatory mapping correct (SR_11_7 + NAIC_AIS).
- **Findings (filed in `BACKLOG.md`, unfixed in this session):**
  - `MPC_NAMESPACE` takes a group *path* (`rmsharp-modelpilot`), not a URL (`https://gitlab.com/rmsharp-modelpilot`). `.env.example`, `OPERATIONS.md` §1, and `docs/tutorial.md` §5 all omit this constraint. The GitLab adapter returns a generic `"group lookup failed: 404"` instead of a clearer `"MPC_NAMESPACE must be a group path, not a URL"`.
  - `scripts/` is not ruff-checked in CI (`.github/workflows/ci.yml` lint job scans `src/ tests/ packages/` only). Running ruff locally surfaces 10 `E402` errors in `scripts/run_pipeline.py` — the `sys.path.insert` pattern needs `# noqa: E402` or a refactor.
  - `packages/` is not mypy-checked in CI (typecheck job runs `mypy src/` only) even though `[tool.mypy] packages = [...]` in `pyproject.toml` declares both `model_project_constructor` and `model_project_constructor_data_agent`. Running mypy with the declared packages surfaces 13 errors, mostly in `packages/data-agent/.../anthropic_client.py:218` — Anthropic SDK's content-block union has grown ~8 variants since the code was written, and `block.text` no longer narrows without a type guard. Latent bit-rot.
  - `docs/tutorial.md` §5c says `MPC_HOST_URL="https://github.mycompany.com/api/v3"` works for GitHub Enterprise, but `scripts/run_pipeline.py:109-113` constructs `PyGithubAdapter(token=token)` with no URL argument — GHE users silently hit public `api.github.com`. (Not live-tested in Session 22; confirmed by code reading.)
  - `docs/tutorial.md` §5 and `OPERATIONS.md` §4.2/4.3 document two different live-run commands. The OPERATIONS recipe uses `python -m model_project_constructor.agents.website --intake ... --host ... --private-token ...` — this flow should be reconciled with the script path or marked deprecated.

### 2026-04-16 — Gotcha cleanup (Session 21)

- **Changed:** `CHANGELOG.md` refreshed from Session-0-only stub to full authoritative history covering Phases 1–6, Phases A–D, pilot readiness, tutorial, wiki expansion, and license change.
- **Changed:** `BACKLOG.md` "Up Next" items "Pilot readiness audit" and "Ruff cleanup sweep" removed — both completed in Session 17 and now recorded here.
- **Changed:** `SESSION_NOTES.md` duplicate "What Session 18 Did" block and duplicate Session 17 handoff-evaluation block collapsed.

### 2026-04-16 — Wiki expansion (Sessions 19, 20A, 20B)

- **Added:** 14 initial wiki pages for `claims-model-starter` (Session 19) — Home, Getting Started, Pipeline Overview, Generated Project Structure, Governance Framework, Development Workflow, Data Guide, Agent Reference, Monitoring and Operations, Software Bill of Materials, Architecture Decisions, Glossary, Content Recommendations, plus `_Sidebar` navigation. Commit: `0acdd37`.
- **Added:** Intake Interview Design, Schema Reference, Security Considerations wiki pages (Session 20A). Covers the two intake system prompts verbatim, full Pydantic schema set field-by-field, outbound-network boundaries, and 9-item security review checklist. Commit: `8c96f24`.
- **Added:** Worked Examples, Extending the Pipeline, Changelog (wiki), Contributing wiki pages (Session 20B). Traces subrogation and renewal-profitability end-to-end; documents 4 extension surfaces; derives CI/test conventions from actual config. Commit: `9535665`.
- **Changed:** License updated from Proprietary to **MIT** across `LICENSE`, both `pyproject.toml` files, and the SBOM wiki page. Commit: `f2f2a70`.
- **Changed:** Session 19 close-out formalized with scored self-assessment and 20A/20B handoff plan. Commits: `06ef12f`, `da8d485`.

### 2026-04-16 — End-to-end pipeline script + tutorial (Session 18)

- **Added:** `scripts/run_pipeline.py` — 265-line driver running Intake → Data → Website end-to-end against fixture data with `FakeRepoClient`. `--live` flag switches to real GitLab / GitHub hosts. Tested against both `--host gitlab` and `--host github`. Commit: `4dc2f5d`.
- **Added:** `docs/tutorial.md` — six-step user tutorial (YAML fixture → IntakeReport JSON → pipeline run → checkpoint inspection → live host → programmatic API). Restructured during user testing to start with fixture creation. Commits: `4dc2f5d`, `1613d60`.
- **Fixed:** tutorial install command was missing `--extra ui`. Commit: `883935a`.
- **Changed:** replaced conflated "likelihood" with "probability" in fixtures, tests, and `initial_purpose.txt` where referring to `P(event)` (5 files). Commit: `1613d60`.
- **Added:** BACKLOG items for data-source discovery (intake + data agents), statistical terminology glossary, `render_tutorial.sh`, tutorial copy-UX, SQLite connection warnings. Commits: `1f9c28a`, `9f3399c`.
- **Added:** `.orchestrator/`, `my_intake.yaml`, `my_intake_report.json` to `.gitignore`.
- **Docs:** session-18 close-out handoff notes. Commit: `d831414`.

---

## [0.1.0 — Pilot Ready] — 2026-04-15

Phases 1 through 6 complete. 422 tests at 97.18% coverage. Both GitLab and GitHub adapters pass structural + integration tests. CI green across lint, typecheck, test, and decoupling jobs.

### Pilot readiness audit (Session 17) — 2026-04-15

- **Added:** `docs/planning/pilot-readiness-audit.md` — all 46 `architecture-plan.md §14` acceptance criteria verified against the actual codebase. PILOT-READY declared. Commit: `b9c87c7`.
- **Fixed:** all 62 pre-existing ruff errors across `src/`, `tests/`, `packages/` (56 auto-fixable + 6 manual). Commit: `17f661d`.
- **Fixed:** 3 CI workflow failures — mypy typecheck missing `--extra ui`, decoupling job below coverage floor, CLI tests failing on ANSI color codes (resolved via `click.unstyle`). Commits: `d62efc2`, `b8d8d7e`.
- **Changed:** `BACKLOG.md` marks all 6 phases complete. Commit: `66b44c8`.

### Phase 6 — Production hardening (Session 16) — 2026-04-15

- **Added:** structured logging via `make_logged_runner` — binds `run_id` and `correlation_id` to every stage's log context; emits `agent.start` / `agent.end` / `agent.error` events.
- **Added:** in-memory metrics via `MetricsRegistry` + `make_measured_runner` — run counts, status distribution, per-agent latency; no external metrics backend required.
- **Added:** `OrchestratorSettings.from_env()` — env-var-driven configuration with `require_*` guards that fail fast on missing credentials; `.env.example` template.
- **Added:** `.github/workflows/ci.yml` — four-job CI pipeline (`lint`, `typecheck`, `test`, `decoupling`).
- **Added:** `OPERATIONS.md` production runbook and `TROUBLESHOOTING.md` diagnostics (one walkthrough per `FAILED_AT_*` path).
- **Added:** 54 new tests across 3 new test files.
- **Design:** zero new dependencies. Observability is opt-in via runner composition — `pipeline.py` has no imports from the new logging/metrics modules.
- **Changed:** coverage floor raised 93% → 94%. Commit: `c3943a8`.
- Feature commit: `2060d4a`.

### Phase 5 — Orchestrator (Session 15) — 2026-04-15

- **Added:** `src/model_project_constructor/orchestrator/` package — `pipeline.py` (sequential `run_pipeline` driver per §12), `adapters.py` (sole `IntakeReport ↔ DataRequest` bridge enforcing the §7 decoupling invariant), `checkpoints.py` (`CheckpointStore` with envelope save/load + `save_result` for terminal artifacts).
- **Added:** `PipelineStatus` literal — `COMPLETE` / `FAILED_AT_INTAKE` / `FAILED_AT_DATA` / `FAILED_AT_WEBSITE`. Partial state retained on halt so operators can inspect or resume.
- **Added:** 45 new tests under `tests/orchestrator/` — happy path for both `ci_platform="gitlab"` and `ci_platform="github"` with positive + negative CI-file assertions; halt behavior for each `FAILED_AT_*` path; downstream-agent-not-called guards; adapter inference rules; envelope round-trip; terminal-result filename isolation; run-directory isolation.
- Commit: `b94cb47`.

### Phases A–D — GitHub/GitLab abstraction (Sessions 10–14) — 2026-04-15

- **Phase A (Session 11) — Neutral rename:** `GitLabClient → RepoClient` protocol, `GitLabTarget → RepoTarget`, `GitLabProjectResult → RepoProjectResult`. Widened `project_id: int → str` to accommodate the GitHub `owner/repo` form. Commit: `8c00e1a`.
- **Phase B (Session 12) — GitHub Actions CI template:** `render_github_actions_ci` sibling to the GitLab CI renderer; `ci_platform` plumbed through website agent state and governance manifest. Commit: `9b2ab5e`.
- **Phase C (Session 13) — PyGithub adapter:** `PyGithubAdapter` sibling to `PythonGitLabAdapter`, both implementing the neutral `RepoClient` protocol. `PyGithub` added as dependency (LGPL-3.0; usage is pure API, no redistribution). Commit: `55745ed`.
- **Phase D (Session 14) — Host selection CLI:** website CLI `--host gitlab|github` flag; dual-adapter selection; README mentions GitHub alongside GitLab. Commits: `e9f0d10`, `9f20e95`.
- **Supporting:** abstraction plan document — `f44f8dc` (Session 10). Session close-out handoffs — `0f132e0`, `a869904`, `a7fa214`, `72ac527`, `c996c0d`.
- **Changed:** coverage floor raised 90% → 93%. Commit: `e91c9f2`.

### Phase 4B — Website Agent governance (Session 9) — 2026-04-14

- **Added:** governance artifact scaffolding proportional to `risk_tier` and `cycle_time` per architecture-plan §8. `is_governance_artifact` classifier is the single source of truth for which files are governance-tagged (derives manifest rather than storing in state).
- **Added:** `python-gitlab` adapter (`PythonGitLabAdapter`) implementing the original `GitLabClient` protocol (later renamed to `RepoClient` in Phase A).
- **Added:** retry / exponential backoff on repo operations.
- Commit: `f97b530`.
- Session close-out: `5a20eb8`.

### Phase 4A — Website Agent core (Session 8) — 2026-04-14

- **Added:** Website Agent LangGraph flow — `CREATE_PROJECT`, `SCAFFOLD_BASE`, `INITIAL_COMMITS` nodes.
- **Added:** initial model build scaffolding — `.qmd` files, `src/` module stubs, reasonable defaults clearly marked where human judgment is required.
- Commit: `9887286`.
- Session close-out: `c996c0d`.

### Phase 3B — Intake Agent web UI (Session 7) — 2026-04-14

- **Added:** FastAPI + SSE + HTMX frontend for interactive interview sessions.
- **Added:** SQLite session persistence and resume.
- **Added:** fixture statelessness preserved for testing (fixtures bypass DB).
- Commit: `1c1141a`.
- Session close-out: `41449a8`.

### Phase 3A — Intake Agent core (Session 6) — 2026-04-14

- **Added:** Intake Agent LangGraph flow — expert data-scientist / business-analyst / consultant persona for P&C claims domain.
- **Added:** one-question-at-a-time interview with `MAX_QUESTIONS=10` and `MAX_REVISIONS=3` budgets.
- **Added:** `IntakeReport` generation with `GovernanceMetadata` (risk tier, cycle time, model type) re-derived on every revision.
- **Added:** 6-token review-loop accept vocabulary in `nodes.py`.
- **Added:** fixture-driven CLI.
- Commit: `64b8a99`.
- Session close-out: `081cb20`.

### Phase 2B — Data Agent standalone package (Session 5) — 2026-04-14

- **Changed:** Data Agent refactored into standalone package `packages/data-agent/` with its own `pyproject.toml` — enables reuse as a query-writing tool for analyst teams per `initial_purpose.txt`. Commit: `4982332`.
- **Added:** `AnthropicLLMClient`, Typer CLI, Python API docs. Commit: `aca858a`.
- **Changed:** coverage floor raised 80% → 90%. Commit: `0b30014`.
- Session close-out: `0c0197e`.

### Phase 2A — Data Agent core (Session 4) — 2026-04-14

- **Added:** Data Agent LangGraph flow — query generation, quality checks, data expectation confirmation.
- **Added:** AST-walk decoupling test ensuring the Data Agent has no `intake` imports (enforces the §7 invariant that the only `IntakeReport ↔ DataRequest` bridge is the orchestrator adapter).
- **Added:** `sqlparse`-based SQL parse validation for generated queries.
- **Added:** `DataAgent.run(DataRequest) -> DataReport`.
- Commit: `e526332`.
- Session close-out: `5c73ed0` (also restored `pyproject` readme field, added `README.md`).
- Session 4 claim + `uv` bootstrap: `530bff9`.

### Phase 1 — Architecture plan and payload schemas (Sessions 2–3) — 2026-04-14

- **Added:** `docs/planning/architecture-plan.md` — full pipeline architecture with 14 phases of work planned (6 product phases + 4 abstraction phases + planning/hardening). Commit: `5bf0d8a`.
- **Added:** repo skeleton, v1 payload schemas (`IntakeReport`, `DataRequest`, `DataReport`, plus what later became `RepoTarget` / `RepoProjectResult`), `HandoffEnvelope` with versioning, `schemas/registry.py`. Commit: `f94e211`.

### Early architecture exploration — 2026-04-10

- **Added:** architecture-approaches document with pros/cons for 4 critical features (authored before the canonical architecture-plan). Commit: `4a9840c`.

---

## [0.0.1 — Project bootstrap] — 2026-04-10

Initial commit of methodology framework and empty project scaffolding. Commit: `ff0228e`.

### 2026-04-10 — Project setup (Session 0)

- **Added:** Iterative Session Methodology (v2.1) — `SESSION_RUNNER.md`, `SAFEGUARDS.md`, `SESSION_NOTES.md`, `methodology_dashboard.py`.
- **Added:** Task tracking files — `BACKLOG.md`, `CHANGELOG.md`, `ROADMAP.md`.
- **Added:** Framework reference docs in `docs/methodology/` (`ITERATIVE_METHODOLOGY.md`, `HOW_TO_USE.md`, 5 workstreams).
- **Added:** `CLAUDE.md` with session protocol, pipeline description, agent design principles, and worked examples from `initial_purpose.txt`.
- **Customized:** `SESSION_RUNNER.md` Phase 1 task-to-workstream mapping for project-specific work types (agent building, prompt engineering, schema definition, pipeline integration).
- **Populated:** `ROADMAP.md` with 5 milestones, pipeline overview table, and domain context.
- **Populated:** `BACKLOG.md` with granular tasks broken down by milestone (Architecture, Intake Agent, Data Agent, Website Agent, Integration).
- **Populated:** `SESSION_NOTES.md` with active task, key files, and gotchas for the first real session.
