# Resume-from-Checkpoint Plan

> **Status:** Draft for executor review (Session 48 of project, planning workstream).
> **Author:** Session 48 — 2026-04-18.
> **Implements:** BACKLOG.md item "Automated resume-from-checkpoint".
> **Supersedes:** B-3 Web UI bridge (see `scope-b-plan.md:309` — the general resume path absorbs the bespoke `--resume-intake` glue).
> **Out of scope:** anything that is NOT building a general, envelope-driven `--resume` mechanism on top of the existing `CheckpointStore`. See §10.

---

## 1. Context

### 1.1 What "resume-from-checkpoint" means

Today, a crashed pipeline run is recovered by a **manual Python snippet** documented in `OPERATIONS.md:329-353`:

```python
from model_project_constructor.orchestrator import CheckpointStore, run_pipeline
store = CheckpointStore(Path("/var/lib/mpc/checkpoints"))
intake = store.load_payload("run_abc", "IntakeReport")
# ... build config, stub intake runner with lambda: intake, re-run ...
```

`scope-b-plan.md:619-637` walks through the same recipe and explicitly defers a CLI flag to "BACKLOG #7 — it deserves its own plan." **This is that plan.**

The deliverable is a `scripts/run_pipeline.py --resume <run_id>` flag that picks up at the first missing envelope/result on disk. The on-disk format is **already resume-ready** per `checkpoints.py:13-16`:

```
Re-running a pipeline with the same ``run_id`` overwrites the previous
checkpoint. Resumption support (reading back an envelope and skipping
an earlier stage) is deferred to Phase 6, but the on-disk format is
ready for it.
```

### 1.2 What success looks like

A partial run that halted at `FAILED_AT_DATA` because Claude rate-limited is resumed with:

```bash
uv run python scripts/run_pipeline.py --live --host gitlab \
    --llm data --resume run_abc
```

- The intake envelope on disk is loaded — no interview is re-conducted, no Claude intake call is made.
- The data agent re-runs (it was the failure point); it consumes the same `DataRequest` envelope that was persisted before the original failure.
- The website stage runs as before.
- Final `RepoProjectResult.result.json` lands, run completes.

### 1.3 Why this supersedes B-3

`scope-b-plan.md §7.3` proposed a dedicated `--resume-intake <session_id>` flag that reads the completed `IntakeReport` from the intake Web UI's SQLite store (`INTAKE_DB_PATH`). That flag is **one specific instance** of the general pattern "load a pre-built IntakeReport and skip the intake stage."

Once `--resume <run_id>` exists, the UI → pipeline handoff becomes: have the UI write an `IntakeReport.json` envelope into `MPC_CHECKPOINT_DIR/<run_id>/` when the interview completes. Then the operator invokes `--resume <run_id>`. No bespoke CLI flag, no `--intake-db` path parameter, no SQLite schema knowledge in `run_pipeline.py`. The Web UI bridge is absorbed into Phase 4 of this plan.

### 1.4 What this plan does NOT do

- Does **not** change the `CheckpointStore` on-disk format. All four phases read/write the existing envelope layout.
- Does **not** touch LangGraph's intra-agent checkpointers (`MemorySaver` / `SqliteSaver`). Those are a different layer — they persist state **inside** one agent's run; this plan only persists state **between** agents. See §10 anti-scope.
- Does **not** add cross-run-id resumption ("use run_abc's IntakeReport for a new run_xyz"). That's a different feature (`--clone-intake-from`) and is not in this plan.
- Does **not** automate retry-on-failure. The operator still decides whether to resume after a failure — a rate limit that recurs immediately is not solved by `--resume`.

---

## 2. Glossary

| Term | Meaning |
|---|---|
| **Resume point** | The first stage that must be re-executed. One of `intake`, `intake_to_data_adapter`, `data`, `website`, or `already_complete`. |
| **Envelope** | A `HandoffEnvelope` wrapping one of `IntakeReport`, `DataRequest`, `DataReport`, `RepoTarget`. Written by `CheckpointStore.save()` to `<base>/<run_id>/<payload_type>.json`. |
| **Terminal result** | `RepoProjectResult.result.json` — written by `CheckpointStore.save_result()` (not an envelope). Its presence means the run reached `COMPLETE` or `FAILED_AT_WEBSITE` with a typed result. |
| **Resume truth table** | The function mapping `(which envelopes + results exist on disk)` → `(resume point, what to skip, what to re-execute)`. See §5. |
| **Checkpoint dir** | `MPC_CHECKPOINT_DIR` / `--checkpoint-dir` (default `./.orchestrator/checkpoints`). Per-run subdirectory: `<checkpoint_dir>/<run_id>/`. |

---

## 3. Evidence-based inventory

Every grep count below was run against the current tree on Session 48 (commit `eaaf7f8`). Counts are `files:hits` pairs.

### 3.1 `CheckpointStore` — 77 hits across 19 files

Production code (6 hits across 4 files):
- `src/model_project_constructor/orchestrator/checkpoints.py:2` — the class definition.
- `src/model_project_constructor/orchestrator/pipeline.py:4` — the `store or CheckpointStore(...)` default at `pipeline.py:114` + type hint in signature.
- `src/model_project_constructor/orchestrator/__init__.py:2` — re-export.
- `src/model_project_constructor/orchestrator/config.py:1` — docstring reference to `DEFAULT_CHECKPOINT_DIR` (not a code usage).

Test code (27 hits across 2 files):
- `tests/orchestrator/test_checkpoints.py:21` — the store's own tests (round-trip, listing, run-isolation).
- `tests/orchestrator/test_pipeline.py:6` — pipeline tests that assert envelopes are written.

Docs (44 hits across 13 files) — descriptive prose in `OPERATIONS.md`, `TROUBLESHOOTING.md`, `README.md`, wiki pages, archived plans, SESSION_NOTES. Not load-bearing for this plan's edits.

### 3.2 `PipelineConfig` — 26 hits across 8 files

