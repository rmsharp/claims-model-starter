> *This document is a concept-era artifact preserved for design archaeology. It describes the system as designed on 2026-06-12 and may not reflect current implementation. For current state, see `docs/wiki/claims-model-starter/Evolution.md` (design-decision arc) and the code itself (authoritative). See `PROJECT_CONVENTIONS.md` for archive scope.*

# model_project_constructor — Methodology PR #25 + PR #27 Remediation (execution brief)

*Generated 2026-06-07 from the methodology-repo master plan (`~/Development/methodology/docs/planning/adopter-pr25-27-remediation-plan.md`, project #2/§3). Wording below is captured **verbatim** from the PR-25 branch (`fix/3c-learnings-destination`) — do not improvise.*

> **This whole brief = ONE deliverable** ("1 and done"). mpc is the *clean, simple* adopter: no `bin/sync`, no vendored BOOTSTRAP/CLAUDE_TEMPLATE (so **Asset D is N/A**), no drift directives in the table. Scope is exactly: migrate → receptacle/pointer → C1/C2/C3.

## Goal

1. **Migrate** the 46 project-learning rows out of the `SESSION_RUNNER.md` "Learnings (added by sessions)" table → a new project-owned `PROJECT_LEARNINGS.md`.
2. **Restore** the table to canonical's 6 framework seed rows + new caption (C2) and update the 3C body (C1).
3. **Add** the `## Project-Specific Methodology Adaptations` receptacle to `CLAUDE.md` with a plain-link pointer (NOT an `@`-import).
4. **Apply** C3 to `HOW_TO_USE.md`.

## Verified current state (2026-06-07 — re-grep before editing)

| Item | Location |
|---|---|
| 3C body to replace (C1) | `SESSION_RUNNER.md:162` — `Update the workstream document and/or the Learnings table below:` |
| Caption to replace (C2) | `SESSION_RUNNER.md:269` — `*This table starts empty...*` |
| Learnings table | heading `:267`; data rows `~:271`–`:321`; next heading `## Launch Prompt Templates` at `:322` |
| **Table size** | **46 data rows, #1–#46, NO duplicates, NO self-referential drift rows** — straight contiguous block move |
| `CLAUDE.md` | **61 lines, no receptacle**; last heading `## Key Files :53` → append receptacle at end. Already within budget; **no slimming**. |
| C3 target | `docs/methodology/HOW_TO_USE.md:763` |
| Not present | `bin/sync`, vendored `BOOTSTRAP.md`/`CLAUDE_TEMPLATE.md` → **Asset D skipped** |

---

## Step 0 — Branch + claim

You're on `master` with a live `o4-controlled-vocabulary` session. Branch off `master` for this (don't fold it into the vocabulary deliverable): `chore/methodology-pr2527-remediation`. Write a Phase 1B claim stub per mpc's `SESSION_RUNNER.md` before technical work.

## Step 1 — Extract the 46 rows → `PROJECT_LEARNINGS.md`

Create `PROJECT_LEARNINGS.md` at the project root:

```markdown
# model_project_constructor — Project-Specific Learnings

> Migrated verbatim from `SESSION_RUNNER.md`'s "Learnings (added by sessions)" table on 2026-06-07 to keep `CLAUDE.md` lean and route project learnings to a project-owned file (methodology PR #25/#27). No content changed in the move. **Append new project learnings here, not in `CLAUDE.md` and not in `SESSION_RUNNER.md`.** Base, methodology-level learnings remain in `SESSION_RUNNER.md`.

| # | Learning | Source | When to Apply |
|---|----------|--------|---------------|
<the 46 data rows (#1–#46), cut verbatim from SESSION_RUNNER.md>
```

Cut the entire contiguous block of data rows between the caption and `## Launch Prompt Templates`. Keep them byte-for-byte. Leave the `| # | Learning | Source | When to Apply |` header+separator in the source file (the canonical seed rows go back under it in Step 2).

