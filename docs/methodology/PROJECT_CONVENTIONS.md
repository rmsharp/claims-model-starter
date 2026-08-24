# Project Conventions

**Project-local supplement to the iterative methodology.** This file documents conventions that are specific to `model_project_constructor` and are not part of the upstream methodology framework. Upstream framework files in `docs/methodology/` (README.md, HOW_TO_USE.md, ITERATIVE_METHODOLOGY.md, `workstreams/*.md`) are imported material and must not be edited from within this project.

---

## 1. Inward vs outward documentation

The wiki is the outward-facing documentation; all other documentation in the repo root and `docs/` is internal to the iterative methodology.

**Outward-facing:** `docs/wiki/model_project_constructor/*.md`. Audience is users and implementers of the generated project. Written in present tense, production-shape language. Freshness-tracked — pages should describe current behavior of the shipped pipeline.

**Inward-facing:** everything else — repo-root `.md` files (`README.md`, `CLAUDE.md`, `CHANGELOG.md`, `BACKLOG.md`, `ROADMAP.md`, `SESSION_NOTES.md`, `SAFEGUARDS.md`, `SESSION_RUNNER.md`, `OPERATIONS.md`, `TROUBLESHOOTING.md`), the `docs/methodology/` framework, `docs/planning/` (and its archive), and any other `docs/` subdirectory except `docs/wiki/`. Audience is the maintainer and the iterative methodology's AI agents. Mixed freshness — some files are append-only historical logs (`SESSION_NOTES.md`, `CHANGELOG.md`), some are freshness-tracked state (`BACKLOG.md`, `ROADMAP.md`), some are point-in-time archives (see §3).

---

## 2. Three-surface split for "what changed"

Three files answer three different questions. Each file carries a per-file opener pointing to the other two.

| File | Audience | Cadence | Purpose |
|---|---|---|---|
| `CHANGELOG.md` (repo root) | Maintainer | Per behavior change | Commit-linked ledger. A session adds an entry when it changes shipped code or test logic (see "CHANGELOG cadence" below). Authoritative; when any summary disagrees, this file wins. |
| `docs/wiki/model_project_constructor/Changelog.md` | Users and implementers | Release-shaped (episodic) | Audience-facing release summary. Grouped by implementation phase, not by session. Tone may evolve; detail level is curated. |
| `docs/wiki/model_project_constructor/Evolution.md` | Onboarding readers, code-sharing context | User-requested only | Decision-arc narrative — "how the application grew from original concept to current state." Full rewrite each time; see §4. |

**Why three surfaces.** `CHANGELOG.md` answers *"what was committed?"*; `wiki/Changelog.md` answers *"what's new for me?"*; `wiki/Evolution.md` answers *"why is it like this?"*. A reader joining the project has no digestible narrative in the first two — the session log is too raw, the user changelog is too summary. Evolution fills that gap without polluting the other two.

**CHANGELOG cadence.** A session earns a `CHANGELOG.md` entry when it changes shipped code — `src/`, `packages/`, `scripts/` — or adds/changes `tests/` test logic. Documentation-only sessions (the wiki, the rest of `docs/`, the methodology framework, and project-state files such as `SESSION_NOTES.md`, `BACKLOG.md`, `ROADMAP.md`), and sessions whose only code-tree touch is non-behavioral (fixture data, docstring or path strings), are recorded in `SESSION_NOTES.md` and — where user-relevant — surfaced through the wiki `Changelog`/`Evolution`; they do not get a `CHANGELOG.md` entry. A multi-session feature or overhaul may be recorded as a single entry spanning its sessions, dated by its completion/landing commit. *(This refined the earlier "every completed session adds an entry" rule in Session 149: Sessions 114–148 had drifted under the per-session rule — the shipped-code work in that span was backfilled to `CHANGELOG.md` and the documentation-only sessions were left in `SESSION_NOTES.md` per this gate.)*

**Measurement-only sessions: SETTLED, do not re-ask (operator ruling, 2026-08-17, Session 223).** A session that only *runs* the live eval harness — measuring providers, probing variance, reproducing a defect — and changes no `src/`, `packages/`, `scripts/`, or `tests/` logic **does not get a `CHANGELOG.md` entry**. The written gate above is correct as it stands; **Session 216's entry was the deviation, not the precedent.** Do not backfill S216, and do not amend it — `CHANGELOG.md` is an append-only historical ledger (§1), so an entry that should not have been written stays written. Sessions 219, 220, 221 and 222 each flagged this as an unresolved convention-vs-precedent conflict and each correctly followed the written rule; the ruling exists so a fifth session does not spend the same paragraph re-litigating it. The measurement itself is recorded in `SESSION_NOTES.md` and, where it changes what a user should believe about the pipeline, in the wiki `Changelog`/`Evolution`.

