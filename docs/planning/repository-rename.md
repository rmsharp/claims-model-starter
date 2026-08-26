# Plan: rename the GitHub repository `claims-model-starter` → `model_project_constructor`

**Status:** **EXECUTED — all 5 phases are done. This plan is closed.**
Phase 1 — Session 227, `c1fe06f`. Phase 2 — Session 229, `73b9418`. Phase 3 — Session 232,
`f58948a`. Phase 4 — Session 233, `1865fc2`. Phase 5 — Session 234, **the commit carrying this
line** — find it with
`git log --oneline -S'EXECUTED — all 5 phases are done' -- docs/planning/repository-rename.md`,
which returns **exactly one** commit: the one that flipped this line. *A hash cannot be written into
the commit that creates it, and a placeholder nothing checks is a promise nothing keeps — so this
cites what `git` can find instead. **Do not "simplify" it to `--grep 'rename Phase 5'`:** that
matches commit **subjects**, and every session close-out in this rename carries the phrase
*"rename Phase N"* while three of the four phase commits did not carry their own — so it resolves
to the close-out, confidently and wrongly. Found by the pre-commit review, against a first fix that
had already replaced a placeholder for being unverifiable.*
**Every check in §7 passes**, including §7.4's three out-of-repo surfaces, which no `git grep` at
`HEAD` can reach — with one stated qualification: §7.3's residue line greps *directories*, so its
verdict is "no **tracked** residue" and depends on the `grep` implementation. See the warning under
§7.3 and §9.2. **`BACKLOG.md`'s rename item is deleted, not edited** — that was the closing
criterion. Two things survive the rename **on purpose and forever**: §3.1's 552 frozen-record lines,
and §3.3's D-R5-pinned lines naming `~/Development/claims-model-starter.wiki`, a directory on disk
that GitHub's rename never moved. A future sweep that "completes" either one is a regression, not a
finish.
**This plan was itself repaired in Session 230 — see §9.1**, and reconciled by Phase 5 — see §9.2.
Session 230: Phase 4's `publish_wiki.sh` line list
contradicted D-R5 and would have broken wiki publishing if obeyed literally; three downstream
completion criteria were unsatisfiable as a consequence; and dragon 1 pointed the reader into a
phase that had already closed.
**Written:** Session 226, 2026-08-19 — that session's entire deliverable was this file, with the
rename itself deferred to later sessions. It was, and they have begun.

> **Operator ruling, 2026-08-19 (recorded in `2033e95`):** *"set rename of repository as the next
> session ; it may take a planning session because of the blast radius of a rename."*
> **Operator, this session:** *"rename repository ; use planning session if needed."*
>
> The "if needed" is answered by evidence, not preference: the sweep is 97 lines across 23 files,
> three automated mechanisms key on the literal old name, and **one consequence of the rename is
> permanent and irreversible** (§1). `SESSION_RUNNER.md` FM #18 and `SAFEGUARDS.md` ("never
> rename/move files as part of a quick fix"; "renames cascade — they are never quick") both put the
> plan and the execution in different sessions.

**How to read this.** §1 is the finding that should change the operator's mind about *whether* to
rename at all, or at least about what is being traded away. §2 is the inventory. §3 classifies every
file. §4 is the gate: five questions only the operator can answer. §5 is the phase sequence. §6 is
the dragons. §7 is how you know it is finished.

---

## §1 The one irreversible consequence: the published Pages URL dies permanently

**This is the headline finding of the planning session and it was not in the filed backlog item.**

GitHub redirects almost everything after a repository rename — the repo web URL, `git clone` /
`fetch` / `push` against the old remote, issues, **the wiki**, stars, and followers. It does **not**
redirect GitHub Pages **project site** URLs.

*(One caveat on that list, stated because the plan leans on it: repo-URL redirection and Pages
non-redirection are both **measured** below. Git **push** continuity over the stale remote is
**documented but not measured** — the `git-receive-pack` advertisement returns 401 without
credentials, so it cannot be probed read-only. Fetch, however, is measured: GitHub serves the
`git-upload-pack` advertisement at the old path with **200 and no redirect at all**. Treat push
continuity as very likely, not proven, and confirm it during Phase 1.)* That is stated as the explicit exception in GitHub's
own documentation:

> "When you rename a repository, all existing information, with the exception of project site URLs,
> is automatically redirected to the new name."
> — *Renaming a repository*, GitHub Docs
> <https://docs.github.com/en/repositories/creating-and-managing-repositories/renaming-a-repository>
>
> "If you plan to rename a repository that has a GitHub Pages site, we strongly recommend using a
> custom domain for your site. This ensures that the site's URL isn't impacted by renaming the
> repository."
> — same page
>
> "…renaming a Pages repository will continue to break any existing links to content hosted on the
> github.io domain…"
> — *Troubleshooting 404 errors for GitHub Pages sites*, GitHub Docs
> <https://docs.github.com/en/pages/getting-started-with-github-pages/troubleshooting-404-errors-for-github-pages-sites>

**And it is not only documented — it is measured.** Two real same-owner renames, one with a Pages
config identical to this repository's (`build_type: legacy`, source `gh-pages`, `cname: null`):

```
apache/incubator-superset  ->  apache/superset          (gh api …/incubator-superset --jq .full_name)
  https://github.com/apache/incubator-superset          -> 301  Location: …/apache/superset   REDIRECTS
  https://apache.github.io/incubator-superset/          -> 404  no Location header            DOES NOT
  https://apache.github.io/superset/                    -> 200
facebook/jest -> jestjs/jest
  https://facebook.github.io/jest/                      -> 404  no Location header            DOES NOT
```

**The same rename that 301s the repository URL 404s the Pages URL, on the same host, at the same
instant.** That contrast is the whole finding.

**Verified live state of this repository's site** (`gh api repos/rmsharp/claims-model-starter/pages`):

```
"status": "built", "build_type": "legacy", "source": {"branch": "gh-pages", "path": "/"},
"html_url": "https://rmsharp.github.io/claims-model-starter/", "public": true, "cname": null
```

`cname` is `null` — there is **no custom domain**, which is precisely the mitigation GitHub
recommends and this project does not have.

**Therefore, the moment the rename lands:**

`https://rmsharp.github.io/claims-model-starter/tutorial/` — the URL advertised in `README.md:9`,
the project's only public tutorial link — **becomes a permanent 404.** The site reappears at
`https://rmsharp.github.io/model_project_constructor/` only after the next `mkdocs gh-deploy`.

This collides head-on with **decision D6** of `docs/planning/enterprise-migration.md:549`, answered
by the operator on 2026-07-27: *"refresh and keep public, indefinitely."* A URL that is public
indefinitely and then 404s forever is not a transient inconvenience; it is the deliberate
destruction of the project's one published address. **The backlog item's dragon #5 says GitHub's
redirect "softens but does not remove the break." That is too gentle for the Pages URL: there is no
redirect at all.**

### §1.1 The three ways out, and what each costs

| # | Option | Cost | Recommendation |
|---|--------|------|----------------|
| A | **Accept the 404.** Rename; update `README.md:9` and `mkdocs.yml:3`; the old URL dies. | Every external link, bookmark, or citation of the tutorial URL breaks permanently. Search engines re-index over weeks. | **Recommended** *if* the operator judges the tutorial URL to have no meaningful external audience yet. The project is pre-UAT (`docs/wiki/claims-model-starter/Contributing.md:238`: "no public issue tracker actively in use for pre-UAT development"), which argues the external audience is close to zero. |
| B | **Custom domain.** Point a domain the operator owns at the Pages site *before* renaming. | Requires owning/configuring a domain and DNS; the site URL then never depends on the repo name again. | The durable fix, and GitHub's own advice. Worth it only if the operator wants a stable public address long-term. |
| C | **Squat the old name** with a new repo serving redirects. | **Do not do this.** GitHub Docs, same page: *"If you create a new repository under your account in the future, do not reuse the original name of the renamed repository. If you do, redirects to the renamed repository will no longer work."* You would buy back the Pages URL by destroying **every other** redirect — repo, git remote, and wiki. Strictly worse. | **Rejected.** Recorded here so a later session does not rediscover it as a clever idea. |

**This is operator decision D-R1 in §4.** It is the only decision in this plan that cannot be
reversed after the fact.

---

## §2 Evidence-based inventory (derived 2026-08-19, this session)

### §2.1 Method — stated, because the previous two counts disagreed with each other

Counting unit is **matching lines** over **tracked files at `HEAD`**:

```bash
git grep -c "claims-model-starter" -- . | awk -F: '{s+=$NF} END {print s}'   # lines
git grep -l "claims-model-starter" -- . | wc -l                              # files
```

**At `HEAD` = `59615e2`: 666 matching lines across 51 files** (795 raw occurrences —
`git grep -o … | wc -l` — because some lines carry the string twice). The working-tree count was
identical, and **no untracked file contained the string**.

**`59615e2` is the pin, and it is deliberately the commit BEFORE this file existed.** Committing this
plan adds ~91 more matching lines and a 52nd file — *this* file. Every number in §2 and §3 is stated
against `59615e2` so that the plan's own prose does not contaminate the inventory it reports. To
reproduce any of them: `git grep -c "claims-model-starter" 59615e2 -- .`

### §2.2 Both previously filed counts were wrong, in different ways

| Source | Claimed | Actual at that commit | Verdict |
|--------|---------|----------------------|---------|
| `BACKLOG.md` per-pattern table (Session 221, `5d906e9`) | 644 / 50 | **659 / 50** | Session 222 already caught this and said so. |
| Operator-ruling commit `2033e95` (Session 225) | 667 / 52 | **665 / 51** | **Not reproducible at any commit or by any counting method.** Nearest real values: 661/50 at `2070547`, 665/51 at `2033e95` itself. |

I could not reproduce 667/52 by matching-lines, by raw occurrences, by working-tree grep, by
including untracked files, or at any of the fourteen commits from `5d906e9` to `HEAD`. **Treat the
recount in `2033e95` as unfounded and this section as replacing it.** The lesson is the same one
that recount was trying to teach — re-derive, don't inherit — applied one level further up.

Full trajectory (matching lines / files), so a future session can see the drift rate:

```
5d906e9 2026-08-17  659/50     6aec809 2026-08-19  661/50
8bc3ef3 2026-08-17  659/50     90a50d5 2026-08-19  661/50
f91f8e0 2026-08-17  659/50     2f853f7 2026-08-19  661/50
7ee10a0 2026-08-17  661/50     fcb4366 2026-08-19  661/50
6823b3f 2026-08-18  661/50     27c2007 2026-08-19  661/50
07e1ab9 2026-08-19  661/50     2070547 2026-08-19  661/50
                               2033e95 2026-08-19  665/51   <- the ruling commit itself added 4
                               59615e2 2026-08-19  666/51   <- this session's Phase 1B stub added 1
```

**The count grows every time anyone writes about the rename.** It is a self-inflating metric and a
poor completion criterion. §7 uses a file allowlist instead.

### §2.3 Per-pattern (each pattern has a different fix)

| # | Pattern | Lines | Files | What it is |
|---|---------|-------|-------|-----------|
| 1 | `docs/wiki/claims-model-starter` | 516 | 42 | the wiki **source directory** path |
| 2 | `claims-model-starter.wiki` (**literal**, `grep -F`) | 95 | 7 | the wiki **clone** name / URL |
| 3 | `github.com/rmsharp/claims-model-starter` | 36 | 12 | repo and wiki-page URLs |
| 4 | `rmsharp.github.io/claims-model-starter` | 25 | 7 | the **Pages** site URL (§1) |
| 5 | `Claims Model Starter` (title case) | 5 | 3 | reader-visible branding |
| 6 | `claims_model_starter` (underscored) | 1 | 1 | **one row in `BACKLOG.md`'s own per-pattern table** — the row that says this form does not exist. Self-matching. Do not read it as a real occurrence. (Cited as `:527` at plan time; the line has moved twice since. `grep -n "claims_model_starter" BACKLOG.md`.) **Session 234: that grep now returns nothing — the row it matched was inside the rename item Phase 5 deleted, so this measurement is now 0/0 in the working tree while staying 1/1 at `59615e2`, which is the frame §2 is pinned to.** |
| 7 | `claims model starter` (spaced), `Claims-Model-Starter` | 0 | 0 | do not exist |

**The table is complete, not merely enumerated.** Searched and confirmed **zero** for every other
form the name could take: case-insensitive `claims.model.starter` outside the three known spellings;
URL-encoded `claims%2Dmodel` / `claims%20model`; camel-case `ClaimsModelStarter`; any abbreviation
like `cms-starter`; the name split across a line break (`claims-model-$`); and — the widest net —
any line matching `claims.*starter` case-insensitively that is not one of the three known forms.
All returned nothing. **The three spellings in rows 1-6 are the whole surface.**

Patterns overlap; the column does not sum to 666.

**⚠ Pattern 2 must be matched literally.** As a *regex*, `claims-model-starter.wiki` reports
**104 lines / 11 files** — the unescaped `.` also matches `claims-model-starter**/**wiki`, i.e. the
`github.com/rmsharp/claims-model-starter/wiki/<Page>` **page URLs**. Those 9 extra lines belong to
pattern 3 and take pattern 3's fix (a URL that redirects), not pattern 2's (a git remote guarded by
a fail-closed check). Use `git grep -F` or escape the dot. The filed backlog table's "89" was the
same measurement made the same loose way; this plan's 95/7 is the literal count, verified both ways.

### §2.4 Surfaces that contain **zero** hits — verified, so nobody re-searches them

- `src/**` and `packages/**`: **0**. No shipped code names the repository.
- `.github/workflows/**`: **0** in both `ci.yml` and `publish-tutorial.yml`.
- `pyproject.toml`, `packages/data-agent/pyproject.toml`: **0** — no `[project.urls]` block at all.
- `docs/architecture-history/SESSION_NOTES-S220-through-S217.md` (the second shard): **0**.
- Git tags: `v0.1.0`, `v0.2.0` — neither names the repo.
- Non-text tracked files: none (`git grep -I -l` and `git grep -l` return identical lists).
- `docs/index.md`: **0**.
- **Both tracked binaries** — `docs/architecture-history/architecture-approaches.pdf` and
  `docs/explainers/interview-convergence-explainer.pdf` — `pdftotext | grep -i` → **0** each.
- `.gitleaksignore`: **0** references to `docs/wiki/` paths, so the directory move cannot silently
  un-suppress a secret-scanning finding. `CODEOWNERS` is `* @rmsharp` with no paths. `.git/hooks/`
  holds only `.sample` files (the live hook is `core.hooksPath = .githooks`).
- Ignored-but-present operational state — `.env`, `intake_sessions.db`,
  `.orchestrator/checkpoints/` (22 run dirs), and all three `.claude/settings.local.json` files:
  **0**. A permission-allowlist entry naming a wiki path would have broken silently; there is none.
- Shell startup files, `~/.config/gh/`, LaunchAgents, `crontab -l`, and
  `git config --global url.*.insteadOf`: **0**. No scheduled job or alias depends on either name.
- **Both annotated tags already carry the NEW name** — `v0.1.0`: *"First release tag on the
  model_project_constructor project"*; `v0.2.0`: *"Second release tag on model_project_constructor."*
  Nothing needs re-tagging, and this is a second independent sign the rename is the consistent
  direction (the first is `publish_wiki.sh:101`).
- **No tracked symlinks** (`git ls-files -s | awk '$1=="120000"'` → none), so nothing dangles when the
  directory moves.

### §2.4b Two affected files carry **zero** hyphenated hits and are therefore outside the 51

`docs/wiki/claims-model-starter/Home.md:1` (`# Claims Model Starter Wiki`) and
`_Sidebar.md:1` (`**Claims Model Starter**`) match only the **title-case** pattern. Every count in
§2 and §3 excludes them. If D-R3 is "yes", they are two additional edits that no
`claims-model-starter` grep will ever surface. **A completion criterion built on the hyphenated
pattern cannot see this decision at all.**

### §2.5 One surface outside the sweep's reach: `origin/gh-pages` — and one blob inside it that **no grep can read**

`git grep -c "claims-model-starter" origin/gh-pages` reports 25 lines across 4 files. **That census
is incomplete, and the missing file is the dangerous one.** Decompressing every blob gives the true
picture (occurrences, not lines):

| blob | occurrences | reachable by `git grep`? |
|---|---|---|
| `404.html` | 13 | yes |
| `tutorial/index.html` | 6 | yes |
| `index.html` | 5 | yes |
| `sitemap.xml` | 2 | yes |
| **`sitemap.xml.gz`** | **2** | **NO — gzipped** |
| `search/search_index.json` | 0 | yes |
| `.nojekyll` | 0 | — |
| **total** | **28 across 5 files** | |

**`sitemap.xml.gz` is served live and advertises the dead path**, verified:

```bash
curl -s https://rmsharp.github.io/claims-model-starter/sitemap.xml.gz | gzip -dc
#   <loc>https://rmsharp.github.io/claims-model-starter/</loc>
#   <loc>https://rmsharp.github.io/claims-model-starter/tutorial/</loc>
```

**Why this matters more than the count.** The obvious criterion —
`curl …/sitemap.xml | grep -c claims-model-starter` → 0 — **passes while the `.gz` still says the old
name, and crawlers prefer the `.gz`.** That is a fail-open in the completion criteria themselves;
§7.4 now checks both. `search_index.json` is clean today because its `location` values are
**relative** (`""`, `"tutorial/"`, …) *and* neither published page's body contains the string — both
conditions must hold, and on the `gh-pages-preA4` rollback branch the same file carries **10**
occurrences.

