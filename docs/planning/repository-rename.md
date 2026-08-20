# Plan: rename the GitHub repository `claims-model-starter` → `model_project_constructor`

**Status:** PLAN. Nothing in this document has been executed.
**Written:** Session 226, 2026-08-19.
**Deliverable of this session:** this file. **Renaming is a later session.**

> **Operator ruling, 2026-08-19 (recorded in `2033e95`):** *"set rename of repository as the next
> session ; it may take a planning session because of the blast radius of a rename."*
> **Operator, this session:** *"rename repository ; use planning session if needed."*
>
> The "if needed" is answered by evidence, not preference: the sweep is 114 lines across 23 files,
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
| 6 | `claims_model_starter` (underscored) | 1 | 1 | **`BACKLOG.md:527` only** — the row that says this form does not exist. Self-matching. Do not read it as a real occurrence. |
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

### §3.1 KEEP the old name — 552 lines across 28 files

| Group | Files | Lines | Why |
|-------|-------|-------|-----|
| `docs/architecture-history/**` | 21 | 418 | Frozen historical records. Includes `SESSION_NOTES-through-S216.md` (293 lines of the 418). **`grep` that file, never `Read` it** — it is 24,590 lines and an agent `Read` truncates at 2,000 with no marker. |
| `CHANGELOG.md` | 1 | 117 | Authoritative append-only ledger; every entry records what-was-true-then. |
| `audits/**` | 2 | 12 | `2026-06-10-wiki-vs-code-accuracy-audit.md` (10), `2026-07-28-b2-import-readiness.md` (2). Dated findings. |
| `PROJECT_LEARNINGS.md` | 1 | 2 | Learning #14's source attribution and #32's worked example. Both are records of past sessions. |
| `prs-export.json`, `releases-export.json` | 2 | 2 | Frozen GitHub API exports captured at a point in time (`enterprise-migration.md:911`). Rewriting them would falsify the snapshot. |
| `docs/wiki/…/Changelog.md` | 1 | 1 | **Its only hit, `:124`, is a dated entry** — *"Added: 14 initial wiki pages for the `claims-model-starter` project … (Session 19)."* `PROJECT_LEARNINGS.md` #32 exists because of this exact file: it is freshness-tracked yet carries permanent historical records. Its **path** moves in Phase 4 if D-R2 is yes; its **content** does not. |

**552 + 114 = 666 ✓. 28 + 23 = 51 ✓.**

### §3.2 CHANGE (or decide) — 114 lines across 23 files

**The real size of this job is 114 lines, not 666.** Ordered by what they are, not by hit count.

**(a) Executable / config — these break something if wrong (17 lines, 4 files)**

| File | Lines | What |
|------|-------|------|
| `scripts/publish_wiki.sh` | 10 | `:2`, `:11` header prose; `:19`, `:23-24` documented clone URL; `:42` `WIKI_CLONE` default; `:44` `SOURCE_DIR`; `:63` error-message clone URL; `:72`, `:75` **the remote-URL guard** |
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
*(`Evolution.md:266` also says "22 outward-facing wiki pages"; there are 25. Fix the count while
you are in the line.)*

**(d) Active plans (48 lines, 3 files)** — `docs/planning/enterprise-migration.md` (43),
`opencode-adapter-spec.md` (3), `httpx-adapter-migration.md` (2). **Mid-execution, and the 43 are
not prose — see §6 dragon 1, which is the second-most-serious finding in this document.**

**(e) Working documents whose hits are self-referential (23 lines, 2 files)** — `BACKLOG.md` (18)
and `SESSION_NOTES.md` (5). These hits exist *in order to* name the old name.
**All 5 of `SESSION_NOTES.md`'s are self-referential** (the rename handoff and this session's stub).
**17 of `BACKLOG.md`'s 18 are too** — they are the rename item, and they die by **row deletion** in
Phase 5, not by substitution. **Exactly one is a genuine substitution: `BACKLOG.md:74`**, a
`docs/wiki/claims-model-starter/` path citation inside an unrelated item, which moves with the
directory in Phase 4. **Do not run a blind `sed` over these two files.**

