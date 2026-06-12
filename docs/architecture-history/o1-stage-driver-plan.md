> *This document is a concept-era artifact preserved for design archaeology. It describes the system as designed on 2026-06-12 and may not reflect current implementation. For current state, see `docs/wiki/claims-model-starter/Evolution.md` (design-decision arc) and the code itself (authoritative). See `PROJECT_CONVENTIONS.md` for archive scope.*

# O1 — `Stage`-Descriptor Pipeline Driver: Stage-Order Single-Source & God-Function Decomposition Plan

> **Status:** Draft for executor review (Session 119, planning/architecture workstream). **The plan is the deliverable; implementation is separate sessions.**
> **Author:** Session 119 — 2026-06-06.
> **Implements:** Audit `docs/audits/2026-06-01-technical-debt-audit.md` — Overhaul **O1** (`:172`, "single highest-leverage refactor"); themes **C1** (`:56-59`, the ~170-line god-function), **E3** (`:129-131`, fixed-3-stage sequence), and finding **#44** (`:212`, the `determine_resume_point` truth-table cascade); table rows **#10/#38/#40/#44** (`:197-212`) and **#13** (`:220`, the four `_envelope` saves = D5).
> **Decision (Session 119, 3-lens design panel + adversarial completeness critic, run `wf_c6ade87e-fb3`):** a frozen **`Stage` descriptor tuple `STAGE_ORDER`** is the single source of stage order + per-stage metadata; the gates and the CLI banner derive from it by index; `ResumePoint`/`PipelineStatus`/`PipelineResult`-fields are pinned to it by import-time drift guards; the god-function is decomposed via `_save`/`_halt`/`_run_or_load_stage` helpers. The adapter's execution stays **inline** (no fake runner) and the website terminal stage stays an **explicit branch** (no save-timing flag matrix).
> **Out of scope (say it twice):** the **generic-loop collapse** of `run_pipeline` into a uniform `for stage in STAGE_ORDER` iteration engine (the "true E3 composability" slice) is **deferred** to a future, re-opened phase — see §11. Three phases are committed; the loop collapse is **not** one of them.

---

## 1. Context

### 1.1 What O1 is

Audit O1 (`docs/audits/2026-06-01-technical-debt-audit.md:172`):

> *O1 — `Stage`-list pipeline driver. **Single highest-leverage refactor.** Replaces the god-function, the four save blocks, the resume tuples, and the dual stage-ordering encodings with one ordered stage list. **Prerequisite for cleanly wiring the real data step and any new pipeline stage.** Regression risk: resume-from-checkpoint is the load-bearing, side-effect-sensitive path — needs the full existing resume test matrix green plus new per-stage tests. Multi-session.*

`run_pipeline` (`orchestrator/pipeline.py:224-392`) drives the four pipeline steps **inline**, halting on the first `status != "COMPLETE"`. The stage **order** is hand-encoded **four times** that must be kept in lockstep by hand (§3.1); the four `_envelope` saves and three `FAILED_AT_*` early-returns are near-verbatim copies (§3.2-3.3); and `determine_resume_point` (`:80-157`) encodes the *inverse* of the resume gates as a manual cascade. O1 collapses the **order** into one drift-guarded `STAGE_ORDER` descriptor tuple, decomposes the god-function via three helpers, and turns the four order-copies into derivations — **without changing one byte of observable resume behavior**.

### 1.2 Why this is an architecture decision, not a quick win

The orchestrator is the audit's "**cleanest seam in the codebase**" (`:44`): agents are injected as plain callables (`IntakeRunner`/`DataRunner`/`WebsiteRunner`, `pipeline.py:48-50`), so `run_pipeline` has zero import-time dependency on any agent/LLM/DB/repo SDK. **That seam is not the debt.** The debt is that the *control structure* — stage order, resume gating, save/halt boilerplate — is duplicated and hand-synced. Three consequences make this more than cosmetic:

1. **A wrong resume tuple silently skips or double-runs a stage.** The three membership tuples (`:253/:285/:321`) and the `determine_resume_point` demotion ladder (`:139-157`) are inverses that must agree by hand; the audit calls this "the single most error-prone part of the orchestrator" (`:58`). *Mitigated today* only by heavy comments + full test coverage.
2. **The four `_envelope` saves repeat the orchestrator-source invariant four times** (`:255/:304/:323/:352`); a future edit to one is a latent divergence (D5/#13).
3. **Adding a stage is a 6-point shotgun edit** (E3, `:130`): a new `ResumePoint` literal + a new `PipelineStatus` literal + a new inline save/halt block + an entry in `_SKIPPED_STAGES_BY_RESUME_POINT` + a `determine_resume_point` branch + a resume-tuple edit at the right position.

This is the *selection-vs-behavior asymmetry* the audit names as the codebase's one root cause (`:183`): behavior (the agents) is abstracted well; *sequencing and ordering* is hardcoded. O1 is the orchestration-layer instance of the same fix O3 applied to host selection — **derive scattered enumerations from one registry / ordered source.**

### 1.3 The reframe — there is ONE order, but FOUR genuinely-different stage *shapes*

**This is the load-bearing finding of this plan.** The four steps are **not** four instances of one shape. They are **three shapes**, and a naive uniform `[Stage(runner, halt)]` list the driver iterates is a *leaky abstraction* that re-concentrates the per-stage special-casing it claims to remove (Ousterhout deletion test, `ARCHITECTURE_WORKSTREAM.md:204-212`):

| Stage | `ResumePoint` token | Runner? | Halt? | Persistence | Load-on-resume? |
|---|---|---|---|---|---|
| Intake | `intake` | `intake_runner()` | `FAILED_AT_INTAKE` if `status != COMPLETE` | `save()` envelope `IntakeReport` → `target="data"` | yes |
| **Adapter** | `intake_to_data_adapter` | **NONE — pure code** | **NONE** (`DataRequest` has no `.status`) | `save()` envelope `DataRequest` → `target="data"` | yes |
| Data | `data` | `data_runner(data_request)` | `FAILED_AT_DATA` if `status != COMPLETE` | `save()` envelope `DataReport` → `target="website"` | yes |
| **Website** | `website` | `website_runner(intake, data, target)` | `FAILED_AT_WEBSITE` if `status != COMPLETE` | **DOUBLE-SAVE**: `save()` envelope `RepoTarget` (from config) **then** `save_result()` `RepoProjectResult` (`.result.json`, not an envelope) | **NO — always re-executes** |

- The **adapter** has no injected runner (it is the deterministic `intake_qa_pairs_to_inventory` / `load_curated_inventory` / `merge_inventories` / `intake_report_to_data_request` chain, `:285-318`) and no halt predicate (`DataRequest` carries no `.status` — confirmed `packages/data-agent/.../schemas.py:46`).
- The **website** stage is terminal: it **always** re-executes when reached (the `already_complete` case is intercepted by the CLI *before* `run_pipeline`, which itself raises `ValueError` on `resume_from == "already_complete"`, `:244-247`); it **double-saves** with two *different* `CheckpointStore` methods (`save()` for the `RepoTarget` envelope, `save_result()` for the terminal `RepoProjectResult` — a `.result.json`, deliberately un-enveloped per `checkpoints.py:36-43`); and **operator `config.repo_target` always wins** (the saved `RepoTarget` is overwritten unconditionally, `:352-359`; `determine_resume_point` never reads it, `:91-94`).

**The decisive thought experiment (the roadmap's "wire the real data step + plausible validation/review stages"):** the stages the roadmap will *add* are all **mid-pipeline `runner + halt` stages** (shape 1) inserted *before* website. They do **not** need a generic iteration engine — they need the *order* single-sourced so insertion is a descriptor-row add, not a six-site shotgun edit. A uniform `stage.run()` loop would have to special-case the runner-less adapter (`if stage.runner is None: …`) and flag-disable the terminal website (`save_result` + `terminal` + `no_load` booleans) — i.e. the engine special-cases the very stages it was meant to unify. **Scope consequence:** O1 single-sources the **order** and **decomposes the god-function**; it deliberately does **not** build the generic loop. The honest reading of the audit's "ordered stage list" is *one ordered descriptor table the gating + banner derive from* — not *one loop body for four different shapes*.

---

## 2. Glossary

| Term | Meaning |
|---|---|
| **`Stage`** | A frozen dataclass of per-stage **metadata** (name, payload_type, target_agent, has_runner, halt_status, always_runs, terminal_result). **No callables** — runners stay `run_pipeline` kwargs. |
| **`STAGE_ORDER`** | The ordered `tuple[Stage, ...]` (4 rows). Its sequence is the single source of stage order; `STAGE_NAMES = tuple(s.name for s in STAGE_ORDER)` is the membership source. |
| **stage order** | The sequence `intake → intake_to_data_adapter → data → website`. Today encoded **4×** (§3.1); O1 makes `STAGE_ORDER` the one authority. |
| **`_should_run(resume, stage)`** | `resume is None or index(resume) <= index(stage)` — the one gate replacing the three membership tuples. |
| **`skipped_stages(resume)`** | Derives the CLI "Skipping: …" banner list from `STAGE_ORDER`, replacing the hand-written `_SKIPPED_STAGES_BY_RESUME_POINT` dict. |
| **drift guard** | An import-time `raise`-based parity check (reuse `model_project_constructor._vocab_guard.assert_vocab_parity`, raise-based so it survives `python -O`) pinning the hand-written `ResumePoint`/`PipelineStatus` Literals to `STAGE_ORDER`. |
| **resume policy** | The status-aware demotion + INVALID-missing-predecessor guards + `RepoProjectResult` short-circuit in `determine_resume_point`. **NOT order-encoding** — stays hand-written, only its vocabulary is pinned. |
| **characterization test** | A test that pins *currently-unguarded* behavior (envelope `target_agent`, website save-ordering, banner rows) **before** the refactor, so the refactor cannot silently change it. |
| **the loop collapse** | The deferred future phase: rewriting `run_pipeline`'s body as a generic `for stage in STAGE_ORDER` iteration engine. **Out of this plan's scope** (§11). |

---

## 3. Evidence Inventory (grep-based — MANDATORY for a refactor plan)

All counts below were produced by **direct `grep`/`pytest --co` against the working tree at HEAD `ba2e715`** (Session 119), then cross-checked against an 8-agent research workflow (§12). **The executor MUST re-run these in their Phase 0** — symbols drift (Learnings #19/#28). The exact re-run block is §13. One **per-pattern surface** per subsection (Learning #8).

> **Interpreter trap (verified).** Bare `python` on this machine is **3.10.12**, where `from datetime import UTC` (`pipeline.py:25`, `run_pipeline.py:170`) fails at *collection* with `ImportError`. The suite collects only under **`.venv/bin/python` (3.13.5)**. Every command in this plan uses `.venv/bin/python` — do **not** substitute bare `python`/`pytest`.

### 3.1 Stage-order — **4 independent encodings, none derived** (2 files)

| Encoding | Site | Form |
|---|---|---|
| 3 resume-membership gates (forward) | `pipeline.py:253`, `:285`, `:321` | `resume is None or resume == "intake"` ; `resume in (None, "intake", "intake_to_data_adapter")` ; `resume in (None, "intake", "intake_to_data_adapter", "data")` |
| demotion ladder (inverse) | `pipeline.py:139-157` | `determine_resume_point`'s presence cascade (`report_present → website/data`, `request_present → data`, `intake_present → intake_to_data_adapter`) |
| banner skip-list | `scripts/run_pipeline.py:317-323` | `_SKIPPED_STAGES_BY_RESUME_POINT: dict[ResumePoint, list[str]]` (5 hand-written rows) |
| Literal member order | `pipeline.py:59-65` | `ResumePoint = Literal["intake","intake_to_data_adapter","data","website","already_complete"]` |

`grep -nE 'resume (is None\|in \(\|==)' src/model_project_constructor/orchestrator/pipeline.py` → 4 hits (`:244` is the `already_complete` guard, **not** a stage gate; the 3 stage gates are `:253/:285/:321`). **The forward gates and the inverse ladder are exact inverses kept in lockstep by hand.**

### 3.2 Persistence boilerplate — **4 `_envelope` saves + 1 `save_result`** (1 file, D5/#13)

`grep -nE '_envelope\(|checkpoint_store\.save\b|\.save_result\(' src/model_project_constructor/orchestrator/pipeline.py`

| Save | Site | payload_type / target_agent | mechanism |
|---|---|---|---|
| Intake | `:255-264` | `IntakeReport` / `data` | `save()` envelope |
| Adapter | `:304-313` | `DataRequest` / `data` | `save()` envelope |
| Data | `:323-332` | `DataReport` / `website` | `save()` envelope |
| Website pre-save | `:352-361` | `RepoTarget` / `website` (from `config.repo_target`) | `save()` envelope |
| Website terminal | `:364-368` | `RepoProjectResult` (`name=`) | **`save_result()`** (`.result.json`) |

The keyword-only `_envelope(...)` factory is `:395-413` (`source_agent="orchestrator"`, `payload_schema_version="1.0.0"` hardcoded). **`save()` and `save_result()` are deliberately distinct (`checkpoints.py:57/70`) — O1 must NOT unify them.**

### 3.3 Halt/return boilerplate — **3 `FAILED_AT_*` returns + 1 success return** (1 file, C1)

`grep -nE 'return PipelineResult\(' src/model_project_constructor/orchestrator/pipeline.py` → 4 hits: `:266-275` (FAILED_AT_INTAKE), `:334-342` (FAILED_AT_DATA), `:370-382` (FAILED_AT_WEBSITE), `:384-392` (COMPLETE). Each rebuilds a `PipelineResult` with the **reports produced so far** + `resume_point=resume` echoed on **every** path (incl. success, `:391`).

### 3.4 Public surface the refactor must keep stable (1 file + 1 package)

`orchestrator/__init__.py:41-77` re-exports **9** symbols from `pipeline.py`: `DataRunner`, `IntakeRunner`, `PipelineConfig`, `PipelineResult`, `ResumeInconsistent`, `ResumePoint`, `WebsiteRunner`, `determine_resume_point`, `run_pipeline`. **`PipelineStatus` is `pipeline.py`-`__all__` only (`:421`), NOT package-re-exported** (`scripts` import it directly if at all). The callable type aliases `IntakeRunner`/`DataRunner`/`WebsiteRunner` (`pipeline.py:48-50`) are part of the contract. **No symbol may be removed or renamed; new symbols (`Stage`/`STAGE_ORDER`/`skipped_stages`) are additive.**

### 3.5 Consumers / test blast radius (gates every phase — mind §10's coverage trap)

| Consumer | Uses | Implication |
|---|---|---|
| `scripts/run_pipeline.py` | imports `ResumePoint` (`:79`), `determine_resume_point` (`:386`), `run_pipeline` (`:594`); owns `_SKIPPED_STAGES_BY_RESUME_POINT` (`:317`, consumed `:526`) | the banner derivation crosses the CLI↔orchestrator boundary — `skipped_stages()` is exported from the orchestrator and imported by the CLI |
| `tests/orchestrator/test_pipeline.py` | `TestHappyPath` / `TestHaltPaths` / `TestPipelineConfig` / `TestDetermineResumePoint` / `TestRunPipelineResume` | **core gate** — 34 `def test_` → **35 collected** (the happy-path test is parametrized `[gitlab][github]`) |
| `tests/scripts/test_run_pipeline_resume.py` | 7 fns | **core gate** — CLI resume integration + the single banner assertion (`:290`) |
| `tests/orchestrator/test_metrics.py` | 14 fns | **extended gate** — `record_run(result.status)` keys `status_counts` by the literal status **value** (`:101/:136/:258`); a bad status literal regresses *here*, **not** in the core gate |
| `tests/scripts/test_run_pipeline_adapter.py` | 8 fns | adapter wiring + Session-30 regression |
| `tests/agents/website/test_cli.py` | 13 fns | CLI host/CI plumbing (orthogonal; must stay green) |

**Core acceptance gate = `test_pipeline.py` + `test_run_pipeline_resume.py` = 42 collected, currently GREEN at HEAD `ba2e715`** (verified `.venv/bin/python -m pytest … --co --no-cov` → `42 tests collected`; full run → `42 passed`). Re-confirm; do NOT hardcode (Learnings #19/#28).

### 3.6 Currently-UNGUARDED behaviors O1 could silently break (the correctness target of the new tests)

The completeness critic (§12) found four behaviors the refactor risks regressing that **no current test catches**. Closing these is a deliverable of Phase O1-1 (characterization tests **before** the refactor consumes the descriptor):

| Unguarded behavior | What exists today | Risk under O1 |
|---|---|---|
| **Per-stage envelope `target_agent`** | the ONLY `target_agent ==` assertion is `tests/schemas/test_envelope_and_registry.py:52` — on a **hand-built** envelope, not a pipeline-produced one (verified). Pipeline tests only `store.has(run_id, payload_type)` (file existence keyed by `payload_type`). | moving `target_agent` into a `Stage` field and mis-transcribing it (e.g. `IntakeReport`→`website`) **passes all 42 gate tests silently.** |
| **CLI banner per resume row** | the ONLY `"Skipping"` assertion is `test_run_pipeline_resume.py:290` (the `resume="data"` row). The `website` row and the (dead-but-present) `already_complete` row are unpinned. | deriving `skipped_stages()` could break the unpinned rows green. |
| **Website save-ordering** | tests assert only *end-state* (`store.has(RepoTarget)` + `RepoProjectResult` persist even on FAILED, `test_halt_at_website…`); the `data`-halt asserts `not store.has(RepoTarget)` (`:308`). **No test asserts `RepoTarget` is saved BEFORE the runner runs and `save_result` AFTER.** | a reshuffled website block (runner-first) still passes (both files exist at the end) yet violates "config written before run". |
| **`record_run` status-key integrity** | `test_metrics.py` pins `status_counts` by literal value but is **not in the core 42-test gate**. | the `str | None` `failed_status` → `PipelineStatus` cast (§6.4) is exactly where a non-literal status could leak into a metrics key. |

---

## 4. Decision

**Adopt a frozen `Stage` descriptor tuple `STAGE_ORDER` as the single source of stage order + per-stage metadata; derive the resume gates and the CLI banner from it by index; pin `ResumePoint`/`PipelineStatus`/`PipelineResult`-fields to it with import-time drift guards; and decompose `run_pipeline`'s god-function via `_save`/`_halt`/`_run_or_load_stage` helpers — keeping the adapter inline and the website terminal stage an explicit branch.** Recommended by a 3-lens design panel (minimalist/YAGNI, extensibility/roadmap, testability) and an adversarial completeness critic (`wf_c6ade87e-fb3`); the testability design is the spine, with the minimalist design's two "do-NOT-uniformize" verdicts adopted as firm contracts.

Rationale:

1. **It targets the actual harm.** The win is eliminating the four hand-synced order encodings (a wrong tuple silently mis-runs a stage, `:58`) and the four copy-paste saves — not merely shortening a function. The order becomes a *real* single source: a future reorder fails the **build** (the drift guard), not production — the same correctness-not-cosmetics bar O3 set for `HostLiteral`.
2. **It is a deep module (Ousterhout, `ARCHITECTURE_WORKSTREAM.md:191-212`).** `STAGE_ORDER` as **data** *disperses* the order duplication into one authority (deletion test: keep). A uniform execute *loop* would *concentrate* per-stage special-casing back onto a god-record with nullable callables — moving names, not complexity (deletion test: reject). The two designs that read the deletion test correctly land on the descriptor table; the `kind`-discriminator design partially relapses.
3. **The asymmetries stay honest and visible** (`has_runner=False`, `halt_status=None`, `always_runs`, `terminal_result`) as a **test-pinned table**, not smeared across 170 lines and not hidden behind a leaky uniform interface.
4. **It is mechanically behavior-preserving.** `_should_run` is provably the inverse of the demotion ladder; Phase O1-1 *proves* it reproduces the three current gates row-for-row **before** any call site changes; and the resume *policy* (status-aware demotion, INVALID guards, `RepoProjectResult` short-circuit) is **left hand-written** — only its vocabulary pinned — because it is genuinely not pure-ordinal (§6.5).
5. **It right-sizes against the astronaut anti-pattern** (`:227`). The audit says "none of the overhauls are urgent." O1 single-sources the order the roadmap's mid-stages actually need, and **defers** the generic iteration engine until a concrete mid-stage justifies it (§11) — each phase is independently shippable, so a partial landing is a strict improvement.

> **On the audit's E3 wording (`:131`):** E3 recommends "model the pipeline as an ordered `[Stage]` list and **drive save/halt/resume generically by index**." This plan **adopts the index-driven order** (`_should_run` + the drift guard) and the **helper decomposition** of save/halt, but deliberately **reinterprets "generically"** as *one ordered descriptor source the gates/banner derive from* — **NOT** a uniform iteration loop over the four heterogeneous stage shapes (the §1.3 deletion-test argument). The literal "iterate the list" loop is the deferred slice (§11), re-opened on a concrete mid-stage. So O1 resolves the *order-encoding and persistence-boilerplate* of C1/D5/#44/E3; it does **not** claim to deliver the generic loop.

---

## 5. Alternatives Considered

| Option | What it does | Coupling / blast radius | Verdict |
|---|---|---|---|
| **C — `Stage` descriptor table + helpers, adapter inline, website explicit, loop collapse DEFERRED** | one `STAGE_ORDER` of metadata records; `_should_run`/`skipped_stages` derive 3 of 4 encodings; drift guards pin the rest; `_save`/`_halt`/`_run_or_load_stage` decompose the god-function | medium; pays for itself at the first order-edit | **CHOSEN** (this plan) |
| A — minimalist: `STAGE_NAMES` tuple + index helper + `_save`/`_halt`, **no `Stage` record** | single-source the order as a bare name-tuple; keep run_pipeline 4 labelled blocks | smallest | **Rejected as the headline, folded in** — correct that a uniform loop is a leak (its deletion-test argument is adopted in §4/§6), but a bare name-tuple loses the test-pinnable asymmetry table and the `target_agent`/`payload_type` single-source. The metadata record is worth its weight; the *loop* is not. |
| B — extensibility: `Stage` with a `kind` discriminator + 3 per-kind executors + generic loop | model each shape as a `kind`; iterate | large; doubles the at-risk surface on the most load-bearing function | **Rejected** — more machinery than A for a 4-element tuple, and its own cons admit it makes neither a 2nd terminal nor a 2nd pure-derive stage cheap, so it pays full price for two genuine singletons to optimize one *speculative* extension. The `kind` enum is redundant: the boolean fields already encode the three shapes as data. Its loop-collapse is exactly the high-risk slice this plan defers. |
| D — derive `determine_resume_point` from `index()` too | collapse the inverse ladder into ordinal math | medium | **Rejected** — the ladder is **not** pure ordinal: it interleaves status-aware demotion (`_is_saved_payload_complete`), the `RepoProjectResult` short-circuit, and three `ResumeInconsistent` guards (§6.5). An index walk would obscure load-bearing resume policy and risk re-introducing the FAILED-report-handed-to-website bug. Pin its vocabulary; keep its logic. |
| E — do nothing | keep the four hand-synced encodings | none now; 6-site shotgun edit when a stage lands | **Rejected** — but note the audit's own framing: "*none of the overhauls are urgent*." This plan is right-sized, not urgent; each phase is independently shippable. |

**Re-open trigger for the deferred loop collapse (§11):** a concrete request to **add a mid-pipeline stage** (wire the real data step by default; a validation or review stage). Until then, the descriptor table + helpers serve the four stages that exist.

---

## 6. Interface / Target Design

### 6.1 `Stage` and `STAGE_ORDER`

```python
# Home: inline in orchestrator/pipeline.py, beside ResumePoint (:59) / PipelineStatus (:52).
# Rationale (§6.6): pipeline.py already owns ResumePoint + PipelineStatus and is SDK-free;
# inlining avoids a new module AND the circular import a separate orchestrator/stages.py would
# create (it would need ResumePoint/PipelineStatus from pipeline.py, which would import STAGE_ORDER
# back). Mirrors O3's "config.py inline" home choice. (Open contract Q for Phase O1-1, §6.6.)

from dataclasses import dataclass

TargetAgent = Literal["intake", "data", "website"]   # == HandoffEnvelope.target_agent domain

@dataclass(frozen=True)
class Stage:
    name: ResumePoint                 # == its ResumePoint token
    payload_type: str                 # envelope filename / load key
    target_agent: TargetAgent         # per-stage envelope target_agent
    has_runner: bool                  # adapter=False (pure code); intake/data/website=True
    halt_status: PipelineStatus | None  # FAILED_AT_* | None (adapter & the RepoTarget save have none)
    result_field: str                 # the PipelineResult attr this stage populates
    always_runs: bool = False         # website only — no load/skip branch
    terminal_result: bool = False     # website only — save_result(RepoProjectResult), not save(envelope)

STAGE_ORDER: tuple[Stage, ...] = (
    Stage("intake", "IntakeReport", "data",
          has_runner=True,  halt_status="FAILED_AT_INTAKE",  result_field="intake_report"),
    Stage("intake_to_data_adapter", "DataRequest", "data",
          has_runner=False, halt_status=None,                result_field="data_request"),
    Stage("data", "DataReport", "website",
          has_runner=True,  halt_status="FAILED_AT_DATA",    result_field="data_report"),
    Stage("website", "RepoTarget", "website",
          has_runner=True,  halt_status="FAILED_AT_WEBSITE", result_field="project_result",
          always_runs=True, terminal_result=True),
)
STAGE_NAMES: tuple[ResumePoint, ...] = tuple(s.name for s in STAGE_ORDER)
_STAGE_INDEX: dict[str, int] = {s.name: i for i, s in enumerate(STAGE_ORDER)}
```

**Locked-down constraints (verified against the code — the load-bearing shape decision, §6.6):**

1. **No runner/halt/save CALLABLES on the record.** It is metadata only; runners stay `run_pipeline` kwargs (the `IntakeRunner`/`DataRunner`/`WebsiteRunner` aliases, `:48-50`). Reason: closures need per-run state (`intake_report`, `data_request`, `config.repo_target`) so a callable-bearing record could not be built at module import — and **import-time inspectability is the precondition for the drift guard** to derive `ResumePoint` and the CLI banner *without executing a runner*.
2. **No `kind` discriminator** (reject Design B). The boolean fields (`has_runner`, `halt_status is None`, `always_runs`, `terminal_result`) already encode the three shapes as test-pinnable data.
3. **The asymmetries are pinned by a test** (Phase O1-1): `assert STAGE_ORDER[1].has_runner is False and STAGE_ORDER[1].halt_status is None` (adapter); `assert STAGE_ORDER[3].always_runs and STAGE_ORDER[3].terminal_result and STAGE_ORDER[-1].name == "website"` (terminal-must-be-last).

### 6.2 Order derivations — the 4 encodings collapse to `STAGE_ORDER`

```python
def _should_run(resume: ResumePoint | None, stage: Stage) -> bool:
    """Replaces the 3 membership tuples (:253/:285/:321). True iff `stage`
    must (re-)execute given `resume`. A stage runs when the resume point is at
    or before it; `always_runs` (website) is unconditional."""
    return stage.always_runs or resume is None or _STAGE_INDEX[resume] <= _STAGE_INDEX[stage.name]

def skipped_stages(resume: ResumePoint | None) -> list[str]:
    """Replaces _SKIPPED_STAGES_BY_RESUME_POINT (run_pipeline.py:317). The stages
    LOADED (not re-executed) for `resume`. `already_complete` (not a stage) returns
    all four names — the dead-but-present CLI row (intercepted before the banner)."""
    if resume == "already_complete":
        return list(STAGE_NAMES)
    return [s.name for s in STAGE_ORDER if not _should_run(resume, s)]
```

- **(a)** the 3 gates → `if _should_run(resume, STAGE_ORDER[i]):`. Each current tuple is exactly "the resume tokens at-or-before this stage" = `index(resume) <= index(stage)` — proven equivalent by the Phase O1-1 truth-table test.
- **(b)** the demotion ladder → **stays hand-written** (status-aware; §6.5); its return tokens come from `STAGE_NAMES`, pinned by the guard (§6.3). It is NOT derived.
- **(c)** `_SKIPPED_STAGES_BY_RESUME_POINT` → `skipped_stages()` (exported from `pipeline.py`; the CLI imports it). The `website` row (`["intake","intake_to_data_adapter","data"]`) and the `already_complete` row (all four) are pinned by the Phase O1-1 banner-parity test **before** the dict is deleted.
- **(d)** the `ResumePoint` Literal → **stays hand-written** (mypy cannot read a runtime tuple — the same constraint O3 documents for `HostLiteral`); pinned by the guard.

### 6.3 Import-time drift guards (reuse `_vocab_guard`, don't reinvent)

Reuse the **existing** `model_project_constructor._vocab_guard.assert_vocab_parity(members, literal, *, name, reconcile_hint)` (verified: dependency-free, `raise AssertionError` so it survives `python -O`, takes a parameterized `reconcile_hint` — extracted by O3 Phase O3-1, Session 116). Three guards run at `pipeline.py` import:

```python
# 1. ResumePoint = stage names + the non-stage 'already_complete' sentinel.
#    ⚠ assert_vocab_parity does an EXACT set match against get_args(literal) (verified
#    _vocab_guard.py:45-46), so `members` MUST include the sentinel — passing
#    set(STAGE_NAMES) ALONE would (correctly) fail import with missing=['already_complete'].
#    Include it explicitly:
assert_vocab_parity(
    set(STAGE_NAMES) | {"already_complete"}, ResumePoint, name="STAGE_ORDER",
    reconcile_hint="Reconcile STAGE_ORDER with ResumePoint in pipeline.py "
                   "(ResumePoint = stage names + 'already_complete').",
)
# 2. PipelineStatus = COMPLETE + each stage's halt_status (closes the §3.6 metrics gap).
#    Exact match holds: {COMPLETE, FAILED_AT_INTAKE, FAILED_AT_DATA, FAILED_AT_WEBSITE}.
assert_vocab_parity(
    {"COMPLETE", *(s.halt_status for s in STAGE_ORDER if s.halt_status)}, PipelineStatus,
    name="STAGE_ORDER.halt_status",
    reconcile_hint="Reconcile STAGE_ORDER.halt_status with PipelineStatus in pipeline.py.",
)
# 3. result_field names a real PipelineResult attribute (closes the §3.6 wrong-field gap).
#    This is a SUBSET check, so it canNOT use assert_vocab_parity (exact-match only).
#    Use a RAISE (NOT a bare assert — python -O strips asserts; the guard must survive -O):
#       _missing = {s.result_field for s in STAGE_ORDER} - {f.name for f in fields(PipelineResult)}
#       if _missing:
#           raise AssertionError(f"STAGE_ORDER.result_field not on PipelineResult: {_missing}")
```

Guards #2 and #3 are **new** vs O3 and directly close two silent-regression surfaces the critic found (§3.6): a misspelled `failed_status` leaking into a `record_run` metrics key, and a `result_field` populating a wrong-but-valid `PipelineResult` attribute. Each guard is proven **non-vacuous** by a deliberate-mismatch RED test (the house pattern, `tests/orchestrator/test_host_registry_guard.py`).

### 6.4 Decomposition helpers (`_save` / `_halt` / `_run_or_load_stage`)

```python
def _save(store: CheckpointStore, config: PipelineConfig, *, stage: Stage, payload: BaseModel) -> None:
    """ONE place that builds the orchestrator envelope + persists the 4 envelopes
    (:255/:304/:323/:352). source_agent always 'orchestrator'; target_agent +
    payload_type come from the Stage. NOT for the terminal RepoProjectResult."""
    store.save(_envelope(
        run_id=config.run_id, correlation_id=config.correlation_id,
        source="orchestrator", target=stage.target_agent,
        payload_type=stage.payload_type, payload=payload.model_dump(mode="json"),
    ))

def _halt(config: PipelineConfig, status: PipelineStatus, *, failure_reason: str | None, **reports: Any) -> PipelineResult:
    """Collapses the 3 FAILED returns (:266/:334/:370) AND the COMPLETE return (:384).
    `reports` is the result_field-keyed dict of artifacts produced so far. resume_point
    is echoed on EVERY path (incl. COMPLETE, :391) — load-bearing for the resume matrix."""
    return PipelineResult(
        run_id=config.run_id, status=status, failure_reason=failure_reason,
        resume_point=config.resume_from, **reports,
    )

def _run_or_load_stage(
    store: CheckpointStore, config: PipelineConfig, *, stage: Stage,
    execute: Callable[[], BaseModel], payload_model: type[BaseModel],
) -> tuple[BaseModel, bool]:
    """Returns (payload, executed). If _should_run: payload = execute(); save; executed=True.
    Else: payload = load_payload(stage.payload_type); executed=False. The halt check stays at
    the CALL SITE, gated on `executed`, so a LOADED FAILED envelope NEVER halts (resume
    risk #5, §6.5). `_save` is called here for the 3 non-terminal stages; the website
    terminal block calls store.save_result() itself."""
    if _should_run(config.resume_from, stage):
        payload = execute()
        _save(store, config, stage=stage, payload=payload)
        return payload, True
    return cast(payload_model, store.load_payload(config.run_id, stage.payload_type)), False
```

**Call-site shape (intake/data — the `runner + halt` stages):**

```python
intake_report, executed = _run_or_load_stage(
    store, config, stage=_STAGE_INTAKE, execute=intake_runner, payload_model=IntakeReport)
if executed and intake_report.status != "COMPLETE":
    return _halt(config, "FAILED_AT_INTAKE",
                 failure_reason=f"intake_status={intake_report.status}; missing_fields={intake_report.missing_fields}",
                 intake_report=intake_report)
```

**Call-site shape (adapter — NO halt branch; `DataRequest` has no `.status`):**

```python
data_request, _ = _run_or_load_stage(
    store, config, stage=_STAGE_ADAPTER, payload_model=DataRequest,
    execute=lambda: _derive_data_request(intake_report, config),  # inline merge, §6.5
)
# ⚠ NO `if executed and data_request.status != "COMPLETE"` line here — halt_status is
# None and DataRequest carries no .status. Copying the intake/data halt pattern onto the
# adapter would raise AttributeError. The adapter has no halt branch by design.
```

The success path becomes one `_halt(config, "COMPLETE", failure_reason=None, intake_report=…, data_request=…, data_report=…, project_result=…)` (or keep an explicit final `PipelineResult(status="COMPLETE", …)` — a readability nicety, **but it MUST still echo `resume_point` and all four reports**; §3.6).

> **`_halt(**reports)` key safety:** `reports` keys are `PipelineResult` field names. `PipelineResult` is a `@dataclass`, so an **unknown** key raises `TypeError` at call time (it does NOT silently drop) — a typo fails loudly. A **wrong-but-valid** key (e.g. `data_report=` where `data_request=` was meant) is caught by guard #3 (result_field ⊆ fields, for the descriptor-driven path) **and** the `TestHaltPaths` retained-report-set assertions (`:337-339`, `:373-376`).

### 6.5 The adapter and website stages — KEPT special, by design (§1.3 made concrete)

**Adapter (`intake_to_data_adapter`):** uniform at the *save* boundary, special at the *execute* boundary. `has_runner=False, halt_status=None`. The inline inventory-merge code (`:285-318`) **stays inline** — it closes over `config.curated_inventory_path` (`:287`), `config.inventory_from_intake` (`:292`), `config.run_id` (`:302`), and the live `intake_report`, none of which the `DataRunner`/`IntakeRunner` aliases carry; wrapping it as a fake runner would widen a signature for one stage and hide the merge logic the inventory tests pin (`test_curated_inventory_alone_populates_request`, `test_curated_plus_intake_merges_*`). (Optionally factor the body into a private `_derive_data_request(intake_report, config) -> DataRequest` so the `execute=` lambda in §6.4 is a one-liner — purely cosmetic, no behavior change.) It routes through `_save` (`payload=data_request`). `halt_status=None` means the loop simply has no halt branch — there is no "always COMPLETE" special-case to write because `DataRequest` carries no `.status`.

**Website (terminal):** `always_runs=True, terminal_result=True`, with **ONE explicit terminal block** in the driver — NOT a save-timing flag matrix. The exact sequence is preserved **literally**: `_save(RepoTarget envelope from config.repo_target)` (config always wins, overwrites prior) → `website_runner(intake_report, data_report, config.repo_target)` → `store.save_result(run_id, "RepoProjectResult", project_result)` → halt-on-non-COMPLETE. `save_result` is **NOT** folded into `_save` (different method, different `.result.json` suffix, un-enveloped — `checkpoints.py:36-43`). The `save → run → save_result` ordering is pinned by a **new** spy test (§3.6), because the existing tests only assert end-state existence.

**`determine_resume_point` (resume policy — NOT order-encoding):** stays hand-written. Per §6.2(b)/(d), O1 only swaps its literal stage names for `STAGE_NAMES` references and pins its vocabulary; it does **not** touch its branch structure. Preserve exactly (the truth table, §9): the **check order** (3 INVALID guards → `RepoProjectResult` short-circuit *without* loading a payload → status-aware demotion in the order DataReport, DataRequest, IntakeReport); the **status-aware demotion** (a non-`COMPLETE` saved `IntakeReport`/`DataReport` re-executes its own stage — `_is_saved_payload_complete`, `:160-173`); the **`RepoProjectResult` asymmetry** (result status NOT consulted for the enum — deferred to the CLI's `_handle_already_complete`, because the website stage has irreversible side effects); **`RepoTarget` is never read** (config wins); and the **`ResumeInconsistent` vs `pydantic.ValidationError`** exception-class boundary. **Anti-goal:** do NOT "simplify" the ladder into index math while in `pipeline.py` (Design A's explicit warning) — that is where behavior-preservation is hardest and BACKLOG-critical (the FAILED-report-to-website bug class).

### 6.6 Open contract questions for Phase O1-1 (Learning #40 — resolve at Phase 1A, before code)

1. **(Load-bearing) `Stage` representation:** **metadata-only frozen record, no callables** (recommended — enables the import-time guard; preserves the runner-injection seam) vs callables/`kind`-discriminator on the record (rejected, §6.1). *This decision gates every later phase* (the guard in O1-1, the helpers in O1-3) — reversing it later would un-inspectable-ify the record and silently break the guard's ability to run at import.
2. **(Secondary) Home:** `STAGE_ORDER`/`Stage` **inline in `pipeline.py`** (recommended — mirrors O3's `config.py`-inline; avoids a circular import with `ResumePoint`/`PipelineStatus`) vs a new `orchestrator/stages.py` (cleaner separation, but requires moving `ResumePoint`/`PipelineStatus` there or accepting the import dance — and `pipeline.py` is already SDK-free, so there is no SDK-isolation reason to split).

---

## 7. Implementation Plan (per-phase)

**Three committed phases, one session each.** Each leaves the tree green and is **independently shippable** (O1-1 alone delivers a drift-guarded SoT + a hardened safety net; O1-2 alone kills the order drift; O1-3 alone decomposes the god-function). **Do NOT bundle phases** (FM #18). The generic-loop collapse is **deferred** (§11), not a phase here.

`Stage`/`STAGE_ORDER` is introduced **dormant** in O1-1 (zero consumers), then consumed by the gates/banner in O1-2 and by the helpers in O1-3 — each phase consumes only what the prior phase proved.

### 7.1 Phase O1-1 — Descriptor SoT + drift guards + safety-net extension (ZERO behavior change)

- **Goal:** `STAGE_ORDER` + helpers + three import-time guards exist and are tested; the four §3.6 unguarded behaviors are now **characterization-pinned**. `run_pipeline` / `determine_resume_point` / the CLI are **unchanged** (new symbols dormant).
- **Why first:** lands the tested, guarded single source AND extends the safety net **before** any call site consumes it — so O1-2/O1-3 refactor under a net that already catches the silent regressions.
- **Files to change:**

| File | Change | LOC est. |
|---|---|---|
| `orchestrator/pipeline.py` | add `Stage`, `STAGE_ORDER`, `STAGE_NAMES`, `_STAGE_INDEX`, `_should_run`, `skipped_stages`; `from .._vocab_guard import assert_vocab_parity`; the 3 import-time guards (§6.3). **No edit to `run_pipeline`/`determine_resume_point`.** | ~55 |
| `orchestrator/__init__.py` | re-export `Stage`, `STAGE_ORDER`, `skipped_stages` (additive `__all__`) | ~4 |
| `tests/orchestrator/test_stage_order.py` (new) | (a) `STAGE_ORDER` field-table pin incl. asymmetry fields; (b) `_should_run` reproduces all 3 current gates (a 4×5 `(stage,resume)` truth table); (c) `skipped_stages(rp)` equals the current `_SKIPPED_STAGES_BY_RESUME_POINT` for **all** rows incl. `website` + `already_complete`; (d) **3 non-vacuous guard RED tests** (mismatched stub → `AssertionError`, like `test_host_registry_guard.py`); (e) bounded **extensibility proof**: a synthetic 5th `Stage` inserted into a **COPY** of `STAGE_ORDER` partitions load-vs-run + `skipped_stages` correctly (proves the SoT scales — NOT zero-edit insertion) | +90 |
| `tests/orchestrator/test_pipeline.py` (extend) | **characterization tests (§3.6)**: load each pipeline-produced envelope and assert `target_agent` (intake→data, DataRequest→data, DataReport→website, RepoTarget→website); a spy test asserting website saves `RepoTarget` **before** the runner and `save_result` **after**; a test asserting `result.resume_point` is echoed on **every** return path — both `COMPLETE` (`:391`) and each `FAILED_AT_*` (`:274/:341/:381`) | +60 |

- **What DONE looks like:** (1) `import …orchestrator.pipeline` runs the 3 guards and stays SDK-free; (2) the truth-table test proves `_should_run` == the 3 current tuples row-for-row; (3) `skipped_stages` matches the hand-written dict for every row; (4) each guard RAISES on a deliberate mismatch (proven, not assumed); (5) the envelope-`target_agent` + website-save-ordering characterizations are green against **unchanged** code; (6) `run_pipeline`/`determine_resume_point`/`_SKIPPED_STAGES_BY_RESUME_POINT` are byte-unchanged; (7) full suite green.
- **Verification commands:**

```bash
cd /Users/rmsharp/Development/model_project_constructor; PY=.venv/bin/python   # 3.13.5 — NOT bare python (3.10, §3)
# (a) guards live + parity (the new SoT):
$PY -c "import model_project_constructor.orchestrator.pipeline as p; \
  from typing import get_args; \
  assert {s.name for s in p.STAGE_ORDER} == set(get_args(p.ResumePoint)) - {'already_complete'}; \
  assert {'COMPLETE',*(s.halt_status for s in p.STAGE_ORDER if s.halt_status)} == set(get_args(p.PipelineStatus)); \
  print('parity OK', p.STAGE_NAMES)"
# (b) guard survives -O (raise, not assert) AND clears the UTC import (uv/.venv only):
$PY -O -c "import model_project_constructor.orchestrator.pipeline; print('guard live under -O')"
# (c) new tests (subset → --no-cov, §10):
$PY -m pytest tests/orchestrator/test_stage_order.py -q --no-cov
# (d) run_pipeline body untouched this phase:
git diff -U0 src/model_project_constructor/orchestrator/pipeline.py | grep -E '^\+' | grep -E 'resume in |return PipelineResult' && echo "REGRESSION: control flow changed in O1-1" || echo "control flow untouched OK"
# (e) full suite + lint + types (coverage gate is FULL-suite only, §10):
$PY -m pytest -q && .venv/bin/ruff check src/ tests/ packages/ scripts/ && .venv/bin/mypy
```

- **Session boundary:** **One session. Close out when `STAGE_ORDER` + the 3 guards + the truth-table/banner/characterization tests are green and `run_pipeline`/`determine_resume_point` are unchanged. STOP.**

### 7.2 Phase O1-2 — Single-source the stage order (consume the descriptor for gating)

- **Goal:** the four order encodings (§3.1) all derive from `STAGE_ORDER`; 3 are derived, the 4th (the ladder) is pinned. **No behavior change.**
- **Files to change:**

| File | Change | LOC est. |
|---|---|---|
| `orchestrator/pipeline.py` | the 3 membership gates (`:253/:285/:321`) → `_should_run(resume, _STAGE_*)`; `determine_resume_point` (`:139-157`) literal stage names → `STAGE_NAMES`/`_STAGE_INDEX` refs, **keeping the branch structure** (status-demotion/INVALID/short-circuit untouched) | ~20 |
| `scripts/run_pipeline.py` | delete `_SKIPPED_STAGES_BY_RESUME_POINT` (`:317-323`); import `skipped_stages` from the orchestrator; banner (`:526`) → `skipped_stages(resume_point)` | ~8 |
| `tests/orchestrator/test_pipeline.py` (extend) | an **inverse-consistency** test: for every `(presence × status)` on-disk state, `determine_resume_point` and `_should_run` agree (the gate ⇄ ladder are exact inverses) | +30 |

- **What DONE looks like:** (1) no resume-membership tuple remains in `run_pipeline` (`grep` clean); (2) `_SKIPPED_STAGES_BY_RESUME_POINT` is gone; the banner derives from `STAGE_ORDER`; (3) `determine_resume_point`'s status-aware demotion + INVALID + short-circuit branches are behaviorally identical (the existing `TestDetermineResumePoint` proves it); (4) the banner-parity test (O1-1) + `test_run_pipeline_resume.py:290` still green; (5) full suite green.
- **Verification commands:**

```bash
cd /Users/rmsharp/Development/model_project_constructor; PY=.venv/bin/python
grep -nE 'resume in \(' src/model_project_constructor/orchestrator/pipeline.py            # expect ZERO (was :285,:321)
grep -rn '_SKIPPED_STAGES_BY_RESUME_POINT' src/ scripts/                                  # expect ZERO (dict deleted)
$PY -m pytest tests/orchestrator/test_pipeline.py::TestDetermineResumePoint \
              tests/orchestrator/test_pipeline.py::TestRunPipelineResume \
              tests/scripts/test_run_pipeline_resume.py -q --no-cov   # resume matrix + banner
$PY -m pytest -q && .venv/bin/ruff check src/ tests/ packages/ scripts/ && .venv/bin/mypy   # full suite + lint + types
```

- **Session boundary:** **One session. Close out when the order is single-sourced (gates + banner derive; ladder pinned) and the full suite + resume matrix pass. STOP.**

### 7.3 Phase O1-3 — Decompose the god-function (extract `_save` / `_halt` / `_run_or_load_stage`)

- **Goal:** the four `_envelope` saves (§3.2) collapse to `_save`; the four `PipelineResult` returns (§3.3) collapse to `_halt`; the three load-or-execute branches collapse to `_run_or_load_stage`. `run_pipeline` shrinks from ~170 to ~60 lines. Adapter inline, website explicit (§6.5). **No behavior change.**
- **Files to change:**

| File | Change | LOC est. |
|---|---|---|
| `orchestrator/pipeline.py` | add `_save`, `_halt`, `_run_or_load_stage` (§6.4); route the intake/data stages through `_run_or_load_stage` + call-site halt; the adapter through `_run_or_load_stage` (no halt) with its merge body inline; the website terminal block uses `_save` (RepoTarget) + literal `save_result` (§6.5); all returns through `_halt` (incl. COMPLETE) | ~60 / −110 |
| `tests/orchestrator/test_pipeline_helpers.py` (new) | per-helper unit tests: `_save` envelope shape per stage (target_agent/payload_type/source); `_halt` incremental-reports population per `FAILED_AT_*` + COMPLETE incl. `resume_point` echo; `_run_or_load_stage` execute-vs-load + the `(payload, executed)` halt-gating (loaded payload does NOT halt — risk #5) | +70 |

- **What DONE looks like:** (1) no inline `_envelope(...)`/`PipelineResult(...)` construction remains outside `_save`/`_halt` (the `_envelope` factory stays); (2) `_run_or_load_stage` returns `(payload, executed)` and the halt check is call-site-gated on `executed`; (3) `save()`/`save_result()` remain distinct; the website `save → run → save_result` ordering test (O1-1) + the envelope-`target_agent` test (O1-1) still green; (4) `record_run` status keys unchanged (`test_metrics.py` green — the **extended** gate); (5) full suite green, mypy clean (mind the `halt_status: str|None → PipelineStatus` cast at the `_halt` boundary), ruff clean, decoupling 2/2.
- **Verification commands:**

```bash
cd /Users/rmsharp/Development/model_project_constructor; PY=.venv/bin/python
grep -cnE 'return PipelineResult\(' src/model_project_constructor/orchestrator/pipeline.py   # expect 1 (inside _halt only)
grep -cnE 'checkpoint_store\.save\(_envelope' src/model_project_constructor/orchestrator/pipeline.py  # expect 0 (all via _save)
$PY -m pytest tests/orchestrator/test_pipeline.py tests/orchestrator/test_pipeline_helpers.py \
              tests/orchestrator/test_metrics.py tests/scripts/test_run_pipeline_resume.py \
              tests/scripts/test_run_pipeline_adapter.py -q --no-cov                          # core + extended gate
$PY -m pytest -q && .venv/bin/ruff check src/ tests/ packages/ scripts/ && .venv/bin/mypy \
  && $PY -m pytest tests/test_data_agent_decoupling.py --no-cov                               # full + lint + types + decoupling
# Runtime smoke (DEV checklist hard gate): the fixture pipeline still runs end-to-end.
$PY scripts/run_pipeline.py --host gitlab >/tmp/o1_smoke.txt 2>&1; tail -3 /tmp/o1_smoke.txt   # expect Status: COMPLETE
```

- **Session boundary:** **One session. Close out when the three helpers carry the saves/halts/load-branches, the god-function is ~60 lines, and the full suite + extended gate + mypy + ruff + decoupling + runtime smoke pass. STOP. O1 (committed scope) is complete.**

---

## 8. Impact Analysis

| Surface | Impact | Action |
|---|---|---|
| Agent-injection seam (`IntakeRunner`/`DataRunner`/`WebsiteRunner`, `:48-50`) | **none** | runners stay `run_pipeline` kwargs; no callable on the `Stage` record |
| Resume gates (`:253/:285/:321`) | collapse to `_should_run` derivations | Phase O1-2 |
| `determine_resume_point` ladder (`:139-157`) | literal names → `STAGE_NAMES` refs; **branch structure + status policy unchanged** | Phase O1-2; pinned, not derived |
| `_SKIPPED_STAGES_BY_RESUME_POINT` (`run_pipeline.py:317-323`) | deleted; banner derives via `skipped_stages()` | Phase O1-2 |
| `ResumePoint` / `PipelineStatus` Literals (`:59-65`, `:52-57`) | stay hand-written | pinned to `STAGE_ORDER` by import-time guards |
| Four `_envelope` saves (`:255/:304/:323/:352`) | collapse to `_save` | Phase O1-3; `_envelope` factory retained |
| Four `PipelineResult` returns (`:266/:334/:370/:384`) | collapse to `_halt` | Phase O1-3; `resume_point` echo on every path preserved |
| Website terminal (`save()` + `save_result()`, `:352-368`) | **`save()`/`save_result()` stay distinct**; one explicit terminal branch | Phase O1-3; save-ordering test pins it |
| Adapter merge body (`:285-318`) | **stays inline** (no fake runner) | Phase O1-3 |
| `orchestrator/__init__.py` exports | **additive** (`Stage`/`STAGE_ORDER`/`skipped_stages`) | Phase O1-1; no removals |
| `metrics.record_run(result.status)` (`run_pipeline.py:600`) | **none** (status literal integrity guarded) | guard #2 + `test_metrics.py` in the extended gate |

**What does NOT change:** the resume truth table behavior (§9); the `RepoClient`/agent seams; `CheckpointStore` (`save`/`save_result` stay distinct); the public symbol set (only additions); the `ci_platform` / host plumbing (orthogonal — O3 territory).

**What might break (risk, all guarded by §7):** a mis-transcribed `target_agent`/`payload_type` in a `Stage` row (→ envelope-target characterization test, O1-1); a reroute that re-orders `determine_resume_point`'s checks or regresses its load-laziness (→ `TestDetermineResumePoint` + inverse-consistency test); a website block reshuffle that breaks save-ordering (→ spy test, O1-1); a `failed_status`/`result_field` typo (→ guards #2/#3 + `test_metrics.py`); `save_result` accidentally folded into `_save` (→ terminal-result file test); the success path dropping its `resume_point` echo or a report (→ `TestRunPipelineResume` resume_point-on-COMPLETE pins).

---

## 9. Failure-Mode Analysis

| Failure | Surfaces in | Caught by | Result |
|---|---|---|---|
| `STAGE_ORDER` drifts from `ResumePoint` | edit-time | import-time guard #1 (`raise`, survives `-O`) | build fails loudly |
| `failed_status` misspelled / leaks a non-literal | `record_run` metrics key | guard #2 + `test_metrics.py` (extended gate) | build/test fails (was: silent wrong key) |
| `result_field` names a wrong-but-valid attr | `_halt(**reports)` | guard #3 + `TestHaltPaths` retained-report pins | build/test fails |
| Mis-transcribed envelope `target_agent` | saved envelope | **new** envelope-target characterization test (O1-1) | test fails (was: silent — §3.6) |
| Website block reshuffled (run-then-save) | save ordering | **new** save-ordering spy test (O1-1) | test fails (was: silent — §3.6) |
| Banner derivation breaks a non-`data` row | CLI banner | **new** per-row `skipped_stages` parity test (O1-1) | test fails (was: silent — §3.6) |
| `determine_resume_point` "simplified" to index math | resume policy | `TestDetermineResumePoint` (status-demotion + INVALID) + inverse-consistency test | tests fail; §6.5 anti-goal warns |
| `_run_or_load_stage` halts on a LOADED FAILED envelope | resume risk #5 | `TestRunPipelineResume` (loaded stage skips halt) + `_run_or_load_stage` unit test | test fails |
| `already_complete` guard dropped/relocated into the loop | `resume_from=="already_complete"` | `test_already_complete_raises_value_error` | test fails; §6.5 keeps the guard before any consumption |
| Subset run reports false RED (coverage 24.68%) | CI / local | §10 coverage trap (`--no-cov` for subsets; full suite for the gate) | avoided by command discipline |
| Bare `python` (3.10) used | collection | `ImportError: cannot import name 'UTC'` | avoided — all commands use `.venv/bin/python` |

---

## 10. Verification Plan

"Verified-complete" for each implementation session:

1. **Full suite green:** `.venv/bin/python -m pytest -q`. **Re-confirm the count — do NOT hardcode** (Session-119 baseline at HEAD `ba2e715`: **691/691 @ 97.14%**; each new test raises it). Core gate (`test_pipeline.py` + `test_run_pipeline_resume.py`) = **42 collected**, green at HEAD.
2. **⚠ Coverage-gate trap (verified):** `pyproject.toml:65` sets `--cov-fail-under=95`, so **any pytest subset — even `--co` collect-only — reports `FAIL Required test coverage of 95% not reached` (≈24.68% on a subset)** even when every selected test passes. **For subset runs, append `--no-cov`** (as in §7); for the coverage gate, run the **full** suite.
3. **⚠ Interpreter trap (verified):** use **`.venv/bin/python` (3.13.5)**. Bare `python` is 3.10.12 → `ImportError: cannot import name 'UTC' from 'datetime'` at collection. `-O` guard-survival proofs must be `.venv/bin/python -O`.
4. **mypy clean:** `.venv/bin/mypy` (no-arg — the exact CI scope, Learning #18). Baseline 0/62. Watch the `halt_status: PipelineStatus | None → PipelineResult.status` cast at the `_halt` boundary.
5. **ruff clean:** `ruff check src/ tests/ packages/ scripts/` (the exact CI invocation; `scripts/` IS included — O1-2 edits `run_pipeline.py`).
6. **Decoupling 2/2:** `.venv/bin/python -m pytest tests/test_data_agent_decoupling.py --no-cov`.
7. **Extended gate (O1-3):** `test_metrics.py` (status-key integrity), `test_run_pipeline_adapter.py`, `test_cli.py` must also stay green — the status-value/record_run regression surfaces **only** here, not in the core 42.
8. **Behavior-preservation proofs (positive, not just "tests pass"):** the O1-1 truth-table test proves `_should_run` == the 3 current gates row-for-row; the guard RED tests prove the guards fire; the characterization tests (envelope-target, save-ordering, banner rows) pin the §3.6 gaps **before** the refactor.
9. **Runtime smoke (DEV checklist hard gate, O1-3):** `.venv/bin/python scripts/run_pipeline.py --host gitlab` exits `Status: COMPLETE` with the full scaffold.

> **Corrected/rejected verification commands** the executor must NOT copy: (a) bare `python -m pytest` / `pytest` — fails at collection on 3.10 (`UTC`); use `.venv/bin/python`. (b) a subset `pytest …` without `--no-cov` — false RED at ~25% coverage. (c) a clean `python -O -c import` proves the guard *runs* but **not** that it *fires* — only a deliberately-mismatched stub proves non-vacuity. (d) asserting only `store.has(payload_type)` does **not** verify `target_agent` or save-ordering — load the envelope / spy the calls (§3.6).

---

## 11. Out of Scope (explicit)

- **THE GENERIC-LOOP COLLAPSE of `run_pipeline` — DEFERRED, not committed.** Rewriting the body as a uniform `for stage in STAGE_ORDER` iteration engine (the "true E3 composability" slice). **Why deferred:** (1) the four stages are three genuinely-different shapes (§1.3); a uniform loop re-concentrates that asymmetry as nullable-callable/flag special-casing (deletion test → reject, `ARCHITECTURE_WORKSTREAM.md:204-212`); (2) it is the highest-risk change against the most load-bearing truth table, for the lowest marginal payoff (LoC + a *speculative* mid-stage convenience the roadmap has not concretely asked for); (3) the audit itself says "none of the overhauls are urgent." The committed three phases already resolve C1 (god-function shrinks via helpers), D5/#13 (four saves → `_save`), #44 (order-drift → `STAGE_ORDER` + guard), and the order-encoding portion of E3/#38 — i.e. **all the parts that cause drift bugs** — without it. **Re-open trigger:** a concrete request to add a mid-pipeline stage (wire the real data step by default; a validation or review stage). At that point, re-evaluate whether a 5th linear block beats an engine; if an engine, it is a future **O1-4** (its own plan-then-implement sessions).
- **Deriving `determine_resume_point` from `index()`** (Alternative D). Its status-aware demotion + INVALID guards + `RepoProjectResult` short-circuit are resume *policy*, not order-encoding. Pin its vocabulary; keep its logic hand-written (§6.5).
- **Adding a `kind` discriminator + per-kind executors** (Design B). Redundant machinery for a 4-element tuple; the boolean fields encode the shapes as data.
- **Touching the `RepoClient` / agent seams, `CheckpointStore`, the `ci_platform`/host plumbing (O3), the LLM-provider factory (E4), or controlled-vocabulary enums (O4).**
- **Wiring the real data step / any actual new stage.** O1 makes it *cheaper* (descriptor row + guard-caught Literal edits); adding one is a separate session — and is the re-open trigger above.
- **Bundling any other backlog item** in an implementation session (FM #18).

---

## 12. Provenance

- **Audit:** `docs/audits/2026-06-01-technical-debt-audit.md` — O1 `:172`, C1 `:56-59`, E3 `:129-131`, #44 `:212`, D5/#13 `:103`/`:220`, sequencing note `:177`, structural root-cause `:183`.
- **Code read in full (Session 119):** `orchestrator/pipeline.py` (`run_pipeline`, `determine_resume_point`, `_is_saved_payload_complete`, `_envelope`, `PipelineConfig`/`PipelineResult`), `scripts/run_pipeline.py` (`main`, `_SKIPPED_STAGES_BY_RESUME_POINT`, `_resolve_resume`/`_handle_already_complete`), `orchestrator/checkpoints.py` (`CheckpointStore`), `orchestrator/__init__.py`, `docs/planning/resume-from-checkpoint-plan.md` §5-6.
- **Evidence inventory (§3):** produced by direct `grep`/`pytest --co` against the working tree at **HEAD `ba2e715`** (Session 119); cross-checked against an 8-agent research workflow (`wf_c6ade87e-fb3`: 3 mappers — test-matrix / contracts / truth-table; a 3-lens design panel — minimalist/extensibility/testability; a design judge; an adversarial completeness critic). Per **Learning #45**, every count entering this doc was re-derived by direct grep; per **Candidate #82**, every code claim (CheckpointStore signatures, `target_agent` test gap, banner pin, `_vocab_guard` signature, the 3.10 `UTC` trap, the 42-test gate) was confirmed against canonical source before being written.
- **Corrections made during verification (provenance hygiene):** (1) the workflow prompt referred to a "41/42-test gate"; **direct `pytest --co` confirms 42 collected** (34 `def test_` in `test_pipeline.py` → 35 collected via the parametrized happy-path + 7 resume = 42) — the plan states 42. (2) The completeness critic's commands used `uv run python`; the repo's established convention (O3, last 3 sessions) is `.venv/bin/python` — **both resolve to 3.13.5**; this plan standardizes on `.venv/bin/python` and documents that bare `python` (3.10) fails. (3) The published resume-plan §5 truth table shows only structural presence rows; the **code at HEAD additionally implements status-aware demotion** (resume-plan §11 risk #8) — §9 trusts the code, not the §5 table.
- **Guard precedent:** `model_project_constructor._vocab_guard.assert_vocab_parity` (raise-based, `python -O`-safe, parameterized `reconcile_hint`; extracted O3 Phase O3-1, Session 116). `tests/orchestrator/test_host_registry_guard.py` is the non-vacuous-guard-test shape to mirror; `tests/orchestrator/test_host_registry_extensibility.py` is the bounded-extensibility-proof shape.
- **Methodology:** `ARCHITECTURE_WORKSTREAM.md` (Interface-First `:126`, Refactor Heuristics / deletion test `:191-212`, anti-patterns `:226-227`); house-style mirror of `docs/planning/o3-repo-platforms-plan.md`.

---

## 13. Appendix — Full grep inventory (executor re-run block)

Run in Phase 0 **before** starting any phase. If counts drift, investigate before implementing.

```bash
cd /Users/rmsharp/Development/model_project_constructor   # verified 2026-06-06 @ HEAD ba2e715
PY=.venv/bin/python                                       # 3.13.5 — NOT bare python (3.10 → UTC ImportError)
P=src/model_project_constructor/orchestrator/pipeline.py
R=scripts/run_pipeline.py
# §3.1 — stage-order encodings (4)
grep -nE 'resume (is None|in \(|==)' "$P"                 # Expected: 4 (:244 already_complete guard + 3 stage gates :253/:285/:321)
grep -nE '_SKIPPED_STAGES_BY_RESUME_POINT' "$R"           # Expected: 2 (def :317, use :526)
grep -nE 'ResumePoint = Literal' "$P"                     # Expected: 1 (:59)
# §3.2 — persistence boilerplate (4 saves + 1 result)
grep -nE '_envelope\(|checkpoint_store\.save\b|\.save_result\(' "$P"   # Expected: save( ×4 + save_result( ×1 + _envelope factory def
# §3.3 — return boilerplate (3 FAILED + 1 COMPLETE)
grep -cnE 'return PipelineResult\(' "$P"                  # Expected: 4
# §3.4 — public exports (must stay; additions only)
grep -nE '"(run_pipeline|determine_resume_point|ResumePoint|PipelineConfig|PipelineResult|ResumeInconsistent)"' src/model_project_constructor/orchestrator/__init__.py   # Expected: 6 of the 9
# §3.6 — currently-UNGUARDED behaviors (the new-test target)
grep -rn 'target_agent ==' tests/                        # Expected: 1 (schemas/test_envelope_and_registry.py:52 — hand-built, NOT pipeline-produced)
grep -rn 'Skipping' tests/                                # Expected: 1 (test_run_pipeline_resume.py:290 — only the resume=data row)
# guard reuse target
grep -nE 'def assert_vocab_parity' src/model_project_constructor/_vocab_guard.py   # Expected: 1 (raise-based, reconcile_hint kwarg)
# gate count (the safety net)
$PY -m pytest tests/orchestrator/test_pipeline.py tests/scripts/test_run_pipeline_resume.py --co -q --no-cov | tail -1   # Expected: 42 tests collected
```

## 14. Appendix — File reference map

| Concern | File:Line |
|---|---|
| `STAGE_ORDER`/`Stage` home (recommended) | `orchestrator/pipeline.py` (inline, beside `ResumePoint:59` / `PipelineStatus:52`) |
| Shared drift guard (reuse) | `src/model_project_constructor/_vocab_guard.py` (`assert_vocab_parity`) |
| The god-function | `orchestrator/pipeline.py:224-392` (`run_pipeline`) |
| Resume gates (forward) | `pipeline.py:253`, `:285`, `:321` |
| Demotion ladder (inverse) | `pipeline.py:139-157` (`determine_resume_point`) + `_is_saved_payload_complete:160-173` |
| Banner skip-list | `scripts/run_pipeline.py:317-323` (`_SKIPPED_STAGES_BY_RESUME_POINT`), consumed `:526` |
| Four `_envelope` saves | `pipeline.py:255`, `:304`, `:323`, `:352`; `save_result` `:364`; factory `:395-413` |
| Four `PipelineResult` returns | `pipeline.py:266`, `:334`, `:370`, `:384` |
| Website terminal asymmetry | `pipeline.py:349-382`; `CheckpointStore.save`/`save_result` `checkpoints.py:57`/`:70` |
| Adapter (inline, pure) | `pipeline.py:285-318` |
| `already_complete` guards (2 modules) | `pipeline.py:244-247` (ValueError) + `run_pipeline.py:394-395` (CLI intercept) |
| Public exports | `orchestrator/__init__.py:41-77` (9 symbols; `PipelineStatus` module-only) |
| Type aliases (contract) | `pipeline.py:48-50` (`IntakeRunner`/`DataRunner`/`WebsiteRunner`) |
| Core acceptance gate | `tests/orchestrator/test_pipeline.py` (35 collected) + `tests/scripts/test_run_pipeline_resume.py` (7) = **42** |
| Extended gate | `tests/orchestrator/test_metrics.py` (status-key), `tests/scripts/test_run_pipeline_adapter.py`, `tests/agents/website/test_cli.py` |
| Resume truth table (semantics) | `docs/planning/resume-from-checkpoint-plan.md` §5-6 (+ status-demotion per §11 risk #8) |

---

## Sign-off checklist for the executor

- [ ] Re-read this whole plan.
- [ ] Re-ran §13 grep inventory; counts match (or deltas understood).
- [ ] Confirmed the core gate (`test_pipeline.py` + `test_run_pipeline_resume.py` = 42) is GREEN at your HEAD before changing anything.
- [ ] Resolved the §6.6 Phase-1A contracts: (1) **metadata-only `Stage` record** (no callables); (2) home = **`pipeline.py` inline** (or `orchestrator/stages.py`).
- [ ] Using `.venv/bin/python` everywhere (NOT bare `python` — 3.10 `UTC` trap); `--no-cov` for subset runs, full suite for the coverage gate (§10).
- [ ] Pre-flight green: `pytest && ruff && mypy && decoupling` (full suite for coverage; `--no-cov` for subsets).
- [ ] Phase 1B stub written to `SESSION_NOTES.md` **before** any code.
- [ ] Doing **exactly one** phase this session (FM #18 is the active risk); the generic-loop collapse is **deferred** (§11), not in scope.
```

