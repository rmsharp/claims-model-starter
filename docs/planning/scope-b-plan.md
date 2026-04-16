# Scope B Plan — Real LLM-Backed Intake + Data Agents

> **Status:** Draft for executor review (Session 23 of project, planning workstream).
> **Author:** Session 23 — 2026-04-16.
> **Implements:** BACKLOG.md "Up Next" item #1.
> **Predecessor:** Scope A (Session 22) — proved the live website stage works against public GitLab. Real project at `https://gitlab.com/rmsharp-modelpilot/subrogation-pilot`.
> **Out of scope:** anything that is NOT wiring real `Anthropic`-backed intake/data runners into `run_pipeline`. See §14.

---

## 1. Context

### 1.1 What "Scope B" means

`scripts/run_pipeline.py:201-206` currently stubs the intake and data stages with constant lambdas:

```python
intake_runner = instrument(
    lambda: intake, name="intake", config=config, metrics=metrics,
)
data_runner = instrument(
    lambda _req: data, name="data", config=config, metrics=metrics,
)
```

`intake` and `data` come from fixture JSON loaded at line 176-177 (`subrogation_intake.json`, `sample_datareport.json`). **Nothing runs the LLM.** Scope A was sufficient to prove the website-stage live path; it did not prove that the real `IntakeAgent` and `DataAgent` produce reports the pipeline can consume end-to-end.

Scope B replaces those two lambdas with real LangGraph runners backed by `AnthropicLLMClient`. The website stage is unchanged from Scope A.

### 1.2 What success looks like

A live invocation that:

1. Drives a real Claude-backed intake interview producing a validated `IntakeReport`,
2. Hands the report to a real Claude-backed data agent that produces a validated `DataReport`,
3. Feeds both into the existing live website stage that creates a real GitLab/GitHub project.

Per the architecture plan §4.2 and §12, every error path returns a typed report with a non-`COMPLETE` status; the orchestrator halts at the first such status with a `FAILED_AT_*` `PipelineStatus`.

### 1.3 What Scope B does NOT do

- Does not add resume-from-checkpoint logic. Manual re-run with the same `run_id` continues to be the recovery path (per `OPERATIONS.md` §5).
- Does not change agent prompts, the intake graph, or the data agent graph — only the runner-level wiring.
- Does not add a new public CLI entry point. `scripts/run_pipeline.py` stays canonical.
- Does not rewrite the broken `OPERATIONS.md` §4.2/4.3 — that is BACKLOG item #6 and is a separate one-session deliverable.
- Does not extend CI to include a live-LLM smoke test. Live invocations remain operator-driven.

---

## 2. Glossary

| Term | Meaning |
|---|---|
| **Runner** | A `Callable` matching one of the three orchestrator type aliases at `pipeline.py:41-43`. |
| **Agent** | A class (`IntakeAgent`, `DataAgent`, `WebsiteAgent`) wrapping a compiled LangGraph. |
| **LLM client** | A protocol-typed object that issues Claude API calls (`IntakeLLMClient`, `LLMClient`). `AnthropicLLMClient` is the production impl in both packages. |
| **Fixture-mode** | Run an agent with a `FixtureLLMClient` / fake LLM — no Anthropic calls, fully deterministic. |
| **Scripted-answers mode** | Drive the *real* `AnthropicLLMClient` for question generation, but feed pre-recorded *answers* into the graph's `ask_user` interrupts. Asymmetric: questions are real, answers are canned. |
| **Interactive mode** | Real LLM + real human typing answers. Today only the Phase 3B Web UI provides this. |
| **Stage** | One of `intake` / `data` / `website` in the orchestrator's halt vocabulary (`PipelineStatus` literal at `pipeline.py:45-50`). |

---

## 3. Evidence-based inventory

Per the planning workstream rules (`SESSION_RUNNER.md:97-104`), every claim about the codebase below is anchored to a grep result or a line-level reference. The executor should re-run these greps before starting — symbols may have moved.

### 3.1 Orchestrator runner contract

**Source of truth:** `src/model_project_constructor/orchestrator/pipeline.py:41-43`

```python
IntakeRunner = Callable[[], IntakeReport]
DataRunner = Callable[[DataRequest], DataReport]
WebsiteRunner = Callable[[IntakeReport, DataReport, RepoTarget], RepoProjectResult]
```

These aliases are re-exported through `orchestrator/__init__.py:42-46` and consumed by `run_pipeline(...)` at `pipeline.py:97-104`. They are the contract Scope B must satisfy.

**Grep:** `IntakeRunner|DataRunner|WebsiteRunner` — 11 matches across `pipeline.py` (definitions + uses), `orchestrator/__init__.py` (re-exports + `__all__`), `scripts/run_pipeline.py:93` (in a docstring), and 3 references in docs (`SESSION_NOTES.md`, `Extending-the-Pipeline.md`).

**Implication:** No call site uses the type alias directly outside the orchestrator package. Adding new runners (real LLM-backed) is a wiring change in `scripts/run_pipeline.py` only.

### 3.2 Existing call sites of `run_pipeline(`

**Grep:** `run_pipeline\(` — 16 matches across:

- `src/model_project_constructor/orchestrator/pipeline.py:97` — the definition.
- `scripts/run_pipeline.py:214` — the only production call site (the rest are docs and tests).
- `tests/orchestrator/test_pipeline.py` — 9 test call sites, all stub all three runners with lambdas.
- `tests/orchestrator/test_metrics.py:246` — one wrapped-runner test.
- `OPERATIONS.md:144`, `TROUBLESHOOTING.md:112,165`, `docs/tutorial.md:423`, `README.md:74`, `docs/planning/architecture-plan.md:747,932`, `docs/wiki/.../Extending-the-Pipeline.md:67`, `docs/wiki/.../Changelog.md:44`, `docs/planning/pilot-readiness-audit.md:264` — documentation and references.

**Implication:** `scripts/run_pipeline.py` is the *single* production call site. The plan's surface area is bounded.

### 3.3 IntakeAgent constructor sites

**Grep:** `IntakeAgent\(` — 6 matches:

| File:Line | Use | Notes |
|---|---|---|
| `src/model_project_constructor/agents/intake/cli.py:76` | `IntakeAgent(llm=_DummyLLM())` | Phase 3A CLI; `_DummyLLM` is replaced inside `run_with_fixture`. |
| `tests/agents/intake/test_graph.py:25,94,109` | `IntakeAgent(llm=FixtureLLMClient(fixture))` | All test wiring is fixture-driven. |
| `docs/wiki/.../Agent-Reference.md:63` | `IntakeAgent().run(config)` | DOC IS WRONG — `IntakeAgent` requires `llm` and has no `.run(config)` method. |
| `docs/wiki/.../Intake-Interview-Design.md:238` | `IntakeAgent(AnthropicLLMClient())` | The closest thing to a Scope B example, but only documents the constructor — no driver method shown. |

**Implication:** No production code instantiates `IntakeAgent` with a real `AnthropicLLMClient` and runs it. Scope B is the first to do so.

### 3.4 DataAgent constructor sites

**Grep:** `DataAgent\(` — 13 matches:

| File:Line | Use |
|---|---|
| `packages/data-agent/src/.../cli.py:104` | `DataAgent(llm=llm, db=db)` — the standalone CLI; `llm` is `AnthropicLLMClient` or `_FakeCLIClient` |
| `tests/agents/data/test_data_agent.py` (×8) | `DataAgent(llm=fake, db=...)` — all fake-LLM test wiring |
| `packages/data-agent/USAGE.md:11,100,157` | Documentation examples |
| `docs/wiki/.../Data-Guide.md:96`, `Agent-Reference.md:124` | `DataAgent().run(...)` — docs are wrong (constructor requires `llm`) |

**Implication:** The `data-agent` standalone CLI already wires `DataAgent(AnthropicLLMClient(), db=...)` correctly at `cli.py:104`. Scope B can mimic this pattern verbatim.

### 3.5 AnthropicLLMClient instantiation

**Grep:** `AnthropicLLMClient` — 39 matches across both packages, tests, docs, and the UI. Two production-relevant instantiation sites:

- `packages/data-agent/src/.../cli.py:119` — `return AnthropicLLMClient(model=model)` (data agent CLI)
- `src/model_project_constructor/ui/intake/app.py:60` — `return AnthropicLLMClient()` (Web UI factory)

**Implication:** Both packages already have a production code path that constructs `AnthropicLLMClient` from `ANTHROPIC_API_KEY`. The pattern Scope B needs already exists; it just hasn't been wired into `scripts/run_pipeline.py`.

### 3.6 IntakeAgent runner methods

`src/model_project_constructor/agents/intake/agent.py` defines two driver methods on the facade:

- `run_scripted(*, stakeholder_id, session_id, interview_answers, review_responses, domain="pc_claims", initial_problem=None) -> IntakeReport` (lines 48-125)
- `run_with_fixture(fixture_path: str) -> IntakeReport` (lines 127-141)

The docstring at line 7-12 explicitly notes: *"The graph itself is generic: Phase 3B can reuse `build_intake_graph` and drive it from a Web UI instead. The facade below is specifically the headless / fixture driver."*

**Critical gap:** Neither method matches the orchestrator's `IntakeRunner = Callable[[], IntakeReport]` shape. `run_scripted` requires answer/review lists; `run_with_fixture` requires a fixture path. A bare-arg adapter (closure) is needed.

**Critical safety gap:** `run_scripted` raises `RuntimeError` on under-supplied scripts and on max-turn overflow (lines 100-104, 116-120). `DataAgent.run` does NOT raise — it always returns a typed report (see `agent.py:50-61`). The intake adapter must catch and convert exceptions to a `DRAFT_INCOMPLETE` `IntakeReport`, otherwise the orchestrator's `make_logged_runner` will see an exception and the pipeline will crash instead of halting cleanly with `FAILED_AT_INTAKE`.

### 3.7 DataAgent runner method

`packages/data-agent/.../agent.py:40` already declares:

```python
def run(self, request: DataRequest) -> DataReport:
```

This **exactly matches** `DataRunner = Callable[[DataRequest], DataReport]`. No adapter needed:

```python
data_runner = DataAgent(AnthropicLLMClient(model=...), db=db_or_none).run
```

The internal `try/except` at `agent.py:50-53` and the helpers `_incomplete_report` / `_execution_failed_report` (lines 84-110) guarantee `run` never raises for expected failures. Scope B can rely on this.

### 3.8 LLM provider-specific clients are already idempotent

`AnthropicLLMClient.__init__` in both packages accepts `client: Any | None = None`; when `None`, it lazy-imports `anthropic` and constructs `Anthropic()` which reads `ANTHROPIC_API_KEY` from the environment (`anthropic_client.py:62-66` in both packages). Scope B does NOT need to plumb the API key explicitly — the `.env` populated by Session 22 already exports it.

### 3.9 OPERATIONS.md §4.2/4.3 references a non-existent entry point

**Grep:** `agents/website/__main__.py` and `agents/website/cli.py` — **0 files exist**. The OPERATIONS.md documented invocation `python -m model_project_constructor.agents.website --intake intake.json --data data.json --host gitlab ...` does not work. This is BACKLOG item #6, NOT a Scope B concern, but the plan must avoid documenting that invocation.

### 3.10 Fixture format for scripted intake

`src/model_project_constructor/agents/intake/fixture.py:9-45` documents the YAML schema (`intake_fixture/v1`). The shipped fixtures are `tests/fixtures/subrogation.yaml` (and 6 others — see `tests/fixtures/intake_fixtures/` per the wiki Worked-Examples page). For a scripted intake mode that uses a *real* LLM but pre-scripted answers, only the `qa_pairs[*].answer` field would be consumed; the LLM generates its own questions live.

### 3.11 Failure-mode surface for the Anthropic SDK

The intake side raises `IntakeLLMError` (`anthropic_client.py:86-88, 116-118, 134-136, 152-154`) on bad JSON; the data side raises `LLMParseError` (`anthropic_client.py:94, 130, 169, 199`). Both inherit from `RuntimeError`/`ValueError` and propagate up. The `anthropic` SDK itself raises:

- `anthropic.RateLimitError` — 429
- `anthropic.APIError` / `APIConnectionError` — network
- `anthropic.AuthenticationError` — 401
- `anthropic.BadRequestError` — 400

These propagate UNCAUGHT in the intake graph node call paths. **DataAgent catches everything** at `agent.py:52` — so data is safe. **IntakeAgent does NOT catch** — so a rate limit in the middle of an interview will crash the graph and propagate up through `run_scripted`. Scope B must wrap.

---

