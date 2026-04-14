# Session Notes

**Purpose:** Continuity between sessions. Each session reads this first and writes to it before closing out.

---

## ACTIVE TASK
**Task:** Phase 2B of the architecture plan — Data Agent standalone package + CLI + Python API
**Status:** Phase 2A complete on `master`. Data Agent core, LangGraph flow, decoupling test, and 101 passing tests (98.62% coverage) ship at commit `<phase-2a-hash>` (see `git log --oneline -5`). Remote `origin` is now `https://github.com/rmsharp/claims-model-starter.git`. Next session builds the `model-project-constructor-data-agent` subpackage, the `typer` CLI, and a Python API `USAGE.md`.
**Plan:** `docs/planning/architecture-plan.md` §14 Phase 2 (Sub-phase 2B) defines DONE criteria and verification commands.
**Priority:** HIGH

### What You Must Do
1. **Re-read the plan sections that govern Phase 2B before writing any code:**
   - §7 (specifically "Three Entry Points for the Data Agent") — pipeline, CLI, Python API. The CLI and Python API are packaged as a *separate installable subpackage* (`model-project-constructor-data-agent`) under `packages/data-agent/` to physically enforce decoupling.
   - §14 Phase 2B — explicit DONE criteria and verification commands.
2. Execute **only Sub-phase 2B** from §14:
   - `packages/data-agent/pyproject.toml` — standalone distribution, depends on `sqlalchemy`, `sqlparse`, `pydantic`, `langgraph`, `anthropic`, `typer`. Does NOT depend on the orchestrator package.
   - Decide how to share code between the two packages without the standalone pulling in `schemas.v1.intake` or anything outside `agents/data/` and `schemas/v1/data.py` + `schemas/v1/common.py`. Candidates:
     a. vendored copy of the data agent directory (simple; duplication risk)
     b. re-export via a namespace package or src-layout symlink
     c. restructure the main repo so `agents/data/` lives under `packages/data-agent/src/...` and the main package re-exports it
     — pick one and document the tradeoff. Option (c) is the cleanest but touches existing imports.
   - `typer`-based CLI: `model-data-agent run --request request.json --output report.json`.
   - Python API documented in `packages/data-agent/USAGE.md` with three examples (CLI, Python in script, Python in notebook). Since CLAUDE.md forbids creating docs files without explicit request, confirm with the user before writing USAGE.md — OR interpret the plan's explicit requirement for it as authorisation.
   - The decoupling test from Phase 2A must still pass after restructuring.
3. Add `python -m model_project_constructor.agents.data --help` entry point (mentioned in §14 Phase 2A verification but not in its DONE list — belongs in 2B; see "Plan inconsistencies" below).
4. Verify with §14 Phase 2B's commands.
5. **Do NOT start Phase 3 (Intake Agent + Web UI).** That is a separate session.

### Key Files from Phase 2A (already implemented)
- `src/model_project_constructor/agents/data/__init__.py` — re-exports `DataAgent`, `LLMClient`, `ReadOnlyDB`, `DBConnectionError`, `PrimaryQuerySpec`, `QualityCheckSpec`, `SummaryResult`. **Module docstring forbids intake imports.**
- `src/model_project_constructor/agents/data/llm.py:1-94` — `LLMClient` Protocol + intermediate dataclasses. **No concrete Anthropic implementation ships in 2A.** 2B's CLI will need one; see `anthropic` SDK in `pyproject.toml:18`.
- `src/model_project_constructor/agents/data/sql_validation.py` — conservative sqlparse wrapper; only rejects empty input and `UNKNOWN` statement type. This is deliberately weak; don't tighten it without a corresponding improvement to the LLM prompt.
- `src/model_project_constructor/agents/data/db.py` — `ReadOnlyDB` with `DBConnectionError`. Line 42 is a defensive `RuntimeError` branch not covered by tests (intentional — it guards programmer error).
- `src/model_project_constructor/agents/data/state.py` — `DataAgentState` TypedDict, `total=False`.
- `src/model_project_constructor/agents/data/nodes.py:1-171` — all node factories and the router. `MAX_SQL_RETRIES = 1` is the retry cap from §4.2.
- `src/model_project_constructor/agents/data/graph.py` — `build_graph(llm, db)` returns a compiled StateGraph. **Uses `StateGraph(DataAgentState)` with partial-update dict returns from nodes** — verified on langgraph 0.2.76.
- `src/model_project_constructor/agents/data/agent.py:34-74` — `DataAgent.run()` with the pre-flight semantic check and the try/except that catches all graph exceptions and surfaces them as `status="EXECUTION_FAILED"`.
- `tests/agents/data/conftest.py` — seeded SQLite fixture (5 rows into a `claims` table on tmp_path) + sample `DataRequest`, valid `PrimaryQuerySpec`, QC specs, `SummaryResult`, `Datasheet` fixtures.
- `tests/agents/data/test_data_agent.py:31-75` — `FakeLLMClient` deterministic stub. The `primary_queries_sequence` list lets tests drive the RETRY_ONCE / fail-after-retry branches.
- `tests/test_data_agent_decoupling.py` — **verified to actually fire** by temporarily injecting an `IntakeReport` import and running (failed as expected, reverted). Do not treat it as passive scenery; a failing decoupling test must block the build.
- `pyproject.toml` — readme field has been removed (README.md was stale; user asked for one at session end). Re-check before editing.

