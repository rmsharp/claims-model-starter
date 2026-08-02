# Plan: Land the branch work on `origin/master`, converge all three documentation surfaces, and provision a one-time enterprise clone of the repository + wiki

**Status:** DRAFT plan (deliverable of Session 182, a planning session; **sequencing revised by
Session 194, §1.3, 2026-07-28** — see that section for what changed and why). Each phase below is
a *separate* session. Nothing in this document was executed while it was being written — no merge,
no push, no wiki publish, no MkDocs deploy. **Since then, real progress has landed:** Phases
A1–A4, B1's D3-independent core, B2, and B3 are complete (see each phase's own status line and
`CHANGELOG.md`); **Phase C4's gate is now fully satisfied** — the fork can run as soon as the
operator supplies D9/D5/D4/D8/D16 live at that session's start (§4's "Before step 1" note).

**Operator directive (recorded at the close of Session 181, 2026-07-27):**

> *"In the next session, produce a plan to get all of the branch work in the remote master, the
> wiki reflecting all of the updates, and anything else that needs to be done to move this wiki
> and main repository into an enterprise environment."*

**Note:** see §1.2 for the operator's 2026-07-27 clarification of what "move ... into an enterprise
environment" means — a one-time clone/fork, not a relocation of the repo/wiki/site quoted above.

**Evidence basis.** Every "files to change" list below comes from an executed search, not from
architectural memory (per `SESSION_RUNNER.md` Phase 2 → Planning Sessions). Evidence was gathered
by a 14-agent workflow (7 disjoint inventory surfaces, each adversarially re-verified), then the
plan itself was attacked by a 4-agent review (facts / commands / sequencing / completeness) that
raised 53 defects — 10 of them blocking. Every fix is folded in below and every surviving number
was reproduced first-hand. Where a count could not be reproduced exactly, this plan publishes the
**command** rather than the count and says so.

**Frame of reference.** All line numbers are valid at `feat/bedrock-mantle-migration` = `fc12d9f`
unless stated otherwise. **Do not cite `SESSION_NOTES.md` line numbers** — that file grows every
session, and the Session-181 handoff's own citations are already off by 7 against `fc12d9f`.

---

## 1. Executive summary

The operator named three goals. Their true shapes, after measurement:

| # | Goal | Reality |
|---|---|---|
| 1 | All branch work into remote `master` | **25 commits**, not 24 — two stacked fast-forwards (9 + 16). Topologically trivial. What makes it non-trivial is that **pushing to `master` is publishing**: it fires a public GitHub Pages deploy that currently leaks documents nobody decided to publish. |
| 2 | The wiki reflecting all updates | **Already published and byte-identical** — but published *from an unmerged branch*. The public wiki is ahead of the public `master`. The real work is a **merge-status sweep** across 6 pages and **provisioning separate publish machinery for a one-time enterprise clone** — the original's publish machinery is untouched (see §1.2). |
| 3 | Anything else needed to move to an enterprise environment | A licensing conflict that is a **hard legal gate**, a live public exposure, an unauthenticated web UI, an incomplete security guard, no deployment artifact at all, and a governance/CI surface that is essentially empty. **Only the legal-conflict and public-exposure gaps must be fixed on the original before Phase C4's one-time clone captures them** (see §1.2) — the destination is a non-syncing enterprise fork, not this repo's relocation. **Per §1.3, only the deployment-artifact gap (C2b) is fully out of this repository's scope**, stranded because its one gate (D14) is unanswerable here. The security-guard fix and the web-UI-auth *decision* (C1, C2) remain live pre-fork work this repository still tracks — D10, D13, and `bedrock-enterprise.md` §0's three security questions are all now resolved (Sessions 199–201, 2026-07-29), so both phases are fully ungated; their own bundled scope is separate work, not itself part of this table's snapshot. The governance/CI surface splits in two: the generated-projects' CI portability work (C3b) is ungated and tracked here now; the clone's own CI authoring (C3) is still a session this repository schedules — it just needs D9/D15 supplied live by the operator at that session's start, the same pattern C4 uses for D9/D5/D4, rather than a pre-written answer. |

**The single most important structural finding:** every push to `origin/master` triggers
`mkdocs gh-deploy --force --clean`, which publishes the **entire non-excluded `docs/` tree** — and
`mkdocs.yml`'s exclusion list is a *denylist* that omits four directories. Stage 1 fires the deploy
via `docs/tutorial.md`; Stage 2 fires it via `pyproject.toml`. **There is no way to land this work
without publishing.** The publication surface must therefore be fixed *before* the first push.

**The single highest-severity finding:** third-party methodology material — `docs/methodology/`
(12 files) **plus `SESSION_RUNNER.md` and `SAFEGUARDS.md`** — carries a copyright with an explicit
no-redistribution clause, inside a public repository whose root `LICENSE` grants the world the
right to "publish, distribute, sublicense, and/or sell". This is a rights conflict, it is already
realized (the repo is public), and pushing to a corporate host republishes it a second time under
the company's name. **It gates the corporate push and only the operator and legal can clear it.**

### 1.1 Corrections to the inherited state facts

The Session-181 handoff is the input to this plan. Four of its state facts are wrong:

| Handoff claim | Verified reality | Command |
|---|---|---|
| "15-commit branch… 24-commit problem" | **16** on the branch, **25** total | `git rev-list --count master..feat/bedrock-mantle-migration` → 16; `… origin/master..feat/…` → 25 |
| "46 branch-status markers across 6 pages" | Mixed units. The baseline grep matches **46 occurrences on 29 lines**; the handoff's per-page breakdown (14/8/3/2/1/1 = 29) is the *line* count. The canonical grep in §2.5 finds **36 lines**, of which 2 are unrelated false positives → **34 real sites**. | `grep -rno … \| wc -l` → 46; `grep -rn … \| wc -l` → 29 |
| "the merge changes no file under `docs/wiki/`, so it produces no diff there and no review signal" | **False.** The merge changes **20 wiki pages, +318/−129** — the Session-181 refresh (`a1d8af7`) lives on the branch. The merge is the one and only review opportunity. | `git diff --stat master..feat/… -- docs/wiki/` |
| "`origin/gh-pages` … last deployed 2026-06-04 (`18c9853`), ~26 sessions stale" | The **local ref is stale**. Real remote `gh-pages` is `e8fcba1`, deployed **2026-06-19** from `d6ea1e7`. | `git rev-parse origin/gh-pages` → `18c9853…`; `git ls-remote origin gh-pages` → `e8fcba1…` |

> **Do not "fix" the historical record.** These corrections belong in this plan and in live docs.
> Per project convention, the Session-178/180/181 narratives in `SESSION_NOTES.md` stay as written.

### 1.2 Correction to Goal 3's shape (Session 183)

The operator directive above reads as *"move … into an enterprise environment,"* and this plan's
first draft — including its D6/D8/D9/D16 rows and Phases C4/C5 — treated that as
**relocate-and-retire**: land the branch, then eventually decommission the public repo, wiki, and
MkDocs site. **That reading is wrong.** Corrected by the operator, 2026-07-27, verbatim in
substance:

> The current public repo, wiki, and MkDocs/gh-pages site continue to exist, unchanged, publicly,
> indefinitely. "Move into an enterprise environment" means prepare a **one-time clone/fork** that
> becomes the proprietary enterprise instance. The fork does **not** sync from the original
> afterward.

**What this changes:** D6 (site fate), D8 (wiki destination), D9 (host target), and D16
(post-cutover disposition) are re-scoped in §3 below — none of the public surfaces get
decommissioned. Phase C4 becomes **fork provisioning**, not migration; Phase C5 becomes
**fork-independence verification**, not decommission.

**The load-bearing consequence of "one-time, no sync":** whatever is wrong in the public repo at
the moment C4 clones it is **permanently baked into the proprietary copy** — there is no later sync
to carry a fix over. This is why C4 is gated on **A1–A4 and B1's D3-independent core complete**
(§1.3 corrects what "B1 complete" means), not just its D-items (dragon #20). It is also why
**`~/Development/claims-model-starter.wiki` must not be repurposed** for the clone (dragon #21) —
it is the live publish target for the original, which keeps operating.

### 1.3 Further correction: post-fork sequencing for D3 and the platform-team decisions (Session 190, 2026-07-27)

Session 190 recorded a second operator clarification, given in direct response to Phase B1's own
D1/D2/D3 gate (§4). The operator's own words, preserved verbatim (`SESSION_NOTES.md`, Session 190
handoff):

> All of those will be determined after the fork is created and not reported back to this
> repository.

**"Those" = D3** (IP disposition) **plus the platform-team decision bucket named at Phase 0
(§4): D4, D5, D8, D9, D14, D15, D16.** The legal bucket's other two items (D1, D2) and the
security bucket (D10, D13) are unaffected — D1/D2 are already answered (§3), and D10/D13 were not
named in the operator's decision; they remain live, Security-and-operator-owned decisions with the
pre-fork/post-fork timing flexibility dragon #20 already grants non-D14/D15 readiness work.

**What this changes, concretely:**

- **Phase C4's explicit `D4, D5, D8, D9, D16` gate is removed.** These five decisions — and D3,
  via its indirect gate on full Phase B1 — no longer need a written answer in this repository's
  Decision Register before C4 can run. The operator supplies whatever C4's mechanics need live (for
  example, the destination host URL for D9) at the time that session actually executes, and the
  eventual answers are **not** written back into `BACKLOG.md`, `SESSION_NOTES.md`, or this plan.
  C4 remains gated on **A1–A4 complete, B1's D3-independent core complete, and B2 complete** — see
  the corrected Phase C4 text (§4).
- **Full Phase B1 (the corporate DCO/CLA mechanism, which depends on D3) no longer gates C4.**
  Session 190 already executed and pushed B1's D3-independent core (LGPL wiki fix, root
  `SECURITY.md`/`CODEOWNERS`/`THIRD-PARTY-LICENSES`/baseline `CONTRIBUTING.md`, the AI-provenance
  statement, and the D1 attribution) — see the corrected Phase B1 text (§4) for what remains open
  and why it no longer blocks.
- **Phases C2b (gated only on D14) and C3 (gated on D9, D15) lose their last pre-fork gate.**
  Dragon #20 already scoped C1–C3's code/config work as flexible-timing; this decision resolves
  that flexibility to **"after, inside the clone, not tracked here"** for the phases whose gates
  fall entirely in the deferred bucket. C2b was never executable without D14 and is now explicitly
  the clone's own future work, not a session this repository will schedule. C3 was already framed
  as clone-only (§4); this removes only the now-moot "do not start before D9" pre-fork blocker.
- **Phases C1 and C2 are only partially affected**, because each has one gate outside the deferred
  bucket (C1: D10, D13; C2: D13) and one inside it (C1: D14; C2: D15). Splitting a phase's gate
  bucket down the middle is unusual enough to flag rather than silently merge: **C1 and C2 keep a
  narrower, still-live scope**, gated on their non-deferred D-items alone, with the D14/D15-dependent
  sub-tasks carved out into the clone's own future work. See the corrected Phase C1/C2 text (§4)
  for exactly which lines move.
- **C5's D16 gate is removed by the same decision** (§4) — not called out as its own bullet above
  because the change is small (one gate dropped, C4-complete remains) relative to C1/C2/C2b/C3.

**Confidence note, flagged rather than silently assumed.** The operator's recorded words name
D4/D5/D8/D9/D14/D15/D16 as a set, which is not literally identical to any single column of §3 — D14
and D15 do not appear in Phase C4's `Gated on:` line at all (they gate C1/C2/C2b/C3 instead). The
reading applied throughout this revision is that the named set is **Phase 0's own "platform team"
bucket** (§4 Phase 0: *"D4/D5/D8/D9/D14/D15/D16 to the platform team"*), reproduced in the same
order — i.e. the operator deferred an entire ownership bucket, not a literal reading of "C4's
gates." This is corroborated by the security bucket (D10, D13) being named separately in that same
Phase 0 line and *not* included in the deferral — though note the §3 Decision Register's own
**Owner** column for D13 still reads "Operator + platform team" (inherited unchanged from the
original plan, not edited by this revision), in some tension with routing D13 to "security" here;
this pre-existing wrinkle doesn't overturn the reading (Phase 0's routing line, not the Owner
column, is what groups D10/D13 together and predates Session 190 by several sessions), but is
flagged rather than silently smoothed over. If the "platform team bucket" reading is wrong, the
phases most affected by re-checking it are **C1 and C2** (left partially gated rather than fully
resolved) **and C2b** (currently ruled fully out of scope on the strength of D14 being in the
deferred set — if D14 turns out *not* to be deferred, C2b reverts to "in scope, blocked on D14"
rather than "not this repository's phase at all," a bigger reversal than C1/C2's narrowing).

### 1.4 Correction: the `.env` credential-rotation rationale in §2.8 and Phase C4 step 9 was wrong (Session 198, 2026-07-29)

§2.8 and Phase C4 step 9 both instruct rotating the three personal dev credentials (Anthropic API
key, GitLab PAT, Bedrock bearer token) "so the clone never depends on personal dev credentials."
**That premise is false, verified this session:**

- Phase C4 step 1 already mandates `git clone --mirror` over a filesystem copy **specifically
  because** "a folder copy carries `.env`" (line 1132, unchanged by this correction) — i.e. the
  plan already engineered the fork mechanism to structurally exclude `.env`. Re-confirmed live:
  `git check-ignore -v .env` → ignored; `git log --all --oneline -- .env` → empty (never
  committed, any branch, any ref).
- No tracked code auto-loads `.env` either — `orchestrator/config.py:5-16` documents that `.env`
  loading is "the caller's responsibility"; every consumer (`gitlab_adapter.py:54`,
  `github_adapter.py:65`, `bedrock_client.py:100`, etc.) reads only `os.environ`.

So `git clone --mirror` carries **zero** credential values to `<enterprise-clone>` — it gets
`.env.example` placeholders only. Rotating the *existing* personal credentials is therefore
**neither necessary** (the mirror-clone mechanism already prevents the dependency) **nor
sufficient** (if someone manually copied a `.env` into `<enterprise-clone>` anyway, freshly
rotated-but-still-personal keys would recreate the identical dependency the rotation was meant to
prevent).

**What actually matters, and replaces the rotation instruction:** whoever bootstraps
`<enterprise-clone>`'s runtime config (`.env` or the destination host's CI/CD secret variables)
must populate it with **enterprise-owned** credentials — an org-issued Anthropic key, a token
scoped to the enterprise GitLab instance/service account, and whatever auth the enterprise AWS
account uses for Bedrock — and must **not** copy the personal `.env` over as a shortcut. This is
routine C4-time provisioning, not a pre-fork gate; nothing needs to happen to the personal `.env`
before Phase C4 runs. Phase C4 step 9 is corrected accordingly below. Rotating the personal
credentials remains a legitimate "someday" hygiene item for the operator's own continued local
dev use of this repository, independent of the fork — but it is no longer a named C4 disposition
or a B2 register item.