## 4. Current state vs. target state

### 4.1 What changes

Only `scripts/run_pipeline.py`. Specifically:

- Lines 195-209 (the runner-wiring block) will gain two new branches alongside the current "fake intake/data" branch.
- A new CLI flag `--llm` (with values `none`, `data`, `both`) selects which stages use real Anthropic.
- Two new helpers (`build_intake_runner`, `build_data_runner`) parallel the existing `build_website_runner`.

### 4.2 What does NOT change

- `pipeline.py` — runner contract is satisfied by closures, no API change needed.
- `IntakeAgent`, `DataAgent`, the graphs, the prompts, the LLM clients.
- Tests — the orchestrator test suite continues to use stub lambdas. New live wiring is not unit-tested (live LLM = not deterministic = not a unit-test).
- CI — live runs stay operator-driven.

### 4.3 The wiring (in pseudocode)

```python
# Today (Scope A):
intake_runner = instrument(lambda: intake, name="intake", ...)
data_runner   = instrument(lambda _req: data, name="data", ...)

# Scope B target:
intake_runner = instrument(
    build_intake_runner(args.llm, args.intake_fixture),  # closure
    name="intake", ...
)
data_runner = instrument(
    build_data_runner(args.llm, args.db_url),            # method bound to instance
    name="data", ...
)
```

`build_intake_runner` returns one of three closures depending on `--llm`:

- `"none"` — `lambda: load_intake_fixture()` (current Scope A behavior)
- `"data"` — same as `"none"` (intake stays fixture)
- `"both"` — `lambda: _drive_intake_with_real_llm(args.intake_fixture)` (see §5)

`build_data_runner` is simpler:

- `"none"` — `lambda _req: load_data_fixture()` (current Scope A behavior)
- `"data"` or `"both"` — `DataAgent(AnthropicLLMClient(model=...), db=...).run`

---

## 5. Three implementation shapes for the intake side

The data side is mechanical (§4.3). The intake side has three legitimate shapes; Scope B must pick one (or sequence them).

### Shape I-1: Fixture intake (no real LLM at intake)

**What:** `--llm data` mode. Intake stays fixture-driven; only the data agent uses real Claude.
**Pros:** Deterministic intake; only one LLM stage in the loop; fastest path to "first real Claude run end-to-end."
**Cons:** Doesn't actually exercise the intake LLM client against a live API in the pipeline.
**When:** Always — this is the lowest-risk first milestone (Phase B1 below).

### Shape I-2: Scripted-answers intake with real LLM questioner

**What:** `--llm both --intake-fixture path/to/sub.yaml` mode. The fixture supplies *answers* (and an `initial_problem`); the real `AnthropicLLMClient` generates *questions* and the *draft*. `IntakeAgent.run_scripted(...)` already supports this — no agent changes needed.

**Pros:**
- Exercises real prompts, real JSON parsing, real governance classification.
- Asymmetric drift detection: if Claude's questions diverge from the fixture's answers, the report quality degrades visibly.
- Works in a non-interactive script — fits `scripts/run_pipeline.py` model.

**Cons:**
- Asymmetric: real LLM gets canned answers it didn't ask for. Surreal but operationally fine for smoke testing.
- A run can fail mid-interview if Claude asks a question the fixture has no answer for and the script runs out before the LLM flips `believe_enough_info=true`. The `RuntimeError` raised at `agent.py:100-104` must be caught and converted to a `DRAFT_INCOMPLETE` report (see §3.6).

**When:** Phase B2 — second milestone, after B1 proves real-data works.

### Shape I-3: Web UI intake + orchestrator pickup

**What:** Operator runs the intake Web UI separately (Phase 3B), interactively conducts the interview, then `scripts/run_pipeline.py --resume-intake <session_id>` reads the produced `IntakeReport` from the SQLite session DB and feeds it to the pipeline.

**Pros:**
- True end-to-end Scope B: real LLM + real human + real data + real website.
- Closest to the eventual production shape (`go/modelintake` per `initial_purpose.txt`).

**Cons:**
- Two-process workflow; not driven by a single `scripts/run_pipeline.py` invocation.
- Requires new glue: a function that pulls the latest `IntakeReport` for a `session_id` out of the intake's `SqliteSaver`-backed state.
- The intake UI's `IntakeSessionStore._snapshot` (`ui/intake/runner.py:113-164`) already builds an `IntakeReport` on `phase="complete"` — the glue is small but real.

**When:** Phase B3 — third milestone, after B2. May or may not be in scope at all (see §8 Open Decisions).

### Shape comparison

| | I-1 (Fixture) | I-2 (Scripted) | I-3 (Web UI) |
|---|---|---|---|
| Real intake LLM | ❌ | ✅ | ✅ |
| Real data LLM | ✅ | ✅ | ✅ |
| Single-process | ✅ | ✅ | ❌ |
| Interactive | ❌ | ❌ | ✅ |
| New code in `scripts/run_pipeline.py` | small | medium | medium |
| New code outside `scripts/` | none | small (RuntimeError → DRAFT_INCOMPLETE adapter) | small (UI → orchestrator session bridge) |
| Cost per run (USD, rough) | ~$0.05–0.20 (data only) | ~$0.10–0.40 (intake + data) | ~$0.10–0.40 (intake + data) |
| Sessions to implement | 1 (Phase B1) | 1 (Phase B2) | 1–2 (Phase B3) |

**Recommendation:** Sequence B1 → B2 → optionally B3. Each is a single session. Each phase's commit + close-out is independent.

---

## 6. Recommended sequence

### Phase B1 — Real data agent only

**Goal:** First end-to-end live run where the data agent uses real Anthropic. Intake stays fixture-driven.

**Why first:** The `DataAgent.run` shape already matches `DataRunner` exactly (§3.7). The `data-agent` CLI already does this wiring (§3.4). Risk is bounded to "does Claude produce parseable SQL on the subrogation request."

### Phase B2 — Scripted-answers intake

**Goal:** Add `--llm both` driving `IntakeAgent.run_scripted` with fixture-supplied answers and real Claude-generated questions/drafts.

**Why second:** Builds on B1's CLI surface; touches only intake-side wiring. Adds the `RuntimeError → DRAFT_INCOMPLETE` adapter required by §3.6.

### Phase B3 — Web UI bridge (OPTIONAL — needs user decision)