None of this needs an edit: it is generated output, rewritten wholesale by
`mkdocs gh-deploy --force --clean`, which **Phase 1 triggers**. It needs *checking*, not fixing.

---

## §3 Classification: what changes, what keeps the old name

The governing precedent is **`bfd9f36`** (the SR 11-7 → SR 26-2 rename, Session 144), whose commit
message rules it explicitly:

> "Historical records (root CHANGELOG, SESSION_NOTES, architecture-history, audits, wiki Changelog
> Phase 4B entry, banner-anchored Evolution) deliberately retain the old name."

Run `git show --stat bfd9f36` before executing (learning #60) — it is 26 files and the shape of its
live/historical split is the shape this rename must reproduce.

### §3.1 KEEP the old name because it is a frozen record — 552 lines across 28 files

**There are now THREE buckets, not two.** §3.1 is the historical records. §3.2 is what changes.
**§3.3 is new** — live files that keep the old name *forever* for a reason that has nothing to do
with history: they name a **local filesystem path that GitHub's rename does not touch** (D-R5).
A sweep that "completes" §3.1 falsifies the record; a sweep that "completes" §3.3 **breaks wiki
publishing.**

| Group | Files | Lines | Why |
|-------|-------|-------|-----|
| `docs/architecture-history/**` | 21 | 418 | Frozen historical records. Includes `SESSION_NOTES-through-S216.md` (293 lines of the 418). **`grep` that file, never `Read` it** — it is 24,590 lines / 3.9 MB, and a default agent `Read` of it is **refused outright** (`File content (3.9MB) exceeds maximum allowed size (256KB)`, zero content returned; measured Session 249). The *"truncates at 2,000 with no marker"* rationale this row carried until Session 249 was false — see `docs/planning/ledger-budgets-review.md` §1. |
| `CHANGELOG.md` | 1 | 117 | Authoritative append-only ledger; every entry records what-was-true-then. |
| `audits/**` | 2 | 12 | `2026-06-10-wiki-vs-code-accuracy-audit.md` (10), `2026-07-28-b2-import-readiness.md` (2). Dated findings. |
| `PROJECT_LEARNINGS.md` | 1 | 2 | Learning #14's source attribution and #32's worked example. Both are records of past sessions. |
| `prs-export.json`, `releases-export.json` | 2 | 2 | Frozen GitHub API exports captured at a point in time (`enterprise-migration.md:911`). Rewriting them would falsify the snapshot. |
| `docs/wiki/…/Changelog.md` | 1 | 1 | **Its only hit, `:124`, is a dated entry** — *"Added: 14 initial wiki pages for the `claims-model-starter` project … (Session 19)."* `PROJECT_LEARNINGS.md` #32 exists because of this exact file: it is freshness-tracked yet carries permanent historical records. Its **path** moves in Phase 4 if D-R2 is yes; its **content** does not. |

**552 + 17 + 97 = 666 ✓** (§3.1 + §3.3 + §3.2). **28 + 2 + 23 = 53 file-slots for 51 distinct
files** — the two extra slots are `scripts/publish_wiki.sh` and `docs/planning/enterprise-migration.md`,
each of which has lines in **both** §3.3 and §3.2. Every other file is wholly on one side.

> *Session 230 correction. This line previously read* **552 + 114 = 666 ✓. 28 + 23 = 51 ✓.** *The
> 666 lines / 51 files is unchanged and still derives from `59615e2` — nothing was re-measured. What
> moved is the classification of **17 lines**, from CHANGE to a new permanent-KEEP bucket (§3.3),
> because the plan had no bucket for "live file, pinned by an operator decision, forever". Not having
> one is what made §7.2 unsatisfiable.*

### §3.2 CHANGE (or decide) — 97 lines across 23 files

**The real size of this job is 97 lines, not 666.** Ordered by what they are, not by hit count.

**(a) Executable / config — these break something if wrong (14 lines, 4 files)**

| File | Lines | What |
|------|-------|------|
| `scripts/publish_wiki.sh` | **7 of 10** | **CHANGE 7:** `:2`, `:11` header prose (the *in-repo* source directory); `:23` the documented clone **URL**; `:44` `SOURCE_DIR`; `:63` the clone **URL** again; `:72`, `:75` **the remote-URL guard**. **KEEP 3 — `:19`, `:24`, `:42`** are the clone's **filesystem path**, pinned permanently by D-R5 (§3.3, first row). **The old `:23-24` range is split**: `:23` is a URL and changes, `:24` is the destination directory on the next line and does not. |
| `.githooks/post-commit` | 2 | `:3` prose; `:18` the `grep -q '^docs/wiki/claims-model-starter/'` trigger |
| `tests/test_wiki_no_line_citations.py` | 2 | `:7` docstring; `:38` `WIKI_DIR` constant — **`:60` asserts `WIKI_DIR.is_dir()`, so the suite fails if the directory moves without this line** |
| `mkdocs.yml` | 3 | `:3` `site_url`, `:4` `repo_url`, `:5` `repo_name` |

**(b) Reader-facing / published (12 lines, 7 files)**

| File | Lines | Note |
|------|-------|------|
| `docs/wiki/…/Contributing.md` | `:19-20`, `:124`, `:238` | clone command, hook path, issue-tracker URL — **published content** |
| `README.md` | `:7`, `:9` | `:9` is the Pages URL (§1). **`:7` cannot be string-replaced — see §6 dragon 6.** |
| `SECURITY.md` | `:9` | security-advisory URL — redirects, but should be correct |
| `CONTRIBUTING.md` | `:6` | Contributing wiki-page URL — redirects |
| `docs/tutorial.md` | `:218` | Intake-Interview-Design wiki URL — redirects. **Editing this file triggers a Pages redeploy** (§6 dragon 5) |
| `docs/wiki/…/Software-Bill-of-Materials.md` | `:3`, `:113` | **semantic, not mechanical** — see §6 dragon 7 |
| `docs/wiki/…/Development-Workflow.md` | `:3` | **semantic** — same dragon |

**(c) Internal docs — wiki **path** references (13 lines, 6 files)** —
`docs/style/statistical_terms.md` (`:7`, `:103`, `:137`, `:165`),
`docs/methodology/PROJECT_CONVENTIONS.md` (`:11`, `:24`, `:25`, `:44`),
`executive-summaries/stakeholder-readiness-dossier.qmd` (`:57`, `:95`), `THIRD-PARTY-LICENSES`
(`:50`), `docs/wiki/…/License.md` (`:3`), `docs/wiki/…/Evolution.md` (`:266`). All change **iff**
§4's D-R2 is "yes"; if it is "no", this whole group is untouched. **None of them ship to Pages** —
`mkdocs.yml:13-16` is a fail-closed allowlist admitting only `index.md` and `tutorial.md`.
*(`Evolution.md:266` also said "22 outward-facing wiki pages plus the sidebar"; there are **24**
(25 files, one of which is `_Sidebar.md`). Fix the count while you are in the line.)*

> *Session 234 correction (Phase 5) — the second half of Session 232's filed defect #2. This
> parenthetical previously read* **"also says “22 outward-facing wiki pages”; there are 25."**
> *Two errors in one sentence. The quotation stopped one clause short of the page's own convention
> — the page says "plus the sidebar" — and **25 is the total FILE count**, a different quantity from
> the outward-facing page count the sentence is correcting. An executor obeying it as written landed
> off by one instead of off by two. Session 233 measured rather than copied
> (`ls docs/wiki/model_project_constructor/ | grep -vc '^_'` -> **24**) and shipped 24 to the live
> wiki, so the page has been right since `1865fc2`; this is the plan catching up to the page.*

**(d) Active plans (34 lines, 3 files)** — `docs/planning/enterprise-migration.md` (**29 of its
43**), `opencode-adapter-spec.md` (3), `httpx-adapter-migration.md` (2). **Mid-execution, and they
are not prose — see §6 dragon 1, which is the second-most-serious finding in this document.**
**The other 14 of `enterprise-migration.md`'s 43 are §3.3 and are permanent** — they name
`~/Development/claims-model-starter.wiki`, the clone D-R5 pins in place.

**(e) Working documents whose hits are self-referential (23 lines, 2 files)** — `BACKLOG.md` (18)
and `SESSION_NOTES.md` (5). These hits exist *in order to* name the old name.
**All 5 of `SESSION_NOTES.md`'s are self-referential** (the rename handoff and this session's stub).
**17 of `BACKLOG.md`'s 18 are too** — they are the rename item, and they die by **row deletion** in
Phase 5, not by substitution. **Exactly one is a genuine substitution: `BACKLOG.md:74`**, a
`docs/wiki/claims-model-starter/` path citation inside an unrelated item, which moves with the
directory in Phase 4. **Do not run a blind `sed` over these two files.**

**Subtotals reconcile: 14 + 12 + 13 + 34 + 23 + 1 = 97 lines; 4 + 7 + 6 + 3 + 2 + 1 = 23 files.**
*(Session 230: group (a) was 17 and group (d) 48, before 3 lines of `publish_wiki.sh` and 14 of
`enterprise-migration.md` moved to §3.3. Both **files** stay change-side — they have change lines
too — so the file count is unchanged at 23.)*

**(f) The file that must not be edited (1 line, 1 file)** — `SESSION_RUNNER.md:209` names
`docs/wiki/claims-model-starter/` inside the "Wiki sync" paragraph. It is **synced from the
canonical methodology repo**; `CLAUDE.md` forbids editing it, and a local edit blocks future syncs.
The prescribed seam is `CLAUDE.md` → *Project-Specific Methodology Adaptations*. See §5 Phase 4.

### §3.3 KEEP the old name because D-R5 pins a filesystem path — 17 lines across 2 files

**Added in Session 230. The plan shipped without this bucket, and its absence is what made §7.2 —
Phase 5's DONE gate — unsatisfiable.** These lines are neither historical records nor documents
about the rename. They are **live** text naming
`~/Development/claims-model-starter.wiki`, the wiki clone the operator ruled is **re-pointed in
place** (D-R5): GitHub's rename moves a URL, it never moves a directory on your disk. **Every one of
these lines still NAMES the pinned clone directory after the rename, and must go on doing so, unless
a later operator decision reverses D-R5.** Sixteen of the seventeen are correct verbatim, forever.
**The seventeenth — trap 1 below — is half-right: it names the clone *and* the in-repo directory, so
Phase 4 must edit one half and preserve the other.**

| File | Lines | Which, and why |
|---|---|---|
| `scripts/publish_wiki.sh` | 3 | `:19` the `WIKI_CLONE` default's doc comment, `:24` the documented clone command's destination directory, `:42` the `WIKI_CLONE` default itself. **Change `:42` and the script hard-fails at its own `:58` clone-exists guard** — D-R5 says so. Its other 7 lines are §3.2. |
| `docs/planning/enterprise-migration.md` | 14 | every line naming `~/Development/claims-model-starter.wiki`: the C-phase clone commands, the "still the ORIGINAL's wiki" acceptance criteria, and **dragon #21's prohibition on repurposing that clone**. Its other 29 lines are §3.2. |

**Two traps live in this bucket.**

1. **One line is in both §3.3 and §3.2 *within itself*.**
   `enterprise-migration.md`'s `diff -r -x '.git' docs/wiki/claims-model-starter ~/Development/claims-model-starter.wiki`
   names the **in-repo directory** (which Phase 4 renames) *and* the **clone directory** (which never
   moves). Phase 4 must edit the first half and leave the second. A `sed` over that line breaks it
   whichever way it runs. Re-derive it with
   `grep -n 'diff -r' docs/planning/enterprise-migration.md` rather than by line number.
2. **This bucket grows.** Session 229's Phase 2 added a fifteenth D-R5 line to
   `enterprise-migration.md` (*"The on-disk directory name stays `claims-model-starter.wiki` (rename
   plan D-R5)"*) after the `59615e2` inventory was taken. **The 17 above is the count in §2's frame,
   not a live count.** Do not treat it as a target — the criterion in §7.2 is written against the
   *pattern*, not the number, for exactly this reason.

**Why this is a bucket and not an exception.** §7.1 rules that a hit count is the wrong completion
criterion and an allowlist is right. An allowlist needs every permanent survivor to sit in a named
category, or the check prints a path and §7.2's *"no judgment call"* rule turns a correct execution
into a failed one. §3.3 is that category, and §7.2 group 3 is its enforcement.

---

## §4 Operator decisions — execution is BLOCKED until these are answered

These are not implementer's calls. Each changes what gets built.

> **✅ ALL FIVE ANSWERED — operator, 2026-08-20 (Session 227).** Verbatim: *"accept the 404, go with
> option A; accept all recommendations for D-R2, D-R3, D-R4, and D-R5."* Quoted rather than
> paraphrased because D-R1 is the one irreversible act in this plan (§1) and this sentence is the
> whole authorization for it.
>
> | # | Answer | Effect on the plan |
> |---|---|---|
> | **D-R1** | **Option A — accept the permanent 404.** No custom domain, so no phase ahead of Phase 1. | Phase 1 runs exactly as written. |
> | **D-R2** | **Yes** — `docs/wiki/claims-model-starter/` is renamed too. | Phase 4 stands; the 51 wiki-path lines are in scope. |
> | **D-R3** | **Yes** — rebrand `Home.md:1` and `_Sidebar.md:1`. | Phase 3 carries those two lines; they publish live the moment they commit. |
> | **D-R4** | **Rename first**, ahead of the enterprise fork; repair its five assertions inside the sweep. | Phase 2 stands. |
> | **D-R5** | **Re-point in place** — the clone keeps its directory name; `publish_wiki.sh`'s three filesystem-path lines (`:19`, `:24`, `:42`) are not touched. | Phase 4 is `set-url` only, never `mv`. **It changes 7 of that file's 10 old-name lines, not all 10** — §3.3's first row. |
>
> **§4 is closed. Do not re-open D-R1.** Once the rename lands, option B is no longer reachable —
> the old Pages URL cannot be recovered by any means, and §1.1 option C explains why the obvious
> rescue is strictly worse.

### D-R1 — The Pages URL. **Accept the permanent 404, buy a custom domain, or don't rename?**

See §1. This is the only irreversible consequence. **Recommendation: Option A (accept the 404)**,
on the evidence that the project is pre-UAT with no active issue tracker and the tutorial URL has no
established external audience. But it is the operator's call because the operator is the only one
who knows who has been given that link. **If the answer is B (custom domain), the domain must be
configured and verified BEFORE the rename**, which adds a phase ahead of everything else.

### D-R2 — Does `docs/wiki/claims-model-starter/` get renamed too?

**How much actually rides on this: 51 lines of wiki-path edits, plus a `git mv` of 25 files** —
*not* the 516 that match the path pattern. 465 of those 516 sit in frozen historical records that
keep the old path either way (§3.1); a further 9 are the self-referential hits in `BACKLOG.md`,
`SESSION_NOTES.md` and the un-editable `SESSION_RUNNER.md`. The honest number is ~42 real edits.

**Recommendation: yes.** The directory is named after the
repository, and `scripts/publish_wiki.sh:42-44` pairs it with a clone whose name GitHub derives from
the repository (`<repo>.wiki.git`); leaving it stale splits one name across two conventions and
guarantees a future session "fixes" it at a worse moment.

**Note what it is not:** renaming the source directory changes **nothing** about the published wiki.
`publish_wiki.sh:92` rsyncs the *contents* of `SOURCE_DIR` into the clone root, so the directory
name never reaches GitHub. The live wiki is unaffected either way. This makes D-R2 a purely internal
tidiness decision — which is an argument for doing it, and also an argument for doing it **last**.

### D-R3 — Do the wiki's reader-visible titles rebrand?

Two lines, and they are branding rather than paths:
- `docs/wiki/claims-model-starter/Home.md:1` — `# Claims Model Starter Wiki`
- `docs/wiki/claims-model-starter/_Sidebar.md:1` — `**Claims Model Starter**`

Renaming a repository is not the same act as rebranding its documentation. Note that other wiki
pages already call the project **"Model Project Constructor"** in prose
(`License.md:3`, `Software-Bill-of-Materials.md:3`), so the wiki is **already internally
inconsistent** — the sidebar says one name and the body text says another.
**Recommendation: yes, rebrand**, because the inconsistency exists today and the rename is the
natural moment to close it. But it changes what a reader sees, so it is the operator's call.
**These two lines auto-publish to the live GitHub Wiki the moment they are committed.**

### D-R4 — Sequencing against `docs/planning/enterprise-migration.md`

The rename does not conflict with the fork itself: §1.2/D6 keeps this repository on GitHub, public,
indefinitely, and Phase C4 is a one-time clone. **But the rename breaks five of that plan's
verification commands, three of them by making a real assertion pass vacuously** — see §6 dragon 1.
**Recommendation: rename first, and fix those five lines as part of the sweep** (they are already
inside the 97). Renaming after the fork would leave the clone carrying the old name in the same
five places, and the fork is not obviously imminent — B2 is its last remaining pre-fork gate.

### D-R5 — Is `~/Development/claims-model-starter.wiki` re-pointed **in place**, or renamed on disk?

These are two independent knobs and `publish_wiki.sh` reads both:

- `:72`/`:75` guard the clone's **origin URL** — changes with the repository name.
- `:42` sets the `WIKI_CLONE` default **filesystem path** — changes only if you `mv` the directory.
  GitHub's rename does not touch it. **`:19` and `:24` document that same path** — `:19` the default
  in the usage header, `:24` the destination directory of the documented `git clone` — so all three
  move together, or none do.

