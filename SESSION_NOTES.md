# Session Notes

**Purpose:** Continuity between sessions. Each session reads this first and writes to it before closing out.

---

## ACTIVE TASK
**Task:** Phase 3A of the architecture plan — Intake Agent core + LangGraph + CLI
**Status:** Phase 2B complete on `master`. Data Agent now lives as the standalone `model-project-constructor-data-agent` package under `packages/data-agent/` with its own CLI (`model-data-agent run`), concrete `AnthropicLLMClient`, and `USAGE.md`. Main package re-exports it via thin shims so all Phase 2A imports keep working. 123 tests pass at 96.45% coverage. Commits: `4982332` (refactor move) + `aca858a` (CLI + Anthropic + docs).
**Plan:** `docs/planning/architecture-plan.md` §14 Phase 3 (Sub-phase 3A) defines DONE criteria and verification commands. §4.1 and §10 Intake Agent LangGraph govern the flow. §5.1 defines the `IntakeReport` schema (already shipped in Phase 1).
**Priority:** HIGH

### What You Must Do
1. **Re-read the plan sections that govern Phase 3A before writing any code:**
   - §4.1 Intake Agent — scope, 10-question cap, 3-revision cap, governance sub-prompt
   - §10 — Intake Agent LangGraph (diagram + nodes; specifically the `AWAIT_REVIEW` interrupt node)
   - §5.1 `IntakeReport` schema — `business_problem`, `proposed_solution`, `model_solution`, `estimated_value`, `governance_metadata`. Already implemented at `src/model_project_constructor/schemas/v1/intake.py`.
   - §14 Phase 3A — explicit DONE criteria and verification commands.
2. Execute **only Sub-phase 3A** from §14:
   - `src/model_project_constructor/agents/intake/` — the LangGraph flow from §10
   - CLI: `python -m model_project_constructor.agents.intake --fixture tests/fixtures/subrogation.yaml` producing a valid `IntakeReport`
   - Interview with synthetic stakeholder responses from a fixture
   - 10-question cap enforced, 3-revision cap enforced
   - Governance sub-prompt produces sensible `cycle_time`/`risk_tier` classifications for 3 test scenarios
3. **Verify the LangGraph interrupt pattern on a toy graph BEFORE wiring the real intake flow.** Phase 2A only used `StateGraph` + `add_conditional_edges`. The `AWAIT_REVIEW` node requires `interrupt` / `Command(resume=...)`, which is different machinery. Build a 3-node toy graph that interrupts, resumes via user input, and re-enters a loop. Confirm it works on langgraph 0.2.76 before committing any real intake code. Failure mode: you write 400 lines of agent code against an API that doesn't exist on the installed version.
4. **Do NOT start Phase 3B (Web UI).** That is a separate session.
5. **Do NOT touch the Data Agent package.** Phase 2B moved it to `packages/data-agent/`; the intake agent should import NOTHING from the data agent. Symmetric to §7 in the other direction.

### Key Files to Reuse (Phase 1 + 2B)
- `src/model_project_constructor/schemas/v1/intake.py` — `IntakeReport`, `ModelSolution`, `EstimatedValue`, `GovernanceMetadata`. All `StrictBase` subclasses. `schema_version: Literal["1.0.0"]`.
- `src/model_project_constructor/schemas/v1/common.py` — `StrictBase`, `CycleTime`, `RiskTier`, `ModelType`, `SCHEMA_VERSION`. Use these for the governance sub-prompt's typed output.
- `src/model_project_constructor/schemas/envelope.py`, `registry.py` — handoff envelope protocol. Register intake output under `("IntakeReport", "1.0.0")` (already done in `registry.py:27`).
- `packages/data-agent/src/model_project_constructor_data_agent/llm.py` — the `LLMClient` Protocol pattern is a good template for the intake agent's own LLM boundary. The intake agent should define its own Protocol, not share the data agent's.
- `packages/data-agent/src/model_project_constructor_data_agent/anthropic_client.py` — working concrete example of Claude 4.6 via SDK 0.94.1, with prompt construction, code-fence stripping (`_extract_json`), and `LLMParseError`. Copy the parsing utilities but give the intake agent its own `AnthropicLLMClient` since the prompts are completely different.
- `packages/data-agent/src/model_project_constructor_data_agent/cli.py` — typer CLI pattern with `@app.callback()` + `@app.command()` is the working shape for a single-subcommand app. Do not forget the callback — typer collapses single-command apps otherwise.