### Gotchas — Read These First
- **`origin` is now the GitHub remote** `https://github.com/rmsharp/claims-model-starter.git`. Push discipline applies — do not force-push master.
- **Python is 3.13.5 in `.venv`, not 3.11.** `uv python install 3.11` was run but `.venv` resolved to 3.13 because `requires-python = ">=3.11"` is inclusive. The agent code is 3.11-compatible (PEP 604 unions, `dataclasses`, `typing.Protocol`). If you need to pin 3.11 hard, use `uv venv --python 3.11`.
- **LangGraph 0.2.76 is installed; interrupt pattern is NOT yet verified.** Phase 2A used only `StateGraph` + `add_conditional_edges`; the Intake Agent's `AWAIT_REVIEW` interrupt node is a Phase 3A concern. Verify the interrupt pattern on a toy graph BEFORE wiring the real intake flow.
- **The FakeLLMClient is the only `LLMClient` implementation in the repo.** 2B's CLI needs a real one — don't tie the CLI to the fake. Add `AnthropicLLMClient` as a concrete impl, inject via constructor, and write one integration-style test that skips if `ANTHROPIC_API_KEY` is not set.
- **Schema-plan reconciliation decisions (documented in the Phase 2A commit message).** §4.2 references `qc_status` and `primary_query_status` fields that do not exist on `DataReport`/`PrimaryQuery`. Session 4 interpreted the three-valued `DataReport.status` as authoritative:
  - DB-down → `status=COMPLETE`, per-QC `execution_status=NOT_EXECUTED`, `data_quality_concerns` gets a "database unreachable" entry.
  - Invalid SQL after one retry → `status=EXECUTION_FAILED`, empty `primary_queries`, reason in `summary`.
  - Vacuous required fields → `status=INCOMPLETE_REQUEST`, empty `primary_queries`, `data_quality_concerns=["missing_field:<name>", …]`, graph not invoked.
  - Per-QC ERROR is isolated (other QCs proceed, report remains COMPLETE).
  Do not change these interpretations in 2B without updating Phase 2A tests.
- **QC "PASSED/FAILED" is a coarse proxy.** `make_execute_qc` marks `PASSED` if the query returns ≥1 row and `FAILED` if 0 rows. This is enough to exercise all four `execution_status` values end-to-end. A richer expectation evaluator (structured `expected_row_count > 0` DSL or LLM-judged) is explicit future work — Phase 6 hardening.
- **No concrete AnthropicLLMClient was shipped in 2A.** `anthropic>=0.40` is in `pyproject.toml [project.optional-dependencies].agents` but nothing imports it yet. Phase 2B should add `agents/data/anthropic_client.py` implementing `LLMClient`.
- **README.md now exists** (added at end of Session 4 at user request). It points to the architecture plan and is deliberately minimal. Do not treat it as authoritative documentation — `docs/planning/architecture-plan.md` still wins on conflicts.
- **Plan inconsistency (flagged in 2A commit):** §14 Phase 2A's verification list includes `python -m model_project_constructor.agents.data --help`, but that CLI entry point is Phase 2B's DONE criterion. Session 4 skipped the CLI smoke test in 2A. Add `__main__.py` in 2B.
- **Coverage gate is `--cov-fail-under=80`**, currently at 98.62%. Phase 2B's restructuring may briefly drop coverage; add tests as you go.
- **Do not refactor the data agent module layout solely for aesthetics.** If you restructure for Option (c) above (move under `packages/data-agent/src/`), do it in Plan Mode or at least commit the move as a standalone commit separate from the CLI/API additions so the diff stays reviewable.

### How You Will Be Evaluated
Your handoff will be scored on:
1. Was the ACTIVE TASK block sufficient to orient the next session?
2. Did you preserve the decoupling guarantee across the Phase 2B restructure?
3. Are key files listed with line numbers / section references?
4. Were gotchas and traps flagged, especially around schema-plan reconciliation and the untested interrupt pattern?
5. Did you complete Phase 2B as defined, or did you bundle Phase 3?

---

*Session history accumulates below this line. Newest session at the top.*