- `src/model_project_constructor/orchestrator/pipeline.py:4` — definition + usage.
- `src/model_project_constructor/orchestrator/__init__.py:2` — re-export.
- `scripts/run_pipeline.py:3` — construction at line 407-411.
- `tests/orchestrator/test_pipeline.py:5` + `tests/orchestrator/test_metrics.py:3` — test helpers.
- `docs/tutorial.md:2` — prose.
- `SESSION_NOTES.md:6` + `docs/architecture-history/architecture-plan.md:1` — prose.

**Significance:** `PipelineConfig` has no `resume_from` field today. Phase 2 adds one. Call-site count is small (one construction in `scripts/`, plus test helpers).

### 3.3 `run_pipeline` — 312 hits across 27 files

Call sites (the load-bearing ones):
- `src/model_project_constructor/orchestrator/pipeline.py:4` — definition.
- `src/model_project_constructor/orchestrator/__init__.py:3` — re-export.
- `scripts/run_pipeline.py:4` — one call at line 443.
- `tests/orchestrator/test_pipeline.py:11` — ~11 test invocations.

**Significance:** Phase 2 modifies `run_pipeline`'s internals. No call-site signature change if `resume_from` is stored on `PipelineConfig` (preferred).

### 3.4 CLI flags `--run-id` / `--checkpoint-dir` — 38 hits across 6 files

- `scripts/run_pipeline.py:4` — argparse definitions at lines 308-323.
- `docs/tutorial.md:6` — worked examples.
- `OPERATIONS.md:3` + `CHANGELOG.md:2` + `docs/planning/scope-b-plan.md:12` + `SESSION_NOTES.md:11` — prose.

**Significance:** Phase 3 adds `--resume` adjacent to `--run-id`. Argparse is already the pattern; the doc surface is small.

### 3.5 `checkpoint_dir` in Python files — 24 hits across 6 files

- `src/model_project_constructor/orchestrator/config.py:4` — `DEFAULT_CHECKPOINT_DIR` + env var + from_env + docstring.
- `src/model_project_constructor/orchestrator/pipeline.py:2` — `PipelineConfig.checkpoint_dir` field + usage.
- `tests/orchestrator/test_pipeline.py:8` + `tests/orchestrator/test_config.py:3` + `tests/orchestrator/test_metrics.py:1` — test fixtures.
- `scripts/run_pipeline.py:6` — argparse + usage.

### 3.6 Existing resume-related references

`--resume*` in the tree (scope-b-plan and SESSION_NOTES prose only — no production code):
- `docs/planning/scope-b-plan.md:309, 504, 534, 637, 695, 721, 735` — B-3 `--resume-intake` proposal and `--resume-from-checkpoint` anti-scope notes. **These are all PROPOSALS / prose, not implementations.** No `--resume` flag exists in production today.
- `BACKLOG.md:7-8` — the two items this plan covers.
- `ROADMAP.md:11` — one-line mention in the post-pilot improvements list.

**Inventory conclusion:** the surface area is small. The plan touches one production file (`pipeline.py`), adds a small CLI flag (`run_pipeline.py`), adds one OPERATIONS section and one tutorial mention. Phase 4 adds one UI-side method. The on-disk format is already correct.

---

## 4. Current state vs. target state

### 4.1 Current state (Session 48, commit `eaaf7f8`)

`run_pipeline()` at `pipeline.py:97-209`:
1. Always calls `intake_runner()`.
2. Saves `IntakeReport.json` envelope.
3. Halts with `FAILED_AT_INTAKE` if `intake_report.status != "COMPLETE"`.
4. Always calls `intake_report_to_data_request(intake_report, run_id)`.
5. Saves `DataRequest.json` envelope.
6. Always calls `data_runner(data_request)`.
7. Saves `DataReport.json` envelope.
8. Halts with `FAILED_AT_DATA` if `data_report.status != "COMPLETE"`.
9. Saves `RepoTarget.json` envelope.
10. Always calls `website_runner(intake_report, data_report, config.repo_target)`.
11. Saves `RepoProjectResult.result.json` (terminal).
12. Halts with `FAILED_AT_WEBSITE` if `project_result.status != "COMPLETE"`.

Re-running with the same `run_id` **overwrites** every envelope and the result. There is no "load from disk instead of calling the runner" branch.

### 4.2 Target state (after all four phases)

`run_pipeline()` accepts an optional `resume_from: ResumePoint | None` on `PipelineConfig`. When set:
- Envelopes that precede the resume point are **loaded** from `CheckpointStore`, not re-executed.
- Envelopes at or after the resume point are **re-executed** by their runner (which can overwrite the disk envelope).
- The CLI `--resume <run_id>` resolves the resume point by calling a pure function `determine_resume_point(store, run_id)` that inspects which envelopes/results exist on disk.

### 4.3 Why the envelope layout already supports this

`CheckpointStore` already provides:
- `has(run_id, payload_type)` at `checkpoints.py:97-100` — existence check.
- `load_payload(run_id, payload_type)` at `checkpoints.py:91-95` — envelope → typed model via `schemas.registry.load_payload`.
- `has_result(run_id, name)` at `checkpoints.py:102-105` — terminal existence check.

No new store methods are needed. The resume logic reads only these three.

---

## 5. Resume truth table

Given a `run_id` and `store`, let:
- `I = store.has(run_id, "IntakeReport")`
- `Q = store.has(run_id, "DataRequest")`
- `D = store.has(run_id, "DataReport")`
- `T = store.has(run_id, "RepoTarget")`
- `R = store.has_result(run_id, "RepoProjectResult")`

Then `determine_resume_point(store, run_id)` returns:

| Case | I | Q | D | T | R | Resume point | What loads from disk | What re-executes |
|---|---|---|---|---|---|---|---|---|
| **S0** | — | — | — | — | — | `intake` | (nothing) | intake → adapter → data → website |
| **S1** | ✓ | — | — | — | — | `intake_to_data_adapter` | `IntakeReport` | adapter → data → website |
| **S2** | ✓ | ✓ | — | — | — | `data` | `IntakeReport`, `DataRequest` | data → website |
| **S3** | ✓ | ✓ | ✓ | — | — | `website` | `IntakeReport`, `DataRequest`, `DataReport` | website (save `RepoTarget` first) |
| **S4** | ✓ | ✓ | ✓ | ✓ | — | `website` | `IntakeReport`, `DataRequest`, `DataReport` (ignore disk `RepoTarget`; use config's) | website |
| **S5** | ✓ | ✓ | ✓ | ✓ | ✓ | `already_complete` | (nothing — error or no-op per §8.2) | (nothing) |
| **INVALID** | ✗ | * | * | * | * | (raise `ResumeInconsistent`) | — | — |
| **INVALID** | * | ✗ | ✓ | * | * | (raise `ResumeInconsistent`) | — | — |
| **INVALID** | * | * | ✗ | * | ✓ | (raise `ResumeInconsistent`) | — | — |

**Rationale for each case:**

- **S0** — `--resume <run_id>` with no envelopes is an error condition (the operator gave the wrong run_id) OR it degrades to "start fresh" per §8.1. Phase 1 implementation returns `intake`; Phase 3 CLI layer decides whether to reject or allow.
- **S1** — intake completed, failure was in the `intake_to_data_adapter` step (rare — it's pure code) OR the run was interrupted before the adapter ran. Load the IntakeReport, re-derive the DataRequest. Note: the adapter's output is **deterministic** given `(IntakeReport, run_id)` (see `adapters.py:44-77`), so re-running it produces the exact same envelope — no provenance drift.
- **S2** — intake + adapter completed, data agent failed. Load IntakeReport + DataRequest; re-run the data agent. The data agent receives the **same** DataRequest it received on the failed run (by-contents identity), preserving determinism at the request boundary.
- **S3** — intake + adapter + data completed, failure was before `RepoTarget.save` OR inside the website agent. Phase 2 handles both: re-save the `RepoTarget` envelope from `config.repo_target` (it may have changed between runs — see S4), then run the website agent.
- **S4** — same as S3 but a previous run also saved a `RepoTarget`. The question: does the resumed run use the **disk** RepoTarget or the **config** RepoTarget? Phase 2 answer: **config wins**. If the operator re-points to a different GitLab group between runs, that is a deliberate choice; silently preferring the old target would surprise. This is an open decision for operator review — see §8.3.
- **S5** — the run is already COMPLETE. `--resume` is either a no-op (exit 0 with a message) or an error. See §8.2.
- **INVALID rows** — a missing predecessor with a present successor means someone mutated the checkpoint dir by hand. The resume logic refuses to guess and raises `ResumeInconsistent`.

---

## 6. Architecture decisions

### 6.1 Where the resume logic lives

**Decision:** in `src/model_project_constructor/orchestrator/pipeline.py`, NOT in `scripts/run_pipeline.py`.

**Why:** the orchestrator is the layer that owns pipeline semantics. `scripts/run_pipeline.py` is a thin CLI wrapper. Putting the resume logic in the orchestrator means programmatic callers (tests, future alternate entry points) get it for free.

### 6.2 Function vs. method vs. flag

**Decision:** a pure function `determine_resume_point(store, run_id) -> ResumePoint` lives in `pipeline.py`. It takes the store + run_id, inspects files on disk, returns the enum. `run_pipeline()` calls it when `config.resume_from == "auto"` (or whenever resume is requested), and skips execution up to that point.

**Why pure function, not method on `CheckpointStore`:** the store is generic envelope I/O. The resume semantics depend on the specific pipeline stages (`intake → data → website`), which is pipeline's knowledge, not the store's.

**Why enum, not boolean:** distinguishes S0-S5 cleanly; the CLI can format a per-case message ("resuming from data stage") that a boolean cannot.

### 6.3 Re-deriving vs. loading the `DataRequest`

`DataRequest` is produced by the deterministic `intake_report_to_data_request(intake, run_id)` adapter. Two options in case S2/S3:

- **(a) Re-derive on every resume** — call the adapter again even though the envelope exists. Simpler code.
- **(b) Load from disk** — trust the original envelope. Preserves the historical record of what the data agent actually saw on the failed run.

**Decision:** **(b) load from disk.** The envelope on disk is the "ground truth" of what was sent to the data agent. If we re-derive and the adapter's behavior has changed between the original run and the resume (e.g. a code change altered `infer_target_granularity`), the resumed data agent would see a different request — silent divergence. Loading the saved envelope eliminates that class of bug. For S1 only (DataRequest not yet saved), the adapter runs.

### 6.4 Terminal `RepoProjectResult`

A successful run writes `RepoProjectResult.result.json`. A failed website run also writes it (with `status="FAILED"` and populated `failure_reason`). **Both count as "terminal"** — if the result file exists, the website runner completed, whether success or failure.

**Decision:** `determine_resume_point` returns `already_complete` only when `has_result(run_id, "RepoProjectResult")` is true. The CLI layer (Phase 3) distinguishes `status="COMPLETE"` from `status="FAILED"` for the operator message:
- `COMPLETE` → "Run is already complete. Nothing to resume."
- `FAILED` → "Run ended with FAILED website stage. Delete the result file to retry the website stage, or start a new run."

The "delete and retry" recipe is documented in OPERATIONS; no new CLI flag for it in this plan.

### 6.5 Metrics + logging on resume

Current `MetricsRegistry` (`orchestrator/metrics.py`) records per-stage latency via `make_measured_runner`. When a stage is skipped on resume, there is no latency to record.

**Decision:** Phase 2 adds a `resume_point` field to `PipelineResult` (optional, `None` when not resumed). Phase 2 does NOT add a new metric. The logging layer (`orchestrator/logging.py`) emits a `pipeline.resumed` structured event at the start of a resumed run with `{run_id, resume_point, loaded_payloads}`. Operators can grep logs for resume events without new metric plumbing.

### 6.6 Default behavior when `--resume` targets a missing run_id

**Decision:** Phase 3 CLI rejects `--resume <run_id>` if `<checkpoint_dir>/<run_id>/` does not exist. Error message: `Run <run_id> has no checkpoints at <path>. Start a new run without --resume.` Exit code 2.

This differs from the pipeline-level behavior (S0 returns `intake` as a valid resume point). The CLI adds the guard because from an operator's perspective, "`--resume` on a bare run_id" is almost certainly a typo, not an intent to start fresh.

---

## 7. Per-phase implementation plan

Each phase is **one session**. Failure mode #18 (planning-to-implementation bleed) is the specific risk; Learning #18 applies. Per-phase completion criteria are explicit (what DONE looks like + verification commands + session boundary).

### 7.1 Phase 1 — `determine_resume_point` + tests (no pipeline changes)

**Goal:** land the pure function and its test suite. `run_pipeline` still ignores it. This isolates the truth-table logic from the larger orchestrator change.

#### 7.1.1 Files to change

| File | Change | LOC est. |
|---|---|---|
| `src/model_project_constructor/orchestrator/pipeline.py` | Add `ResumePoint` `Literal` type + `ResumeInconsistent` exception + `determine_resume_point(store, run_id)` function. Add to `__all__`. | +60 / -0 |
| `src/model_project_constructor/orchestrator/__init__.py` | Re-export `ResumePoint`, `ResumeInconsistent`, `determine_resume_point`. | +6 |
| `tests/orchestrator/test_pipeline.py` | New `TestDetermineResumePoint` class: one test per row of §5 truth table (S0–S5 + 3 INVALID rows = 9 tests). | +120 |
| `CHANGELOG.md` | `[Unreleased]` entry: "feat(resume): add `determine_resume_point` pure function." | +5 |

#### 7.1.2 Shape

```python
# pipeline.py

ResumePoint = Literal[
    "intake",
    "intake_to_data_adapter",
    "data",
    "website",
    "already_complete",
]

class ResumeInconsistent(RuntimeError):
    """Raised when a checkpoint dir has a successor envelope without its predecessor."""

def determine_resume_point(store: CheckpointStore, run_id: str) -> ResumePoint:
    """Inspect the on-disk envelopes for ``run_id`` and return the first stage
    that must be re-executed. See resume-from-checkpoint-plan.md §5 truth table.
    """
    I = store.has(run_id, "IntakeReport")
    Q = store.has(run_id, "DataRequest")
    D = store.has(run_id, "DataReport")
    # T = store.has(run_id, "RepoTarget")   # not needed for the decision; see §6.4
    R = store.has_result(run_id, "RepoProjectResult")

    # Invalid states first — a present successor without its predecessor.
    if R and not D:
        raise ResumeInconsistent(...)
    if D and not Q:
        raise ResumeInconsistent(...)
    if (Q or D) and not I:
        raise ResumeInconsistent(...)

    if R:
        return "already_complete"
    if D:
        return "website"
    if Q:
        return "data"
    if I:
        return "intake_to_data_adapter"
    return "intake"
```

#### 7.1.3 Per-phase completion criteria

**What DONE looks like:**
1. `ResumePoint` + `ResumeInconsistent` + `determine_resume_point` live in `pipeline.py` and are importable via `from model_project_constructor.orchestrator import ...`.
2. 9 tests in `TestDetermineResumePoint` pass (one per §5 truth table row).
3. `run_pipeline` is **unchanged** — Phase 1 does not wire resume into execution. This is deliberate; it keeps the Phase 1 diff small and reviewable.
4. No regressions in the existing test suite.

**Verification commands:**
```bash
uv run pytest -q tests/orchestrator/test_pipeline.py  # existing + 9 new tests
uv run pytest -q                                       # full suite green
uv run ruff check src/ tests/                          # clean
uv run mypy src/                                       # clean
```

**Session boundary:** when all four commands above pass, commit `feat(resume-phase1): add determine_resume_point pure function`, close out. Phase 2 is a separate session.

### 7.2 Phase 2 — `run_pipeline` resume execution

**Goal:** `run_pipeline()` respects `PipelineConfig.resume_from` and skips stages whose envelopes already exist.

#### 7.2.1 Files to change

| File | Change | LOC est. |
|---|---|---|
| `src/model_project_constructor/orchestrator/pipeline.py` | Add `resume_from: ResumePoint \| None = None` field to `PipelineConfig`. Branch logic in `run_pipeline` — load envelopes up to the resume point, re-execute from that point. Add `resume_point: ResumePoint \| None = None` to `PipelineResult`. | +90 / -5 |
| `tests/orchestrator/test_pipeline.py` | New `TestRunPipelineResume` class: one test per case S1–S4 (S0 and S5 covered separately). ~5-6 tests total. | +180 |
| `CHANGELOG.md` | `[Unreleased]` entry: "feat(resume): `run_pipeline` honors `resume_from`." | +5 |

#### 7.2.2 Shape

```python
# pipeline.py — new fields on PipelineConfig

@dataclass
class PipelineConfig:
    run_id: str
    repo_target: RepoTarget
    checkpoint_dir: Path
    correlation_id: str = field(default="")
    resume_from: ResumePoint | None = None  # NEW

# pipeline.py — new branch in run_pipeline (sketch)

def run_pipeline(config, *, intake_runner, data_runner, website_runner, store=None):
    checkpoint_store = store or CheckpointStore(config.checkpoint_dir)
    resume = config.resume_from

    # Intake stage
    if resume in (None, "intake"):
        intake_report = intake_runner()
        # ... save envelope ... (existing logic)
    else:
        intake_report = checkpoint_store.load_payload(config.run_id, "IntakeReport")
    # Halt logic stays, but only fires when intake_runner ran.
    # ...

    # Adapter stage
    if resume in (None, "intake", "intake_to_data_adapter"):
        data_request = intake_report_to_data_request(intake_report, config.run_id)
        checkpoint_store.save(_envelope(...))
    else:
        data_request = checkpoint_store.load_payload(config.run_id, "DataRequest")

    # Data stage
    if resume in (None, "intake", "intake_to_data_adapter", "data"):
        data_report = data_runner(data_request)
        # ... save envelope ... (existing logic)
    else:
        data_report = checkpoint_store.load_payload(config.run_id, "DataReport")
    # Halt logic for data only fires when data_runner ran.

    # Website stage — always re-executes when resume != "already_complete"
    if resume == "already_complete":
        # Phase 2 behavior: raise. Phase 3 CLI translates to a friendly message.
        raise ValueError(f"Run {config.run_id} already complete; no-op")
    # ... RepoTarget + website_runner ... (existing)

    return PipelineResult(
        run_id=config.run_id,
        status="COMPLETE",
        # ... existing fields ...
        resume_point=resume,
    )
```

#### 7.2.3 Per-phase completion criteria

**What DONE looks like:**
1. `PipelineConfig.resume_from` and `PipelineResult.resume_point` exist and are type-checked.
2. `run_pipeline(config_with_resume, ...)` loads the correct envelopes and re-executes only the correct stages, verified by §5 truth table cases S1–S4 as unit tests. Stubs assert the skipped runner is **not called** (e.g. `assert intake_runner.call_count == 0` when `resume == "data"`).
3. Halt semantics remain correct: if the re-executed stage fails, the `FAILED_AT_*` status is returned exactly as in the non-resume path.
4. Existing tests stay green (no signature-break on `run_pipeline`; `resume_from=None` default preserves behavior).
5. CI lint + typecheck green.

**Verification commands:**
```bash
uv run pytest -q tests/orchestrator/test_pipeline.py  # 6 new cases green
uv run pytest -q                                       # full suite green
uv run ruff check src/ tests/                          # clean
uv run mypy src/                                       # clean
```

**Session boundary:** commit `feat(resume-phase2): run_pipeline honors resume_from`, close out. Phase 3 is a separate session.

### 7.3 Phase 3 — `--resume` CLI flag + OPERATIONS + tutorial

**Goal:** operator-facing CLI. `scripts/run_pipeline.py --resume <run_id>` resolves the resume point via `determine_resume_point` and invokes `run_pipeline` with the right config.

#### 7.3.1 Files to change

| File | Change | LOC est. |
|---|---|---|
| `scripts/run_pipeline.py` | Add `--resume` argparse flag (mutually exclusive with the default "fresh run" path when `--run-id` is not supplied). Rewrite `main()` to: if `--resume <run_id>` → call `determine_resume_point(store, run_id)`; reject if S0 OR `already_complete` with friendly messages; else construct `PipelineConfig` with `resume_from=<point>` and `run_id=<resumed run_id>`. Print a "Resuming from <point>; skipping <stages>" banner. | +50 / -2 |
| `tests/scripts/test_run_pipeline_resume.py` | NEW file. Exercises the CLI argparse parsing + the `determine_resume_point`-based branching, not a live pipeline run. 4-5 tests. | +100 |
| `OPERATIONS.md` | Replace §5 ("Resume after a partial run") with the new automated recipe. Keep the manual `CheckpointStore.load_payload` snippet as a fallback ("for unusual cases"). | +25 / -10 |
| `docs/tutorial.md` | Add a short §7 "Resuming a partial run" after the current final section. Cross-reference OPERATIONS §5. | +20 |
| `CHANGELOG.md` | `[Unreleased]` entry: "feat(resume): `scripts/run_pipeline.py --resume <run_id>`." | +5 |
| `BACKLOG.md` | **Remove** (not flip to `[x]` — Learning #26) the "Automated resume-from-checkpoint" line. Also remove the B-3 line, because §1.3 of this plan explains B-3 is superseded. Leave a CHANGELOG entry documenting the B-3 supersession. | −2 |
| `README.md` | One-line mention in the CLI flags summary. | +3 |

#### 7.3.2 CLI UX

```
$ uv run python scripts/run_pipeline.py --resume run_abc --live --host gitlab --llm data

=============================================================
  Model Project Constructor — End-to-End Pipeline Run
  Mode: LIVE  |  Host: gitlab  |  LLM: data=claude-opus-4-7
  Run ID: run_abc  (RESUMED from: data)
  Skipping: intake, intake_to_data_adapter
=============================================================

[1/5] Loading checkpoints from .orchestrator/checkpoints/run_abc/...
      IntakeReport: loaded (subrogation, classification)
      DataRequest: loaded (target=was_subrogation_successful)
[2/5] Building pipeline config...
...
[4/5] Running pipeline (data + website)...
...
```

Error cases:
- `--resume <run_id>` + `<checkpoint_dir>/<run_id>/` missing → `Run <run_id> has no checkpoints at <path>. Start a new run without --resume.` Exit 2.
- `--resume <run_id>` + S5 (`already_complete`, `status=COMPLETE`) → `Run <run_id> is already complete. Nothing to resume. Result: <project_url>.` Exit 0.
- `--resume <run_id>` + S5 (`already_complete`, `status=FAILED`) → `Run <run_id> ended with FAILED website stage. Delete <result_path> to retry the website, or start a new run.` Exit 2.
- `--resume <run_id>` + `ResumeInconsistent` → `Checkpoint directory <path> has inconsistent envelopes: <details>. Manual intervention required.` Exit 2.
- `--resume` without `<run_id>` → argparse rejects with standard usage message.

#### 7.3.3 Per-phase completion criteria

**What DONE looks like:**
1. `uv run python scripts/run_pipeline.py --help` shows `--resume` with a clear description.
2. All four error cases print the exact message above and exit with the documented code.
3. One live invocation **proves** resume works end-to-end:
   - (a) Start a fresh run with an intentionally-failing data-agent DB (e.g. bad `--db-url`). Run halts at `FAILED_AT_DATA`; note the `run_id`.
   - (b) Fix the DB. Re-invoke with `--resume <run_id>`. Run completes. Capture the final `RepoProjectResult.result.json` path.
4. OPERATIONS §5 reads correctly and the old manual recipe is preserved as a fallback.
5. Test suite green (including 4-5 new CLI tests in `test_run_pipeline_resume.py`).
6. BACKLOG loses two lines (resume-from-checkpoint + B-3).

**Verification commands:**
```bash
uv run pytest -q                                       # full suite green
uv run ruff check src/ tests/ packages/                # clean
uv run mypy src/                                       # clean
# Live verification (operator-driven; not CI-gated):
uv run python scripts/run_pipeline.py --resume nonexistent_run_id 2>&1 | grep "no checkpoints"
# Full round-trip documented in the CHANGELOG entry with the real run_id.
```

**Session boundary:** commit `feat(resume-phase3): --resume CLI + operations + tutorial`, close out. Phase 4 (UI bridge) is a separate session AND is optional.

### 7.4 Phase 4 (OPTIONAL) — Intake Web UI writes `IntakeReport.json` envelope

**Goal:** when an interview completes in the intake Web UI, the UI writes an `IntakeReport.json` envelope to the configured checkpoint directory. The operator then invokes `--resume <run_id>` to continue into data + website. This supersedes `scope-b-plan.md §7.3`'s bespoke `--resume-intake` flag.

**Why optional:** Phase 3 already delivers the general-case value (crash recovery in single-process runs). Phase 4 is specifically about wiring the Web UI into the resume mechanism. Deprioritize unless a pilot operator demands the UI → CLI workflow.

#### 7.4.1 Files to change

| File | Change | LOC est. |
|---|---|---|
| `src/model_project_constructor/ui/intake/runner.py` | On interview completion, compute a `run_id` (either derived from `session_id` or supplied by a request header), wrap the `IntakeReport` in a `HandoffEnvelope`, and call `CheckpointStore(settings.checkpoint_dir).save(envelope)`. Gate behind a config flag `MPC_UI_WRITES_CHECKPOINT=1` to avoid surprising existing UI deployments. | +40 |
| `src/model_project_constructor/ui/intake/app.py` | Surface the resulting `run_id` to the UI so the operator can copy it into a `--resume` invocation. (Response header OR a "Copy resume command" button.) | +15 |
| `OPERATIONS.md` | New §5.1 "Resuming from the Web UI": walks the UI → `--resume` workflow. | +25 |
| `tests/ui/intake/test_runner_checkpoint.py` | New test file. Drive a UI interview to completion with `MPC_UI_WRITES_CHECKPOINT=1` set; assert `IntakeReport.json` exists at the expected path. | +80 |
| `CHANGELOG.md` | `[Unreleased]` entry: "feat(resume-phase4): intake UI writes checkpoint envelope (supersedes B-3)." | +5 |

#### 7.4.2 Per-phase completion criteria

**What DONE looks like:**
1. `MPC_UI_WRITES_CHECKPOINT=1 uv run uvicorn model_project_constructor.ui.intake.app:app` — run an interview end to end via the UI; confirm `IntakeReport.json` lands at `$MPC_CHECKPOINT_DIR/<run_id>/`.
2. `--resume <run_id>` picks up at `intake_to_data_adapter`, runs data + website, completes.
3. Default behavior unchanged when `MPC_UI_WRITES_CHECKPOINT` is unset — existing UI deployments do not start writing envelopes silently.
4. New test green; existing tests green.

**Verification commands:**
```bash
uv run pytest -q tests/ui/intake/                      # new test green
uv run pytest -q                                       # full suite green
uv run ruff check src/ tests/                          # clean
uv run mypy src/                                       # clean
# Live verification:
MPC_UI_WRITES_CHECKPOINT=1 uv run uvicorn ... &
# Drive an interview, note run_id
uv run python scripts/run_pipeline.py --resume <run_id> --live --host gitlab --llm data
```

**Session boundary:** commit `feat(resume-phase4): UI writes checkpoint envelope`, close out. Plan is fully delivered.

---

## 8. Operator decisions (resolved at the Session 48 review gate, 2026-04-18)

> **All five recommendations below were accepted by the operator at the Session 48 review gate.** The options and rationale are retained for future reviewers who may want to revisit a choice. No further operator input is required before Phase 1 starts.

### 8.1 S0 behavior at the CLI boundary

**Options:**
- (a) Reject — `--resume <run_id>` with no checkpoints on disk is a typo. Exit 2 with message.
- (b) Degrade — `--resume <run_id>` with no checkpoints starts a fresh run with that `run_id`.

**Recommendation:** (a). Silent degradation from "resume" to "fresh run" is surprising behavior; the operator likely meant a different run_id.

### 8.2 S5 behavior — already-complete run

**Options:**
- (a) No-op — print "already complete" + `project_url`, exit 0. `--resume` is idempotent.
- (b) Error — `--resume` on a complete run is a mistake; exit 2.

**Recommendation:** (a) when `status=COMPLETE` (idempotent resume is friendly); (b) when `status=FAILED` at the website stage (operator must opt in to the retry recipe by deleting the result file).

### 8.3 S4 behavior — a saved `RepoTarget` exists from a prior run

**Options:**
- (a) Config wins — silently replace the disk `RepoTarget` with `config.repo_target`.
- (b) Disk wins — preserve the original target; require operator to delete the envelope to change hosts.
- (c) Error if they differ — refuse to resume if the operator changed repo_target between runs.

**Recommendation:** (a). The operator supplied `config.repo_target` on the resumed invocation; that's the active intent. (c) is the safer but more paperwork-heavy alternative; (b) is too sticky.

### 8.4 Flag name

**Options:**
- (a) `--resume <run_id>`
- (b) `--resume-from-checkpoint <run_id>`
- (c) `--resume-run <run_id>`

**Recommendation:** (a). Shortest, matches `OPERATIONS.md §5`'s prose verb, not ambiguous because `--run-id` is the positive form (start a new run with this id) and `--resume` is the corresponding resume form.

### 8.5 Is Phase 4 in scope at all?

**Options:**
- (a) In scope — deliver Phase 4 after Phase 3.
- (b) Out of scope — this plan is Phases 1–3. The UI bridge is a separate BACKLOG item (replacing B-3).

**Recommendation:** (b) unless the operator expresses a UI-driven workflow. The value of Phases 1–3 is independent of Phase 4. Keeping Phase 4 optional keeps the plan's critical path to three sessions.

---

## 9. Failure-mode handling

| Failure | Surfaces in | Caught by | Result |
|---|---|---|---|
| `--resume <id>` with `<id>/` missing | Phase 3 CLI | Pre-flight check in `main()` | Exit 2 with message (§7.3.2) |
| `--resume <id>` with inconsistent envelopes (successor without predecessor) | `determine_resume_point` | `ResumeInconsistent` raised | Phase 3 CLI converts to exit 2 + message |
| `--resume <id>` with `RepoProjectResult.result.json` (status=COMPLETE) | `determine_resume_point` returns `already_complete` | Phase 3 CLI no-ops gracefully | Exit 0 |
| `--resume <id>` with `RepoProjectResult.result.json` (status=FAILED) | Same | Phase 3 CLI prints retry recipe | Exit 2 |
| Re-executed stage fails again | Existing `run_pipeline` halt logic | Same as non-resume path | `FAILED_AT_*` + `PipelineResult` (now with `resume_point=<stage>`) |
| Loaded envelope fails pydantic validation (schema changed between runs) | `CheckpointStore.load_payload` | `ValidationError` — not caught in Phase 2; surfaces as uncaught exception | Phase 3 CLI wraps and prints a "checkpoint incompatible — start a new run" message. This is rare — the schema registry is versioned; no field removals between minor versions. |
| `MPC_CHECKPOINT_DIR` not set on resumed invocation but set on original | Phase 3 CLI | `config.checkpoint_dir` defaults to `./.orchestrator/checkpoints` — same default as original, so same dir unless the operator actively changed it. If operator moved the dir, the pre-flight check in §7.3.2 catches it. | Exit 2 |

---

## 10. Anti-scope (do NOT do in this plan)

1. **Do not change the `CheckpointStore` on-disk format.** The envelope layout at `checkpoints.py:45-128` is already resume-ready. Any format change is a separate plan.
2. **Do not add LangGraph intra-agent checkpointing surfacing.** `MemorySaver` (`agents/intake/graph.py:7`) and `SqliteSaver` (`ui/intake/runner.py:26`) are a separate layer — they persist state **inside** an agent's graph, not between agents. Resuming mid-interview is NOT the goal of this plan.
3. **Do not add `--clone-intake-from <source_run_id>` (cross-run-id resumption).** That is a separate feature: "copy someone else's IntakeReport into a new run."
4. **Do not add automatic retry-on-failure.** The operator still decides whether to resume. Retry logic (backoff, max-retries) is a different concern — see `scope-b-plan.md §9` on rate-limit handling.
5. **Do not modify `IntakeAgent`, `DataAgent`, or `WebsiteAgent`.** Only the orchestrator and the CLI. Phase 4 touches `ui/intake/runner.py` + `ui/intake/app.py`; those are UI-layer, not agent-layer.
6. **Do not introduce new dependencies.** Plan uses stdlib `argparse`, `pathlib`, and the existing `CheckpointStore`.
7. **Do not bundle phases into one session.** Failure mode #18 applies. Each phase is one session; each session closes out.
8. **Do not fix adjacent BACKLOG items.** Tutorial UX, agent enhancements, glossary — each is its own session.

---

## 11. Risks and mitigations

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| 1 | Between the original and resumed runs, the `intake_report_to_data_request` adapter changes behavior (e.g. a `infer_target_granularity` tweak) | Low | Silent divergence — data agent sees a different request | §6.3 decision: load `DataRequest.json` from disk rather than re-derive. Envelope is ground truth. |
| 2 | Between the original and resumed runs, a schema field is renamed | Very low | `pydantic.ValidationError` on `load_payload` | Schema registry is versioned per `schemas/envelope.py:payload_schema_version`. Renames across a minor version are prohibited by convention. If it happens, error-message points at the schema version mismatch. |
| 3 | Operator resumes with a different `--run-id` than originally checkpointed | Low | Run starts fresh silently (if `--run-id X --resume Y` are both supplied inconsistently) | Phase 3 CLI: `--resume <id>` overrides `--run-id`. Argparse enforces this via `set_defaults` or a post-parse check. |
| 4 | Two concurrent processes resume the same `run_id` simultaneously | Very low | One overwrites the other's final result | Same as today — `CheckpointStore` is file-based, no locking. Documented in OPERATIONS as an operator responsibility. |
| 5 | Phase 2 subtly breaks `run_pipeline`'s halt semantics (e.g. `FAILED_AT_INTAKE` fires when intake was loaded from disk) | Low | A resumed run that originally halted at intake would re-halt even though intake is `COMPLETE` on disk | Halt logic must only fire after a runner **executes**. Test coverage: one explicit test per halt point under resume. |
| 6 | Phase 4 side-effect: UI writes an envelope on every interview completion, cluttering the checkpoint dir | Medium | Disk usage grows; operator confused | Phase 4 gates behind `MPC_UI_WRITES_CHECKPOINT=1` (opt-in). Default behavior unchanged. |
| 7 | The `MPC_UI_WRITES_CHECKPOINT` flag drifts out of sync with `MPC_CHECKPOINT_DIR` — UI writes to a different path than the CLI reads | Low | `--resume` can't find the envelope | Phase 4 documentation: both flags must point at the same dir. The UI uses `OrchestratorSettings.from_env()` for its checkpoint dir, matching the CLI default. |
| 8 | `determine_resume_point` treats a FAILED envelope (`IntakeReport.status=DRAFT_INCOMPLETE`, `DataReport.status=EXECUTION_FAILED`) as a completed handoff and skips the failed stage on resume — the inverse of risk #5 | Medium (observed) | A run halted at `FAILED_AT_DATA` would resume by handing the FAILED `DataReport` to the website agent, skipping data re-execution. Observed Session 51 live-LLM round-trip (`run_id=run_b1_resume_live_1776570556`) | Session 52 (BACKLOG item 1) fix: `determine_resume_point` loads `IntakeReport` / `DataReport` and checks `status == "COMPLETE"`. A non-COMPLETE payload demotes the resume point to `"intake"` / `"data"` respectively. `RepoProjectResult` is NOT symmetric: its FAILED case is handled by `_handle_already_complete` with opt-in-to-retry UX (the website stage has irreversible side effects). `ResumeInconsistent` is NOT raised for FAILED envelopes — they are legitimate halt artifacts, not structural corruption. |

---

## 12. Test strategy

### 12.1 What is unit-tested

- **Phase 1:** `TestDetermineResumePoint` — 9 tests, one per truth table row + 3 invalid.
- **Phase 2:** `TestRunPipelineResume` — 5-6 tests, one per S1–S4 case + halt-under-resume regression.
- **Phase 3:** `TestRunPipelineResumeCLI` — 4-5 tests, argparse + `determine_resume_point` branching + error messages.
- **Phase 4:** `TestUIRunnerCheckpoint` — 2-3 tests, envelope written when flag set + not written when unset.

### 12.2 What is NOT unit-tested

- The live Claude-backed resume round-trip. Live LLM = non-deterministic = not a unit test. Phase 3 proves it with one operator-driven live invocation; the `run_id` of that invocation is captured in the CHANGELOG entry for future forensics.
- The live GitLab/GitHub host on a resumed website stage. Same reasoning.

### 12.3 CI impact

None. All new tests stub `CheckpointStore`, `intake_runner`, `data_runner`, `website_runner`. No live LLM or live host calls. Coverage floor stays 95%; expect +2–3 points from Phase 2's new branches.

---

## 13. Verification commands per phase (consolidated)

### Phase 1
```bash
uv run pytest -q tests/orchestrator/test_pipeline.py   # existing + 9 new
uv run pytest -q                                        # full suite green
uv run ruff check src/ tests/ packages/                 # clean
uv run mypy src/                                        # clean
```

### Phase 2
```bash
uv run pytest -q tests/orchestrator/test_pipeline.py   # existing + 6 new
uv run pytest -q                                        # full suite green
uv run ruff check src/ tests/ packages/                 # clean
uv run mypy src/                                        # clean
```

### Phase 3
```bash
uv run pytest -q tests/scripts/                         # existing + 4-5 new
uv run pytest -q                                        # full suite green
uv run ruff check src/ tests/ packages/                 # clean
uv run mypy src/                                        # clean
# Live operator-driven verification (not CI-gated):
uv run python scripts/run_pipeline.py --live --host gitlab --llm data \
    --run-id run_resume_smoke --db-url sqlite:///does-not-exist.db
# Expect: FAILED_AT_DATA. Note run_id.
uv run python scripts/run_pipeline.py --resume run_resume_smoke \
    --live --host gitlab --llm data --db-url sqlite:///tests/fixtures/claims.db
# Expect: COMPLETE. Capture project_url for CHANGELOG.
```

### Phase 4
```bash
uv run pytest -q tests/ui/intake/                       # existing + 2-3 new
uv run pytest -q                                        # full suite green
uv run ruff check src/ tests/                           # clean
uv run mypy src/                                        # clean
# Live:
MPC_UI_WRITES_CHECKPOINT=1 uv run uvicorn \
    model_project_constructor.ui.intake.app:app &
# Conduct interview, note run_id from UI response
uv run python scripts/run_pipeline.py --resume <run_id> \
    --live --host gitlab --llm data
```

---

## 14. Per-phase session boundaries (for the executor)

| Session (future) | Phase | Deliverable | Stop condition |
|---|---|---|---|
| N | Phase 1 | `determine_resume_point` + `ResumePoint` + `ResumeInconsistent` + 9 unit tests. | `pytest`/`ruff`/`mypy` all green. Commit `feat(resume-phase1): ...`. Close out. |
| N+1 | Phase 2 | `PipelineConfig.resume_from` + `run_pipeline` resume branching + 6 unit tests. | Same. Commit `feat(resume-phase2): ...`. Close out. |
| N+2 | Phase 3 | `--resume` CLI + OPERATIONS + tutorial + one live round-trip. | CI green + one captured live `run_id` documented in CHANGELOG. BACKLOG lines for "resume" + "B-3" removed. Commit `feat(resume-phase3): ...`. Close out. |
| N+3 (optional) | Phase 4 | UI writes `IntakeReport.json` envelope. | CI green + one live UI → `--resume` round-trip. Commit `feat(resume-phase4): ...`. Close out. |

Each session writes its own handoff. Each handoff names the `run_id` of any live invocation used to prove completion.

---

## 15. Appendix A — File reference map

### 15.1 Files changed per phase (for executor to cross-check)

Phase 1 — 3 production + test + changelog files:
- `src/model_project_constructor/orchestrator/pipeline.py`
- `src/model_project_constructor/orchestrator/__init__.py`
- `tests/orchestrator/test_pipeline.py`
- `CHANGELOG.md`

Phase 2 — 3 files:
- `src/model_project_constructor/orchestrator/pipeline.py`
- `tests/orchestrator/test_pipeline.py`
- `CHANGELOG.md`

Phase 3 — 7 files:
- `scripts/run_pipeline.py`
- `tests/scripts/test_run_pipeline_resume.py` (NEW)
- `OPERATIONS.md` (§5 rewrite)
- `docs/tutorial.md` (new §7)
- `CHANGELOG.md`
- `BACKLOG.md` (−2 lines)
- `README.md` (+1 line)

Phase 4 — 5 files:
- `src/model_project_constructor/ui/intake/runner.py`
- `src/model_project_constructor/ui/intake/app.py`
- `tests/ui/intake/test_runner_checkpoint.py` (NEW)
- `OPERATIONS.md` (new §5.1)
- `CHANGELOG.md`

### 15.2 Files read but NOT changed (context only)

- `src/model_project_constructor/orchestrator/checkpoints.py` — the store surface this plan builds on. No changes.
- `src/model_project_constructor/orchestrator/adapters.py` — the deterministic `intake_report_to_data_request`. No changes.
- `src/model_project_constructor/orchestrator/config.py` — `OrchestratorSettings`. Phase 4 reads `checkpoint_dir` from it; no changes.
- `src/model_project_constructor/schemas/envelope.py` — `HandoffEnvelope` and `payload_schema_version`. No changes.
- `src/model_project_constructor/schemas/registry.py` — `load_payload` used by `CheckpointStore.load_payload`. No changes.

---

## 16. Sign-off checklist for the executor

Before starting **each** phase session:

- [ ] Phase 0 orientation completed per `SESSION_RUNNER.md`.
- [ ] This plan re-read from the top — specifically §5 (truth table), §6 (decisions), and the phase's §7.X (completion criteria).
- [x] §8 operator decisions — all five resolved at Session 48 review gate (2026-04-18); no further input required before Phase 1.
- [ ] Learning #11 applied: if the plan's signatures or field names contradict current code, trust the code; note the drift in the session handoff for a plan revision.

Before closing **each** phase session:

- [ ] Phase's `What DONE looks like` items all checked.
- [ ] Phase's verification commands all green.
- [ ] CHANGELOG `[Unreleased]` entry added.
- [ ] Commit message follows `feat(resume-phaseN): ...` convention.
- [ ] Handoff names the next phase explicitly (or, after Phase 3, marks the plan complete).

---

**End of plan.**