### Phase 2B — What Changed
- **New standalone package:** `packages/data-agent/` with its own `pyproject.toml`, `src/model_project_constructor_data_agent/` (9 source modules + `__main__.py`), `USAGE.md`. Standalone has ZERO runtime dependency on the main package (its own minimal `StrictBase`, its own schemas).
- **Main package shims:**
  - `src/model_project_constructor/agents/data/__init__.py` re-exports `DataAgent`, `LLMClient`, etc. from the standalone.
  - `src/model_project_constructor/agents/data/db.py` and `llm.py` are submodule shims so `from model_project_constructor.agents.data.db import ReadOnlyDB` still works.
  - `src/model_project_constructor/schemas/v1/data.py` re-exports `DataRequest`/`DataReport`/etc. from `model_project_constructor_data_agent.schemas`. The canonical definitions live in the standalone.
  - Deleted: `agents/data/agent.py`, `graph.py`, `nodes.py`, `state.py`, `sql_validation.py` (moved to standalone).
- **Workspace wiring:** `pyproject.toml:26-30` adds `[tool.uv.workspace] members = ["packages/*"]` and `[tool.uv.sources] model-project-constructor-data-agent = { workspace = true }`. `uv sync` builds both packages editable. `uv.lock` updated.
- **Pytest/coverage/mypy:** `pyproject.toml:51-61,79-83` — coverage now tracks both packages, pythonpath includes both source trees, mypy packages list includes both.
- **Decoupling test:** `tests/test_data_agent_decoupling.py` rewritten to walk the standalone's source (new canonical location) AND the main-package shims (defense in depth). Verified the test still fires on injected violation. Two test functions now; previously one.
- **AnthropicLLMClient:** `packages/data-agent/src/model_project_constructor_data_agent/anthropic_client.py`. Implements all four `LLMClient` protocol methods. Default model `claude-sonnet-4-6`. Parses JSON responses, strips code fences, raises `LLMParseError` on malformed output. Client injected via constructor for testability.
- **typer CLI:** `packages/data-agent/src/model_project_constructor_data_agent/cli.py`. Exposes `model-data-agent run --request ... --output ... [--db-url ...] [--model ...] [--fake-llm]`. Registered as console script. `__main__.py` supports `python -m model_project_constructor_data_agent`.
- **Tests added:** `tests/data_agent_package/test_anthropic_client.py` (16 tests, all mocked at SDK boundary), `tests/data_agent_package/test_cli.py` (5 tests via `CliRunner` + subprocess for `python -m`). `tests/fixtures/sample_request.json` is the canonical `DataRequest` fixture used by CLI tests and `USAGE.md` examples.