**Change `:42` without the `mv` and the script hard-fails at its own `:58` clone-exists guard.** They
are one paired decision, not two.

**Recommendation: re-point in place; leave `:42` and the directory name alone.** Renaming the
directory buys cosmetic consistency and costs three real things:
the methodology dashboard keys projects on the **directory basename**, so it would strand 26
snapshots of history in `~/Development/dashboard_history.jsonl` and fabricate a "new project" row;
Claude Code keeps a project-state directory keyed on that filesystem path; and
`~/Development/methodology`'s `tools/test_methodology_trim.py:1480,:1723` name the path in test
docstrings — another project's repository, which this one must not edit.

If the operator wants the `mv` anyway, it belongs in **Phase 4 step 1**, in the same breath as the
`set-url`, and `:42` moves with it in the same commit. Never one without the other.

---

## §5 Execution phases

**Each phase below is ONE session.** Close out at the end of each (`SESSION_RUNNER.md` Phase 3).
Do not bundle — FM #18 is exactly this shape, and the whole reason this plan exists is that
`SAFEGUARDS.md` refuses to let a rename be a "quick fix."

**Read this first — the ordering constraints that force the sequence:**

| # | Constraint | Consequence |
|---|-----------|-------------|
| K1 | Editing `mkdocs.yml` or `docs/*.md` triggers `mkdocs gh-deploy` (dragon 5) | The site fix cannot land **before** the rename (it would publish a canonical URL that does not exist) and must not land **long after** it (Pages does not redirect, so the site is dead in the gap). **Therefore they are one session** — Phase 1 |
| K2 | `publish_wiki.sh:72`'s guard literal and the wiki clone's origin URL must agree | Change them **together**, and not before any wiki-content commit |
| K3 | `tests/test_wiki_no_line_citations.py:60` asserts `WIKI_DIR.is_dir()` | The `git mv` and the `WIKI_DIR` constant must be in the **same commit** |
| K6 | `WIKI_DIR` is built from **path parts**, not a joined string (§6 dragon 11) | A sweep driven by the path pattern **cannot see it**. Drive the sweep from the bare name, not the path |
| K7 | The post-commit trigger fails **open** — stale prefix or merge commit means silent no-publish (§6 dragon 4) | Phase 4 must prove the hook fired, not merely that the script runs. Keep every phase on a **direct commit to `master`**, never a merge |
| K8 | `publish_wiki.sh` guards existence, not content (§6 dragon 3) | **Never `mkdir` the destination.** `git mv` only |
| K4 | The post-commit hook fires on any commit touching `docs/wiki/claims-model-starter/` | Keep wiki-content commits and non-wiki commits separate, so each publish is deliberate |
| K5 | GitHub redirects the repo, git remotes and the **wiki**; it does **not** redirect Pages (§1) | The Pages URL is the only thing that must be fixed urgently; everything else can be leisurely |

**No phase of this rename earns a `CHANGELOG.md` entry.** `docs/methodology/PROJECT_CONVENTIONS.md`
§2 gates the ledger on shipped-code or test-logic changes and explicitly exempts *"sessions whose
only code-tree touch is non-behavioral (fixture data, docstring or **path strings**)."* Every
`scripts/` and `tests/` edit in this plan is a path string. `CHANGELOG.md` is append-only — an entry
written by mistake can never be removed — so this is settled here rather than left to the executor.

---

### Phase 1 — Rename **and** repair the site. One session, one commit, one push.

**Gated on:** D-R1 answered (and, if the answer is "custom domain", on that domain being live and
verified **first**).

> **Why the rename and the `mkdocs.yml` fix are the same session.** An earlier draft of this plan
> made the rename a commit-free phase and deferred `site_url` to the next one. An adversarial review
> killed it: Pages does not redirect (§1), so that gap leaves the public site dead at its advertised
> URL for **at least one session boundary** — days, under "1 and done" — in direct violation of
> decision D6 ("keep public, indefinitely"). And the gap cannot be closed from the other side either:
> pushing `mkdocs.yml` *before* the rename fires `mkdocs gh-deploy` (K1) and publishes a site whose
> canonical tags and `sitemap.xml` advertise a path that does not exist yet. **The only order that
> leaves no broken window is: rename, then immediately push the site fix.** The outage becomes the
> length of one Actions run.

**Step 0 — record the baseline.** The site is *already* partly broken (dragon 10); the rename must
not be blamed for it.
```bash
curl -s -o /dev/null -w 'page=%{http_code} ' https://rmsharp.github.io/claims-model-starter/tutorial/
curl -s -o /dev/null -w 'css=%{http_code}\n'  https://rmsharp.github.io/claims-model-starter/assets/stylesheets/main.484c7ddc.min.css
#   measured 2026-08-19 (Session 226): page=200 css=404
git push origin master        # master is 2 commits ahead as of 59615e2; start from parity

# Back up the DEPLOYED SITE before the first forced deploy. origin/gh-pages is a single
# PARENTLESS commit and `gh-deploy --force --clean` replaces it outright — there is no
# ordinary revert. This is the same precaution enterprise-migration.md:787-789 took for A4
# (which is what the local `gh-pages-preA4` branch is).
git fetch origin gh-pages:refs/heads/gh-pages-pre-rename
git bundle create ~/gh-pages-pre-rename.bundle refs/heads/gh-pages-pre-rename
```

**Step 1 — rename, and re-point this clone only.**
```bash
gh repo rename model_project_constructor      # from inside the repo
git remote -v                                 # gh may rewrite origin; CONFIRM, do not assume
git remote set-url origin https://github.com/rmsharp/model_project_constructor.git   # if it did not
```
**Do not touch `~/Development/claims-model-starter.wiki` here** (K2). Its stale origin keeps working
via GitHub's wiki redirect; it moves in Phase 4, alongside the guard that checks it.

**Step 2 — the site commit, pushed immediately.** Exactly four files, chosen because two of them are
on the deploy trigger and the other two are the reader-facing URL:

| File | Lines | Change |
|------|-------|--------|
| `mkdocs.yml` | `:3`,`:4`,`:5` | `site_url`, `repo_url`, `repo_name` |
| `README.md` | `:9` | the advertised tutorial URL |
| `README.md` | `:7` | **rewrite, do not substitute** — dragon 6 |
| `docs/tutorial.md` | `:218` | wiki page URL (and it is a deploy trigger) |

Nothing else. Every other file is inert and belongs to Phase 2 — keeping them out means that if the
deploy comes back broken, `git bisect` lands on a four-file commit instead of a twelve-file one.
`mkdocs gh-deploy --force --clean` writes a **parentless** commit to `gh-pages`; it is not revertible
by ordinary means, so the commit that triggers it should be as small as the job allows.

**DONE looks like:** the site is live at the new URL, serving content that declares the new URL as
canonical, and the old URL's death has been *measured* rather than assumed.

**Verification:**
```bash
gh repo view --json nameWithOwner          # -> rmsharp/model_project_constructor
gh run list --workflow=publish-tutorial.yml --limit 1     # -> one run, from this commit, success
gh api repos/rmsharp/model_project_constructor/pages/builds/latest --jq '.status, .commit'
#   -> "built", and a commit newer than 1b9ce68. The legacy `dynamic/pages/pages-build-deployment`
#      builder is a SECOND stage (dragon 5) — a green publish-tutorial run does not prove it ran.
curl -s -o /dev/null -w '%{http_code}\n' https://rmsharp.github.io/model_project_constructor/tutorial/
#   -> 200. If 404, the deploy has not landed: `gh workflow run publish-tutorial.yml` and re-check.
curl -s -o /dev/null -w '%{http_code}\n' https://rmsharp.github.io/claims-model-starter/tutorial/
#   -> 404, EXPECTED and PERMANENT. This is §1 happening, not a defect. Record the number.
#      Do NOT "fix" it by renaming back — a second rename has the same consequence and also
#      breaks the redirect chain the first one established.
curl -s https://rmsharp.github.io/model_project_constructor/sitemap.xml | grep -c claims-model-starter   # -> 0
# The page returning 200 is NOT sufficient (dragon 10). Assert its stylesheet resolves:
css=$(curl -s https://rmsharp.github.io/model_project_constructor/tutorial/ \
      | grep -o 'href="\.\./assets/stylesheets/[^"]*"' | head -1 | sed 's/.*"\(.*\)"/\1/')
curl -s -o /dev/null -w '%{http_code}\n' "https://rmsharp.github.io/model_project_constructor/${css#../}"
#   -> compare against the step-0 baseline. 404 here means the PRE-EXISTING defect, not rename damage.
git fetch origin && git -C ~/Development/claims-model-starter.wiki fetch origin   # both -> succeed via redirect
uv run pytest -q                           # -> 1230 passed + 9 live-skipped, unchanged
```

**If it has to be undone:** `gh repo rename claims-model-starter` reverses the rename, and the
`gh-pages-pre-rename` bundle restores the deployed site. **But record this before you do it:** after
a round trip, *neither* name may ever be given to another repository — GitHub Docs warns that
reusing a renamed repository's old name destroys its redirects, and **552 lines of historical record
in this repository depend on the old-name redirects continuing to resolve.** *(552 is §3.1's
subtotal — the frozen-record bucket — and it is the group this sentence means. §3.3's 17 D-R5 lines
are live files, not records, and no redirect resolves a local directory path, so they are correctly
outside it. **Do not "reconcile" this number** against §3.3. Separately, Session 230 measured that
only **44** of the 552 carry an old-name URL at all — 465 are in-repo `docs/wiki/` path strings — so
"depend on the old-name redirects" overstates the exposure. Session 226's risk claim is left as
written: Phase 1 has run, the decision it informed is made, and re-litigating it is not a
plan-repair session's call. Flagged, not fixed.)*

**Session boundary. Close out here.**

---

### Phase 2 — Inert prose, and the other plans' broken assertions. **One commit. No deploy, no publish.**

**Gated on:** Phase 1 verified.
Touches **no** file on `publish-tutorial.yml`'s trigger list and **no** file under `docs/wiki/`, so
this commit fires neither the Pages deploy nor the wiki hook. That is deliberate: it is the phase
where a mistake is cheapest.

| File | Lines | Change |
|------|-------|--------|
| `SECURITY.md` | `:9` | advisory URL |
| `CONTRIBUTING.md` | `:6` | Contributing wiki-page URL |
| `docs/planning/enterprise-migration.md` | `:831`,`:832`,`:833`,`:1356`,`:1520` | the five `curl` criteria — **dragon 1**. Add `-fL` while you are there so a future rename fails loudly instead of vacuously. |
| `docs/planning/enterprise-migration.md` | `:1311`, `:1358` | **`# → unchanged, still the public wiki` becomes false** the moment Phase 4 re-points that clone. Restate as "still points at the ORIGINAL's wiki (under its current name)". |
| `docs/planning/enterprise-migration.md` | `:1256-1257`, dragon #21 at `:1436-1439` | **the instruction conflict — see below** |
| `docs/planning/enterprise-migration.md` | `:363`, `:1308`, `:1351` | the independence pattern — **dragon 1's sixth item** |

**The instruction conflict, stated plainly.** `enterprise-migration.md:1256-1257` and its dragon #21
both say, verbatim: ***"Do NOT delete or re-remote `~/Development/claims-model-starter.wiki`."***
Phase 4 of this plan re-remotes exactly that clone. A C4 executor who reads dragon #21 mid-fork will
refuse, correctly, and stall on the one phase that plan calls irreversible.

**The conflict is textual, not substantive.** Dragon #21 states its own reason: the clone *"continues
to serve the original's live auto-publish (D6: refresh and keep) and must keep working unchanged."*
Re-pointing it at **the same wiki under the repository's new name** is what *preserves* that
property; the prohibition is aimed at repurposing the clone for the **enterprise** wiki. **Amend the
wording to say that** — "do not aim this clone at the enterprise wiki; create a separate clone" —
rather than deleting the dragon, which is still a live and correct warning.

**DONE looks like:** no executable assertion anywhere in `docs/planning/` is falsified or made
vacuous by the rename, and no instruction in another plan contradicts this one.

**Verification:**
```bash
git grep -n "rmsharp.github.io/claims-model-starter" -- . \
  | grep -vE '^(CHANGELOG\.md|audits/|docs/architecture-history/|BACKLOG\.md|SESSION_NOTES\.md|docs/planning/repository-rename\.md)'
#   -> empty
grep -n "re-remote" docs/planning/enterprise-migration.md    # -> reworded, dragon #21 still present
gh run list --workflow=publish-tutorial.yml --limit 1        # -> UNCHANGED from Phase 1. No new run.
git -C ~/Development/claims-model-starter.wiki log --oneline -1   # -> UNCHANGED. No publish fired.
uv run pytest -q                                             # -> unchanged
```

**Session boundary. Close out here.**

---

### Phase 3 — Published wiki content. **One commit. This one goes live to readers.**

**Gated on:** D-R3 answered; Phase 2 verified.
**Touches `docs/wiki/claims-model-starter/**` only,** so the hook fires and publishes — which is the
point. The guard at `publish_wiki.sh:72` and the clone's origin still both say the old name, so they
still agree (K2) and the publish succeeds.

| File | Lines | Change |
|------|-------|--------|
| `docs/wiki/…/Contributing.md` | `:19`,`:20` | clone command → new URL and new directory. **Note the two published surfaces already contradict each other today:** `docs/tutorial.md:30` (on the Pages site) says `git clone <repo-url> model_project_constructor`, while this page (on the wiki) says `git clone …/claims-model-starter.git` then `cd claims-model-starter`. The clone URL will keep *working* via the redirect, so nothing 404s — it just leaves the reader in a directory named after a repository that no longer exists. |
| `docs/wiki/…/Contributing.md` | `:238` | issues URL |
| `docs/wiki/…/Home.md` | `:1` | title — **only if D-R3 = yes** |
| `docs/wiki/…/_Sidebar.md` | `:1` | sidebar heading — **only if D-R3 = yes** |
| `docs/wiki/…/Development-Workflow.md` | `:3` | **semantic rewrite — dragon 7** |
| `docs/wiki/…/Software-Bill-of-Materials.md` | `:3`,`:113` | **semantic rewrite — dragon 7** |

**Leave alone permanently:** `Changelog.md:124` — a dated historical entry, and the very file
`PROJECT_LEARNINGS.md` #32 was written about. It is in the §3.1 KEEP group; its path moves in
Phase 4, its content never does.
**Defer to Phase 4:** `Evolution.md:266`, `License.md:3` and `Contributing.md:124` are wiki-**path**
references, so they move with the directory, not with the branding.

**DONE looks like:** the live GitHub Wiki shows the new content, and the local clone is in parity.

**Verification** — capture the clone's HEAD **before** committing; a silent no-publish is the whole
risk here too (dragon 4):
```bash
BEFORE=$(git -C ~/Development/claims-model-starter.wiki rev-parse HEAD)
#   ... commit ...
AFTER=$(git -C ~/Development/claims-model-starter.wiki rev-parse HEAD)
[ "$BEFORE" != "$AFTER" ] && echo "HOOK FIRED AND PUBLISHED" || echo "FAIL: hook did not fire"
scripts/publish_wiki.sh                                              # -> "no changes to publish"
diff -r -x '.git' docs/wiki/claims-model-starter ~/Development/claims-model-starter.wiki   # -> identical
gh run list --workflow=publish-tutorial.yml --limit 1                # -> UNCHANGED. No wiki file is a Pages trigger.
```
**If the hook did not fire, do not hand-edit the clone** — fix the cause and re-run
`scripts/publish_wiki.sh`. It is idempotent (dragon 2).

> *Session 234 correction (Phase 5), discharging Session 232's filed defect #1. **Every command in
> the block above reads LOCAL state**, so all of them go green — and `HOOK FIRED AND PUBLISHED`
> prints — in the one state that matters: `publish_wiki.sh` commits into the clone at `:102` and
> pushes at `:104`, so a failed push exits **2 with the local commit left in place**. `BEFORE !=
> AFTER` is then TRUE, the re-run short-circuits at `:96` on an empty index and exits 0, and the
> local-vs-local `diff -r` is identical by construction — while the live wiki is **stale**. The
> recovery sentence directly above is **inert** in exactly that state: the re-run never reaches the
> push. See dragon 2 item 6. **The block is left byte-identical because Phase 3 has run and it is
> now a record of what its executor was told** — the same disposition §9.1 gave Phase 2's `-fL`
> advice. What the phase actually needed is appended below; Session 232 ran it by hand and Phase 3
> passed.*

**Push-reachability — appended after the fact (Session 234). Run these too:**
```bash
CLONE=~/Development/claims-model-starter.wiki          # D-R5: the on-disk name never moves
git -C "$CLONE" push --dry-run origin master           # BEFORE committing -> "Everything up-to-date"
[ "$(git -C "$CLONE" rev-list --count origin/master..master)" = 0 ] && echo PUSHED || echo "STALE: exit-2"
curl -sf https://raw.githubusercontent.com/wiki/rmsharp/model_project_constructor/Home.md >/dev/null \
  && echo "LIVE WIKI READS BACK"                       # the public artifact, not a local mirror
```
**If the count is non-zero, the push failed and `publish_wiki.sh` cannot retry it** — push the clone
directly (`git -C "$CLONE" push origin master`), then re-check. Do not re-run the publisher first.

**Session boundary. Close out here.**

---

### Phase 4 — The directory move and the mechanisms that key on it. **One commit + one out-of-repo change.**

**Gated on:** D-R2 = yes; Phase 3 verified. **If D-R2 = no, this phase does not exist** — skip to
Phase 5, and the 51 wiki-path lines on the change side (§4 D-R2) all stay as they are, along with
the directory itself.

**This is the highest-risk phase. Its whole risk is K3 atomicity.**

Order within the session:

1. **Re-point the wiki clone first** (out of repo, no commit):
   ```bash
   git -C ~/Development/claims-model-starter.wiki remote set-url origin \
       https://github.com/rmsharp/model_project_constructor.wiki.git
   ```
   From this moment until the step-3 commit lands, `publish_wiki.sh:72` still greps for the **old**
   literal and therefore rejects the re-pointed clone: publishing is **disabled**, fail-closed and
   loud (dragon 2). That is the intended safe state, and it is why the guard literal must be in the
   same commit as everything else.
   **Whether you also `mv` the directory is D-R5, and it is a PAIRED change, not an optional
   flourish.** `publish_wiki.sh:42` is the `WIKI_CLONE` **filesystem-path** default; GitHub's rename
   does not touch it. Change `:42` without the `mv` and step 3 dies at the `:58` clone-exists guard;
   `mv` without changing `:42` and it dies the same way. Either do both here, or neither — the
   recommendation in D-R5 is **neither**.

2. **One commit, everything atomic:**
   ```bash
   git mv docs/wiki/claims-model-starter docs/wiki/model_project_constructor
   ```
   plus, in the same commit:
   - `scripts/publish_wiki.sh` — **7 of its 10 lines. Not all 10.**
     - **CHANGE (7):** `:2`, `:11`, `:23`, `:44`, `:63`, `:72`, `:75`.
     - **KEEP, permanently (3):** `:19`, `:24`, `:42`. These are the clone's **filesystem path**
       `~/Development/claims-model-starter.wiki` — `:19` the `WIKI_CLONE` default's doc comment,
       `:24` the documented clone command's destination directory, `:42` the `WIKI_CLONE` default
       itself. D-R5 answered *"re-point in place"*; GitHub's rename moves a URL, never a local
       directory. **D-R5 and step 1 above both say what happens if you ignore this: change `:42`
       without the `mv` and the script hard-fails at its own `:58` clone-exists guard — wiki
       publishing stops, on the very commit that lands the rename.**
     - **Note the split inside the old `:23-24` range**, which is why this used to read "all 10":
       `:23` is the clone **URL** and changes; `:24` is the destination **directory** on the very
       next line and does not. A range citation hid a boundary.
     - Verification for this bullet, after editing: `grep -n "claims-model-starter"
       scripts/publish_wiki.sh` → **exactly 3 lines, `:19`, `:24`, `:42`.** Not 0.
   - `.githooks/post-commit` — `:3`, `:18`
   - **Do not touch `publish_wiki.sh:101`.** It already emits the new name
     (`COMMIT_MSG="docs: sync wiki from model_project_constructor@$SOURCE_SHA"`) — evidence the
     rename was anticipated, and a line a careless sweep would "fix" into being wrong.
   - `tests/test_wiki_no_line_citations.py` — `:7`, `:38` **(K3 — the suite fails if this is late)**
   - the remaining wiki-path prose: `THIRD-PARTY-LICENSES:50`, `docs/style/statistical_terms.md`
     (`:7`,`:103`,`:137`,`:165`), `docs/methodology/PROJECT_CONVENTIONS.md` (`:11`,`:24`,`:25`,`:44`),
     `executive-summaries/stakeholder-readiness-dossier.qmd` (`:57`,`:95`),
     `docs/wiki/…/License.md:3`, `docs/wiki/…/Evolution.md:266`, `docs/wiki/…/Contributing.md:124`
   - the wiki-path references inside the other plans — **all five are pure path citations**:
     `docs/planning/opencode-adapter-spec.md` (`:9` ×2, `:655`, `:656`) and
     `docs/planning/httpx-adapter-migration.md` (`:110`, `:270`), plus the 17 path lines inside
     `docs/planning/enterprise-migration.md`
     — **and one more line in that file that is NOT a path line and that nothing else owns:** its
     §2.6 coupling-points row describing `publish_wiki.sh:72`/`:75`'s guard literal (`:345` as of
     2026-08-20; re-derive with `grep -n 'Hard-rejects' docs/planning/enterprise-migration.md`).
     **This commit is what falsifies it** — it rewrites that guard to grep for
     `model_project_constructor.wiki` — so it must be repaired here, not left to Phase 5.
     Phase 2 handled that file's five `curl` URL lines and its two wiki-comment lines and **those**
     must not be re-touched; `:345` was never among them.
   - **`CLAUDE.md`** — a new bullet under *Project-Specific Methodology Adaptations* recording that
     `SESSION_RUNNER.md:209` still names the old directory and must not be edited (dragon 8)

