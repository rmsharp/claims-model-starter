# Session Notes

**Purpose:** Continuity between sessions. Each session reads this first and writes to it before closing out.

---

## ACTIVE TASK
**Task:** Phase 3B of the architecture plan — Intake Agent Web UI (FastAPI + SSE + minimal HTMX frontend + SQLite session persistence)
**Status:** Phase 3A complete on `master`. The Intake Agent ships as `src/model_project_constructor/agents/intake/` with a full LangGraph flow (plan → ask_user interrupt → evaluate → draft → governance → await_review interrupt → revise/finalize), a `FixtureLLMClient` for deterministic replay, an `AnthropicLLMClient` for production runs, and a single-command typer CLI (`python -m model_project_constructor.agents.intake --fixture ...`). 179 tests pass at 96.18% coverage. Commits: `64b8a99` (Phase 3A implementation + tests + fixtures + close-out).
**Plan:** `docs/planning/architecture-plan.md` §14 Phase 3B defines DONE criteria and verification commands. §9.3 "Web UI (Intake Agent)" defines the stack (FastAPI + SSE + HTMX). §10 Intake Agent LangGraph and §4.1 governance cadence still govern — the web UI is a driver over the **same** compiled graph Phase 3A shipped.
**Priority:** HIGH

### What You Must Do
1. **Re-read the plan sections that govern Phase 3B before writing any code:**
   - §9.3 "Web UI (Intake Agent)" — FastAPI + SSE + HTMX stack, SQLite session persistence, resume-by-session-id
   - §14 Phase 3B — explicit DONE criteria and verification commands
   - §4.1 — cycle-time-driven governance still applies; the UI must surface the draft for review
   - §10 — Intake Agent LangGraph (you are driving the EXISTING compiled graph, not rewriting it)
2. Execute **only Sub-phase 3B** from §14:
   - `src/model_project_constructor/ui/intake/` — FastAPI app with SSE endpoint
   - Minimal HTMX frontend: question display + answer input + draft review page
   - SQLite checkpointer (swap `MemorySaver` → `langgraph.checkpoint.sqlite.SqliteSaver`) so session state survives server restart
   - Resume by `session_id` works across server restart
3. **Verification commands (from §14):**
   - `uv run uvicorn model_project_constructor.ui.intake:app` starts
   - Manual test: complete an interview end-to-end in the browser
   - `curl` smoke tests for SSE endpoint
4. **Do NOT rewrite the graph.** Phase 3A's `build_intake_graph()` in `src/model_project_constructor/agents/intake/graph.py` is the canonical flow. You only need to:
   (a) parameterize the checkpointer choice so you can pass a SQLite-backed one,
   (b) drive interrupts from HTTP requests instead of a scripted list,
   (c) wrap the `AnthropicLLMClient` from `anthropic_client.py` so users can hit a real API.
5. **Do NOT start Phase 4 (Website Agent).** That is a separate session.
6. **Do NOT touch the Data Agent package.** The intake → data decoupling symmetry is now tested indirectly — intake agent imports from the data agent would be caught by code review, not the AST test, since the AST test only walks the data agent side. If you need the symmetric test, add one that walks `src/model_project_constructor/agents/intake/` for imports matching `model_project_constructor_data_agent`. Session 6 deliberately did NOT add this because it would be testing non-existent behavior — the intake agent has zero reason to import data-agent code right now.

### Key Files Shipped in Phase 3A — Read Before Starting 3B
- `src/model_project_constructor/agents/intake/__init__.py:27-41` — the public API. Import from here, not from submodules.
- `src/model_project_constructor/agents/intake/state.py:28-54` — `IntakeState` TypedDict (no reducers, all deltas). `MAX_QUESTIONS=10`, `MAX_REVISIONS=3` are the cap constants.
- `src/model_project_constructor/agents/intake/protocol.py:64-84` — `IntakeLLMClient` Protocol with 4 methods. `AnthropicLLMClient` is the production implementation at `anthropic_client.py:51-151`.
- `src/model_project_constructor/agents/intake/nodes.py:33-150` — 8 graph nodes. **Critical:** `plan_next_question` and `ask_user` are split on purpose. `plan_next_question` calls the LLM; `ask_user` ONLY calls `interrupt()`. On resume, the interrupted node re-executes from the top, so putting the LLM call in `ask_user` would double-bill. See the next bullet.
- `src/model_project_constructor/agents/intake/graph.py:18-56` — `build_intake_graph(llm)` returns the compiled graph with `MemorySaver`. **For Phase 3B you MUST parameterize the checkpointer** so the web UI can pass a SQLite-backed saver. Either add a `checkpointer=None` kwarg or split into `make_graph_builder()` + `build_intake_graph(llm, checkpointer)`. Preserve the current API for tests.
- `src/model_project_constructor/agents/intake/agent.py:51-125` — `IntakeAgent.run_scripted()` is the headless driver. It loops `graph.get_state(config).tasks[0].interrupts` → `Command(resume=...)` → `graph.invoke(...)`. The web UI driver follows the same shape but one HTTP request at a time instead of from an in-memory list.
- `src/model_project_constructor/agents/intake/cli.py` — single-command typer app. **NO `@app.callback()`** — intake is one command so typer's auto-collapse is what we want. This is the OPPOSITE call from the data agent CLI, which DOES need the callback because it has a `run` subcommand.
- `tests/fixtures/subrogation.yaml` — canonical tier-3/tactical worked example (from `initial_purpose.txt`). Keep it as your Phase 3B smoke-test fixture — if the web UI can run this end-to-end with a real `AnthropicLLMClient`, you're done.
- `tests/fixtures/pricing_optimization.yaml` — tier-2/strategic governance scenario.
- `tests/fixtures/fraud_triage.yaml` — tier-1/continuous governance scenario.
- `tests/fixtures/intake_question_cap.yaml`, `tests/fixtures/intake_revision_cap.yaml` — cap-exhaustion scenarios used to assert `DRAFT_INCOMPLETE` behavior.
- `tests/agents/intake/test_graph.py:30-97` — end-to-end interrupt+resume tests. These exercise the real LangGraph interrupt machinery on langgraph 0.2.76. Copy this shape for the web-UI integration tests.

### How Session 6 Verified the LangGraph Interrupt Pattern
Session 6 ran a standalone toy graph (3 nodes: ask → decide → finalize, looping via `interrupt()` + `Command(resume=...)`) before writing any intake code. **Confirmed behaviors on langgraph 0.2.76:**
- `from langgraph.types import interrupt, Command` works.
- `from langgraph.checkpoint.memory import MemorySaver` works (resolves to `InMemorySaver` internally — both names work).
- `interrupt({"payload": ...})` pauses the graph; `state.tasks[0].interrupts[0].value` is the payload.
- `graph.invoke(Command(resume=value), config=...)` resumes; inside the node, `interrupt()` returns `value`.
- Loop-back through an interrupt node works — the same node interrupts multiple times in one run.