### What Session 4 Did
**Deliverable:** Phase 2A of architecture plan — Data Agent core + LangGraph + AST decoupling test (COMPLETE)
**Started:** 2026-04-14
**Completed:** 2026-04-14
**Commits:** `chore(env)` (env bootstrap) + `feat(phase-2a)` (agent + tests) + `docs/chore` session closeout — see `git log --oneline -5`.

**What was done (chronological):**
1. Phase 0 orientation — read SAFEGUARDS, SESSION_NOTES, architecture-plan.md §4.2/§7/§10.2/§12/§14 Phase 2A, git status, reported, waited for direction.
2. Phase 1B session stub written to SESSION_NOTES.md before any technical work.
3. Addressed Session 3's environment trap: `brew install uv` (got 0.11.6), `uv python install 3.11` (got 3.11.15 but the venv resolved to 3.13.5 because `requires-python = ">=3.11"` is inclusive — acceptable).
4. `uv sync --extra agents --extra dev` failed on a missing `README.md` referenced by pyproject.toml. Removed the `readme` line rather than auto-create a README (CLAUDE.md forbids creating docs files autonomously). `uv sync` then succeeded. Re-ran Phase 1 tests under the new interpreter: 88 passed, 100% schemas coverage.
5. Checkpoint-committed env bootstrap before touching agent code (SAFEGUARDS "commit before starting any new task").
6. Verified LangGraph 0.2.76 on a toy graph (conditional edges, `add_conditional_edges` with router function, partial-update dict returns, `.invoke()` merge semantics). Worked as expected.
7. Designed the Data Agent package layout with clean separation: `llm.py` (Protocol + dataclasses), `sql_validation.py`, `db.py`, `state.py`, `nodes.py` (factory functions closing over llm/db), `graph.py` (StateGraph assembly), `agent.py` (outer `DataAgent.run()`).
8. Made a deliberate decision NOT to ship a concrete `AnthropicLLMClient` in 2A — deferred to 2B — to avoid a half-finished implementation (global rule) and keep Phase 2A strictly scoped.
9. Wrote all 8 source files under `src/model_project_constructor/agents/data/` and verified imports.
10. Wrote `tests/agents/data/conftest.py` (seeded SQLite claims table with 5 rows, sample DataRequest, valid PrimaryQuerySpec, QC specs, SummaryResult, Datasheet fixtures).
11. Wrote `tests/agents/data/test_data_agent.py` — `FakeLLMClient` (deterministic stub with a `primary_queries_sequence` list that drives RETRY_ONCE and fail-after-retry) + 12 end-to-end tests: protocol check, happy path against real SQLite, RETRY_ONCE success, retry-exhausted → EXECUTION_FAILED, DB-unreachable via bad URL, DB=None, per-QC error isolation, INCOMPLETE_REQUEST parametrised over all four required fields, and unexpected-exception containment via an `ExplodingLLM` subclass.
12. Wrote `tests/test_data_agent_decoupling.py` — AST-walks every `.py` under `agents/data/`, asserts no import references `IntakeReport`, `schemas.v1.intake`, or `intake_report`.
13. **Verified the decoupling test actually fires** by temporarily injecting `from model_project_constructor.schemas.v1.intake import IntakeReport` into `state.py`. Test failed as expected, reporting both `IntakeReport` and `schemas.v1.intake` as offenders with the exact file path. Reverted the injection.
14. Ran §14 Phase 2A verification commands:
    - `uv run pytest tests/agents/data/ -v` → 12 passed
    - `uv run pytest tests/test_data_agent_decoupling.py` → 1 passed
    - Full suite: `uv run pytest -q` → 101 passed, coverage 98.62% (well above 80% gate)
    - Skipped `python -m model_project_constructor.agents.data --help` because that CLI is a Phase 2B deliverable (flagged as a plan inconsistency in the commit and the new handoff).
15. Committed Phase 2A under `feat(phase-2a): Data Agent core + LangGraph flow + AST decoupling test`.
16. **Late-session user addition:** create `README.md` and push to a new remote `https://github.com/rmsharp/claims-model-starter.git`. README created (explicit user authorisation overrides the CLAUDE.md prohibition). Remote `origin` added; `git push -u origin master` sent all history.
17. Rewrote ACTIVE TASK for Phase 2B, wrote this Session 4 closeout.