3. **Let the hook fire, and use it as the trigger test.** This is the only phase that can prove
   dragon 4 did not bite, so do **not** muzzle it. Capture the clone's HEAD first:

   ```bash
   BEFORE=$(git -C ~/Development/claims-model-starter.wiki rev-parse HEAD)
   git commit -m "refactor(wiki): rename source directory to model_project_constructor"
   AFTER=$(git -C ~/Development/claims-model-starter.wiki rev-parse HEAD)
   [ "$BEFORE" != "$AFTER" ] && echo "HOOK FIRED AND PUBLISHED" || echo "FAIL: dragon 4 — silent no-publish"
   git -C ~/Development/claims-model-starter.wiki show --stat HEAD
   #   -> exactly 3 changed lines: Evolution.md:266, License.md:3, Contributing.md:124.
   #      The 25 renamed files must NOT appear — the directory name never reaches the clone.
   ```

   **Why this commit publishes and the directory rename does not.** `publish_wiki.sh:92` rsyncs the
   *contents* of `SOURCE_DIR` into the clone root, so a pure `git mv` is a publish **no-op**. This
   commit publishes only because it also edits three wiki pages' path prose. That makes the clone's
   3-line diff a two-in-one proof: **the trigger still works** (dragon 4 clear) **and the directory
   rename disturbed no published byte** (only the 3 intended lines moved).

   Then confirm idempotence and read the trigger literal back **out of the file** — do not retype it,
   or the check becomes a tautology that cannot see a typo:
   ```bash
   scripts/publish_wiki.sh                                          # -> "no changes to publish"
   grep -c 'claims-model-starter' .githooks/post-commit             # -> 0
   grep -c "\^docs/wiki/model_project_constructor/" .githooks/post-commit   # -> 1, UNDERSCORES
   #   The hyphenated form `model-project-constructor` is the likeliest typo in this whole plan
   #   (three naming conventions live here — dragon 6) and it fails SILENTLY. Read it, don't assume.
   ```
   **If `HOOK FIRED` did not print, stop.** Do not hand-edit the clone. The trigger prefix is stale —
   fix `.githooks/post-commit:18`, amend, and re-run.

   > *Session 234 correction (Phase 5) — the same defect as Phase 3's, filed by Session 232 as
   > defect #1 and carried here because this phase's block is identical in kind. `BEFORE != AFTER`,
   > `show --stat HEAD`, the publisher re-run and the two greps all read **local** state, so an
   > `exit 2` push failure (`publish_wiki.sh:104-108`, local commit left in place) prints
   > `HOOK FIRED AND PUBLISHED` while the live wiki is stale. **Left byte-identical: Phase 4 has
   > run and this is now a record.** Session 233 ran the appended checks by hand and Phase 4 passed
   > them — the live pages were read back over HTTP. See dragon 2 item 6.*

   **Push-reachability — appended after the fact (Session 234). Run these too:**
   ```bash
   CLONE=~/Development/claims-model-starter.wiki
   # Order matters IN THIS PHASE: run the dry-run AFTER step 1's `remote set-url`, BEFORE step 2's
   # commit. It talks to the remote directly, so it is unaffected by the `:72` guard being
   # momentarily out of step with the clone's origin (dragon 2 item 5).
   git -C "$CLONE" push --dry-run origin master        # -> "Everything up-to-date"
   [ "$(git -C "$CLONE" rev-list --count origin/master..master)" = 0 ] && echo PUSHED || echo "STALE: exit-2"
   curl -sf https://raw.githubusercontent.com/wiki/rmsharp/model_project_constructor/Evolution.md \
     | grep -c 'outward-facing wiki pages'             # -> 1, read off the PUBLIC artifact
   ```

**DONE looks like:** the suite is green, the hook fired and published on its own, the live wiki
differs from its pre-phase state by exactly the three intended lines, and no page was renamed,
added, or removed.