**Subtotals reconcile: 17 + 12 + 13 + 48 + 23 + 1 = 114 lines; 4 + 7 + 6 + 3 + 2 + 1 = 23 files.**

**(f) The file that must not be edited (1 line, 1 file)** — `SESSION_RUNNER.md:209` names
`docs/wiki/claims-model-starter/` inside the "Wiki sync" paragraph. It is **synced from the
canonical methodology repo**; `CLAUDE.md` forbids editing it, and a local edit blocks future syncs.
The prescribed seam is `CLAUDE.md` → *Project-Specific Methodology Adaptations*. See §5 Phase 4.

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
> | **D-R5** | **Re-point in place** — the clone keeps its directory name; `publish_wiki.sh:42` is not touched. | Phase 4 is `set-url` only, never `mv`. |
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

**How much actually rides on this: 51 of the 114 change-side lines, plus a `git mv` of 25 files** —
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
inside the 114). Renaming after the fork would leave the clone carrying the old name in the same
five places, and the fork is not obviously imminent — B2 is its last remaining pre-fork gate.

### D-R5 — Is `~/Development/claims-model-starter.wiki` re-pointed **in place**, or renamed on disk?

These are two independent knobs and `publish_wiki.sh` reads both:

- `:72`/`:75` guard the clone's **origin URL** — changes with the repository name.
- `:42` sets the `WIKI_CLONE` default **filesystem path** — changes only if you `mv` the directory.
  GitHub's rename does not touch it.

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
in this repository depend on the old-name redirects continuing to resolve.**

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
   - `scripts/publish_wiki.sh` — all 10 lines (`:2`, `:11`, `:19`, `:23-24`, `:42`, `:44`, `:63`,
     `:72`, `:75`)
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
     `docs/planning/enterprise-migration.md` (its URL and clone-path lines were already handled in
     Phase 2 — do not re-touch those)
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

**DONE looks like:** the suite is green, the hook fired and published on its own, the live wiki
differs from its pre-phase state by exactly the three intended lines, and no page was renamed,
added, or removed.

**Verification:**
```bash
uv run pytest -q                                    # -> 1230 passed + 9 live-skipped, unchanged
uv run ruff check src/ tests/ packages/ scripts/    # -> clean
git diff --stat HEAD~1 -M                           # -> the 25 pages show as pure renames (R100)
ls docs/wiki/model_project_constructor/ | wc -l      # -> 25
grep -rn "claims-model-starter" scripts/ tests/ .githooks/   # -> empty
```

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
that is neither a §3.1 historical record nor deliberate self-reference is a miss — fix it here.

Then:
- **`BACKLOG.md`: delete the rename item's rows; do not substitute them.** 17 of its 18 hits are the
  item itself and vanish with it. **The 18th, `BACKLOG.md:74`, is a genuine wiki-path substitution**
  inside an unrelated item and moves with the directory (it should already have been done in
  Phase 4 — verify, do not assume).
- **`README.md`** — re-read `:7` end to end. It was rewritten in **Phase 1** under time pressure with
  the site down; this is the calm second look (dragon 6).
- **This plan's own status line** — change `Status: PLAN` to executed, with the phase commit hashes.
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

**Fix all five in the same commit as `mkdocs.yml`.** They are executable acceptance criteria for
un-executed phases, not prose.

**And a sixth, subtler one — the rename reopens the exact hole that check was built to close.**
`enterprise-migration.md:363`, `:1308` and `:1351` carry the C4/C5 *clone-independence* criterion:

```bash
git grep -n -I -iE 'rmsharp|rmsharp\.github\.io|github\.com/rmsharp|claims-model-starter' -- . \
  | grep -vE '^(SESSION_NOTES|CHANGELOG|PROJECT_LEARNINGS)\.md|^docs/architecture-history/'   # -> 0
```

Its own comment at `:1349-1350` states the danger it exists to prevent: *"a narrower pattern can pass
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

