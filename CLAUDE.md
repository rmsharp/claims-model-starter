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
- `SESSION_NOTES.md` — Session continuity: active task, handoff notes, session history. **Trimmed seven times (Sessions 222, 224, 228, 231, 235, 239, 242):** holds the newest 4 sessions. Retired records live in **seven** write-once shards under `docs/architecture-history/`. **`grep` them, never `Read` them**, and grep *all seven* — none is a prefix of another. The routing table that says which shard holds Session N is in the bullet below; it is deliberately stated once here rather than restated in this line. See "SESSION_NOTES.md is trimmed" below.
- `SESSION_RUNNER.md` — Operating procedure for every session (customized Phase 1 mapping for this project)
- `SAFEGUARDS.md` — Commit discipline, blast radius limits, mode-switching rules
- `docs/methodology/` — Framework reference (ITERATIVE_METHODOLOGY.md, HOW_TO_USE.md, workstreams/)

---

## Project-Specific Methodology Adaptations

*Additions and overrides to the base methodology at `SESSION_RUNNER.md` and `SAFEGUARDS.md` (synced from canonical, not project-owned). The base files govern unless explicitly overridden here. **Do not edit the synced files** — put customizations here.*

### Third-party methodology attribution (decision D1, `docs/planning/enterprise-migration.md` §3)

`SESSION_RUNNER.md`, `SAFEGUARDS.md`, `docs/methodology/` (12 files), the `PROJECT_LEARNINGS.md` seed rows, and `docs/architecture-history/methodology-pr2527-remediation-mpc.md` are the "Iterative Session Methodology," copyright © 2025-2026 Terrell Deppe (KJ5HST). Per the operator (2026-07-27), Terrell Deppe granted permission for this material to be used and redistributed under MIT terms. See `NOTICE` at the repository root for the full attribution and provenance record — this is the customization-seam location for that grant precisely because the synced files themselves must not be edited (rule above).

### `SESSION_RUNNER.md:209` names the OLD wiki directory. Do not fix it. (rename plan dragon 8)

Session 233 renamed `docs/wiki/claims-model-starter/` → **`docs/wiki/model_project_constructor/`** (repository-rename plan Phase 4, decision D-R2 = yes). `SESSION_RUNNER.md:209`'s "Wiki sync" paragraph still names the old path and is now **stale**. It is synced from canonical and the rule above forbids editing it — a local edit blocks future syncs — so **this bullet is the correction**, exactly as the Third-party attribution above is the correction for its own synced-file problem. The live path is `docs/wiki/model_project_constructor/`; everything else that paragraph says (hook, idempotence, `MPC_SKIP_WIKI_PUBLISH=1`, `core.hooksPath`) is still true. **Two things stay on the OLD name on purpose** and are not stale: the wiki *clone* at `~/Development/claims-model-starter.wiki` (D-R5 — GitHub's rename moves a URL, never a directory on your disk), which **permanently** pins the three lines of `scripts/publish_wiki.sh` that name it — the `WIKI_CLONE` default and the two clone instructions in its header; and the 28 frozen historical records of §3.1. **Locate those three lines by content, never by line number**: `git grep -n claims-model-starter scripts/publish_wiki.sh` → 3 hits. This bullet cited `:19`, `:24`, `:42` until Session 241 edited that file and moved two of them, which is the whole argument against pinning anything permanent to a digit. See `docs/planning/repository-rename.md` §3.3 and §7.2.

### `SESSION_NOTES.md` is trimmed (Sessions 222, 224, 228, 231, 235, 239, 242)

The live ledger holds only the newest sessions; retired records live in frozen shards, each with its own proof.

