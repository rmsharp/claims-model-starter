# Evolution Page + Documentation Convention Plan

**Session 43 — 2026-04-18 — Planning deliverable.** Evidence-based implementation plan for (a) the project-local maintainer/user documentation convention, (b) `wiki/Evolution.md` initial write + update discipline, (c) `docs/planning/` → archive-directory move with in-file banners, and (d) refinements to CHANGELOG.md and wiki/Changelog.md.

Per `SESSION_RUNNER.md` Planning Sessions protocol: this plan is the deliverable. Implementation happens in separate sessions (one per phase).

---

## 1. Goal and non-goals

### Goal

The project currently has one place where a new reader can learn *why the system looks the way it does*: `SESSION_NOTES.md` (752 KB, raw, append-only). Someone joining the project — another developer, a contractor reviewing the codebase, or the maintainer reviewing the state of things — has no digestible narrative for "how the application grew from original concept to current state." This plan fills that gap with a **wiki page** while simultaneously establishing a **project-local documentation convention** that disambiguates the four existing "what changed" surfaces.

### Non-goals

- Changes to upstream methodology framework material (`docs/methodology/README.md`, `ITERATIVE_METHODOLOGY.md`, `HOW_TO_USE.md`, `workstreams/*.md` — copyrighted by T. Deppe).
- Changes to SESSION_NOTES.md structure or content conventions.
- Changes to `wiki/Changelog.md` content shape (per Design Decision 5 below — opener addition only).
- Implementation of any phase below (plan only).
- Any change to `docs/methodology/` that would pollute imported upstream material.

---

## 2. Design decisions (settled prior to this plan)

Five decisions settled through multi-turn design discussion across Session 42's conversational envelope. All are **locked**; the plan executes against them.

| # | Decision | Detail |
|---|---|---|
| 1 | **Inward vs outward split** | Maintainer-facing (inward): methodology files, repo root `.md` files, `docs/` excluding `docs/wiki/`. User/implementer-facing (outward): `docs/wiki/claims-model-starter/*`. Exact user-supplied wording: *"the wiki is the outward-facing documentation; all other documentation in the repo root and docs/ is internal to the iterative methodology."* |
| 2 | **Three-surface split for "what changed"** | `CHANGELOG.md` — inward, maintainer-facing, commit-linked ledger. `wiki/Changelog.md` — outward, release-shaped audience summary (unchanged). `wiki/Evolution.md` — outward, decision-arc narrative (new). Each surface carries a per-file opener pointing to the others. |
| 3 | **Evolution update cadence** | No scheduled updates. User-requested only (triggers: sharing code with another developer; wanting a current-state assessment). **Full rewrite** each time, not incremental. Review discipline: "last updated" banner at top + CHANGELOG as completeness checklist + SESSION_NOTES as rationale source + deliberately-omitted appendix + diff-against-prior on rewrite #2 onward. |
| 4 | **Planning-doc disposition** | Physically move to an archive directory (option b). In-file banner at top of each moved doc. Still publicly linkable as primary-source archaeology. |
| 5 | **`wiki/Changelog.md` content unchanged** | Content shape fits the user-facing role. Only the per-file opener is added. |

---

## 3. Evidence-based inventory

### 3.1 `docs/planning/` contents (6 files)

```
docs/planning/architecture-approaches.md       (Session 1 exploration)
docs/planning/architecture-approaches.pdf      (PDF of same)
docs/planning/architecture-plan.md             (Session 2 authoritative plan)
docs/planning/github-gitlab-abstraction-plan.md (Session 10 phased plan — Phases A-D complete)
docs/planning/pilot-readiness-audit.md         (Pilot acceptance)
docs/planning/scope-b-plan.md                  (Scope B plan — B1+B2 shipped, B3 optional/pending)
```

### 3.2 Outward-wiki references to `docs/planning/*` (link-update required under Phase 2)

Four hits across three files:

| File | Line | Reference |
|---|---|---|
| `docs/wiki/claims-model-starter/Architecture-Decisions.md` | 3 | "For the full architecture plan, see `docs/planning/architecture-plan.md`" |
| `docs/wiki/claims-model-starter/Changelog.md` | 3 | "phases map to the structure in `docs/planning/architecture-plan.md` §14" |
| `docs/wiki/claims-model-starter/Contributing.md` | 195 | "Cross-module refactors need a written plan (in `docs/planning/`) before code changes" |
| `docs/wiki/claims-model-starter/Contributing.md` | 212 | "Reference any related `docs/planning/` document" |

