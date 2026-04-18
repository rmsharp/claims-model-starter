# Project Conventions

**Project-local supplement to the iterative methodology.** This file documents conventions that are specific to `model_project_constructor` and are not part of the upstream methodology framework. Upstream framework files in `docs/methodology/` (README.md, HOW_TO_USE.md, ITERATIVE_METHODOLOGY.md, `workstreams/*.md`) are imported material and must not be edited from within this project.

---

## 1. Inward vs outward documentation

The wiki is the outward-facing documentation; all other documentation in the repo root and `docs/` is internal to the iterative methodology.

**Outward-facing:** `docs/wiki/claims-model-starter/*.md`. Audience is users and implementers of the generated project. Written in present tense, production-shape language. Freshness-tracked — pages should describe current behavior of the shipped pipeline.

**Inward-facing:** everything else — repo-root `.md` files (`README.md`, `CLAUDE.md`, `CHANGELOG.md`, `BACKLOG.md`, `ROADMAP.md`, `SESSION_NOTES.md`, `SAFEGUARDS.md`, `SESSION_RUNNER.md`, `OPERATIONS.md`, `TROUBLESHOOTING.md`), the `docs/methodology/` framework, `docs/planning/` (and its archive), and any other `docs/` subdirectory except `docs/wiki/`. Audience is the maintainer and the iterative methodology's AI agents. Mixed freshness — some files are append-only historical logs (`SESSION_NOTES.md`, `CHANGELOG.md`), some are freshness-tracked state (`BACKLOG.md`, `ROADMAP.md`), some are point-in-time archives (see §3).

---

## 2. Three-surface split for "what changed"

Three files answer three different questions. Each file carries a per-file opener pointing to the other two.

| File | Audience | Cadence | Purpose |
|---|---|---|---|
| `CHANGELOG.md` (repo root) | Maintainer | Per session | Commit-linked ledger. Every completed session adds an entry here. Authoritative; when any summary disagrees, this file wins. |
| `docs/wiki/claims-model-starter/Changelog.md` | Users and implementers | Release-shaped (episodic) | Audience-facing release summary. Grouped by implementation phase, not by session. Tone may evolve; detail level is curated. |
| `docs/wiki/claims-model-starter/Evolution.md` | Onboarding readers, code-sharing context | User-requested only | Decision-arc narrative — "how the application grew from original concept to current state." Full rewrite each time; see §4. |

**Why three surfaces.** `CHANGELOG.md` answers *"what was committed?"*; `wiki/Changelog.md` answers *"what's new for me?"*; `wiki/Evolution.md` answers *"why is it like this?"*. A reader joining the project has no digestible narrative in the first two — the session log is too raw, the user changelog is too summary. Evolution fills that gap without polluting the other two.

---

## 3. Planning-doc archive convention

**Active plans live at `docs/planning/`.** When a plan's primary scope is delivered, move it to `docs/architecture-history/`.

**Tiebreaker rule.** A plan is archive-eligible when its primary scope is delivered, regardless of optional or deferred follow-ups. A plan returns to archive when the final optional scope ships *or* is formally descoped. This prevents a plan from sitting in `docs/planning/` indefinitely because one optional item is still pending.

**Banner on every archived document.** Prepend at the top of each moved file:

```markdown
> *This document is a concept-era artifact preserved for design archaeology. It describes the system as designed on YYYY-MM-DD and may not reflect current implementation. For current state, see `docs/wiki/claims-model-starter/Evolution.md` (design-decision arc) and the code itself (authoritative). See `PROJECT_CONVENTIONS.md` for archive scope.*
```

Replace `YYYY-MM-DD` with the date the document is moved (not the date it was written).

**Scope of archive.** `docs/architecture-history/` holds planning documents, the repo's concept-era `initial_purpose.txt`, and equivalent point-in-time artifacts. It is **not** a graveyard — archived documents remain publicly linkable as primary-source archaeology. The banner is the signal; the location is secondary.

**What does *not* move.** Freshness-tracked state (wiki pages, `BACKLOG.md`, `ROADMAP.md`), append-only logs (`SESSION_NOTES.md`, `CHANGELOG.md`), and active plans (whose primary scope is still being delivered).

**SESSION_RUNNER.md references to `docs/planning/` are unchanged by this convention.** The runner points to `docs/planning/` as the canonical location for *active* plans; the archive move is a retrospective action for plans whose work is done.

---

## 4. Evolution.md update discipline

The Evolution page is rewritten in full on request, not maintained incrementally. This section is the discipline for every rewrite.

### 4.1 Trigger

User-requested only. No scheduled cadence. Typical triggers: sharing the codebase with another developer, preparing a current-state assessment, or reaching a milestone worth narrating.

### 4.2 Full rewrite, not incremental edit

Every rewrite produces the page from scratch. Incremental edits are explicitly not the model — the narrative arc changes as the project evolves, and stitching new sections into an old arc produces a disjointed document.

### 4.3 Source material for each rewrite

- **`CHANGELOG.md`** — the completeness checklist. Every session entry since the prior rewrite (or since project inception on rewrite #1) must be accounted for: either incorporated into the arc, or listed in the deliberately-omitted appendix (see §4.5).
- **`SESSION_NOTES.md`** — the rationale source. Where CHANGELOG says *what*, SESSION_NOTES explains *why*. Use it to recover the design-discussion context behind each decision.
- **The code itself** — authoritative on current shape. When SESSION_NOTES and the code disagree, the code wins.

### 4.4 Banner on every rewrite

Prepend at the top of `Evolution.md`:

```markdown
> *Last updated: YYYY-MM-DD (commit `<short-sha>`, after Session N). This page is a full-rewrite synthesis — not continuously updated. For commits since this date, see `CHANGELOG.md` (maintainer) or `git log`.*
```

Use the 7-character short-sha form. Update all three placeholders (`YYYY-MM-DD`, `<short-sha>`, `Session N`) on every rewrite.

### 4.5 Deliberately-omitted appendix

End every rewrite with a short appendix listing sessions intentionally excluded from the arc. Format: session number, one-line summary, reason for omission. This prevents a reader from wondering *"was Session X forgotten, or left out on purpose?"* — the appendix answers.

### 4.6 Diff-against-prior discipline (rewrite #2 onward)

Before committing rewrite #2 or later, read the prior rewrite end-to-end and note what changed in the arc (not just what's new). The page evolves deliberately; unexplained disappearances of earlier framing are a regression signal.

### 4.7 Review gate

Evolution rewrites use an **explicit review gate**, unlike all other sessions in this project:

- The rewrite session writes the draft, verifies it against §4.3 sources, and **stops before committing**.
- The operator reviews the draft interactively.
- The session commits only after explicit approval.

**Why the gate is here and nowhere else.** Evolution is outward-facing and persistent between rewrites. Errors are audience-visible and can hide for months before the next rewrite catches them. The review cost (one round-trip) is small relative to the audience-visibility risk. Every other session in this project continues the autonomous-commit pattern.
