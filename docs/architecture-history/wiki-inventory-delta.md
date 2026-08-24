> *This document is a concept-era artifact preserved for design archaeology. It describes the system as designed on 2026-06-12 and may not reflect current implementation. For current state, see `docs/wiki/model_project_constructor/Evolution.md` (design-decision arc) and the code itself (authoritative). See `PROJECT_CONVENTIONS.md` for archive scope.*

# Wiki Inventory Delta Plan — Phase 3 / Phase 4 Documentation Sweep

**Status:** Draft v1 — written Session 75 (2026-05-12).
**Predecessor plan:** `docs/planning/data-source-inventory-contract-plan.md` (defines Phase 1-4 of the data-source-inventory contract; this plan addresses the documentation debt the implementation phases left behind).
**Successor sessions:** see §5 — 2-session execution split.

---

## 1. Context

The data-source-inventory contract was implemented across four phases:

| Phase | Session | Commit (HEAD-relative) | Production deliverable |
|-------|---------|------------------------|------------------------|
| 1 — schema types | 58 | (in `data-source-inventory-contract-plan.md` §9 Phase 1) | `DataSourceInventory`, `DataSourceEntry`, `ProducerMetadata`, `ColumnMetadata` |
| 2 — automated producer | 59 | (Phase 2) | `probe_information_schema` + `model-data-agent discover` CLI + `ReadOnlyDB.get_information_schema` |
| 3 — consumer integration | 60 | `f5d05a8 feat(data-agent): add consumer integration for data source inventory (Phase 3)` | `DataRequest.data_source_inventory` + `PrimaryQuery.inventory_entries_used` + prompt-rendering + truncation/sanitization |
| 4 — intake coupling | 70 | `4154227 feat(adapters): phase 4 — intake_qa_pairs_to_inventory converter + --inventory-from-intake CLI` | `intake_qa_pairs_to_inventory(intake: IntakeReport) -> DataSourceInventory` (in `src/.../orchestrator/adapters.py:113`) + `--inventory-from-intake` flag in `scripts/run_pipeline.py:477` + `pipeline.PipelineConfig.inventory_from_intake` |

The plan §8.6 named six documentation surfaces that were supposed to be updated alongside Phases 3 + 4:

1. `docs/wiki/claims-model-starter/Schema-Reference.md`
2. `docs/wiki/claims-model-starter/Data-Guide.md`
3. `docs/wiki/claims-model-starter/Worked-Examples.md`
4. `docs/wiki/claims-model-starter/Pipeline-Overview.md`
5. `packages/data-agent/USAGE.md`
6. `docs/architecture-history/architecture-plan.md` ("a note")

Session 74's handoff framed these as "skipped." The Session 75 Phase 0 audit (grep `DataSourceInventory|data_source_inventory|data source inventory` across all six surfaces) returned per-file hit counts of **13 / 7 / 7 / 3 / 2 / 0** respectively — partial coverage already exists in five of six files; only `architecture-plan.md` is fully unaware of the inventory contract. The corrected framing is therefore **"delta audit + selective fill"**, not "write from scratch."

This plan inventories what each file is missing for Phases 3 and 4, with per-file completion criteria the executor sessions can verify mechanically.

### 1.1 What this plan is

- A per-file gap inventory anchored to current line numbers.
- A suggested 2-session execution split that respects the SAFEGUARDS 5-file blast-radius rule.
- Per-file completion criteria the executor can verify with grep / file-existence checks.

### 1.2 What this plan is not