---

## 3. Planning-doc archive convention

**Active plans live at `docs/planning/`.** When a plan's primary scope is delivered, move it to `docs/architecture-history/`.

**Tiebreaker rule.** A plan is archive-eligible when its primary scope is delivered, regardless of optional or deferred follow-ups. A plan returns to archive when the final optional scope ships *or* is formally descoped. This prevents a plan from sitting in `docs/planning/` indefinitely because one optional item is still pending.

**Banner on every archived document.** Prepend at the top of each moved file:

```markdown
> *This document is a concept-era artifact preserved for design archaeology. It describes the system as designed on YYYY-MM-DD and may not reflect current implementation. For current state, see `docs/wiki/model_project_constructor/Evolution.md` (design-decision arc) and the code itself (authoritative). See `PROJECT_CONVENTIONS.md` for archive scope.*
```

Replace `YYYY-MM-DD` with the date the document is moved (not the date it was written).

**The banner tracks its template; it is NOT part of the frozen record (operator ruling, Session 240).** The banner is project-added boilerplate, so when its target moves, **every deployed copy is re-pointed in the same commit that moves the target.** Session 147's precedent already requires each deployed copy to be byte-identical to the template above, and that invariant is only maintainable if the copies track it. The repository rename (Session 233) is the worked example of the failure: Phase 4 updated this template and **none** of its copies, leaving 21 dead in-repo banner pointers across 20 files, plus 2 more lines in `CHANGELOG.md`'s preamble — 23 in all, re-pointed in Session 240. Nothing caught it because `repository-rename.md` §7.2 exempted `docs/architecture-history/` and `CHANGELOG.md` **wholesale**, on §3.1's rationale that they are frozen historical records. That rationale is true of their *entries* and false of a banner and a preamble, which record nothing and **navigate** — an exemption is only as fine-grained as the assertion traded for it (learning #135). **One documented exception to byte-identity:** `bedrock-testing-enablement.md` appends a document-specific sentence inside its banner, naming where its still-useful reference tables were carved forward. Text after `for archive scope.` is the document's own; only the template portion tracks.

**Scope of archive.** `docs/architecture-history/` holds planning documents, the repo's concept-era `initial_purpose.txt`, and equivalent point-in-time artifacts. It is **not** a graveyard — archived documents remain publicly linkable as primary-source archaeology. The banner is the signal; the location is secondary.

**What does *not* move.** Freshness-tracked state (wiki pages, `BACKLOG.md`, `ROADMAP.md`), append-only logs (`SESSION_NOTES.md`, `CHANGELOG.md`), and active plans (whose primary scope is still being delivered).

**Ledger shards are the one exception (Session 222).** The *live* append-only log never moves — but a **frozen shard of its retired records** does, as `<STEM>-through-<CUTKEY>.md` beside a `<same>.verify.sh` proving the move was byte-for-byte lossless. This is a size remedy, not an archaeology judgement: a ledger past the 2,000-line agent read cap is silently truncated on every `Read`, with no error and no missing-data marker. A shard therefore does **NOT** carry the concept-era banner above — that banner says "describes the system as designed on YYYY-MM-DD", which is false of a session log — it carries its own banner naming its record count, its session span, and the fact that nothing below it was altered. **Seven instances so far**, and the naming rule above bent at the second: `SESSION_NOTES-through-S216.md` (Session 222, Sessions 216→1), `SESSION_NOTES-S220-through-S217.md` (Session 224, Sessions 220→217), `SESSION_NOTES-S224-through-S221.md` (Session 228, Sessions 224→221), `SESSION_NOTES-S227-through-S225.md` (Session 231, Sessions 227→225) `SESSION_NOTES-S231-through-S228.md` (Session 235, Sessions 231→228), `SESSION_NOTES-S235-through-S232.md` (Session 239, Sessions 235→232) and `SESSION_NOTES-S238-through-S236.md` (Session 242, Sessions 238→236). The `<STEM>-through-<CUTKEY>.md` form is only unambiguous for the FIRST shard, whose span is open at the bottom — a second shard named `-through-S220` would read as "everything through Session 220", which is false, since 216→1 sit in the earlier file. **A non-first shard therefore takes the range form `<STEM>-<NEWEST>-through-<OLDEST>.md`.** This is a deliberate departure, recorded here so a later trim copies the rule rather than the first filename — **the third, fourth, fifth, sixth and seventh trims all did**, which is the evidence the note works rather than merely reads well. A corollary of write-once: shard names are load-bearing routing information, and the set of them is only correct when read together — no single shard is authoritative about where Session N lives. The canonical `methodology_trim.py` deliberately refuses `SESSION_NOTES.md` (no generic grammar fallback), so the shard is hand-built and its proof ships a `--self-test` that proves the proof itself can fail.

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