**Key design calls:**
- `LLMClient` is a `Protocol` rather than an ABC. Runtime-checkable for tests. Methods take typed domain objects and return typed domain objects — nodes never parse JSON.
- Intermediate `PrimaryQuerySpec`/`QualityCheckSpec`/`SummaryResult` dataclasses exist so LLM output and schema output can evolve independently. Downstream pydantic models are the enforcement point.
- `expected_row_count_order` typed as `str` on the intermediate spec but enforced as `Literal[...]` on the pydantic `PrimaryQuery`. Noted in the module docstring.
- Node factories (`make_*`) close over `llm` and `db` so node bodies take only `DataAgentState`. This keeps the StateGraph plumbing orthogonal to dependency injection.
- `DataAgentState` is a `TypedDict(total=False)` so nodes can populate incrementally. Initial state has `request`, `sql_retry_count=0`, `db_executed=False`.
- QC `PASSED/FAILED` uses a coarse ≥1-row proxy. Sufficient to exercise all four `execution_status` values; richer expectation evaluation is future work.
- Schema-plan reconciliation: plan §4.2 text references `qc_status` and `primary_query_status` fields that don't exist on the Phase 1 schemas. Session 4 interpreted the three-valued `DataReport.status` as authoritative — DB-down returns COMPLETE with per-QC NOT_EXECUTED, invalid SQL after retry returns EXECUTION_FAILED, missing/vacuous fields return INCOMPLETE_REQUEST. Documented in the commit and the new handoff.
- No `AnthropicLLMClient` in 2A. Deferred to 2B's CLI work to avoid half-finished implementations.
- README removed from pyproject.toml rather than auto-created (CLAUDE.md rule); README.md itself was created only after the user explicitly asked.

**Files created (15):**
- `src/model_project_constructor/agents/__init__.py`
- `src/model_project_constructor/agents/data/{__init__,llm,sql_validation,db,state,nodes,graph,agent}.py`
- `tests/agents/__init__.py`
- `tests/agents/data/{__init__,conftest,test_data_agent}.py`
- `tests/test_data_agent_decoupling.py`
- `README.md`
- `uv.lock`

**Files modified (3):**
- `pyproject.toml` (removed stale `readme = "README.md"` line)
- `SESSION_NOTES.md` (this file)

**Session 3 Handoff Evaluation (Session 4 scoring Session 3):**
- **Score: 10/10**
- **What helped:** The ACTIVE TASK block was the highest-quality handoff in the project so far. Every single gotcha fired during my session:
  1. The `uv` / Python 3.10 trap was item #1 in gotchas — I hit it immediately and had the fix ready (brew install uv, uv python install 3.11).
  2. The "LangGraph pattern unverified" flag drove me to write the toy graph before the real flow — saved me from discovering the state-merge semantics mid-implementation.
  3. The "decoupling test must actually fire" warning was the difference between writing theater and writing a real test. I explicitly verified it fires on an injected violation.
  4. The "three-valued status field, set each one explicitly" note drove the schema-plan reconciliation decisions.
  5. The "agents do NOT raise for expected failures (§12)" note drove the outer try/except in `DataAgent.run()`.
  The Key Files section with `data.py:21-98` and `common.py:13-31` line ranges was surgical — saved re-reading whole files.
- **What was missing:** Almost nothing. One gap: Session 3 didn't flag that `pyproject.toml` references a README.md that doesn't exist. `uv sync` would have hit it immediately on any fresh checkout. Worth ~3 minutes of my time. Not a 10→9 penalty because Session 3 didn't run `uv sync` themselves (they ran `python3 -m pytest`), so they couldn't have known.
- **What was wrong:** Nothing. The handoff was accurate end-to-end. The `database_hint` interpretation note was correct; the `StrictBase` `protected_namespaces` note was correct; the Phase 1 file line ranges matched.
- **ROI:** Very high. I estimate reading SESSION_NOTES.md + the plan sections saved me 60+ minutes of discovery and at least one wrong-direction start. The "verify decoupling test fires" instruction alone was worth the entire read.
- **Process notes:** Session 3 wrote the Phase 1B stub, held the phase boundary, and produced a handoff that was demonstrably load-bearing. This is the quality bar for the project.