### 3.3 Inward references to `docs/planning/*` (link-update required under Phase 2, except historical)

| File | Hits | Disposition |
|---|---|---|
| `README.md` | 4 (lines 9, 108, 197, 201, 202) | Update to new archive path |
| `OPERATIONS.md` | 1 (line 6) | Update |
| `TROUBLESHOOTING.md` | 1 (line 6) | Update |
| `ROADMAP.md` | 4 (lines 5, 31, 80, 81, 82) | Update (line 81 references `scope-b-plan.md`; see §4.2 framing) |
| `BACKLOG.md` | 1 (line 7) | Update (references `scope-b-plan.md`; see §4.2) |
| `SESSION_RUNNER.md` | 4 (lines 57, 90, 241, 259) | **Special case — methodology convention.** See §4.7 below. |
| `CHANGELOG.md` | 7 historical entries | **DO NOT UPDATE** — append-only history. |
| `SESSION_NOTES.md` | many historical entries | **DO NOT UPDATE** — append-only history. |

### 3.4 `contributor-facing` grep result (word-tightening target)

Single hit: `CHANGELOG.md:8`. Verified via `grep -rn "contributor-facing" .`. No other occurrences.

### 3.5 Outward wiki inventory (21 pages, currently all freshness-tracked)

```
Home.md, _Sidebar.md
Getting-Started.md, Pipeline-Overview.md, Content-Recommendations.md
Intake-Interview-Design.md, Agent-Reference.md, Schema-Reference.md
Generated-Project-Structure.md, Governance-Framework.md, Security-Considerations.md
Development-Workflow.md, Monitoring-and-Operations.md, Data-Guide.md
Software-Bill-of-Materials.md, Glossary.md, Architecture-Decisions.md
Extending-the-Pipeline.md, Worked-Examples.md, Changelog.md, Contributing.md
```

No existing page named `Evolution.md`, `Project-Evolution.md`, or similar — no namespace collision.

### 3.6 `docs/methodology/README.md` provenance

License section at `docs/methodology/README.md:253-255`: "Copyright 2026 by Terrell Deppe." This is **upstream framework material** imported via the Quick Start instruction *"Use this methodology: https://github.com/KJ5HST/methodology"*. Editing it directly would:
- Pollute material that may be overwritten on a future methodology update.
- Conflate project-local conventions with generic framework guidance.

**Conclusion:** the user's intent ("methodology README should state explicitly...") needs a project-local home. See §4.4 below.

### 3.7 Repo-root concept-era artifacts

- `initial_purpose.txt` — referenced in CLAUDE.md as "Original project vision with pipeline description and worked examples for Steps 2 and 3." Predates the planning docs. Candidate for archive; see §4.3.

---

## 4. Open decisions — operator must confirm before Phase 1 starts

Nine decisions surfaced by evidence. Recommendations provided with rationale; operator picks.

### 4.1 Archive directory name

Candidates:
- `docs/architecture-history/`  ← **recommended**
- `docs/design-history/`
- `docs/concept-archive/`
- `docs/planning-archive/`

Rationale for `architecture-history/`: "history" signals archaeology; "architecture" matches the dominant content (architecture-plan.md, architecture-approaches.md, and three sub-plans under that umbrella). Avoids "archive" connotation of "to be deleted."

### 4.2 Archive scope — all current planning docs, or only completed?

- **Framing A (strict):** move every file in `docs/planning/`. Includes `scope-b-plan.md` despite optional B3 being pending.
- **Framing B (selective):** move plans whose **primary scope** is delivered.
  - Move: `architecture-plan.md` (phases 1-6 complete), `architecture-approaches.md` (historical exploration), `github-gitlab-abstraction-plan.md` (Phases A-D complete), `pilot-readiness-audit.md` (pilot declared), `architecture-approaches.pdf`.
  - Keep in `docs/planning/`: `scope-b-plan.md` (B3 still pending per BACKLOG.md:7).