**Goal:** `scripts/run_pipeline.py --resume-intake <session_id>` reads the completed `IntakeReport` from the intake UI's SQLite store and uses it as the intake stage.

**Why optional:** This shape is closer to production but introduces a multi-process workflow. Skip if BACKLOG item #7 (resume-from-checkpoint) lands first — the resume mechanism would supersede the bespoke "pick up the last intake" glue with a general resume path.

---

## 7. Per-phase implementation plan

### 7.1 Phase B1 — Real data agent

#### 7.1.1 Files to change

| File | Change | LOC est. |
|---|---|---|
| `scripts/run_pipeline.py` | Add `--llm {none,data,both}` flag (default `none`); add `--db-url` flag (mirror data CLI); add `build_data_runner(llm, db_url)` helper; replace `lambda _req: data` with the helper's return value when `--llm in {data,both}`. | +30 / -2 |
| `OPERATIONS.md` | Add §4.4 documenting `scripts/run_pipeline.py --live --host gitlab --llm data` as the Scope B-1 invocation. | +25 |
| `docs/tutorial.md` | Add §6 "Step 6: Real LLM-backed run" after §5; cross-reference OPERATIONS §4.4. | +30 |
| `CHANGELOG.md` | `[Unreleased]` entry: "feat(scope-b1): wire real Anthropic data agent into run_pipeline." | +5 |
| `BACKLOG.md` | Mark BACKLOG #1 "Scope B-1" complete; note B2/B3 still open. | +5 / -3 |

#### 7.1.2 Wiring

```python
# in scripts/run_pipeline.py

def build_data_runner(*, llm_mode: str, db_url: str | None):
    """Return a DataRunner. Fixture mode in 'none', real Anthropic otherwise."""
    if llm_mode == "none":
        data = load_data_fixture()
        return lambda _req: data

    # llm_mode in {"data", "both"} — real Anthropic
    from model_project_constructor_data_agent.agent import DataAgent
    from model_project_constructor_data_agent.anthropic_client import (
        AnthropicLLMClient,
    )
    from model_project_constructor_data_agent.db import ReadOnlyDB

    llm = AnthropicLLMClient()  # reads ANTHROPIC_API_KEY
    db = ReadOnlyDB(db_url) if db_url else None
    return DataAgent(llm=llm, db=db).run
```

#### 7.1.3 Per-phase completion criteria

**What DONE looks like:**

1. `uv run python scripts/run_pipeline.py --live --host gitlab --llm data --run-id run_b1_001` produces a `COMPLETE` `PipelineResult` against a real Claude API (intake fixture, real data LLM, real GitLab project).
2. `.orchestrator/checkpoints/run_b1_001/DataReport.json` envelope's payload has `status: "COMPLETE"` and at least one primary query whose `sql` is *different* from the fixture's `sample_datareport.json` SQL (proves Claude actually ran; not a re-emission of the fixture).
3. `--llm none` invocation continues to produce identical output to Scope A.
4. Test suite stays green: `uv run pytest -q` → 422/422 (no new tests required for B1; live-LLM is not unit-tested).
5. CI lint + typecheck stay green: `uv run ruff check src/ tests/ packages/` + `uv run mypy src/`.

**Verification commands:**

```bash
# baseline (Scope A) — must still pass
uv run python scripts/run_pipeline.py --run-id run_b1_pre

# B1 fake mode — must equal baseline
uv run python scripts/run_pipeline.py --llm none --run-id run_b1_fake

# B1 live mode — must produce COMPLETE
set -a; source .env; set +a
uv run python scripts/run_pipeline.py --live --host gitlab --llm data \
    --run-id run_b1_live

# Inspect the data envelope to confirm real LLM output
python -c "
from pathlib import Path
import json
env = json.loads(Path('.orchestrator/checkpoints/run_b1_live/DataReport.json').read_text())
report = env['payload']
print('status:', report['status'])
print('queries:', len(report['primary_queries']))
print('sql_0_first_80:', report['primary_queries'][0]['sql'][:80])
"
```

**Session boundary:** Phase B1 is one session. Close out when the live `run_b1_live` produces `COMPLETE`. Do not start B2 in the same session.

#### 7.1.4 Cost estimate

Per-run Claude cost for the data side (sonnet-4-6 pricing as of 2026-04-16 — verify before invoicing):

- `generate_primary_queries`: ~1500 input + ~600 output tokens
- `generate_quality_checks`: ~2000 input + ~1200 output tokens
- `summarize`: ~1500 input + ~400 output tokens
- `generate_datasheet`: ~1000 input + ~800 output tokens × N primary queries (typically N=1, sometimes 2)

Total: ~7,000 input + ~4,000 output tokens ≈ **$0.05–0.10 per run** at sonnet-4-6 list rates.

### 7.2 Phase B2 — Scripted-answers intake

#### 7.2.1 Files to change

| File | Change | LOC est. |
|---|---|---|
| `scripts/run_pipeline.py` | Add `--intake-fixture path/to/sub.yaml` flag; add `build_intake_runner(llm_mode, fixture_path)` helper; activate when `--llm both`. | +35 / 0 |
| `src/model_project_constructor/agents/intake/agent.py` | Add `run_scripted_safely(...) -> IntakeReport` that wraps `run_scripted` and converts `RuntimeError` → `IntakeReport` with `status="DRAFT_INCOMPLETE"` and a `missing_fields` entry naming the failure. Or: add this adapter inside `scripts/run_pipeline.py` only. **Pick one — see §8.4.** | +25 |
| `OPERATIONS.md` | Extend §4.4 with the `--llm both --intake-fixture ...` invocation. | +15 |
| `docs/tutorial.md` | Extend §6 with the scripted-intake recipe. | +15 |
| `CHANGELOG.md` | `[Unreleased]` entry: "feat(scope-b2): scripted-answers intake with real Anthropic." | +5 |
| `BACKLOG.md` | Mark Scope B-2 complete. | +2 / -2 |

#### 7.2.2 Wiring