**Session 4 Self-Assessment:**
- (+) Followed Phase 0 orientation fully before any work. Phase 1B stub written before the first technical action.
- (+) Addressed every trap Session 3 flagged: installed uv, pinned 3.11+ via uv, verified LangGraph on a toy graph before wiring the real flow, verified the decoupling test actually fires.
- (+) Scope discipline: Phase 2A only. No CLI, no standalone subpackage, no Anthropic client, no intake work. Explicit decision to skip the plan's §14 Phase 2A CLI smoke test because it belongs to 2B.
- (+) Clean separation of concerns: `LLMClient` Protocol, intermediate dataclasses, node factories, graph assembly, outer agent boundary. Every concrete concern is in exactly one file.
- (+) Test coverage 98.62% total, 100% on every new agent module except `db.py:42` (defensive `RuntimeError`) and `sql_validation.py:25,28` (defensive parse branches). All three uncovered lines are intentionally defensive and documented.
- (+) Parametrised the INCOMPLETE_REQUEST test over all four required fields so regressions in the semantic-check list get caught.
- (+) `ExplodingLLM` test proves the outer try/except in `DataAgent.run()` actually catches graph-internal exceptions and surfaces them as `EXECUTION_FAILED` — a critical part of the §12 contract.
- (+) Commit discipline: env bootstrap committed as a standalone checkpoint before agent code was touched (SAFEGUARDS "commit before starting any new task"). Agent code committed as one `feat(phase-2a)` commit. README + remote-push as their own commits at the end.
- (+) Schema-plan reconciliation decisions are documented in the commit body AND in the new handoff — future sessions can see what was interpreted and why.
- (+) Flagged a plan inconsistency (§14 Phase 2A verification list contains a CLI command that belongs to 2B) in the commit, in the handoff, and verbally to the user.
- (−) Did not build a concrete `AnthropicLLMClient`. Defensible decision (avoids half-implementation), but 2B will need one and may feel the pinch.
- (−) The `validate_sql` function is deliberately weak — it only rejects empty/whitespace and `UNKNOWN` statement type. `sqlparse` will accept a lot of garbage as "valid." A sharper validator (e.g., `EXPLAIN` against SQLite) would catch more, but it would also couple validation to the DB. Deferred.
- (−) Did not run `mypy` (not in §14 Phase 2A verification commands, but `mypy strict = true` is in `pyproject.toml:71`). Some `type: ignore[arg-type]` on line `agent.py:124` where I pass `str` into a `Literal[...]` field — pydantic validates at runtime.
- (−) ResourceWarning: unclosed SQLite connections in a few tests (the `seeded_sqlite_url` fixture leaks an engine handle). Non-blocking; clean up in 2B or a Phase 6 hardening pass.
- (−) Did not pin `--python 3.11` on the venv; `.venv` resolved to 3.13.5. The code is 3.11-compatible so this is not a bug, but the plan said "pin a 3.11+ interpreter" and I got a 3.13 interpreter that happens to satisfy `>=3.11`. Documented in the handoff.

**Score: 9/10** — Phase 2A delivered with comprehensive tests, proven decoupling guarantee, all known traps addressed, and strict scope adherence. Loses a point for the resource leak in the SQLite fixture and for not shipping even a stub `AnthropicLLMClient` that 2B could extend. The `mypy` gap is noted but not weighted against the score since it wasn't in the verification commands.

**Learnings added to SESSION_RUNNER.md Learnings table:** Not added this session. Pattern candidates for future sessions: (a) "LLM-driven agents: ship a Protocol + FakeClient in the core phase; defer concrete vendor integration to the CLI phase" and (b) "decoupling tests must be verified to actually fire by temporarily injecting a violation — a green-only history means nothing." These are in the handoff prose for now; I'll not retroactively add them unless a future session asks.

### What Session 3 Did
**Deliverable:** Phase 1 of architecture plan — Repo Skeleton + Schemas (COMPLETE)
**Started:** 2026-04-14
**Completed:** 2026-04-14
**Commit:** See git log for hash

**What was done (chronological):**
1. Phase 0 orientation — read SAFEGUARDS, SESSION_NOTES, architecture-plan.md in full (both halves), checked git, reported, waited for direction.
2. Phase 1B session stub written to SESSION_NOTES.md before any technical work.
3. Probed environment: `uv` not installed; system Python is 3.10.12 with pydantic 2.12.5 and pytest 9.0.2 already available. Decided to keep `pyproject.toml` strictly compliant with the plan (requires-python >=3.11, uv-ready) and run local tests via `python3 -m pytest`, flagging the Python-version gap for Phase 2A.
4. Wrote `pyproject.toml` — PEP 621 + hatchling, `model-project-constructor` package at `src/model_project_constructor`, core dep `pydantic>=2.6,<3`, optional groups `agents` / `ui` / `dev`. Pytest config includes `pythonpath = ["src"]` so tests run without manual `PYTHONPATH`. Per-session-3 user directive, added `pytest-cov` with `--cov-fail-under=80`.
5. Implemented `schemas/v1/common.py` (`StrictBase` with `extra="forbid"`, `protected_namespaces=()`, plus `CycleTime`, `RiskTier`, `ModelType`, `SCHEMA_VERSION`).
6. Implemented `schemas/v1/intake.py` — `ModelSolution`, `EstimatedValue`, `GovernanceMetadata`, `IntakeReport`. All inherit `StrictBase`.
7. Implemented `schemas/v1/data.py` — `DataGranularity`, `DataRequest`, `QualityCheck`, `Datasheet`, `PrimaryQuery`, `DataReport`. Module docstring forbids importing from `intake.py` (runtime AST test comes in Phase 2A per the plan).
8. Implemented `schemas/v1/gitlab.py` — `GitLabTarget`, `GovernanceManifest`, `GitLabProjectResult`.
9. Implemented `schemas/v1/__init__.py` re-exporting everything public.
10. Implemented `schemas/envelope.py` — `HandoffEnvelope` with its own `envelope_version="1.0.0"` and `payload: dict[str, Any]` (resolved by registry, not by envelope).
11. Implemented `schemas/registry.py` — `REGISTRY`, `SchemaKey`, `UnknownPayloadError(KeyError)`, `load_payload(envelope)`.
12. Wrote `tests/schemas/fixtures.py` — `make_*` factories for every schema.
13. Wrote `tests/schemas/test_intake.py`, `test_data.py`, `test_gitlab.py`, `test_envelope_and_registry.py` — 88 tests total.
14. `python3 -m pytest tests/schemas/ -v` → **88 passed in 0.13s**. Coverage on the `schemas` package is 100%.
15. Ran §14 Phase 1 smoke tests — both import checks pass; `len(REGISTRY) == 5`.
16. Rewrote ACTIVE TASK for Phase 2A and wrote this closeout.