---

## 2. Evidence-based inventory

### 2.1 Git topology — measured, not assumed

```
git rev-list --count origin/master..master                        →  9
git rev-list --count master..feat/bedrock-mantle-migration        → 16
git rev-list --count origin/master..feat/bedrock-mantle-migration → 25
git merge-base --is-ancestor origin/master master                 → exit 0
git merge-base --is-ancestor master feat/bedrock-mantle-migration → exit 0
git log --merges --oneline                                        → (empty — zero merge commits, ever)
```

- `origin/master` = `f590585` (Session 175). Local `master` = `b791d77` (Session 178).
  Branch = `fc12d9f` (Session 181), and **`origin/feat/bedrock-mantle-migration` is also at
  `fc12d9f`** — so any commit a phase adds locally is *not* on the remote until pushed. This
  matters in A4; see the pre-flight.
- **Both stages are true fast-forwards, and the merged tree is byte-identical to the branch tip**
  (`git merge-tree --write-tree master feat/…` → `aa50ede6…` = `git rev-parse feat/…^{tree}`).
  No conflict is possible, and the Session-181 gate result applies to the merged state unchanged.
- The repo has **zero merge commits in its entire history** — fast-forward landing is house
  convention (`Evolution.md:216`). Any step phrased "review the merge commit" has nothing to review.
- ⚠ **"master" is ambiguous by one file.** `git diff --stat origin/master..master -- docs/wiki/`
  → `Intake-Interview-Design.md | 4 ++--`. Name which `master` in every wiki assertion.

### 2.2 What fires on a push to `master`

| Workflow | Trigger | Stage 1 (9 commits) | Stage 2 (16 commits) |
|---|---|---|---|
| `ci.yml` | push to `master`, **no** path filter | **FIRES** | **FIRES** |
| `publish-tutorial.yml` | push to `master`, paths `docs/*.md`, `mkdocs.yml`, the workflow file, **`pyproject.toml`** | **FIRES** — via `docs/tutorial.md` | **FIRES** — via `pyproject.toml` (`>=0.40`→`>=0.94`) |

Three traps in that table:

1. **`docs/*.md` is non-recursive.** None of the 20 changed `docs/wiki/claims-model-starter/*.md`
   pages match it. Stage 2 fires *because of `pyproject.toml`*. Never phrase the reason as
   "because docs changed" — change that line and the reasoning silently inverts.
2. **Trigger scope ≠ publication scope.** A file under `docs/<subdir>/` never *triggers* a deploy
   but is always *published* by one. That decoupling is how the audits went public.
3. **`ci.yml` has `concurrency: cancel-in-progress: true`; `publish-tutorial.yml` has no
   concurrency block at all.** Two pushes in quick succession cancel the first CI run (leaving a
   grey "cancelled" that reads like a pass) and race two `gh-deploy --force` jobs.

### 2.3 The live public exposure — verified by fetching the site

`mkdocs.yml:12-17` excludes only `/methodology/`, `/planning/`, `/architecture-history/`,
`/style/`, `/wiki/`. It is a **denylist**, and `nav:` does not gate publication (MkDocs publishes
every non-excluded file and emits only an INFO notice). Four `docs/` subdirectories are therefore
published by default: `audits/`, `deployment/`, `executive-summaries/`, `explainers/`.

Fetched 2026-07-27:

| URL | Status | What it is |
|---|---|---|
| `/audits/2026-06-01-technical-debt-audit/` | **200** | Internal technical-debt audit |
| `/audits/2026-06-10-wiki-vs-code-accuracy-audit/` | **200** | Internal accuracy audit; **renders the operator's absolute home-directory path into public HTML** |
| `/executive-summaries/business-value-capture.qmd` | **200** | Raw Quarto source of an executive business-case document |
| `/deployment/bedrock-enterprise/` | **404** | *Goes public on the next deploy — which the merge triggers* |
| `/robots.txt` | **404** | Nothing blocks crawling |

`sitemap.xml` lists exactly four URLs — `/`, `/tutorial/`, and **both audits** — i.e. the audits
are not merely reachable, they are *submitted for indexing*. The executive summary is served but
absent from the sitemap (link-discoverable only), so a take-down scoped to `docs/audits/` leaves
it live.

`gh-deploy --force --clean` writes a **parentless single commit** each deploy (`gh api
…/commits/e8fcba1 --jq '.parents'` → `[]`), so there is no recoverable record of what was
published and no `git revert` path. **Bundle the branch before the next deploy** (A4 pre-flight) —
a path listing is not enough to reconstruct content.

### 2.4 Documentation-accuracy inventory

| Surface | Freshness | Load-bearing defects |
|---|---|---|
| GitHub Wiki (23 pages) | Current as of S181 — but **published from an unmerged branch** | 6 pages carry merge-status markers; 4 rows publish the stale `>=0.40` SDK floor; `Security-Considerations.md:388` states `PyGithub` is "the one LGPL-3.0 direct dependency" (false), and 4 further locations name PyGithub as the LGPL example without mentioning `python-gitlab` |
| MkDocs / gh-pages (public) | Deployed 2026-06-19 from `d6ea1e7` | `tutorial.md:522` "Only `anthropic` exists today" — **false since `cf40dc0` (2026-06-17), two days before the deploy**; `tutorial.md:53` "422+ tests"; `tutorial.md:218` a wiki-relative link that 404s |
| In-repo docs | Not refreshed since S177 | `README.md:215` "Proprietary."; `README.md:128` "795 tests"; `ROADMAP.md:7` "797 tests"; `OPERATIONS.md:33` bedrock default `sonnet-4-6` (actual: `opus-4-8`); `OPERATIONS.md` documents **no** `AWS_*` variable |

**Test-count claims disagree four ways** (422 / 795 / 797 / 922) and coverage three ways. Scoped
counts, measured: `--ignore=tests/ui` → **898**; `tests/ui` → **32**; full → **930**.
`README.md:128`'s counterpart is **898** (its documented `uv sync` omits the `ui` extra), not 930
— CI installs `ui` and gates on the full set. Single-source the number or drop it.

### 2.5 The wiki merge-status sweep

Zero markers exist on `master` or `origin/master` today. **The merge is what carries them onto
`master` for the first time.**

Baseline grep (`"unmerged\|feat/bedrock-mantle-migration"`) → **29 lines / 46 occurrences**.

**Canonical sweep command** — publish this, not the handoff's two-term grep:

```bash
grep -rniE "unmerged|feat/bedrock-mantle-migration|not[- ]yet[- ]merged|branch-only|branch only|in[- ]flight|on the branch|last session on|the branch lands|when it lands|has not been merged" \
  docs/wiki/claims-model-starter/
```

It returns **36 lines**: **34 real sites** plus **2 unrelated false positives** (below). The
baseline grep misses 6 of the 34 — `AI-Dependencies.md:36`, `:56`, `Changelog.md:13`,
`Evolution.md:379`, `Security-Considerations.md:392`, and `Evolution.md:380`'s neighbour context.
`Evolution.md:379` is reachable **only** because `last session on` was added to the regex; the
handoff's grep would have left it stale.

Three edit kinds are mixed together — delete-the-block (the `Changelog.md:15` unreleased
blockquote, the `Security-Considerations.md:46` merge-status blockquote), change-a-value, and
rewrite-surrounding-prose. `Evolution.md`'s hits are almost all narrative rewrites. **This is not
a `sed`.**

**Mechanical value changes** — verified exhaustively:

| Change | Sites |
|---|---|
| `>=0.40` → `>=0.94` | `Software-Bill-of-Materials.md:31`, `:73`, `Security-Considerations.md:352`, `AI-Dependencies.md:36` |
| bedrock default `sonnet-4-6` → `opus-4-8` | `Security-Considerations.md:126`, `:127`, `AI-Dependencies.md:56` — **and only these three** |
| test count `916`/`922` split → one number | `Monitoring-and-Operations.md:100`, `Evolution.md:254` |

**NO-EDIT list — five traps.** The first three do *not* match the canonical grep, so they are
protected only by reading before editing; the last two *do* match and must be left alone:

1. `Changelog.md:20` already reads `…is now anthropic[bedrock]>=0.94 … (was >=0.40)`. **Correct
   post-merge.** A blind `>=0.40`→`>=0.94` replace corrupts it.
2. `grep -rn "sonnet-4-6" docs/wiki/claims-model-starter/` returns **12 lines; exactly 3 change**
   (above). The other **9** are correct — `Changelog.md:18`, `Security-Considerations.md:124`,
   `:125`, `:376`, `AI-Dependencies.md:10`, `:55`, `Data-Guide.md:110`, `:121`, `Evolution.md:89`
   — because the **first-party `anthropic` default really is `claude-sonnet-4-6`** and is
   deliberately unchanged.
3. `Changelog.md:5` — "Dates are the commit dates on `master`" — a permanently-true convention
   statement, at risk only from a manual `on \`master\`` sweep.
4. **`AI-Dependencies.md:151`** — "an in-flight Anthropic **outage**". Unrelated sense. Matches
   the canonical grep.
5. **`Schema-Reference.md:632`** — "in-flight **runs** must not break mid-upgrade". Unrelated
   sense. Matches the canonical grep.

**Therefore the sweep's terminal state is: the canonical grep returns exactly two lines —
`AI-Dependencies.md:151` and `Schema-Reference.md:632` — and nothing else.**

**No automated backstop exists.** `tests/test_wiki_no_line_citations.py` checks *citation form*
only. Nothing in the repo checks merge status.

> **Confirmed:** that guard does **not** cover `docs/planning/`. Existing plans there already
> carry `path.ext:N` citations and the guard is green — so this document may use them freely.

### 2.6 Host and identity coupling points

`.githooks/post-commit` → `scripts/publish_wiki.sh` → `~/Development/claims-model-starter.wiki`
→ `git push origin master` to **github.com/rmsharp**.

| File:line | Coupling | Breaks on an enterprise host? |
|---|---|---|
| `scripts/publish_wiki.sh:42` | `WIKI_CLONE` default path | Defaults to the **personal public** clone — see dragon #3 |
| `scripts/publish_wiki.sh:44` | `SOURCE_DIR=…/docs/wiki/claims-model-starter` | Only if the directory is renamed |
| `scripts/publish_wiki.sh:23`, `:63` | Hardcoded clone URL (comment + error text) | Misleading |
| `scripts/publish_wiki.sh:72`, `:75` | **Hard-rejects** any origin URL not containing `claims-model-starter.wiki` | **YES — hard blocker on rename** |
| `scripts/publish_wiki.sh:80` | **Hard-requires** the wiki branch be named `master` | **YES — most enterprise hosts default to `main`** |
| `scripts/publish_wiki.sh:104` | `git push origin master` — hardcoded refspec | **YES** |
| `.githooks/post-commit:18` | Path prefix `^docs/wiki/claims-model-starter/` | Only if renamed |
| `mkdocs.yml:3-5` | `site_url` / `repo_url` / `repo_name` — all personal | **YES** |
| `tests/test_wiki_no_line_citations.py:38` | Hardcoded wiki dir | Only if renamed |
| **`orchestrator/config.py:198,354,355,365,366`** | Personal GitLab namespace embedded in a **user-facing `ConfigError` message** | **YES — code change** |
| **`tests/orchestrator/test_config.py:38,39,121,222,234`** | Assert on those literals | **YES — paired test edit** |
| `.env.example:25,26,30`; `OPERATIONS.md:25` | Personal namespace examples | Cosmetic but user-facing |
| **`docs/tutorial.md:427,445-447`** | The *published* tutorial tells users to export a personal namespace | **YES — user-facing** |
| `README.md:9` | Published-site URL | **YES** |
| `Contributing.md:19`, `:236`, `:238` | Public clone URL, public issue tracker, **"contact `rmsharp` on GitHub" as the security-disclosure path** | **YES** |
| `Monitoring-and-Operations.md:16` | Personal namespace example | Cosmetic |
| `SESSION_RUNNER.md:209`, `Contributing.md:122` | **Prose** documenting the publish mechanism | **YES — omitted from every code-level inventory** |

**Rediscovery command** — re-derive rather than trusting this table after any edit:

```bash
git grep -n -I -iE 'rmsharp|rmsharp\.github\.io|github\.com/rmsharp|claims-model-starter' -- . \
  | grep -vE '^(SESSION_NOTES|CHANGELOG|PROJECT_LEARNINGS)\.md|^docs/architecture-history/'
```

Two behaviours the plan must build on:

- **`rsync -a --delete` (`publish_wiki.sh:92`) is a destructive one-way sync.** Any page edited
  through the web UI during the migration is **silently deleted** by the next publish.
- **`core.hooksPath=.githooks` is per-clone local config, not tracked.** A fresh enterprise clone
  publishes nothing, silently. And `post-commit` runs *after* the commit object exists, so a
  publish failure cannot fail the commit — the only signal is console output.

### 2.7 Licensing and legal exposure

**Licence table — 22 declared direct dependencies plus 3 notable transitive components.** This
artifact does not exist anywhere in the repo today and is what legal review will demand.

| Class | Package | Version | Licence |
|---|---|---|---|
| **LGPL (direct)** | `python-gitlab` | 8.2.0 | LGPL-3.0-or-later (License field + classifier + bundled COPYING) |
| **LGPL (direct)** | `PyGithub` | 2.9.1 | LGPL-3.0-only — *classifier is version-ambiguous*; provable only from bundled `licenses/COPYING.LESSER` |
| **MPL (transitive)** | `certifi` (via httpx/anthropic), `orjson` (via LangGraph), `pathspec` (via mkdocs/hatchling) | — | MPL-2.0 (`orjson`: `MPL-2.0 AND (Apache-2.0 OR MIT)`) |

The other **20** direct packages are MIT / BSD / Apache-2.0. **Zero GPL-only, zero AGPL** across
all 96 installed distributions. The achievable end state is *"permissive + MPL-2.0"*, **not**
"fully MIT" — `orjson` arrives via LangGraph and survives the LGPL removal entirely.

Four legal items, in descending severity:

1. **Third-party methodology rights conflict (HARD GATE).** Verified first-hand:
   `docs/methodology/README.md:361` — *"Iterative Session Methodology — Copyright © 2025-2026
   Terrell Deppe (KJ5HST)"*; `:365` — *"You may not sell, sublicense, redistribute, publish,
   market, or commercially exploit this methodology itself … without prior written permission"*;
   `:369` points at a `LICENSE` file that **does not exist** (`find docs/methodology -iname
   'LICENSE*'` → empty). The root `LICENSE:8` grants exactly those rights.
   **⚠ The exposure is wider than `docs/methodology/`.** `CLAUDE.md:67` declares
   **`SESSION_RUNNER.md` (304 lines) and `SAFEGUARDS.md` (183 lines)** "synced from canonical, not
   project-owned" — the same framework — and both carry **zero attribution**
   (`grep -c -i "terrell\|KJ5HST\|copyright"` → 0, 0). `PROJECT_LEARNINGS.md`'s seed rows and
   `docs/architecture-history/methodology-pr2527-remediation-mpc.md:6` ("captured **verbatim**"
   from the upstream repo) are further instances. Deleting only `docs/methodology/` would leave
   ~490 lines of the same material shipping to the corporate host. *(12 of the 13 files under
   `docs/methodology/` are third-party; `PROJECT_CONVENTIONS.md` is project-authored.)*
2. **`README.md:215` says "Proprietary."** while `LICENSE:1`, `pyproject.toml:7`,
   `packages/data-agent/pyproject.toml:7`, `Contributing.md:5`/`:228` and the SBOM all say MIT.
   Root cause is provable: `f2f2a70` (2026-04-16, *"change license from Proprietary to MIT"*)
   changed exactly 4 files and missed the README; `git log -L 213,216:README.md` returns one
   commit, `5c73ed0` (2026-04-14). **104 days old.**
3. **Copyright is held by an individual** — `LICENSE:3`. Exactly **one human author** across all
   345 commits, so a single signature closes the inbound question — but **329 commits carry
   `Co-Authored-By: Claude` trailers** (`git log --grep="Co-Authored-By: Claude" --format=%H | wc -l`),
   and no document in the repo answers AI-provenance. The MIT grant already made publicly is
   **irrevocable** for code published to date.
4. **The published wiki is a separate repository with no licence of its own** — 23 pages on the
   public internet under no stated terms, with its own 33-commit history.

**Absent legal artifacts** (all verified absent at repo root): `NOTICE`, `THIRD-PARTY-LICENSES`,
`REUSE.toml`, `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`, `CLA`/`DCO`, `AUTHORS`,
`CODEOWNERS`. Zero `SPDX-License-Identifier` headers anywhere. And **projects generated by the
pipeline carry no licence at all** (`agents/website/templates.py:150-170` emits no `license` field
and no `LICENSE` file) — a policy violation that recurs on every pipeline run.

### 2.8 Secrets, identity, and data hygiene — the good news

Package this evidence *for the reviewer*, not just record it:

- **No credential file has ever entered git history.** Across all refs the only env-shaped blob is
  `.env.example`. Only two files were ever deleted in the entire history, neither sensitive.
  **No history rewrite is needed on secrets grounds.**
- **Zero committed secret values**, by two orthogonal proofs (credential-shape grep + entropy
  scan). The entropy scan's only genuine high-entropy string is the **Subresource-Integrity hash**
  in `ui/intake/templates.py`.
- **`rmsharp@me.com` appears in zero tracked file contents** — it exists only in commit metadata.
- **All runtime artifacts are correctly gitignored**, each confirmed with `git check-ignore -v`.
- **All test fixtures and eval corpora are synthetic** — a PII-shape grep and a real-insurer grep
  both return zero.

Against that, five real items:

- **~10 scanner false positives will fire on import** (`glpat-xyz` / `ghp_xyz` / `sk-ant-xyz` test
  literals; `.env.example` placeholders; `uv.lock:522`'s `ghp_import-2.1.0` wheel; the SRI hash;
  and `Security-Considerations.md:339`, which literally contains scanner-bait). No
  `.gitleaksignore` or baseline exists. **Ship the allowlist with the import request.**
- **Two live docs carry abandoned-personal-account identifiers** — `docs/planning/bedrock-testing-enablement.md`
  (`:19`, `:50`, `:63`, `:64`, `:77`) and **this plan** until A3 scrubs both. The identifiers are
  referred to here only as *the abandoned AWS account id* and *the abandoned support-case number*;
  find them with `git grep -nE '[0-9]{12}|1784409[0-9]+'` scoped to those files.
- **Three live credentials sit in the local `.env`** (Anthropic key, GitLab PAT, Bedrock bearer
  token). ~~Rotate them so the enterprise clone never depends on personal dev credentials.~~
  **Corrected, §1.4 (Session 198): this rationale was wrong** — `git clone --mirror` (Phase C4
  step 1) already carries zero credential values, so rotation doesn't achieve the stated goal.
  The real requirement is provisioning `<enterprise-clone>` with enterprise-owned credentials at
  C4 time (step 9), not rotating the personal ones beforehand. This is independent of the GitHub
  account hosting the public repo/wiki/site, which is **never** closed or decommissioned (§1.2) —
  "the personal account" here means the personal Anthropic/GitLab/AWS dev credentials, not that
  account.
- **Three live GitLab pilot projects exist outside git**, recorded only in the gitignored
  checkpoint store. Invisible to every repo-scoped check.
- **`.git` is 162 MB with 3148 loose objects and zero packs**, plus 8 unreachable dropped-stash
  commits. `git clone` drops both; `cp -r`/`rsync` does not.

### 2.9 Enterprise runtime readiness

**Already done — do not budget work for these:**

- **PrivateLink needs no code.** The SDK reads **`ANTHROPIC_BEDROCK_MANTLE_BASE_URL`**
  (`_mantle.py:142`, verified first-hand) — a VPCE base URL is a pure env setting.
- `aws_profile` **is** supported by `AnthropicBedrockMantle` and treated as SigV4 — closing
  `bedrock-enterprise.md` §7 punch-list item 5.
- The **repo-host adapters themselves** accept an enterprise host:
  `PyGithubAdapter(host_url=…)` → GHES via `/api/v3`; `PythonGitLabAdapter(host_url=…)` →
  self-hosted GitLab. *(But see the `cli.py` gap below — the adapters are ready; one entrypoint is
  not.)*

**Gaps, each verified:**

| Gap | Evidence | Consequence |
|---|---|---|
| `bedrock-enterprise.md:149` says `ANTHROPIC_BASE_URL` is honored | It is **not** — that var is first-party-client only | A platform engineer sets it, sees no error, and believes PrivateLink is working while all traffic leaves publicly |
| `require_sigv4` checks only `AWS_BEARER_TOKEN_BEDROCK` | SDK's `_MANTLE_API_KEY_ENV_VARS = ("AWS_BEARER_TOKEN_BEDROCK", "ANTHROPIC_AWS_API_KEY")` | A stray `ANTHROPIC_AWS_API_KEY` silently bypasses the IAM role **with the guard enabled** |
| `bedrock-enterprise.md` §4/§7 say `base_url`/`http_client` are "not yet" exposed | `56dc700` shipped both (`bedrock_client.py:92-93,115-118`) | Reviewers scope and bill code work that is already done |
| Enterprise hooks are library-only | Exactly 2 construction sites (`factory.py:72` ×2), both passing only `model` | **No deployment can set a proxy or corporate CA** for the Bedrock path |
| **`MPC_HOST_URL` is read in only two places** — `config.py:245` and `run_pipeline.py:129,300` | `agents/website/cli.py` reads **no** environment variable; `:98-108` declares a `--host-url` flag and `:155-156` falls back to the **public** host | An operator who exports `MPC_HOST_URL` and runs the website CLI without `--host-url` creates the project on **gitlab.com / api.github.com**, silently |
| `ssl_verify` is dead config | Accepted at `gitlab_adapter.py:61`, never forwarded by `_make_gitlab_adapter` (`config.py:59-69`) | Behind TLS inspection both adapters fail cert verification with no in-app knob |
| **The intake web UI has zero auth** | No `authenticat`/`authoriz`/`login`/`CSRF`/`CORSMiddleware`/`add_middleware` anywhere in `src/…/ui/` | `go/modelintake` is the stakeholder front door and is an unauthenticated FastAPI app |
| htmx loads from `unpkg.com` at render time | `ui/intake/templates.py:46-50` | **Browser-side** egress — invisible to a server-side firewall review; when blocked the page renders fine and silently does nothing |
| `provider_creds_available('bedrock')` probes only `AWS_ACCESS_KEY_ID` / `AWS_PROFILE` / `~/.aws/credentials` | `eval_cutover.py:55-92` (re-cited Session 214; the finding is unchanged, a third provider shifted the range) | Under IRSA/ECS/instance-profile auth every live test **skips** and pytest exits 0 |
| **Two** plaintext stores, not one | `checkpoints.py:57-68` (0644 JSON) **and** `ui/intake/app.py:52` `DEFAULT_DB_PATH` (SQLite interview transcripts, 0644); no `chmod`/`umask`/`0o###` anywhere | Both will hold real stakeholder content on a shared host |
| **Generated projects' CI is hardcoded to public registries** | `governance_templates.py:615` `python:3.11` (Docker Hub), `:617,656,667,678` `pip install uv` (PyPI), `:652-653,663-664,674-675` `actions/checkout@v4`+`setup-python@v5`, `:688` `ruff-pre-commit`; only knob is `--ci-platform {gitlab,github}` | **Every project the pipeline produces lands with red CI** on an enterprise runner — and the generated project *is* the deliverable |
| **No package-index configuration anywhere** | `git grep -E 'UV_INDEX\|PIP_INDEX\|index-url\|\[\[tool.uv.index\]\]'` → nothing | `uv sync` is the first command in every documented workflow; on an allowlist-only runner nothing else in this plan can be validated |
| No container image, manifest, or IaC | No `Dockerfile`/`*.tf`/`*.service` | The runtime shape is undecided — **and it determines the §3 IAM trust policy** |

**Egress inventory** (the firewall-review deliverable), in three tiers:

- *Server-side runtime:* `bedrock-mantle.{region}.api.aws`, `api.anthropic.com`, the repo host,
  AWS STS, IMDS `169.254.169.254`.
- *Browser-side (stakeholder workstation):* `unpkg.com`.
- *Build-time:* `pypi.org` / `files.pythonhosted.org`; and **inside every generated project** —
  Docker Hub, GitHub Actions marketplace, `ruff-pre-commit`, PyPI.

Note `anthropic[bedrock]` pulls **boto3 + botocore** — SigV4 is not pure-httpx. An internal index
mirroring only `anthropic` fails at the first call, not at startup. `botocore` honours
`AWS_CA_BUNDLE`, which appears nowhere in this repo.

### 2.10 Governance and CI surface

Verified **absent**: `CODEOWNERS`, `dependabot.yml`, PR/issue templates, `SECURITY.md`,
`.pre-commit-config.yaml`, `.gitleaksignore`, `.python-version`. `.github/` contains nothing but
`workflows/`, holding exactly `ci.yml` and `publish-tutorial.yml` — **and there is no
`.gitlab-ci.yml` or any other CI definition**, so a move to GitLab means authoring CI from
scratch.

Verified absent from CI: SAST, dependency-vulnerability audit, licence gate, machine-readable
SBOM.

Present but weak:

- **All 11 `uses:` lines are floating tags** (`@v4`), not SHAs; `setup-uv` pulls `version: "latest"`;
  all four jobs are `runs-on: ubuntu-latest` (GitHub-hosted runners, which GHES and GitLab do not
  provide).
- **No `--frozen`/`--locked` on any of 5 `uv sync` invocations.**
- **`publish-tutorial.yml` is the only job with `contents: write`** while the repo default is
  read-only — the single supply-chain blast path is an unpinned third-party action inside a
  write-scoped job that force-pushes a branch.
- The **"Upload coverage" step is a permanent no-op**.
- **Live tests auto-activate whenever credentials are present.** CI is hermetic only because
  GitHub Actions has no AWS chain. A corporate runner using OIDC role assumption — the pattern
  `bedrock-enterprise.md` recommends — **un-skips 8 live tests and starts making paid calls**.
- `origin/master` has **no branch protection, no rulesets**; the 25 pending commits have **never
  run CI on GitHub**.
- The available `gh` token has scopes `gist, read:org, repo, workflow` — **no `security_events`,
  no `admin:org`**. Any step reading code-scanning results or setting org rulesets needs re-auth.

---

## 3. Decision register

Phases are gated on these. **Owners are named because most are not engineering calls.**