Recommendation: **Framing B**. Tiebreaker criterion to codify in `PROJECT_CONVENTIONS.md`: *"when a plan's primary scope is delivered, move to archive regardless of optional/deferred follow-ups; the plan returns to archive when the final optional scope ships OR is formally descoped."*

### 4.3 Does `initial_purpose.txt` move too?

It is the ur-concept artifact per CLAUDE.md. It sits at repo root, which mildly violates the "docs and root md = inward" convention (it's a `.txt`, not `.md`, but same spirit).

Recommendation: **move to `docs/architecture-history/initial_purpose.txt`** with banner. Update the reference in `CLAUDE.md:25` to the new path. Evolution page references it as "concept origins."

### 4.4 Project-local convention home

Four options:

| Option | Pro | Con |
|---|---|---|
| A. Edit `docs/methodology/README.md` | Matches user's original phrasing | Pollutes upstream; may be overwritten |
| B. New `docs/methodology/PROJECT_CONVENTIONS.md` | Project-local; discoverable in methodology dir | New file |
| C. Paragraph in repo-root `README.md` | High-visibility | Mixes project-pitch content with internal convention |
| D. Paragraph in `CLAUDE.md` | Read at every session start | `CLAUDE.md` is already the agent-protocol spec; scope creep |

Recommendation: **Option B** (`docs/methodology/PROJECT_CONVENTIONS.md`). Short, project-local, doesn't pollute upstream, lives near the methodology it complements.

### 4.5 Banner exact wording (two banners to standardize)

**Evolution.md banner** (top of file):
```markdown
> *Last updated: YYYY-MM-DD (commit `<short-sha>`, after Session N). This page is a full-rewrite synthesis — not continuously updated. For commits since this date, see `CHANGELOG.md` (maintainer) or `git log`.*
```

**Archive-doc banner** (top of each moved doc):
```markdown
> *This document is a concept-era artifact preserved for design archaeology. It describes the system as designed on YYYY-MM-DD and may not reflect current implementation. For current state, see `docs/wiki/claims-model-starter/Evolution.md` (design-decision arc) and the code itself (authoritative). See `PROJECT_CONVENTIONS.md` for archive scope.*
```

Confirm both. Short-sha form preferred (7-char).

### 4.6 Review gate for Evolution rewrites (session autonomy vs. explicit approval)

- **Option 1 (autonomous):** session writes, verifies, commits, pushes — like all other sessions. User reviews post-commit.
- **Option 2 (explicit):** session writes, shows the draft, stops. User reviews interactively. Commit after explicit approval.

Recommendation: **Option 2** for Evolution rewrites only. The page is outward-facing and persistent between rewrites; errors are audience-visible and can hide for months. Worth one extra round-trip per rewrite. All other sessions continue autonomous-commit pattern.

### 4.7 SESSION_RUNNER.md planning-doc references

Four hits in SESSION_RUNNER.md (lines 57, 90, 241, 259) reference `docs/planning/` as the canonical plan destination. Under the archive move, two interpretations:

- **Interpretation A:** `docs/planning/` is the active-plan directory; completed plans get moved to archive. SESSION_RUNNER.md stays unchanged; the archive move is a one-time retrospective action for already-complete plans.
- **Interpretation B:** Completed plans live at `docs/architecture-history/`; active plans stay at `docs/planning/`. Update SESSION_RUNNER.md to clarify the split.

Recommendation: **Interpretation A** for SESSION_RUNNER.md body (no change), but add a one-line clarification to `PROJECT_CONVENTIONS.md`: *"Active plans live at `docs/planning/`. When a plan's primary scope is delivered (see §4.2 tiebreaker), move it to `docs/architecture-history/`."*

### 4.8 Evolution page filename

Candidates: `Evolution.md`, `Project-Evolution.md`, `Design-Evolution.md`, `Project-History.md`.

Recommendation: **`Evolution.md`** — concise; matches the wiki's short-name convention (`Contributing.md`, `Glossary.md`, `Changelog.md`).

### 4.9 Bundling — combine Phase 1 + Phase 4 into one session?

Current plan has four phases (see §9 phase dependency graph). Phase 4 (update-discipline doc) is small and naturally bundles with Phase 1 (convention doc) because both write to `PROJECT_CONVENTIONS.md`.

Recommendation: **bundle Phase 1 + Phase 4 into Phase 1** (single session, one file). Final plan has 3 phases, not 4.

---

## 5. Phase 1 — Project-local convention + update discipline + per-file openers + CHANGELOG word-tightening

### 5.1 Deliverables

1. **New file:** `docs/methodology/PROJECT_CONVENTIONS.md`. Contents:
   - Section 1: Inward vs outward documentation (user-supplied sentence verbatim).
   - Section 2: Three-surface split table (CHANGELOG.md, wiki/Changelog.md, wiki/Evolution.md — purpose, audience, cadence).
   - Section 3: Planning-doc archive convention (archive scope tiebreaker from §4.2; when plans move; where they move to).
   - Section 4: Evolution.md update discipline (full rewrite; CHANGELOG-as-checklist; SESSION_NOTES-as-rationale; deliberately-omitted appendix; diff-against-prior from rewrite #2; review gate per §4.6).
2. **Edit `CHANGELOG.md:8`:** `contributor-facing` → `maintainer-facing`.
3. **Prepend opener to `CHANGELOG.md`** (between title and current line 3):
   ```markdown
   > *Maintainer-facing commit-linked ledger. For the user-facing release summary, see `docs/wiki/claims-model-starter/Changelog.md`. For the design-decision arc, see `docs/wiki/claims-model-starter/Evolution.md`.*
   ```
4. **Prepend opener to `docs/wiki/claims-model-starter/Changelog.md`:**
   ```markdown
   > *Audience-facing release summary. For the maintainer commit-linked ledger, see `CHANGELOG.md` at the repository root. For the design-decision arc, see `Evolution` (sibling wiki page).*
   ```

### 5.2 Files touched

- `docs/methodology/PROJECT_CONVENTIONS.md` (new, ~150 lines)
- `CHANGELOG.md` (2 edits: line 8 word change, opener prepended)
- `docs/wiki/claims-model-starter/Changelog.md` (1 edit: opener prepended)

### 5.3 What DONE looks like

- `docs/methodology/PROJECT_CONVENTIONS.md` exists with all four sections.
- `grep -c "contributor-facing" CHANGELOG.md` returns 0.
- `grep -c "maintainer-facing" CHANGELOG.md` returns ≥1.
- Both CHANGELOG files have a blockquote opener visible in their first 10 lines.
- pytest remains 446/446 @ 97.27%.

### 5.4 Verification commands

```bash
test -f docs/methodology/PROJECT_CONVENTIONS.md
grep -c "contributor-facing" CHANGELOG.md    # expect 0
grep -c "maintainer-facing" CHANGELOG.md     # expect >= 1
head -10 CHANGELOG.md
head -10 docs/wiki/claims-model-starter/Changelog.md
uv run pytest -q                             # smoke; doc-only should be 446/446 unchanged
```

### 5.5 Session boundary

**One session.** Commit: `docs(session-N): establish project documentation convention + Evolution update discipline + per-file openers`. Close out at commit. Do not proceed to Phase 2.

---

## 6. Phase 2 — Archive directory + planning-doc move + banner + link updates

### 6.1 Deliverables

1. Create directory: `docs/architecture-history/`.
2. `git mv` per Framing B (§4.2):
   - `docs/planning/architecture-plan.md` → `docs/architecture-history/architecture-plan.md`
   - `docs/planning/architecture-approaches.md` → `docs/architecture-history/architecture-approaches.md`
   - `docs/planning/architecture-approaches.pdf` → `docs/architecture-history/architecture-approaches.pdf`
   - `docs/planning/github-gitlab-abstraction-plan.md` → `docs/architecture-history/github-gitlab-abstraction-plan.md`
   - `docs/planning/pilot-readiness-audit.md` → `docs/architecture-history/pilot-readiness-audit.md`
   - `initial_purpose.txt` → `docs/architecture-history/initial_purpose.txt` (per §4.3)
3. Prepend archive banner (§4.5 wording) to each moved `.md` file. PDF + .txt handled per §6.2 notes.
4. Update references in inward docs per §3.3 (SKIP CHANGELOG.md historical entries, SKIP SESSION_NOTES.md entirely).
5. Update references in outward wiki per §3.2 (all 4 hits).
6. Update `CLAUDE.md:25` reference to `initial_purpose.txt` path if moved.

### 6.2 Notes on non-markdown files

- `architecture-approaches.pdf`: move via `git mv`; no in-file banner possible. Acceptable — the markdown sibling carries the banner, and the PDF is rarely consulted directly.
- `initial_purpose.txt`: add banner as `.txt` (same blockquote-style prefix prose, no markdown syntax).

### 6.3 Files touched

- `docs/architecture-history/` (new directory + 6 moved files)
- `README.md`, `OPERATIONS.md`, `TROUBLESHOOTING.md`, `ROADMAP.md`, `BACKLOG.md` (link updates)
- `CLAUDE.md` (line 25 reference update)
- `docs/wiki/claims-model-starter/Architecture-Decisions.md` (line 3)
- `docs/wiki/claims-model-starter/Changelog.md` (line 3)
- `docs/wiki/claims-model-starter/Contributing.md` (lines 195, 212)
- `docs/wiki/claims-model-starter/Home.md` (if Home.md references planning — verify in Phase 2 inventory pass)

### 6.4 What DONE looks like

- `docs/architecture-history/` has all 6 moved files.
- Each moved `.md` + `.txt` file has the archive banner as its first blockquote / comment block.
- `grep -rn "docs/planning/" --include="*.md" .` returns only: (i) the archive files themselves, (ii) SESSION_NOTES.md historical entries, (iii) CHANGELOG.md historical entries, (iv) the remaining `docs/planning/scope-b-plan.md` per Framing B.
- All tests pass (pytest 446/446).
- No markdown files have broken relative links (spot-check via Grep for remaining `docs/planning/` or orphan file references).

### 6.5 Verification commands

```bash
ls docs/architecture-history/
for f in docs/architecture-history/*.md; do echo "=== $f ==="; head -5 "$f"; done
head -5 docs/architecture-history/initial_purpose.txt
# Remaining docs/planning/ references should be limited to scope-b-plan + historical entries:
grep -rn "docs/planning/" --include="*.md" . \
  | grep -v "SESSION_NOTES.md" \
  | grep -v "CHANGELOG.md" \
  | grep -v "scope-b-plan"
# Expect empty OR only the archive files themselves.
uv run pytest -q    # 446/446
```

### 6.6 Session boundary

**One session.** This is the largest phase by link-update count (~15 updates across 10+ files); use parallel Edits to parallelize. Commit: `docs(session-N): move completed plans to docs/architecture-history/ + banner + link updates`. Close out at commit. Do not proceed to Phase 3.

---

## 7. Phase 3 — `wiki/Evolution.md` initial write

### 7.1 Pre-work research

**Before writing any prose:**

1. Full read of `CHANGELOG.md` end-to-end (~380 lines, ~50 entries from Session 0 to Session 42).
2. **Classification pass** — for every CHANGELOG entry, classify as:
   - **Include** — directly material to the design-decision arc.
   - **Subsume** — absorbed into a broader decision already in the arc.
   - **Omit-as-operational** — micro fix, typo, test-count update, or session-maintenance work.
   Produce a markdown table (session, date, classification, one-line rationale). This table becomes the source of the "Deliberately omitted" appendix.
3. **Rationale extraction** — for each "Include" entry, open the corresponding session's SESSION_NOTES.md Phase 3C (learnings) and Phase 3D (handoff). Extract the WHY: what constraint motivated the decision? what alternative was considered? SESSION_NOTES is the rationale source; CHANGELOG is the completeness checklist.
4. **Thematic outline** — organize the "Include" set by theme, not chronology. Themes (candidate):
   - Concept origins (`initial_purpose.txt` — subrogation worked example; P&C insurance claims focus).
   - Foundational architecture (pipeline shape, LangGraph, Pydantic, f-string templates).
   - Intake agent arc (single prompt → LangGraph with cycles → question cap 10→20 → web UI).
   - Data agent arc (decoupled-from-intake → standalone package → real LLM backing).
   - Website agent arc (GitLab-first → platform abstraction → governance tier fan-out).
   - Platform abstraction arc (neutral rename → PyGithub adapter → per-platform CI).
   - Methodology arc (session-runner v1 → planning workstream → learnings accumulation → ghost-session countermeasures → 31 learnings).
   - Current state summary (what the system does today, in one paragraph).

### 7.2 Deliverables

1. **New file:** `docs/wiki/claims-model-starter/Evolution.md` with:
   - "Last updated" banner at top (§4.5 wording).
   - Per-file opener: *"Design-decision arc from concept to current state. For the maintainer commit-linked ledger, see `CHANGELOG.md` at the repository root. For the user-facing release summary, see the `Changelog` wiki page."*
   - Thematic narrative (per §7.1 outline).
   - "Deliberately omitted" appendix listing every `Omit-as-operational` classification with one-line rationale.
   - Reference list pointing to archived planning docs (`docs/architecture-history/*`) where Evolution says "for the original design, see..."
2. **Update `docs/wiki/claims-model-starter/_Sidebar.md`:** add Evolution entry in the appropriate section.
3. **Update `docs/wiki/claims-model-starter/Home.md`:** add Evolution to the wiki page list.
4. **Update `docs/wiki/claims-model-starter/Content-Recommendations.md`:** if "project history" / "design arc" / "evolution" appears under Known Gaps, remove that entry (closed gap). Spot-check; may not appear.

### 7.3 What DONE looks like

- `docs/wiki/claims-model-starter/Evolution.md` exists.
- Banner at top with current date + short-sha.
- Every `Include`-classified CHANGELOG entry appears in the narrative (directly or as part of a broader decision arc).
- Every `Omit-as-operational` entry appears in the "Deliberately omitted" appendix with rationale.
- Sidebar + Home updated; new page discoverable from the wiki entry points.
- pytest 446/446 @ 97.27% unchanged.
- **Review gate (§4.6):** session presents draft + stops for user review before committing.

### 7.4 Verification commands

```bash
test -f docs/wiki/claims-model-starter/Evolution.md
head -10 docs/wiki/claims-model-starter/Evolution.md      # banner visible
grep -c "Deliberately omitted" docs/wiki/claims-model-starter/Evolution.md   # expect >= 1
wc -l docs/wiki/claims-model-starter/Evolution.md          # sanity check (expect ~300-600 lines)
grep -c "Evolution" docs/wiki/claims-model-starter/_Sidebar.md   # expect >= 1
grep -c "Evolution" docs/wiki/claims-model-starter/Home.md       # expect >= 1
uv run pytest -q                                            # 446/446
```

### 7.5 Session boundary

**Probably one session, with a checkpoint for time-box safety.**

Budget: ~2-3 hours of focused work for 42 sessions of history synthesized into a decision arc. Natural checkpoint:

- **Sub-commit 1 (WIP if time-boxed):** CHANGELOG classification table + thematic outline written into a scratch file. Commit as `wip(session-N): Evolution classification + outline`.
- **Sub-commit 2:** Narrative prose written. Commit as `docs(session-N): wiki/Evolution.md initial write + sidebar + home updates`.

If Sub-commit 1 completes but the session is running long, hand off to Session N+1 for the prose. The classification table is the load-bearing artifact; the prose rewrite is more predictable once the classification exists.

**Review gate per §4.6:** the session presents the draft to the user BEFORE committing. Approval → commit. Changes requested → revise → re-present.

Close out at prose-commit (or classification-commit if split). Do not bundle with anything else.

---

## 8. Phases 4+ — future Evolution rewrites

Not part of this plan's scope. Governed by `PROJECT_CONVENTIONS.md` §4 (written in Phase 1). Key invariants for every future rewrite:

1. User-triggered only.
2. Full rewrite, not incremental.
3. CHANGELOG-as-checklist pass.
4. SESSION_NOTES-as-rationale pass.
5. Diff-against-prior review (for rewrite #2 onward).
6. "Deliberately omitted" appendix refreshed.
7. Banner updated (date + short-sha).
8. Review gate before commit.

---

## 9. Phase dependency graph

```
Phase 1 (convention + openers + word-tightening + update discipline)
    │
    ├── establishes convention referenced by Phase 2
    ├── establishes update discipline consumed by Phase 3
    ▼
Phase 2 (archive directory + move + banner + link updates)
    │
    ├── creates docs/architecture-history/ — referenced by Phase 3 Evolution
    ▼
Phase 3 (wiki/Evolution.md initial write)
    │
    └── consumes conventions (Phase 1) + archive paths (Phase 2)
```

Phases MUST run sequentially. Each is a separate session per `SESSION_RUNNER.md` Planning Sessions discipline.

---

## 10. Planning-session checklist (per SESSION_RUNNER.md §Planning Sessions)

- [x] Plan document written with file paths and line numbers.
- [x] Grep-based inventory completed for affected symbols:
  - `docs/planning/` references (§3.2, §3.3)
  - `contributor-facing` (§3.4)
  - `docs/planning/` directory contents (§3.1)
  - Wiki inventory (§3.5)
  - Upstream methodology material identification (§3.6)
- [x] Each phase has explicit completion criteria and verification commands (§5.3–5.4, §6.4–6.5, §7.3–7.4).
- [x] Each phase marked as "separate session" with a STOP point (§5.5, §6.6, §7.5).
- [ ] Close-out: evaluate predecessor, self-assess, commit, STOP (pending this turn).

---

## 11. Outstanding risks

| # | Risk | Mitigation |
|---|------|------------|
| 1 | **SESSION_RUNNER.md planning-doc references.** If `docs/planning/` remains the active-plan directory and `docs/architecture-history/` is only for completed plans, the convention is split across two directories and a future planning session might write to the wrong one. | §4.7 Interpretation A. `PROJECT_CONVENTIONS.md` §3 codifies the split explicitly. |
| 2 | **Evolution drift between rewrites.** Without a schedule, the page can sit stale for months. | Banner (§4.5) tells readers the page's currency. User-triggered cadence puts currency in operator's hands at share time. |
| 3 | **Evolution classification subjectivity.** "Include vs subsume vs omit" is judgment. Two rewrites by different sessions could classify differently. | "Deliberately omitted" appendix makes classification visible. Diff-against-prior on rewrite #2+ surfaces reclassification. |
| 4 | **Link-break during Phase 2 move.** 15+ link updates across 10+ files. Miss one and wiki renders a broken path. | §6.5 verification grep catches every remaining `docs/planning/` reference that isn't in the allowlist. |
| 5 | **`initial_purpose.txt` move breaks CLAUDE.md load-bearing pointer.** CLAUDE.md:25 references the file by path. | §6.1 step 6 explicit. |
| 6 | **Phase 3 session length.** 42 sessions of history may exceed one-session budget. | §7.5 built-in checkpoint. Sub-commit split option. |
| 7 | **Review gate (§4.6) only applies to Phase 3.** If Phases 1-2 commit autonomously and contain an error that the review would have caught, the error lives in git history until caught later. | Phases 1-2 are well-bounded; verification commands (§5.4, §6.5) are mechanical. Review gate cost-vs-benefit favors autonomous commit for those phases. |

---

## 12. Out-of-scope notes

1. **Planning-docs MAX_QUESTIONS drift (Session 42 finding).** Under Framing B, `architecture-plan.md` and `pilot-readiness-audit.md` both move to the archive. Their MAX_QUESTIONS drift becomes part of the "concept-era artifact" — NOT fixed, NOT freshness-tracked. The banner explicitly disclaims freshness. The ~9 drift hits (documented in Session 42 CHANGELOG out-of-scope block) are **resolved by the archive move** (they become archaeology, not current-state claims).

2. **MkDocs / Docusaurus / other static-site generators.** BACKLOG item for tutorial UX mentions this. Evolution.md is GitHub-flavored Markdown — works in the wiki today without additional tooling. If the project later adopts a static site generator, Evolution.md converts without changes.

3. **Multi-page Evolution split.** If the single page grows past ~800 lines in future rewrites, consider splitting into per-component Evolution pages (`Intake-Evolution.md`, etc.) with an index. Not needed for initial write; flagged for future sessions.

---

## 13. Close-out of this planning session

Per `SESSION_RUNNER.md` §Planning Sessions: the plan IS the deliverable. Session 43 closes out after committing this plan. Implementation begins in Session 44 (Phase 1), Session 45 (Phase 2), Session 46 (Phase 3) at the earliest — subject to operator confirmation of §4 open decisions.

**Operator sign-off requested before Phase 1 starts:** please review §4 (nine open decisions) and either confirm recommendations or specify alternatives.