## Step 2 — Restore the synced table + 3C

**(a) Replace the 3C body** at `:162` — remove `Update the workstream document and/or the Learnings table below:` and paste **C1**:

> Capture what this session learned so the next session inherits it. Always update the relevant workstream document for any workstream-level pattern or anti-pattern. Then record session learnings in the right place for your audience:
>
> - **Adopter project** (you copied this `SESSION_RUNNER.md` from the methodology repo): put project learnings in your `CLAUDE.md` → **Project-Specific Methodology Adaptations** → **Project-specific Learnings** subsection. Do NOT edit the "Learnings (added by sessions)" table further down in this file — `SESSION_RUNNER.md` is synced from canonical and must stay byte-identical, or local edits will block future syncs (see BOOTSTRAP, "Customizations Go in CLAUDE.md, Not in Synced Files"). Agents read `CLAUDE.md` at session start, so a learning recorded there is applied on top of the base protocol.
> - **Canonical methodology repo** (you are dogfooding the framework on itself): record framework-level learnings by appending a new row to the "Learnings (added by sessions)" table further down in this file. This repo has no `CLAUDE.md` Adaptations section because the SESSION_RUNNER table is its learnings home; the seed rows there are real framework learnings, not placeholders. Append new rows — do not edit or overwrite existing ones.
>
> Capture, wherever it lands:

*(the existing six `- What you did...` bullets follow, unchanged)*

**(b) Replace the caption** at `:269` with **C2**:

> *These rows are the methodology's own framework learnings, recorded as the canonical repo dogfoods itself — canonical sessions append new rows here (append only; do not edit existing rows). Adopter projects do NOT edit this synced table — record project learnings in `CLAUDE.md` → Project-Specific Methodology Adaptations → Project-specific Learnings instead (see 3C).*

**(c) Put canonical's 6 framework seed rows** back under the table header (these are canonical's framework learnings, which mpc as an adopter inherits and does not edit — NOT mpc's rows):

```markdown
| # | Learning | Source | When to Apply |
|---|----------|--------|---------------|
| 1 | Plan-mode output is a draft, not a verified plan. When a prompt contains a multi-phase plan with "implement," the deliverable is a plan document with evidence-based inventory, not Phase 1 code. The gap: Phase 1's task mapping had no entry for plan-mode handoffs, so the session defaulted to "implement." Structural fix: new mapping row + FM #19. | FM #19 discovery | When a prompt contains a multi-phase plan with "implement" — recognize this as a planning workstream. |
| 2 | **Protocol discipline is perishable.** 14 consecutive clean sessions can collapse to 1/10 deliveries within 12 hours of relaxed discipline. The protocol is perishable — it doesn't maintain itself. Each session must actively re-internalize it, not assume it's "already known." The compounding loop works only when every link in the chain is complete. | Field observation | Whenever you catch yourself thinking "I know the protocol, I don't need to re-read it" — re-read it. The fast-collapse case (FM #17 slow-drip's sibling) is real. |
| 3 | Plans should flag "here be dragons" areas where implementation is non-obvious — not all phases are equally risky. Call out which phases need extra caution, what assumptions are load-bearing, and where the executor should stop and re-orient. | Field observation | When writing any multi-phase plan. A plan that presents all phases as equally tractable lies to the executor about where the cost actually lives. |
| 4 | **Verify a plan's output against its completion criteria — not against session duration or count.** Execution speed is not evidence of plan quality, and "fits in one session" is not a planning goal. A plan whose phases each fit cleanly in one session and produce work that matches the completion criteria is high-quality; a plan that tempts the executor to bundle phases or skip close-out to "finish faster" is not. The "1 and done" rule does not bend for high-quality plans. | Field observation (refined from rmsharp feedback on issue #7) | When evaluating a plan or judging plan quality. Resist the temptation to read execution speed as plan quality — they are uncorrelated when the protocol holds. |
| 5 | Code review is a distinct deliverable, not overhead. Reviews that produce actionable plans (exact code snippets, line numbers, implementation order) have higher ROI than vague "this needs improvement" feedback. A review that doesn't identify specific changes a future session can execute is incomplete. | Field observation | When the session deliverable is a code review. Output an actionable plan, not a critique. |
| 6 | A plan written from memory of a file read is an assumption-level claim. Reading implementations before estimating complexity catches wrong assumptions early — estimating from a backlog description alone is unreliable. This is a special case of FM #11 (gaps from memory) and FM #20 (edit from memory) applied to planning. | Field observation | Before estimating effort or scope for any phase, read the actual implementation file. The backlog description is a hint, not a spec. |
```

