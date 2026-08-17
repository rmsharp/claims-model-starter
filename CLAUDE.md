# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## SESSION PROTOCOL — FOLLOW BEFORE DOING ANYTHING

**Read and follow `SESSION_RUNNER.md` step by step.** It is your operating procedure for every session. It tells you what to read, when to stop, and how to close out.

**Three rules you will be tempted to violate:**
1. **Orient first** — Read SAFEGUARDS.md -> SESSION_NOTES.md -> run `methodology_dashboard.py` -> git status -> report findings -> WAIT FOR THE USER TO SPEAK
2. **1 and done** — One deliverable per session. When it's complete, close out. Do not start the next thing.
3. **Auto-close** — When done: evaluate previous handoff, self-assess, document learnings, write handoff notes, commit, report, STOP.

`SESSION_RUNNER.md` documents known failure modes and their countermeasures. The protocol compensates for documented tendencies to skip orientation, skip close-out, and continue past the deliverable.

## What This Project Is

**Model Project Constructor** — A multi-agent pipeline that takes a business idea from intake interview through data collection, validation, and initial model website creation, delivered as a GitLab project.

### The 6-Step Pipeline

1. **Business Intake Interview** — An agent conducts a guided discussion at go/modelintake to capture: business problem, proposed solution, model solution (target + inputs), estimated value
2. **Intake Report** — The intake agent writes a summary report and hands off to the data collection agent
3. **Data Collection & Validation** — An agent creates queries to collect relevant data, writes quality-check queries, and confirms expectations about data
4. **Data Report & Handoff** — The data agent summarizes queries and hands off (with queries) to the model website agent
5. **Initial Model Website** — An agent creates a GitLab project with a draft website containing: Business Understanding, Implementation Plans & Measuring Value, Data section (query explanation, validation, EDA), Initial model build & evaluation (feature engineering, selection, initial models)
6. **Data Science Team Handoff** — The GitLab project includes results from steps 2-4, plus ideas for additional tests and potential extensions

### Domain Context

This tool serves a **claims organization within a property & casualty insurance company** (auto and property policies). The intake agent acts as an expert data scientist, business analyst, and consultant focused on this domain.

### Agent Design Principles

Each agent in the pipeline follows these principles (derived from `docs/architecture-history/initial_purpose.txt`):

1. **Agents produce structured reports, not free-form text.** Every agent's output has a defined schema with required sections. The receiving agent should be able to parse and act on the report without ambiguity.

2. **Agents hand off explicitly.** Step N writes a report, then hands it (and any artifacts like queries) to Step N+1. There is no shared state — everything the next agent needs must be in the handoff.

3. **The intake agent interviews, not interrogates.** It asks one question at a time (max 20), converging on the 4 output sections. It guides the business stakeholder with its own domain expertise — it doesn't just transcribe answers.

4. **The data agent is potentially reusable.** The `docs/architecture-history/initial_purpose.txt` notes that this agent "would likely be useful for just writing queries in general" for analyst teams. Design it with reuse in mind.

5. **The website agent produces a draft, not a finished product.** The model website is an initial scaffold for the data science team to refine. It should contain reasonable defaults and clearly mark areas that need human judgment.

### Worked Examples (from docs/architecture-history/initial_purpose.txt)

**Step 2 example:** The intake agent interviews a stakeholder about subrogation recovery in P&C claims. The output document describes: the business problem (lower subrogation outcomes due to new claims system), proposed solution (prompts/external systems to guide adjusters), model solution (supervised classification predicting successful subrogation), and estimated value (10% improvement in recovery rates = hundreds of thousands to millions annually).

**Step 3 note:** The data agent should be designed so it can also serve as a standalone query-writing tool for analyst teams (especially DAs) who spend significant time writing queries. Speeding up query work enables exploratory analysis that is currently infeasible.

## Key Files

- `docs/architecture-history/initial_purpose.txt` — Original project vision with pipeline description and worked examples for Steps 2 and 3
- `BACKLOG.md` — Active and upcoming tasks, broken down by milestone
- `ROADMAP.md` — Pipeline overview table, milestone sequence, feature inventory
- `SESSION_NOTES.md` — Session continuity: active task, handoff notes, session history. **Trimmed (Session 222):** holds the newest ~6 sessions. Sessions 216→1 are frozen in `docs/architecture-history/SESSION_NOTES-through-S216.md` — **`grep` that shard, never `Read` it** (24,564 lines). See "SESSION_NOTES.md is trimmed" below.
- `SESSION_RUNNER.md` — Operating procedure for every session (customized Phase 1 mapping for this project)
- `SAFEGUARDS.md` — Commit discipline, blast radius limits, mode-switching rules
- `docs/methodology/` — Framework reference (ITERATIVE_METHODOLOGY.md, HOW_TO_USE.md, workstreams/)