**Key design calls:**
- `StrictBase` centralizes `ConfigDict(extra="forbid", protected_namespaces=())`. Avoids 14 copies of model_config and avoids the `model_` warning on `model_solution`/`model_type`/`model_registry_entry`.
- `UnknownPayloadError` inherits from `KeyError` (dict-lookup semantics); pydantic `ValidationError` remains separate for bad payloads.
- `target_variable: str | None` and `annual_impact_usd_low/high: float | None` are **required-nullable** (no default) — matches the plan's literal code. If Phase 2A finds this too strict, relax to `= None`.
- `database_hint` and `regulatory_mapping` have explicit defaults because the plan marks them "optional context."
- Decoupling rule is enforced textually in `data.py`'s docstring; runtime AST test is a Phase 2A deliverable per §14.
- Tests use `pytest.mark.parametrize` on every literal-enum field so adding a value is a one-line test change. Explicit regression guard against `default_factory` aliasing on `GovernanceManifest.regulatory_mapping`.

**Files created (17):**
- `pyproject.toml`
- `src/model_project_constructor/{__init__.py, schemas/__init__.py, schemas/envelope.py, schemas/registry.py, schemas/v1/{__init__,common,intake,data,gitlab}.py}`
- `tests/{__init__.py, schemas/{__init__,fixtures,test_intake,test_data,test_gitlab,test_envelope_and_registry}.py}`

**Session 2 Handoff Evaluation (Session 3 scoring Session 2):**
- **Score: 9/10**
- **What helped:** The ACTIVE TASK block was surgical — task, plan location, exact subsections to obey, explicit "do NOT start Phase 2," five-bullet evaluation rubric. The Gotchas section flagged four concrete traps; three were load-bearing for Session 3. Reading the plan + handoff took ~8 minutes and saved an estimated 45+ minutes of discovery.
- **What was missing:**
  - **No mention that `uv` was not installed on this machine.** Session 2 wrote "`uv` is the package manager" as a directive but did not verify it was available. ~2 minutes of probing.
  - **No flag that local Python is 3.10 while the plan pins 3.11+.** Latent trap for Phase 2A if LangGraph needs 3.11-only features.
  - The plan's `| None` comment syntax is ambiguous about required-nullable vs. optional-with-default. I had to make judgment calls on `target_variable`, the annual-impact bounds, and `database_hint`.
- **What was wrong:** Nothing factually wrong. Minor gap: the handoff references the `model_governance` project as the source of `GovernanceMetadata` but does not give its path.
- **ROI:** Very high. The plan was the valuable artifact; the handoff was a precise index.
- **Process note:** Session 2 correctly wrote a Phase 1B stub and held the planning-vs-implementation line.

**Session 3 Self-Assessment:**
- (+) Scope discipline. Phase 1 only. No agent code, no LangGraph, no adapters, no decoupling test — all Phase 2A.
- (+) Phase 1B stub written before any technical work.
- (+) All §14 Phase 1 verification commands green (pytest + both imports + `len(REGISTRY)`).
- (+) Tests exercise non-obvious cases: extra-field rejection, every literal value, serialization round-trip for every top-level schema, `load_payload` happy paths plus three failure modes, mutable-default aliasing regression guard.
- (+) Proactive abstractions (`StrictBase`, `SchemaKey`) only where they prevented repetition; no speculative generalization.
- (+) Module-level decoupling comment in `data.py` captures the §7 rule textually even without the runtime test.
- (+) Phase 2A gotchas are concrete: `uv`/Python 3.10 mismatch, unverified LangGraph interrupt pattern, three-valued status field, `extra="forbid"` discipline, `model_` namespace override, decoupling test must actually fire.
- (−) Did not install `uv`. Tests ran via `python3 -m pytest`; equivalent to `uv run pytest` but not the literal plan commands.
- (−) Local Python is 3.10; pyproject targets 3.11+. Works today because the schema code is 3.10-compatible; may bite Phase 2A.
- (−) `annual_impact_usd_low/high` are required-nullable. If intake agent has to pass `None` 80% of the time, relax to `= None` in Phase 2A or 3A.
- (−) No grep-based inventory — greenfield, so not mandatory per SESSION_RUNNER.md.