> mpc is **not** sync-managed (no `bin/sync`), so byte-alignment with canonical isn't a tooling requirement — these 6 rows are inserted for consistency with canonical's end-state and the new C2 caption. Reconfirm against canonical if unsure: `git -C ~/Development/methodology show origin/fix/3c-learnings-destination:starter-kit/SESSION_RUNNER.md`.

## Step 3 — Add the `CLAUDE.md` receptacle (Asset A + plain-link pointer)

`CLAUDE.md` (61 lines) has no Adaptations section. Append at the end (after `## Key Files`). Corpus is large (46 rows) → Learnings subsection is the **plain-link pointer**, NOT inline, NOT `@`-import:

```markdown
---

## Project-Specific Methodology Adaptations

*Additions and overrides to the base methodology at `SESSION_RUNNER.md` and `SAFEGUARDS.md` (synced from canonical, not project-owned). The base files govern unless explicitly overridden here. **Do not edit the synced files** — put customizations here.*

### Additional Phase 0 steps

(none)

### Additional task-to-workstream mappings

(none)

### Project-specific Learnings

Project institutional memory (46 learnings, Sessions 92–110) lives in [`PROJECT_LEARNINGS.md`](PROJECT_LEARNINGS.md) — extracted from the `SESSION_RUNNER.md` table to keep `CLAUDE.md` within its size budget (Claude Code targets ~200 lines / ~25 KB). **Read it when a task resembles earlier work; append new learnings there, not here.** Base methodology-level learnings remain in `SESSION_RUNNER.md`.

### Project-specific Failure Modes

(none — the base failure modes in `SESSION_RUNNER.md` apply.)
```

> Verify plain link: `grep -n '@PROJECT_LEARNINGS' CLAUDE.md` must return nothing.

## Step 4 — Apply C3 to `HOW_TO_USE.md:763`

Replace `Update workstream prompt and SESSION_RUNNER learnings table` so the bullet reads:

> **3C: Document learnings** — Update the workstream document; record project learnings in CLAUDE.md → Adaptations → Project-specific Learnings (adopters), or append to the SESSION_RUNNER learnings table (canonical repo dogfooding)

---

## Verification (all must pass)

- `git diff SESSION_RUNNER.md` shows **only**: 3C body → C1, caption → C2, 46 project rows → canonical's 6 seed rows. No other change.
- Rows removed from the table **== 46 == rows now in `PROJECT_LEARNINGS.md`** (no drops).
- `grep -n '@PROJECT_LEARNINGS' CLAUDE.md` → empty.
- `CLAUDE.md` has `## Project-Specific Methodology Adaptations → ### Project-specific Learnings` with the pointer.
- `HOW_TO_USE.md:763` carries the C3 wording.

## Close out

Commit as one logical change. Write handoff notes, score the previous session, STOP — "1 and done."

---

### Provenance
- Master plan §3 (model_project_constructor); verbatim wording from methodology PR #25 (`origin/fix/3c-learnings-destination`), OPEN as of 2026-06-07.
- Asset D (BOOTSTRAP/CLAUDE_TEMPLATE) intentionally skipped — those files are not vendored in mpc. No `bin/sync` → no baseline-alignment step.