**Conclusion for the `publish_wiki.sh` guard specifically: loud, safe, and recoverable.** Plan for
it; do not fear it. **The hook's own trigger is a different story — dragon 4 — and that one is
silent.**

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
It is deliberate; `BACKLOG.md:508-513` records the operator correcting a hyphenated reading within
the same session. Do not "fix" the hyphens.

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
  exact path. `enterprise-migration.md:1436` (dragon #21 there) warns that this clone must not be
  repurposed for the enterprise fork; that warning survives the rename unchanged.
- The methodology dashboard scans `~/Development` and lists that clone as a project named
  `claims-model-starter.wiki` (health 16/100). Renaming the directory changes what the dashboard
  reports and orphans its history rows in `~/Development/dashboard_history.jsonl`.
- This repository's own `origin` (`https://github.com/rmsharp/claims-model-starter.git`) — GitHub
  redirects it, so nothing breaks, but leaving it stale means `git remote -v` lies to every future
  session. **Note `master` is currently 2 commits ahead of `origin/master`** (`2033e95`, `59615e2`).
  Push before Phase 1 or know that the first post-rename push travels the redirect.
- **A third clone exists and nobody has mentioned it:**
  `~/Development/mpc_tests/model_project_constructor`, `origin` =
  `https://github.com/rmsharp/claims-model-starter.git`. It keeps working via the redirect; it is
  listed here so the rename does not "complete" with a stale clone nobody remembered.
- **`.git/config` in all three clones** carries the old URL, and is invisible to the sweep — both
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

Every surviving occurrence of `claims-model-starter` must sit in a file that is either a **frozen
historical record** or a **document whose subject is the old name**. This command must print nothing:

```bash
git grep -l "claims-model-starter" -- . \
  | grep -v -E '^(docs/architecture-history/|audits/|CHANGELOG\.md$|PROJECT_LEARNINGS\.md$|prs-export\.json$|releases-export\.json$)' \
  | grep -v -E '^docs/wiki/[^/]+/Changelog\.md$' \
  | grep -v -E '^(BACKLOG\.md|SESSION_NOTES\.md|SESSION_RUNNER\.md|CLAUDE\.md|docs/planning/repository-rename\.md)$'
```

- **Group 1** (lines 2-3) is §3.1 — the 28 files that keep the old name by the `bfd9f36` precedent.
  The wiki `Changelog.md` gets its own line with `[^/]+` because **its directory name changes in
  Phase 4 while its content does not**; pinning the old path would make the check pass for the wrong
  reason afterwards.
- **Group 2** (line 3) is the five files whose remaining hits exist *in order to* name the old name:
  the backlog item's history, the session ledger, the synced file that cannot be edited (dragon 8),
  the `CLAUDE.md` seam note that records why it cannot be edited, and this plan.

**If the command prints a path, that file was missed.** No judgment call, no re-derivation.

**This criterion was falsified before it was written down.** Run today it prints **20 paths** —
every change-side file that has not yet been touched. (It is 20, not 23: `BACKLOG.md`,
`SESSION_NOTES.md` and `SESSION_RUNNER.md` are change-side but sit in allowlist group 2, and the wiki
`Changelog.md` moved to KEEP in §3.1.)

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
nothing — the project has learned this the hard way twice (learnings #99, #102). **Re-run it at the
start of execution and confirm it still reports exactly these 20 paths.** A different set means this
plan has drifted, and §2 must be re-derived before anything else is touched.

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
grep -rn "claims-model-starter" scripts/ tests/ .githooks/ src/ packages/ .github/   # -> empty
```

`src/`, `packages/` and `.github/` are in that last grep even though they have **zero** hits today
(§2.4) — so that a future session's addition is caught rather than assumed absent.

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

**Do not use the criterion filed in `BACKLOG.md:617`** (`grep -rIl "claims-model-starter" . | grep -v
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
`59615e2`, and the arithmetic reconciles (114 + 552 = 666 across 23 + 28 = 51). The claim in §1 is
sourced to two GitHub documentation pages, quoted inline. The mechanism claims in dragon 2 were
verified against `man githooks` and against the real historical rename commit `35ccbd9` in this
repository's own history — not reasoned about. Where something could not be verified before
execution (whether Pages re-points to the new URL without a redeploy), the plan says so and gives the
command that settles it, rather than guessing.

**Nothing in this plan has been executed. `git status` at the end of Session 226 shows only this file
and the session ledger.**