**Score: 9/10** — Deliverable met with comprehensive tests, explicit gotchas, scope discipline. Loses a point for not installing `uv` and for punting on the annual-impact default interpretation.

**Learnings added to SESSION_RUNNER.md Learnings table:** None this session. The schema code and tests are the Phase 1 institutional memory.

### What Session 2 Did
**Deliverable:** Formal architecture plan at `docs/planning/architecture-plan.md` (COMPLETE)
**Started:** 2026-04-14
**Completed:** 2026-04-14
**Commit:** See git log for hash

**What was done (in chronological order):**
1. **Orientation only (no work)** — followed Phase 0; reported state; waited for direction.
2. **Deleted `methodology_dashboard.py`** per user instruction during orientation.
3. **Jupyter → Quarto replacement** in `docs/planning/architecture-approaches.md` (3 edits: line 88, 100, 249). Replaced references with "Quarto markdown documents (.qmd) and unit-tested Python/R functions" per user directive that all code must live in tested modules.
4. **Regenerated `architecture-approaches.pdf`** via pandoc/xelatex after the edits.
5. **Governance research** — used Explore subagent to read all markdown in `/Users/rmsharp/Documents/Projects/Active_Projects/model_governance`. Findings: cycle-time taxonomy, risk tiering, first-line evidence ownership, three-pillar validation (SR 11-7), datasheets (Gebru 2021), model cards (Mitchell 2019), regulatory frameworks (SR 11-7, NAIC AIS, EU AI Act, ASOP 56). User directed: hold governance findings for formal plan, do NOT augment approaches doc.
6. **User selected approaches:** Sequential Script + LangGraph/Claude + Pydantic envelope + Code Gen Only (Quarto).
7. **Wrote `docs/planning/architecture-plan.md`** — 19 sections, ~1000 lines:
   - §1 Context, constraints, explicit scope boundary
   - §2 Decision summary (chosen approaches)
   - §3 High-level architecture with ASCII diagram
   - §4 Agent boundaries with per-agent I/O and failure mode tables
   - §5 Pydantic schemas with field-level detail (`IntakeReport`, `DataRequest`, `DataReport`, `GitLabTarget`, `GitLabProjectResult`, governance models)
   - §6 Handoff envelope protocol with schema registry and versioning rules
   - §7 Data Agent reuse interface with adapter pattern and decoupling test
   - §8 Governance integration — proportional scaffolding by risk tier + cycle time
   - §9 Technology stack with specific versions and models
   - §10 LangGraph orchestration pattern with ASCII graphs per agent
   - §11 Generated GitLab repo structure (full file tree)
   - §12 Error handling strategy (agents return reports, don't raise)
   - §13 Consolidated failure mode analysis
   - §14 Implementation phases: 6 phases across 8 implementation sessions, each with explicit DONE criteria, verification commands, and session boundary markers
   - §15 Alternatives considered (pointer to approaches doc)
   - §16 Impact analysis
   - §17 Verification plan
   - §18 Open questions (deferred decisions)
   - §19 ARCHITECTURE_WORKSTREAM verification checklist

**Key decisions baked into the plan:**
- LangGraph is used **inside each agent**, not at the top level. The top-level orchestrator is still a Sequential Script. This preserves the upgrade path.
- `GovernanceMetadata` is a new addition to `IntakeReport` beyond what `initial_purpose.txt` describes — driven by the governance research in step 5.
- Data Agent decoupling is enforced by a CI test in `tests/test_data_agent_decoupling.py` that AST-walks the Data Agent source and fails on any `IntakeReport` import.
- The Data Agent is packaged as a separate installable subpackage (`model-project-constructor-data-agent`) to physically enforce the decoupling.
- Quarto + `src/` split: all code lives in `src/` as tested functions; `.qmd` files are narratives that import from `src/`. This satisfies the user's C6 constraint.
- EDA is code-generation-only — generated `.qmd` files are NOT rendered by the pipeline; the data science team renders them. This avoids executing LLM-generated code against corporate databases.
- Governance scaffolding is proportional: tier 3+ adds three-pillar validation, tier 2+ adds impact assessment and regulatory mapping, tier 1 adds LCP integration and audit log.

**Session 1 Handoff Evaluation (Session 2 scoring Session 1):**
- **Score: 7/10**
- **What helped:** The ACTIVE TASK block clearly stated the deliverable. The Gotchas section was genuinely useful — particularly the one flagging that Step 4 is not a separate agent (prevented me from over-counting agents), the one about Data Agent decoupling having multiple approaches with different implications, and the one noting the `initial_purpose.txt` output is prose not JSON (led me to think carefully about how LLMs produce structured output). The key-files list with line numbers for `initial_purpose.txt:18-80` and `:84-87` was precise and saved a re-read.
- **What was missing:** No mention of the `model_governance` project existing. The user had to volunteer it mid-session. A "related projects" section in the handoff would have surfaced it earlier. Also: no mention that `methodology_dashboard.py` was problematic/deprecated — user asked to delete it during orientation, which suggests the previous session knew it wasn't working but didn't flag it.
- **What was wrong:** Nothing inaccurate. The handoff was honest.
- **ROI:** High. Reading the handoff took ~2 minutes and saved probably 20+ minutes of discovery work. The line-number references specifically saved re-reading full files.
- **Process note:** Session 1 did not write a Phase 1B stub (no ghost session risk because it was the first session, but it should have followed the protocol). I corrected this for Session 2 by writing the stub before any technical work.

**Session 2 Self-Assessment:**
- (+) Followed Phase 0 orientation fully before doing any work; waited for user direction.
- (+) Wrote the Phase 1B session stub before starting technical work (corrected Session 1's omission).
- (+) Did not bundle the plan with implementation — strict adherence to the "plan IS the deliverable" rule.
- (+) The plan has explicit per-phase completion criteria and verification commands (SESSION_RUNNER.md planning-session requirement).
- (+) Governance integration is first-class, not a bolt-on — it's woven through intake capture, schemas, and repo scaffolding.
- (+) Decoupling test for the Data Agent is specified at the AST level, not just as a convention.
- (+) Quarto + `src/` split directly satisfies user constraint C6.
- (+) Failure modes analyzed per-agent and consolidated globally (§4 + §13).
- (+) Alternatives explicitly rejected with honest reasons (§15).
- (-) Did not run a grep-based inventory — but this is a **greenfield** plan, not a deletion/migration/rename, so per SESSION_RUNNER.md the evidence-based inventory is not mandatory. Noted here for transparency.
- (-) §18 Open Questions has 5 items that should ideally have been resolved during planning. They are genuinely deferrable (they don't block Phase 1), but a stricter plan would have pushed on them.
- (-) The plan is long (~1000 lines). A shorter plan would be easier for a future session to read fully. However, the alternative (a short plan with vague phases) is worse because it invites bundling.
- (-) Did not verify `langgraph==0.2.x` actually supports the interrupt pattern I described for the intake review step. This should be verified in Phase 3A before implementing the intake agent. Noted as a risk in the Phase 3A session start.

**Score: 9/10** — Comprehensive, actionable, with explicit session boundaries and verification commands. Loses a point for the unverified LangGraph interrupt pattern and the 5 deferred open questions. No bundling, no scope creep, no protocol violations.

**Learnings added to SESSION_RUNNER.md Learnings table:** Not added this session. The plan itself is the learning artifact for future implementation sessions.

### What Session 1 Did
**Deliverable:** Architecture approaches document (COMPLETE)
**Started:** 2026-04-10
**Commit:** See git log for hash

**What was done:**
- Created initial commit with all project scaffolding files (18 files)
- Deep analysis of `initial_purpose.txt`, `ROADMAP.md`, `BACKLOG.md`, all methodology workstream docs
- Produced `docs/planning/architecture-approaches.md` covering 4 critical features:
  1. Pipeline Orchestration (3 approaches: Sequential Script, State Machine, Event-Driven)
  2. Technology Stack & LLM Integration (3 approaches: LangGraph+Claude, Agents SDK+GPT-4o, Custom+Mixed Models)
  3. Schema Design & Handoff Protocol (3 approaches: Pydantic Envelope, JSON Schema+Codegen, Markdown+Frontmatter)
  4. EDA & Model Building (3 approaches: Code Gen Only, Sandboxed Subprocess, Containerized)
- Each approach includes concrete pros/cons, technology names, "best suited for" guidance
- Decision dependencies table mapping which choices constrain others
- Recommended starting combination at bottom of document

**Self-Assessment:**
- (+) Thorough coverage of all 4 critical features with concrete, actionable approaches
- (+) Each approach grounded in the project's specific constraints (P&C domain, Data Agent reuse, GitLab output)
- (+) Decision dependencies table helps avoid incompatible combinations
- (+) Recommended starting point gives a pragmatic default
- (-) Did not produce the formal architecture plan — approaches doc is the prerequisite, not the final deliverable. This was the correct scope for one session.
- (-) No session stub was written before starting work (Phase 1B violation — first session, so no ghost session risk, but protocol should be followed)

**Score: 7/10** — Good approaches document with concrete detail. Loses points for missing the session stub and for not having line-number references in the approaches doc itself.

Session 1 Handoff Evaluation: N/A (first session, no predecessor)