```python
# in scripts/run_pipeline.py (or agents/intake/agent.py per §8.4)

def build_intake_runner(*, llm_mode: str, fixture_path: str | None):
    """Return an IntakeRunner. Fixture-only in 'none' or 'data'; scripted in 'both'."""
    if llm_mode in ("none", "data"):
        intake = load_intake_fixture()
        return lambda: intake

    # llm_mode == "both" — scripted answers, real LLM
    if fixture_path is None:
        raise SystemExit("--llm both requires --intake-fixture")

    from model_project_constructor.agents.intake.agent import IntakeAgent
    from model_project_constructor.agents.intake.anthropic_client import (
        AnthropicLLMClient,
    )
    from model_project_constructor.agents.intake.fixture import (
        answers_from_fixture, load_fixture, review_sequence_from_fixture,
    )

    fixture = load_fixture(fixture_path)
    llm = AnthropicLLMClient()  # reads ANTHROPIC_API_KEY
    agent = IntakeAgent(llm=llm)

    def runner() -> IntakeReport:
        try:
            return agent.run_scripted(
                stakeholder_id=fixture["stakeholder_id"],
                session_id=fixture["session_id"],
                domain=fixture.get("domain", "pc_claims"),
                initial_problem=fixture.get("initial_problem"),
                interview_answers=answers_from_fixture(fixture),
                review_responses=review_sequence_from_fixture(fixture),
            )
        except RuntimeError as exc:
            # The script ran out of answers OR the graph exceeded max turns.
            # Convert to a DRAFT_INCOMPLETE report so the orchestrator halts
            # with FAILED_AT_INTAKE instead of crashing.
            return _draft_incomplete_from_exception(exc)
        except Exception as exc:  # Anthropic SDK errors, parse errors, etc.
            return _draft_incomplete_from_exception(exc)

    return runner
```

`_draft_incomplete_from_exception` builds a minimal `IntakeReport` with `status="DRAFT_INCOMPLETE"`, `missing_fields=["interview_aborted: <type(exc).__name__>"]`, and stub values for required prose fields. The orchestrator's `FAILED_AT_INTAKE` path at `pipeline.py:127-136` already handles this cleanly.

#### 7.2.3 Per-phase completion criteria

**What DONE looks like:**

1. `uv run python scripts/run_pipeline.py --live --host gitlab --llm both --intake-fixture tests/fixtures/subrogation.yaml --run-id run_b2_001` produces a `COMPLETE` `PipelineResult`.
2. The intake envelope at `.orchestrator/checkpoints/run_b2_001/IntakeReport.json` has a `business_problem` field that is *not* identical to `subrogation_intake.json` (proving Claude drafted, not the fixture).
3. A failure-injection test: invoke with a fixture that has only 1 `qa_pairs` entry but `draft_after: 99` — the run halts at `FAILED_AT_INTAKE`, not crashes. Verify with: `python -c "from pathlib import Path; import json; print(json.loads(Path('.orchestrator/checkpoints/run_b2_fail/IntakeReport.json').read_text())['payload']['status'])"` → `DRAFT_INCOMPLETE`.
4. `--llm none` and `--llm data` continue to produce Scope A / Scope B-1 behavior respectively.

**Verification commands:**

```bash
set -a; source .env; set +a

# Happy path
uv run python scripts/run_pipeline.py --live --host gitlab --llm both \
    --intake-fixture tests/fixtures/subrogation.yaml --run-id run_b2_live

# Failure injection — needs a small fixture with insufficient qa_pairs
uv run python scripts/run_pipeline.py --live --host gitlab --llm both \
    --intake-fixture tests/fixtures/_b2_failmode.yaml --run-id run_b2_fail
# Must exit non-zero with FAILED_AT_INTAKE (not a Python traceback).
```

**Session boundary:** Phase B2 is one session. Close out when both happy-path and failure-injection invocations behave correctly.

#### 7.2.4 Cost estimate

Per-run intake cost adds:
- `next_question` × ~6–10 calls (one per question; cap at MAX_QUESTIONS=10)
- `draft_report` × 1
- `classify_governance` × 1
- `revise_report` × 0–3 (cap at MAX_REVISIONS=3; usually 0 with `ACCEPT` review)

Roughly: ~10,000 input + ~3,000 output tokens ≈ **$0.05–0.10 per run** added on top of the data side. Combined B2 run: **$0.10–0.20**.

### 7.3 Phase B3 — Web UI bridge (OPTIONAL — defer pending §8 decision)

#### 7.3.1 Files to change

| File | Change | LOC est. |
|---|---|---|
| `scripts/run_pipeline.py` | Add `--resume-intake <session_id> --intake-db <path>` flags; add `build_intake_runner_from_ui(session_id, db_path)` helper. | +40 |
| `src/model_project_constructor/ui/intake/runner.py` | Add `IntakeSessionStore.load_completed_report(session_id) -> IntakeReport \| None` that returns the validated report iff `phase=="complete"`. | +20 |
| `tests/ui/intake/test_runner.py` | Add a test for `load_completed_report` covering the happy path and `phase != "complete"`. | +30 |
| `OPERATIONS.md` | Add §4.5 documenting the two-step workflow. | +20 |
| `docs/tutorial.md` | Add §7 "Step 7: Production-shape intake (Web UI)". | +25 |
| `CHANGELOG.md` | Entry. | +3 |

#### 7.3.2 Wiring

The orchestrator's intake runner becomes:

```python
def build_intake_runner_from_ui(session_id: str, db_path: str):
    from model_project_constructor.ui.intake.runner import IntakeSessionStore
    # The UI uses an LLMFactory; for read-only loading we don't need it.
    store = IntakeSessionStore(db_path=db_path, llm_factory=lambda _sid: _NullLLM())
    report = store.load_completed_report(session_id)
    if report is None:
        raise SystemExit(f"Intake session {session_id!r} is not complete")
    store.close()
    return lambda: report
```

`_NullLLM` is a no-op `IntakeLLMClient` whose methods raise — they're never called because the graph's state is loaded from SQLite and is already at `phase="complete"`.

#### 7.3.3 Per-phase completion criteria

**What DONE looks like:**

1. Operator runs the intake UI (`uv run uvicorn model_project_constructor.ui.intake.app:app`), conducts an interview to completion, notes the `session_id`.
2. `uv run python scripts/run_pipeline.py --live --host gitlab --llm data --resume-intake <session_id> --intake-db ./intake_sessions.db --run-id run_b3_live` produces `COMPLETE`.
3. The intake envelope's `IntakeReport` matches the report the UI displayed at the end of the interview (deep-equal on `model_dump()`).
4. New unit test `tests/ui/intake/test_runner.py::test_load_completed_report` passes.

**Verification commands:** as 7.3.3.1 above; tests via `uv run pytest tests/ui/intake/test_runner.py -q`.