- Not the implementation. No wiki, USAGE, or architecture-plan file is edited in Session 75.
- Not a redesign of the inventory contract. The contract is `data-source-inventory-contract-plan.md`; this plan is downstream documentation alignment.
- Not a wiki-publish trigger. Wiki publish runs only when an actual wiki file changes (the executor session's commit will trigger the hook).

---

## 2. Current-state audit (grep-verified, Session 75 Phase 0)

```
$ grep -cE "DataSourceInventory|data_source_inventory|data source inventory" \
    docs/wiki/claims-model-starter/{Schema-Reference,Data-Guide,Worked-Examples,Pipeline-Overview}.md \
    packages/data-agent/USAGE.md \
    docs/architecture-history/architecture-plan.md
```

| File | Hits | Phase 3 coverage | Phase 4 coverage | Status |
|------|------|------------------|------------------|--------|
| `packages/data-agent/USAGE.md` | 13 | Full (Examples 4 + 5, §"Data source inventory") | Partial — "interview" producer listed as future; new `intake_qa_pairs_to_inventory` API + `--inventory-from-intake` flag NOT documented | Phase 4 gap only |
| `docs/wiki/claims-model-starter/Data-Guide.md` | 7 | Full (new §"Providing a data source inventory" lines 101-122; producer classes listed) | Partial — "interview producer (reference implementation deferred until pilot demand)" prose is now stale (Phase 4 landed Session 70); "pilot demand" language outdated | Phase 4 gap only |
| `docs/wiki/claims-model-starter/Worked-Examples.md` | 7 | Full (Example 1 Step 3 §"Optional: attaching a data source inventory" lines 79-96) | Missing — no walkthrough using `--inventory-from-intake` against any intake fixture | Phase 4 gap |
| `docs/wiki/claims-model-starter/Schema-Reference.md` | 3 | Partial — `DataRequest.data_source_inventory` field is documented (lines 216-223) and `PrimaryQuery.inventory_entries_used` is documented (lines 267-272), BUT the four inventory types themselves (`DataSourceInventory`, `DataSourceEntry`, `ProducerMetadata`, `ColumnMetadata`) are not given their own §; the Schema layout table §1 (line 15-22) does not list them; the Key Files table §13 (lines 506-516) does not list them | N/A — Schema-Reference is type-focused; Phase 4 is an adapter, not a schema | Phase 3 schema-listing gap |
| `docs/wiki/claims-model-starter/Pipeline-Overview.md` | 2 | Partial — Data Agent section (lines 55-62) mentions inventory in input + behavior; precedence rules + `inventory_entries_used` mentioned | Missing — Orchestrator section step 2 (line 76) does not mention the intake→inventory adapter; no mention of `--inventory-from-intake` flag in agent summary | Phase 4 gap + minor Phase 3 amplification |
| `docs/architecture-history/architecture-plan.md` | 0 | Missing — §5.2 `DataRequest` (lines 285-306) doesn't include the new field; §5.3 `DataReport` `PrimaryQuery` (lines 321-327) doesn't include `inventory_entries_used`; §7 "Data Agent Reuse Interface" (lines 435+) doesn't mention the inventory plug-in contract; no inline reference to `data-source-inventory-contract-plan.md` anywhere | Missing — §7 doesn't mention intake-to-inventory adapter | Phase 3 + Phase 4 inline-note gaps (per plan §8.6 "a note" was the agreed scope — not a full rewrite of §5.2/5.3/7) |

---

## 3. Per-file delta inventory

Each subsection states: **current coverage / what's missing / what to add / file-anchored completion criteria**. The executor session uses §3.X to drive a single file's edit pass.

### 3.1 `packages/data-agent/USAGE.md` (Phase 4 gap)

**Current coverage (lines verified Session 75):**
- §"Example 4 — Data-source discovery (`discover` CLI)" lines 184-238 — Phase 2 producer.
- §"Example 5 — Inventory-aware run (consumer integration)" lines 240-296 — Phase 3 consumer.
- §"Public API" lines 298-329 — includes `DataSourceInventory`, `DataSourceEntry`, `ProducerMetadata`, `ColumnMetadata`, `probe_information_schema`.
- §"Data source inventory" lines 331-355 — lists four producer classes; describes "Interview" as "converter from stakeholder-named systems captured by the intake agent (Guidewire, Duck Creek, etc.) into inventory entries" and says "Phase 3 (shipped) ... Callers who do not set the field continue to work unchanged."

**What's missing (Phase 4 — Session 70):**
- The "Interview" producer class is described as future (line 343) but the Session 70 commit shipped `intake_qa_pairs_to_inventory(intake: IntakeReport) -> DataSourceInventory` in `src/.../orchestrator/adapters.py:113`. The package-USAGE perspective should note that this converter lives in the main orchestrator (not the data-agent package) since the data-agent doesn't import `IntakeReport` by design (decoupling guarantee §"Decoupling guarantee" lines 366-372).
- No mention of the `--inventory-from-intake` orchestrator flag (`scripts/run_pipeline.py:477`). Because USAGE.md is package-scoped, the cross-reference should be brief — a one-line pointer to `scripts/run_pipeline.py --help` or the corresponding wiki page, not a code example duplicated from the orchestrator side.

**What to add:**
1. In §"Data source inventory" (around line 343), update the "Interview" bullet to reflect Phase 4 shipped status — something like: *"Interview — converter (`intake_qa_pairs_to_inventory`, shipped Phase 4) from stakeholder-named systems captured by the intake agent (Guidewire, Duck Creek, etc.) into inventory entries with `producer_type="interview"`. Lives in the orchestrator package, not data-agent — see Pipeline-Overview.md."*
2. In §"Data source inventory" closing paragraph (around lines 347-355), append: *"Phase 4 (shipped) wires the orchestrator's `--inventory-from-intake` flag in `scripts/run_pipeline.py` to that converter; see the wiki Pipeline-Overview for the pipeline-mode flow."*

**Completion criteria (executor must verify, one-shot greps):**
- `grep -c "Phase 4" packages/data-agent/USAGE.md` ≥ 2.
- `grep -c "intake_qa_pairs_to_inventory\|--inventory-from-intake\|inventory-from-intake" packages/data-agent/USAGE.md` ≥ 1.
- Tests + lint unchanged (USAGE.md not on tooling input paths).

**Blast radius:** 1 file.

### 3.2 `docs/wiki/claims-model-starter/Data-Guide.md` (Phase 4 gap)

**Current coverage (lines verified Session 75):**
- §"Providing a data source inventory" lines 101-122 — describes Phase 3 consumer behavior + three producer classes (curated / automated / interview).

**What's missing:**
- Line 109 describes interview producer as: *"Interview — convert stakeholder-named systems from an `IntakeReport`'s `qa_pairs` (**reference implementation deferred until pilot demand**)."* That parenthetical is now factually wrong — the reference implementation shipped Session 70 (`intake_qa_pairs_to_inventory` + `--inventory-from-intake`).

**What to add:**
1. Update line 109's parenthetical: *"reference implementation deferred until pilot demand"* → *"shipped Phase 4 as `intake_qa_pairs_to_inventory` in `orchestrator/adapters.py`; engaged via `scripts/run_pipeline.py --inventory-from-intake`"*.
2. Optionally append a one-line pipeline example to §"Providing a data source inventory" closing paragraph showing the flag usage, mirroring the existing Python example style. Keep it short — full pipeline run details belong in Pipeline-Overview.md, not Data-Guide.md.

**Completion criteria:**
- `grep -c "shipped Phase 4\|--inventory-from-intake\|intake_qa_pairs_to_inventory" docs/wiki/claims-model-starter/Data-Guide.md` ≥ 1.
- `grep -c "deferred until pilot demand" docs/wiki/claims-model-starter/Data-Guide.md` == 0 (stale prose removed).
- Tests + lint unchanged.

**Blast radius:** 1 file. **Triggers wiki publish hook** (file is under `docs/wiki/claims-model-starter/`).

### 3.3 `docs/wiki/claims-model-starter/Worked-Examples.md` (Phase 4 gap)

**Current coverage (lines verified Session 75):**
- Example 1 Step 3 §"Optional: attaching a data source inventory" lines 79-96 — Phase 3 walkthrough with `tests/fixtures/sample_curated_inventory.json`.

**What's missing:**
- No walkthrough for Phase 4 (`--inventory-from-intake`). The subrogation example's `qa_pairs` in `tests/fixtures/subrogation.yaml` are an ideal driver for showing the converter's output shape (one or more `producer_type="interview"` entries derived from stakeholder-named systems).

**What to add:**
1. After the existing §"Optional: attaching a data source inventory" block (after line 96), add a sibling §"Optional: deriving an inventory from the intake interview" sub-section showing:
    - The CLI invocation: `uv run python scripts/run_pipeline.py --host gitlab --inventory-from-intake` (1-line command).
    - A short prose paragraph describing what the converter does: reads `IntakeReport.qa_pairs`, extracts stakeholder-named systems, emits `DataSourceEntry` records with `producer_type="interview"`. Cite `src/model_project_constructor/orchestrator/adapters.py:113` for the converter and `scripts/run_pipeline.py:477` for the flag.
    - One sentence on precedence when combined with `--curated-inventory` (curated wins on duplicate `fully_qualified_name`, interview entries enrich — per plan §9.4 / Phase 4 spec).
2. Optionally update §"Reproducing a worked example" (lines 239-253) to mention the `--inventory-from-intake` flag in the variant invocations.

**Completion criteria:**
- New sub-section heading exists (verifiable by `grep -c "deriving an inventory from the intake interview\|--inventory-from-intake" docs/wiki/claims-model-starter/Worked-Examples.md` ≥ 1).
- Cited line numbers (`adapters.py:113`, `run_pipeline.py:477`) match current code (executor re-verifies at edit time — Learning #11).
- Tests + lint unchanged.

**Blast radius:** 1 file. **Triggers wiki publish hook.**

### 3.4 `docs/wiki/claims-model-starter/Schema-Reference.md` (Phase 3 schema-listing gap)

**Current coverage (lines verified Session 75):**
- §5 `DataRequest` lines 207-223 — `data_source_inventory: DataSourceInventory | None` field documented.
- §5 `PrimaryQuery` lines 259-272 — `inventory_entries_used: list[str]` documented.
- §13 Key Files table lines 506-516 — lists data-agent schemas as one row.

**What's missing:**
- The four inventory Pydantic types (`DataSourceInventory`, `DataSourceEntry`, `ProducerMetadata`, `ColumnMetadata`) live in `packages/data-agent/src/model_project_constructor_data_agent/schemas.py` (and are re-exported via `src/model_project_constructor/schemas/v1/data.py`) but are not documented in §5 alongside `DataRequest` / `DataReport`. A reader landing on Schema-Reference can see the field exists on `DataRequest` but cannot find the type definition without leaving the page.
- §1 "Schema layout" table (lines 15-22) says "5 registered payload schemas" — accurate, since the inventory is a payload-field type, not a top-level registered payload. So §1 does NOT need changes; this is correct as-is. (Calling this out to prevent over-scoping at edit time.)

**What to add:**
1. In §5 (after the existing `DataRequest` block, before `QualityCheck` at line 227), add a new sub-section §5.X "DataSourceInventory and nested types" with:
    - `ColumnMetadata` — fields per `packages/data-agent/.../schemas.py` (read the file to get current field list; per Learning #11, trust the code).
    - `ProducerMetadata` — fields per same file.
    - `DataSourceEntry` — fields + the cross-field validator on `producer_id` (per plan §4.3).
    - `DataSourceInventory` — top-level fields + the `extra="forbid"` invariant + the `schema_version` pin.
    - A one-sentence note that these are part of the data-agent package (consistent with the §5 preamble at line 187-191) and re-exported from `src/.../schemas/v1/data.py`.
2. Optionally update §13 Key Files table to add a row for the inventory types (or note them in the existing data-agent row).

**Completion criteria:**
- New §5.X sub-section exists; covers all four types.
- `grep -c "class DataSourceInventory\|class DataSourceEntry\|class ProducerMetadata\|class ColumnMetadata" docs/wiki/claims-model-starter/Schema-Reference.md` ≥ 4.
- Field lists match `packages/data-agent/.../schemas.py` at edit time (Learning #11 verification).
- Tests + lint unchanged.

**Blast radius:** 1 file. **Triggers wiki publish hook.**

### 3.5 `docs/wiki/claims-model-starter/Pipeline-Overview.md` (Phase 4 gap + minor Phase 3 amplification)

**Current coverage (lines verified Session 75):**
- §"Agent summary — Data Agent" lines 55-62 — mentions `DataSourceInventory` in input + `inventory_entries_used` in behavior + precedence prose.

**What's missing:**
- §"Orchestrator" lines 71-79: step 2 says "DATA — adapts `IntakeReport` to `DataRequest`, produces `DataReport`" — does not mention that this adaptation optionally derives a `DataSourceInventory` from `qa_pairs` when `--inventory-from-intake` is set.
- §"Agent summary — Data Agent" line 60 lists CLI interfaces (`model-data-agent run`, `model-data-agent discover`) but does not mention the orchestrator-side `scripts/run_pipeline.py --inventory-from-intake` mode (which crosses the agent boundary — fair to omit from the Data-Agent-only summary, but the Orchestrator section is the natural home).

**What to add:**
1. In §"Orchestrator" step 2 (line 76), expand to a 2-line bullet: *"DATA — adapts `IntakeReport` to `DataRequest`, optionally deriving a `DataSourceInventory` from `IntakeReport.qa_pairs` when `--inventory-from-intake` is set (via `intake_qa_pairs_to_inventory` in `orchestrator/adapters.py`), produces `DataReport`."*
2. Optionally append a one-line note to §"Orchestrator" that the `--inventory-from-intake` flag is documented in `scripts/run_pipeline.py --help` and shown in Worked-Examples §1 Step 3.

**Completion criteria:**
- `grep -c "inventory-from-intake\|intake_qa_pairs_to_inventory" docs/wiki/claims-model-starter/Pipeline-Overview.md` ≥ 1.
- Step 2 bullet mentions both `IntakeReport` → `DataRequest` adaptation AND optional inventory derivation.
- Tests + lint unchanged.

**Blast radius:** 1 file. **Triggers wiki publish hook.**

### 3.6 `docs/architecture-history/architecture-plan.md` (Phase 3 + Phase 4 inline note)

**Current coverage:** **None.** Zero hits across the file.

**What's missing — and the constraint per plan §8.6:**
- Plan §8.6 explicitly says the deliverable for architecture-plan.md is **"a note"**, not a rewrite. The architecture-plan is a historical design document (`docs/architecture-history/`) — its schema sections (§5.2 `DataRequest`, §5.3 `DataReport`, §7 Data Agent Reuse Interface) describe the v1 schema and the v1 reuse principle. Rewriting them risks confusing the historical-as-of-design-time record with current state.
- The inventory contract has its own forward-looking design doc at `docs/planning/data-source-inventory-contract-plan.md`. The architecture-plan note's job is to **point readers there**, not to duplicate the design.

**What to add:**
1. Add a single block-quote or admonition near §5.2 `DataRequest` (around line 285) — *"Note (Phase 3, Session 60): `DataRequest` accepts an optional `data_source_inventory: DataSourceInventory | None` field not shown above; see `docs/planning/data-source-inventory-contract-plan.md` for the contract design and `docs/wiki/claims-model-starter/Schema-Reference.md` §5 for the current types."*
2. Add a matching note near §5.3 `DataReport` `PrimaryQuery` (around line 321) — *"Note (Phase 3, Session 60): `PrimaryQuery` carries an additional `inventory_entries_used: list[str]` field recording inventory provenance; see the contract plan for details."*
3. Optionally add a note to §7 "Data Agent Reuse Interface" (around line 435) — *"Note (Phase 4, Session 70): the orchestrator's `intake_qa_pairs_to_inventory` adapter (`src/.../orchestrator/adapters.py`) implements the 'interview' producer class from the inventory contract, engaged via `scripts/run_pipeline.py --inventory-from-intake`. See `docs/planning/data-source-inventory-contract-plan.md` §5.3."*

**Completion criteria:**
- `grep -c "data_source_inventory\|inventory_entries_used\|data-source-inventory-contract-plan" docs/architecture-history/architecture-plan.md` ≥ 2 (at least two of the three notes landed).
- No structural changes to §5.2 / §5.3 / §7 (the existing schema bodies remain intact — verifiable by `git diff --stat` showing +N lines, ~0 lines removed).
- Tests + lint unchanged.

**Blast radius:** 1 file. **Does NOT trigger wiki publish hook** (not under `docs/wiki/claims-model-starter/`).

---

## 4. Cross-file invariants

These constraints apply to **every** execution session and to **every** file in this plan:

1. **No new wiki page is created.** All edits are to existing files. (Pipeline-Overview, Data-Guide, Worked-Examples, Schema-Reference already exist.)
2. **No structural restructuring.** Edits are additive (new bullets, new sub-sections, new prose paragraphs) — they do NOT renumber existing sections, rename headings, or remove existing prose unless explicitly noted (the one exception: §3.2 Data-Guide.md asks the executor to update the stale "deferred until pilot demand" parenthetical).
3. **Cite line numbers at edit time, not at plan-write time.** This plan cites current line numbers, but per Learning #11 the executor MUST re-grep + re-read the target file before writing line-number citations into the edit — line numbers shift on every insert.
4. **No edits to `data-source-inventory-contract-plan.md` itself.** That document is the upstream design; the wiki delta is downstream.
5. **No edits to `CHANGELOG.md` Phase 3/4 entries.** Those are historical-record (append-only); see Learning #32 — historical entries describe what was added when, not current state.
6. **Wiki publish hook fires on any wiki file change.** SESSION_RUNNER.md Phase 3E mandates running `scripts/publish_wiki.sh` after any commit that touches `docs/wiki/claims-model-starter/*.md`. The 2-session split below groups wiki edits to amortize a single publish invocation per session.

---

## 5. Execution sessions (suggested split)

The 6 files are split across **2 executor sessions** to respect SAFEGUARDS' 5-file blast-radius rule. Each session is bounded; the plan recommends an ordering but the operator can re-split if scope tightens.

### Session A — wiki-side deltas (5 files; triggers wiki publish)

**Scope (`docs/wiki/claims-model-starter/*.md` + `packages/data-agent/USAGE.md`):**

| File | Plan §  | Estimated insert size |
|------|---------|------------------------|
| `Schema-Reference.md` | §3.4 | ~30-50 lines (new §5.X with four types) |
| `Data-Guide.md` | §3.2 | ~1 line edit + 1 short paragraph |
| `Worked-Examples.md` | §3.3 | ~15-25 lines (new sub-section in Example 1) |
| `Pipeline-Overview.md` | §3.5 | ~2-3 line bullet expansion |
| `USAGE.md` | §3.1 | ~3-5 line update in §"Data source inventory" |

**Why grouped:** All four wiki files trigger the same publish hook; running it once per session is cheaper. USAGE.md is grouped here because the Data-Guide / Worked-Examples / Pipeline-Overview edits cross-reference it ("see USAGE.md") — keeping them in lock-step prevents pointer-to-stale-prose.

**Deliverable:** all five files edited, gates green, single commit, `scripts/publish_wiki.sh` run.

**Completion criteria (mechanical):**
- All five §3.X grep checks pass.
- `pytest -q` 588/588 (USAGE.md / wiki files not on tooling input paths; expect zero test delta).
- `ruff check src/ tests/ packages/ scripts/` clean.
- `mypy src/` and `mypy packages/data-agent/src/` clean.
- `scripts/publish_wiki.sh` runs without error.

**Blast radius:** 5 files. Right at the SAFEGUARDS limit. **No additional unrelated edits in this session.**

### Session B — architecture-plan note (1 file; no wiki publish)

**Scope (`docs/architecture-history/architecture-plan.md` only):**

| File | Plan § | Estimated insert size |
|------|--------|------------------------|
| `architecture-plan.md` | §3.6 | ~6-9 lines total (2-3 notes, ~3 lines each) |

**Why separate:**
- Different surface class (historical design doc vs current wiki).
- Does NOT trigger the wiki publish hook — clean small commit.
- Different verification grep target.
- Lower blast radius leaves room for the executor session to pick up an adjacent task if scope is light.

**Deliverable:** one file edited, gates green, single commit, NO wiki publish.

**Completion criteria:**
- §3.6 grep checks pass.
- `pytest -q` 588/588.
- ruff + mypy unchanged.

**Blast radius:** 1 file.

### Sequencing recommendation

Run **Session A first**, **Session B second**. Rationale:
- Session A's wiki edits create the citation targets that Session B's architecture-plan notes point at (e.g., the §3.6 note for §5.2 says *"see Schema-Reference.md §5"* — if §5 hasn't yet grown the inventory sub-section, the cross-reference is broken until Session A lands).
- Session B is small enough that operator could bundle it with whatever the next BACKLOG item turns out to be, if scope is right.

---

## 6. Non-goals

- **Not adding new schema fields or types.** This is documentation only.
- **Not changing the architecture-plan's §5.2 / §5.3 / §7 design.** Only annotating with forward pointers.
- **Not regenerating the schema sections from code.** Executor reads current schemas at edit time (Learning #11) for the Schema-Reference §3.4 type body, but does not pull in unrelated changes.
- **Not updating CHANGELOG.md for "Phase 3 docs" or "Phase 4 docs"** — the doc updates ARE the deliverable, so each executor session gets a normal CHANGELOG entry at close-out. The plan §8.6 rows are not retroactively re-completed.
- **Not bumping `schema_version`** anywhere. Documentation alignment doesn't touch schema versions.

---

## 7. Risks + mitigations

| Risk | Mitigation |
|------|------------|
| Line numbers in §3 drift between plan-write and execution | Executor re-greps each anchor before editing (Learning #11). |
| Session A hits 6+ files due to inadvertent cross-file edit | Plan explicitly names 5 files; SAFEGUARDS rule caps further inserts; commit incrementally if needed. |
| `Data-Guide.md` removal of "deferred until pilot demand" is a destructive prose edit, not additive | Verified by `git diff` review at commit time; the parenthetical was factually wrong post-Session-70 — removal restores accuracy. |
| Wiki publish hook fails mid-session | SESSION_RUNNER.md Phase 3E says it's idempotent — re-run after fixing. |
| Schema-Reference §3.4 type bodies drift from `schemas.py` between sessions | Executor reads `packages/data-agent/src/model_project_constructor_data_agent/schemas.py` at edit time (Learning #11), not from this plan. |

---

## 8. Grep-based completion evidence (for plan-readers)

The current-state hit counts in §2 were generated by:

```bash
grep -cE "DataSourceInventory|data_source_inventory|data source inventory" \
    docs/wiki/claims-model-starter/Schema-Reference.md \
    docs/wiki/claims-model-starter/Data-Guide.md \
    docs/wiki/claims-model-starter/Worked-Examples.md \
    docs/wiki/claims-model-starter/Pipeline-Overview.md \
    packages/data-agent/USAGE.md \
    docs/architecture-history/architecture-plan.md
```

Post-execution (after Session A + Session B), expected counts (mechanically verifiable):

| File | Pre | Post (lower bound) |
|------|-----|--------------------|
| Schema-Reference.md | 3 | ≥ 7 (existing 3 + four new `class` blocks) |
| Data-Guide.md | 7 | ≥ 7 (one prose phrase swapped + optionally one added) |
| Worked-Examples.md | 7 | ≥ 9 (existing 7 + new sub-section) |
| Pipeline-Overview.md | 2 | ≥ 3 (existing 2 + Orchestrator step 2 mention) |
| USAGE.md | 13 | ≥ 14 (existing 13 + one Phase 4 update) |
| architecture-plan.md | 0 | ≥ 2 (at least two of three notes) |

---

## 9. Plan checklist (Session 75)

- [x] Plan document written with file paths and line numbers.
- [x] Per-file delta inventory (§3.1-§3.6) with current line-number citations.
- [x] Each per-file delta has explicit completion criteria with grep commands.
- [x] Cross-file invariants documented (§4).
- [x] Per-session split with blast-radius accounting (§5).
- [x] Non-goals documented (§6).
- [x] Grep-based current-state evidence (§2 table).
- [x] Expected post-state grep counts (§8 table).
- [x] Each execution session marked as "separate session" with a STOP point.
- [x] Plan committed; no implementation work bundled in Session 75 (FM #18 / #19 respected).