**Two pitfalls documented in the intake code and relevant to Phase 3B:**
1. **Interrupted nodes re-execute from the top on resume.** Never put a non-idempotent side effect before the `interrupt()` call in a node. Intake's solution: a `plan_next_question` node before `ask_user`. The first does the LLM call, the second only interrupts. Keep this split when wiring the Web UI.
2. **`Annotated[list, add]` reducers + nodes returning the full state dict = duplication.** Intake state deliberately has NO reducers; every node returns only a delta. If you add fields for the web UI session store (e.g. a list of audit events), do NOT use `operator.add` as the reducer — append in the node instead.

### Gotchas — Read These First
- **`origin` is still the GitHub remote** `https://github.com/rmsharp/claims-model-starter.git`. Push discipline applies — do not force-push master. GitHub issue tracker will be populated once UAT begins; until then `gh issue list` is expected to be empty (see `~/.claude/projects/-Users-rmsharp-Development-model-project-constructor/memory/project_issue_tracker.md`).
- **`methodology_dashboard.py` does not exist in the repo.** SESSION_RUNNER.md Phase 0 step 5 references it. Sessions 5 and 6 skipped this step with a flag; treat the dashboard as an undelivered tool unless a future session creates it.
- **Python is still 3.13.5 in `.venv`**, not 3.11. `requires-python = ">=3.11"` is inclusive. The code is 3.11-compatible; if you need to pin 3.11 hard, use `uv venv --python 3.11` and re-run `uv sync`.
- **LangGraph 0.2.76 interrupt pattern IS NOW VERIFIED** (Session 6, subrogation + all 5 fixtures through `build_intake_graph()`). The toy-graph verification step is DONE; don't redo it unless you bump langgraph versions.
- **`claude-sonnet-4-6` is hardcoded as the default model** in both `packages/data-agent/.../anthropic_client.py:43` and `src/model_project_constructor/agents/intake/anthropic_client.py:36`. STILL not verified against a live API (Session 6 did not have an API key either). If Phase 3B does its first real-API smoke test and the model ID is rejected, fall back to `claude-sonnet-4-5-20250929` or whatever is current, and flag it in the next handoff. The CLI's future `--model` flag should let users override; intake's CLI doesn't expose one yet.
- **Neither `AnthropicLLMClient` has been exercised against a real API.** All tests mock at `client.messages.create`. First real-API run of the intake agent during Phase 3B will be the first real-API run of anything in this repo. Expect either a working response or a model-ID-related 404/400 — both are easy fixes.
- **Two `StrictBase` classes exist in the codebase.** One at `src/model_project_constructor/schemas/v1/common.py:12` (used by intake, gitlab), one at `packages/data-agent/src/model_project_constructor_data_agent/schemas.py:28` (used by the standalone data schemas). They are deliberately duplicated — the standalone must not depend on the main package. Do not "DRY" them up.
- **`agents/data/__init__.py`, `db.py`, `llm.py` in the main package are NOT implementations** — they are thin re-exports of the standalone. Do not add logic to them. Any change to data agent behavior belongs in `packages/data-agent/src/model_project_constructor_data_agent/`.
- **Typer single-command trap works both ways.** The data agent CLI needs `@app.callback()` because it has `run` as a subcommand. The intake agent CLI does NOT have a callback because it has exactly one command and we WANT typer to auto-collapse so the plan's `python -m ... --fixture X` literal works. If you add a second intake subcommand in Phase 3B (e.g. `serve`), you MUST add `@app.callback()` at the same time or `python -m ... --fixture X` will break.
- **Intake fixture schema is `intake_fixture/v1`** (defined in `src/model_project_constructor/agents/intake/fixture.py:36`). The YAML must include `schema`, `stakeholder_id`, `session_id`, `qa_pairs`, `draft`, `governance`. Optional: `initial_problem`, `domain`, `draft_after`, `review_sequence`, `revised_draft`. The loader raises `IntakeLLMError` on any missing required field — exercised by `tests/agents/intake/test_fixture.py:49-63`.
- **Coverage gate is `--cov-fail-under=90`**, currently at 96.18%. Phase 3B's web UI + new test surface may temporarily drop this; add tests as you go or you will hit the floor.
- **Schema-plan reconciliation decisions from Phase 2A are still load-bearing.** Do not change the `DataReport` status interpretations without updating the data agent's Phase 2A tests.
- **README.md at repo root** is now updated through Phase 3A (repo layout, test count 179, coverage ≈96%, phase-3A-complete row). Update it again when Phase 3B ships.
- **QC "PASSED/FAILED" is still a coarse proxy** in the data agent (≥1 row = PASSED). Explicit future work for Phase 6 hardening. Not blocking for Phase 3.
- **`packages/data-agent/USAGE.md` is the standalone's README.** It's registered in its `pyproject.toml` as `readme = "USAGE.md"`. If you rename or delete it, `uv sync` fails on the workspace build.
- **Intake agent has NO `USAGE.md` yet** — Phase 3A's verification commands are in the main README. Consider adding `src/model_project_constructor/agents/intake/USAGE.md` in Phase 3B to document the web UI and the fixture format together.
- **`_DummyLLM` in `src/model_project_constructor/agents/intake/cli.py:85-99`** is a placeholder passed to `IntakeAgent()` that `run_with_fixture` immediately replaces. It only exists because typer instantiates the agent outside the LLM context. If Phase 3B builds a long-lived `IntakeAgent` per session, delete `_DummyLLM` and require a real client up-front.
- **mypy is not in §14 Phase 3A verification commands** but was run by Session 6 on the intake package alone — clean (0 errors in 10 source files). The rest of the repo has 33 pre-existing strict-mypy errors (mostly the Anthropic SDK's `ContentBlock` union for `anthropic_client.py`, plus one `QualityCheck.execution_status` `arg-type` error in the data agent). Phase 3B should not let these grow; running `uv run mypy src/model_project_constructor/agents/intake/` before committing is cheap and catches regressions on the intake side.
- **Intake graph re-entry does NOT leak state across sessions** as long as each session uses a unique `thread_id` in `config["configurable"]`. Session 6 uses `session_id` verbatim as `thread_id` in `agent.py:86`. Phase 3B should do the same — one HTTP session ↔ one `thread_id`.

### How You Will Be Evaluated
Your handoff will be scored on:
1. Was the ACTIVE TASK block sufficient to orient the next session?
2. Did you reuse `build_intake_graph()` instead of re-implementing the flow? (If Phase 3B re-implements nodes/graph, that's a regression on Session 6's split of flow vs. driver.)
3. Did you parameterize the checkpointer so the web UI gets SQLite persistence without breaking the CLI's in-memory mode?
4. Are key files listed with file:line references?
5. Did you complete Phase 3B as defined, or did you bundle Phase 4 (Website Agent)?
6. Were the Phase 2A + 2B + 3A gotchas preserved for Session 8 without dilution?
7. Did you do the first real-API smoke test OR explicitly defer it with a reason?

---

*Session history accumulates below this line. Newest session at the top.*

### What Session 6 Did
**Deliverable:** Phase 3A of architecture plan — Intake Agent core + LangGraph + CLI (COMPLETE)
**Started:** 2026-04-14
**Completed:** 2026-04-14
**Commits:** Session-6 single commit (pending at close-out) — Phase 3A implementation + tests + fixtures + README/SESSION_NOTES updates.

**What was done (chronological):**
1. Phase 0 orientation — read SAFEGUARDS, SESSION_NOTES Session 5 block, architecture-plan §4.1/§5.1/§10/§14 Phase 3A, checked git, confirmed `methodology_dashboard.py` still absent (Session 5 precedent) and `gh issue list` still empty (UAT-only, per memory note). Reported findings, waited for user direction.
2. Phase 1B session stub written to SESSION_NOTES.md before any technical work (`claimed Session 6, work beginning`).
3. **LangGraph interrupt-pattern toy-graph verification** — Session 5's hard prerequisite. Built a throwaway 3-node graph (ask → decide → finalize) on langgraph 0.2.76 using `from langgraph.types import interrupt, Command` and `from langgraph.checkpoint.memory import MemorySaver`. Ran invoke → pause (interrupts surface via `state.tasks[0].interrupts[0].value`) → resume (`Command(resume=...)`) → loop → resume → finalize. Confirmed two critical behaviors: (a) interrupted node re-executes from the top on resume, so LLM calls CANNOT sit in the same node as `interrupt()`; (b) `Annotated[list, add]` reducers plus a later node returning full state causes list duplication. Both shaped the design below.
4. Created 12 TaskCreate items covering design, toy verification, implementation phases, tests, verification, and close-out.
5. Designed the intake state as a plain `TypedDict` with NO reducers — nodes return deltas only. Deliberate, documented in `state.py`.
6. Designed `IntakeLLMClient` as a 4-method Protocol (`next_question`, `draft_report`, `classify_governance`, `revise_report`) with dataclass result types (`NextQuestionResult`, `DraftReportResult`, `GovernanceClassification`, `InterviewContext`). Separate from the data agent's LLMClient by design — they share no methods and the data agent package cannot be imported from anyway (Phase 2B).
7. Implemented 8 graph nodes in `nodes.py` — split `plan_next_question` (LLM call, idempotent-relative) from `ask_user` (interrupt only). Same split for the review step: `await_review` has only `interrupt()`, no side effects. `evaluate_interview` enforces the 10-question cap. `revise` increments `revision_cycles` AND re-runs `classify_governance` because governance can shift when the draft changes. `finalize` computes `missing_fields` based on which caps were hit (`questions_cap_reached`, `revision_cap_reached`) and validates the full `IntakeReport` through Pydantic via `build_intake_report()`.
8. Built the compiled graph in `graph.py` using `StateGraph(IntakeState)` + `MemorySaver`. Routing: `evaluate_interview` → `draft_report` or back to `plan_next_question`; `await_review` → `revise` or `finalize` based on `review_accepted` and cap.
9. Built `FixtureLLMClient` and `load_fixture()` in `fixture.py` with schema validation (`intake_fixture/v1`), missing-field checks, and `revised_draft` override to exercise revision cycles. Wrote `IntakeAgent.run_scripted()` in `agent.py` — it drives the compiled graph one interrupt at a time against a scripted answer list, with an explicit max-turns safety so a buggy graph can't infinite-loop a test run.
10. Smoke-tested the full flow against an in-memory fixture before writing any tests or fixtures. Printed `status=COMPLETE, Q=7, tier=tier_3_moderate, target=successful_subrogation, value_low=2000000`. That proved interrupt/resume + the whole node chain works end-to-end on the installed langgraph version.
11. Built the CLI as a typer app. **Initial mistake:** I used the `@app.callback()` + `@app.command("run")` pattern (copying the data agent exactly), which meant the CLI required `python -m ... run --fixture`. The plan literally specifies `python -m ... --fixture` with no subcommand. Ran the plan's verification command, caught the discrepancy, rewrote the CLI as a single `@app.command()` with NO callback so typer auto-collapses. Added to handoff gotchas that the two CLIs take OPPOSITE decisions on the callback.
12. Registered `model-intake-agent` console script in `pyproject.toml`. Added `pyyaml>=6` as an explicit dependency (was already transitively installed). Ran `uv sync` and confirmed the script works.
13. Wrote `anthropic_client.py` — concrete `AnthropicLLMClient` implementing all 4 Protocol methods with prompts for each. Mirrors the structure of the data agent's Anthropic client (code-fence stripping, JSON parsing, `IntakeLLMError` on bad shapes) but with interview-specific prompts. Injected SDK client for test mocking; lazy-imports `anthropic` when constructed without a client.
14. Wrote 5 fixtures: `subrogation.yaml` (tier-3 tactical, the canonical worked example from `initial_purpose.txt`), `pricing_optimization.yaml` (tier-2 strategic, consumer-facing auto pricing), `fraud_triage.yaml` (tier-1 continuous, SIU routing), `intake_question_cap.yaml` (11 QA pairs + `draft_after: 99` forces the 10-question hard cap), `intake_revision_cap.yaml` (4 rejection reviews forces the 3-revision hard cap). Smoke-tested all 5 end-to-end; every plan §14 Phase 3A DONE criterion is observable from this fixture set.
15. Wrote 56 tests across 5 test files:
    - `test_fixture.py` (15 tests) — fixture loader happy path, schema mismatch, missing fields, wrong shape; `FixtureLLMClient` question dispensing, draft/governance return, revise-default vs revise-override, answer/review helpers, error paths for draft and governance missing fields.
    - `test_nodes.py` (14 tests) — unit tests for each node with a hand-rolled `_StaticLLM`, plus router tests for both conditional edges, plus `build_intake_report` end-state assembly tests at both the `COMPLETE` and `DRAFT_INCOMPLETE` path.
    - `test_graph.py` (9 tests) — end-to-end interrupt+resume runs against all 5 fixtures, including the two cap scenarios, plus error paths for under-supplied answer/review scripts and a review-accept-token variants test.
    - `test_cli.py` (7 tests) — `CliRunner` tests for help, happy-path stdout + file output, missing fixture, `--anthropic` not-yet-wired error, revision cap fixture producing `DRAFT_INCOMPLETE`, and a real `subprocess.run(['python', '-m', ...])` that matches the plan's literal verification command.
    - `test_anthropic_client.py` (14 tests, all mocked) — every Protocol method's happy path, missing-key errors, non-object-response errors, code-fence stripping, garbage-JSON errors, and the lazy-import default constructor path via `monkeypatch` on `anthropic.Anthropic`.
16. **First pytest run caught one bug:** `review_sequence_from_fixture({"review_sequence": []})` returned `["ACCEPT"]` instead of raising because `seq or ["ACCEPT"]` treated `[]` as falsy. Fixed to distinguish `None` (default) from `[]` (error). All 56 intake tests green after the fix.
17. Ran full suite: **179 passed, 96.18% coverage** (123 → 179; +56 intake tests). Coverage floor of 90% met. Intake package coverage: `nodes.py` 94%, `fixture.py` 100%, `graph.py` 100%, `anthropic_client.py` 98%, `cli.py` 100%, `agent.py` 90%, `protocol.py` 91%, `state.py` 100%, `__init__.py` 100%.
18. Ran both plan §14 Phase 3A verification commands LITERALLY:
    - `uv run pytest tests/agents/intake/ -v` → 56 passed.
    - `uv run python -m model_project_constructor.agents.intake --fixture tests/fixtures/subrogation.yaml` → writes a `COMPLETE` `IntakeReport` JSON; `status=COMPLETE, Q=7, tier=tier_3_moderate, cycle=tactical`.
19. Ran `uv run mypy src/model_project_constructor/agents/intake/` — initially 20 errors across 5 files. Fixed the easy wins (nodes None-guards, graph.py return annotation, cli.py helper method annotations, anthropic_client.py `list` generic parameter, one `# type: ignore[union-attr]` for the SDK's content block union mirroring the data agent's pattern, `# type: ignore[import-untyped]` on `import yaml`, `# type: ignore[arg-type]` on the `_DummyLLM` injection). **Final: 0 errors in 10 source files on the intake package alone.** The rest of the repo still has 33 pre-existing strict-mypy errors that predate Session 6 (most in the data agent's anthropic_client.py, same content-block union issue).
20. Updated `README.md`: added Phase 3A row (Complete), added Phase 3B row (Not started), added `agents/intake/` to the repo layout with a short module breakdown, added `tests/agents/intake/` to the tests section, added all 5 intake fixtures, updated test count 123 → 179, updated coverage floor 80% → 90%, added an intake agent CLI quick-start block pointing at the subrogation fixture.
21. Rewrote the `ACTIVE TASK` block for Phase 3B with: plan sections to re-read, DONE criteria, explicit instruction to reuse `build_intake_graph()` rather than re-implement, key Phase 3A files with file:line references, the LangGraph interrupt pattern verification results (so Session 7 doesn't redo the toy graph), all gotchas from Phase 2B + new ones from Phase 3A (CLI callback asymmetry, fixture schema, `_DummyLLM` disposability, mypy status, thread_id = session_id convention).
22. Close-out commit pending: all Phase 3A code + tests + fixtures + README + SESSION_NOTES as a single commit.

**Key design calls:**
- **Split `plan_next_question` from `ask_user`.** The plan's §10 diagram shows one `ASK_NEXT_Q` → `WAIT_FOR_ANS` node pair. I split them because the toy graph proved that interrupted nodes re-run from the top on resume, which would double-call the LLM if `interrupt()` sat in the same node. This is the single highest-leverage correctness decision in Phase 3A — getting it wrong would have caused silent cost doubling and potentially non-deterministic questions on resume.
- **No state reducers.** `Annotated[list, add]` is a footgun when a later node returns full state (the toy demonstrated this). All intake state fields are replaced wholesale by the node that owns them, and the `qa_pairs` append is done manually inside `ask_user`. Documented in the `IntakeState` docstring.
- **Fixture is NOT the CLI's production path, but it IS the verification path.** `--anthropic` is a real flag on the CLI that currently errors out with "interactive terminal not shipped in Phase 3A — use the web UI from Phase 3B". This keeps the CLI from locking in a headless-interview pattern that Phase 3B will supersede. The fixture path is the ONLY way to drive the CLI today.
- **`AnthropicLLMClient` is its own class, not shared with the data agent.** Different prompts, different result shapes, different system prompts. Session 5's handoff explicitly warned against "DRYing" the LLM boundaries and I followed it.
- **Default model `claude-sonnet-4-6` without live-API verification.** Same caveat as Session 5's data agent anthropic client. Documented in handoff as a likely first-real-run fixable.
- **`IntakeAgent.run_scripted()` with a hard max-turns cap.** A cap of `MAX_QUESTIONS + MAX_REVISIONS + 5 = 18` stops a buggy graph from spinning forever in tests. Hit the cap in the revision-cap fixture before I noticed the count — it triggered a `RuntimeError` with a clear message rather than hanging.
- **Fixture schema is `intake_fixture/v1`** with strict field validation in the loader. Tests cover schema-version mismatch, non-mapping YAML, missing required fields, and missing nested draft/governance fields. Fails loud, which is the §12 contract.
- **Review-accept tokens are a fixed set** — `"accept"`, `"yes"`, `"approve"`, `"approved"`, `"ok"`, `"looks good"` (case-insensitive). Anything else is treated as revision feedback. This is a heuristic, and the web UI in Phase 3B should use a button rather than text matching; the CLI path uses it because a fixture driver needs something to script.
- **Single-command typer app for intake CLI, the OPPOSITE of the data agent CLI.** The data agent has `run` as an explicit subcommand, which requires `@app.callback()` to defeat typer's auto-collapse. The intake agent has exactly one entry point, so the auto-collapse is what we want — without the callback, `python -m ... --fixture X` works directly and matches the plan's literal verification command. If Phase 3B adds a `serve` subcommand, the callback must be added simultaneously or the CLI verification breaks.

**Files created (16):**
- `src/model_project_constructor/agents/intake/__init__.py`
- `src/model_project_constructor/agents/intake/__main__.py`
- `src/model_project_constructor/agents/intake/state.py`
- `src/model_project_constructor/agents/intake/protocol.py`
- `src/model_project_constructor/agents/intake/nodes.py`
- `src/model_project_constructor/agents/intake/graph.py`
- `src/model_project_constructor/agents/intake/fixture.py`
- `src/model_project_constructor/agents/intake/agent.py`
- `src/model_project_constructor/agents/intake/anthropic_client.py`
- `src/model_project_constructor/agents/intake/cli.py`
- `tests/agents/intake/__init__.py`
- `tests/agents/intake/conftest.py`
- `tests/agents/intake/test_fixture.py`
- `tests/agents/intake/test_nodes.py`
- `tests/agents/intake/test_graph.py`
- `tests/agents/intake/test_cli.py`
- `tests/agents/intake/test_anthropic_client.py`
- `tests/fixtures/subrogation.yaml`
- `tests/fixtures/pricing_optimization.yaml`
- `tests/fixtures/fraud_triage.yaml`
- `tests/fixtures/intake_question_cap.yaml`
- `tests/fixtures/intake_revision_cap.yaml`

**Files modified (3):**
- `pyproject.toml` — added `pyyaml>=6`, added `[project.scripts] model-intake-agent`
- `uv.lock` — regenerated by `uv sync`
- `README.md` — Phase 3A complete, repo layout updated, test count 179, coverage 90% floor, intake CLI quick-start
- `SESSION_NOTES.md` — this file

**Session 5 Handoff Evaluation (Session 6 scoring Session 5):**
- **Score: 10/10**
- **What helped (ranked by how much time each saved):**
  1. The "LangGraph 0.2.76 interrupt pattern STILL not verified" gotcha with explicit "Build a 3-node toy graph before any real intake code. Failure mode: you write 400 lines of agent code against an API that doesn't exist on the installed version" — this was the single most load-bearing note in the entire handoff. I did exactly that, found two pitfalls (node re-execution on resume, reducer duplication), and the whole agent design downstream was shaped by those findings. Without this I would have put the LLM call in `ask_user` and shipped a broken-on-resume agent.
  2. The `How You Will Be Evaluated` section — pre-declared six success criteria. I used it as a close-out self-check. Items 2 (toy graph first) and 5 (don't bundle 3B) were the ones I was most tempted to shortcut.
  3. The typer single-command-trap gotcha with exact file:line — I initially copied the data agent's pattern (callback + run subcommand), then the plan's literal verification command forced me to flip it. Session 5's warning framed the trap so I recognised my error within minutes of first `pytest` instead of spending 20 minutes debugging.
  4. The "fixture format not defined in plan, YAML is more comfortable" guidance — took the decision off my plate.
  5. Key files with file:line references (`intake.py`, `common.py`, `llm.py:1-94`, `anthropic_client.py`) — I read each one cold and knew exactly where to look.
  6. The empty-`gh issue list` + dashboard-missing protocol notes — orientation step completed in about 30 seconds because Session 5 had already established these as non-blocking.
- **What was missing (minor):**
  1. Session 5 didn't specify whether the intake agent's CLI should reuse the data agent's `run` subcommand pattern or match the plan literal. I chose the data agent pattern first (wrong) and had to redo the CLI. A one-liner saying "plan's Phase 3A verification command is top-level flags, NOT a subcommand" would have saved about 10 minutes.
  2. Nothing about how the fixture's review_sequence should handle the cap-exhaustion case. I invented the `intake_revision_cap.yaml` pattern (review_sequence with 4 rejections) from first principles, which worked but could have been pre-decided.
- **What was wrong:** Nothing. Every claim about existing code matched the repo state. The Session 5 `--fake-llm` escape-hatch framing correctly predicted that the intake agent would need its own fixture mode.
- **ROI:** Enormous. I estimate the handoff saved 60-90 minutes of re-derivation — the LangGraph verification guidance alone saved a full session of "why does my agent behave weirdly on resume". Read-cost was maybe 15 minutes.
- **Process notes:** Session 5 produced a 10/10 handoff by (a) pre-declaring evaluation criteria, (b) giving the next session an explicit technical risk to de-risk first, (c) naming traps with file:line breadcrumbs, (d) distinguishing "do these things" from "do not do these things" cleanly. I have copied all four patterns into my own handoff.

**Session 6 Self-Assessment:**
- (+) Completed Phase 0 orientation in full before any file touch. Wrote Phase 1B stub before any technical work. Reported findings and waited for user direction on a task-in-prompt turn.
- (+) Verified the LangGraph interrupt pattern on a toy graph BEFORE writing real agent code, per Session 5's explicit instruction. Caught two pitfalls (node re-execution, reducer duplication) that shaped the final design.
- (+) Split `plan_next_question` from `ask_user` at design time rather than after an expensive bug — direct result of the toy-graph discovery. This is the correctness decision I'm most proud of.
- (+) All 3 governance scenarios in tests hit distinct tiers (tier-1 continuous, tier-2 strategic, tier-3 tactical) with distinct rationales. Plan's "sensible classifications for 3 test scenarios" criterion is met with distinct, non-overlapping cases.
- (+) Both cap enforcement mechanisms have dedicated fixtures and dedicated tests. The 10-question cap and 3-revision cap are BOTH verified end-to-end through the real graph, not just at the node level.
- (+) Ran the plan's §14 Phase 3A verification commands LITERALLY. When my first CLI design didn't match the plan's literal command (it required `run` as a subcommand), I rewrote the CLI instead of updating the plan. Plan literal wins.
- (+) 56 new tests, 179 total, 96.18% coverage — comfortably above the 90% floor. Every intake source file is at ≥90% coverage; `fixture.py`, `graph.py`, `cli.py`, `state.py`, `__init__.py` are at 100%.
- (+) Ran mypy on the intake package and fixed every error — 0 errors in 10 files. Session 5 flagged not running mypy as a minor gap; I closed it. Did NOT fix the 33 pre-existing errors elsewhere in the repo — out of scope, noted in handoff.
- (+) Scope discipline: Phase 3A only. Did not start Phase 3B. Did not touch the Data Agent. Did not DRY the two `AnthropicLLMClient`s or the two `StrictBase` classes.
- (+) Recovered from three self-inflicted errors without user intervention: (1) wrong CLI subcommand pattern → rewrote as single command, (2) `review_sequence_from_fixture` treating empty list as None → fixed to distinguish, (3) mypy errors from missing type annotations → fixed with minimal `# type: ignore` use matching the data agent's patterns. All three documented in the chronological log and relevant ones in the handoff gotchas.
- (+) Used TaskCreate throughout — 12 tasks created up-front, each moved to in_progress when started, completed when done. No batching.
- (+) Handoff for Session 7 includes all required items: ACTIVE TASK updated with Phase 3B scope, what's done + commit reference, what's next with file:line references, key files, gotchas, evaluation criteria, LangGraph verification results so Session 7 doesn't redo it. Specifically guides Session 7 to REUSE `build_intake_graph()` rather than re-implement the flow.
- (−) I wrote the CLI twice — first with the data agent's callback+subcommand pattern, then as a single command. That cost ~10 minutes. Could have been avoided by reading the plan's verification command literal first, which I did but mis-interpreted. Self-inflicted, recoverable.
- (−) The `_DummyLLM` in `cli.py` is an ugly workaround for `IntakeAgent.__init__` requiring a client even when `run_with_fixture` will immediately replace it. A cleaner design would have `IntakeAgent` construct the graph lazily on first run. Noted for Phase 3B to clean up if a long-lived agent makes sense there.
- (−) The `AnthropicLLMClient` was never exercised against a real API. Same caveat as Session 5's data agent client. I did not attempt a live smoke test (no API key available in this session). Flagged in the handoff, but someone will discover whether `claude-sonnet-4-6` is a valid model ID on first real run.
- (−) I did NOT add a symmetric AST decoupling test for the intake agent (walking `src/model_project_constructor/agents/intake/` for imports matching `model_project_constructor_data_agent`). Session 5's handoff didn't require it, and the decoupling direction the plan enforces is data-agent-does-not-depend-on-main-package, not the reverse. Adding a symmetric test would be testing a non-existing relationship. Explicitly decided not to add it; noted in handoff.
- (−) The three governance fixtures are a MINIMUM — two of the four cycle-time values are covered (tactical, strategic, continuous) but `operational` is not. If a future Phase 3B or 3A polish session wants comprehensive governance-matrix coverage, that's an easy add.
- (−) I moved the toy graph work out of process before writing a test for it — the verification was shell output, not a committed test. The test files exercise the `interrupt` machinery implicitly through `test_graph.py`, so the pattern IS tested, but there's no standalone "langgraph 0.2.76 interrupt API exists" test. This is intentional (the implicit coverage is sufficient) but worth noting — if langgraph bumps major version and the API shifts, that test suite will fail loudly but the error might blame the intake code rather than the library.
- (−) No `USAGE.md` for the intake agent. The data agent has one (it's a separate distributable package so it needs its own readme); the intake agent lives in the main package and is documented in the main README. This is consistent but a dedicated document would be more discoverable for web-UI users in Phase 3B. Not in scope for 3A.

**Score: 9.5/10.** Phase 3A delivered with:
- Full LangGraph flow from §10 correctly implemented (with the interrupt-re-execution pitfall avoided)
- Both plan §14 verification commands passing literally
- 3 distinct governance scenarios tested end-to-end
- Both hard caps enforced end-to-end with dedicated fixtures
- Full Pydantic validation at the boundary
- 56 new tests, 96.18% coverage
- mypy clean on the intake package (which Session 5 flagged as a gap)
- Session 7 handoff that reuses Session 5's pattern language

Loses half a point for the CLI rewrite (self-inflicted, recovered without user intervention) and for not attempting a real-API smoke test of `AnthropicLLMClient`. The `_DummyLLM` ugliness and missing `USAGE.md` are intentional debts rather than mistakes.

---

### What Session 5 Did
**Deliverable:** Phase 2B of architecture plan — Data Agent standalone subpackage + CLI + Python API + AnthropicLLMClient (COMPLETE)
**Started:** 2026-04-14
**Completed:** 2026-04-14
**Commits:** `4982332` (refactor move) + `aca858a` (CLI + Anthropic + docs) + session-5 closeout (this commit). See `git log --oneline -5`.

**What was done (chronological):**
1. Phase 0 orientation — read SAFEGUARDS, SESSION_NOTES, architecture-plan §7/§14 Phase 2B, checked git. Flagged two protocol gaps: `methodology_dashboard.py` does not exist (SESSION_RUNNER.md step 5 references an absent tool); `gh issue list` returns empty (user confirmed UAT-only, saved to memory at `~/.claude/projects/.../memory/project_issue_tracker.md`).
2. Phase 1B session stub written to SESSION_NOTES.md before any technical work.
3. Presented three restructuring approaches (a/b/c) to the user with pros/cons and recommended (c). User approved (c) on `/effort max`.
4. Read every existing Data Agent source file and every file importing from the data agent (conftest, test_data_agent, schemas/v1/__init__.py, schemas/registry.py) to map every internal import and every test-facing name. This is what let the shim layer preserve Phase 2A tests unchanged.
5. Created 13 tasks in TaskCreate covering the two-commit execution plan + closeout.
6. Built `packages/data-agent/` skeleton + `pyproject.toml` (no `readme` field initially — added it back in commit B after USAGE.md existed).
7. Wrote `packages/data-agent/src/model_project_constructor_data_agent/schemas.py` as the new canonical home for `DataRequest/DataReport/PrimaryQuery/QualityCheck/Datasheet/DataGranularity` + its own 3-line `StrictBase`. Two `StrictBase` classes now exist (main + standalone); deliberate per Option (c) tradeoff.
8. Wrote/moved 8 agent source files into the standalone: `db.py`, `sql_validation.py`, `llm.py`, `state.py`, `nodes.py`, `graph.py`, `agent.py`, `__init__.py`. All internal imports rewritten from `model_project_constructor.agents.data.*` to `model_project_constructor_data_agent.*` and from `model_project_constructor.schemas.v1.data` to `model_project_constructor_data_agent.schemas`. Git detected all 5 moves as renames with 85–100% similarity.
9. Replaced main-package files with thin re-export shims: `agents/data/{__init__,db,llm}.py` and `schemas/v1/data.py`. Deleted `agents/data/{agent,graph,nodes,state,sql_validation}.py`.
10. Wired uv workspace in root `pyproject.toml`: `[tool.uv.workspace] members = ["packages/*"]` + `[tool.uv.sources]` + added `model-project-constructor-data-agent` as a dep. Updated pytest/coverage/mypy to walk both source trees.
11. Rewrote `tests/test_data_agent_decoupling.py` to walk the standalone's source AND the main-package shims (two test functions now, defense in depth).
12. **Error recovery #1:** First `uv sync` attempt failed because my `[tool.uv.workspace]` edit sliced `ui`/`dev` out of `[project.optional-dependencies]`. Fixed by moving the uv sections to after the optional-dependencies table.
13. **Error recovery #2:** Second `uv sync` failed because the standalone's `pyproject.toml` declared `readme = "USAGE.md"` which did not exist yet. Removed the field temporarily, re-added it in commit B.
14. `uv sync` succeeded; both packages built editable. Ran full suite: **102 passed, 98.66% coverage** (+1 test from decoupling split, +0.04 pts coverage — essentially flat).
15. Verified the decoupling test actually fires by injecting `from model_project_constructor.schemas.v1.intake import IntakeReport` into `state.py`, running the test (failed as expected with both forbidden tokens reported), and reverting.
16. **Commit A:** `refactor(phase-2b): move data agent to standalone package` — `4982332`. 17 files changed, 476+/247−, 5 renames detected.
17. Wrote `anthropic_client.py` — concrete `AnthropicLLMClient` implementing all four `LLMClient` protocol methods. Default model `claude-sonnet-4-6`. `_call_claude` centralises the SDK call; `_extract_json` handles code-fence stripping; `LLMParseError` propagates unparseable responses through the outer try/except as `EXECUTION_FAILED`.
18. Wrote `cli.py` — `typer` app with `run` subcommand. Flags: `--request`, `--output`, `--db-url`, `--model`, `--fake-llm`. `--fake-llm` uses an in-file `_FakeCLIClient` that returns canned deterministic responses so CI can exercise the CLI end-to-end without an API key.
19. **Error recovery #3:** First CLI test failed with "Got unexpected extra argument (run)" — typer auto-collapses single-command apps. Fixed by adding `@app.callback() def _main()` above the command, which promotes the app to a group. Flagged in the handoff gotchas for future sessions.
20. Wrote `__main__.py` to support `python -m model_project_constructor_data_agent`.
21. Wrote `tests/fixtures/sample_request.json` (canonical DataRequest fixture, used by CLI tests AND the USAGE.md CLI example).
22. Wrote `tests/data_agent_package/test_cli.py` — 5 tests covering: happy path without db, happy path with live SQLite (creates a `claims` table in `tmp_path`), missing-file error, help output, and `python -m` entry point via subprocess.
23. Wrote `tests/data_agent_package/test_anthropic_client.py` — 16 tests with a `_FakeAnthropic` / `_FakeMessages` harness that mocks at the `client.messages.create` boundary. Covers: protocol conformance, JSON parsing for each method, code-fence stripping, retry hint propagation, malformed-response errors for all 4 methods, `_extract_json` edge cases, and the default constructor path via `monkeypatch` on `anthropic.Anthropic`.
24. Wrote `packages/data-agent/USAGE.md` with three examples (CLI, Python script, Python notebook), full public API listing, and error-contract documentation. Interpreted the plan's explicit requirement for USAGE.md as authorisation (CLAUDE.md forbids autonomously creating docs files; this one is a plan deliverable).
25. Restored `readme = "USAGE.md"` in `packages/data-agent/pyproject.toml`. `uv sync` succeeded.
26. Ran the three plan §14 Phase 2B verification commands:
    - `uv run python -c "from model_project_constructor_data_agent import DataAgent"` → **ok** (`model_project_constructor_data_agent.agent`)
    - `uv run model-data-agent run --request tests/fixtures/sample_request.json --output /tmp/report.json --fake-llm` → **COMPLETE**, 1 query, schema_version 1.0.0
    - Full suite: **123 passed, 96.45% coverage**
27. **Commit B:** `feat(phase-2b): AnthropicLLMClient + typer CLI + Python API docs` — `aca858a`. 9 files created, 1089+ lines.
28. Updated README.md (user-requested during closeout): marked Phase 2B Complete, added standalone package to repo layout, updated test count 101 → 123, added CLI quick-start pointing at USAGE.md.
29. Phase 3A handoff written for Session 6 (full rewrite of ACTIVE TASK), Session 4 evaluation below, self-assessment below. Closeout commit pending.

**Key design calls:**
- **Option (c) restructure** — moved data agent + data schemas into standalone; main package re-exports. Picked over (a) vendored copy (divergence risk) and (b) re-export shim (fake physical decoupling). Cost: two `StrictBase` classes, ~10 moved files, one afternoon. Benefit: the standalone could be published to PyPI tomorrow and has provably zero dependency on the main package.
- **Two commits, not one.** Commit A is a pure-refactor move that keeps 102 tests green through the shim layer (one more than 2A's 101 because of the decoupling test split). Commit B adds all new behavior (AnthropicLLMClient, CLI, USAGE, tests). This makes the diff reviewable — the move and the feature work can be audited independently.
- **LLMClient Protocol stays on the data agent side.** The intake agent in Phase 3 should define its own Protocol, not share this one. They have nothing in common at the method level.
- **AnthropicLLMClient takes an injected `client`** so tests can mock at the SDK boundary. Construction without a `client` arg lazily imports `anthropic` and constructs `Anthropic()` (reads `ANTHROPIC_API_KEY`). One test covers this path via `monkeypatch` on `anthropic.Anthropic`.
- **`--fake-llm` is a real CLI flag, not hidden.** It's visible in `--help` but documented in USAGE.md as smoke-test-only. CI can exercise the full CLI path without an API key; this keeps test_cli.py tests green in any environment.
- **`_FakeCLIClient` is colocated with the CLI** rather than in tests. Justification: it's a runtime feature (the `--fake-llm` flag), not a test-only utility. Moving it to tests would mean the CLI imports from tests, which is wrong.
- **Two canonical `StrictBase` classes, two decoupling test functions.** Duplication is acknowledged and documented; both the schemas module docstring (`packages/data-agent/.../schemas.py:10`) and SESSION_NOTES gotchas explicitly flag that this is deliberate.
- **CLI subcommand trap fix** (`@app.callback()`) — typer's single-command auto-collapse bit me on the first test run. Fixed in one edit. Documented for future CLIs (the intake agent will need the same trick).
- **`claude-sonnet-4-6` as default model** — set from the system-reminder's stated current model family, NOT verified against a live API. Flagged in the handoff as a likely first-real-run failure if the model ID is wrong. Tests all mock the SDK so they don't care.

**Files created (14):**
- `packages/data-agent/pyproject.toml`
- `packages/data-agent/USAGE.md`
- `packages/data-agent/src/model_project_constructor_data_agent/__init__.py`
- `packages/data-agent/src/model_project_constructor_data_agent/schemas.py`
- `packages/data-agent/src/model_project_constructor_data_agent/db.py`
- `packages/data-agent/src/model_project_constructor_data_agent/sql_validation.py`
- `packages/data-agent/src/model_project_constructor_data_agent/llm.py`
- `packages/data-agent/src/model_project_constructor_data_agent/state.py`
- `packages/data-agent/src/model_project_constructor_data_agent/nodes.py`
- `packages/data-agent/src/model_project_constructor_data_agent/graph.py`
- `packages/data-agent/src/model_project_constructor_data_agent/agent.py`
- `packages/data-agent/src/model_project_constructor_data_agent/anthropic_client.py`
- `packages/data-agent/src/model_project_constructor_data_agent/cli.py`
- `packages/data-agent/src/model_project_constructor_data_agent/__main__.py`
- `tests/data_agent_package/__init__.py`
- `tests/data_agent_package/test_cli.py`
- `tests/data_agent_package/test_anthropic_client.py`
- `tests/fixtures/sample_request.json`

**Files moved (5, via git rename detection):**
- `agents/data/agent.py` → `packages/data-agent/.../agent.py` (95% similarity)
- `agents/data/graph.py` → `packages/data-agent/.../graph.py` (85%)
- `agents/data/nodes.py` → `packages/data-agent/.../nodes.py` (89%)
- `agents/data/sql_validation.py` → `packages/data-agent/.../sql_validation.py` (100%)
- `agents/data/state.py` → `packages/data-agent/.../state.py` (88%)

**Files modified (7):**
- `pyproject.toml` (workspace + coverage + mypy)
- `src/model_project_constructor/agents/data/__init__.py` (re-export shim)
- `src/model_project_constructor/agents/data/db.py` (shim)
- `src/model_project_constructor/agents/data/llm.py` (shim)
- `src/model_project_constructor/schemas/v1/data.py` (shim)
- `tests/test_data_agent_decoupling.py` (walk standalone + shim, 2 test functions)
- `README.md` (Phase 2B status + repo layout + test count + CLI quick-start)
- `uv.lock` (workspace resolution)
- `SESSION_NOTES.md` (this file)

**Session 4 Handoff Evaluation (Session 5 scoring Session 4):**
- **Score: 10/10**
- **What helped:** Session 4's ACTIVE TASK block was load-bearing from the first minute:
  1. The three restructuring options (a/b/c) with Session 4's explicit note that (c) is cleanest but "do it in Plan Mode or commit the move as a standalone commit" — I adopted exactly that structure (commit A = pure move, commit B = new features). Without this guidance I probably would have bundled everything into one commit and the reviewability would have suffered.
  2. The "plan inconsistency" flag on `python -m model_project_constructor.agents.data --help` being a Phase 2B entry point correctly predicted that I'd need `__main__.py`.
  3. The Key Files section with line ranges (`llm.py:1-94`, `agent.py:34-74`, `nodes.py:1-171`) was surgical — saved me from re-reading entire files when I only needed import shapes.
  4. The schema-plan reconciliation note (`DataReport.status` as authoritative vs. `qc_status`/`primary_query_status`) meant I preserved the Phase 2A test interpretation without re-deriving it.
  5. The "FakeLLMClient is the only implementation" warning + "don't tie the CLI to the fake" instruction directly shaped my design: I built `AnthropicLLMClient` first, then the CLI, with the fake as an explicit escape hatch flag rather than the default.
  6. The "SQLite resource leak" note and the coverage 98.62% baseline meant I knew what to expect and could notice immediately when I hit 96.45% (with full context of why — new CLI/Anthropic code has defensive paths).
- **What was missing:** Almost nothing. Two tiny gaps:
  1. Session 4 didn't flag that `methodology_dashboard.py` doesn't exist — I discovered this during orientation. Saved me maybe 30 seconds, but the Phase 0 checklist's step 5 explicitly references a non-existent tool, which is a protocol-level gap Session 4 could have flagged.
  2. Session 4's gotcha about "do the move in Plan Mode or as a standalone commit" didn't preemptively address whether user approval was required for the restructure. I spent a turn getting buy-in (correct per SAFEGUARDS) but Session 4 could have pre-authorized this for me by framing it as pre-approved since the plan requires it.
- **What was wrong:** Nothing. Every claim about existing code matched the repo state.
- **ROI:** Very high. I estimate reading the Phase 2B ACTIVE TASK block + the relevant plan sections saved me 45+ minutes of architecture re-derivation and at least one false start (probably would have gone for Option (b) as "safer" without the explicit "don't fake the decoupling" framing).
- **Process notes:** Session 4 wrote the Phase 1B stub, held the phase boundary (Phase 2A only, no CLI), addressed every Session 3 gotcha, and produced a handoff I could score against my own. The `How You Will Be Evaluated` section at the bottom of the ACTIVE TASK block is a pattern I should preserve.

**Session 5 Self-Assessment:**
- (+) Followed Phase 0 orientation fully. Phase 1B stub written before the first technical action. Phase 0 flagged two protocol gaps (missing dashboard, empty issue tracker) and saved one to memory.
- (+) Asked for architectural approval BEFORE touching code on a cross-module refactor, per SAFEGUARDS "Refactoring always requires plan mode approval". User approved (c) and I executed only (c).
- (+) Read every file whose imports would change BEFORE making changes — conftest.py, test_data_agent.py, tests/schemas/*, schemas/v1/__init__.py, registry.py. This is why the shim layer worked on the first try and zero test files needed to be edited.
- (+) Two-commit structure: pure refactor first (102 tests green through shims), then feature additions. Commit A is 17 files changed with 5 git-detected renames, reviewable as a move; commit B is 9 new files, reviewable as feature work. Followed Session 4's explicit advice.
- (+) Verified the decoupling test actually fires on injected violation before committing — Session 4's "don't treat it as passive scenery" guidance held.
- (+) Scope discipline: Phase 2B only. No intake work, no LangGraph interrupt investigation, no schema cleanup. Phase 3 is Session 6's.
- (+) Three plan §14 Phase 2B verification commands all passed explicitly; ran them separately, not just as part of the full suite.
- (+) `AnthropicLLMClient` has 16 tests covering every protocol method, every JSON-parse path, code-fence stripping, retry hint, and default-construction via monkeypatch. The CLI has 5 tests including a real-subprocess `python -m` smoke test.
- (+) Recovered from three self-inflicted errors without user intervention: (1) pyproject.toml structural edit mistake, (2) missing readme file referenced in pyproject.toml, (3) typer single-command auto-collapse trap. All three recoveries documented in the handoff so Session 6 knows the shape of the traps.
- (+) Used TaskCreate/TaskUpdate to track the 13 sub-tasks of a two-commit refactor. Each task was marked in_progress when started and completed when done, not batched at the end.
- (+) Saved one memory (project_issue_tracker.md) — user said GitHub issues are UAT-only; this will inform every future Phase 0 that currently treats empty `gh issue list` as a gap.
- (−) Did not run `mypy` (not in the §14 Phase 2B verification commands, but `strict = true` is in `pyproject.toml:80`). The one `type: ignore[arg-type]` inherited from Phase 2A at `agent.py:138` is still there. Any `AnthropicLLMClient`-level type errors (e.g., around the untyped `client: Any | None`) are uncaught.
- (−) Session 4's "SQLite resource leak" in `seeded_sqlite_url` fixture still leaks the engine handle. I added more tests that exercise the same fixture and did not fix the leak. Still non-blocking.
- (−) `claude-sonnet-4-6` as `DEFAULT_MODEL` is a guess from the system-reminder model family list. It is NOT verified against a live Anthropic API call — no `ANTHROPIC_API_KEY` in this session. If the actual model ID is something slightly different, the CLI will fail on first real-API invocation. Flagged in the handoff gotchas; the CLI `--model` flag lets users override.
- (−) I did not build a concrete integration-style test that skips when `ANTHROPIC_API_KEY` is absent — Session 4 specifically suggested this pattern. Decided against it: all tests mocking the SDK gives deterministic coverage; an integration test that conditionally runs is harder to reason about and tends to rot. A future hardening pass (Phase 6) can add one.
- (−) The CLI has a small dead-code path at `cli.py:119` (error handling around `_load_request`) that isn't covered. Same for `__main__.py` lines 3-6. Acceptable — they're defensive paths that only fire on environment-level failure.
- (−) README.md update happened during closeout at user request rather than being part of the plan. That's not a mistake, but it suggests README maintenance should be in the default closeout checklist for session boundaries that ship a user-facing feature. Adding to learnings.
- (−) Did not verify the LangGraph interrupt pattern — Session 4 flagged this as a Phase 3A concern. Correct to defer. But Session 6 MUST verify it first, and my handoff should make that boringly explicit (it does).

**Score: 9/10.** Phase 2B delivered with a clean two-commit refactor, all plan verifications green, 123 tests passing, decoupling guarantee preserved and re-verified, and a rich handoff. Loses a point for the unverified `DEFAULT_MODEL` string (real first-run will probably expose it) and for not running mypy. The error-recovery count (three self-inflicted mistakes) is acceptable given all three were caught and corrected without user intervention and left clear warning breadcrumbs for Session 6.

**Learnings added to SESSION_RUNNER.md Learnings table:** Not adding this session. Pattern candidates for future sessions: (a) "When a plan requires a cross-module refactor, the user-approval gate is the first step of the session, not a mid-session pause" — getting buy-in before any file touch prevents half-committed state; (b) "Typer single-command apps silently collapse the subcommand unless an `@app.callback()` is present" — worth a one-line entry in the Python idioms section once one exists. Not retroactively adding.

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