- **Retention rule.** Fire a new trim when the live file exceeds **1,500 lines** (75% of the 2,000-line agent read cap); cut back to **≤1,050 lines**; never retain fewer than **4** sessions. This is a level with hysteresis, and it is judgment. Do **not** borrow the canonical trimmer's *rate* rule — at this file's ~184-lines-per-record density its stop condition is unsatisfiable at every retention depth including one record, so a trimmer using it would trim to empty and still report the trigger unmet.
- **Shards + proofs — there are SEVEN, and a lookup must consult all of them.** `SESSION_NOTES-through-S216.md` (Sessions 216→1, 24,590 lines), `SESSION_NOTES-S220-through-S217.md` (220→217, 804 lines), `SESSION_NOTES-S224-through-S221.md` (224→221, 933 lines), `SESSION_NOTES-S227-through-S225.md` (227→225, 790 lines), `SESSION_NOTES-S231-through-S228.md` (231→228, 976 lines) `SESSION_NOTES-S235-through-S232.md` (235→232, 1,057 lines) and `SESSION_NOTES-S238-through-S236.md` (238→236, 644 lines), each beside its own `.verify.sh`. **Session N is in:** **N ≤ 216** → `SESSION_NOTES-through-S216.md`; **217 ≤ N ≤ 220** → `SESSION_NOTES-S220-through-S217.md`; **221 ≤ N ≤ 224** → `SESSION_NOTES-S224-through-S221.md`; **225 ≤ N ≤ 227** → `SESSION_NOTES-S227-through-S225.md`; **228 ≤ N ≤ 231** → `SESSION_NOTES-S231-through-S228.md`; **232 ≤ N ≤ 235** → `SESSION_NOTES-S235-through-S232.md`; **236 ≤ N ≤ 238** → `SESSION_NOTES-S238-through-S236.md`; **N ≥ 239** → `SESSION_NOTES.md`. **That table is written in the canonical clause form on purpose: the newest trim's L5 parses it out of THIS file and checks it — against the cut key, and against the record ids the named files actually contain. It is the one copy here that cannot silently go stale.** **`grep` them; never `Read` them** — and *nothing watches any of them*: the dashboard's `READ_CAP_WATCHED` is an exact-path set containing none. (The six newer shards are under the 2,000-line cap today; that is luck, not protection.) Shards are **write-once**: a new trim writes a new file with a new cut key and never appends to an existing one — which is why every shard after the first is named as a *range*, not the first's open-ended `-through-S216`. Since Session 231 that rule has enforcement across the whole lineage: **L9** compares every shard on disk against the blob committed at the commit that added it, where **L7** only ever guarded the shard it shipped with — and since Session 235 **L10** does the same for every ancestor **proof**, which L9 left unguarded. **L5 reads three copies — the live pointer block, the shard banner and this bullet's routing table; Session 231's L8 reads four more**: `README.md`'s repo map, the shard-naming rule in `docs/methodology/PROJECT_CONVENTIONS.md`, `BACKLOG.md`'s read-cap item (a third copy no earlier trim had noticed), and **this bullet's surrounding prose** — its count words were read by nothing while its table was checked. All six copies are load-bearing: update them in the trim commit or a proof goes red. **Do not trust that list at the eighth trim — re-derive it**, `git grep -l 'SESSION_NOTES-'` is the whole sweep. Session 235 did exactly that and found five further count-carrying strings inside those same four files that no assertion was reading — including one, three lines below, that was already false. Session 239 did it again and found **four files the fifth trim's sweep had never named** — and declared none of them: two match only on the phrase `SESSION_NOTES-as-rationale` (the sweep string over-matches; `git grep -l 'SESSION_NOTES-[A-Za-z0-9-]*\.md'` drops both), and two cite shard filenames inside frozen historical statements that state no census, which `L8/set` would have failed for naming only part of the set. Session 242 re-derived it a third time, confirmed that prediction, and found **four** unread count-carrying strings inside the four declared files — this bullet's own newest-sessions count, `PROJECT_CONVENTIONS.md`'s trim-ordinal sentence, and two in `BACKLOG.md`'s read-cap item. **Three of the four were found only because an adversarial review reverted each one and watched all seven proofs stay green.** All four are declared now; what is still unread, deliberately, is every ANCESTOR shard's span and size figure in those same four files — sixteen true statements nothing derives, and the eighth trim's L14. **A sweep result is a deliverable; publish it rather than repeating the sweep sentence unchanged.** And note what no proof can help with: a copy inside a **write-once** shard banner is frozen the moment the next trim lands — the S220 shard's banner says `N ≥ 221` → the live file, the S224 shard's routes Sessions 225 and up to the live file, the S227 shard's routes Sessions 228 and up there too, the S231 shard's routes Sessions 232 and up, and the S235 shard's — which predicted its own staleness "at the seventh trim" — now does the same for Sessions 236 and up; all five are falsified and none may be repaired. The S216 shard's banner is not among them and never will be: measured at the seventh trim, its own words are "states no forward-looking rule". A shard banner is a snapshot of its own cut; the live pointer block is the authority.
- **Two commits, always.** The trim commit must contain **no** record edit — not the Phase 1B stub, not the close-out. Claim the session in its own commit first, trim second, close out third. A bundled record edit registers as an added record and holds the proof red forever with zero data loss; that is the shape 5 of the 20 proofs shipped across the project fleet exhibit. The proof treats a non-zero `added` count as a FAIL, which is a deliberate divergence from the canonical tool (v1.2.0 downgraded it to a note because the canonical repo bundles by practice).
- **Declared grammar.** A record is a heading-delimited **byte span**, never a session: `/^### What Session \S+ Did$/`, column-0, fence-aware, `footer_mode=none` (asserted, not assumed). `\S+` not `\d+` (else Sessions 20B+20A merge); `Did$` anchored (else seven `### What Session N should do` headings become phantom records). 16 sessions have a record but no heading at all; 5 headings are duplicate zero-body Phase-1B stubs. None of that is special-cased — it rides inside the byte spans.
- **Run `--self-test` before trusting a green run.** A proof that has never been falsified proves less than it appears to. Any future hand-built proof ships mutants that must all be caught — **including one per assertion the proof adds beyond its ancestor.** Session 224 shipped an assertion (`L2/b0`) that no mutant could reach; an adversarial review caught it, and the fix was a mutant, not a rewrite. **Session 228 then shipped the same defect one level down** — `L5/2`, the gap/overlap check, was reachable by no mutant in its 28, because both of its ROUTING-mutating mutants happened to stay contiguous; Session 231 found it by neutering assertions one at a time and added the overlap mutant. **Sub-assertions need mutants too, and the neuter loop in the proof's header is how you find the ones that do not.** **A green `--self-test` whose mutants never exercise your new assertion is the same lie as a green run.**
- **L0–L3 are blind to WHERE the cut fell.** Moving one whole record across the boundary preserves concatenation, multiset membership *and* order at once, so L1 and L3 cannot see it — the S216 proof concedes this in prose and defers to a human. Session 224 added **L4**, which compares each side against a hand-declared cut key (never read back from the artifacts — that would be a restatement, not an assertion). Session 228 added **L5**, which holds the *prose* routing tables — the live pointer block's and the shard banner's — against that same key, because L4 proves the records landed where the key says while nothing proved the key agreed with the sentence telling a session which file to `grep`. Copy both forward; each ancestor predates one. **L5's mutants must mutate the declaration and the artifact together** — a live-file-only mutation is caught by L2 and proves nothing about L5. Session 231 added **L8** (the **four** prose copies outside every earlier proof — `README.md`'s repo map, `PROJECT_CONVENTIONS.md`'s shard-naming rule, `BACKLOG.md`'s read-cap item and `CLAUDE.md`'s own count words — held against hand-declared required/forbidden text *and* against the shard set ROUTING names; *this line said "two" until Session 235, three lines below a line saying "four more", and no assertion read either*) and **L9** (write-once for the whole lineage, not just the newest shard). Session 235 added **L10** (the same write-once enforcement for every ancestor **proof script**, held against a hand-declared freeze commit, because a weakened proof still exits 0) and **L11** (the retention rule above, enforced: that the cut fired above the trigger, landed under the target and kept the floor, with those three numbers held against the sentence that declares them). It also **narrowed L2/b3** to the shard's banner — the records half of that scan is pinned byte-for-byte by L1, so it could only ever false-positive, and on this cut it did. **That narrowing is conditional and the condition must travel with it:** b3 is safe as the banner-only form *only while* `TRANSFORM is None` and L1 is present and evaluated. A trim that ever needs a rebase, or that drops L1, must restore b3's records half in the same commit — and note that L1 has no uniquely-catching mutant, so the neuter loop will call it removable when it is not. Session 239 added **L12** (every number a trim states about the SIZE of its own artifacts — the archived heading count, the archived line count and the shard's total — measured from the artifacts, held against hand-declared integers, and held again against the formatted figures printed in the pointer block, the shard banner, `README.md` and `BACKLOG.md`; the fifth trim's three size figures were all correct and all read by nothing, which is the failure class this project self-reports more than any other). Session 242 added **L13** (a shard's own FILENAME, parsed and held against the record ids inside it — `PROJECT_CONVENTIONS.md` states the naming rule and seven trims obeyed it by hand while nothing checked it, and a misnamed shard satisfies L5/3, L5/4 and L8/set together — plus eight declared sentences stating which sessions moved, which L12 left untouched because it reads sizes, not spans; it also gave L12 and L13 an arm apiece asserting each declared literal is UNIQUE in the text it is read from, after a review defeated a substring test with a quotation of that same substring three lines away). Copy all of L0–L13 forward; each ancestor predates one.
- **Not an override of `SESSION_RUNNER.md`.** Step 14 ("focus on the ACTIVE TASK section at the top") still holds — the pointer block is inserted *above* the front matter's `---`, so `## ACTIVE TASK` → newest record is byte-identical. Step 18's ghost-session check is a **frontier** comparison against the newest session, so a trim cannot make it false-positive. Stated here so nobody re-litigates either.

### Additional Phase 0 steps

(none)

### Additional task-to-workstream mappings

(none)

### Project-specific Learnings

Project institutional memory (178 learnings, Sessions 9–242) lives in [`PROJECT_LEARNINGS.md`](PROJECT_LEARNINGS.md) — extracted from the `SESSION_RUNNER.md` table to keep `CLAUDE.md` within its size budget (Claude Code targets ~200 lines / ~25 KB). **Read it when a task resembles earlier work; append new learnings there, not here.** Base methodology-level learnings remain in `SESSION_RUNNER.md`.

### Project-specific Failure Modes

(none — the base failure modes in `SESSION_RUNNER.md` apply.)
