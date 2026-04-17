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
  - [x] **B-2 follow-up: end-to-end `COMPLETE` with `--llm both`** — Session 27 raised `MAX_QUESTIONS` 10→20, expanded `subrogation_b2.yaml` to 15 qa_pairs (pre-answers for latency SLA, per-claim recovery $, fairness/bias plan), and expanded `intake_question_cap.yaml` to 21 qa_pairs so the cap-test fixture stays valid. Live `run_b2_complete` produced `Status: COMPLETE` at `subrogation-pilot-v3`. See `CHANGELOG.md`.
  - [ ] **B-3 (optional): Web UI bridge** — Per plan §7.3. `--resume-intake <session_id>` reads completed `IntakeReport` from the intake UI's SQLite store. Plan §8.3 recommends deferring unless user wants a production-shape demo; "Automated resume-from-checkpoint" item below may supersede.
- [x] **Clearer `MPC_NAMESPACE` validation and docs** (Session 22 finding) — Session 28 added `validate_namespace(raw)` in `orchestrator/config.py` (raises `ConfigError` on `http://`/`https://` prefix), wired it through `OrchestratorSettings.from_env()` + `scripts/run_pipeline.py:build_repo_target`, added 13 tests, and updated `.env.example`, `OPERATIONS.md` §1, and `docs/tutorial.md` §5c with the path-not-URL guidance + a worked error example. See `CHANGELOG.md`.
- [x] **CI typecheck coverage extension to `packages/`** (Session 22 finding) — Session 29 switched `.github/workflows/ci.yml` from `mypy src/` to bare `mypy` (picks up `[tool.mypy] packages = [...]` in `pyproject.toml`). Fixed all 13 pre-existing errors: `anthropic_client.py:218` (11 × `union-attr` → `isinstance(block, TextBlock)` guard + `LLMParseError` fallback), `nodes.py:142` (`arg-type` → explicit `Literal["PASSED", "FAILED"]` annotation), `sql_validation.py:26` (`no-untyped-call` on sqlparse → inline `type: ignore`). Added `test_call_claude_rejects_non_text_block` + swapped the test fake to real `anthropic.types.TextBlock`. 440 → 441 tests, coverage 97.25 → 97.26%. See `CHANGELOG.md`.
- [x] **Self-hosted GitHub URL override** (Session 22 finding) — Session 30 fixed `scripts/run_pipeline.py:273-278`. `PyGithubAdapter.__init__` already accepted `host_url=` (no adapter change needed); the bug was entirely in the pipeline script's call site, which passed `token=token` (wrong kwarg — adapter's is `private_token=`) and never read `MPC_HOST_URL`. This meant `--live --host github` had never worked — first invocation would have raised `TypeError`. Fix parallels Session 22's `url=` → `host_url=` GitLab fix. Added 3 new tests in `tests/scripts/test_run_pipeline_adapter.py` covering both GitHub paths (with `MPC_HOST_URL` set + unset) + a symmetric GitLab regression guard. 441 → 444 tests. See `CHANGELOG.md`. Closes the last of Session 22's three code-gap findings.
- [x] **Reconcile `OPERATIONS.md` §4.2/4.3 live-run recipes with `scripts/run_pipeline.py --live`** (Session 22 finding) — Session 31 re-audited both recipes and reconciled them with README.md's canonical pattern. Decision: **keep, don't deprecate** — README + cli.py docstring + 14 pinned tests + github-gitlab-abstraction-plan all confirm `python -m ...website` is an intended entry point (runs the website agent in isolation given pre-built intake+data JSON, as distinct from `scripts/run_pipeline.py`'s end-to-end pipeline). Fixed 4 drift findings: (F1) removed over-listed `ANTHROPIC_API_KEY` export (website agent makes no LLM calls), (F2) replaced abstract `intake.json`/`data.json` with the canonical fixture paths + substitution note, (F3) dropped cosmetic `export MPC_*` preambles (cli.py reads zero env vars), (F4) fixed §4.3 GHE case (previous recipe exported `MPC_HOST_URL` but invocation omitted `--host-url`, silently hitting public github.com). See `CHANGELOG.md`.
- [ ] **cli.py GitLab default URL inconsistency** (Session 31 F5) — `src/model_project_constructor/agents/website/cli.py:39` defaults `GITLAB_DEFAULT_HOST_URL = "https://gitlab.example.com"` (RFC-2606 placeholder). Inconsistent with `orchestrator/config.py:33` + `scripts/run_pipeline.py:105,283` + `.env.example:18-19` + `OPERATIONS.md:24` — all four of those declare the default as `https://gitlab.com`. Operators invoking `python -m ...website --host gitlab --private-token X --namespace ...` without `--host-url` hit a non-resolving domain. Small code + test change: bump the constant, add a regression test pinning the default, verify `test_cli.py:test_cli_host_gitlab_with_token_invokes_python_gitlab_adapter` still passes (it explicitly passes `--host-url` so the default is untested today — add coverage for the default path too).
- [ ] **Document `--ci-platform` flag in OPERATIONS §4.x** (Session 31 F6, low-impact) — cli.py:107-116 + README.md:197 describe `--ci-platform {gitlab,github}` (defaults to `--host`); OPERATIONS.md §4.1/§4.2/§4.3 don't mention it. Add a one-line note at the end of §4.1 or as a new §4.5.
- [ ] **Automated resume-from-checkpoint** — CLI or orchestrator logic to resume a failed pipeline run from the last successful checkpoint.
- [ ] **Add `scripts/render_tutorial.sh`** — Wrap the pandoc invocation with inline CSS (body width, hr margins, table borders) so rendering the tutorial to HTML is a one-liner.
- [ ] **Tutorial UX: split code blocks** — Split multi-command code blocks in `docs/tutorial.md` into individual blocks so each command is independently copyable. Pandoc/GitHub rendering doesn't provide per-block copy buttons, so also consider rendering to a format that does (e.g. MkDocs, Docusaurus).
- [ ] **Intake agent: data source discovery prompts** — Enhance the intake agent's system prompt to ask whether the stakeholder wants help identifying data sources, and if so, probe about existing systems (data warehouses, claims systems, policy admin). Currently the agent accepts whatever the stakeholder says about available data at face value.
- [ ] **Data agent: metadata discovery mode** — Add a discovery mode to the data agent that queries database metadata (`information_schema`, catalog tables) to identify relevant tables before generating training set queries. The data agent was designed to be reusable as a standalone query tool (per `initial_purpose.txt`); discovery mode extends that to data exploration.
- [ ] **Statistical terminology glossary** — Create `docs/style/statistical_terms.md` defining terms like probability vs likelihood, and inject it into agent system prompts so LLM-generated content uses correct statistical terminology instead of reproducing common conflations from training data.
- [ ] **Fix unclosed SQLite connection warnings** — ~20 `ResourceWarning: unclosed database` warnings from `tests/agents/data/test_data_agent.py` and one from `tests/agents/intake/test_anthropic_client.py`. Source is `ReadOnlyDB` / LangGraph checkpoint SQLite not closing connections. Surfaced by Python 3.13's stricter GC. Not a correctness issue but noisy.
- [ ] **Wiki freshness sweep** — Update `docs/wiki/claims-model-starter/` pages so each reads as a description of the current tool rather than a record of how it evolved. Specifically: walk every "Recommended additions" / "Future enhancements" / "Planned" list and (a) delete items that have already been implemented, (b) rewrite items that are only partially implemented to describe the remaining gap (not the original ask). Audit trigger: Session 19's wiki expansion and Sessions 20A/20B added surface area the "Content Recommendations" page hasn't been reconciled against; Scope B-1 (Session 24) now ships real LLM-backed data runs that some pages still describe as future work. Start with `Content-Recommendations.md`, `Home.md`, `Pipeline-Overview.md`, `Getting-Started.md`, and `Agent-Reference.md` which are the likely drift hotspots.