**Session boundary:** Phase B3 is one session. Close out when the round-trip works.

#### 7.3.4 Cost estimate

Same as B2 (intake interview cost, paid in the UI session) plus the data side. Total: **$0.10–0.20**.

---

## 8. Open decisions for the user (resolve before Phase B1)

These are not implementation details — they are choices the user must make. List the decision, the options, the recommendation, and the consequence.

### 8.1 Should the data agent's database be wired to a live SQL store, or stay disconnected?

**Options:**
- (a) **Disconnected** (`db=None`) — Data agent generates queries and quality checks, but does not execute them. The `DataReport`'s `data_quality_concerns` will include the standard "database unreachable at QC execution time" line. Matches Scope A's current behavior.
- (b) **Live read-only** — Provide `--db-url sqlite:///path` or a Postgres URL. Quality checks execute, expectations get confirmed/rejected based on real query results.

**Recommendation:** **(a) for B1 and B2.** The pilot's purpose is to prove the LLM-driven query generation works; introducing a live DB doubles the failure surface. (b) is a separate post-pilot step.

**Consequence of (b) chosen:** Need a seeded test DB (the data-agent CLI already supports SQLite — see `cli.py:79-86`). Adds DB setup to the operator runbook.

### 8.2 Which model ID for both stages?

**Options:**
- (a) `claude-sonnet-4-6` — current default in both `AnthropicLLMClient`s. Cheap, fast.
- (b) `claude-opus-4-7` — best quality, slower, more expensive.
- (c) `claude-haiku-4-5-20251001` — cheapest, fastest, may be insufficient for governance classification nuance.

**Recommendation:** **(a) for B1.** Defer the model-quality conversation to after the first real run produces output we can judge.

**Consequence:** The plan's cost estimates assume sonnet-4-6. Override via `--model` flag (data CLI already supports it; intake side must add it in B2).

### 8.3 Is Phase B3 in scope at all?

**Options:**
- (a) **In scope** — implement after B2. Adds the production-shape Web-UI-driven intake.
- (b) **Out of scope** — Scope B is just B1 + B2. The Web UI continues to exist standalone; the pipeline never reads from its SQLite store. BACKLOG-#7 (resume-from-checkpoint) is the alternate path to "pick up where you left off."

**Recommendation:** **(b) — out of scope** unless the user expressly wants a production-shape demo. B1 + B2 already prove "real Anthropic intake + data + live host." B3 is more of a workflow integration than a Scope-B requirement.

**Consequence of (a):** +1 session, more code to maintain. The bridge is small but real (§7.3).

### 8.4 Where does the `RuntimeError → DRAFT_INCOMPLETE` adapter live?

**Options:**
- (a) **Inside `scripts/run_pipeline.py`** as a private helper. Pros: keeps `agent.py` untouched; the wrap is a wiring concern. Cons: boilerplate at the call site; future callers reinvent the wrap.
- (b) **As a new method on `IntakeAgent` (`run_scripted_safely`)**. Pros: reusable; future callers get safe behavior by default. Cons: adds a public method for a one-caller use case; future callers may misuse.

**Recommendation:** **(a) for B2.** Premature abstraction is the larger risk; if a second caller appears, refactor to (b) then.

### 8.5 Should the `--llm` flag accept `intake` (real intake, fake data)?

**Options:**
- (a) **No** — only `none` / `data` / `both`. Three modes is enough.
- (b) **Yes** — symmetric four-mode flag (`none` / `intake` / `data` / `both`).

**Recommendation:** **(a)**. Real intake without real data has no operational use case (the data report's queries depend on the intake's `target_variable` / `candidate_features`; if the data side is fixture, the queries are decoupled from the live intake and the run becomes confusing to read).

---

## 9. Failure-mode handling