**Verification:**
```bash
uv run pytest -q                                    # -> 1230 passed + 9 live-skipped, unchanged
uv run ruff check src/ tests/ packages/ scripts/    # -> clean
git diff --name-status -M HEAD~1 | awk '{print $1}' | sort | uniq -c
#   -> 22 R100  +  3 R09x.  The three are Evolution.md, License.md and Contributing.md, which
#      step 2 also edits one path line in each, so they are rename+edit rather than pure renames.
#      Use --name-status, NOT --stat: `git diff --stat -M` prints no similarity code at all
#      (measured 2026-08-20 -- it renders a rename as `docs/wiki/{claims-model-starter =>
#      model_project_constructor}/Foo.md | 0`, and `grep -c R100` on it returns 0).
#      What this does NOT prove: `-M` detects renames from content similarity, so a hand-rolled
#      delete+add of identical files also reports R100 (measured: 25 R100 without any `git mv`).
#      The criterion asserts the 25 pages MOVED intact -- it cannot witness which command moved
#      them.  Any `A`/`D` pair in the output means a page's content diverged, not that `git mv`
#      was skipped.
ls docs/wiki/model_project_constructor/ | wc -l      # -> 25
grep -rn "claims-model-starter" scripts/ tests/ .githooks/ \
  | grep -v '^scripts/publish_wiki\.sh:'            # -> empty
grep -n "claims-model-starter" scripts/publish_wiki.sh
#   -> EXACTLY 3 lines: :19, :24, :42. The D-R5 filesystem path (§3.3, first row).
#      NOT 0 -- 0 means a sweep drove them out and `scripts/publish_wiki.sh` now dies at its :58
#      guard. NOT 10 -- 10 means this phase's edit did not land.
```

**The exclusion and the assertion are one check, not two.** Dropping `scripts/` from the first grep,
or `--exclude=publish_wiki.sh`, would both be wrong: measured 2026-08-20, `--exclude` matches a
**basename glob**, so it also swallows any other `publish_wiki.sh` anywhere in those trees — a probe
file at `packages/probe/publish_wiki.sh` went undetected, while the path-anchored `grep -v` above
caught it. Anchor on the path, and always pair the exclusion with the 3-line assertion.

**Recovery if it goes wrong:** the repo commit is one `git revert` away, and the clone's origin goes
back with the same `set-url` command. **This phase does push to the live wiki** (step 3, three
lines), so recovery there is `git -C <clone> revert HEAD && git -C <clone> push` — the wiki repo has
full history and nothing is lost. **Nothing in this phase is irreversible.** The only irreversible
act in the whole plan is the Pages URL in Phase 1 (§1).

**Session boundary. Close out here.**

---

### Phase 5 — Reconcile, classify the residue, close the item. **One commit.**

**Gated on:** Phase 4 verified (or Phase 3 verified, if D-R2 = no).

Walk the **whole** remaining `git grep` and classify **every** surviving hit against §3. Anything
that is neither a **§3.1** historical record, nor a **§3.3** D-R5-pinned line, nor a deliberate
self-reference, is a miss — fix it here.

> ⚠ **Session 230: the §3.3 clause is not optional, and its absence was fail-dangerous.** Without
> it this rule reads as an order to "fix" the 17 lines naming
> `~/Development/claims-model-starter.wiki` — 3 in `scripts/publish_wiki.sh`, 14 in
> `enterprise-migration.md`. Obeying it points those instructions and acceptance criteria at a
> directory that **does not exist**, hard-fails `publish_wiki.sh` at its `:58` clone-exists guard,
> and contradicts both D-R5 and `enterprise-migration.md`'s own *"The on-disk directory name stays
> `claims-model-starter.wiki` (rename plan D-R5)."* **Leave every §3.3 line alone — with one
> exception: the dual-purpose `diff -r` line (§3.3 trap 1) must have had its *in-repo* half changed
> by Phase 4. Verify that, do not "leave it alone" wholesale, and never `sed` it.** The four
> independence-grep sites are out of scope here too — they are flagged to the operator in
> `BACKLOG.md`, and §8 says they are not this plan's to rewrite. *(Session 234: that flag lived
> inside the rename item this phase deletes, so Phase 5 **re-filed it as its own `BACKLOG.md`
> item** rather than letting an open operator decision die with the item it happened to be filed
> under. See §9.2. **Session 240: ruled and executed** — the criterion is restated in
> `enterprise-migration.md` §2.6 and the backlog item is closed, so that grep now returns nothing;
> see dragon 1's RULED note.)*

Then:
- **`BACKLOG.md`: delete the rename item's rows; do not substitute them.** 17 of its 18 hits are the
  item itself and vanish with it. **The 18th, `BACKLOG.md:74`, is a genuine wiki-path substitution**
  inside an unrelated item and moves with the directory (it should already have been done in
  Phase 4 — verify, do not assume).
- **`README.md`** — re-read `:7` end to end. It was rewritten in **Phase 1** under time pressure with
  the site down; this is the calm second look (dragon 6).
- **This plan's own status line** (`:3`) — it has read **`Status: IN EXECUTION`** since the Session
  230 repair, listing Phases 1 and 2 and their commits. Phase 5 flips it to **executed** and appends
  Phases 3, 4 and 5's hashes. *(It read `Status: PLAN` until then; that literal is gone, so grep for
  `**Status:**`.)*
- **File the four out-of-scope findings** in §8.1 as backlog items.

**DONE looks like:** every check in §7 passes — including §7.4's three, which the allowlist cannot
reach — and the backlog item is gone rather than edited.


---

## §6 Dragons — where the implementation is non-obvious

*Ordered by how much damage being wrong causes.*

### Dragon 1 — The rename silently converts three real assertions in `enterprise-migration.md` into vacuous passes. **This is a fail-open, and it is the worst thing in this plan.**

Phase A1's whole purpose was to take already-public audit pages **off** the Pages site. Its
verification is three `curl`s that assert the pages are gone:

```
docs/planning/enterprise-migration.md:831   curl … /claims-model-starter/audits/2026-06-01-technical-debt-audit/   # → 404
docs/planning/enterprise-migration.md:832   curl … /claims-model-starter/deployment/bedrock-enterprise/            # → 404
docs/planning/enterprise-migration.md:833   curl -s … /claims-model-starter/sitemap.xml | grep -c audits           # → 0
docs/planning/enterprise-migration.md:1520  (same sitemap check, repeated in the C-phase criteria)
```

After the rename **the entire host path 404s** (§1). All three checks then pass — `:831`/`:832`
because everything 404s, and `:833`/`:1520` because `curl` on a 404 emits a body with no `audits`
in it, so `grep -c` returns 0. **They would report containment as verified while proving nothing.**
Rewrite all four against `model_project_constructor`, or they are worse than deleted.

A fifth line fails in the opposite, honest direction:

```
docs/planning/enterprise-migration.md:1356  curl … /claims-model-starter/tutorial/   # → 200 (still live)
```

This is a **Phase C4 acceptance criterion asserting the original's site is still up**. Post-rename it
returns 404 and C4 reports a false failure. Loud, so less dangerous — but it must move too.

**Fix all five in Phase 2.** They are executable acceptance criteria for un-executed phases, not
prose. **Done — Session 229, `73b9418`.**

> *Session 230 correction. This line previously read* **"Fix all five in the same commit as
> `mkdocs.yml`."** *`mkdocs.yml` is a Phase 1 file and only Phase 1's (Phase 1's table); Phase 1
> explicitly disclaimed every other file (*"Every other file is inert and belongs to Phase 2"*) and
> closed without these five — `c1fe06f` touched three files, none of them `enterprise-migration.md`.
> Phase 2's table always assigned them. The plan shipped self-inconsistent here; the rename did not
> break it. It matters because this dragon is billed as the second-most-serious finding in the
> document, so it is the passage a later reader is most likely to consult in isolation — where it
> sent them hunting inside a closed phase. **Only the sequencing sentence was wrong; the fail-open
> finding above it is correct, and it is why Phase 2 existed.**

**One warning about how these five were actually fixed.** Phase 2's table says *"Add `-fL` while you
are there so a future rename fails loudly instead of vacuously."* **Measured in Session 229: that
does not work.** A shell pipeline reports its **last** command's status, so `-f` on a piped `curl`
is invisible — `curl -sfL <live> | grep -c audits` and `curl -sfL <404> | grep -c audits` both print
`0` and both exit `1`. The vacuous pass this dragon exists to close survives its own prescription.
What shipped instead: the two sitemap checks capture **curl's own exit** (`sitemap=$(curl -sfL …) ||
echo FAIL`), the two 404-expecting checks got a **positive control** in front of them (a host that
404s every path makes "→ 404" meaningless), and `-fL` was applied only to the tutorial check —
quoted as `:1356` above, which is its **pre-repair** position; it is `:1368` today — because that is
the one line expecting 200, where `-f` is genuinely load-bearing. **If you ever assert on `curl … | grep`, capture curl's exit
separately.**

**And a sixth, subtler one — the rename reopens the exact hole that check was built to close.**
`enterprise-migration.md:363`, `:1319` and `:1363` carry the C4/C5 *clone-independence* criterion:

```bash
git grep -n -I -iE 'rmsharp|rmsharp\.github\.io|github\.com/rmsharp|claims-model-starter' -- . \
  | grep -vE '^(SESSION_NOTES|CHANGELOG|PROJECT_LEARNINGS)\.md|^docs/architecture-history/'   # -> 0
```

Its own comment at `:1361-1362` states the danger it exists to prevent: *"a narrower pattern can pass
'→ 0' while a hardcoded `claims-model-starter` string survives in the clone's publish_wiki.sh."*
After the rename, that hardcoded string **is** `model_project_constructor.wiki` — and the
`claims-model-starter` alternative no longer matches it. The `rmsharp` alternatives still catch
*URL* forms, so the check does not collapse; what it stops catching is a **bare, un-URL'd mention of
the repository name**, which is precisely the `publish_wiki.sh` case the comment names.

**The obvious repair does not work.** Adding `model_project_constructor` as a fifth alternative makes
the criterion permanently unsatisfiable: that string matches **1,916 lines across 183 files** in this
repository — it is the import package, the `src/` directory, and the distribution's stem. A criterion
that can never return 0 is not a criterion.

**Recommended repair: scope the check by path instead of by pattern** — e.g. run the bare-name grep
over `scripts/`, `.githooks/`, `mkdocs.yml` and `tests/` only, where a hardcoded repository name is
always a defect. **Flag this to whoever owns `enterprise-migration.md`; do not silently rewrite
another plan's acceptance criteria beyond the five URL lines above.**

> **Session 230: that recommendation was never measured, and it does not work either.** Re-derived
> 2026-08-20 at `be3bc4a`:
>
> ```bash
> git grep -c "model_project_constructor" -- scripts/ .githooks/ mkdocs.yml tests/
> #   -> 336 lines across 74 tracked files:  tests/ 317, scripts/ 16, mkdocs.yml 3, .githooks/ 0.
> #      286 of the 317 are `from|import model_project_constructor` — the import package's own name.
> ```
>
> **A criterion that can never return 0 is not a criterion** — the exact objection this dragon raises
> two paragraphs above against the fifth-alternative fix, and it applies to this dragon's own
> proposal with a wider margin. (The fifth-alternative figure quoted above, *"1,916 lines across 183
> files"*, re-derives today as **1,986 across 187** — the conclusion is unchanged and the number was
> never load-bearing.)
>
> **The path set that does work is the four coupling points in `enterprise-migration.md`'s own
> §2.6 (*"Host and identity coupling points"*), not whole directories:**
> `scripts/publish_wiki.sh`, `.githooks/post-commit`, `mkdocs.yml`,
> `tests/test_wiki_no_line_citations.py` — the files where a hardcoded repository name is always a
> defect. Post-Phase-4 that set legitimately contains the **new** name, so the criterion has to be
> restated as *"no repository name **other than the clone's own**"*, not *"no name at all"*.
> **That restatement is an operator ruling and is NOT this plan's to make** (§8, first bullet). The
> flag, with these measurements, is filed in `BACKLOG.md`. *(Session 234: re-filed as a
> standalone item when Phase 5 deleted the rename item — rather than letting an open operator
> decision die with the item it happened to be filed under.)*
>
> **RULED, 2026-08-24 (Session 240) — this dragon is closed, and the recommendation two paragraphs
> above must NOT be executed.** The operator ruled exactly the restatement this note proposes: *"no
> repository name other than the clone's own"*, scoped to the four §2.6 coupling files. It is
> written into `enterprise-migration.md` §2.6 as a **two-arm** criterion — arm 1 the unchanged
> repository-wide personal-account check, arm 2 the scoped foreign-repository-name check — and both
> arms are now inlined at the C4 and C5 verify blocks. Anchor on content, not on the line numbers
> quoted above: `grep -n 'clone-independence criterion (restated' docs/planning/enterprise-migration.md`.
> The backlog item is closed and the grep for it now returns nothing. **The re-derived figures at
> that cut were 1,103/176 and 357/269**, not the 1,986/187 and 336/74 recorded above — the drop is
> benign and worth knowing: trims 4-6 relocated session history into `docs/architecture-history/`,
> which the criterion's own exclusion filter drops. The conclusion never depended on the digits.)*

### Dragon 2 — The wiki publisher's own guards all fail CLOSED. Verified, not assumed — and narrower than it sounds (dragons 3 and 4).

The filed backlog item calls `publish_wiki.sh:72-75` a *"hard blocker on rename."* It is a blocker on
**publishing**, not on the **commit**, and the distinction decides how much sequencing care it needs.
Mechanics, each verified this session:

1. **The hook fires on the rename commit either way.** `git diff-tree --no-commit-id --name-only -r`
   lists a rename as *both* the old and the new path — verified empirically against `35ccbd9`, which
   shows `docs/planning/bedrock-testing-enablement.md` **and**
   `docs/architecture-history/bedrock-testing-enablement.md`. So the old pattern matches the deleted
   path and the new pattern matches the added path. **On the rename commit specifically** there is
   therefore no "the hook silently skips" case — but do not generalise that reassurance one commit
   further: dragon 4 is exactly the case where it does silently skip.
2. **The version that runs is the post-commit working tree** — i.e. the *updated* hook and the
   *updated* script, if they were changed in that same commit.
3. **A failing hook cannot hurt the commit.** `man githooks`: post-commit *"is meant primarily for
   notification, and cannot affect the outcome of git commit."*
4. **Every guard in `publish_wiki.sh` exits 1 and changes nothing:** `:53` source dir missing,
   `:58` clone missing, `:72` origin URL mismatch, `:80` wrong branch, `:86` dirty clone. Each is
   loud and non-destructive. **But they are existence checks, not content checks — see dragon 3.**
5. **The one genuinely coupled pair:** `publish_wiki.sh:72`'s literal `claims-model-starter\.wiki`
   and the *out-of-repo* origin URL of `~/Development/claims-model-starter.wiki`. Change either
   alone and publishing stops with a clear message. **The clone's old origin URL keeps working
   after the rename** — GitHub redirects wikis — so there is no urgency at all. The honest fix is
   `git remote set-url` on the clone **and** the guard literal, in the same session, minutes apart
   (Phase 4 steps 1 and 2). Splitting them across a session boundary is what turns a fail-closed
   guard into a multi-day publishing outage nobody notices.
6. **One exit path is neither a guard nor fail-closed — `exit 2`, the failed push. Added Session
   234 (Phase 5), discharging Session 232's filed defect #1.** Every guard in item 4 runs *before*
   anything changes. The push does not: `:92` rsyncs, `:102` commits **into the clone**, and only
   then `:104` pushes — so a push failure exits **2 with the local commit left in place**
   (`:104-108`; the script's own header `:32` says so). **Three prescribed checks then report
   success while the live wiki is stale:** the clone's `HEAD` *has* moved, so `BEFORE != AFTER`
   prints `HOOK FIRED AND PUBLISHED`; a re-run short-circuits at `:96` on an empty index and exits
   **0**; and a local-vs-local `diff -r` is identical by construction. **"It is idempotent, re-run
   it" is inert here** — the re-run never reaches `:104`. It is not silent (the hook `exec`s the
   script, so `:105-106`'s stderr reaches the terminal) but it is **unchecked**, and `man githooks`
   guarantees git discards the status. **Only two things can see it:**
   `git -C <clone> rev-list --count origin/master..master` (must be `0`) and a `curl` of the live
   page. Both are now appended to Phases 3 and 4 and to §7.3. Recovery is a **direct**
   `git -C <clone> push origin master`, never another publisher run.

**Conclusion for the `publish_wiki.sh` guard specifically: loud, safe, and recoverable.** Plan for
it; do not fear it. **The hook's own trigger is a different story — dragon 4 — and that one is
silent.**

> *Session 234 qualification. That conclusion is true of the **guards** and was never meant to
> cover the push, but it is the sentence a reader carries away, and item 6 above is the exception
> to all three words: the exit-2 state is loud-but-unchecked, leaves a commit behind, and is **not**
> recoverable by the mechanism the plan offers for it. The enumeration was complete for `exit 1`
> and silently partial for the script as a whole — `grep -cin 'push fail'` over this document
> returned **0** before this repair.*

### Dragon 3 — `publish_wiki.sh` has no emptiness check, and one plausible execution order **deletes the entire public wiki and pushes it**

`:53` tests `[ ! -d "$SOURCE_DIR" ]` — **existence, not content.** Line `:92` is then:

```bash
rsync -a --delete --exclude='.git/' "$SOURCE_DIR/" "$WIKI_CLONE/"
```

An **empty-but-existing** `SOURCE_DIR` passes every guard, and `--delete` then removes all 25 pages
from the clone. `:94-102` stages the deletions, sees a non-empty diff, commits, and `:104` **pushes**.
The live public wiki is emptied.

`git mv` never produces this state — it removes the old directory outright. **The way an executor
reaches it is by hitting a `git mv` error first.** `man git-mv`: the single-source form requires the
destination **not** to exist, while the multi-source form requires the destination directory to
**already** exist. An operator whose one-shot `git mv` errors reaches for the multi-source form, and
the multi-source form needs a `mkdir`:

```bash
mkdir docs/wiki/model_project_constructor            # <- the fatal step
# edit publish_wiki.sh SOURCE_DIR to point at it
git add -A && git commit -m "wip: start the wiki move"   # hook fires, source is empty
```

**Rule, absolute: never create the destination directory. Use `git mv` and nothing else, and never
commit a state in which `SOURCE_DIR` resolves to a directory that does not already contain the 25
pages.** Recovery exists (the wiki repo has history; `git -C <clone> revert` and push) but it is a
public-facing outage in the meantime.

*This is pre-existing and not caused by the rename. It is in scope for this plan only as a rule the
executor must follow; hardening the script with a page-count check is filed separately (§8).*

### Dragon 4 — The post-commit trigger is the one **fail-OPEN** mechanism, and the rename is exactly what arms it

Dragon 2 establishes that the *publisher* fails closed. **The hook that decides whether to call the
publisher does not.** `.githooks/post-commit:18-20`:

```bash
if ! git diff-tree --no-commit-id --name-only -r HEAD | grep -q '^docs/wiki/claims-model-starter/'; then
    exit 0
fi
```

Rename the directory and leave that prefix stale, and every subsequent commit that edits a wiki page
produces paths under `docs/wiki/model_project_constructor/`, the `grep` misses, and the hook
**exits 0 in silence** — no error, no output, no non-zero status. The wiki source and the published
wiki then diverge indefinitely, and the first person to notice is a reader.

Note the asymmetry that makes this easy to miss: **on the rename commit itself the hook still fires**,
because `diff-tree` lists a rename as both the deleted old path and the added new path (verified
against `35ccbd9`). So the executor gets one reassuring successful publish, and the failure begins on
the *next* wiki edit — a different session, with no obvious cause.

**And no test will ever catch it.** `git grep -ln "post-commit\|publish_wiki\|hooksPath" -- tests/`
returns **nothing**: the hook and the publisher have **zero** test coverage, and neither is exercised
by `ci.yml`. Every other mechanism in this rename has a guard that shouts or a test that reddens.
This one has neither, which is exactly why Phase 4's proof has to be an end-to-end observation rather
than an assertion.

> **SUPERSEDED, 2026-08-24 (Session 241).** That paragraph was true when written and is now false.
> `tests/scripts/test_wiki_publishing.py` gives the pair **38** tests, collected by `ci.yml`'s
> `uv run pytest -q` job, and one of them (`test_hook_prefix_matches_publish_script_source_dir`)
> pins the hook's trigger prefix to the publisher's `SOURCE_DIR` — so the *specific* divergence
> this dragon describes now reddens a test instead of going unnoticed. **The dragon's advice still
> stands** for any future move of the wiki directory: keep the prefix and the `git mv` in one
> commit, and prove Phase 4 by exercising the hook end-to-end. What has changed is only that the
> "no test will ever catch it" premise no longer holds.

**Two consequences for Phase 4:**
- The trigger prefix and the `git mv` **must** be in the same commit (already required by K3 for a
  different reason — this is a second, independent reason).
- **Phase 4's verification must exercise the hook, not just the script.** `scripts/publish_wiki.sh`
  returning "no changes to publish" proves the *script* works; it proves nothing about the *trigger*.
  See Phase 4's step 3.

**The likeliest way to trigger it is a typo, and the repository makes that typo natural.** This
project deliberately runs three naming conventions at once (dragon 6), so writing
`^docs/wiki/model-project-constructor/` — **hyphens** — into `:18` is the single most probable slip
in the whole rename. It produces no error, no failing test, and no output. Only an end-to-end check
that the clone actually advanced can see it; Phase 4 step 3 is built for exactly this.

**A second silent case, and it has ALREADY HAPPENED IN THIS REPOSITORY.** The hook's `git diff-tree`
call carries neither `-m` nor `--cc`, so it emits **nothing at all for a merge commit**. Verified
against `ff04c02` ("merge: land feat/httpx-adapters"), a real 2-parent merge in this history:

```
git diff-tree --no-commit-id --name-only -r      ff04c02  ->  0 lines      (what the hook runs)
git diff-tree --no-commit-id --name-only -r -m   ff04c02  ->  5 wiki pages (what actually changed)
       Agent-Reference.md, Content-Recommendations.md, Contributing.md,
       Security-Considerations.md, Software-Bill-of-Materials.md
```

Five published pages changed and the publisher never ran. **This plan keeps every phase on a direct
commit to `master` (K7) precisely because of this**, and a future session that adopts PR merges
inherits a wiki publisher that is already, demonstrably, silently broken.

### Dragon 5 — The Pages deploy fires on the very files the sweep edits, and that pins the whole sequence

`.github/workflows/publish-tutorial.yml:6-10` triggers on pushes to `master` touching
`docs/*.md`, `mkdocs.yml`, the workflow itself, or `pyproject.toml`, and runs
`mkdocs gh-deploy --force --clean`. Exactly two files in the sweep are on that list —
**`mkdocs.yml` (3 lines) and `docs/tutorial.md` (1 line)** — so the commit carrying them *is* a
deploy. (`docs/*.md` is **single-level**: `docs/style/statistical_terms.md` and
`docs/methodology/PROJECT_CONVENTIONS.md` are **not** triggers.)

This squeezes the sequence from both sides:

- **Not before the rename.** A deploy that stamps `site_url: …/model_project_constructor/` into
  canonical tags and `sitemap.xml` while the repo is still `claims-model-starter` publishes a live
  site advertising a URL that does not exist.
- **Not long after it.** Pages does not redirect (§1), so between the rename and the deploy the
  advertised URL is simply dead — and under "1 and done" a phase boundary is days, not minutes.

**There is also a third workflow nobody has named.** `gh api …/actions/workflows` lists **three**
active workflows, not the two in `.github/workflows/`: `ci.yml`, `publish-tutorial.yml`, and
**`dynamic/pages/pages-build-deployment`** — GitHub's legacy Pages builder. `publish-tutorial.yml`
pushes `gh-pages`; the dynamic builder then publishes it. A post-rename "did the site rebuild?" check
that looks only at `publish-tutorial.yml` sees half the pipeline; `gh api …/pages/builds/latest` sees
the other half. Check both.

**Hence Phase 1 is one session containing both.** Keep the commit to the four files that actually
need to move together: `mkdocs gh-deploy --force --clean` writes a **parentless** commit to
`gh-pages` (no ordinary revert), so the triggering commit should be small enough to bisect.

### Dragon 6 — `README.md:7` cannot be string-replaced; it must be rewritten

```
The repository is published as `claims-model-starter` on GitHub; the internal package name
remains `model-project-constructor`.
```

A `sed` produces *"published as `model_project_constructor` … the internal package name remains
`model-project-constructor`"* — a sentence whose only remaining content is an unexplained
hyphen/underscore difference. The sentence exists to explain the naming divergence, and after the
rename the divergence it must explain is a **different** one. Verified live:

| Convention | Value | Source |
|---|---|---|
| PyPI distribution | `model-project-constructor` (hyphens) | `pyproject.toml:2` |
| Import package | `model_project_constructor` (underscores) | `src/model_project_constructor/` |
| Repository (after) | `model_project_constructor` (underscores) | this plan |

Post-rename the repository and the import package agree, and only the **PyPI distribution name**
diverges — which is not an anomaly but PEP 503 normalization. **Rewrite the sentence to say that.**
It is deliberate. **The operator corrected an initial hyphenated reading
(`model-project-constructor`) to `model_project_constructor` within the same session (Session 221,
2026-08-17).** Do not "fix" the hyphens. *(Session 234: that ruling was recorded in `BACKLOG.md`'s
*"The name form is underscores, and it is deliberate"* paragraph, inside the rename item Phase 5
deletes. It is quoted here so the ruling outlives its filing location. The only other surviving copy
is in a frozen shard — `grep -n "name form is underscores" docs/architecture-history/SESSION_NOTES-*.md`
finds it in `SESSION_NOTES-S227-through-S225.md`. A first draft of this note cited `CHANGELOG.md`
too; `CHANGELOG.md` does not contain it, and the pre-commit review caught the fabrication — which is
the same defect this note exists to repair, committed while repairing it.)*

### Dragon 7 — The string is overloaded: three hits mean the *generated output*, not this repository

```
docs/wiki/…/Development-Workflow.md:3        "…in a generated claims-model-starter repository."
docs/wiki/…/Software-Bill-of-Materials.md:3  "…the generated claims-model-starter projects (the output)."
docs/wiki/…/Software-Bill-of-Materials.md:113 "The generated claims-model-starter repository has its own…"
```

These use the repo name as a generic label for **the projects this tool produces**, not for this
repository. A blind replace renames a concept it has no business renaming. And the label is
*already* wrong: `src/model_project_constructor/agents/website/` derives generated project names at
runtime via `derive_project_name` / `derive_project_slug` from the intake session id — **`src/` and
`packages/` contain zero occurrences of `claims-model-starter`.** Nothing this tool generates has
ever been called that. **Rewrite these three to say "generated model project" (or the project's own
term); do not substitute the new repo name.**

### Dragon 8 — One hit lives in a file that must not be edited

`SESSION_RUNNER.md:209` names `docs/wiki/claims-model-starter/` in the "Wiki sync" paragraph. That
file is synced from the canonical methodology repo and `CLAUDE.md` forbids local edits — they block
future syncs. **If D-R2 is "yes", that line goes stale and the correction belongs in `CLAUDE.md` →
Project-Specific Methodology Adaptations**, which exists as the customization seam for exactly this.
`CLAUDE.md` already carries a precedent for this pattern (the third-party attribution note under the
same heading). **Do not edit `SESSION_RUNNER.md`.**

### Dragon 9 — Out-of-repo surfaces a `git grep` completion criterion can never see

- `~/Development/claims-model-starter.wiki` — the live publish target. Its **directory name** and its
  **origin URL** both carry the old name, and `publish_wiki.sh:42` defaults `WIKI_CLONE` to that
  exact path. `enterprise-migration.md:1449` (dragon #21 there — `:1436` is inside dragon #20; re-derive with
  `grep -n "^21\. " docs/planning/enterprise-migration.md`) warns that this clone must not be
  repurposed for the enterprise fork; that warning survives the rename unchanged.
- The methodology dashboard scans `~/Development` and lists that clone as a project named
  `claims-model-starter.wiki` (health 16/100). Renaming the directory changes what the dashboard
  reports and orphans its history rows in `~/Development/dashboard_history.jsonl`.
- This repository's own `origin` (`https://github.com/rmsharp/claims-model-starter.git`) — GitHub
  redirects it, so nothing breaks, but leaving it stale means `git remote -v` lies to every future
  session. ~~**Note `master` is currently 2 commits ahead of `origin/master`** (`2033e95`,
  `59615e2`). Push before Phase 1 or know that the first post-rename push travels the redirect.~~
  **Struck by Phase 5 (Session 234), which §9.1 assigned this line to.** Plan-time truth, moot since
  Phase 1 landed; the origin was re-pointed and every phase has pushed cleanly under the new name.
  **Do not re-pin the number** — an ahead-count is stale one commit after it is written, which is
  the whole reason this line needed striking rather than updating.
- **A third clone exists and nobody has mentioned it:**
  `~/Development/mpc_tests/model_project_constructor`, `origin` =
  `https://github.com/rmsharp/claims-model-starter.git`. It keeps working via the redirect; it is
  listed here so the rename does not "complete" with a stale clone nobody remembered.
  **DISCHARGED by Phase 5 (Session 234)** — `git remote set-url` on that clone, out of repo and in no
  commit; the new URL was proved to resolve with `git ls-remote`, not merely written. This bullet is
  why it was found: Session 233 checked §7.4 and left it deliberately rather than bundling it into
  Phase 4. **All three clones are now on the new name.**
- ~~**`.git/config` in all three clones** carries the old URL~~ — **false since Phase 5; all three
  now carry the new URL** (the bullet above records the last one). The *mechanism* claim below stands
  and is why they had to be checked by hand: `.git/config` is invisible to the sweep — both
  `git grep` (tracked files only) and the filed criterion's `grep -rIl … --exclude-dir=.git`
  structurally exclude it. Only `git remote -v` finds it.
- **The local-only branch `gh-pages-preA4`** holds an older copy of generated site output carrying
  the old name. It is a frozen rollback artifact — **keep it as-is**; it is history, and it is
  invisible to any `HEAD`-scoped grep anyway.
- **Rendered artifacts of the stakeholder dossier.** `executive-summaries/stakeholder-readiness-dossier.qmd`
  is tracked and carries 2 hits; its rendered `.html` and `.pdf` siblings are **gitignored**
  (`.gitignore:24-25`, confirmed with `git check-ignore -v`), so no `git grep` will ever see them.
  The `.html` still contains the old path on 2 lines; I could not confirm one way or the other for
  the `.pdf` (its text streams are font-subset glyph runs — a naive search finds nothing, which is
  not the same as absence). **Editing the `.qmd` does not re-render either one.** If the dossier is
  ever handed to a stakeholder again, re-render it; otherwise it quietly ships the old path.
- **`~/Development/methodology` (third-party, not this project's to edit) references
  `claims-model-starter.wiki` on 7 lines** — 5 archived history, and 2 in
  `tools/test_methodology_trim.py` (`:1480`, `:1723`) that name the wiki clone's local path in test
  docstrings. Renaming the clone directory makes those two stale. **Out of scope** — flag it to the
  operator rather than editing another project's repository.

### Dragon 10 — `curl → 200` cannot detect a broken deploy, because the site is **already** broken

The obvious acceptance criterion for Phases 1 and 2 is *"the tutorial returns 200."* It is nearly
worthless here. Verified live, **today, before any rename**:

```
curl -o /dev/null -w '%{http_code}' https://rmsharp.github.io/claims-model-starter/tutorial/        -> 200
curl -o /dev/null -w '%{http_code}' https://rmsharp.github.io/claims-model-starter/assets/stylesheets/main.css -> 404
```

`origin/gh-pages` holds **7 files total** — `.nojekyll`, `404.html`, `index.html`,
`search/search_index.json`, `sitemap.xml`, `sitemap.xml.gz`, `tutorial/index.html` — and **no
`assets/` tree at all**, while `tutorial/index.html` links
`../assets/stylesheets/main.484c7ddc.min.css` and `../assets/javascripts/bundle.79ae519e.min.js`.
**The published tutorial has been serving unstyled for some time.**

**This is a pre-existing defect, discovered while planning the rename and deliberately not fixed by
it** (§8). It matters to this plan in two ways: the acceptance criteria must check an asset rather
than the page (done, in Phases 1/2 and §7.3), and **the executor must not read the 404 as damage the
rename caused.** Record the pre-rename measurement before Phase 1 so the comparison is honest.

### Dragon 11 — The most important line in the sweep is invisible to the obvious grep

```python
tests/test_wiki_no_line_citations.py:38
WIKI_DIR = REPO_ROOT / "docs" / "wiki" / "claims-model-starter"
```

The path is **assembled from parts**. `grep "docs/wiki/claims-model-starter"` over that file returns
**only line 7** (the docstring); line 38 — the constant that `:60`'s `WIKI_DIR.is_dir()` assertion
depends on, and therefore the single line whose omission turns the suite red — **does not match.**

An executor who drives the Phase 4 sweep from the 516-hit path pattern will miss it, `git mv` the
directory, and break the test suite. **Drive every sweep from the bare `claims-model-starter`
pattern**, never from the joined path. Assume this is not the only place the name is split; the
allowlist check in §7.2 uses the bare pattern precisely so that split occurrences cannot hide.

### Dragon 12 — Never create a new repository called `claims-model-starter`

GitHub Docs, *Renaming a repository*: *"If you create a new repository under your account in the
future, do not reuse the original name of the renamed repository. If you do, redirects to the
renamed repository will no longer work."* Recorded because "let's park a redirect stub at the old
name" is the obvious idea for saving the Pages URL, and it would silently destroy the repo, git, and
wiki redirects to buy it. See §1.1 option C.

---

## §7 Completion criteria for the whole rename

### §7.1 Why this is an allowlist and not a number

A hit count is the wrong criterion here. **Every document that discusses the rename adds hits** —
the ruling commit added 4, this session's Phase 1B stub added 1, and **this plan file adds ~98 more.**
A criterion of the form "`grep -c` returns N" was already unsatisfiable before execution started
(§2.2).

**And note where those ~98 live: `docs/planning/`, which every classification rule in §3 treats as
the LIVE bucket.** By the plan's own rule this document is the single largest block of MUST_CHANGE
lines in the repository. It is not one. Its hits are self-referential literals of exactly the
`BACKLOG.md` class — *"`publish_wiki.sh:72` greps for the literal `claims-model-starter.wiki`"* —
that must survive **verbatim** or the plan stops describing the thing it is planning. Phase 5's
"classify every surviving hit" walks straight into this, so it is settled here: **the planning
artifact is exempt, permanently, and it is in allowlist group 2 below.**

Use the file allowlist: it is stable under the plan's own prose.

### §7.2 The allowlist check

Every surviving occurrence of `claims-model-starter` must sit in a file that is a **frozen
historical record** (§3.1), a **document whose subject is the old name**, or a **live file pinned by
D-R5** (§3.3). This command must print nothing:

```bash
git grep -l "claims-model-starter" -- . \
  | grep -v -E '^(docs/architecture-history/|audits/|CHANGELOG\.md$|PROJECT_LEARNINGS\.md$|prs-export\.json$|releases-export\.json$)' \
  | grep -v -E '^docs/wiki/[^/]+/Changelog\.md$' \
  | grep -v -E '^(BACKLOG\.md|SESSION_NOTES\.md|SESSION_RUNNER\.md|CLAUDE\.md|docs/planning/repository-rename\.md)$' \
  | grep -v -E '^(scripts/publish_wiki\.sh|docs/planning/enterprise-migration\.md)$'
```

**And these two commands are not optional — they are the other half of the same criterion.** They
are what the exemption above is traded for; run them, or the exemption is a blindfold:

```bash
# (i) publish_wiki.sh keeps exactly its three D-R5 lines -- no more, and never zero.
grep -n "claims-model-starter" scripts/publish_wiki.sh
#   -> EXACTLY 3 lines: :19, :24, :42.  Not 0 (a sweep broke publishing); after Phase 4, not 10
#      (the phase's edit did not land).

# (ii) enterprise-migration.md keeps ONLY D-R5 lines and the four independence-grep sites.
grep -n "claims-model-starter" docs/planning/enterprise-migration.md \
  | grep -v 'Development/claims-model-starter\.wiki' \
  | grep -v 'claims-model-starter\.wiki` (rename plan D-R5)' \
  | grep -vE "iE 'rmsharp|narrower pattern|survives in the clone"
#   -> empty after Phase 5.  Measured 2026-08-20 it prints 20: 16 `docs/wiki/` path lines Phase 4
#      owns, plus the four residue lines (:345 in Phase 4's commit, :919/:1250/:1372 in Phase 5).
#      16 and not 17, because one of the 17 also carries the D-R5 clone path and the first
#      `grep -v` removes it -- that is the dual-purpose line §3.3 warns about.
#      The `grep -v`s are §3.3 plus the independence sites flagged to the operator and NOT this
#      plan's to rewrite (§8). They match on CONTENT: those line numbers move every session.

# (iii) THE DUAL-PURPOSE LINE. Neither of the two commands above can see it, and that is not an
#       oversight you may skip -- (ii)'s first `grep -v` removes it by construction, and command 1
#       exempts the whole file. It needs its own assertion:
grep -n "diff -r -x '.git'" docs/planning/enterprise-migration.md
#   -> exactly ONE line. After Phase 4 it must read
#        diff -r -x '.git' docs/wiki/model_project_constructor ~/Development/claims-model-starter.wiki
#      NEW name on the left (the in-repo directory Phase 4 renames), OLD name on the right (the
#      clone D-R5 pins). Both wrong ways fail silently: leave the left half stale and that plan's
#      C-phase parity check `diff`s a directory Phase 4 deleted; `sed` both halves and the line
#      stops naming the clone at all. §3.3 trap 1 is this line.
```

- **Group 1** (lines 2-3) is §3.1's frozen historical records — the 28 files that keep the old name
  by the `bfd9f36` precedent. The wiki `Changelog.md` gets its own line with `[^/]+` because **its
  directory name changes in Phase 4 while its content does not**; pinning the old path would make the
  check pass for the wrong reason afterwards.
- **Group 2** (line 4) is the five files whose remaining hits exist *in order to* name the old name:
  the backlog item's history, the session ledger, the synced file that cannot be edited (dragon 8),
  the `CLAUDE.md` seam note that records why it cannot be edited, and this plan.
- **Group 3** (line 5) is **§3.3** — the two files that are different in kind from both groups
  above. `scripts/publish_wiki.sh` is **live executable code** and
  `docs/planning/enterprise-migration.md` is a **live plan**; neither is a record, neither is about
  the rename, and both keep old-name lines **forever** because D-R5 pins a filesystem path they
  name. Exempting a live file from a completion check is exactly the move that turns an allowlist
  into a blindfold — **which is why this exemption is void without the two paired commands above.**
  Allowlisting them alone would make §7.2 unable to see a genuine future miss inside either, which
  is what the "no judgment call" rule below forbids. Run all three, or none.

**If the first command prints a path, that file was missed. If (i) prints anything other than the
10 lines before Phase 4 or exactly `:19`, `:24`, `:42` after it, `scripts/publish_wiki.sh` is broken
— and `0` is broken at every point in the plan's life. If (ii) prints anything after Phase 5, a
rename line was missed inside `enterprise-migration.md`.** No judgment call, no re-derivation.

> ⚠ **Both verdicts are phase-relative, and (i)'s especially.** Run §7.2 at the start of Phase 3 —
> as the ledger below tells you to — and (i) prints **10**, which is correct, because Phase 4 has not
> run. An earlier draft of this sentence made (i)'s verdict unconditional, which would have declared
> a healthy publisher broken at the start of every phase before Phase 4. Worse, the natural "fix" is
> to apply Phase 4's 7-line edit early — which flips the `:72`/`:75` guard literal while the clone's
> origin still carries the old name and **disables publishing** (dragon 2), breaking K2 and K3's
> same-commit rule.

> *Session 230 addition. Before it, §7.2 had no group 3, and both files were wholly on the change
> side of §3. That made **§7.2 unsatisfiable**: a correct execution leaves 17 lines standing across
> those two files, §7.2 would print both paths, and the rule immediately above rules a printed path
> a miss — with no judgment call available to excuse it. **§7.2 is Phase 5's DONE gate**, so Phase 5
> could never have gone green. The three paired commands are what keep the exemption from costing
> anything.*
>
> *`enterprise-migration.md` was the harder half, and it was nearly missed. The filed defect named
> only `publish_wiki.sh` (3 lines); the second file carries **14** in the same frame. A repair that
> fixed the named instance and stopped would have left this gate exactly as unreachable as it found
> it. If a future session finds a **third** live file pinned this way, it belongs in §3.3 and in
> group 3 — not in an ad-hoc exception.*

**This criterion was falsified before it was written down.** Run at plan time (Session 226, `HEAD` =
`59615e2`) it printed **20 paths** — every change-side file that had not yet been touched. (It is 20,
not 23: `BACKLOG.md`, `SESSION_NOTES.md` and `SESSION_RUNNER.md` are change-side but sit in allowlist
group 2, and the wiki `Changelog.md` moved to KEEP in §3.1.) **That plan-time baseline is below; the
current expected set is the ledger under it.**

```
.githooks/post-commit           docs/tutorial.md
CONTRIBUTING.md                 docs/wiki/claims-model-starter/Contributing.md
README.md                       docs/wiki/claims-model-starter/Development-Workflow.md
SECURITY.md                     docs/wiki/claims-model-starter/Evolution.md
THIRD-PARTY-LICENSES            docs/wiki/claims-model-starter/License.md
docs/methodology/PROJECT_CONVENTIONS.md
docs/planning/enterprise-migration.md
docs/planning/httpx-adapter-migration.md   docs/wiki/claims-model-starter/Software-Bill-of-Materials.md
docs/planning/opencode-adapter-spec.md     executive-summaries/stakeholder-readiness-dossier.qmd
docs/style/statistical_terms.md            mkdocs.yml
scripts/publish_wiki.sh                    tests/test_wiki_no_line_citations.py
```

It is red now and must go green. A completion criterion that has never been observed failing proves
nothing — the project has learned this the hard way twice (learnings #99, #102).

**Ledger — the expected set shrinks as phases land, and a shrinking set is NOT drift.** Every row
measured 2026-08-20 by checking out that commit and running the command.

**Read the "command" column before comparing a number.** The first three rows are the **four-group**
command as it stood before this repair; the last two are the **five-group** command printed above.
That is not sloppiness — the historical rows record what an executor standing at those commits would
actually have seen. Re-running the five-group command over the first three commits gives 18 / 15 /
13, because group 3 hides two files that were present all along.

| At | Command | Prints | What left, and why |
|---|---|---|---|
| plan time, `59615e2` | 4-group | **20** | the baseline block above |
| after Phase 1, `c1fe06f` | 4-group | **17** | `mkdocs.yml`, `README.md`, `docs/tutorial.md` — fixed |
| after Phase 2, `73b9418` | 4-group | **15** | `SECURITY.md`, `CONTRIBUTING.md` — fixed |
| after this repair | **5-group** | **13** | `scripts/publish_wiki.sh` **and** `docs/planning/enterprise-migration.md` — **exempted, not fixed**; their §3.3 lines are permanent |
| after Phases 3, 4 and 5 | 5-group | **0** | the remaining 13, all owned by a phase |

**Re-run it at the start of every phase and confirm it prints exactly the set this ledger predicts
for the last landed commit.** A path *leaving* the set is a phase doing its job. **A path
*appearing* that the ledger does not predict means the plan has drifted, and §2 must be re-derived
before anything else is touched.** Measured 2026-08-20: nothing has appeared since plan time — all
five departures are Phases 1 and 2, named above.

> *Session 230 correction. This paragraph previously read* **"Re-run it at the start of execution and
> confirm it still reports exactly these 20 paths. A different set means this plan has drifted."*
> *By then the true reading was 15 and every one of the five departures was a phase succeeding. An
> executor obeying that sentence at the start of Phase 3 would have halted the plan and re-derived §2
> because it had been working.*

### §7.3 The rest

```bash
gh repo view --json nameWithOwner                  # -> rmsharp/model_project_constructor
git remote -v                                      # -> .../model_project_constructor.git
git -C <wiki-clone> remote get-url origin          # -> .../model_project_constructor.wiki.git
curl -sf https://rmsharp.github.io/model_project_constructor/tutorial/ >/dev/null && echo OK
curl -s -o /dev/null -w '%{http_code}\n' https://rmsharp.github.io/claims-model-starter/tutorial/
#   -> 404, permanently, by design (§1). Record it; do not treat it as a defect.
uv run pytest -q                                   # -> 1230 passed + 9 live-skipped
uv run ruff check src/ tests/ packages/ scripts/   # -> clean
uv run mypy                                        # -> clean
scripts/publish_wiki.sh                            # -> "no changes to publish"
git -C ~/Development/claims-model-starter.wiki rev-list --count origin/master..master   # -> 0
#   NOT implied by the line above, and not optional (Session 234, from Session 232's defect #1).
#   `publish_wiki.sh` commits into the clone and then pushes, so a failed push exits 2
#   with the local commit LEFT IN PLACE. In that state the re-run above short-circuits at the
#   "no changes to publish" early return and
#   prints "no changes to publish" with exit 0 -- a green line that is fully consistent with a
#   STALE live wiki. Only a count against origin/master separates the two. Dragon 2 item 6.
grep -rn "claims-model-starter" scripts/ tests/ .githooks/ src/ packages/ .github/ \
  | grep -v '^scripts/publish_wiki\.sh:'                  # -> empty
grep -c "claims-model-starter" scripts/publish_wiki.sh    # -> exactly 3 — never 0, never more
```

`src/`, `packages/` and `.github/` are in that grep even though they have **zero** hits today
(§2.4) — so that a future session's addition is caught rather than assumed absent.

> ⚠ **That residue line greps *directories*, not the index, so it reaches untracked and ignored
> files and its verdict depends on which `grep` you have.** Measured in Session 234: on a shell
> where `grep` is a `ugrep --ignore-files` wrapper (which honours `.gitignore`) it prints **empty**;
> the same command as `command grep` prints **two** `tests/__pycache__/*.pyc` blobs — stale bytecode
> of the pre-Phase-4 test file, untracked and harmless. §7.2's *"no judgment call, a printed path is
> a miss"* rule would therefore fail a correct tree on a different machine. **Read it as: no
> *tracked* residue.** A criterion of this shape should be `git grep` (index-scoped, deterministic),
> which still catches the future addition §2.4 is defending against, since an addition would be
> tracked. Left as-is here rather than rewritten, because changing an instrument in the act of
> declaring it passed is exactly the move this project refuses elsewhere.

**`scripts/publish_wiki.sh` is excluded from the first line and asserted on the second, and the two
travel together** — §7.2 group 3 explains why, and §3.3's first row is the authority. Anchor the
exclusion on the **path** (`^scripts/publish_wiki\.sh:`), never on `--exclude=publish_wiki.sh`:
measured 2026-08-20, `--exclude` takes a **basename glob** and silently swallowed a probe planted at
`packages/probe/publish_wiki.sh`, while the path-anchored form caught it.

### §7.4 Three checks `git grep` at `HEAD` structurally cannot perform

The allowlist covers tracked files at `HEAD`. These three surfaces are real, reader-visible, and
invisible to it — a plan that stops at §7.2 reports green while two of them still say the old name.

```bash
# 1. The DEPLOYED site (generated; fixed by Phase 1's redeploy, not by any edit).
#    git grep CANNOT read the gzipped blob -- decompress every blob or this check is fail-open (§2.5).
git fetch origin gh-pages
git ls-tree -r --name-only origin/gh-pages | while read f; do
  case "$f" in
    *.gz) n=$(git show "origin/gh-pages:$f" | gzip -dc | grep -c claims-model-starter);;
    *)    n=$(git show "origin/gh-pages:$f" | grep -c claims-model-starter);;
  esac
  [ "$n" != "0" ] && echo "STILL OLD: $f ($n)"
done                                                    # -> prints nothing
# And against the LIVE site, both sitemap forms -- the .gz is the one crawlers prefer:
curl -sL https://rmsharp.github.io/model_project_constructor/sitemap.xml    | grep -c claims-model-starter   # -> 0
curl -sL https://rmsharp.github.io/model_project_constructor/sitemap.xml.gz | gzip -dc | grep -c claims-model-starter   # -> 0

# 2. The LIVE WIKI, a separate git repository this repo's grep cannot see
git -C ~/Development/claims-model-starter.wiki fetch origin && \
  git -C ~/Development/claims-model-starter.wiki grep -n -e 'claims-model-starter' -e 'Claims Model Starter' origin/master
#   -> only the historical Changelog entry (and the titles, if D-R3 said "no")

# 3. Every clone's remote — invisible to any content grep, including the filed criterion's
#    `grep -rIl … --exclude-dir=.git`
for d in . ~/Development/claims-model-starter.wiki ~/Development/mpc_tests/model_project_constructor; do
  echo "$d -> $(git -C "$d" remote get-url origin 2>/dev/null)"
done
```

**Do not use the criterion that was filed in `BACKLOG.md`'s "Completion criteria" list** — deleted
with the rename item in Phase 5, and reproduced here because the warning outlives it (`grep -rIl "claims-model-starter" . | grep -v
'^\./\.git/'`). It returns **58 files against 51 tracked** — the extras are `.venv/…/METADATA` (the
README embedded as `long_description`), the gitignored `site/` build, a generated `.html`, and this
plan file. It can never go green.

---

## §8 What this plan deliberately does not cover

- **The enterprise fork.** `docs/planning/enterprise-migration.md` owns it. This plan only repairs
  the five verification lines the rename breaks (dragon 1). Its remaining pre-fork gate is B2, which
  the rename neither helps nor blocks.
- **Renaming the local working directory.** `~/Development/model_project_constructor` already matches
  the target name; nothing to do.
- **Renaming the PyPI distribution.** `pyproject.toml:2` stays `model-project-constructor`. Three
  conventions, one project, on purpose (dragon 6).
- **Renaming the generated-project concept.** Dragon 7 rewrites three sentences that misuse the repo
  name as an output label; it does not introduce a new name for the output.
- **A redirect for the dead Pages URL.** §1.1 evaluates and rejects the only mechanism that exists.

### §8.1 Found while planning, deliberately NOT fixed here — file these as backlog items

Each is real, verified, and outside a rename's scope. Fixing them inside this plan would be the
scope creep `SAFEGUARDS.md` exists to prevent.

1. **The published tutorial site is unstyled** (dragon 10). `origin/gh-pages` has no `assets/` tree
   and the stylesheet the page links returns 404 live. Pre-dates the rename; needs its own
   diagnosis of why `mkdocs gh-deploy` stopped emitting assets.
2. **`publish_wiki.sh` can wipe and push the live wiki from an empty source directory** (dragon 3).
   A one-line page-count assertion before `rsync` would close it.
3. **`.githooks/post-commit` fails open** — both on a stale path prefix and on any merge commit
   (dragon 4). It should announce that it decided not to publish, rather than exiting 0 in silence.
4. **`docs/planning/httpx-adapter-migration.md` is fully executed but still sits in
   `docs/planning/`**, against `PROJECT_CONVENTIONS.md` §3's archive convention. Its 2 old-name hits
   would become historical the moment it is archived — which would shrink this rename's scope by one
   file. Worth doing *before* execution if it is cheap.

---

## §9 Provenance

Every number in §2 and §3 was derived in Session 226 by running the commands shown, at `HEAD` =
`59615e2`. **Session 230 re-reconciled the §3 split without re-measuring anything**: 17 lines — 3 in
`scripts/publish_wiki.sh`, 14 in `docs/planning/enterprise-migration.md` — moved CHANGE → a new
permanent-KEEP bucket, **§3.3**. The arithmetic now reads **552 + 17 + 97 = 666, across 28 + 2 + 23 =
53 file-slots for 51 distinct files**; those two files sit on both sides. The 666/51 totals are
unchanged and still derive from `59615e2` — only the classification moved. The claim in §1 is
sourced to two GitHub documentation pages, quoted inline. The mechanism claims in dragon 2 were
verified against `man githooks` and against the real historical rename commit `35ccbd9` in this
repository's own history — not reasoned about. Where something could not be verified before
execution (whether Pages re-points to the new URL without a redeploy), the plan says so and gives the
command that settles it, rather than guessing.

**As of the end of Session 226, nothing in this plan had been executed** — `git status` then showed
only this file and the session ledger. **That is provenance, not current status.** Phases 1 and 2
have since landed (`c1fe06f`, `73b9418`); the status line at the top of this file is the authority,
and §9.1 below records the one session that changed this document without executing any phase of it.

---

### §9.1 Repair log — Session 230, 2026-08-20

**No phase ran in this session.** Session 229 executed Phase 2 and, while walking §7's completion
criteria backwards against the phase list, found two defects in *this document*. The operator ruled
(2026-08-20) that the repair get its own session rather than widen Phase 2 past its three-file table.

**No measurement in §2 changed, and no dragon's *finding* changed** — every number here is a
re-classification of lines already counted at `59615e2`, or a fresh measurement run against the
working tree at `be3bc4a`. **§4 is edited in two places** (D-R5's knob list and the recorded
operator-answer table's D-R5 row) — the *decision* is untouched; what changed is that D-R5 now names
all three `publish_wiki.sh` filesystem-path lines instead of one, because the rest of the repair
cites D-R5 as the authority for all three.

**The largest change is one the filed defects did not ask for: §3.3 is new.** The filed defect #3
named `scripts/publish_wiki.sh` (3 permanent lines). Repairing only that left §7.2 — Phase 5's DONE
gate — **still unsatisfiable**, because `docs/planning/enterprise-migration.md` carries **14** more
lines pinned by the same decision, and no allowlist group exempted it either. That was found by an
adversarial review of this repair, not by the filing. The general fix is a classification bucket
(§3.3) rather than a second one-file exception, so a third such file has somewhere to go.

| # | Where | What it said | What it says now |
|---|---|---|---|
| **1** | **Phase 4 step 2** | *"`scripts/publish_wiki.sh` — all 10 lines"* | **CHANGE 7, KEEP 3.** `:19`, `:24`, `:42` are the clone's **filesystem path**, pinned by D-R5. **An executor who obeyed the old line disabled wiki publishing**, because `:42` without the `mv` hard-fails the script at its `:58` guard — **D-R5 says so itself**, and this is the phase the plan calls its riskiest. The old `:23-24` range citation is what hid the boundary. |
| **2** | **Phase 4 verification; §7.3** | `grep -rn "claims-model-starter" scripts/ … # -> empty` | Split in two: the sweep grep now excludes `^scripts/publish_wiki\.sh:` **and** a paired `grep -n` asserts exactly 3 surviving lines. `-> empty` could not hold once the 3 lines legitimately survive. |
| **3** | **§7.2 allowlist** | four exclusion groups, none exempting `publish_wiki.sh` | a fifth line (**group 3**) exempts it, **paired with the 3-line assertion**. §7.2 is Phase 5's DONE gate and was **unsatisfiable**: a correct Phase 4 makes it print a path, and its own rule says a printed path is a miss, "no judgment call". |
| **4** | **§3.1, §3.2, §3.3 (new), §9** | 552 + 114 = 666, 28 + 23 = 51 | **552 + 17 + 97 = 666**, 28 + 2 + 23 = **53 slots for 51 distinct files** — `publish_wiki.sh` and `enterprise-migration.md` are on both sides. §3.1 keeps its original 552/28; the 17 D-R5-pinned lines went to the new **§3.3** rather than being forced into the historical-record bucket, whose rationale (`bfd9f36`) does not cover them. The 552 in **Phase 1's "if it has to be undone" note** is deliberately *not* reconciled, and now says why. |
| **5** | **Dragon 1** | *"Fix all five in the same commit as `mkdocs.yml`"* | *"Fix all five in Phase 2"* — done in `73b9418`. `mkdocs.yml` is Phase 1's file; Phase 1 disclaimed those five and closed without them. **Dragon 1 itself is untouched: its fail-open finding is correct.** |
| **6** | **Status line; §9** | *"PLAN. Nothing in this document has been executed."* | the executed-phase ledger. False since `c1fe06f`. Phase 5 still owns the final flip. |
| **7** | **§3.3 (new); §7.2's rubric, group 3 and ledger** | defect #3's repair covered `publish_wiki.sh` only | **the same defect existed for `docs/planning/enterprise-migration.md` at ~5× the scale** and would have left Phase 5's gate unreachable. §7.2's exemption now covers both, **§7.2's** opening two-category rubric became three, and the ledger's terminal row is 0 out of **13**, not 14. |
| **8** | **Phase 5's residue rule** | *"Anything that is neither a §3.1 historical record nor deliberate self-reference is a miss — fix it here"* | *"…nor a **§3.3** D-R5-pinned line…"*. **This was the second fail-dangerous instruction in the plan** and it is defect A's twin: obeyed literally it orders an executor to rewrite all 17 pinned lines to a directory that does not exist. Found by the same adversarial review. |

**Repaired beyond the six filed.** Each is a consequence of one of the six, or a statement in a
passage the six sent me into that had since been measured false. All are listed here so the next
reader can reverse any of them cheaply.

- **§7.2's expected-output paragraph** (a consequence of #3). It read *"Re-run it at the start of
  execution and confirm it still reports exactly these 20 paths. A different set means this plan has
  drifted."* The true reading was already **15**, and all five departures were Phases 1 and 2
  **succeeding** — an executor obeying that sentence at the start of Phase 3 would have halted a
  working plan and re-derived §2 because it had been working. Repair #3 takes it to 14 and would have
  made the sentence wronger still. It is now a per-phase ledger, and the drift trigger is a path
  **appearing**, not the count changing. *(Also in that block: "Group 2 (line 3)" was an off-by-one —
  group 2 is the pipeline's **line 4**.)*
- **Three stale statements inside dragon 1**, which repair #5 sends the reader into:
  1. **Its citations into `enterprise-migration.md` had drifted.** The clone-independence criterion
     is at `:363`, **`:1319`** and **`:1363`** (was cited as `:1308`, `:1351`), and its warning
     comment at **`:1361-1362`** (was `:1349-1350`). Session 229's own Phase 2 edits moved that
     file, and **the offset is cumulative and not uniform** — measured across `73b9418^..73b9418`:
     **+8** through the 800s, **+11** by `:1319`, **+12** by `:1365`, **+13** by `:1447`, **+21** at
     the sitemap check (`:1520`→`:1541`). Any single "the file moved by N" figure is wrong somewhere,
     which is the whole reason a copied line number goes stale. Corrected, and re-derivable with
     `grep -n "a narrower pattern can pass" docs/planning/enterprise-migration.md`. **§7.4's
     pointer at the filed criterion had drifted the same way** (`BACKLOG.md:617`), as had §2.3's
     pattern-6 row (`:527`). Both now name the section instead of a line, for the reason in the
     bullet below. The four/five
     `curl` line numbers quoted higher in the dragon are the **pre-repair** positions and are left
     as the record of what was found. Today: `:831`→**`:834`**, `:832`→**`:835`**, `:833`→**`:839`**,
     `:1520`→**`:1541`**, `:1356`→**`:1368`** — and `:833` is now the **positive control** Session
     229 inserted ahead of the two 404 assertions, because a retired site 404s every path.
  2. **Phase 2's `-fL` advice does not work**, measured in Session 229: a pipeline reports its
     **last** command's status, so `-f` on a piped `curl` is invisible and the vacuous pass survives
     its own prescription. Phase 2's table still carries the original wording because that phase is
     closed and its table is now a record; the correction is attached to dragon 1, where a reader
     consulting the fail-open finding will actually meet it.
  3. **The dragon's own "recommended repair" is unsatisfiable**, and nobody had measured it: scoping
     the bare-name grep to `scripts/`, `.githooks/`, `mkdocs.yml` and `tests/` returns **336 lines
     across 74 files** (286 of them the import package's own `from model_project_constructor`
     imports). That is the identical objection the dragon raises against the fifth-alternative fix.
     The measurement and the path set that *does* work are now in the dragon, and the restatement it
     implies is flagged to the operator rather than made here.
- **This document's own line-number self-citations were removed rather than updated.** Two draft
  sentences cited `:411` (D-R5's hard-fail line) and `:538` (Phase 1's rollback note) by number.
  Both are now cited by **section name**, because both numbers moved **twice** inside this one
  session as the repair grew — the second time after the replacement text had already been written,
  which is how the first version of this very bullet shipped two wrong "now" values. Session 229's
  handoff evaluation named the pattern: numbers carrying an *assertion* stay right; numbers that are
  merely *navigational* drift. **Inside this file, prefer a section name or a `grep -n` to a line
  number** — it grew by over 300 lines in this session, so every pre-existing self-citation is off
  by at least that much.
- **Two more drifted citations into other files**, same class as dragon 1's: dragon 9 sent the
  reader to `enterprise-migration.md:1436` for dragon #21 there, which is inside **dragon #20**
  (#21 is `:1449`); and dragon 6 cited `BACKLOG.md:508-513` for the operator's underscore ruling.
  Dragon 9's is corrected with a `grep -n` beside it. **Dragon 6's and §7.4's now carry NO line
  number at all**, and the reason is worth recording: the first fix re-pinned them to fresh
  `BACKLOG.md` numbers measured at `HEAD` — and this same session's `BACKLOG.md` edit then shifted
  both by 28 lines, so the "corrected" citations were stale in the commit that shipped them. **A
  line number into a file the current session is also editing is stale before it is written.** Both
  are now quoted section names, which `grep` finds and no edit moves.
- **Phase 4's rename criterion was wrong three ways, and it took two passes to get right.** It read
  `git diff --stat HEAD~1 -M   # -> the 25 pages show as pure renames (R100)`.
  1. **Phase 4's own step 2 contradicts it** — that step edits one path line in each of
     `Evolution.md`, `License.md` and `Contributing.md` in the same commit, so 3 of the 25 cannot be
     pure renames.
  2. **`git diff --stat` never prints a similarity code at all.** Measured 2026-08-20 in a scratch
     repo reproducing Phase 4's exact shape: `git diff --stat -M | grep -c R100` → **0**; `--stat`
     renders a rename as `docs/wiki/{claims-model-starter => model_project_constructor}/Foo.md | 0`.
     The command is now `git diff --name-status -M`, which prints **22 R100 + 3 R09x**.
  3. **The obvious repair was also wrong**, and the first draft of this bullet shipped it: *"none of
     the 25 may appear as delete+add, which is what a missing `git mv` looks like."* Measured — `-M`
     detects renames from **content similarity**, so a hand-rolled delete+add of identical files
     reports **25 R100** with no `git mv` anywhere. The criterion can witness that the pages moved
     intact; it cannot witness which command moved them, and it now says so.

- **The §7.2 exemption needed a THIRD assertion, not two.** Group 3 exempts
  `enterprise-migration.md` wholesale, and assertion (ii)'s first `grep -v` removes the dual-purpose
  `diff -r` line **by construction** — so between them, no §7 command could see the one line §3.3
  itself calls a trap. Phase 5's new "leave every §3.3 line alone" made it worse by telling the
  executor not to touch it. Assertion **(iii)** now pins that line specifically, §3.3's "correct
  forever" is qualified to "16 of the 17", and Phase 5's clause carries the exception. **An exemption
  is only as good as the assertion traded for it, and a filter written to make the arithmetic work
  can silently remove the case you most needed to check.**
- **`enterprise-migration.md:345` was owned by no phase.** §7.2 (ii)'s comment assigned it to Phase
  4's commit — correctly, since that commit rewrites the `publish_wiki.sh:72`/`:75` guard the line
  describes — but Phase 4's own step 2 scoped that file to "the 17 path lines" and told the executor
  *"do not re-touch"* its other lines as already handled in Phase 2, which was false for `:345`.
  Phase 4's bullet now names it explicitly.
- **Phase 5's DONE gate went green while `publish_wiki.sh` was healthy but "broken".** A draft of
  §7.2's verdict made assertion (i) unconditional, so running the mandatory block at the start of
  Phase 3 — as the ledger instructs — would have failed a correct file that legitimately still has
  all 10 lines. Both verdicts are now phase-relative, and the warning names the dangerous "fix"
  (applying Phase 4's edit early, which disables publishing).

**Found and deliberately NOT fixed** — outside this repair, filed so they are not re-discovered:

- **Dragon 9** says *"`master` is currently 2 commits ahead of `origin/master` (`2033e95`,
  `59615e2`). Push before Phase 1"*. Plan-time truth; it was **7 ahead at `be3bc4a`** and Phase 1
  has long since run, unpushed. The instruction is moot rather than dangerous, and the count moves
  every commit — do not re-pin it without an anchor. Phase 5's reconciliation owns it.
  **DISCHARGED, Session 234 (Phase 5):** the sentence is struck in dragon 9 with the reason, and
  deliberately not re-pinned. See §9.2 row 5.
- **The three independence-pattern greps in `enterprise-migration.md`** (`:363`, `:1319`, `:1363`).
  Dragon 1 forbids rewriting another plan's criteria, and the repair needs an operator ruling on
  restating the criterion as *"no name other than the clone's own"*. The flag is in `BACKLOG.md`.
  *(Session 234: re-filed there as a standalone item when Phase 5 deleted the rename item. Still
  open — see §9.2.)*
- **`enterprise-migration.md:1372`'s `--json isPrivate,archived`** — `archived` is not a `gh repo
  view` field (`isArchived` is), so that C5 criterion has never been able to pass. Pre-dates the
  rename. One word, outside the five lines dragon 1 authorises.
  **DISCHARGED, Session 234 (Phase 5):** Phase 5 had to rewrite that line for the rename anyway, so
  the one word went with it. See §9.2 row 2.

---

### §9.2 Reconciliation log — Session 234, Phase 5, 2026-08-20

**The last phase. One commit.** Phase 5's charter is to walk the whole surviving `git grep`, classify
every hit against §3, fix what is a miss, close the backlog item, and flip the status line above.
All of that happened; what follows is what it *found*, because a reconciliation that only reports
"green" is not worth reading.

**Pre-flight matched the ledger exactly.** §7.2 command 1 printed **0** (already there a phase early
— all 11 remaining paths were Phase 4's, which §7.2's ledger predicts as "after Phases 3, 4 and 5";
arriving early is a phase working, not drift). (i) printed exactly `:19 :24 :42`; (ii) printed the
three residue lines this phase owns; (iii) printed one line, new name left, old name right.

| # | Where | What it said | What it says now |
|---|---|---|---|
| **1** | `enterprise-migration.md:919`, `:1250`, `:1372` | three surviving `claims-model-starter` lines — §7.2 (ii)'s whole remaining content | rewritten to the new name. **(ii) is now empty**, which is what Phase 5's DONE gate asks for. `:919` and `:1250` are re-runnable commands (`:919`'s own phase text ships them *"so the reviewer can re-run them"*; `:1250` is an unexecuted C4 instruction and **two lines below it that mirror is pushed** with `--mirror`). `:1372` is an unexecuted C5 acceptance criterion. None is a record. |
| **2** | `enterprise-migration.md:1372` (same line) | `--json isPrivate,archived` | `--json isPrivate,isArchived`. **§9.1 filed it as *"one word, outside the five lines dragon 1 authorises"*; the instruction to *"fix the field name whenever that line is next touched"* was `BACKLOG.md`'s Session-229 flag 3 — which this commit deletes.** Phase 5 touched the line, so the fix is discharged rather than lost with the rows that carried the instruction. |
| **3** | §3.2(c)'s `Evolution.md:266` parenthetical | *"also says '22 outward-facing wiki pages'; there are 25"* | *"also said '22 outward-facing wiki pages **plus the sidebar**'; there are **24** (25 files, one of which is `_Sidebar.md`)"*. Session 232's filed defect #2, **now fully discharged** — Session 233 fixed the live page; this fixes the plan. |
| **4** | Phase 3's and Phase 4's verification blocks; dragon 2 | every command reads **local** state, and `BEFORE != AFTER` positively prints `HOOK FIRED AND PUBLISHED` in the one state that matters | Session 232's filed defect #1, **discharged**. `publish_wiki.sh` commits into the clone (`:102`) *then* pushes (`:104`), so a failed push exits **2 with the local commit left in place** — after which the clone's `HEAD` has moved, a re-run short-circuits at `:96` and exits 0, and a local-vs-local `diff -r` is identical, all while the live wiki is stale. **Both blocks are left byte-identical** (those phases have run; the blocks are records now — the disposition §9.1 gave Phase 2's `-fL` advice) and a correction plus a runnable *push-reachability* block is **appended** to each. Dragon 2 gains **item 6** and a qualification of its *"loud, safe, and recoverable"* conclusion, and **§7.3** — which is live, not a record — gains the `rev-list --count origin/master..master` assertion. `grep -cin 'push fail'` over this document returned **0** before this repair. |
| **5** | dragon 9's *"`master` is currently 2 commits ahead… push before Phase 1"* | plan-time truth, moot since `c1fe06f` | struck through with the reason. §9.1 assigned this line to *"Phase 5's reconciliation"*. **Not re-pinned**: an ahead-count is stale one commit after it is written. |
| **6** | six pointers into `BACKLOG.md` | *"flagged to the operator in `BACKLOG.md`"* (Phase 5's §3.3 box), dragon 1's *"filed… under the rename item"*, §9.1's *"The flag is in `BACKLOG.md`"*, dragon 6's citation of the *"name form is underscores"* paragraph, §7.4's *"the criterion filed in `BACKLOG.md`'s 'Completion criteria' list"* | all six re-pointed, inlined or annotated. **Deleting the backlog item silently dangles every pointer into it**, and three of these route the reader to an *open operator decision*. Dragon 6's case is the sharpest: the operator's underscore ruling existed nowhere else in this plan, so it is now **quoted inline** rather than cited. **The sixth — §2.3's pattern-6 row, whose `grep` now returns nothing — was missed by the first pass and found by the pre-commit review, because that pass worked from a list of known pointers instead of `git grep`-ing for them. That is learning #137's own failure mode, committed while writing learning #137.** |
| **7** | `README.md:7` | Phase 5 owes it a "calm second look" (dragon 6) — it was rewritten in Phase 1 with the site down | **verified, not re-read.** Every claim checked against the live repository: repo name (`gh repo view`), `src/` tree, import package, **both** `[project]` names (`pyproject.toml:2`, `packages/data-agent/pyproject.toml:2` — exactly two distributions exist, no third), and `README.md:9`'s URL (**200, zero redirects**). **No edit.** The sentence is in fact more complete than dragon 6's own table, which names one distribution. |

**Found, measured, and deliberately NOT fixed here — filed in `BACKLOG.md` instead.** This is the
finding worth carrying forward, and it is a defect in **this plan's classification**, not residue.

**Every archived document's banner points at a directory Phase 4 deleted.**
`docs/methodology/PROJECT_CONVENTIONS.md:44` holds the canonical archive banner. Phase 4 updated it
to `docs/wiki/model_project_constructor/Evolution.md` — and updated **none of the 21 lines across
20 files** under `docs/architecture-history/` that carry the banner text; **zero** name the new one.
**20 of the 21 are deployed banners; the 21st is `evolution-page-plan.md:161`, the banner's
*original specification*** inside a fenced block, which `PROJECT_CONVENTIONS.md:44` is the live copy
of — so the spec and its copy now disagree verbatim, and Session 147's archive precedent requires
banners to be byte-identical to the template. `CHANGELOG.md`'s **preamble** (`:3` twice, `:10`)
carries the same class, above the first version heading at `:16` — **twice on each of those two
lines**, and `:10`'s second is `claims-model-starter/wiki`, the GitHub wiki path, alive only on the
rename redirect.

**§7.2 could never have seen it, and the reason generalises.** Group 1 exempts
`^docs/architecture-history/` and `^CHANGELOG\.md$` **wholesale**, on §3.1's rationale that they are
frozen records. That is true of their *entries* and false of a banner and a preamble, which record
nothing and navigate. §9.1's rubric for exactly this hazard — *"An exemption is only as good as the
assertion traded for it, and a filter written to make the arithmetic work can silently remove the
case you most needed to check"* — is right, and §7.2 says the same in its own words (*"run them, or
the exemption is a blindfold"*). The assertion traded for group 1 was a **file-level** one, so the
blindfold reappears **one level down**, inside an exempt file. §7.2's group 3 anticipated exactly this shape for live
files and paired the exemption with three line-level assertions. Group 1 got none.

**Why it was filed rather than swept.** Classified against §3 — which is what Phase 5 is told to do —
these hits land in **§3.1**, so by the letter of the residue rule they are not misses. The claim is
that §3.1's *classification* is wrong for this one sentence. That is a plan defect, and this
project's settled answer to a plan defect found mid-execution is to file it (Session 229 → Session
230's dedicated repair session), not to widen the closing commit into a 22-file sweep of frozen
archives against `SAFEGUARDS.md`'s blast-radius rule. The fix is 23 one-line substitutions and needs
one ruling first: **is the archive banner part of the frozen record, or project-added boilerplate
that tracks its template?**

**§7.3's eleven, recorded rather than asserted.** `gh repo view` → `rmsharp/model_project_constructor`;
`git remote -v` and the wiki clone's origin both on the new name; the new tutorial **200** and the old
one **404** (§1 by design — recorded, not treated as a defect); the residue grep empty *with the
caveat below*; `publish_wiki.sh` → *"no changes to publish"*, exit 0; the new push-reachability line
→ **0**; `grep -n … publish_wiki.sh` → exactly `:19 :24 :42`. And the four that are not greps:
**`uv run pytest -q` → 1230 passed, 9 skipped; `uv run ruff check src/ tests/ packages/ scripts/` →
clean; `uv run mypy` → clean** — all three unchanged since Session 230, as this phase touches no code.

**§7.4's three out-of-repo checks, which the allowlist cannot reach — all green, all measured.**

- **The deployed site.** Every blob on `origin/gh-pages` scanned, decompressing the one `.gz`;
  **zero** old-name hits. Run with a **positive control** — the same loop against the *new* name
  reported `sitemap.xml.gz (2)`, proving the `gzip -dc` branch executed and can return non-zero, so
  the zero is a real absence and not §2.5's fail-open. Both live sitemap forms return 0.
- **The live wiki.** One hit across 25 pages: `Changelog.md:124`, the dated Session-19 entry §3.1
  predicts. **No title survives** — `Home.md:1` and `_Sidebar.md:1` both read *Model Project
  Constructor* (D-R3 = yes). A case-insensitive sweep including `claims model starter` and
  `claims_model_starter` found nothing further, so the check is not fail-open on casing.
- **Every clone's remote.** All three now on the new name. The third —
  `~/Development/mpc_tests/model_project_constructor`, which dragon 9 lists and Session 233 found
  still stale — was **re-pointed by this phase** (`git remote set-url`, out of repo, no commit) and
  the new URL was proved to resolve with `git ls-remote`, not merely written.

**Untracked and non-`HEAD` surfaces, recorded so nobody re-discovers them.** None is a defect in
this repository's tracked content; all are invisible to every check in §7.

- **The dossier's renders — and dragon 9's open question is now closed.** Dragon 9 says the rendered
  `.html` carries the old path on 2 lines and that it *"could not confirm one way or the other for
  the `.pdf`"* because a naive search of its font-subset glyph runs finds nothing. **Measured:
  `pdftotext … | grep -c` returns 2 — the PDF carries it too.** The `.qmd` source is clean (Phase 4
  swept `:57` and `:95`), so both are stale renders of correct source, and editing the `.qmd` does
  not re-render either. Both are gitignored. **Re-render before the dossier is handed to anyone
  again.**
- **The installed distribution's own metadata.**
  `.venv/…/model_project_constructor-0.3.0.dist-info/METADATA:43,:45` still carries the
  **pre-Phase-1 README sentence** dragon 6 rewrote and the **dead Pages URL**, because `long_description`
  is a snapshot taken at install. Anyone running `uv pip show` sees it. Cleared by a reinstall.
- **`origin/feat/bedrock-mantle-migration`** — a remote branch, already merged into `master`, holding
  **40 files / 607 lines** of the old name. Frozen history, so its content is right; but non-`HEAD`
  refs sit outside §7.4 as well as §7.2, and deleting a merged branch is ordinary hygiene.
- **The gitignored `site/` build** — 4 files, 24 occurrences, built 2026-04-20 and long stale. Local
  only and overwritten by the next `mkdocs build`; listed because §7.4 names it and nobody looked.
- **`~/Development/methodology`**, third-party and not this project's to edit, names the wiki clone
  in two test docstrings. D-R5 kept that directory's name, so those two are **not** stale after all.
- **Clean, and checked because nobody had:** git tags (2, no old name in either message), GitHub
  releases (live API rewritten by the rename; the frozen `releases-export.json` correctly disagrees,
  being a snapshot), open PRs (none), repo metadata, and `.github/` (zero hits of any repository
  name — vacuous today, correctly defensive).

**A tooling fail-open worth more than any of the above: §7.3's residue grep is
implementation-dependent, and this machine's `grep` hides the difference.** In the session that ran
it, `grep` is a shell function wrapping **`ugrep --ignore-files`**, which **honours `.gitignore`**.
Run verbatim, §7.3's residue line prints **empty**. Run with `command grep`, it prints **two**
`tests/__pycache__/*.pyc` blobs — stale Python-3.10 bytecode of the pre-Phase-4 test file. The
content is harmless and untracked; **the criterion is not.** It reaches untracked files because it
greps *directories* rather than the index, so its verdict depends on the grep implementation and on
build state — and §7.2's rule for a printed path is *"no judgment call"*, which would make a correct
tree read as a miss on another machine. Recorded, not silently "fixed": changing an instrument at
the moment you declare it passed is the move this project refuses elsewhere (see the `opencode`
re-measure item). §7.3 now carries the warning; a future criterion of this shape should use
`git grep` and say so.

**No `CHANGELOG.md` entry, by §5's ruling** — every touch in this phase is documentation or a path
string, and `PROJECT_CONVENTIONS.md` §2 exempts exactly that.