### Gotchas — Read These First
- **`origin` is still the GitHub remote** `https://github.com/rmsharp/claims-model-starter.git`. Push discipline applies — do not force-push master. GitHub issue tracker will be populated once UAT begins; until then `gh issue list` is expected to be empty (see `~/.claude/projects/-Users-rmsharp-Development-model-project-constructor/memory/project_issue_tracker.md`).
- **`methodology_dashboard.py` does not exist in the repo.** SESSION_RUNNER.md Phase 0 step 5 references it. Session 5 skipped this step with a flag; treat the dashboard as an undelivered tool unless a future session creates it.
- **Python is still 3.13.5 in `.venv`**, not 3.11. `requires-python = ">=3.11"` is inclusive. The code is 3.11-compatible; if you need to pin 3.11 hard, use `uv venv --python 3.11` and re-run `uv sync`.
- **LangGraph 0.2.76 interrupt pattern is STILL not verified.** Phase 2B did not exercise it (no interrupt needed). Phase 3A MUST verify on a toy graph before wiring the real intake flow. The interrupt/resume API may differ between langgraph 0.2.x and 0.3.x; your toy must use the installed version's actual API, not docs from a newer release.
- **`claude-sonnet-4-6` is hardcoded as the default model** in `packages/data-agent/src/model_project_constructor_data_agent/anthropic_client.py:39` (`DEFAULT_MODEL`). If you discover at runtime that this model ID is wrong (the anthropic SDK rejects it), fall back to `claude-sonnet-4-5-20250929` or whatever is current. This was set from system-reminder context at session time and was not verified against a live API call (no `ANTHROPIC_API_KEY` in this session). The CLI `--model` flag lets users override, and the tests mock the SDK so they don't care.
- **The AnthropicLLMClient was never exercised against a real API.** All 16 of its tests mock `anthropic.Anthropic().messages.create`. First real run will need to verify: (a) model ID is accepted, (b) Claude actually returns JSON in the format the prompts request, (c) the code-fence stripping regex covers what Claude emits. Session 3 of the intake agent is a good opportunity to do a single real-API smoke test for the data agent.
- **Two `StrictBase` classes exist in the codebase now.** One at `src/model_project_constructor/schemas/v1/common.py:12` (used by intake, gitlab), one at `packages/data-agent/src/model_project_constructor_data_agent/schemas.py:28` (used by the standalone data schemas). They are deliberately duplicated — the standalone must not depend on the main package. Do not "DRY" them up.
- **`agents/data/__init__.py`, `db.py`, `llm.py` in the main package are NOT implementations** — they are thin re-exports. Do not add logic to them. Any change to data agent behavior belongs in `packages/data-agent/src/model_project_constructor_data_agent/`.
- **Typer single-command-app trap:** a typer app with one `@app.command()` and no `@app.callback()` auto-collapses the subcommand. `model-data-agent run ...` fails with "Got unexpected extra argument (run)". The fix is `@app.callback() def _main(): ...` above the command. This bit me in Session 5 on the first CLI test; fixed in `packages/data-agent/src/model_project_constructor_data_agent/cli.py:46-48`. Do the same for the intake CLI.
- **Plan verification commands for 3A say `uv run python -m model_project_constructor.agents.intake --fixture ...`.** The fixture format is not defined in the plan. Pick YAML or JSON and document it in the intake agent's USAGE/README. The data agent used JSON (`tests/fixtures/sample_request.json`); YAML is more comfortable for multi-turn dialogs. The plan suggests YAML (`tests/fixtures/subrogation.yaml`).
- **Coverage gate is `--cov-fail-under=80`**, currently at 96.45%. Phase 3A's intake agent will initially drop coverage if you write lots of new code without tests. Add tests as you go.
- **Schema-plan reconciliation decisions from Phase 2A are still load-bearing** (see the Phase 2A section below). Do not change the `DataReport` status interpretations without updating the data agent's Phase 2A tests.
- **README.md at repo root is minimal** and points to the architecture plan. Do not treat it as authoritative — `docs/planning/architecture-plan.md` wins on conflicts.
- **QC "PASSED/FAILED" is still a coarse proxy** in the data agent (≥1 row = PASSED). Explicit future work for Phase 6 hardening. Not blocking for Phase 3.
- **`packages/data-agent/USAGE.md` is the standalone's README.** It's registered in its `pyproject.toml` as `readme = "USAGE.md"`. If you rename or delete it, `uv sync` fails on the workspace build.
- **The `--fake-llm` CLI flag is a CI escape hatch, not user-facing.** It is visible in `--help` but documented in USAGE.md as "smoke-test only". The intake agent should have an equivalent for its fixture-mode interview (the plan already requires fixture mode, so this is natural).

### How You Will Be Evaluated
Your handoff will be scored on:
1. Was the ACTIVE TASK block sufficient to orient the next session?
2. Did you verify the LangGraph interrupt pattern on a toy graph BEFORE writing real code? (If this is still unverified after your session, that's a protocol violation — Session 4 flagged it; Session 5 didn't need it; Session 6 must.)
3. Did you preserve the data-agent/intake decoupling symmetry? The intake agent should not import anything from `model_project_constructor_data_agent` or the Phase 2B shims.
4. Are key files listed with file:line references?
5. Did you complete Phase 3A as defined, or did you bundle 3B (Web UI)?
6. Were the Phase 2A + 2B gotchas preserved for Session 7 without dilution?

---

*Session history accumulates below this line. Newest session at the top.*

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