| Failure | Surfaces in | Caught by | Result |
|---|---|---|---|
| `anthropic.RateLimitError` (429) on intake | Inside `next_question` / `draft_report` / etc. | B2's adapter (§7.2.2) | `IntakeReport(status="DRAFT_INCOMPLETE", missing_fields=["interview_aborted: RateLimitError"])` → `FAILED_AT_INTAKE` |
| `anthropic.RateLimitError` on data | Inside `_call_claude` | `DataAgent.run`'s outer try/except (`agent.py:50-53`) | `DataReport(status="EXECUTION_FAILED", data_quality_concerns=["graph crashed: RateLimitError ..."])` → `FAILED_AT_DATA` |
| `IntakeLLMError` (bad JSON from LLM) | Inside intake graph node | Same as rate limit | Same |
| `LLMParseError` (bad JSON, data side) | Inside data graph node | Same as data rate limit | Same |
| Pydantic validation error on `IntakeReport.model_validate(...)` | `build_intake_report` at `nodes.py` | NOT currently caught | Crashes the pipeline. **B2 must add to the adapter's `except Exception`.** |
| `RuntimeError("Fixture ran out of answers")` | `agent.py:100-104` | B2's adapter | Same as B2 rate limit |
| `RuntimeError("Intake graph exceeded max turns")` | `agent.py:117-120` | B2's adapter | Same |
| Network timeout | SDK | Same as rate limit (typed as `APIConnectionError`) | Same |
| `MPC_NAMESPACE` is a URL not a path | `OrchestratorSettings.from_env()` | NO validation today (BACKLOG #2) | Surfaces as `404` from the host adapter. Independent of Scope B. |

**Critical contract:** Both runners must always return a typed report, never raise. The orchestrator at `pipeline.py:127-136, 161-169` halts on non-`COMPLETE` status; an uncaught exception crashes the script and leaves no `PipelineResult` for the operator to inspect. The B2 adapter is the single most important new code in Scope B.

---

## 10. Checkpoint + resume strategy

`CheckpointStore` (`orchestrator/checkpoints.py:29-128`) already persists every inter-agent envelope and the terminal `RepoProjectResult`. Scope B does not change this layer.

**Partial-LLM resume recipe** (per `OPERATIONS.md` §5):

1. A run halts at `FAILED_AT_DATA` because Claude rate-limited on the 4th datasheet generation.
2. The operator reads `.orchestrator/checkpoints/<run_id>/IntakeReport.json` (from the envelope) — this is good.
3. The operator decides: rerun with the SAME `run_id` and a stub intake runner that returns the loaded report. Concretely, a one-off Python snippet:
   ```python
   from model_project_constructor.orchestrator import CheckpointStore, run_pipeline, ...
   store = CheckpointStore(".orchestrator/checkpoints")
   intake = store.load_payload("<run_id>", "IntakeReport")
   # ... build config with same run_id ...
   result = run_pipeline(config, intake_runner=lambda: intake, data_runner=DataAgent(...).run, ...)
   ```
4. Same `run_id` → checkpoint files overwrite cleanly (per `checkpoints.py:13`).

**Scope B does NOT add a CLI flag for this.** Adding `--resume-from-intake <run_id>` is BACKLOG #7's job and belongs in a separate plan. Documenting the manual recipe in OPERATIONS §4.4/4.5 is sufficient for pilot.

---

## 11. Test strategy

### 11.1 What is unit-tested

- Existing intake test suite (`tests/agents/intake/`, `tests/ui/intake/`) continues to pass — no changes to intake graph or LLM clients.
- Existing data agent suite (`tests/agents/data/`, `tests/data_agent_package/`) continues to pass.
- Existing orchestrator suite (`tests/orchestrator/`) continues to pass — runner contracts unchanged.
- B2 only: a new orchestrator-level test asserts that the `RuntimeError → DRAFT_INCOMPLETE` adapter (§7.2.2) produces a report whose `status == "DRAFT_INCOMPLETE"` when wrapped around a callable that raises. This test does NOT call Claude.

### 11.2 What is NOT unit-tested

- The live Claude wiring. Live LLM = non-deterministic = not a unit test. Verification is the operator-driven invocations in §7.1.3, §7.2.3, §7.3.3.
- The live GitLab/GitHub host. Same reasoning. Continues to be operator-driven (Scope A's pattern).

### 11.3 CI impact

**None.** Live runs stay out of CI. The new B1/B2 wiring only activates under `--llm data` / `--llm both`, both of which require `ANTHROPIC_API_KEY` and a live host token; CI sets neither.

---

## 12. Verification commands per phase (consolidated)

### B1
```bash
uv run pytest -q                                                # 422/422
uv run ruff check src/ tests/ packages/                         # clean
uv run mypy src/                                                # clean
set -a; source .env; set +a
uv run python scripts/run_pipeline.py --live --host gitlab \
    --llm data --run-id run_b1_live                             # COMPLETE
```

### B2
```bash
uv run pytest -q                                                # 423/423 (one new test)
uv run ruff check src/ tests/ packages/                         # clean
uv run mypy src/                                                # clean
set -a; source .env; set +a
uv run python scripts/run_pipeline.py --live --host gitlab \
    --llm both --intake-fixture tests/fixtures/subrogation.yaml \
    --run-id run_b2_live                                        # COMPLETE
uv run python scripts/run_pipeline.py --live --host gitlab \
    --llm both --intake-fixture tests/fixtures/_b2_failmode.yaml \
    --run-id run_b2_fail                                        # FAILED_AT_INTAKE
```

### B3 (if pursued)
```bash
uv run pytest -q                                                # 424/424 (B2 + load_completed_report)
# Operator runs the UI, conducts an interview, notes <session_id>:
uv run uvicorn model_project_constructor.ui.intake.app:app
# Then:
set -a; source .env; set +a
uv run python scripts/run_pipeline.py --live --host gitlab \
    --llm data --resume-intake <session_id> \
    --intake-db ./intake_sessions.db --run-id run_b3_live       # COMPLETE
```

---

## 13. Risks and mitigations

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| 1 | Claude rate-limits mid-run | Medium | One run aborts | B2 adapter (§7.2.2) converts to `FAILED_AT_INTAKE` / `FAILED_AT_DATA`. Operator re-runs after backoff. |
| 2 | Real LLM produces SQL that `sqlparse` rejects | Medium | `EXECUTION_FAILED` data report | The data agent already has a `RETRY_ONCE` branch (`agent.py` graph wiring). After 1 retry it gives up — operator inspects + chooses to re-run. |
| 3 | `subrogation.yaml` answers cause the LLM to run past `MAX_QUESTIONS` | Low | `FAILED_AT_INTAKE` | Adapter handles. Operator picks a richer fixture or relaxes `draft_after`. |
| 4 | Claude returns a JSON shape that doesn't match `IntakeReport` schema | Medium | Pydantic raises mid-graph | The adapter's `except Exception` (§7.2.2) catches. **Verify in the failure-injection test.** |
| 5 | Cost overrun (e.g., long interview, many revisions) | Low | < $1 per run worst case | Caps in `state.py:57-58` (`MAX_QUESTIONS=10`, `MAX_REVISIONS=3`). |
| 6 | The `data-agent` package's `AnthropicLLMClient` has never been verified against a real API per Session 10 notes | Low | First B1 run reveals a model-ID mismatch or a parse bug | B1's verification step IS the smoke test. If the model ID is stale, the SDK error names it explicitly — fix the default in `anthropic_client.py:43`. |
| 7 | OPERATIONS.md §4.2/4.3 documents a non-existent entry point (BACKLOG #6) | Already known | Doc drift | Plan deliberately routes through `scripts/run_pipeline.py` and adds a §4.4 there. The §4.2/4.3 cleanup is BACKLOG #6's session. |

---

## 14. Anti-scope (do NOT do in Scope B)

To head off scope creep during implementation:

1. **Do not add a new public CLI entry point.** `scripts/run_pipeline.py` stays canonical. No `python -m model_project_constructor` or `mpc run`.
2. **Do not modify `IntakeAgent`, `DataAgent`, the graphs, or the prompts.** Only the runner-level wiring in `scripts/run_pipeline.py` (and the optional adapter for §8.4).
3. **Do not add `--resume-from-checkpoint`.** That is BACKLOG #7 — it deserves its own plan.
4. **Do not fix BACKLOG items #2 (`MPC_NAMESPACE` validator), #3 (CI ruff scope), #4 (CI mypy scope), #5 (GHE URL override), or #6 (OPERATIONS recipe reconcile) in this plan's sessions.** Each is its own one-session deliverable. Scope B opens enough surface area on its own.
5. **Do not extend CI to run live LLM tests.** Cost-prohibitive and noisy. Live runs stay operator-driven.
6. **Do not introduce new dependencies.** `anthropic` is already a transitive dep through both packages. No new packages needed.
7. **Do not bundle B1 + B2 into one session.** Each phase is a session. Failure mode #18 (plan-to-implementation bleed) is the specific risk.

---

## 15. Per-phase session boundaries (for the executor)

| Session | Phase | Deliverable | Stop condition |
|---|---|---|---|
| 24 | B1 | Real data agent wired into `scripts/run_pipeline.py` via `--llm data`. | One live `COMPLETE` run + Scope A regression check + green test suite. Commit `feat(scope-b1): ...`. Close out. |
| 25 | B2 | Scripted-answers intake via `--llm both --intake-fixture`. | One live `COMPLETE` run + one live `FAILED_AT_INTAKE` run (failure injection) + green test suite. Commit `feat(scope-b2): ...`. Close out. |
| 26 (optional) | B3 | Web UI bridge via `--resume-intake`. Only if §8.3 chooses (a). | One live round-trip + new unit test + green test suite. Commit. Close out. |

Each session writes its own handoff. Each handoff includes the `run_id` of the live invocation that proved completion (for forensics).

---

## 16. Appendix A — File reference map

For the executor's quick lookup. All paths are relative to repo root.

| Concern | File:Line |
|---|---|
| Runner type aliases | `src/model_project_constructor/orchestrator/pipeline.py:41-43` |
| `run_pipeline` body | `src/model_project_constructor/orchestrator/pipeline.py:97-209` |
| `FAILED_AT_INTAKE` halt | `src/model_project_constructor/orchestrator/pipeline.py:127-136` |
| `FAILED_AT_DATA` halt | `src/model_project_constructor/orchestrator/pipeline.py:161-169` |
| `FAILED_AT_WEBSITE` halt | `src/model_project_constructor/orchestrator/pipeline.py:188-200` |
| Current Scope A stub wiring | `scripts/run_pipeline.py:201-206` |
| `build_website_runner` (template) | `scripts/run_pipeline.py:92-122` |
| `instrument` helper (logging + metrics wrap) | `scripts/run_pipeline.py:125-132` |
| Intake facade | `src/model_project_constructor/agents/intake/agent.py` |
| `IntakeAgent.run_scripted` | `src/model_project_constructor/agents/intake/agent.py:48-125` |
| Intake LLM client (real) | `src/model_project_constructor/agents/intake/anthropic_client.py:53-170` |
| Intake LLM error class | `src/model_project_constructor/agents/intake/protocol.py:92-93` |
| Fixture loader + helpers | `src/model_project_constructor/agents/intake/fixture.py` |
| Intake state caps | `src/model_project_constructor/agents/intake/state.py:57-58` |
| Intake CLI (Phase 3A; rejects `--anthropic`) | `src/model_project_constructor/agents/intake/cli.py:60-87` |
| Intake Web UI session store | `src/model_project_constructor/ui/intake/runner.py` |
| Web UI `_snapshot` (builds report) | `src/model_project_constructor/ui/intake/runner.py:113-164` |
| Data agent entry | `packages/data-agent/src/model_project_constructor_data_agent/agent.py:32-61` |
| Data agent Anthropic client | `packages/data-agent/src/model_project_constructor_data_agent/anthropic_client.py:51-218` |
| Data agent CLI (template for B1) | `packages/data-agent/src/model_project_constructor_data_agent/cli.py:60-119` |
| `ReadOnlyDB` (optional dep) | `packages/data-agent/src/model_project_constructor_data_agent/db.py` |
| Checkpoint store | `src/model_project_constructor/orchestrator/checkpoints.py` |
| Settings loader | `src/model_project_constructor/orchestrator/config.py:45-140` |
| OPERATIONS env var matrix | `OPERATIONS.md` §1 (table at lines 21-30) |
| OPERATIONS broken §4.2/4.3 (do NOT extend) | `OPERATIONS.md:174-208` |
| Tutorial live recipe | `docs/tutorial.md:340-376` (Scope A — extend in B1 with §6) |

---

## 17. Appendix B — Full grep inventory (for executor verification)

Re-run these before starting any phase. If counts have drifted, investigate before implementing.

```bash
# Runner contract
grep -rn "IntakeRunner\|DataRunner\|WebsiteRunner" src/ tests/ packages/ scripts/ --include='*.py' | wc -l
# Expected: 16 in .py (pipeline.py:9, orchestrator/__init__.py:6, scripts/run_pipeline.py:1).
# Plus ~5 more in *.md (SESSION_NOTES, README, Extending-the-Pipeline) — Session 23 verified 2026-04-16.

# Pipeline call sites
grep -rn "run_pipeline(" src/ tests/ packages/ scripts/ | wc -l
# Expected: 13 production + test (excludes docs, which are 16 - 13)

# IntakeAgent constructions
grep -rn "IntakeAgent(" src/ tests/ packages/ scripts/ | wc -l
# Expected: 4 (1 CLI + 3 tests)

# DataAgent constructions
grep -rn "DataAgent(" src/ tests/ packages/ scripts/ | wc -l
# Expected: 9 (1 CLI + 8 tests)

# AnthropicLLMClient instantiations in production code
grep -rn "AnthropicLLMClient(" src/ packages/ scripts/ \
    --include='*.py' | grep -v test_ | wc -l
# Expected: 2 (data CLI + intake UI factory). Scope B adds 2 more (B1 data, B2 intake).

# Verify no website CLI entry point exists (Session 22 finding #6 — do not document this!)
ls -la src/model_project_constructor/agents/website/__main__.py 2>&1
ls -la src/model_project_constructor/agents/website/cli.py 2>&1
# Expected: both "No such file or directory"
```

---

## 18. Sign-off checklist for the executor

Before opening Phase B1, the executor confirms:

- [ ] Re-read this entire plan, not just §7.1.
- [ ] Re-ran the grep inventory in §17. All counts match (or deltas are understood).
- [ ] User has resolved §8.1 through §8.5 (or chose the recommendations).
- [ ] `.env` exports `ANTHROPIC_API_KEY` and the chosen host token (`GITLAB_TOKEN` or `GITHUB_TOKEN`).
- [ ] Read `SAFEGUARDS.md` and `SESSION_RUNNER.md`. Failure mode #18 (plan-to-impl bleed) is the active risk — do exactly one phase per session.
- [ ] Phase 1B stub written to `SESSION_NOTES.md` before any code.
- [ ] Pre-flight is clean: `uv run pytest -q && uv run ruff check src/ tests/ packages/ && uv run mypy src/`.

End of plan.