---

## Project-Specific Methodology Adaptations

*Additions and overrides to the base methodology at `SESSION_RUNNER.md` and `SAFEGUARDS.md` (synced from canonical, not project-owned). The base files govern unless explicitly overridden here. **Do not edit the synced files** — put customizations here.*

### Third-party methodology attribution (decision D1, `docs/planning/enterprise-migration.md` §3)

`SESSION_RUNNER.md`, `SAFEGUARDS.md`, `docs/methodology/` (12 files), the `PROJECT_LEARNINGS.md` seed rows, and `docs/architecture-history/methodology-pr2527-remediation-mpc.md` are the "Iterative Session Methodology," copyright © 2025-2026 Terrell Deppe (KJ5HST). Per the operator (2026-07-27), Terrell Deppe granted permission for this material to be used and redistributed under MIT terms. See `NOTICE` at the repository root for the full attribution and provenance record — this is the customization-seam location for that grant precisely because the synced files themselves must not be edited (rule above).

### `SESSION_NOTES.md` is trimmed (Session 222)

The live ledger holds only the newest sessions; retired records live in a frozen shard with a proof.

- **Retention rule.** Fire a new trim when the live file exceeds **1,500 lines** (75% of the 2,000-line agent read cap); cut back to **≤1,050 lines**; never retain fewer than **4** sessions. This is a level with hysteresis, and it is judgment. Do **not** borrow the canonical trimmer's *rate* rule — at this file's ~184-lines-per-record density its stop condition is unsatisfiable at every retention depth including one record, so a trimmer using it would trim to empty and still report the trigger unmet.
- **Shard + proof.** `docs/architecture-history/SESSION_NOTES-through-S216.md` and its `.verify.sh`. **`grep` the shard; never `Read` it** — it is 24,564 lines and *nothing watches it*: the dashboard's `READ_CAP_WATCHED` is an exact-path set that does not contain it. Shards are write-once; a new trim writes a new cut key.
- **Two commits, always.** The trim commit must contain **no** record edit — not the Phase 1B stub, not the close-out. Claim the session in its own commit first, trim second, close out third. A bundled record edit registers as an added record and holds the proof red forever with zero data loss; that is the shape 5 of the 20 proofs shipped across the project fleet exhibit. The proof treats a non-zero `added` count as a FAIL, which is a deliberate divergence from the canonical tool (v1.2.0 downgraded it to a note because the canonical repo bundles by practice).
- **Declared grammar.** A record is a heading-delimited **byte span**, never a session: `/^### What Session \S+ Did$/`, column-0, fence-aware, `footer_mode=none` (asserted, not assumed). `\S+` not `\d+` (else Sessions 20B+20A merge); `Did$` anchored (else seven `### What Session N should do` headings become phantom records). 16 sessions have a record but no heading at all; 5 headings are duplicate zero-body Phase-1B stubs. None of that is special-cased — it rides inside the byte spans.
- **Run `--self-test` before trusting a green run.** A proof that has never been falsified proves less than it appears to. Any future hand-built proof ships mutants that must all be caught.
- **Not an override of `SESSION_RUNNER.md`.** Step 14 ("focus on the ACTIVE TASK section at the top") still holds — the pointer block is inserted *above* the front matter's `---`, so `## ACTIVE TASK` → newest record is byte-identical. Step 18's ghost-session check is a **frontier** comparison against the newest session, so a trim cannot make it false-positive. Stated here so nobody re-litigates either.

### Additional Phase 0 steps

(none)

### Additional task-to-workstream mappings

(none)

### Project-specific Learnings

Project institutional memory (95 learnings, Sessions 9–222) lives in [`PROJECT_LEARNINGS.md`](PROJECT_LEARNINGS.md) — extracted from the `SESSION_RUNNER.md` table to keep `CLAUDE.md` within its size budget (Claude Code targets ~200 lines / ~25 KB). **Read it when a task resembles earlier work; append new learnings there, not here.** Base methodology-level learnings remain in `SESSION_RUNNER.md`.

### Project-specific Failure Modes

(none — the base failure modes in `SESSION_RUNNER.md` apply.)