| # | Decision | Owner | Recommendation | Gates |
|---|---|---|---|---|
| **D1** | **All third-party methodology material** (`docs/methodology/`, `SESSION_RUNNER.md`, `SAFEGUARDS.md`, `PROJECT_LEARNINGS.md` seed rows, `docs/architecture-history/methodology-pr2527-remediation-mpc.md`): remove, obtain written permission, or carve out via NOTICE? | **Operator + legal** | Ask Terrell Deppe for written permission first (one email); if not promptly granted, **remove**. **Add the mandated attribution string in every branch of this decision** — it is currently absent everywhere. | B1, and **any corporate push** |
| **D2** | Licence of record: MIT or proprietary? | **Operator + legal** | **Stay MIT.** Publicly MIT since 2026-04-16; that grant is irrevocable, so a retroactive relicense buys nothing. Fix `README.md:215` to match. | A3, B1 |
| **D3** | IP disposition: assignment, work-for-hire, or third-party OSS intake? | **Legal** | Prepare **third-party OSS intake** as default. One human author = one signature. **Do not edit `LICENSE:3` until legal rules.** **Timing (2026-07-27, Session 190): resolved by the operator after C4 runs, inside the enterprise clone — not reported back here (§1.3).** | ~~B1~~ none — see §1.3 |
| **D4** | Does the corporate host require signed commits / DCO? | **Operator → platform team** | Find out **before** migrating; push for "going forward only". A signed-history rewrite changes every SHA and breaks the provenance chain. A PR-button merge is host-signed, which may satisfy the policy with no local key setup. **Timing (2026-07-27, Session 190): resolved post-fork, inside the clone — not reported back here (§1.3).** | ~~C4~~ none — see §1.3 |
| **D5** | Import history as-is, rewrite, or squash-import? | **Operator + platform team** | **Import as-is.** If an author-email allowlist blocks the push, prefer **squash-import + archived bundle** over `filter-repo` — it breaks SHA references honestly in one place instead of silently everywhere. **Timing (2026-07-27, Session 190): resolved post-fork, inside the clone — not reported back here (§1.3).** | ~~C4~~ none — see §1.3 |
| **D6** | MkDocs/gh-pages site: refresh, retire, or relocate? | **Operator** | **ANSWERED (2026-07-27): refresh and keep public, indefinitely.** The site is not retired. A1's containment fixes (fail-closed `mkdocs.yml`, corrected tutorial) become standing maintenance for an ongoing public site, not one-time cleanup before shutdown. See §1.2. | A1 |
| **D7** | Take down the already-public audits retroactively? | **Operator** | **Move `docs/audits/` out of `docs_dir`** (structural, not a config a future edit can undo), force a re-deploy so the URLs 404, then request search-index removal. They are in `sitemap.xml` with no `robots.txt`. **Unaffected by D6/§1.2** — the site staying public makes this more urgent, not less: there is no future decommission to eventually close the exposure if this is left unanswered. Also decide whether this extends to `/executive-summaries/business-value-capture.qmd` (200, link-discoverable, not in `sitemap.xml`) — as scoped, this action does not cover it. | A1 |
| **D8** | Where does the wiki live **in the enterprise clone** (the original wiki keeps auto-publishing unchanged — D6, §1.2); does the clone's copy need auto-publish at all; **and what does the destination require of page naming, the sidebar file, and intra-wiki link syntax?** | **Operator + platform team** | Resolve the host first. **C4 delivers a hardened, fail-closed local-hook mechanism for the clone as the default** (parameterised `publish_wiki.sh`, no defaults, cannot resolve to the personal wiki) — do **not** reuse `~/Development/claims-model-starter.wiki` for it (dragon #21). Publishing from CI instead of a local hook is a further hardening step, not required for C4's DONE criteria; take it up in C3 if the platform team wants it. Note `_Sidebar.md`/`Home.md` are GitHub-Wiki reserved names and **157 intra-wiki links are extensionless page slugs** that resolve only under GitHub's wiki router. **Timing (2026-07-27, Session 190): resolved post-fork, inside the clone — not reported back here (§1.3); C4 still delivers the fail-closed mechanism unconditionally regardless of what D8 turns out to be.** | ~~C4~~ none — see §1.3 |
| **D9** | Repo-host target **for the enterprise clone** (the original stays on GitHub, untouched — §1.2): self-hosted GitLab or GHES? | **Operator** | Decide before security review. **GHES hard-rejects namespaces containing `/`** (`github_adapter.py:85-89`) — a contract change, not a config line. **If GitLab, all of `.github/workflows/` is dead and CI must be re-authored** for the clone only — the original's `.github/workflows/` is unaffected. **Timing (2026-07-27, Session 190): resolved post-fork, inside the clone — not reported back here (§1.3). Practical consequence: whoever runs C4 needs the operator to supply a live destination host URL at that session's start — do not stall Phase C4 waiting for a written D9 answer in this document.** | ~~C3, C4~~ none — see §1.3 |
| **D10** | Bedrock endpoint: Regional or Global? | **Security + operator** | **ANSWERED (2026-07-29): Regional** — operator accepted the recommendation this session; formal security co-sign is still nominal until an actual security team exists (post-fork). For P&C claims data, residency dominates the ~10% premium. Recorded in `bedrock-enterprise.md` §5; hard-block SCP templated at `docs/deployment/bedrock-residency-scp.json` (specific region allowlist still a platform-team placeholder). | C1 |
| **D11** | Run the LGPL removal before the corporate move? | **Operator + legal** | **Confirm the corporate copyleft policy first.** Many policies permit LGPL for unmodified, dynamically-imported libraries. If permitted, defer — it is a rewrite of the two least-tested modules immediately before their first live use. | B3 |
| **D12** | Version/tag the landing? | **Operator** | **ANSWERED (2026-07-27): bump to 0.3.0** — accepted the recommendation, confirmed by proceeding straight to A3. Done in A3: two `pyproject.toml` files, `README.md:3`, **and `uv lock`** (the lock pinned both workspace members at `0.2.0`, `uv.lock:1109`, `:1175`; now `0.3.0`). The actual `git tag` is a separate, still-open action — A3 has no `git tag` command; it belongs with A4 ("Land it") once the version is on `master`. | A3 |
| **D13** | Wire `http_client`/`require_sigv4` to app/env? | **Operator + platform team** | **RESOLVED (Session 200, 2026-07-29), per its own recommendation:** the `require_sigv4` guard now checks both SDK-recognized bearer-token env vars (`AWS_BEARER_TOKEN_BEDROCK` **and** `ANTHROPIC_AWS_API_KEY` — it previously checked only the first, a real hole) and defaults from a new `BEDROCK_REQUIRE_SIGV4` env var when not passed explicitly, so `INTAKE_LLM_PROVIDER=bedrock` can enforce it purely through config — no call-site change (both `bedrock_client.py` copies + 3 paired tests each; full gate: 970 passed, 8 live-skipped, 97.76% coverage, ruff/mypy clean). **`http_client` wiring left undone, as recommended** — still conditional on TLS-inspection confirmation, which remains unconfirmed. | ~~C2~~ (D13 was C2's sole remaining gate — see corrected Phase C2), ~~C1~~ (the three `bedrock-enterprise.md` §0 security questions — C1's last gate — are now answered too, Session 201: see corrected Phase C1) |
| **D14** | **Runtime shape: EKS+IRSA / ECS task role / EC2 instance profile / on-prem VM?** | **Operator + platform team** | Must be answered before the IAM-trust-policy artifact can be filled in, and it also decides whether the live-test credential probe works at all. **Timing (2026-07-27, Session 190): resolved post-fork, inside the clone — not reported back here (§1.3).** C1's own trust-policy sub-task moves with it (see corrected Phase C1, §4); C1's D10/D13-scoped work does not wait on D14. | ~~C1, C2b~~ none — see §1.3 (C2b fully deferred; C1 narrowed) |
| **D15** | **Package resolution: internal index (Artifactory/Nexus/devpi) or proxied public PyPI?** | **Operator + platform team** | Decide early — `uv sync` is the first command in every documented workflow. **Timing (2026-07-27, Session 190): resolved post-fork, inside the clone — not reported back here (§1.3).** C2's own index-variable-documentation sub-task moves with it (see corrected Phase C2, §4); C2's D13-scoped work does not wait on D15. | ~~C2, C3~~ none — see §1.3 (C2 narrowed; C3 already clone-only) |
| **D16** | **Disposition and access model of the enterprise CLONE** (repo + wiki + releases) — private from creation? who administers it? are the two GitHub Releases recreated on the clone, or left as a pointer to the public originals? *(The public originals get no disposition decision — they are unchanged; §1.2.)* | **Operator + legal** | Default: clone is private from creation; recreate the releases on the clone from `releases-export.json` (already in C4's scope) rather than a pointer, since the clone has no live link back to the original. The MIT grant on the original's published code is irrevocable regardless of the clone's licence posture. **Timing (2026-07-27, Session 190): resolved post-fork, inside the clone — not reported back here (§1.3).** C5 step 3 records whatever the operator decided, live, rather than gating on a pre-written answer. | ~~C4, C5~~ none — see §1.3 |

---

## 4. Phased plan

**Every phase below is ONE session. Close out after each.** Phases A1–A4 are the operator's goals
1 and 2 and form the critical path. B and C are "anything else"; B1 gates the corporate push.

> **The load-bearing sequencing decision: do all preparation on the branch, then push ONCE.**
> Both stages are fast-forwards to the same tree, so `git push origin
> feat/bedrock-mantle-migration:master` lands all commits in a single ref update. This yields one
> CI run and one deploy instead of two, avoids the `cancel-in-progress` trap, avoids racing two
> `gh-deploy --force` jobs, and — decisively — means the **only** deploy that ever fires comes
> from a tree whose publication surface has already been fixed. Pushing `master` first would
> deploy the *unfixed* tree.

> ### ⚠ STANDING RULE for Phases A1, A2, A3 and B1 — disarm the wiki auto-publish hook
>
> All four phases touch files under `docs/wiki/claims-model-starter/` (A1 updates audit-path
> references in `Evolution.md:200,244,268,335,438`; A3 updates planning-doc references in
> `Evolution.md` and `Changelog.md`). `.githooks/post-commit:18` fires on **any** commit touching
> that prefix and pushes to the **public** wiki with no confirmation.
>
> **`export MPC_SKIP_WIKI_PUBLISH=1` does NOT work here.** Each Bash tool call gets a fresh shell,
> so the variable is unset by the time `git commit` runs. Use a form that survives:
>
> ```bash
> # FIRST action of each of these sessions:
> git config --unset core.hooksPath
> git config --get core.hooksPath        # → empty. Verify before editing anything.
> ```
>
> Re-arm **only** in A4, after `scripts/publish_wiki.sh` has run successfully:
> `git config core.hooksPath .githooks`.
> If you keep the hook armed instead, every commit must be written as
> `MPC_SKIP_WIKI_PUBLISH=1 git commit …` **on one command line**. Note `git commit --no-verify`
> does **not** skip `post-commit`.

---

### Phase 0 — Raise the decision register *(operator action, not a session)*

**Revised by §1.3 (Session 190):** D1–D3 (legal) and D4/D5/D8/D9/D14/D15/D16 (platform team) are
no longer raised here — the operator resolves them post-fork, inside the enterprise clone, and
their answers are not reported back to this repository. What remained for this phase was **D10/D13
to security, together with `docs/deployment/bedrock-enterprise.md` §0's three existing questions**
(Guardrails mandate? FIPS mandate? does the target account have current-gen Claude runtime
quota?). A "yes" on Guardrails or FIPS would have redirected mantle → `bedrock-runtime`, a
materially larger change than anything in this plan.

**DONE:** D1, D2, D6, D7, D12 answered (D1/D2/D6/D7 gate Phase A; D12 gated A3, already executed).
**D10 answered (Session 199, 2026-07-29): Regional** — see the Decision Register row and
`bedrock-enterprise.md` §5. **D13 resolved (Session 200, 2026-07-29)** — see the Decision Register
row; only its `require_sigv4` sub-scope (guard completeness + env wiring), not `http_client`. D3–D9,
D14–D16 are explicitly not this repository's decisions to track (§1.3). **`bedrock-enterprise.md`
§0's three security questions answered (Session 201, 2026-07-29, operator):** Guardrails — no;
FIPS — no; runtime quota — expected yes (established enterprise account), **not independently
verified**. Q1/Q2 = no confirms the mantle path stays correct, so Phase C1's narrowed scope applies
as written — the "yes" branch (`bedrock-runtime` re-plan) did not materialize. **Phase 0 is now
fully raised — every item is answered or explicitly deferred post-fork.** The one loose end is Q3's
independent verification (live Service Quotas / Workbench `ping`), which needs the actual
enterprise account and so cannot happen from this repository — carried forward as a flag, not a
blocker on C1's own (non-AWS-connected) scope.

---

### Phase A1 — Contain the public exposure and correct the tutorial — **COMPLETE (Sessions 186–189)**

**Branch:** `feat/bedrock-mantle-migration`. **Gated on:** D6, D7. **Standing rule applies.**

**Scope**

1. **`mkdocs.yml` → fail-closed.** The denylist has failed twice already. Invert to
   gitignore-negation form — exclude everything under `docs/`, re-include `index.md` and
   `tutorial.md`. Fix the misleading comment at `mkdocs.yml:10-11`.
2. **Move `docs/audits/` out of `docs_dir`** (per D7) to a top-level `audits/`. **Update
   references in LIVE documents only** — `docs/wiki/claims-model-starter/Evolution.md` (5 sites)
   and `docs/planning/httpx-adapter-migration.md`. Per §6, `SESSION_NOTES.md`, `CHANGELOG.md` and
   `docs/architecture-history/` keep the old path as historical record; add one line to the new
   `audits/README` noting the former location.
3. **Fix `docs/tutorial.md`:** `:522` ("Only `anthropic` exists today" → two providers ship),
   `:53` ("422+ tests" → the single-sourced number or drop it), `:218` (wiki-relative link that
   404s).
4. **Add a `concurrency:` block to `publish-tutorial.yml`** so deploys serialize.
5. *(Optional)* `validation: links: unrecognized_links: warn` in `mkdocs.yml` — `--strict` alone
   does **not** catch the `:218` class of error.

**DONE looks like:** a clean-tree build publishes only the tutorial, the root redirect, and
`404`/assets/search/sitemap. `bedrock-enterprise.md` is **not** in the manifest.

**Verify** — build from a clean checkout, never the working tree. **Commit first: `git archive`
reads the ref, not the worktree.**

```bash
rm -rf /tmp/clean /tmp/out && mkdir -p /tmp/clean
git archive feat/bedrock-mantle-migration | tar -x -C /tmp/clean
(cd /tmp/clean && uv run --extra docs mkdocs build -d /tmp/out) || { echo BUILD-FAILED; exit 1; }
find /tmp/out -type f | grep -vE '/assets/' | sed 's|/tmp/out/||' | sort
#   expect: 404.html, index.html, search/search_index.json, sitemap.xml, sitemap.xml.gz, tutorial/index.html
#   expect NOT: deployment/, audits/, executive-summaries/, explainers/
grep -n "Only \`anthropic\` exists today\|422+" docs/tutorial.md   # → 0
git config --get core.hooksPath                                    # → empty (hook still disarmed)
```

> `uv run mkdocs` **fails** without `--extra docs` — mkdocs lives in the optional `docs` extra
> (`pyproject.toml:41-43`), and its failure (`Failed to spawn: mkdocs`) reads like a broken
> environment rather than a wrong command.

**Boundary:** one session. Close out. Nothing is pushed; the site is still stale-and-wrong in
public. That is the correct intermediate state.

---

### Phase A2 — Wiki merge-status sweep — **COMPLETE (Sessions 186–189)**

**Branch:** `feat/bedrock-mantle-migration`. **Standing rule applies — verify the hook is
disarmed before touching any wiki file.**

**Scope:** work the canonical grep from §2.5. Apply the three mechanical value changes. Honour the
five NO-EDIT traps. Delete the two blockquotes (`Changelog.md:15`,
`Security-Considerations.md:46`) **and rewrite the sentences around them** —
`Security-Considerations.md:28` and `:48` restate the same master/branch split and would leave
§1.2 self-contradictory if only the blockquote goes. Fix `Evolution.md:3`'s "Last updated" banner,
which already contradicts its own session table at `:381`.

For the test-count split (`Monitoring-and-Operations.md:100`, `Evolution.md:254`): **add the CI
guard first, then re-measure and write the number** — `uv run pytest --collect-only -q | tail -1`.
Do not paste `930` (pre-guard) or A3's `898` (a different, `--ignore=tests/ui` scope).

Add the narrow CI guard: ban the literal string `feat/bedrock-mantle-migration` on wiki pages, in
`tests/test_wiki_no_line_citations.py`, in this same commit.

**DONE looks like:** the canonical grep returns **exactly two lines** — `AI-Dependencies.md:151`
and `Schema-Reference.md:632`, both unrelated uses of "in-flight" — and nothing else.

**Verify:**

```bash
grep -rniE "unmerged|feat/bedrock-mantle-migration|not[- ]yet[- ]merged|branch-only|branch only|in[- ]flight|on the branch|last session on|the branch lands|when it lands|has not been merged" \
  docs/wiki/claims-model-starter/ | cut -d: -f1,2 | sort -u
#   → exactly: AI-Dependencies.md:151 and Schema-Reference.md:632
grep -rn -- ">=0.40" docs/wiki/claims-model-starter/    # → only Changelog.md:20 (historical, correct)
grep -rc "sonnet-4-6" docs/wiki/claims-model-starter/ | awk -F: '{s+=$2} END {print s}'   # → 9 (was 12; exactly 3 changed)
uv run pytest tests/test_wiki_no_line_citations.py -q --no-cov
# dead-path check (also in §7) — Changelog.md is excluded: its entries are dated historical
# records that correctly name where a file lived AT THE TIME (two such refs exist today,
# Changelog.md:107 and :220, both now under docs/architecture-history/). Do not "fix" them.
for p in $(grep -rhoE '`?docs/(audits|planning|architecture-history)/[A-Za-z0-9._/-]+\.md' \
            --exclude=Changelog.md docs/wiki/claims-model-starter/ | tr -d '`' | sort -u); do
  [ -e "$p" ] || echo "DEAD WIKI PATH REFERENCE: $p"
done                                                    # → no output
git -C ~/Development/claims-model-starter.wiki log --oneline -1   # → UNCHANGED (hook disarmed)
```

**Boundary:** one session. Close out. Work **bottom-up within each file** (highest line number
first) — `Security-Considerations.md` alone has ~17 sites and deletions shift everything below.
Re-run the grep after each file rather than trusting a stale list.

---

### Phase A3 — In-repo documentation reconciliation — **COMPLETE (Sessions 186–189)**

**Branch:** `feat/bedrock-mantle-migration`. **Gated on:** D2, D12. **Standing rule applies.**

**Scope**

- `README.md:215` "Proprietary." → per D2. `README.md:128` test count → **898** (the README's own
  documented `uv sync` omits the `ui` extra; do not paste 930).
- `ROADMAP.md:7` counts; add an M6 entry for multi-provider/Bedrock — the milestone sections
  (`ROADMAP.md:26-67`) predate the entire second-provider capability. `ROADMAP.md:9` and
  `BACKLOG.md:7` both claim "nothing open" — land this plan's phases as backlog items.
- `OPERATIONS.md`: add the `AWS_*` block (`AWS_REGION`, `AWS_DEFAULT_REGION`,
  `AWS_BEARER_TOKEN_BEDROCK`, `AWS_PROFILE`, plus the CA/proxy/index variables from C2); fix
  `:33`'s **bedrock** default to `anthropic.claude-opus-4-8`. Cross-check against
  `.env.example:66-83`, which **is** correct on this branch.
- `CHANGELOG.md`: entries for Sessions 178–181. Per D12, convert `[Unreleased]` to a dated `0.3.0`
  heading and bump **both `pyproject.toml` files, `README.md:3`, and regenerate `uv.lock`**
  (`uv lock`) — the lock pins both workspace members at `0.2.0` (`uv.lock:1109`, `:1175`) and
  `uv run` will otherwise rewrite it silently. Stage `uv.lock` explicitly.
- Archive `docs/planning/multi-provider-llm-plan.md` → `docs/architecture-history/` (fully
  executed; `PROJECT_CONVENTIONS.md:35-37` makes it archive-eligible).
- `docs/planning/bedrock-testing-enablement.md`: scrub the abandoned account id and case number,
  carve the still-useful "how the project reaches Bedrock" table and the quota-code table forward
  into `bedrock-enterprise.md`, then archive. Its `Status: ready-for-human` at `:45` currently
  reads as live guidance for an abandoned account.
- **Scrub the same two identifiers from this plan** (`docs/planning/enterprise-migration.md`).

**DONE looks like:** no in-repo doc contradicts the code on provider count, model id, licence, or
test count; the CHANGELOG covers through Session 181; `docs/planning/` holds only live plans; no
live doc carries an abandoned-account identifier.

**Verify:**

```bash
grep -n "Proprietary" README.md                                   # → 0 (if D2 = MIT)
grep -n "anthropic\.claude-sonnet-4-6" OPERATIONS.md              # → 0
grep -c "claude-sonnet-4-6" OPERATIONS.md                         # → 2 (:33 first-party, :297 cost note — BOTH CORRECT)
grep -rnE "[0-9]{12}|1784409[0-9]+" docs/ --include='*.md' | grep -v '^docs/architecture-history/'   # → 0
grep -n "^version" pyproject.toml packages/data-agent/pyproject.toml   # → both 0.3.0
uv lock --check
uv run pytest -q && uv run ruff check src/ tests/ packages/ scripts/ && uv run mypy
```

**Boundary:** one session. Close out.

---

### Phase A4 — Land it: push branch → PR → CI → single fast-forward push → publish → verify — **COMPLETE (Sessions 186–189, PR #2 → `master@9cabe0e`)**

**This is the phase the operator asked for.** Everything before it exists to make this phase safe.

**Pre-flight (all must hold):**

```bash
git status --porcelain                       # → clean (commit or stash SESSION_NOTES.md FIRST)
git fetch origin '+refs/heads/*:refs/remotes/origin/*'   # MANDATORY — local origin/gh-pages is stale

# ⚠ A1–A3 commits are LOCAL ONLY. Push the branch, or the PR will test the pre-A1 tree.
git push origin feat/bedrock-mantle-migration
test "$(git rev-parse feat/bedrock-mantle-migration)" \
   = "$(git ls-remote origin refs/heads/feat/bedrock-mantle-migration | cut -f1)" \
   && echo BRANCH-PARITY-OK

git merge-base --is-ancestor origin/master feat/bedrock-mantle-migration && echo FF-OK

# Preserve the published CONTENT, not just its paths — gh-deploy --force destroys it.
git fetch origin gh-pages:refs/heads/gh-pages-preA4
git bundle create ~/gh-pages-preA4.bundle refs/heads/gh-pages-preA4
```

**Steps**

1. **Open a PR** `feat/bedrock-mantle-migration` → `master` **from the pushed branch**. This is
   the *only* way to get a GitHub-side CI signal before code reaches the default branch — these
   commits have never run CI there. **Confirm the PR head SHA equals the local branch tip** before
   trusting the result. Wait for all four jobs green. Re-push and re-assert parity after any
   fixup commit.
2. **Single push — this is the ONLY landing mechanism.**
   `git push origin feat/bedrock-mantle-migration:master`.
   **Do NOT use any PR merge button.** GitHub offers no fast-forward merge: `--merge` creates the
   repo's first merge commit in 345 commits, and `--rebase`/`--squash` rewrite all 25 SHAs and
   silently invalidate every SHA cited in `SESSION_NOTES.md` and `CHANGELOG.md` (dragon #12). The
   PR auto-closes as merged once its commits appear on `master`.
3. **Fast-forward local `master`** to match, so the two never diverge again.
4. **Publish the wiki explicitly.** The hook will **not** fire — a fast-forward creates no commit,
   and `post-merge` does not exist in `.githooks/`. Chain the guard so a failure aborts:

   ```bash
   git merge-base --is-ancestor a1d8af7 HEAD \
     || { echo 'ABORT: HEAD does not contain a1d8af7 — publishing would regress 20 wiki pages'; exit 1; }
   cd "$(git rev-parse --show-toplevel)"
   scripts/publish_wiki.sh
   ```
   A `no changes to publish` message here is a **FAILURE**, not a pass — A2's sweep guarantees the
   source differs from the live wiki.
5. **Re-arm the hook:** `git config core.hooksPath .githooks`.
6. **Verify the deploy** and confirm the exposure is closed.

**DONE looks like:** `origin/master` = the branch tip; CI green on `master`; the public site serves
only the tutorial; the audits 404; the wiki is published from a commit that is on `master`.

**Verify:**

```bash
git ls-remote origin master                                   # → the branch tip SHA
git rev-list --count origin/master..feat/bedrock-mantle-migration   # → 0
git log --merges --oneline | wc -l                            # → 0 (no merge commit was created)
gh run list --workflow ci.yml --limit 1                       # → success (NOT "cancelled")
gh run list --workflow publish-tutorial.yml --limit 1         # → success
curl -s -o /dev/null -w '%{http_code}' https://rmsharp.github.io/claims-model-starter/audits/2026-06-01-technical-debt-audit/   # → 404
curl -s -o /dev/null -w '%{http_code}' https://rmsharp.github.io/claims-model-starter/deployment/bedrock-enterprise/            # → 404
curl -s https://rmsharp.github.io/claims-model-starter/sitemap.xml | grep -c audits   # → 0
git -C ~/Development/claims-model-starter.wiki log -1 --format=%s
#   → "docs: sync wiki from model_project_constructor@<new master short sha>"
git -C ~/Development/claims-model-starter.wiki status -sb     # → no "[ahead N]"
git config --get core.hooksPath                               # → .githooks (re-armed)
```

**Rollback.** The gh-pages deploy is **not revertible** — restore from `~/gh-pages-preA4.bundle`
and force-push if needed. The only backout for `master` is a force-push to `f590585`, which
rewrites public history: **do not do it without explicit operator authorisation.** If CI fails on
the PR, fix on the branch and re-push; do not proceed to step 2.

**Boundary:** one session. Close out. **Goals 1 and 2 are complete at this point.** Do not start
Phase B in the same session.

---

### Phase B1 — The legal packet *(gates the corporate push)* — **D3-independent core: COMPLETE (Session 190)**

**Gated on:** D1, D2 (both answered — §3). **D3 no longer gates this phase** — per §1.3, the one
D3-dependent sub-item (the corporate DCO/CLA mechanism) is explicitly deferred post-fork, inside
the clone, rather than blocking B1. **Standing rule applied.**

**Scope executed (Session 190, commits `f15b12d`/`86a19e9`/`623a3f2`, pushed to `origin/master`):**
D1 outcome across **all** third-party methodology material — `docs/methodology/` (12 files),
`SESSION_RUNNER.md`, `SAFEGUARDS.md`, `PROJECT_LEARNINGS.md`'s framework seed rows, and
`docs/architecture-history/methodology-pr2527-remediation-mpc.md`. `THIRD-PARTY-LICENSES` (full
distribution table, since updated again by the httpx migration — see `CHANGELOG.md` 2026-07-28).
Corrected the **five** wiki locations that framed `PyGithub` as the only LGPL dependency. Authored
the AI-provenance statement (`NOTICE`). Added root `SECURITY.md`, `CODEOWNERS`.

**Scope explicitly NOT executed, and no longer scheduled here:** root `CONTRIBUTING.md`'s
corporate DCO/CLA mechanism section — added as baseline **TBD** text (D3/D4/D9-dependent). Per
§1.3, D3/D4/D9 are now resolved post-fork, inside the clone — so this section will be authored
**there**, not in a future session of this repository. Do not schedule a follow-up B1 session to
close this gap; it is not this repository's gap to close.

**DONE looks like (achieved):** the D1 conflict resolved with a written record; one file lists
every dependency's licence; no document claims a single LGPL dependency; `SECURITY.md`,
`CODEOWNERS`, `CONTRIBUTING.md` (baseline), `THIRD-PARTY-LICENSES` all exist.

**Verify (re-derived from Session 190's own correction to the plan's original D1 command, which
expected attribution inside the synced `SESSION_RUNNER.md`/`SAFEGUARDS.md` files themselves —
`CLAUDE.md`'s "do not edit synced files" rule makes that impossible; attribution lives in `NOTICE`
+ `CLAUDE.md` instead):**

```bash
grep -rn "the one LGPL-3.0 direct dependency" docs/wiki/         # → 0
grep -rn -i "lgpl" docs/wiki/claims-model-starter/               # every hit names BOTH packages
ls SECURITY.md CONTRIBUTING.md CODEOWNERS THIRD-PARTY-LICENSES
grep -c 'Terrell Deppe' NOTICE                                   # → non-zero
grep -c 'Terrell Deppe' CLAUDE.md                                # → non-zero (Adaptations section)
git grep -l -i 'KJ5HST\|Terrell Deppe' -- . | grep -vE '^NOTICE$|^CLAUDE\.md$'   # → 0 or historical-record-only hits
```

**Boundary:** was one session (Session 190, 2026-07-27). Closed. No further B1 session is owed.

---

### Phase B2 — Import readiness: scanners, identity, external assets — **COMPLETE (Session 195)**

**Delivered:** `.gitleaksignore` (repo root, one real gitleaks fingerprint on a full-history scan —
`ROADMAP.md:65`, a model-id false positive — plus documentation of why); the full classification
table and external-asset register at `audits/2026-07-28-b2-import-readiness.md`; `releases-export.json`
and `prs-export.json` (repo root). The three GitLab pilot projects (`subrogation-pilot`, `-v2`,
`-v3`, all under `rmsharp-modelpilot`) were located via the gitignored checkpoint store and given
project IDs/URLs in the register. **Not performed:** rotating the three live `.env` credentials —
that requires operator action against external consoles (Anthropic/GitLab/AWS), named as an open
disposition in the register rather than silently marked done (see that doc §3.3). **Correction,
§1.4 (Session 198):** this disposition's own rationale ("so the clone never depends on personal
dev credentials") was wrong — the register entry and this note both describe accurately what
Session 195 did and found at the time, but the follow-up action is no longer rotation; see §1.4
and Phase C4 step 9 for what actually replaces it.

**Scope (original):** author `.gitleaksignore` (or the target scanner's baseline) enumerating the ~10 known
false positives from §2.8 **with the classification table**, so the import request arrives with
the answer rather than the alarm. Package the two negative proofs as the secrets attestation —
including the exact commands, so the reviewer can re-run them. Export the API-only assets:
`gh api repos/rmsharp/claims-model-starter/releases > releases-export.json` and
`gh pr list --state all --json number,title,body,mergedAt > prs-export.json` (release bodies are
**not** carried by `git push --tags`). Build the **external-asset register**, split into two kinds
— **the wiki repo and the gh-pages site have a fixed disposition (keep, unconditionally; §1.2/D6)
and do not need a register entry beyond noting that**; the genuinely undecided assets are the three
GitLab pilot projects, the two GitHub Releases and both annotated tags (recreate-vs-pointer is a
D16 call, deferred post-fork per §1.3 — the register simply notes the two options and that C4/C5
will record whichever the operator picks, live), and the three `.env` credentials (rotate
regardless of any account closure — none is planned, §1.2).

**DONE looks like:** a reviewer-ready import packet; every non-git asset has a named disposition.

**Verify:**

```bash
git fetch origin '+refs/heads/*:refs/remotes/origin/*'
[ "$(git rev-parse origin/gh-pages)" = "$(git ls-remote origin gh-pages | cut -f1)" ] \
  || { echo 'ABORT: gh-pages ref stale — the history scan would be incomplete'; exit 1; }
git rev-list --all --objects | awk '{print $2}' | grep -iE "\.env|secret|credential|\.pem|id_rsa"
#   → only .env.example
ls releases-export.json prs-export.json .gitleaksignore
```

**Boundary:** one session. Close out.

---

### Phase B3 — LGPL removal *(was conditional on D11)* — **COMPLETE (Sessions 191–193)**

Execute `docs/planning/httpx-adapter-migration.md` — Phase 1 (GitLab), Phase 2 (GitHub), each its
own session, on a dedicated branch off a clean `master`. **Do not re-plan it**; resolve its
DP1–DP4 and go. Three corrections to fold in first:

- Its §1.1 names only `certifi` as the residual MPL component. **Also `orjson` and `pathspec`** —
  and `orjson` arrives via LangGraph, so it survives this migration regardless. Configure any
  licence allow-list for **MPL-2.0 as a class**, not by package name.
- Its `:99` prune list names `Deprecated` and `wrapt`, which are in neither the venv nor the lock.
  Use `uv tree` as the authoritative prune check. *(Its `greenlet` note is a different case —
  `greenlet` **is** in `uv.lock:526` as a SQLAlchemy dep, excluded on arm64 by marker but
  installed on x86_64 CI. Do not "correct" the SBOM's greenlet row.)*
- Its prerequisite at `:191-195` warns about "uncommitted Session-179 mantle WIP" — stale; that
  branch is fully committed and, after A4, merged.

**DONE looks like:** both LGPL SDKs gone from `pyproject.toml` and `uv.lock`; suite green at
coverage ≥95%.

**Verify:** the plan's own §8 done-greps:
`grep -rn -E "import gitlab|from gitlab|from github import|import github" src/ tests/` → 0;
`grep -rn -iE "python-gitlab|pygithub" pyproject.toml uv.lock` → 0;
`uv tree | grep -iE "python-gitlab|pygithub"` → 0; full gate green.

**Boundary:** 2–3 sessions (its own phases). Close out after each.

---

### Phase C1 — Bedrock enterprise correctness *(narrowed by §1.3 — D14's sub-task carved out)*

**Gated on:** ~~D10~~ (**answered, Session 199: Regional** — see Decision Register and
`bedrock-enterprise.md` §5), ~~D13~~ (**resolved, Session 200** — see Decision Register; only its
`require_sigv4` sub-scope, not the rest of this phase), and ~~`bedrock-enterprise.md` §0's three
security questions~~ (**answered, Session 201, 2026-07-29: Guardrails no, FIPS no, runtime quota
expected-yes-unverified — mantle path confirmed correct, see Phase 0**). **This phase is now fully
ungated.** **D14 no longer gates this phase** — per §1.3, D14 (runtime shape) is resolved
post-fork, inside the clone, so the one D14-dependent sub-task below (the IAM *trust* policy) is
carved out rather than blocking the rest of C1.
**Phase C1 is now fully complete (Session 202, 2026-07-29).** Session 199 implemented only D10's
own artifact (the residency SCP), Session 200 implemented only D13's `require_sigv4` sub-scope
(guard completeness + env wiring, not `http_client`), Session 201 only answered the §0 questions
(no code, no artifact) — Session 202 implemented the remaining bundled scope: the `base_url`/
`ANTHROPIC_BASE_URL` doc fix (see below) and the §3 IAM-permissions-policy extraction. No scope
remains in this phase; D14's trust-relationship fill-in is the enterprise clone's own post-fork
work, unaffected by this phase's completion.

**Former ⚠ (resolved, Session 201):** the scope below used to silently assume "no" to Guardrails
and FIPS with no branch for "yes" — both are now confirmed "no" by the operator (Phase 0), so the
assumption held and the scope below is correct as written. Runtime quota (Q3) is a separate,
non-blocking item — see Phase 0's note — and does not affect this phase's scope, which involves no
live AWS calls.

**Scope — ALL DONE (Session 202, 2026-07-29):** ~~fix the false `ANTHROPIC_BASE_URL` claim at
`bedrock-enterprise.md:149` and document `ANTHROPIC_BEDROCK_MANTLE_BASE_URL` in `.env.example` and
§4/§7~~ — **DONE.** The false claim was actually two-fold once re-investigated against the
installed SDK (0.94.1): §4 said the `base_url` override "does not yet" exist (stale — shipped
`56dc700`) *and* cited `ANTHROPIC_BASE_URL` as the relevant env var (wrong — verified in
`lib/bedrock/_mantle.py` that the mantle client reads the mantle-specific
`ANTHROPIC_BEDROCK_MANTLE_BASE_URL` instead; `ANTHROPIC_BASE_URL` belongs to the plain
`anthropic.Anthropic` client, a different code path). Both fixed; the literal string
`ANTHROPIC_BASE_URL` no longer appears anywhere in `bedrock-enterprise.md`.
Refreshed §4/§7 to reflect that punch-list items 1–3 shipped in `56dc700` and item 5 (`aws_profile`)
is confirmed supported. ~~Close the `require_sigv4` hole~~ — **DONE, Session 200**: both
`bedrock_client.py` copies now check both known bearer-token env vars (a local mirrored tuple, not
a private SDK import — see D13 Decision Register entry) and `require_sigv4` defaults from
`BEDROCK_REQUIRE_SIGV4`. Record the D10 residency decision in §5 — **DONE, Session 199**.
~~Extract the §3 IAM **permissions** policy and the residency SCP into separate applyable artifact
files~~ — **DONE, Session 202** (the residency SCP itself already existed, Session 199): two new
files, `docs/deployment/bedrock-mantle-execution-role-permissions.json` (the real permissions
policy — AWS identity-based policies structurally cannot contain a `Principal`, so this had to be
separate from the trust policy) and `docs/deployment/bedrock-mantle-execution-role-trust.json`
(the trust policy, `Principal` left an explicit placeholder naming D14 as the blocker rather than
guessing a runtime shape).

**DONE looks like:** ~~no false claim in the enterprise guide~~ **(done, Session 202)**;
~~`require_sigv4` rejects both env vars~~ **(done, Session 200)**; ~~the IAM **permissions** policy
and SCP exist as files, with the trust-relationship section explicitly marked TODO rather than
silently omitted or guessed~~ **(done, Session 202 — two files, not one; see above)**.

**Verify (all re-run and passing, Session 202):**

```bash
grep -n "ANTHROPIC_BASE_URL" docs/deployment/bedrock-enterprise.md   # → 0 ✅ (Session 202)
grep -rn "ANTHROPIC_AWS_API_KEY" src/ packages/                      # → present in BOTH guards (✅ Session 200)
ls docs/deployment/*.json                                            # → permissions + trust + SCP (3 files, ✅ Session 202)
grep -n "D14" docs/deployment/*.json                                 # → trust-policy TODO marker (✅ Session 202)
uv run pytest tests/agents/intake/test_bedrock_client.py tests/data_agent_package/test_bedrock_client.py --no-cov   # 25 passed
uv run pytest -q                                                     # 970 passed, 8 live-skipped, 97.76% (unchanged — docs/config only)
```

**⚠ Coverage trap:** `--cov-fail-under=95` is in the default addopts, so any wiring added without
tests fails the **entire** suite with a coverage error that looks unrelated. The C4 decoupling
rule duplicates the clients — **every hook change is a paired edit plus paired tests.** (Not
triggered this session — no code changed.)

**Boundary:** one session. Close out. **Phase C1 is complete as of this session.**

---

### Phase C2 — Runtime, network, and data-at-rest readiness *(narrowed by §1.3 — D15's sub-task carved out)*

**Gated on:** ~~D13~~ — **resolved, Session 200 (see Decision Register). D13 was this phase's only
listed gate, so Phase C2 is now fully ungated and schedulable.** **D15 no longer gates this
phase** — per §1.3, D15 (package index) is resolved post-fork, inside the clone, so the one
D15-dependent sub-task below (documenting the index variables) is carved out rather than blocking
the rest of C2. Resolving D13 fully cleared this phase's gate (D13 was C2's only listed gate) —
**Phase C1 is now also fully ungated** (its own `bedrock-enterprise.md` §0 gate was answered
separately, Session 201), so both phases are schedulable. The scope below (htmx vendoring, intake
UI auth posture, the `MPC_HOST_URL` gap, plaintext-at-rest, `run_pipeline.py:450`) is itself
untouched and remains this phase's own future session, but nothing blocks starting it.

**Scope:** vendor htmx locally and serve it from a static route (fixes both the browser-egress
failure and the licence-inventory gap — a vendored copy carries its own LICENSE). Decide and
document the intake UI's auth posture (**it has none today**). Fix the **`MPC_HOST_URL` gap** in
`agents/website/cli.py` — either fall back to the env var at `:155-156` (with a paired test) or
add a startup guard that refuses the public default when `MPC_HOST_URL` is set; document the
asymmetry in `OPERATIONS.md` either way. Document `HTTPS_PROXY`/`NO_PROXY`/`REQUESTS_CA_BUNDLE`/
`SSL_CERT_FILE`/`AWS_CA_BUNDLE` in `OPERATIONS.md` — **do not** try to plumb `ssl_verify`, which is
dead config, and never set it `False`. **Do not document the D15 index variables
(`UV_INDEX_URL`/`UV_DEFAULT_INDEX`/`PIP_INDEX_URL`, `UV_NATIVE_TLS`) here** — that documentation
depends on knowing which index D15 resolves to and is the clone's own post-fork work. Resolve the
plaintext-at-rest question for **both** stores — `.orchestrator/checkpoints`
(`checkpoints.py:57-68`) and the intake session DB (`ui/intake/app.py:52`, `INTAKE_DB_PATH`) — by
`chmod 0600` at creation plus a documented 0700 parent under a dedicated service account, or a
documented encrypted-volume requirement. Fix `run_pipeline.py:450` to default `--model` to `None`
so the factory resolves the provider default.

**DONE looks like:** no CDN dependency at page render; both stores have a decided and documented
permission posture; every D13-scoped (proxy/CA) enterprise env var is in `OPERATIONS.md`; the
website CLI cannot silently target a public host. **The D15 index variables are explicitly not
part of this phase's DONE criteria** — do not treat their absence from `OPERATIONS.md` as
incomplete.

**Verify:**

```bash
grep -rn "unpkg.com" src/                                        # → 0
grep -nE "REQUESTS_CA_BUNDLE|AWS_CA_BUNDLE|HTTPS_PROXY" OPERATIONS.md                 # → present
grep -n "MPC_HOST_URL" src/model_project_constructor/agents/website/cli.py           # → present (or guard present)
python3 -c "import os,stat;print(oct(stat.S_IMODE(os.stat('intake_sessions.db').st_mode)))"   # → 0o600
uv run pytest -q && uv run mypy
```

**Boundary:** one session. Close out.

---

### Phase C2b — Deployment artifact — **out of scope for this repository (§1.3)**

**Was gated on:** D14 alone. Per §1.3, D14 (runtime shape) is resolved post-fork, inside the
enterprise clone, and not reported back here. Since D14 was C2b's *only* gate and this phase
cannot be scoped, let alone executed, without knowing the runtime shape, **C2b is no longer a
phase this repository schedules.** It becomes the enterprise clone's own future work, on its own
timeline, using whatever runtime shape the operator settles on there.

**Scope, preserved here only as forward-looking context for whoever does this work in the
clone** (not a session this plan's executor should pick up): produce the chosen runtime shape's
container image and deployment manifest/IaC, the intake-UI hosting with TLS termination and the
SSO/auth fronting decided in C2, and the IAM trust relationship matching C1's policy artifact
(including the trust-policy block C1 deliberately left as a TODO). Pin the interpreter
(`.python-version`) and wire the D15 index configuration into the image build.

**Boundary:** not this repository's session to run. If a future session is tempted to pick this
up, re-check §1.3 first — the gate was removed because it is unanswerable here, not because it
was satisfied.

---

### Phase C3 — CI and supply-chain hardening *(clone-only; D9/D15 resolved live, not pre-recorded — §1.3)*

**Gated on: C4 complete.** D9 and D15 no longer need a written answer in this document before C3
can be scheduled (§1.3) — but C3's executor still needs to *know* D9 (GHES vs. GitLab) to author
the right CI system, and D15 to configure the index. Since neither is answered here anymore, **the
operator supplies both live, at the start of this session**, the same way C4's executor gets the
destination host URL. If D9 = GitLab, the whole `.github/workflows/` tree is dead and SHA-pinning
it is discarded work — confirm D9 with the operator before choosing a scope branch below. **This
entire phase targets the enterprise clone's CI configuration**, not the original's — all work is
committed inside `<enterprise-clone>` (C4), which is why C4 must exist first; the original's
`.github/workflows/` stays exactly as A4 left it (§1.2).

**Scope, if D9 = GHES:** SHA-pin all 11 `uses:` lines and bump the deprecated Node-20 action
majors in the same pass; confirm runner labels — `runs-on: ubuntu-latest` requires GitHub-hosted
runners the enterprise will not provide.
**Scope, if D9 = GitLab:** author `.gitlab-ci.yml` reproducing all four `ci.yml` jobs (lint /
typecheck / test / decoupling). This is the **clone's own** docs-publish decision — the original's
`publish-tutorial.yml` keeps serving the public site unchanged (D6, §1.2) and is not touched by
this phase; decide separately whether the clone needs an equivalent internal-docs job at all, or
none. **Every `gh`-based verification command in this plan must be re-expressed for the target
host.**

**Either way:** add `--frozen` to all 5 `uv sync` invocations; add `.python-version`; fix or delete
the dead coverage-upload step; **add `-m 'not live'` to the corporate CI invocation explicitly**
rather than relying on credential absence; add SAST, dependency-vulnerability audit, licence gate
(allow-list = permissive + MPL-2.0), and a machine-generated SBOM from `uv.lock`; enable branch
protection with required checks.

**DONE looks like:** CI runs on the target host with pinned inputs and a hermetic test job.

**Verify:**

```bash
grep -c 'uv sync --frozen' <enterprise-clone>/<ci-definition>                       # → 5
grep -rnE '@v[0-9]+$' <enterprise-clone>/.github/workflows/ 2>/dev/null              # → 0 (if D9 = GHES)
```

**Boundary:** one session. Close out.

**Scope moved out of this phase, §1.3:** the original text bundled a **generated projects' CI**
code change here (parameterising `governance_templates.py`) that touches only this repository's
own source, not the clone, and has no dependency on D9/D15/C4. Bundling it into a now-clone-only
phase would strand it behind a gate it never needed. It is extracted below as Phase C3b, unblocked
and independently schedulable.

---

### Phase C3b — Generated-project CI portability *(independent of the fork — no gate; extracted from the original C3 by §1.3)*

**DONE (Session 205, 2026-07-29).** New frozen `CIHostConfig` dataclass (`base_image`, `index_url`,
`action_prefix`, `pre_commit_repo` — all default to today's public values) in
`governance_templates.py`, threaded through `render_gitlab_ci`/`render_github_actions_ci`/
`render_pre_commit_config`/`build_governance_files` → `WebsiteState`/`scaffold_governance` →
`WebsiteAgent` (constructor kwarg) → the website agent CLI (`--ci-base-image`/`--ci-index-url`/
`--ci-action-prefix`/`--ci-pre-commit-repo`) → `scripts/run_pipeline.py` (new
`build_ci_host_config()`, reading `MPC_CI_BASE_IMAGE`/`MPC_CI_INDEX_URL`/`MPC_CI_ACTION_PREFIX`/
`MPC_CI_PRE_COMMIT_REPO` directly from the environment, matching the existing `MPC_HOST_URL`
direct-read pattern rather than `OrchestratorSettings`, since `ci_platform` itself never flowed
through that settings object either). Verify block below re-run and passed: a fake-mode run with
all four env vars set produced zero `docker.io|python:3.11|github.com/` matches across all 39
generated files, and the same run with the env vars unset still showed the public values in exactly
`.github/workflows/ci.yml` and `.pre-commit-config.yaml` (proving the check isn't vacuous).
989 tests pass (added 15 new: `CIHostConfig` defaults/overrides/integration in
`test_governance.py`, CLI flag threading in `test_cli.py`, env-var threading (fake AND live modes)
in `test_run_pipeline_adapter.py`), `mypy --strict` and `ruff` clean. Two independent adversarial
review passes ran before commit: a correctness/regression lens (no issues; confirmed byte-identical
default output via `git stash` diff and validated the new GitHub Actions `env:` block with
`yaml.safe_load`) and a test-coverage lens (found and closed 3 real gaps — live-mode env threading
was untested, no test isolated a single-field override from its untouched siblings, and no CLI test
covered a partial (not all-four, not zero) flag combination).

**Gated on:** nothing. This phase touches only this repository's own pipeline-generator source and
can run at any time, before or after the fork, in any order relative to A–C.

**Scope:** parameterise `governance_templates.py` on base image, index URL, action prefix, and
pre-commit repo (defaults = today's public values), thread them from `WebsiteAgent`/`cli.py`, with
paired tests — so that projects the pipeline generates can target enterprise-internal hosts when
configured to, instead of hardcoded public ones (Docker Hub, GitHub Actions marketplace, PyPI).

**DONE looks like:** generated projects reference only enterprise-internal hosts when the relevant
env is set, and still default to today's public values when it is not.

**Verify:**

```bash
uv run python scripts/run_pipeline.py --fake                      # with the enterprise env vars set
grep -rn 'docker.io\|python:3.11\|github.com/' <generated-project>/   # → 0
uv run pytest -q && uv run mypy
```

**Boundary:** one session. Close out.

---

### Phase C4 — Enterprise clone provisioning

**Gated on:** **A1–A4 complete** (done), **B1's D3-independent core complete** (done, Session 190),
and **B2 complete** (done, Session 195 — **this phase's gate is now fully satisfied**, pending only
the live D9/D5/D4/D8/D16 answers below). **D4, D5, D8, D9, D16 no longer gate this phase** — per
§1.3, the operator resolves them post-fork, inside the clone, and supplies whatever this phase's
mechanics need live (notably, a destination host URL for step 1) at execution time. *(A1–A4 and
B1's core remain explicit per §1.2 — the clone is one-time and does not sync; anything not fixed on
the original before this phase runs is permanent in the clone. B2 is required because this phase
consumes its `releases-export.json` and external-asset register (now at
`audits/2026-07-28-b2-import-readiness.md`).
C1/C2/C2b/C3 are deliberately **not** gates — see dragon #20's scoping note: they are
enterprise-readiness fixes that can be applied to the original before the fork or, per §1.3, are
now definitively deferred to the clone, at the cost of having to do them there instead, since there
is no sync.)*

**Before step 1 — confirm the live inputs §1.3 deferred, do not assume the plan's recommendations
were adopted as written:** D9 (destination host — needed for `<enterprise-remote>` below), D5
(import as-is vs. squash-import — changes step 1's mechanics, not just its target), D4 (signed
commits/DCO — may require re-authoring commits before the push, not after), **D8** (wiki
destination host and naming/sidebar convention — needed by steps 3, 4, and 7 below, all in this
same session), and **D16** (recreate-vs-pointer for the two GitHub Releases — needed by step 8
below; see dragon #24). Get explicit answers from the operator at the start of this session; do not
silently default to the plan's §3 recommendations, since §1.3 means those were never confirmed as
decisions.

**Scope — fork FIRST; every edit below happens only inside the resulting enterprise checkout,
never in the current working tree, and nothing here is ever committed or pushed to the original's
`origin`:**

1. **Fork the main repo (one-time, no ongoing sync):** `git clone --mirror` **the public `origin`**,
   never a filesystem copy (a folder copy carries `.env`, the checkpoint store with three live
   GitLab project URLs, `intake_sessions.db`, and 8 dropped-stash commits). Push the mirror with
   `git push --mirror <enterprise-remote>` (this already carries tags — no separate tag push
   needed). **The public `origin` is read-only for this operation — nothing about it changes.**
2. **Create the working checkout.** The mirror pushed in step 1 is bare — nothing in it can be
   edited, and a bare repo breaks both `git grep` (no revision to search without one) and any
   command referencing a file path inside it. Clone it normally:
   `git clone <enterprise-remote> <enterprise-clone>`. **Every `<enterprise-clone>` reference below,
   and in this phase's Verify block, means this working checkout — never the bare mirror.**
3. **Fork the wiki repo — it is a second, independent repository with 33 commits:**
   ```bash
   git clone --mirror https://github.com/rmsharp/claims-model-starter.wiki.git /tmp/wiki-mirror
   # ⚠ On GitHub/GHES the target wiki repo does not exist until one page is created via the web UI.
   git -C /tmp/wiki-mirror push --mirror <enterprise-wiki-url>
   # /tmp/wiki-mirror is a scratch clone for this push only — it is NOT
   # ~/Development/claims-model-starter.wiki, which stays wired to the original (dragon #21).
   ```
   Then clone the new enterprise wiki remote to `<new-wiki-clone>` as the working copy the
   remaining wiki steps operate on.
4. **Inside `<enterprise-clone>` only, parameterise `publish_wiki.sh`'s six coupling points —
   fail-closed, NOT "today's values as defaults".** `WIKI_CLONE`, `WIKI_REMOTE_PATTERN`,
   `WIKI_BRANCH`, `WIKI_PUSH_REFSPEC` must be required (`${WIKI_CLONE:?set WIKI_CLONE for the target
   wiki}`), so an unset environment aborts instead of silently publishing enterprise content into
   the **original's** public wiki. Also fix the hardcoded clone-URL text at
   `scripts/publish_wiki.sh:23,63` (comment + error text) — left as-is, it survives the C5
   independence check unnoticed. **Do NOT delete or re-remote
   `~/Development/claims-model-starter.wiki`** — it continues to serve the original's live
   auto-publish (D6: refresh and keep) and must keep working unchanged. Point `WIKI_CLONE` at
   `<new-wiki-clone>` (step 3) instead, and verify with `git -C "$WIKI_CLONE" remote get-url origin`
   before the first commit in the clone touches `docs/wiki/`.
5. **Inside `<enterprise-clone>` only:** update `mkdocs.yml:3-5`, `README.md:9`, the
   **`config.py:198,354-366` error-message namespace** (+ its 5 asserting tests),
   `.env.example:25-30`, `OPERATIONS.md:25`, `docs/tutorial.md:427,445-447`, and
   `Contributing.md:19,236,238`. Re-derive with the §2.6 rediscovery command rather than trusting
   the table. **These are clone-only edits — committing or pushing them to the original's `origin`
   would alter the still-live public site (§1.2).**
6. **Inside `<enterprise-clone>` only:** update the **prose** documenting the mechanism —
   `SESSION_RUNNER.md:209` and `Contributing.md:122`.
7. **If D8's destination is not a GitHub-family wiki:** convert `_Sidebar.md` to the host's sidebar
   convention, rename `Home.md` to the host's landing page, and rewrite the **157** extensionless
   intra-wiki links (`grep -rhoE '\]\([A-Za-z0-9][A-Za-z0-9-]*\)' docs/wiki/claims-model-starter/ | wc -l`).
8. **Recreate both GitHub Releases on the target host from `releases-export.json`, OR leave them as
   a pointer to the public originals — whichever the operator confirmed live for D16 before step 1
   (see the preamble above and dragon #24). Do not default to "recreate" from the §3 Recommendation
   column** — Phase B2 (§4) lists this asset explicitly as "genuinely undecided," and Phase C5
   step 3 records whichever branch was actually taken, which is only possible if this step didn't
   silently pre-empt the choice.
9. **Execute the external-asset register from B2** (`audits/2026-07-28-b2-import-readiness.md` §3),
   **minus the wiki repo and the gh-pages site** — their disposition is fixed (keep, unconditionally;
   §1.2/D6/§6). **Confirm the disposition of the three GitLab pilot projects with the operator**
   (`subrogation-pilot`, `-v2`, `-v3`, project IDs and URLs in the register's §3.2) — B2's register
   lists them as a genuinely undecided asset alongside the Releases, and this plan does not itself
   recommend migrate-vs-leave for them; do not treat their absence from this step's original text as
   "no action needed."
   **Provision `<enterprise-clone>`'s runtime config with enterprise-owned credentials — do not
   copy the personal `.env`.** *(Corrected, §1.4: rotating the personal Anthropic key, GitLab PAT,
   or Bedrock bearer token is neither required nor sufficient here — step 1's `git clone --mirror`
   already carries zero credential values, so there is no dependency to break by rotating. What
   this step actually requires: populate `<enterprise-clone>`'s `.env` (or the destination host's
   CI/CD secret variables) with an org-issued Anthropic key, a token scoped to the enterprise
   GitLab instance/service account, and whatever auth the enterprise AWS account uses for Bedrock
   — and confirm no one has manually copied the operator's personal `.env` in as a shortcut.)*

**DONE looks like:** the enterprise remote carries the full history, both tags, and the 23-page
wiki; `<enterprise-clone>` is a normal (non-bare) working checkout; nothing in the clone's tree
points at the personal account, including the hardcoded strings in `publish_wiki.sh`; the clone's
publish script cannot target the public wiki; **the original repo, wiki, and site are untouched and
continue operating exactly as before this phase.**

**Verify:**

```bash
git -C <enterprise-clone> rev-list --count HEAD          # → matches the source
git -C <enterprise-clone> rev-parse --is-bare-repository # → false (a working checkout, not the mirror)
git ls-remote --tags <enterprise-remote>                 # → both tags
git -C <new-wiki-clone> log --oneline | wc -l            # → 33
git -C <new-wiki-clone> ls-files | wc -l                 # → 23
git -C <enterprise-clone> grep -n -I -iE 'rmsharp|rmsharp\.github\.io|github\.com/rmsharp|claims-model-starter' -- . \
  | grep -vE '^(SESSION_NOTES|CHANGELOG|PROJECT_LEARNINGS)\.md|^docs/architecture-history/'   # → 0 (full §2.6 pattern — do not narrow it)
WIKI_CLONE= <enterprise-clone>/scripts/publish_wiki.sh; echo "exit=$?"   # → non-zero (fails closed)
git -C ~/Development/claims-model-starter.wiki remote get-url origin    # → unchanged, still the public wiki
```

**Boundary:** one session, plus operator actions outside git.

---

### Phase C5 — Fork independence verification

**Gated on:** C4 complete. **D16 no longer gates this phase** — per §1.3, D16 is resolved post-fork,
inside the clone; step 3 below records whatever the operator decided live rather than gating on a
pre-written §3 answer.

**Scope:** confirm the enterprise clone is fully independent and the public originals are
untouched. Per §1.2, this phase does the **opposite** of its original scope (decommission) — the
public repo, wiki, and MkDocs/gh-pages site are not retired.

1. **Independence check on the clone:** re-run C4's rediscovery grep **inside the enterprise
   clone** — confirm zero hits outside the historical-record exclusions, and confirm the clone's
   `publish_wiki.sh` / `.githooks/post-commit` cannot resolve to the personal wiki even with an
   unset environment (dragons #20, #21).
2. **Non-regression check on the originals:** confirm the public site still serves the tutorial,
   `~/Development/claims-model-starter.wiki` still points at its original remote and was not
   touched by C4, and `origin/gh-pages` / `publish-tutorial.yml` on the **original** repo are
   unchanged from their A4 state.
3. **Record the D16 disposition inside `<enterprise-clone>` only** (its own README or governance
   doc, not this repository's `SESSION_NOTES.md`/`BACKLOG.md`/this plan — §1.3's "not reported back
   to this repository" applies to D16 same as the rest of the deferred bucket): access model
   (private from creation, by default), administrator/owner, and whether the two GitHub Releases
   were recreated on the clone (C4) or left as a pointer.

**DONE looks like:** the clone has no live path back to the personal account or the public repo;
the public repo/wiki/site are confirmed unchanged and still serving; the D16 disposition is applied
and recorded for the clone.

**Verify:**

```bash
# clone independence — full §2.6 pattern; do not narrow it (a narrower pattern can pass "→ 0"
# while a hardcoded `claims-model-starter` string survives in the clone's publish_wiki.sh)
git -C <enterprise-clone> grep -n -I -iE 'rmsharp|rmsharp\.github\.io|github\.com/rmsharp|claims-model-starter' -- . \
  | grep -vE '^(SESSION_NOTES|CHANGELOG|PROJECT_LEARNINGS)\.md|^docs/architecture-history/'   # → 0
WIKI_CLONE= <enterprise-clone>/scripts/publish_wiki.sh; echo "exit=$?"        # → non-zero (fails closed)

# original non-regression — none of this should differ from A4's verified state
curl -s -o /dev/null -w '%{http_code}' https://rmsharp.github.io/claims-model-starter/tutorial/   # → 200 (still live)
git ls-remote origin gh-pages                                                # → still populated
git -C ~/Development/claims-model-starter.wiki remote get-url origin         # → unchanged, still the public wiki
gh repo view rmsharp/claims-model-starter --json isPrivate,archived           # → false, false (untouched)
```

**Boundary:** one session. Close out. **This is the last phase — after it, goal 3 is complete.**

---

## 5. Here be dragons

1. **Pushing `master` IS publishing.** No approval gate, no environment protection,
   `permissions: contents: write`, `gh-deploy --force --clean`. An executor who sequences "push,
   then clean up docs" has already published. **This is why A1 precedes A4.**
2. **The publish trigger and the publish scope are decoupled in opposite directions.** Editing
   `docs/deployment/bedrock-enterprise.md` triggers nothing — so it looks safe — and then goes
   live on the next unrelated deploy. Never reason about what the site publishes from the
   workflow's `paths:` list; determine it from `docs_dir` + `exclude_docs`, and **verify by
   building from a clean `git archive` with `--extra docs`**.
3. **The wiki auto-publish hook is armed right now and pushes to a *personal public* repo.** Any
   commit touching `docs/wiki/claims-model-starter/` rsyncs and pushes with no confirmation.
   **`export MPC_SKIP_WIKI_PUBLISH=1` does not work** — each Bash call is a fresh shell. Use the
   standing rule in §4. This bites in **A1 and A3 too**, not just A2.
4. **`rsync -a --delete` silently destroys web-UI wiki edits.** Editing the wiki through the web
   UI during the migration is a natural thing to do — and the next local commit deletes it.
5. **Never run `publish_wiki.sh` from a `master` checkout before A4 lands.** The live wiki is
   published from `a1d8af7`, which exists only on the branch. Running it from `master` mirrors
   master's older wiki over the live one and **regresses 20 pages** — and reports success. The
   guard must be `&&`-chained: `git merge-base --is-ancestor` prints nothing on failure.
6. **The merge will not publish the wiki.** A fast-forward creates no commit, so `post-commit`
   never fires; `post-merge` does not exist. The 20 pages land on `master` and the live wiki is
   untouched. It *happens* to already be correct, which makes the silent no-op harder to notice.
7. **A bulk replace on the wiki corrupts nine correct rows.** Of the 12 `sonnet-4-6` lines, only 3
   change; the rest document the first-party default, which really is `claude-sonnet-4-6`. And two
   lines that *match* the canonical sweep grep — `AI-Dependencies.md:151`, `Schema-Reference.md:632`
   — are unrelated uses of "in-flight" and must not be touched. Read every site in context.
8. **Line numbers shift as you sweep.** Work **bottom-up per file** and re-grep after each.
9. **A1–A3 commits are local only.** If A4 opens the PR without pushing the branch first, CI tests
   the *pre-A1* tree, shows green, and then step 2 pushes an untested tree straight to `master` —
   defeating the plan's central safety claim. **Push the branch and assert parity first.**
10. **GitHub has no fast-forward merge button.** All three merge methods either create the repo's
    first merge commit or rewrite all 25 SHAs. Land by push only.
11. **`--cov-fail-under=95` turns any un-tested wiring change into a red build that looks
    unrelated.** Budget paired tests for both package copies with every hook change.
12. **A history rewrite silently breaks the project's institutional memory.** `SESSION_NOTES.md`
    and `CHANGELOG.md` cite dozens of SHAs. `filter-repo` invalidates all of them with no error.
13. **A green `pytest -m live` in the enterprise proves nothing.** The credential probe cannot see
    IRSA/ECS/instance-profile auth, so every live case skips and pytest exits 0. Prove the run
    happened (`-rs`, non-zero run count) before treating it as validation. **The inverse also
    holds:** a corporate runner with an OIDC AWS chain un-skips the tier and makes paid calls.
14. **`git ls-files .env` returning empty is not proof.** It says nothing about history. Use the
    history-wide object scan — **after a `git fetch`**, or the scan misses refs.
15. **`origin/gh-pages` in this clone is stale.** `git fetch` before reasoning about what is
    public. `origin/master` *is* current, which makes the inconsistency invisible.
16. **The merged history will contain a literal `[WIP]` commit** (`dadf514`). Rewording it
    rewrites 16 SHAs. Check `git grep dadf514` first; prefer accepting it with a rationale.
17. **`SESSION_NOTES.md` is dirty during a session and differs between `master` and the branch.**
    Commit or stash it as step 0 of A4, and use **path-scoped `git add`, never `-a`** (learning #143).
18. **The `gh` token cannot do security or org work** — no `security_events`, no `admin:org`.
19. **"Defaults = today's values" is the wrong shape for `publish_wiki.sh`.** After C4, an unset
    environment must **abort**, not fall back to the personal public wiki.
20. **The one-time fork has no future sync.** Whatever is wrong in the public repo at the moment
    C4 clones it is baked into the proprietary copy permanently — there is no later pull to carry a
    fix over. This is why C4 is gated on A1–A4, B1's D3-independent core, and B2 complete — **not
    its D-items** (§1.3 formally removed D4/D5/D8/D9/D16 as C4 gates; they resolve post-fork,
    inside the clone, per the operator's 2026-07-27 decision). Cloning early "to get started" would
    still silently ship every not-yet-fixed defect of the **legal/exposure/asset-availability**
    kind (stale docs, the live exposure, the licensing conflict) into the thing meant to be the
    clean enterprise copy — that risk is exactly why A1–A4/B1-core/B2 remain hard gates even though
    the D-items no longer are.
    **This logic applies just as much to C1/C2/C2b/C3's enterprise-readiness gaps** (the false
    `ANTHROPIC_BASE_URL` claim, the `require_sigv4` hole, the unauthenticated intake UI, the
    hardcoded-public-registry CI) — they were already **not** gates on C4, on the scoping choice
    that they are ordinary code/config fixes an operator can apply to the original before the fork
    or to the clone after it. §1.3 resolves that choice to "after, inside the clone" for the
    sub-tasks whose only gate (D14 or D15) is in the deferred bucket — C2b entirely, and one
    sub-task each from C1 and C2 (§4). Only the items with a legal/exposure/asset-availability
    character (A1–A4, B1-core, B2) are hard gates on C4; C1/C2's D10/D13-scoped work and C3's
    clone-only work remain schedulable, just no longer blocking or blocked by the fork itself.
21. **`~/Development/claims-model-starter.wiki` is the ORIGINAL's live publish target, not a
    migration scratch directory.** It is tempting to repurpose or re-remote it while provisioning
    the enterprise wiki — doing so silently breaks the original's still-live auto-publish (D6:
    refresh and keep, not retire). Create a separate local clone for the enterprise wiki instead.
22. **§1.3 removed written answers for D3–D9 and D14–D16 from this document — it did not remove
    the need for those answers to exist before the phase that needs them runs.** C4 still needs a
    destination host (D9) and an import strategy (D5) before its first git command; C3 still needs
    D9 to pick a scope branch; C1/C2b still need D14 for the IAM trust policy and deployment
    artifact. The executor's job changed from "read §3" to "ask the operator, live, at session
    start" — do not silently fall back to the §3 **Recommendation** column text as if it were a
    ratified decision. Those columns are preserved as context for whoever eventually answers the
    question, not as a default.
23. **A narrowed phase's DONE criteria are not the original phase's DONE criteria.** §1.3 split
    C1 and C2 in two — a live scope (D10/D13) and a deferred scope (D14/D15) — and left C2b and the
    generated-projects-CI sub-item as fully separate concerns. A future session that runs the
    narrowed C1 or C2 and checks their (also narrowed) Verify blocks has **not** produced the IAM
    trust policy, the deployment artifact, or the D15 index documentation — those remain explicitly
    open, tracked in §1.3 and the phase text itself, not silently satisfied by adjacent work.
24. **A recommendation the operator never confirmed is not a default — even where the original
    plan text (predating §1.3) already reads as an imperative.** Phase C4 step 8 (original,
    Session-182 text) unconditionally said "recreate both GitHub Releases" — silently enacting D16's
    §3 Recommendation column as if it had been ratified, even though Phase B2 lists the same asset
    as "genuinely undecided" and §1.3 places D16 in the deferred, resolved-live bucket. This is
    exactly the failure mode dragon #22 warns about, just easy to miss because the sentence reads
    as a normal scope item rather than a decision point. Before executing *any* single-branch
    imperative sentence in Phases C4/C5 that happens to match a §3 Recommendation for a deferred
    D-item, stop and ask whether the operator actually confirmed it live this session — the
    sentence having always read that way is not evidence that it was confirmed.

---

## 6. Out of scope / explicit non-goals

- **Executing any phase.** This plan is the deliverable of Session 182 (revised by Session 194,
  §1.3).
- **Choosing the licence, the IP disposition, the host, the runtime shape, or the package index.**
  D1, D2 are answered (§3). **D3–D9 and D14–D16 are, per §1.3, not this repository's decisions to
  track at all** — the operator resolves them post-fork, inside the enterprise clone, and the
  outcome is not reported back here. D10, D13 are the live operator/security decisions this plan
  frames and recommends on — **D10 answered (Session 199, 2026-07-29): Regional** (§3 Decision
  Register, Phase 0); **D13 resolved (Session 200, 2026-07-29)** — its `require_sigv4` sub-scope
  only, not `http_client` (§3 Decision Register). `bedrock-enterprise.md` §0's three security
  questions are **answered too (Session 201, 2026-07-29)** — Guardrails no, FIPS no, runtime quota
  expected-yes-unverified. **Nothing D-numbered or §0-numbered remains open in this bucket.** The
  one loose end anywhere in the security bucket is Q3's independent verification (live Service
  Quotas / Workbench `ping`), which needs the actual enterprise account and is carried forward as a
  flag, not a blocker.
- **Re-planning the httpx/LGPL migration** — it already exists in executable form; B3 references
  and corrects it. **B3 is now fully executed** (both LGPL SDKs removed — see `CHANGELOG.md`
  2026-07-28).
- **The `bedrock-runtime` fallback path.** If Guardrails or FIPS are mandated, the client class,
  IAM actions, and model-id form all change — that is a re-plan, not a phase.
- **Live Bedrock validation from this repository.** Still environment-blocked, and — per §1.3 —
  now expected to stay that way: C2b (the deployment artifact live validation would run from) is
  out of scope here (§4), so the unblock happens in the enterprise clone, on its own timeline, not
  as a critical path this plan tracks.
- **Rewriting historical records.** `SESSION_NOTES.md`, `CHANGELOG.md` entries,
  `docs/architecture-history/` and the historical wiki pages stay as written — **with one
  documented exception**: `docs/architecture-history/methodology-pr2527-remediation-mpc.md` is in
  scope for D1, because it reproduces third-party material verbatim.
- **Decommissioning, archiving, or otherwise altering the public repo, wiki, or MkDocs/gh-pages
  site.** Confirmed by the operator (§1.2): they continue to exist, unchanged, indefinitely. Only
  the one-time enterprise clone is provisioned (C4) and verified independent (C5).

---

## 7. Final acceptance — goals 1 and 2

All must hold after Phase A4:

```bash
git rev-list --count origin/master..feat/bedrock-mantle-migration          # → 0
git ls-remote origin master                                               # → branch tip SHA
git log --merges --oneline | wc -l                                        # → 0
gh run list --workflow ci.yml --limit 1                                   # → success, not cancelled
diff -r -x '.git' docs/wiki/claims-model-starter ~/Development/claims-model-starter.wiki   # → identical
git -C ~/Development/claims-model-starter.wiki status -sb                 # → no "[ahead N]"
grep -rniE "unmerged|feat/bedrock-mantle-migration|not[- ]yet[- ]merged|branch-only|branch only|in[- ]flight|on the branch|last session on|the branch lands|when it lands|has not been merged" \
  docs/wiki/claims-model-starter/ | cut -d: -f1,2 | sort -u
#   → exactly AI-Dependencies.md:151 and Schema-Reference.md:632
for p in $(grep -rhoE '`?docs/(audits|planning|architecture-history)/[A-Za-z0-9._/-]+\.md' \
            docs/wiki/claims-model-starter/ | tr -d '`' | sort -u); do
  [ -e "$p" ] || echo "DEAD WIKI PATH REFERENCE: $p"
done                                                                      # → no output
curl -s https://rmsharp.github.io/claims-model-starter/sitemap.xml | grep -c audits   # → 0
uv run pytest -q && uv run ruff check src/ tests/ packages/ scripts/ && uv run mypy
```

**Goal 3, revised scope for this repository (§1.3, supersedes the original "D1–D16 answered"
criterion):** completes when B1's D3-independent core (done), B2 (done, Session 195), B3 (done), C1 and C2 in their
narrowed D10/D13-scoped form, C3, C3b, C4, and C5 — **in its revised form (fork-independence
verification, §1.2, not the original decommission scope)** — all close. **C3, like C4/C5, stays a
session this repository schedules even though its edits land inside `<enterprise-clone>`** — it
needs D9/D15 supplied live by the operator at that session's start (§4), not a pre-written §3
answer, the same pattern C4 uses for D9/D5/D4. **Explicitly excluded from this repository's Goal 3,
per §1.3:** full Phase B1 (the DCO/CLA mechanism), C2b, and the D14/D15-dependent sub-tasks carved
out of C1/C2 (the IAM trust policy, the D15 index documentation) — these are genuinely stranded,
not merely deferred, because their one gate (D14 or D15) is never answered in a form this
repository can act on, and are never expected to close inside this repository's tracked history.
**B1's D3-independent core is the gate: do not push to a corporate host until the third-party
methodology rights conflict is resolved in writing** (already done, Session 190).
