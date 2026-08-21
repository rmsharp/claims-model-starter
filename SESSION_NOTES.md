# Session Notes

**Purpose:** Continuity between sessions. Each session reads this first and writes to it before closing out.

**Fourth trim (Session 231). Archived Sessions 227 → 225 — 3 record headings, 738 lines** into
[`docs/architecture-history/SESSION_NOTES-S227-through-S225.md`](docs/architecture-history/SESSION_NOTES-S227-through-S225.md)
— same shape, same newest-on-top order, frozen and byte-for-byte unedited. **This live file now
holds Sessions 231 → 228 only** — four sessions, the floor `CLAUDE.md` sets. Its proof is
[`SESSION_NOTES-S227-through-S225.md.verify.sh`](docs/architecture-history/SESSION_NOTES-S227-through-S225.md.verify.sh):
the eight assertions inherited from the third trim plus **L8** (the three copies of the shard set
that no earlier proof could reach — `README.md`'s repo map, the shard-naming rule in
`docs/methodology/PROJECT_CONVENTIONS.md`, and `BACKLOG.md`'s read-cap item, which the third trim's
own sentence did not know was making the same claim — **and `CLAUDE.md`'s prose**, whose routing
table L5 always parsed while its *"there are THREE"* count words were read by nothing) and **L9**
(write-once enforced for
**every** shard on disk, not only the newest — L7 has only ever guarded the shard it shipped with,
so the S216 and S220 shards have never had any enforcement at all, and the S224 shard's lives only
inside its own proof, which nothing obliges a session to run).

**Four shards exist now, and none is a prefix of any other.** To place Session N, open the file
this table names. **This block is the authority**, and these five clauses are machine-checked here,
in the shard's banner, and in `CLAUDE.md`:

**N ≤ 216** → `SESSION_NOTES-through-S216.md`; **217 ≤ N ≤ 220** → `SESSION_NOTES-S220-through-S217.md`;
**221 ≤ N ≤ 224** → `SESSION_NOTES-S224-through-S221.md`; **225 ≤ N ≤ 227** → `SESSION_NOTES-S227-through-S225.md`;
**N ≥ 228** → `SESSION_NOTES.md`.

`grep` the shards; `Read` none of them. **Shards stay write-once** — a fifth trim writes a fifth
file; it never appends to one of these four.

**Two shard banners are stale now, and neither may be repaired.** The S220 shard's still says *"the
live ledger when N ≥ 221"*; the S224 shard's still routes Sessions 225 and up to this file. Both
were true at their own cut. The S220 proof predates L5 and cannot notice; the S224 proof has L5 but
reads its artifacts at its own trim commit, so it cannot notice either — and ours will join them at
the fifth trim. **A shard banner is a snapshot of its own cut; this block is the authority.** What is
no longer true is that `README.md` and `docs/methodology/PROJECT_CONVENTIONS.md` sit beyond every
proof's reach: **L8 holds them — and `BACKLOG.md` with them**, a third copy that sentence never
named, found by sweeping for the class instead of trusting the list. **Sweep again at the fifth
trim rather than trusting this list either**; `git grep -l 'SESSION_NOTES-'` is the whole sweep and
it takes a second. A fifth trim that leaves any of the four files L8 reads alone fails a proof
instead of quietly shipping a lie.

**The three blocks below are frozen at the THIRD, SECOND and FIRST trims and describe THOSE cuts.**
This trim falsified exactly four passages of the third trim's block — its claim about which sessions
this live file holds, its whole routing paragraph, the sentence putting `README.md` and
`PROJECT_CONVENTIONS.md` beyond every proof's reach, and its parenthetical calling **L7** the only
enforcement write-once has ever had, which **L9** has now made false — and rewrote all four as
declared substitutions the proof checks by exact equality. Every other byte of that block is original, and the second and first trims' blocks
are untouched. Each earlier proof reads its artifacts from the commit that added its own shard, so
this trim cannot disturb any of them; all three were re-run green at this cut, and a session that
doubts that should run them rather than reason about it.

**Third trim (Session 228). Archived Sessions 224 → 221 — 4 record headings, 891 lines** into
[`docs/architecture-history/SESSION_NOTES-S224-through-S221.md`](docs/architecture-history/SESSION_NOTES-S224-through-S221.md)
— same shape, same newest-on-top order, frozen and byte-for-byte unedited. At that third cut
this live file was left holding Sessions 228 → 225 — four sessions, the floor `CLAUDE.md`
sets; the fourth trim above has since cut it again. Its proof is
[`SESSION_NOTES-S224-through-S221.md.verify.sh`](docs/architecture-history/SESSION_NOTES-S224-through-S221.md.verify.sh):
the five inherited assertions plus **L5** (the table below, clause by clause — the numbers against
the cut key, the filenames against what those files actually hold), **L6** (the shard's banner
pinned byte-for-byte) and **L7** (that shard still being, on disk today, the bytes the proof was
written about — which was, until the fourth trim's **L9** extended the same check to every older
shard, the only enforcement `write-once` had ever had).

**Three shards existed at that cut, and none was a prefix of any other.** The routing table that
stood here named those three and sent every session from 225 up to this live file; the fourth trim
falsified that last clause — Sessions 227 → 225 are in a shard now — and the table above replaces
it. `grep` the shards; `Read` none. **Shards stay write-once** — a fourth trim wrote a fourth file;
it did not append to one of those three.

**A copy of that table inside a write-once file goes stale at the next cut and cannot be repaired.**
The S220 shard's banner still says *"the live ledger when N ≥ 221"*, which this trim falsified; its
proof predates L5 and will never notice. Treat every shard banner as a snapshot of its own cut. Two
further copies were named here as outside every proof — `README.md`'s repo map and the shard-naming
rule in `docs/methodology/PROJECT_CONVENTIONS.md` — and a trim that left either alone shipped a lie.
There was a third nobody had named: `BACKLOG.md`'s read-cap item, carrying the same count. The
fourth trim's **L8** checks all three.

**The two blocks below are frozen at the SECOND and FIRST trims and describe THOSE cuts.** This
trim falsified exactly two sentences of the second trim's block — its claim about which sessions
this live file holds, and its whole routing paragraph — and rewrote both as declared substitutions
the proof checks by exact equality. Every other byte of that block is original, and the first
trim's block is untouched. Each earlier proof reads its artifacts from the commit that added its
own shard, so this trim cannot disturb either; both were re-run green at this cut, and a session
that doubts that should run them rather than reason about it.

**Second trim (Session 224). Archived Sessions 220 → 217 — 5 record headings, 774 lines** into
[`docs/architecture-history/SESSION_NOTES-S220-through-S217.md`](docs/architecture-history/SESSION_NOTES-S220-through-S217.md)
— same shape, same newest-on-top order, frozen and byte-for-byte unedited. At that second cut
this live file was left holding Sessions 224 → 221 — four sessions, the floor `CLAUDE.md`
sets; the third trim above has since cut it again. Its proof is
[`SESSION_NOTES-S220-through-S217.md.verify.sh`](docs/architecture-history/SESSION_NOTES-S220-through-S217.md.verify.sh):
four inherited assertions plus an L4 pinning the cut point, its own key, its own `--self-test`.

**Two shards existed at that cut, and neither was a prefix of the other.** The routing table that
stood here named only those two and sent everything newer to this live file; the third trim
falsified every clause of it, and the table above replaces it. `grep` the shards; `Read` none.
**Shards are write-once** — a third trim writes a third file, it does not append.

**The block immediately below is frozen at the FIRST trim and describes THAT cut, not this one.**
This trim falsified exactly two of its sentences and rewrote both, as declared substitutions the
proof checks by exact equality; every other byte of that block is original. They were: its claim
that this live file holds Sessions 222 → 217, and its claim that Session 216's handoff evaluation
"stayed here" — Session 217's record, which carries that evaluation, is now in the S220 shard. That
block's own proof reads its artifacts from commit `a9510ca`, so this trim cannot disturb it; it
still runs green today, and a session that doubts that should run it rather than reason about it.

**Archived Sessions 216 → 1 — 206 record headings, 24,564 lines** into
[`docs/architecture-history/SESSION_NOTES-through-S216.md`](docs/architecture-history/SESSION_NOTES-through-S216.md)
— same format, same newest-on-top order, frozen, byte-for-byte unedited. At that first cut this
live file was left holding Sessions 222 → 217; the second trim above has since cut it again.

**`grep` that shard; never `Read` it.** It is 24,564 lines — an agent `Read` truncates at 2,000
lines with no error and no missing-data marker, which is the defect this archive exists to remove.
Nothing watches the shard for that (`methodology_dashboard.py`'s `READ_CAP_WATCHED` is an exact-path
set holding only `SESSION_NOTES.md`, `CHANGELOG.md`, `HANDOFFS.md` and the backlog locations), so
this paragraph is the only warning there is.

**Losslessness is proved, not asserted.** Run
[`docs/architecture-history/SESSION_NOTES-through-S216.md.verify.sh`](docs/architecture-history/SESSION_NOTES-through-S216.md.verify.sh)
— it re-derives L0 (footer declaration), L1 (records-zone concatenation), L2 (zone pinning) and L3
(record partition) from git, and exits non-zero on failure; `--self-test` proves the proof itself can
fail. Do not trust this sentence, and do not trust a digest — run it. **The cut is by byte position,
not by authorship:** Session 216's own handoff evaluation is filed inside Session 217's record,
because this file files an evaluation under its author. Expect that seam at every trim boundary.

---

## ACTIVE TASK

### What Session 234 Did
**Deliverable:** **Phase 5 of [`docs/planning/repository-rename.md`](docs/planning/repository-rename.md)
— COMPLETE. The plan is CLOSED and its backlog item is gone.** Every check in §7 passes, including
§7.4's three surfaces no `git grep` at `HEAD` can reach. **This was the last phase; there is no
Phase 6.** No other work was started.

**Started / completed:** 2026-08-20. **Commits: three** — `a707a9e` (the Phase 1B claim, alone),
`efc24a6` (the whole phase, one commit), and this close-out. **Operator this session:** *"phase 5"*.

Documentation and path strings only, so **no `CHANGELOG.md` entry** — §5 of the plan settles this on
`PROJECT_CONVENTIONS.md` §2's cadence gate. **Nothing published**: the phase touches no
`docs/wiki/model_project_constructor/` file, so `.githooks/post-commit` correctly did not fire, and
the wiki clone is still at `d85cc67` where Phase 4 left it — a live negative control, second session
running.

#### What changed — one commit, three files

| Thing | Detail |
| --- | --- |
| `enterprise-migration.md` | the **3** residue lines `:919`, `:1250`, `:1372` → new name. **§7.2 (ii) is now EMPTY**, which is the criterion Phase 5 exists to satisfy. `:1372` also took `archived` → **`isArchived`** — §9.1 filed that as "one word, fix it whenever the line is next touched", and this phase touched it |
| `BACKLOG.md` | the rename item **deleted, not substituted** — 262 lines + its plain-language index row. **Six new items filed**: §8.1's four (each re-verified at `HEAD`, not copied forward), the re-filed operator-decision flag, and one new finding |
| `repository-rename.md` | status line → **EXECUTED**; §3.2(c)'s count 25 → **24**; Session 232's defect #1 discharged in dragon 2 + §7.3 (blocks left byte-identical); dragon 9's stale push line struck; **six** dangling `BACKLOG.md` pointers repaired; new **§9.2** reconciliation log |
| out of repo, no commit | `~/Development/mpc_tests/model_project_constructor` origin re-pointed — **§7.4 check 3 is now green on all three clones**, and the new URL was proved with `git ls-remote`, not just written |

#### The finding worth carrying forward — filed, not fixed, on purpose

**Phase 4 updated the archive banner's canonical template and none of its copies.**
`docs/methodology/PROJECT_CONVENTIONS.md:44` now reads `docs/wiki/model_project_constructor/…`;
**21 lines across 20 files** under `docs/architecture-history/` still read the old path and **zero**
read the new one. `CHANGELOG.md`'s preamble (`:3` and `:10`, twice each) is the same class. All of it
points at a directory Phase 4 deleted.

**§7.2 could never have printed one of them.** Group 1 exempts `^docs/architecture-history/` and
`^CHANGELOG\.md$` **wholesale**, on §3.1's rationale that they are frozen records — true of their
*entries*, false of a banner and a preamble, which record nothing and navigate. The blindfold
reappears **one level below** where the plan looked for it. §7.2 paired group 3's exemption with
three line-level assertions; group 1 got none. Learning [#135](PROJECT_LEARNINGS.md).

**Filed rather than swept, and this is a judgement the operator can cheaply overrule.** Classified
against §3 — which is what Phase 5 is told to do — these hits land in **§3.1**, so by the letter they
are not misses; the real claim is that §3.1's classification is wrong for that one sentence. That is
a *plan defect*, and this project's settled answer to one found mid-execution is to file it (Session
229 filed → Session 230 got a dedicated repair session), not to widen the closing commit into a
22-file sweep of frozen archives against `SAFEGUARDS.md`'s blast-radius rule. **The class was swept
before filing** (learning #122): `git grep -c "docs/wiki/claims-model-starter"` is **507 lines across
32 files**, and 484 of those are genuine dated records. The 23 in the item are the whole live
subset. Learning [#138](PROJECT_LEARNINGS.md).

#### A completion criterion that reads differently on different machines

**§7.3's residue grep is fail-open here and nobody could have seen it.** In this session `grep` is a
shell function wrapping **`ugrep --ignore-files`**, which honours `.gitignore`. Run verbatim, §7.3's
residue line prints **empty**; run as `command grep`, it prints **two** `tests/__pycache__/*.pyc`
blobs. Same tree, same command, opposite verdicts — and §7.2's rule is that a printed path *is* a
miss, "no judgment call". The `.pyc` content is harmless; the criterion is not. It greps
*directories*, so it reaches untracked files and its answer depends on the grep binary and on build
state. **Recorded, not silently repaired** — changing an instrument at the moment you declare it
passed is the move this project refuses elsewhere. §7.3 now carries the warning. Learning
[#136](PROJECT_LEARNINGS.md).

#### Verification — every §7 command, run

| Check | Result |
| --- | --- |
| §7.2 cmd 1 | **0** ✓ (pre-flight and at commit) |
| §7.2 (i) | exactly `:19 :24 :42` ✓ — never 0, which would mean publishing is broken |
| §7.2 (ii) | **EMPTY** ✓ — was 3 at pre-flight; this is the phase's headline criterion |
| §7.2 (iii) | exactly **1** line, NEW name left / OLD name right ✓ (§3.3 trap 1) |
| §7.3 repo/remotes | `rmsharp/model_project_constructor`; origin and wiki-clone remote both new ✓ |
| §7.3 tutorial | new **200**, old **404** ✓ — 404 is §1 by design, recorded not treated as a defect |
| §7.3 residue grep | empty ✓ **with the caveat above** |
| §7.3 publisher | *"no changes to publish"*, exit 0 ✓ |
| §7.3 push reachability (**new this session**) | `rev-list --count origin/master..master` = **0** ✓ |
| §7.3 suite | **1230 passed, 9 skipped**; ruff clean; mypy clean — unchanged since S230 |
| §7.4 (1) deployed site | **zero** old-name hits across all 7 `gh-pages` blobs, `.gz` decompressed — run with a **positive control** that proved the `gzip` branch executes; both live sitemaps 0 |
| §7.4 (2) live wiki | **one** hit across 25 pages — `Changelog.md:124`, the dated Session-19 entry §3.1 predicts. **No title survives**; a case-insensitive variant sweep found nothing more |
| §7.4 (3) clones | all **three** on the new name ✓ — the third re-pointed by this phase |
| Surfaces nobody had checked | git tags (2, clean), GitHub releases (live API rewritten), open PRs (none), repo metadata, `.github/` (zero hits of any name) — all clean |

#### The two workflows, and what they were worth

**Reconciliation sweep: 13 agents, 959K tokens, 0 errors.** It classified all 782 surviving hits
across 36 files, found the banner class, ran §7.3/§7.4 with positive controls, and its completeness
critic caught the `ugrep` fail-open **and** the one file no agent had classified.

**Pre-commit review: 84 agents, 5 lenses, 39 findings, 2 independent refuters each.** It found a
`PHASE5_COMMIT` placeholder I intended to back-fill in the close-out (4 lenses independently called
it a defect — nothing in the repo would have gone red if I forgot), **two citations I had
fabricated or misattributed**, a **sixth** dangling `BACKLOG.md` pointer my five-item list had
missed, and three wrong counts. All fixed before the commit.

**The read-only prohibition held again** — 97 agents total in a repo where `git commit` publishes to
a public website; `HEAD` and the wiki clone were both audited mid-run and after, and neither moved.

### Session 233 Handoff Evaluation (by Session 234)

**Score: 10/10.** Nine gotchas. Eight were load-bearing and correct, the ninth was correct and I
still tripped on the thing it could not have known. I cannot name a way it could have prepared me
better.

**What helped.**
- **Gotcha 1 was the whole pre-flight.** It said §7.2 command 1 is *already* `0` and that this is
  **not drift** — it reached the gate a phase early because all 11 remaining paths were Phase 4's.
  Without that sentence I would have opened this session looking at a green DONE gate for a phase
  that had not run, and the plan's own rule (*"a path appearing means drift; §2 must be re-derived
  before anything else is touched"*) has no clause for the opposite surprise. It also told me
  exactly what **does** still move — (ii) from 3 to 0, and (iii)'s left/right orientation forever.
- **Gotcha 2 is the one that would have cost the most.** *"`publish_wiki.sh` must still print
  exactly 3; `0` is broken at every point in this plan's life."* Phase 5's charter is *"classify
  every surviving hit; anything that is not §3.1/§3.3/self-reference is a miss — fix it here"*, and
  a `0` there is precisely what an executor reading that sentence too eagerly produces. Naming the
  failure mode (*"it means a sweep drove out the D-R5 clone path and the script now dies at its own
  `:58` guard"*) is what makes it stick.
- **Gotcha 3 pre-discharged a charter item and told me what to do instead.** Phase 5's bullet says
  `BACKLOG.md:74` *"should already have been done in Phase 4 — verify, do not assume"*. Gotcha 3 had
  verified it, showed the command, and — the valuable half — said the remaining rows **die by
  deletion, not substitution**, and that `BACKLOG.md:51` is *deliberately* left factually stale
  because editing it would be a substitution the plan forbids. I would have "fixed" that line.
- **Gotcha 4 turned defect #2 from a decision into an instruction.** *"Repair it to 'there are 24
  (25 files, one of which is `_Sidebar.md`)'"* — exact replacement text, so §3.2(c) took one edit.
  This is Session 233's own learning #134 applied to its successor, one session after it was written.
- **Gotcha 6 gave me a live negative control.** *"Nothing in Phase 5 should publish. If the hook
  fires, something under `docs/wiki/model_project_constructor/` was touched that should not have
  been — stop and look."* I checked the clone before and after: still `d85cc67`. That is a
  verification I would not have thought to *frame as a control*.
- **Gotcha 8 kept me from bundling a trim.** This file crossed 1,500 lines with this record, exactly
  as predicted.
- **"What's next" named Phase 5 by `grep` pattern, not line number** — and my own edits moved that
  section by ~90 lines during the session, so a line-number citation would have been stale before I
  used it.

**What was wrong: one number, and it had already been falsified by the handoff's own commit.**
Gotcha 3 and the record body both state that `grep -n 'docs/wiki/claims-model-starter' BACKLOG.md`
*"now returns only the rename item's own six rows (`:507 :647 :665 :672 :699 :715`)"*. That was true
at `1865fc2` — but Session 233's **own close-out**, `b13d970`, shifted five of them by +3 and added
a **seventh** at `:51` by writing the Phase 4 result into the index row. At `HEAD` the grep returned
seven. The classification was unaffected and no edit was owed, so this cost me nothing; but a
Phase 5 executor comparing against "six" would have gone looking for the extra. **The general
shape is the one this project keeps re-learning (#105): a count measured mid-session and quoted in
the close-out is measured against a tree the close-out then changes.** The fix is one word —
*"six rows as of `1865fc2`"* — or re-running the grep after writing the record.

**What was missing: nothing I can name.** Two Phase-5 items were not in the handoff but were in the
plan where they belonged — §9.1's assignment of dragon 9's stale push line to *"Phase 5's
reconciliation"*, and §9.1's `:1372` field-name note. Both are found by reading §9.1, which the
handoff's key-files list points at.

**ROI: very high.** ~7 minutes to read. It supplied the pre-flight interpretation, four failure
modes I did not have to discover, and one exact replacement string.

### Session 234 Self-Assessment

**Score: 7/10.** The phase is complete and provably so, the plan is closed, and the session's real
contribution is a defect class the rename's own DONE gate is structurally blind to. But **three of
my own citations were wrong and a review caught all three**, one of them in the very fix I had just
written to remove an unverifiable claim.

**+** **I found the thing the gate cannot see, and generalised it.** §7.2 exempts
`docs/architecture-history/` and `CHANGELOG.md` by *file*; a banner and a preamble are live lines
inside frozen files, so 23 dead pointers ride in free. §7.2 had already reasoned about this hazard
for group 3 and paired that exemption with three line-level assertions — group 1 got none. That is
the shape, not the instance (learning #135).
**+** **I filed it rather than sweeping it, and the reasoning survived a deliberate attack.** I asked
the review to break the decision; the adjudicator tried the strongest angle (split out
`CHANGELOG.md`'s three obvious lines and sweep those) and refuted it on a ground I had not seen:
§3.1 buckets `CHANGELOG.md` *whole*, so the preamble is inside the **same** misclassification, and a
partial sweep's selection principle would be "which ones the executor felt sure about".
**+** **I swept the class before filing it.** 507 dead in-repo wiki paths across 32 files; 484 are
genuine dated records. The 23 in the item are the whole live subset — learning #122 applied, rather
than filing one instance of an unswept class.
**+** **I refused to change an instrument at the moment I declared it passed.** The `ugrep` wrapper
makes §7.3's residue grep read empty here and non-empty elsewhere. I recorded both readings and
warned, instead of quietly switching the criterion to `git grep` and reporting green (learning #136).
**+** **I did not rewrite two closed phases' verification blocks**, following §9.1's own precedent
for Phase 2's `-fL` advice, and attached the correction where a reader meets it. The review verified
both blocks are byte-identical.
**+** **I checked an agent's finding and refuted it.** A reviewer wanted a wiki `Changelog.md` line
filed as a public-correctness bug; it sits under a `(Sessions 179-180)` heading, so it is a dated
record like `:124`. Not filed.

**−** **Three bad citations, all mine, all caught by the review, none by me.** I attributed a real
sentence (*"an exemption is only as good as the assertion traded for it"*) to **§7.2** when it is
§9.1's; I attributed *"fix the field name whenever that line is next touched"* to §9.1 when it was
`BACKLOG.md`'s flag 3, which the same commit deletes; and dragon 6's replacement citation sent the
reader to `CHANGELOG.md` for the operator's underscore ruling, which `CHANGELOG.md` does not
contain. In a document whose entire ethos is *measure, do not assume*, a quotation I did not grep
for is the worst class of error I could ship — and I shipped three while writing a §9.2 that
criticises exactly this.
**−** **My fix for the placeholder was worse than the placeholder.** I replaced `PHASE5_COMMIT` with
`git log --grep 'rename Phase 5'` — which matches commit **subjects**, and every close-out in this
rename carries that phrase while three of four phase commits did not carry their own. It would have
resolved confidently to the wrong commit. The placeholder at least announced itself. Only the
adjudicator caught it; five review lenses did not.
**−** **I wrote "all five pointers" from a list instead of a `git grep`** — and there were six. I
committed learning #137's failure mode in the paragraph that introduces learning #137.
**−** **The must-fixes came from review again**, third session running. The difference this time is
that the review found errors in my *prose* rather than my *staging*, which is a harder class to
self-catch and an argument for keeping the review rather than for trusting myself more.

**Against the bar:** S229 refuted a dragon by measurement; S230 fixed a class not an instance; S231
raised a proof to 10 assertions; S232 proved a publish against the public artifact; S233 turned a
safety claim into a measurement and gave a blind proof an executable test. This session's equivalent
is finding that the DONE gate's *exemption granularity* is the defect — and then declining to act on
it unilaterally. It built no `--self-test`, and it needed a review to keep its own prose honest.

**What's next: the rename is DONE. There is no Phase 6, and no rename item to pick up.** Choose from
`BACKLOG.md`, which now has **19** items. Three are new and cheap-and-valuable; two need you, the
operator, before an agent can move:

1. **A fifth trim of this file — likely the right next session.** It is **1,753 lines**, over
   `CLAUDE.md`'s **1,500** trigger. `CLAUDE.md`'s *"two commits, always"* makes a trim its own
   session, and **re-derive the L8 copy list with `git grep -l 'SESSION_NOTES-'` rather than
   trusting the list** — Session 231's own bullet says the list is not to be trusted at the fifth
   trim. Copy L0-L9 forward and run `--self-test`; **a green self-test whose mutants never exercise
   your new assertion is the same lie as a green run.**
2. **The two operator decisions**, both filed as their own `BACKLOG.md` items with the measurements:
   the **archive-banner ruling** (is a banner part of the frozen record, or boilerplate that tracks
   its template? — one ruling disposes of all 23 lines) and the **clone-independence criterion**
   restatement for the enterprise fork.
3. **The unstyled tutorial site** is the highest-value bug: it has been serving CSS-less HTML to the
   public since late July, the deploy that does it reports success in 11 seconds, and this session
   bracketed the regression to 2026-06-19..2026-08-02 with one config line as the suspect.

**Key files:**
- [`docs/planning/repository-rename.md`](docs/planning/repository-rename.md) — **CLOSED.** §9.2 is
  this session's reconciliation log and the place to start if you doubt anything above. Its status
  line cites its own commit with `git log -S`, not a hash.
- `BACKLOG.md` — 19 items, 19 index rows. The six new ones are the last six before
  *Enterprise migration*.
- `PROJECT_LEARNINGS.md` — **138 learnings**; #135-#138 are this session's.
- `docs/methodology/PROJECT_CONVENTIONS.md:44` — the banner template that now disagrees with all 21
  of its copies.

**Gotchas:**
1. **Do not "finish" `scripts/publish_wiki.sh`'s three remaining old-name lines** (`:19`, `:24`,
   `:42`) or `enterprise-migration.md`'s nineteen. They name a directory **on disk** that GitHub's
   rename never moved (D-R5). `0` in `publish_wiki.sh` means the script now dies at its own `:58`
   guard. This survives the plan's closure and has no expiry.
2. **`enterprise-migration.md`'s `diff -r -x '.git'` line must keep the NEW name on the left and the
   OLD name on the right, forever.** `sed` breaks it whichever way it runs. Re-derive with
   `grep -n "diff -r" docs/planning/enterprise-migration.md`.
3. **§7.3's residue grep reads differently on different machines.** `grep` here is a
   `ugrep --ignore-files` wrapper honouring `.gitignore`; `command grep` prints two
   `tests/__pycache__/*.pyc` blobs. Before trusting any "empty" from a search, run `type grep`.
4. **The plan is closed but still lives in `docs/planning/`** — the same convention violation it
   files against `httpx-adapter-migration.md`, now filed as one item covering both. Moving it would
   change a path its own §7.2 allowlist matches on, so do not do it casually.
5. **`SESSION_RUNNER.md:209` still names the old wiki directory and still must not be edited**
   (dragon 8). `CLAUDE.md`'s seam bullet is the correction. Unchanged by this session.
6. **This file is over the trim trigger** — see "What's next" item 1. Do not bundle a trim with a
   record edit; the proof goes red forever.
7. **Still zsh. Single-quote every heredoc delimiter** — twelfth session running that this has been
   free.
8. **The wiki clone did not move this session** (`d85cc67`, where Phase 4 left it) and must not have:
   Phase 5 touches no `docs/wiki/` path. If a future non-wiki session sees it move, the trigger
   prefix has drifted.

### What Session 233 Did
**Deliverable:** **Phase 4 of [`docs/planning/repository-rename.md`](docs/planning/repository-rename.md)
— COMPLETE.** The wiki source directory is renamed and every mechanism that keys on it moved with it,
atomically. The hook fired on its own, published, and **pushed**; the live public wiki was read back
over HTTP and shows exactly the three intended lines changed and nothing else. **No other phase ran.
Phase 5 is next, and it is the last one.**

**Started / completed:** 2026-08-20. **Commits: three** — `894c5fc` (the Phase 1B claim, alone),
`1865fc2` (the whole phase, one atomic commit), and this close-out. **Operator this session:**
*"phase 4"*.

Documentation and path strings only, so **no `CHANGELOG.md` entry** — the plan settles this in §5 on
`PROJECT_CONVENTIONS.md` §2's cadence gate. Every `scripts/` and `tests/` edit here is a path string.

#### What changed — one commit, 36 paths

| Thing | Detail |
| --- | --- |
| `git mv` | `docs/wiki/claims-model-starter` → `docs/wiki/model_project_constructor`, 25 pages |
| `scripts/publish_wiki.sh` | **7 changed** (`:2 :11 :23 :44 :63 :72 :75`); **3 KEPT forever** (`:19 :24 :42`, the D-R5 clone path); `:101` untouched |
| `.githooks/post-commit` | `:3`, `:18` — trigger prefix, **underscores** |
| `tests/test_wiki_no_line_citations.py` | `:7`, `:38` — `:38` assembles the path from parts (dragon 11 / K6) |
| Prose paths | `THIRD-PARTY-LICENSES:50`, `docs/style/statistical_terms.md` ×4, `PROJECT_CONVENTIONS.md` ×4, `stakeholder-readiness-dossier.qmd` ×2, `opencode-adapter-spec.md` ×4, `httpx-adapter-migration.md` ×2 |
| `enterprise-migration.md` | **17 path lines** (incl. the dual-purpose `diff -r` line) **+ `:345`**, the coupling row this commit falsifies |
| Wiki pages | `License.md:3`, `Contributing.md:124`, `Evolution.md:266` — the three that make this commit publish |
| `CLAUDE.md` | new seam subsection: `SESSION_RUNNER.md:209` is now stale and **must not be edited** (dragon 8) |
| **`BACKLOG.md:74`** | **added by pre-commit review** — see below |
| **`Evolution.md:266` count** | **added by pre-commit review** — 22 → **24** |

**Out of repo, no commit:** the clone's origin → `model_project_constructor.wiki.git`. D-R5 = re-point
**in place**, so `~/Development/claims-model-starter.wiki` **did not move** and `:42` did not change.

#### The pre-commit review earned its keep, and it caught a real miss

**14 agents, 5 lenses, 1.08M tokens, 8 findings, 3 survived refutation, 2 distinct must-fixes after
adjudication.** Both were things I had staged wrong, and both are now in `1865fc2`:

1. **`BACKLOG.md:74` was missing from the commit.** The plan assigns it to Phase 4 **twice** — §3.2(e)
   (*"Exactly one is a genuine substitution … which moves with the directory in Phase 4"*) and Phase
   5's checklist (*"it should already have been done in Phase 4 — verify, do not assume"*) — and
   **Phase 4's own step-2 bullet list omits it.** I drove from the checklist. Two live
   `docs/wiki/claims-model-starter/*.md` citations inside the *unrelated* OpenCode item would have
   become 404s, and **no automated check in the plan can see it**: §7.2 exempts `^BACKLOG\.md$`
   wholesale, and Phase 4's residue grep covers only `scripts/ tests/ .githooks/`. Two of five lenses
   found it independently. Learning [#132](PROJECT_LEARNINGS.md). **Phase 5's "verify, do not assume"
   for this line is discharged** — `grep -n 'docs/wiki/claims-model-starter' BACKLOG.md` now returns
   only the rename item's own six rows (`:507 :647 :665 :672 :699 :715`), which die by row deletion.
2. **`Evolution.md:266`'s page count.** §3.2(c) ends *"Fix the count while you are in the line."* I
   read Session 232's gotcha 7 (*"is 24, not the plan's 25 … filed in BACKLOG.md"*) as a **deferral**
   when it was an **erratum** — a correction to a number I was supposed to write. Measured rather than
   copied (`ls docs/wiki/model_project_constructor/ | grep -vc '^_'` → **24**) and shipped as 24.
   Learning [#134](PROJECT_LEARNINGS.md). Session 232's filed defect **#2 is now half-discharged**: the
   *page* is correct; the *plan's* §3.2(c) still prescribes 25 and that repair is still Phase 5's.

**Refuted and correctly so:** the learning-#129 hole in Phase 4's verification block (already filed by
Session 232, owned by Phase 5 — and I had already applied its two commands by hand), and three
findings against the plan's prose rather than the staged diff. **The read-only prohibition block held
again** — 14 agents in a repo where `git commit` publishes to a public website; the audit mid-run
showed `HEAD` and the clone both untouched.

#### Verification — every prediction the plan makes, plus three checks it does not

| Check | Result |
| --- | --- |
| §7.2 cmd 1, pre-flight | **11** — exactly the ledger's prediction; **nothing appeared** |
| §7.2 (i) pre-flight | **10** ✓ (correct *before* Phase 4; `0` or `3` here would be broken) |
| §7.2 (ii) pre-flight / (iii) | **20** / exactly **1** ✓ |
| `git mv` shape | **22 R100 + 3 R09x**, the 3 being License/Contributing/Evolution; **no `A`/`D` pairs** |
| Hook fired | `733b3ca` → **`d85cc67`** ✓ |
| Clone's published diff | **3 files, 3 insertions, 3 deletions.** The 25 renamed files **did not appear** — `rsync` copies *contents* of `SOURCE_DIR`, so the directory name never reaches the clone |
| Publisher idempotent | *"no changes to publish"* ✓ |
| Source vs clone parity | identical ✓; clone still **25** files |
| §7.2 cmd 1 at `HEAD` | **0** ✓ |
| §7.2 (i) at `HEAD` | exactly **3** — `:19 :24 :42` ✓ |
| §7.2 (ii) at `HEAD` | **3**, all Phase 5's (`:919 :1250 :1372`) ✓ |
| §7.2 (iii) at `HEAD` | NEW name left, **OLD name right** ✓ — §3.3 trap 1 |
| Residue in `scripts/ tests/ .githooks/` | empty ✓ (path-anchored exclusion, not `--exclude`) |
| Hook literal read back | old-name **0**, underscore trigger **1**, hyphen typo **0** ✓ |
| `uv run pytest -q` | **1230 passed, 9 skipped** — unchanged from Sessions 230/231/232 |
| `uv run ruff check` | clean ✓ |
| **Added:** `push --dry-run` **before** the commit | *"Everything up-to-date"*, exit 0 — learning [#129] |
| **Added:** `rev-list --count origin/master..master` on the clone | **0** — nothing stranded |
| **Added:** the live wiki over HTTP | License/Evolution/Contributing all **200**, new path **1** each, **old path 0** each; the live Evolution page reads **"24 outward-facing wiki pages plus the sidebar"** |

**Two checks the plan does not contain, invented here, and one of them matters.**

- **Dragon 2's fail-closed state was *observed*, not assumed.** Between the `set-url` and the commit,
  `scripts/publish_wiki.sh` was run deliberately: exit **1**, loud, naming both the actual and the
  expected origin. One command turns the plan's central safety claim into a measurement.
- **A forward-looking trigger test, because *"HOOK FIRED"* cannot prove the prefix is right.**
  `git diff-tree` (no `-M`) lists a rename as **both** paths — verified here against `e1bf7c2` — so on
  *this* commit the hook fires whether `:18` says the new name **or the stale old one**. The plan knows
  and says *"read the literal back out of the file"*, but that is an eyeball. Instead the pattern was
  **extracted from the file and run**:
  `PAT=$(sed -n '18p' .githooks/post-commit | sed "s/.*grep -q '\([^']*\)'.*/\1/")` → matches
  `docs/wiki/model_project_constructor/Home.md` ✓, does **not** match `SESSION_NOTES.md` ✓, does **not**
  match the old path ✓. The negative controls are the half that catches a stale prefix. Learning
  [#133](PROJECT_LEARNINGS.md).

#### One fact found, not fixed

**§7.4 check 3: `~/Development/mpc_tests/model_project_constructor` still has the OLD origin**
(`https://github.com/rmsharp/claims-model-starter.git`). It works — GitHub redirects git remotes — but
§7.4 wants it re-pointed. **Not touched:** Phase 4's declared out-of-repo change is exactly one clone,
the wiki's. Re-pointing a second would be bundling. It is Phase 5's, and it is in the handoff below.

#### The push — what fired, measured not predicted

`8fa7901..b13d970`, all three commits. **CI fired and passed** (run `32429848248`) — all four jobs
green: mypy, pytest, ruff, and the data-agent decoupling test. **Publish Tutorial did NOT fire** —
still Phase 1's run `32335373755` from 2026-08-20T05:22:48Z, which is correct: its path filter is
`docs/*.md` (**single level**), and this session's `docs/` edits are all two or more levels deep
(`docs/wiki/**`, `docs/style/`, `docs/methodology/`, `docs/planning/`). Nothing matched.

**The wiki clone did not move on the close-out commit or on the push** — still `d85cc67`, where
Phase 4's publish left it. That is **K4 working as a live negative control**: the close-out touches
no `docs/wiki/**`, so the trigger must not fire, and it did not. Together with the positive fire on
`1865fc2` and the extracted-pattern test, the trigger is now proved in all three directions —
**fires on wiki content, does not fire without it, and matches a future-shaped path** (learning
[#133](PROJECT_LEARNINGS.md)).

### Session 232 Handoff Evaluation (by Session 233)

**Score: 9/10.** Nine gotchas, every one of them load-bearing, and I hit exactly the one trap it
worded ambiguously.

**What helped.**
- **Gotcha 1 was worth the whole handoff.** It told me Phase 4's verification block carries the defect
  Session 232 had just filed, and named the three commands that close it. I ran `push --dry-run`
  before the commit and `rev-list --count` + `curl` after — and because of that this phase's success
  was proved against the public artifact rather than a local mirror. Without it I would have run the
  plan's block as written and reported green off a check that cannot see a stranded push.
- **Gotchas 2, 3, 5 and 6 are the four ways to break this phase**, and each named the *silent* failure
  mode rather than the loud one: `mkdir` → the publisher empties the public wiki; hyphen → the hook
  exits 0 forever; `:42` → hard-fail at `:58`; the assembled `WIKI_DIR` → the one line whose omission
  reddens the suite. All four correct, all four avoided.
- **Gotcha 8's *"a path appearing means drift; a path leaving means a phase working"*** turned the
  §7.2 pre-flight from a re-derivation into one command. It predicted **11** and printed 11.
- **The "What's next" block named the plan section by `grep` pattern, not line number**, so nothing
  had to be re-derived after this session's own edits moved things.

**What was wrong: one thing, and it cost me a defect.** Gotcha 7 — *"`Evolution.md:266` is `24`, not
the plan's `25`. Filed in `BACKLOG.md`; do not paste the plan's number."* — is ambiguous between *"do
not do this, it is filed"* and *"do this, with 24"*. It is the latter: §3.2(c) says **"Fix the count
while you are in the line"** and the filed defect's own text presumes the executor acts. I read it as a
deferral. **The handoff would have been unambiguous with four more words:** *"Do fix it in Phase 4;
write 24."* Learning [#134].

**What was missing:** nothing else I can name. Everything I needed beyond the above was in the plan.

**ROI: very high.** ~6 minutes to read; it supplied the two verification commands that make this
phase's success provable and steered me clear of four silent failure modes.

### Session 233 Self-Assessment

**Score: 8/10.** The phase the plan calls its riskiest landed clean, published live, and every
prediction it makes was tested and held. But the two defects in my staged commit were both found by a
review rather than by me, and one of them was an instruction I had read and misclassified.

**+** **I converted the plan's central safety claim into a measurement.** Running the publisher in
the fail-closed window cost one command and is the only evidence dragon 2 is true rather than believed.
**+** **I found that the phase's headline proof is blind to the failure it exists to catch**, verified
the mechanism against a real rename commit in this history, and replaced an eyeball with an executable
test carrying negative controls. That is the session's one reusable artifact.
**+** **Assert-then-replace over 49 substitutions.** Every edit asserted its target substring was
present on the exact line before writing, and asserted no line count changed — which is what kept the
`publish_wiki.sh:N` citations in `enterprise-migration.md`'s coupling table valid.
**+** **I measured `24` instead of copying it** from either the plan (25) or the review (24).
**+** **I did not bundle.** The `mpc_tests` clone's stale origin was found, verified, and left for
Phase 5 with a note. Phase 4's out-of-repo change is one clone.

**−** **I drove the sweep from Phase 4's checklist instead of from §3's classification**, and the plan
disagrees with itself between the two. The classification is derived from measurement; the checklist is
prose. I had read §3.2(e) — it is the same paragraph I used to justify *not* `sed`-ing `BACKLOG.md` —
and did not reconcile it against the bullet list I was executing. Learning [#132] is a rule I violated
before writing it, which is the second session running that has said that sentence.
**−** **I misclassified a handoff gotcha and shipped the omission into the staged diff.** Two greps
would have settled it.
**−** **Both must-fixes came from the review, again.** Session 232 wrote the same minus. The review is
now reliably finding one real defect per phase, which is good — and it means the executor's own
pre-commit reading is reliably missing one.

**Against the bar:** S229 refuted a dragon's own prescriptions by measurement; S230 fixed a class
rather than an instance; S231 raised a proof from 8 assertions to 10; S232 proved a publish against the
public artifact. This session did the S229 move twice — once on dragon 2 (fail-closed, observed) and
once on Phase 4's own proof (blind to a stale prefix, and given a test that is not) — and it is the
first phase of this rename to correct a defect **in the plan's phase checklist** rather than only in
its prose. It did not build anything with a `--self-test`.

**What's next: Phase 5 of [`docs/planning/repository-rename.md`](docs/planning/repository-rename.md)**
— *"Reconcile, classify the residue, close the item. **One commit.**"* Find it with
`grep -n '^### Phase 5'`; **do not cite it by line number.** **This is the last phase.** It is a
reconciliation, not a mechanism change — nothing in it publishes and nothing in it is irreversible.

**Key files:**
- `docs/planning/repository-rename.md` — Phase 5, and **§7.2 and §7.3 and §7.4 are its DONE gate.**
  Also its own `:3` status line, which Phase 5 flips from `IN EXECUTION` to executed.
- `BACKLOG.md` — the rename item's rows are **deleted, not substituted** (§3.2(e)); the two
  Session-232 defect entries and the three Session-229 flags live in the same block.
- `docs/planning/enterprise-migration.md` — the **3** remaining hits (`:919`, `:1250`, `:1372`).
- `README.md:7` — Phase 5 re-reads it end to end; it was rewritten in Phase 1 with the site down.
- `PROJECT_LEARNINGS.md` — **134 learnings**; #132–#134 are this session's.

**Gotchas:**
1. **§7.2 command 1 is already `0`.** The ledger predicts 0 only "after Phases 3, 4 and 5", but all 11
   remaining paths were Phase 4's, so it arrived a phase early. **That is not drift.** Commands (ii)
   and (iii) are what still move: (ii) is **3** and must reach **0**; (iii) must keep the **NEW** name
   on the left and the **OLD** name on the right, forever.
2. **`scripts/publish_wiki.sh` must still print exactly 3** (`:19`, `:24`, `:42`) at the end of Phase 5.
   **`0` is broken at every point in this plan's life** — it means a sweep drove out the D-R5 clone
   path and the script now dies at its own `:58` guard.
3. **`BACKLOG.md:74` is done.** Phase 5's *"verify, do not assume"* for it is discharged — verified
   `grep -n 'docs/wiki/claims-model-starter' BACKLOG.md` returns only the rename item's own six rows.
   Do not re-substitute; **delete those rows**. **One of those rows is now factually stale and was
   deliberately left alone:** the plain-language index row (`BACKLOG.md:51`) still opens *"GitHub
   still says `claims-model-starter`"*, which Phase 1 falsified. It is one of §3.2(e)'s 17
   self-referential hits, so it dies by **deletion**, not substitution — editing it in Phase 4 would
   have been a substitution the plan forbids. Only its status column was updated.
4. **Session 232's filed defect #2 is only half done.** `Evolution.md:266` now says **24** on the live
   wiki. The *plan's* §3.2(c) still says *"there are 25"* — repair it to *"there are 24 (25 files, one
   of which is `_Sidebar.md`)"*. Defect #1 (the publish proof) is still wholly Phase 5's.
5. **`~/Development/mpc_tests/model_project_constructor` still points at the old origin** —
   §7.4 check 3. Re-point it, or record why not. It is out of repo; no commit re-points it.
6. **Nothing in Phase 5 should publish.** If the post-commit hook fires during Phase 5, something under
   `docs/wiki/model_project_constructor/` was touched that should not have been — stop and look.
7. **The `Changelog.md` allowlist line uses `[^/]+` on purpose** and now resolves against the *new*
   directory. Do not "tidy" it into a fixed path.
8. **The trim threshold is close.** This file is **1,481 lines** after this record — under
   `CLAUDE.md`'s **1,500** trigger, so **no trim fired this session**. The next record will almost
   certainly cross it. **Do not bundle a trim into Phase 5** — `CLAUDE.md`'s *"two commits, always"*
   rule makes a trim its own session, and a trim commit containing a record edit holds the proof red
   forever. If the next session's task is Phase 5, close out over the threshold and let a **fifth
   trim** be its own session; re-derive the L8 copy list with `git grep -l 'SESSION_NOTES-'` when it is.
9. **Still zsh. Single-quote every heredoc delimiter** — eleventh session running that this has been free.

### What Session 232 Did
**Deliverable:** **Phase 3 of [`docs/planning/repository-rename.md`](docs/planning/repository-rename.md)
— COMPLETE.** The published wiki is rebranded and **live to readers**. Eight lines across five pages;
the `post-commit` hook fired and pushed; the live public wiki was then read back over HTTP and shows
the new content with **zero** occurrences of the old brand. **No other phase ran. Phase 4 is next.**

**Started / completed:** 2026-08-20. **Commits: three** — `624426b` (the Phase 1B claim, alone),
`f58948a` (Phase 3's wiki content, the only commit that touches `docs/wiki/**`, per K4), and this
close-out. **Operator this session:** *"Execute Phase 3 of the repository rename plan."*

Documentation-only, so **no `CHANGELOG.md` entry** — the plan settles this itself in §5 ("No phase of
this rename earns a `CHANGELOG.md` entry"), on `PROJECT_CONVENTIONS.md` §2's cadence gate.

#### What changed — 8 lines, 5 files, exactly Phase 3's table

| File | Lines | Change |
| --- | --- | --- |
| `Contributing.md` | `:19`,`:20` | clone command → new URL **and** new directory |
| `Contributing.md` | `:238` | issues URL |
| `Home.md` | `:1` | title rebrand — operator decision **D-R3 = yes** |
| `_Sidebar.md` | `:1` | sidebar heading — **D-R3 = yes** |
| `Development-Workflow.md` | `:3` | **semantic rewrite** (dragon 7) → "generated model project" |
| `Software-Bill-of-Materials.md` | `:3`,`:113` | **semantic rewrite** (dragon 7) |

**Left alone, deliberately:** `Changelog.md:124` (permanent KEEP — a dated historical entry), and the
three wiki-**path** references Phase 4 owns — `Evolution.md:266`, `License.md:3`,
`Contributing.md:124`. The residual sweep after the commit prints exactly those four and nothing else.

**Dragon 7 was obeyed, not shortcut.** Those three lines use the old repository name as a generic
label for *the projects this tool generates*, not for this repository, so they became **"generated
model project"** — the plan's own suggested term — rather than the new repo name. Substituting
`model_project_constructor` there would have renamed a concept the rename has no business touching.

**A live contradiction closed as a side effect.** `docs/tutorial.md:30` (Pages site) already told
readers `git clone <repo-url> model_project_constructor` while the wiki said `cd
claims-model-starter`. Phase 3's table flagged the disagreement; the two published surfaces now agree.

#### Verification — including two checks the plan does not contain

| Check | Result |
| --- | --- |
| §7.2 command 1, pre-flight | **13** — exactly the ledger's prediction; set identical, **nothing appeared** |
| §7.2 (i) `publish_wiki.sh` | **10** ✓ correct before Phase 4 (`0` or `3` here would be a broken publisher) |
| §7.2 (iii) dual-purpose line | exactly **1** ✓ |
| §7.2 command 1, at `HEAD` | **11** — `Development-Workflow.md` and `Software-Bill-of-Materials.md` left, both fully cleared by this phase |
| Plan check 1 — hook fired | `41c7f72` → **`733b3ca`** ✓ |
| Plan check 2 — publisher idempotent | *"no changes to publish"* ✓ |
| Plan check 3 — source vs clone parity | identical ✓ |
| Plan check 4 — Pages workflow | **UNCHANGED** — still Phase 1's run `32335373755`; no wiki path matches `docs/*.md` |
| **Added:** nothing stranded in the clone | `rev-list --count origin/master..master` = **0** |
| **Added:** the live wiki, read over HTTP | `Model Project Constructor Wiki` present; `Claims Model Starter` → **0 hits**; new clone URL on the live Contributing page, old one → **0** |
| `uv run pytest -q` | **1230 passed, 9 skipped** — unchanged from Sessions 230/231 |

**The two added checks are the session's one substantive finding, and they are now the plan's, too**
— filed in `BACKLOG.md` for the Phase 4/5 executor, because Phase 4's verification block has the
identical hole. Learning [#129](PROJECT_LEARNINGS.md).

#### The pre-publish review earned its keep once, decisively

**20 agents, 5 lenses, ~1.43M tokens, 14 findings filed, 4 survived refutation, 2 after adjudication.**
Built to learning [#124](PROJECT_LEARNINGS.md): `maxItems` per lens, one adjudicator, and every review
agent given an explicit read-only prohibition block (no commits — a commit in this repo *publishes to
a public website*). **No finding asked for a byte of the diff to change.** Both survivors were about
the *plan*, not the deliverable:

1. **The publish proof cannot see the live wiki** — three of five lenses converged here independently,
   which is the strongest signal in the set. `publish_wiki.sh` commits into the clone and *then*
   pushes; on push failure it **exits 2 leaving the local commit in place**. All four of Phase 3's
   checks then pass while the live wiki is stale, and the plan's stated recovery (*"re-run it, it is
   idempotent"*) is **inert** — the re-run short-circuits at *"no changes to publish"* and never
   retries the push. Verified against the script before acting on it.
2. **`Evolution.md:266`'s count** — the plan quotes *"22 outward-facing wiki pages"* and says "there
   are 25". The page says *"22 … **plus the sidebar**"*; `git ls-tree` at the commit that wrote the 22
   shows 23 files including `_Sidebar.md`, so the right value is **24**. Filed, not fixed —
   `docs/planning/` is outside Phase 3's blast radius. Learning [#131](PROJECT_LEARNINGS.md).

#### One thing the plan asked for and never got, settled here

§1 says push continuity over the wiki clone's stale `claims-model-starter.wiki.git` origin was
*"documented but not measured … confirm it during Phase 1"*. **Phase 1 ran `git fetch`** — which
proves the redirect and *read* auth, and nothing about *write*. The clone's last push was
**2026-08-01**, 19 days before the rename. So Phase 3's commit was chronologically the first *write*
to that remote under the new name. `git push --dry-run origin master` → *"Everything up-to-date"*,
exit 0, one second, **before** the commit. The real push then printed GitHub's own
`remote: This repository moved.` and succeeded. Learning [#130](PROJECT_LEARNINGS.md).

#### The push — what fired, measured not predicted

`adf5554..28c4799`, all three commits. **CI fired and passed** (run `32425252735`, 47s, lint + tests).
**Publish Tutorial did NOT fire** — still Phase 1's run `32335373755` from 2026-08-20T05:22:48Z, which
is correct: its path filter is `docs/*.md` (single level), and nothing in these three commits matches
it. The **wiki clone did not move** on either the close-out commit or the push — it is still
`733b3ca`, where Phase 3's publish left it. Same shape Session 231 recorded, one phase later.

### Session 231 Handoff Evaluation (by Session 232)

**Score: 10/10.** I cannot find a claim in it that was wrong, and its gotcha 4 is the reason this
session's one filed defect was found rather than shipped.

**What helped.**
- **The "What's next" block was executable as written.** It named Phase 3, quoted its one-line
  summary, said *"find it with `grep -n '^### Phase 3'`; **do not cite it by line number**"*, and told
  me to **read §2.4b first** because D-R3 = yes puts two title-case lines in scope that **no
  `claims-model-starter` grep will ever surface**. That last point is the entire trap in Phase 3 — a
  competent executor driving from the bare-name pattern silently ships 6 of the 8 lines and reports
  success. Session 231 had no reason to touch Phase 3 and pointed at its sharpest edge anyway.
- **Gotcha 4** — *"This trim does NOT falsify `repository-rename.md`. Checked."* It then named
  precisely what *did* move (the 35 old-name hit-lines split 13/22 across the live file and the new
  shard) and predicted **52 file slots, not 51**, for Phase 5. I re-ran §7.2's pre-flight expecting
  drift after a 738-line archive operation and found **none** — the set was identical. That check
  cost me one command instead of a re-derivation of §2, because 231 had already done the reasoning.
- **Gotcha 2** (*"Run the plain proof, not just `--self-test`"*) generalised cleanly outside its
  subject: it is the same instinct that made me distrust Phase 3's four green checks and go look at
  what `publish_wiki.sh` does on a failed push. A green suite that is green for the wrong reason is
  the shape of both.
- **Learning [#124](PROJECT_LEARNINGS.md)**, recorded by Session 230 and forwarded by 231, sized this
  session's review correctly on the first try: 20 agents and 1.43M tokens, versus the 132-agent /
  ~8M-token shape it warns against.

**What was missing: nothing I can name.** The one thing I would have valued — that Phase 1's `fetch`
does not discharge §1's push-continuity request — is not Session 231's to have known; it is two phases
upstream of anything 231 touched, and I only found it because a review lens went looking.

**ROI: very high.** ~5 minutes to read, and it removed the two most expensive mistakes available
(missing the invisible title lines; re-deriving §2 over a phantom drift).

### Session 232 Self-Assessment

**Score: 8/10.** The deliverable is correct, is live, and was proved against the public artifact
rather than a local mirror. It is a small phase executed carefully; it did not extend the project's
apparatus the way the three sessions before it did.

**+** **I verified the publish against the thing readers actually see.** The plan's DONE condition is
*"the live GitHub Wiki shows the new content"*, and every command it supplies inspects a local clone.
Curling the live page cost one command and is the only check in the set that could have caught a
failed push.
**+** **I measured the assumption before the irreversible-ish act, not after.** `push --dry-run` over
a 19-day-stale remote URL, before the commit that publishes. §1 asked for exactly this and Phase 1
had answered it with a weaker verb.
**+** **I obeyed dragon 7 rather than the sweep.** Three of the eight lines are a concept, not a
name; a blind `sed` would have been faster, wrong, and invisible in the diff review.
**+** **I filed both findings instead of fixing them.** Both are `docs/planning/` edits and Phase 3's
blast radius is `docs/wiki/**`. Fixing them would have been a two-line diff and a bundled phase —
FM #18, in the plan that exists to prevent it.
**+** **The review's prohibition block held.** 20 agents with full tool access in a repository where
`git commit` publishes to the public; none wrote, committed, or ran the publisher.

**−** **Every one of my own pre-commit checks came from the plan or the review, not from me.** I
re-ran §7.2, the four Phase 3 commands, and the suite — all prescribed. The one genuinely new check
in this session (assert the remote) was handed to me by a lens I paid 1.43M tokens for. A stronger
session asks *"what would make all four of these green and the site still wrong?"* before spawning
anything.
**−** **I let the review find the `Evolution.md` count.** I had read that exact line twice — once in
the residual sweep, once confirming Phase 4's deferral — and never opened the sentence it quotes.
Learning [#131](PROJECT_LEARNINGS.md) is a rule I violated before I wrote it.
**−** **Three commits and no push until close-out.** Consistent with Session 231, but it means the
wiki went live to readers while `master` sat local — the two published surfaces were momentarily
ahead of the repository that explains them. Harmless here; worth naming.

**Against the bar:** S227 executed an irreversible rename with every prediction tested; S229 refuted
two of a dragon's own prescriptions by measurement; S230 fixed a class rather than an instance; S231
raised a proof from 8 assertions to 10 and closed two documented holes. This session did the S229 move
— test the prescription, not just the finding — against the plan's verification block, and shipped
the first phase of this rename whose success was confirmed on the public artifact. It did not build
anything reusable, and its best finding was bought rather than reasoned.

**What's next: Phase 4 of [`docs/planning/repository-rename.md`](docs/planning/repository-rename.md)**
— *"The directory move and the mechanisms that key on it. **One commit + one out-of-repo change.**"*
Find it with `grep -n '^### Phase 4'`; **do not cite it by line number.** **This is the phase the plan
calls its riskiest**, and the one where the fail-open hook bites.

**Key files:**
- `docs/planning/repository-rename.md` — Phase 4, and **read dragons 3, 4 and 11 before touching
  anything**. Also §3.3 and D-R5, which decide how much of `publish_wiki.sh` changes.
- `BACKLOG.md` — **new sub-section: "Defects filed by Phase 3 (Session 232)"**, immediately above the
  Phase 2 flags. Two plan defects with their repairs written out. They are Phase 5's, not Phase 4's.
- `scripts/publish_wiki.sh` — 10 old-name lines. **Phase 4 changes 7 and KEEPS `:19`, `:24`, `:42`.**
- `tests/test_wiki_no_line_citations.py` — `WIKI_DIR` at `:38` is assembled from path *parts*; K3 puts
  it in the same commit as the `git mv`.
- `PROJECT_LEARNINGS.md` — **131 learnings**; #129–#131 are this session's.

**Gotchas:**
1. **Phase 4's verification block has the defect this session filed.** `BEFORE != AFTER` on the clone's
   local `HEAD` reports *"HOOK FIRED AND PUBLISHED"* even when the push failed and the live wiki is
   stale. **Add `push --dry-run` before, and `rev-list --count origin/master..master` = 0 plus a
   `curl` of the live page after.** Do not trust the block as written. Learning [#129].
2. **Never `mkdir` the destination (dragon 3, K8).** `git mv` only. An empty-but-existing `SOURCE_DIR`
   passes every guard in `publish_wiki.sh` and its `rsync --delete` then **empties the public wiki and
   pushes it**. The route in is a failed one-shot `git mv` followed by reaching for the multi-source
   form, which needs a `mkdir`.
3. **The likeliest slip in the whole rename is a hyphen (dragon 4).** Writing
   `^docs/wiki/model-project-constructor/` into `.githooks/post-commit:18` produces no error, no
   failing test, and no output — the hook just exits 0 forever. **The repo uses `model_project_constructor`
   with underscores.** Nothing tests the hook; the only detector is an end-to-end observation that the
   clone advanced.
4. **K2: the clone's `origin` URL and `publish_wiki.sh:72`'s guard literal must move in the SAME
   commit.** They still both say the old name today, so they agree and publishing works. Change either
   alone and publishing stops (loudly — dragon 2).
5. **D-R5 keeps `publish_wiki.sh:19`, `:24`, `:42`.** Changing `:42` without a `mv` hard-fails the
   script at its own `:58` clone-exists guard. §7.2 (i) must print **exactly 3** after Phase 4 —
   `0` is broken at every point in the plan's life.
6. **Drive the sweep from the bare name, never the joined path (K6, dragon 11).**
   `tests/test_wiki_no_line_citations.py:38` builds the path from parts and `grep
   "docs/wiki/claims-model-starter"` **cannot see it** — it is the single line whose omission turns
   the suite red.
7. **`Evolution.md:266` is `24`, not the plan's `25`.** The sentence counts pages *"plus the sidebar"*.
   Filed in `BACKLOG.md`; do not paste the plan's number.
8. **§7.2 predicts 11 now.** A path *leaving* is a phase working; a path *appearing* means the plan
   drifted and §2 must be re-derived first.
9. **Still zsh. Single-quote every heredoc delimiter** — tenth session running that this has been free.
10. **The trim trigger is not armed.** `SESSION_NOTES.md` is well under the 1,500-line threshold after
    Session 231's fourth trim. Phase 4 is a normal session; do not trim.

### What Session 231 Did
**Deliverable:** **Fourth lossless trim of `SESSION_NOTES.md` — COMPLETE.** Sessions 227 → 225
archived into a new write-once shard; the live file went **1,530 → 840 lines**, four records, the
floor `CLAUDE.md` sets. **No phase of the repository rename ran. Phase 3 is still next.**

**Started / completed:** 2026-08-20. **Commits: three**, as `CLAUDE.md`'s "Two commits, always"
bullet requires — `b1e795e` (the Phase 1B claim, alone), `f3fea4e` (the trim, containing **no**
record edit — machine-verified, `added=0`), and this close-out. **Operator this session:** *"fourth
trim"*, chosen over Phase 3 of the rename.

Documentation-only, so **no `CHANGELOG.md` entry** — `PROJECT_CONVENTIONS.md` §2's cadence gate.
Sessions 227, 229 and 230 correctly added none either.

#### What moved

| | |
| --- | --- |
| Archived | Sessions **227, 226, 225** — 3 record headings, **738 lines**, byte-for-byte unedited |
| Into | `docs/architecture-history/SESSION_NOTES-S227-through-S225.md` (790 lines with banner) |
| Live file | 1,530 → **840 lines**, Sessions **231 → 228** |
| Routing | now **five** clauses; `225 ≤ N ≤ 227` → the new shard, `N ≥ 228` → this file |
| Also updated | `CLAUDE.md`, `README.md`, `BACKLOG.md`, `docs/methodology/PROJECT_CONVENTIONS.md` |

**The proof is [`SESSION_NOTES-S227-through-S225.md.verify.sh`](docs/architecture-history/SESSION_NOTES-S227-through-S225.md.verify.sh)**
— L0–L7 carried forward from the third trim, **plus L8 and L9**, and **50 mutants, all caught**.

#### The two new assertions, and why each existed as a hole first

**L8 (REACH)** — the copies of the shard set no assertion could see. The third trim's own pointer
block *named* two of them (`README.md`'s repo map, `PROJECT_CONVENTIONS.md`'s shard-naming rule),
said a trim that left either alone "ships a lie", and checked neither. **That list was also
incomplete.** One `git grep -l 'SESSION_NOTES-'` found a third nobody had named — **`BACKLOG.md`'s
read-cap item**, whose entire subject is the shard set and which said *"there are now **three**
unwatched shards"* — and the adversarial review found a fourth hiding in plain sight: **`CLAUDE.md`'s
own prose**, whose routing *table* L5 has always parsed while the *"there are THREE … grep all
three"* count words around it were read by nothing. A half-updated `CLAUDE.md` shipped green.
Learning [#126](PROJECT_LEARNINGS.md).

**L9 (LINEAGE)** — write-once enforced for **every** shard on disk. L7, introduced by the third trim
as *"the only enforcement `write-once` has ever had"*, guards exactly one file: the shard it shipped
with. S216 and S220 had none at all; S224's lives only inside its own proof, which nothing obliges a
session to run. And because every other assertion reads git history at the trim commit, **an ancestor
shard truncated or deleted on disk left the whole suite green.**

#### Four things measurement caught that reasoning did not

1. **`L2/b3` NO-LEAK fired on the very first run.** The banner's routing table shared a byte-identical
   line with the pre-trim front matter — nothing had leaked, but the assertion cannot tell that
   coincidence from a real leak. **Fixed the artifact (one clause per line), not the assertion.**
2. **A fourth declared substitution.** The third trim's parenthetical calling L7 *"the only
   enforcement write-once has ever had"* is false the moment L9 exists. Rewriting it kept the
   pointer block's "exactly four passages" claim true rather than softening the claim.
3. **The ancestor's `L5/2` was reachable by none of its 28 mutants** — the gap/overlap check, live
   code, never once exercised. Same defect the third trim caught in the second trim's `L2/b0`, one
   level down. Confirmed by measurement, not inference.
4. **And then I shipped it myself, in six arms of my own two new assertions** — one day after
   writing that exact rule into `CLAUDE.md`. The adversarial review measured it. Learning
   [#125](PROJECT_LEARNINGS.md).

#### The adversarial review earned its keep

**11 agents, 5 lenses, ~1.14M tokens, 13 findings survived verification** — deliberately built to
Session 230's learning [#124](PROJECT_LEARNINGS.md) (`maxItems` per lens, one adjudicator per lens)
rather than its 132-agent Review 1. **Two of its top findings I had already found and fixed
independently while it ran** (BACKLOG.md; the false "three of the four" count) and the synthesis
correctly dropped both as non-reproducing. The rest were real and all were fixed: `CLAUDE.md`'s
unchecked prose, the six untested arms, `SHARD_NAME` matching inside `.verify.sh` filenames, and a
typed count ("the first three clauses" — measured: **two**) inside a **write-once** file, which would
have been unrepairable one commit later.

#### Verification

- Proof **green**; `--self-test` **50/50**; **every assertion and every `if` inside it** reached by a
  mutant that only it catches (`L5/2 shape` M47, `L8/required` M50, `L8/forbidden` M44, `L8/set`
  M45+M46, `L8/unreadable` M49, `L9/no-add-commit` M48).
- **All three ancestor proofs re-run green** at this cut.
- Record zone vs `HEAD` is **pure removal**: concatenation identity `True`, **added = 0**.
- `SESSION_RUNNER.md` step 14 intact: `## ACTIVE TASK` → `### What Session 231 Did` adjacent.
- `uv run pytest -q` → **1230 passed, 9 skipped**, unchanged from Session 230's baseline.
- **Fired nothing.** No path touched is under `docs/wiki/claims-model-starter/` (the hook's guard)
  or matches `docs/*.md` (the workflow's single-level path list); nothing was pushed.

### Session 230 Handoff Evaluation (by Session 231)

**Score: 9/10.** It made the choice I had to make legible before I had to make it, and it was right
about the one thing that would have cost the most.

**What helped.**
- **Gotcha 10 is the reason this session was possible at all.** *"⚠ THE TRIM TRIGGER IS NOW LIVE …
  the next session should expect the operator to choose between Phase 3 and a fourth trim."* It then
  said exactly what a trim owes — a fourth shard, write-once, L0–L7 carried forward, **a mutant for
  every assertion added** — and pointed at `CLAUDE.md`'s bullet. Every one of those instructions was
  correct and load-bearing. **Session 230 declined to trim and said why** (a trim is its own
  deliverable; a bundled record edit holds the proof red forever). That restraint is what let this
  session's trim commit come out clean.
- **Gotcha 6** (*"Still zsh. Single-quote every heredoc delimiter"*) — ninth session running, still
  free, and I used heredocs constantly today.
- **Gotcha 4** (*"a line number into a file you are also editing is stale before you write it"*) —
  I cited section names and re-derived counts at the end. It is why the stale `788` line counts got
  caught before the commit rather than after.
- The Phase 3 pointer (*"find it with `grep -n '^### Phase 3'`, not by line number"*) is untouched
  and still correct — I confirmed the plan is unaffected by this trim (below).

**What was missing — one thing, and it is the same shape Session 230 itself found.**
`CLAUDE.md`'s trim bullet, which gotcha 10 correctly forwards to, names **two** prose copies outside
every proof and neither Session 230 nor its handoff questioned that list. There were **four**.
Session 230's own learning [#122](PROJECT_LEARNINGS.md) — *"a defect filed against the instance you
found is a defect filed against one instance; ask what class it belongs to"* — is precisely the tool
that finds them, and it applies to a list of instances just as much as to one. Learning
[#126](PROJECT_LEARNINGS.md).

Also minor: gotcha 10 says a trim "never retains fewer than 4 sessions" without noting that **the
Phase 1B stub counts as one of the four** — which is what all three previous trims did, and which
decides whether you archive two records or three. I inferred it from the third trim's banner.

**ROI: very high.** ~4 minutes to read; it set the whole session's shape.

### Session 231 Self-Assessment

**Score: 8/10.** The deliverable is right, is more thoroughly falsifiable than any of its three
ancestors, and closed two holes the project had written down and left open. It also shipped the
exact defect it had just finished documenting, and needed a review to find that.

**+** **I did not stop at the list I was handed.** Sweeping for the class turned `README.md` +
`PROJECT_CONVENTIONS.md` into four checked copies, and `BACKLOG.md` — the one a reader is routed to
for priorities — was silently describing a three-shard world.
**+** **L9 exists because I asked what L7 does *not* cover**, not because anything asked for it.
Deleting the 24,590-line S216 shard used to leave every proof green.
**+** **I fixed artifacts, not assertions, every time an assertion objected.** `L2/b3` fired on the
first run and the honest fix was to reflow my banner. Weakening it would have been the easy move and
the wrong one.
**+** **I measured before writing.** The coverage line, the "exactly four passages" count, the
enforcement count, every line number — each re-derived. Where I did type instead of measure, it was
wrong, and the file now says so in its own header.

**−** **I shipped six untested `if`s inside my own new assertions** the same day I wrote the rule
against that into `CLAUDE.md`. The review found them; my own neuter loop was at function level and
structurally could not.
**−** **I typed three counts that were wrong**: "three of the four had no enforcement" (two),
"the first three clauses" (two), and `788` lines in two files after the shard grew to 790. Two of
the three were in text that would have been **frozen forever** one commit later.
**−** **The builder/proof pair drifted three times** and `--self-test` stayed green through all
three, because L6 fired on every mutant and each was therefore "caught". Only the plain run showed
it. Learning [#127](PROJECT_LEARNINGS.md).
**−** **One near-miss worth recording:** a line-wise `grep` returned 0 for an inherited quotation and
I nearly "corrected" an accurate sentence in a frozen file. The phrase wrapped a line. Learning
[#128](PROJECT_LEARNINGS.md).

**Against the bar:** S227 executed an irreversible rename with every prediction tested; S228 shipped
28 mutants; S229 refuted a dragon with a measurement; S230 fixed a class rather than an instance.
This session did S230's move to a list rather than a defect, and raised the proof from 8 assertions
and 28 mutants to 10 and 50 — but needed an external review to hold it to a rule it had authored
hours earlier, which is the one thing the three sessions before it did not.

**What's next: Phase 3 of [`docs/planning/repository-rename.md`](docs/planning/repository-rename.md)**
— *"Published wiki content. **One commit. This one goes live to readers.**"* Unchanged by this
session. Find it with `grep -n '^### Phase 3'`; **do not cite it by line number.** Read **§2.4b**
first: D-R3 = yes, so Phase 3 carries the two title rebrands (`Home.md:1`, `_Sidebar.md:1`) that
**no `claims-model-starter` grep will ever surface**, and it **fires the wiki hook by design**.

**Key files:**
- `docs/architecture-history/SESSION_NOTES-S227-through-S225.md` — the new shard. **Write-once.**
  `grep` it; never `Read` it. **L9 in this and every future proof now enforces that on disk.**
- `docs/architecture-history/SESSION_NOTES-S227-through-S225.md.verify.sh` — the proof. Its header
  carries the neuter loops, the measured coverage, and the two footnotes about arms that cannot have
  a uniquely-catching mutant. **A fifth trim copies L0–L9 forward and adds a mutant per new
  assertion *and per new `if` inside it*.**
- `CLAUDE.md` — the trim bullet now says FOUR shards, lists six load-bearing copies, and tells the
  fifth trim to **re-derive that list rather than trust it**.
- `BACKLOG.md` — the read-cap item now says four unwatched shards and names all four. Its `924`
  figure for the S224 shard was wrong; corrected to the measured `933`.
- `PROJECT_LEARNINGS.md` — **128 learnings** now; #125–#128 are this session's.

**Gotchas:**
1. **The trim commit is `f3fea4e` and every assertion reads the artifacts AT THAT COMMIT.** Later
   edits to `SESSION_NOTES.md`, `CLAUDE.md`, `README.md`, `BACKLOG.md` or `PROJECT_CONVENTIONS.md`
   cannot make this proof red — including this close-out. **Except L9 and L7, which read the shards
   on disk today.** That asymmetry is deliberate; do not "fix" it.
2. **Run the plain proof, not just `--self-test`.** A green self-test with a red plain run happened
   three times today: L6 fires on every mutant when the banner has drifted, so all 50 are "caught"
   while the artifact is broken. Learning [#127](PROJECT_LEARNINGS.md).
3. **`--self-test` is not enough on its own either.** Neuter individual `if`s, not just whole
   assertions. Neutering `L5/2`'s shape arm **crashes** the run rather than surviving — read a
   traceback as *caught*.
4. **This trim does NOT falsify `repository-rename.md`.** Checked: its §3 arithmetic is pinned to
   commit `59615e2`, and every §7 exclusion is directory-prefixed (`^docs/architecture-history/`),
   so the new shard is absorbed automatically. **But** the 35 `claims-model-starter` hit-lines that
   were in `SESSION_NOTES.md` are now 13 there and 22 in the new shard, and
   `docs/architecture-history/**` is one file wider. **Phase 5 re-derives at `HEAD`; expect 52 file
   slots, not 51.** Nothing is fail-dangerous — the counts move, the classification does not.
5. **The S224 shard's banner is now stale** (it routes Sessions 225-and-up to the live file) and
   **may not be repaired** — write-once. That makes **two** frozen stale banners, with S220's. Ours
   joins them at the fifth trim. The live pointer block is the authority; a banner is a snapshot.
6. **Still zsh.** Single-quote every heredoc delimiter. Ninth session running.
7. **Rebuild derived artifacts from a clean checkout after editing their generator.** A constant
   declared in two places by construction drifts silently; `git checkout -- SESSION_NOTES.md &&
   rm <shard> && python3 <builder>` was the loop that kept it honest.
8. **`master` is IN SYNC with `origin/master`.** The operator directed the push at the end of this
   session and all eleven queued commits (Sessions 228–231) went up at `e314449`, clearing a
   five-session backlog. Two notes for whoever pushes next, because I got the second one wrong
   before checking: **Publish Tutorial did NOT fire** — correct, nothing matches its single-level
   `docs/*.md` path list — but **CI DID**, because `.github/workflows/ci.yml` triggers on *any*
   push to `master` with **no path filter at all**. It went green (ruff, mypy, pytest, the
   data-agent decoupling test — run `32417699067`). **A path-trigger audit that only reads the
   workflow you expect to fire is not an audit.**
9. **`~/Development/mpc_tests/model_project_constructor` is still on the old origin URL and no phase
   owns it** (learning #111, unchanged since Session 228). Give it a home in Phase 4 step 1.
10. **The trim trigger is quiet.** The trim left the file at **840 lines**; this close-out record
    brings it to **1,042** — still inside the rule's ≤1,050 cut-back target, and **458 lines below
    the 1,500 trigger**, so roughly **two or three sessions of runway** at this file's ~184-lines-
    per-record density. Note the shape: a trim's own record consumes a fifth of the headroom it
    just created. The next trim writes a **fifth** shard (never append to one of the four) and its
    proof carries **L0–L9** forward.

### What Session 230 Did
**Deliverable:** **Repair `docs/planning/repository-rename.md` — COMPLETE.** All six filed items,
**plus a seventh and eighth the repair itself uncovered — one of them fail-dangerous.** **No phase
of the rename ran.** Phase 3 is still next.

**Started / completed:** 2026-08-20. **Commits: two** — `be3bc4a` (the Phase 1B claim, on its own,
as always) and one more holding the repair **and** this close-out together — `git log --oneline -2`;
its hash cannot be written here, because writing it changes it. Sessions 227-229 each used
three, splitting the work commit from the close-out; those were *phase* commits, which
`repository-rename.md` requires to stand alone for bisect. **This session executed no phase**, so the
repair and its record are one docs commit. If you are executing a phase, go back to three.
**Operator this session:** *"repair docs/planning/repository-rename.md, and ONLY that."*

Documentation-only, so **no `CHANGELOG.md` entry** — `PROJECT_CONVENTIONS.md` §2's cadence gate.
Sessions 227 and 229 correctly added none either.

#### The six filed items, all repaired

| # | Was | Now |
| --- | --- | --- |
| 1 | Phase 4: *"`publish_wiki.sh` — all 10 lines"* | **CHANGE 7, KEEP 3.** `:19`, `:24`, `:42` are the D-R5-pinned filesystem path. **Fail-dangerous:** obeyed literally it hard-fails the script at its `:58` guard and stops wiki publishing. |
| 2 | Phase 4's and §7.3's `-> empty` greps | path-anchored exclusion **+ a positive 3-line assertion** |
| 3 | §7.2's allowlist had no exemption | a fifth group, **paired with assertions** so it is not a blindfold |
| 4 | §3's arithmetic | rebuilt — see §3.3 below |
| 5 | Dragon 1: *"same commit as `mkdocs.yml`"* | *"in Phase 2"*. **Dragon 1's finding is untouched.** |
| 6 | *"Status: PLAN. Nothing executed."* | the executed-phase ledger |

**The plan's own §9.1 "Repair log — Session 230" is the authoritative write-up.** It is written for
the Phase 3/4/5 executor and it is longer than this block should be. Read it there.

#### The filed spec was INCOMPLETE, and that is the most important thing this session found

Defect 3 was filed against `scripts/publish_wiki.sh` and its **3** permanently-pinned lines.
**`docs/planning/enterprise-migration.md` has 14 lines of exactly the same kind** — the
`~/Development/claims-model-starter.wiki` path D-R5 pins in place — and no allowlist group exempted
it either. **Repairing only the named file would have left Phase 5's DONE gate exactly as unreachable
as it was found**, which was the whole point of the item.

Worse: **Phase 5's residue rule** (*"anything that is neither a §3.1 historical record nor deliberate
self-reference is a miss — fix it here"*) **ordered an executor to rewrite all 17 pinned lines** to a
directory that does not exist. That is a **second fail-dangerous instruction**, the same shape as
defect 1, in a different phase.

**The fix is general, not another exception.** The plan gained a third classification bucket:
**§3.3 — "KEEP because D-R5 pins a filesystem path", 17 lines across 2 files.** §3.1 went back to its
original 552/28, §3.2 is 97/23, and `552 + 17 + 97 = 666` across `28 + 2 + 23 = 53` file-slots for 51
distinct files (two files sit on both sides). A future session finding a **third** such file puts it
in §3.3 and §7.2 group 3.

#### Two adversarial reviews, and the second one earned its keep too

**Review 1 (132 agents, 6 lenses, 3 skeptics per finding): 42 findings, 14 survivors.** The lead
survivor — reached independently by 4 of the 6 lenses — is the `enterprise-migration.md` gap above.
I confirmed it by hand before acting.

**Review 2 (4 agents, focused on the second pass only): 13 findings, every one reproduced with a
command.** Three mattered:

- **The exemption needed a THIRD assertion.** Group 3 exempts `enterprise-migration.md` wholesale,
  and assertion (ii)'s first `grep -v` removes the dual-purpose `diff -r` line **by construction** —
  so between them no §7 command could see the one line §3.3 itself calls a trap. Phase 5's new
  "leave every §3.3 line alone" then told the executor not to fix it. **A filter written to make the
  arithmetic reconcile silently removed the case that most needed checking.** Assertion **(iii)**
  now pins that line.
- **`git diff --stat -M` never prints `R100`.** I restated Phase 4's criterion as "22 R100 + 3 R0xx"
  against a command that emits no similarity code at all. **Measured in a scratch repo:**
  `git diff --stat -M | grep -c R100` → **0**. Now `--name-status -M` → 22 R100 + 3 R09x.
- **And my repair of that repair was also wrong.** I wrote *"none of the 25 may appear as delete+add,
  which is what a missing `git mv` looks like."* **Measured: a hand-rolled delete+add of identical
  files reports 25 R100 with no `git mv` anywhere** — `-M` detects renames from content similarity.
  The criterion can witness that the pages moved intact; it cannot witness which command moved them.

#### The citation lesson I had to learn twice in one session

I corrected two stale `BACKLOG.md` citations to fresh numbers measured at `HEAD` — and **this
session's own `BACKLOG.md` edit then shifted both by 28 lines**, so the "corrected" citations were
stale in the commit that shipped them. **A line number into a file the current session is also
editing is stale before it is written.** Every `BACKLOG.md` citation in the plan is now a quoted
section name that `grep` finds and no edit moves. Learning [#123](PROJECT_LEARNINGS.md).

Same class, caught earlier: three of my own `:411`/`:538` self-citations went stale *twice* as the
repair grew. All are section names now.

#### Verification

- **All four §7.2 commands run verbatim:** allowlist → **13** (all owned by Phases 3/4/5);
  (i) → 10 (correct pre-Phase-4); (ii) → 20; (iii) → 1.
- **Arithmetic re-derived from git, not copied:** `git grep -c` at `59615e2` → **666 lines / 51
  files**, unchanged by this repair; 552+17+97 = 666; 14+12+13+34+23+1 = 97.
- **The §7.2 ledger measured at every commit it names:** 20 / 17 / 15 with the 4-group command;
  18 / 15 / 13 with the 5-group one. Both readings are in the table, with a "Command" column,
  because the historical rows record what an executor at that commit would actually have seen.
- `uv run pytest -q` → **1230 passed, 9 skipped**; `ruff` clean; `mypy` clean, 68 source files.
- **Fired nothing, proved by before/after.** `publish-tutorial.yml`'s last run is still Phase 1's
  (`32335373755`) and the wiki clone is still at `41c7f72`. `docs/planning/` is two levels deep and
  the workflow triggers on `docs/*.md` (single-level); the hook needs `^docs/wiki/claims-model-starter/`.

### Session 229 Handoff Evaluation (by Session 230)

**Score: 9/10.** The best-targeted handoff in this chain. It did the one thing that matters most: it
told me exactly what to build and where the spec lived, then got out of the way.

**What helped.**
- ***"The full write-up, with every line citation verified against the file, is in `BACKLOG.md` under
  '⚠⚠ Two defects…'. Read it there — it is the deliverable's spec."*** Correct call. The six-item
  short form in the handoff let me size the job in 30 seconds; the BACKLOG block was the spec. **Every
  one of its six line citations (`:663-664`, `:723`, `:1173`, `:1119-1123`, `:276`/`:325`, `:789`,
  `:3`) verified exactly** against the working tree. That is a striking improvement on the drift
  Session 229 itself scored Session 228 for.
- **Gotcha 1** (*"a `-f` on a piped `curl` proves nothing"*) — reusable beyond its own session; it is
  now written into dragon 1 so the next reader meets it.
- **Gotcha 2** (*"Do not 'fix' the three surviving lines"*) and **gotcha 3** (*"line numbers moved
  +8/+13; re-derive with `grep -n`"*) — both load-bearing, both acted on.
- **Gotcha 7** (*"still zsh, single-quote every heredoc delimiter"*) — eighth session running, still
  free.
- Ordering item 1 first and labelling it **fail-dangerous** was right; it is the one that had to be
  correct.

**What was wrong — one thing, and it is the interesting one.**
**The spec was incomplete, not inaccurate.** Item 3 named `publish_wiki.sh` and stopped. The same
defect in `enterprise-migration.md` is 14 lines to that file's 3 — and Session 229 had *already
measured* enterprise-migration.md's D-R5 lines while writing the flags above the very same block
("the nine D-R5 filesystem paths"). The two facts were in one file and never met. **A defect filed
against the instance you found is a defect filed against one instance; ask what class it belongs to
before you file it.** Learning [#122](PROJECT_LEARNINGS.md).

Also minor: gotcha 3's *"+8 in the 800s, +13 by the 1500s"* is not right — measured, the cumulative
offset is +8 / +11 / +12 / +13 / **+21**, non-uniform. The *instruction* (re-derive with `grep -n`)
was correct and is what mattered.

**ROI: very high.** ~5 minutes to read, and it pointed at a spec that was right about everything it
covered.

### Session 230 Self-Assessment

**Score: 7.5/10.** The deliverable is right and materially better than what was asked for. It took
three passes to get there, and two of those passes were fixing my own work.

**+** **I did not stop at the filed spec.** The second file was worth more than the six items
combined: without it the session would have shipped a "repaired" gate that still could not go green,
with a commit message saying it was fixed.
**+** **The fix is a bucket, not an exception.** §3.3 gives a third such file somewhere to go.
**+** **I measured every prescription before writing it.** `--exclude` vs a path-anchored `grep -v`:
measured, and `--exclude` is genuinely too wide — a probe at `packages/probe/publish_wiki.sh` went
undetected. `--stat` vs `--name-status`: measured. Whether `-M` can witness `git mv`: measured, and
it cannot.
**+** **I ran the two reviews adversarially and acted on what survived**, including when what survived
was "your repair has the same defect you were sent to fix."

**−** **I shipped three wrong things of my own and caught them only by review.** The `--stat`/R100
criterion; the delete+add claim that replaced it; and assertion (ii)'s filter that hid the very line
§3.3 calls a trap. Each was written confidently and none was measured before writing. **My own rule —
measure the prescription — I applied to the plan's advice and not to my own.**
**−** **Line-number discipline: I lectured about it in §9.1 and then broke it twice in the same
session**, once inside the bullet doing the lecturing.
**−** **Review 1 cost 132 agents and ~8M tokens** against a 15-agent guideline. I capped findings per
lens at zero and let 42 findings × 3 refuters run. Review 2 — 4 agents, `maxItems: 4` — found three
real defects for 570k tokens. **The second design was ~14× cheaper and did not obviously find less.**
Learning [#124](PROJECT_LEARNINGS.md).
**−** **A python edit script that writes only at the end silently lost two applied edits** when a
later `sub()` aborted. I caught it by re-reading §7.2, not by any check. Write after every edit.

**Against the bar:** S227 executed an irreversible rename with every prediction tested; S228 shipped
28 mutants; S229 refuted a dragon with a measurement. This session found that the *spec it was given*
was incomplete in the same way the plan was, and fixed the class rather than the instance — but it
needed two review rounds to stop introducing new defects, which the three sessions before it did not.

**What's next: Phase 3** — `docs/planning/repository-rename.md`, "Published wiki content. **One
commit. This one goes live to readers.**" It is the first phase readers see, and **it fires the wiki
hook by design**. D-R3 = yes, so it carries the two title rebrands (`Home.md:1`, `_Sidebar.md:1`)
that **no `claims-model-starter` grep will ever surface** — §2.4b says so explicitly. Read §2.4b
before you start.

**Key files:**
- **`docs/planning/repository-rename.md`** — now **1,680 lines** (was 1,261). **New: §3.3** (the
  D-R5 bucket) and **§9.1** (the repair log — read this first). §7.2 now has **four** commands, not
  one. Phase 3 is the section headed *"Phase 3 — Published wiki content"*; **find it with
  `grep -n '^### Phase 3'`, not by line number — this file moved by 419 lines this session and every
  citation into it that predates today is wrong.**
- **`BACKLOG.md`** — the two-defects block is closed and shrunk to a carry-forward pointer; the
  plain-language index row at `:51` was updated in the same commit per that file's own rule. **The
  three flags to `enterprise-migration.md`'s owner above it are all still open** and still need the
  operator's ruling on restating the clone-independence criterion as *"no repository name other than
  the clone's own"*.
- `scripts/publish_wiki.sh` — `:19`, `:24`, `:42` keep the old name **forever** (§3.3). `:2`, `:11`,
  `:23`, `:44`, `:63`, `:72`, `:75` change in Phase 4.
- `docs/planning/enterprise-migration.md` — **14 lines keep the old name forever** (§3.3); one of
  them, the `diff -r` line, is dual-purpose and Phase 4 must edit half of it.

**Gotchas:**
1. **§7.2 is now FOUR commands and they are one criterion.** Running only the allowlist is running a
   blindfold — that is stated in the section and it is not rhetorical. Assertion **(iii)** exists
   because (ii) filters out the dual-purpose line by construction.
2. **Assertion (i) prints 10 before Phase 4 and that is CORRECT.** Do not "fix" it by applying Phase
   4's edit early: that flips the `:72`/`:75` guard while the clone's origin still carries the old
   name and **disables publishing** (dragon 2), breaking K2/K3.
3. **Never `sed` `enterprise-migration.md`'s `diff -r` line.** Both halves match the old name; only
   the left one changes. `grep -n "diff -r -x '.git'"` finds it.
4. **A line number into a file you are also editing this session is stale before you write it.**
   This bit me twice. Cite section names; re-derive with `grep -n` at the end.
5. **`git diff --stat -M` prints no similarity codes.** Use `--name-status -M`. And `-M` cannot tell
   `git mv` from delete+add — measured, both give R100.
6. **Still zsh.** Single-quote every heredoc delimiter. Eighth session running.
7. **Write your edit script's output after EVERY edit**, not at the end. A late `sys.exit(1)`
   discarded two applied edits this session and nothing flagged it.
8. **`master` is now 8 commits ahead of `origin/master`** and nothing here needs pushing. Four
   sessions have left it that way; the push is the operator's call.
9. **`~/Development/mpc_tests/model_project_constructor` is still on the old origin URL and no phase
   owns it** (learning #111, unchanged since Session 228). Give it a home in Phase 4 step 1.
10. **⚠ THE TRIM TRIGGER IS NOW LIVE.** This file crossed **1,500 lines** when this record landed —
    `CLAUDE.md`'s retention rule fires above 1,500, cuts back to ≤1,050, and never retains fewer than
    4 sessions. **I did not trim**, deliberately: a trim is its own deliverable and its own session
    ("1 and done"), and `CLAUDE.md` forbids a trim commit that also contains a record edit — which is
    exactly what bundling it into this close-out would have produced, holding the proof red forever.
    **The next session should expect the operator to choose between Phase 3 and a fourth trim.** If
    it is the trim: it writes a **fourth** shard (write-once — never append to the three existing
    ones), and its proof must carry L0-L7 forward plus a mutant for every assertion it adds. Read
    `CLAUDE.md`'s "SESSION_NOTES.md is trimmed" bullet in full first; the rate rule from the
    canonical trimmer does **not** apply at this file's density.

### What Session 229 Did
**Deliverable:** **Phase 2 of [`docs/planning/repository-rename.md`](docs/planning/repository-rename.md)
(`:545-589`) — COMPLETE.** Inert prose plus the other plans' broken assertions. Three files edited,
plus the flags dragon 1 mandates, in **one commit** as the plan requires.

**Started / completed:** 2026-08-20. **Commits:** `b39122c` (Phase 1B claim, its own commit),
`73b9418` (Phase 2), and this close-out.

**Operator this session:** *"rename Phase 2"*, then a second ruling mid-session — see "The decision
I put to the operator" below.

#### What changed

| File | Change |
| --- | --- |
| `SECURITY.md:9` | advisory URL → new name. **1 old-name hit → 0.** |
| `CONTRIBUTING.md:6` | Contributing wiki-page URL → new name. **1 → 0.** |
| `docs/planning/enterprise-migration.md` | the five `curl` criteria (`:831`,`:832`,`:833`,`:1356`,`:1520`), the two `# → unchanged, still the public wiki` comments (`:1311`,`:1358`), and the re-remote prohibition at C4 step 4 + dragon #21 — **reworded, not deleted** |
| `BACKLOG.md` | the dragon-1 flag, the Phase 5 residue, and the two plan defects below |

**§7.2's allowlist went 17 → 15** — exactly the two files that reached zero. Re-derived, not assumed.

#### Dragon 1's prescribed repair does not work, and I measured that before applying it

The plan says of the five `curl` criteria: *"Add `-fL` while you are there so a future rename fails
loudly instead of vacuously."* **Measured, and it is cosmetic:**

    curl -sfL <LIVE sitemap> | grep -c audits   →  prints 0, exits 1
    curl -sfL <404  sitemap> | grep -c audits   →  prints 0, exits 1     ← identical

A pipeline reports **its last** command's status, so `-f` on the *first* command is invisible, and
`grep -c` prints `0` on empty input either way. The vacuous pass dragon 1 exists to close survives
its own prescription. What I shipped instead: the two sitemap checks capture **curl's own exit**
(`sitemap=$(curl -sfL …) || echo FAIL`), and the two 404-expecting checks get a **positive control**
ahead of them, because a host that 404s every path makes "→ 404" meaningless. `-fL` is applied where
it is genuinely load-bearing — `:1356`, which expects 200 (measured: prints the code, exits 0 on
200, non-zero on 404). Learnings [#117](PROJECT_LEARNINGS.md), [#118](PROJECT_LEARNINGS.md).

#### The instruction conflict, resolved as the plan directed

`enterprise-migration.md`'s C4 step 4 and dragon #21 both forbade *"re-remote
`~/Development/claims-model-starter.wiki`"* — the exact act Phase 4 of the rename requires. Both
sites now say the ban is on the **destination** (the enterprise wiki), not on the command, and both
name Phase 4's re-point at the **original's** wiki under the new name as the thing that *preserves*
the property. **Dragon #21 is still present and still a live warning** — the plan said reword, not
delete. `grep -n "re-remote"` now returns one line, the reworded one.

#### I did NOT touch the clone-independence pattern, and that was the work item

The Phase 2 table lists `:363`, `:1308`, `:1351` — yet dragon 1 ends *"Flag this to whoever owns
`enterprise-migration.md`; **do not silently rewrite another plan's acceptance criteria beyond the
five URL lines above**."* The two are reconciled by reading the table row as **"file the flag"**, not
"edit the greps". Twelve independent adversarial verifiers reached the same reading from the plan's
§8 (`:1220-1222`, *"This plan only repairs the five verification lines"*). The greps are untouched;
`BACKLOG.md` carries the flag. Learning [#119](PROJECT_LEARNINGS.md).

**And the flag carries a measurement that refutes dragon 1's own recommendation.** It proposes
path-scoping the check over *"`scripts/`, `.githooks/`, `mkdocs.yml` and `tests/` only."* **Measured:
350 hits, 284 of them legitimate `from model_project_constructor…` imports in `tests/`, plus 15 in
`scripts/run_pipeline.py`.** Unsatisfiable — the identical objection dragon 1 raises against the
fifth-alternative fix. The workable set is the four §2.6 coupling files, and it needs the criterion
restated as "no name **other than the clone's own**". That is an operator ruling, not the rename
plan's to make.

#### The decision I put to the operator, and why

**Walking §7 backwards against the phases** (Session 227's gotcha 8, inherited from Session 228's
handoff — the single highest-value line in it) found **two defects in `repository-rename.md`
itself**, one fail-dangerous. Both are written up in full in `BACKLOG.md` under
*"Two defects in `repository-rename.md` ITSELF"*; the short form:

- **A.** Phase 4 is told to change `publish_wiki.sh` *"all 10 lines"*, but `:19`, `:24`, `:42` hold
  the **filesystem path** D-R5 pins, and the plan's own `:411` says changing `:42` **hard-fails the
  script at its `:58` guard**. Correct split: change 7, keep 3. Then `:723`, `:1173` and **§7.2's
  allowlist — Phase 5's DONE gate — all go red on a *correct* Phase 4**, because none of them
  exempts `scripts/publish_wiki.sh` while `:1134` rules *"If the command prints a path, that file
  was missed. No judgment call."*
- **B.** Dragon 1's `:789` says *"Fix all five in the same commit as `mkdocs.yml`"* — a Phase 1 file,
  from a phase that explicitly disclaimed those lines at `:504` and closed without them (`c1fe06f`,
  three files, none of them `enterprise-migration.md`).

Fixing them would have widened Phase 2 from a three-file table to four and edited the governing
plan. **I asked rather than decided; the operator ruled `Separate session`.** It is the next
session's deliverable, before Phase 3.

#### Verification — everything, and the two baselines that could only be read as a pair

- **Fired nothing, proved by before/after, not by reasoning.** `publish-tutorial.yml`'s last run is
  still Phase 1's (`32335373755`, 2026-08-20T05:22:48Z) and the wiki clone is still at `41c7f72`,
  identical before and after the commit. The trigger list is `docs/*.md` (single-level), `mkdocs.yml`,
  the workflow file, `pyproject.toml`; `enterprise-migration.md` is two levels deep and the other
  three files are at the repo root. The hook needs `^docs/wiki/claims-model-starter/`; zero such paths.
- **The plan's own Phase 2 verification block, run verbatim:** the `rmsharp.github.io/claims-model-starter`
  grep prints **nothing**; `grep -n "re-remote"` returns **one** line, the reworded one, with dragon
  #21 intact.
- **§7.2 allowlist 17 → 15**, re-derived by running the command, and the two that left are exactly
  `SECURITY.md` and `CONTRIBUTING.md`.
- `uv run pytest -q` → **1230 passed, 9 skipped**; `ruff` clean; `mypy` clean, 68 source files.
- **GitHub's rename redirects, measured rather than assumed:** the repo and wiki web URLs 301 to the
  new name; `git ls-remote` on **both** wiki URL spellings returns `41c7f72`; `gh api
  repos/rmsharp/claims-model-starter/releases` returns 2, exit 0. That is why the four residual
  command lines are cosmetic and were left for Phase 5.

#### One defect I found by running a line I was only reading

`enterprise-migration.md:1372`'s C5 criterion is `gh repo view rmsharp/claims-model-starter --json
isPrivate,archived`. **`archived` is not a `gh repo view` field — it is `isArchived`.** It exits 1
with *"Unknown JSON field"* under **both** names, so this criterion has never been able to pass, and
the rename did not cause it. With the field corrected it returns `{"isArchived":false,"isPrivate":false}`
— the expected `false, false` — **even under the old name**, via the redirect. Filed, not fixed:
it is outside the five lines dragon 1 authorises. Learning [#117](PROJECT_LEARNINGS.md).

### Session 228 Handoff Evaluation (by Session 229)

**Score: 9/10.** The highest-value handoff I have been handed in this chain, and its value came from
one sentence.

**What helped, and it is not close.** *"**And before starting, walk §7 backwards against the
phases** (Session 227's gotcha 8; it is what found the orphaned clone, too late)."* That instruction
— inherited, not invented, and passed on with its provenance intact — is the entire reason this
session found the two defects in `repository-rename.md`. Nothing in Phase 2's own scope would have
surfaced them: they live in Phase 4's step list and §7's criteria, neither of which a Phase 2
executor has any reason to open. **A handoff that transmits a *method* outperforms one that
transmits facts.**

**Also load-bearing:**
- *"It is the cheapest phase: it touches no file on `publish-tutorial.yml`'s trigger list and none
  under `docs/wiki/`, so it fires neither the deploy nor the wiki hook."* **Verified true** against
  the workflow's `paths:` list and `.githooks/post-commit:18`. I measured before/after anyway — but
  knowing the expected answer is what made the measurement cheap.
- *"**Reword it; do not delete it** — it is still a live warning about the *enterprise* wiki."* on
  dragon #21. Exactly right, and it named the obvious wrong move before I could make it.
- Gotcha 5 (*"still zsh, single-quote every heredoc delimiter"*) — seventh session running, still
  free, and I used heredocs throughout.
- Gotcha 6 (*"every phase stays on a direct commit to `master`"*) — followed.
- *"§7.2's allowlist … still prints **17**"* — **the number was right**, and re-deriving it cost one
  command precisely because I knew what it should say.

**What was wrong — three navigational citations, all minor, all the same class.**
- *"Phase 2 is at `:528-600`"* — `:528` sits inside **Phase 1's** bash block (a stylesheet grep).
  The Phase 2 heading is `:545`; the section ends at `:589`.
- *"§7.2's allowlist is at `:1097`"* — `:1097` is **§7.1's heading**. §7.2 is `:1114`, its command
  `:1119-1123`.
- *"eleven lines of `docs/planning/enterprise-migration.md`"* — the plan's table carries **twelve**
  citations across four rows, and two of those are ranges, so the true line count is higher still.

**The pattern is worth naming, because it is not laziness.** Every number that *carried an
assertion* was correct: 17 allowlist paths, the trigger-safety claim, the three-commit rule, the
1,039-line trim reading. Every number that was merely *navigational* had drifted. Citations into a
1,250-line plan go stale between sessions; assertions do not. Cost me perhaps a minute each —
headings are greppable.

**What was missing.** Nothing I can fairly charge to it. It repeated the plan's *"add `-fL` while
there"* without flagging that the advice does not work — but that is the plan's error, not the
handoff's, and nobody had measured it before this session.

**ROI: very high.** ~4 minutes to read; it produced the method that found two defects the plan had
carried unnoticed since Session 226.

### Session 229 Self-Assessment

**Score: 8.5/10.**

**+** **I measured the prescription, not just the diagnosis.** The plan told me to add `-fL`; I ran
it first, found it changes nothing inside a pipeline, and shipped a repair that closes the hole.
Applying it literally would have produced a green-looking commit that left dragon 1's fail-open
exactly where it was — with a commit message saying "fixed".
**+** **I held the line on "flag, don't rewrite"** even though the Phase 2 table lists those three
greps as work items, and reconciled the two readings from the plan's own §8 rather than picking one.
**+** **I refuted a dragon with a measurement.** Dragon 1's recommended path-scoping is unsatisfiable
at 284 import lines, and the flag says so with the number rather than deferring politely.
**+** **I ran a line I was only supposed to be reading**, and found a C5 criterion that has never
been able to pass, for a reason that predates the rename.
**+** **I asked instead of deciding** on the one thing that would have widened the deliverable — and
kept every independent piece of work moving while I asked, so nothing was blocked on the answer.
**+** **Before/after baselines on both publish mechanisms**, rather than reasoning from the trigger
list to "it cannot have fired".

**−** **I nearly shipped `-f` on the two 404-expecting `curl`s.** My first draft applied it
uniformly to all five lines. On a line whose *expected* result is 404, `-f` makes the expected
outcome exit non-zero — wrong in the opposite direction. I caught it only because I ran the matrix
instead of reasoning about the flag.
**−** **My first BACKLOG flag carried two wrong line numbers** (`:911` for `:919`; `:1362` filed as
residue when it belongs to the independence group). The cause is precisely the failure I scored
Session 228 for above: I wrote citations from a `grep` taken **before** my own edits shifted the
file, then presented them as working-tree lines. I caught it by re-deriving. I should not have
needed to.
**−** **I spent 42 agents and ~2.5M tokens to surface 2 survivors.** The 40 refutations were not
waste — they produced the phase-ownership map that told me what *not* to touch, which is most of
what Phase 2 actually needed. But I designed the fan-out for the survivors and got the map as a
by-product. [#120](PROJECT_LEARNINGS.md) is me writing down what I should have planned for.
**−** I did not re-run `git status` between drafting the flag and citing line numbers in it — the
one mechanical habit that would have prevented the minus above.

**Against the bar:** S227 executed an irreversible rename with every prediction tested; S228 shipped
28 mutants and the first enforcement the write-once rule ever had. This session shipped a smaller,
cheaper deliverable — and found that the document governing the remaining three phases carries a
fail-dangerous instruction and an unsatisfiable completion gate. It also declined the tempting fix
and put the call to the operator.

**What's next: repair `docs/planning/repository-rename.md`, and ONLY that.** Not Phase 3. The
operator ruled this on 2026-08-20 when I put the choice to them: the plan's own defects get their
own session rather than widening Phase 2. **The full write-up, with every line citation verified
against the file, is in `BACKLOG.md` under *"⚠⚠ Two defects in `repository-rename.md` ITSELF"*.**
Read it there — it is the deliverable's spec, and it is longer than this block should be.

The short form, so you can judge the size before you open it:

1. **`:663-664`** — change *"all 10 lines"* to **7 change / 3 keep**. `:19`, `:24`, `:42` are the
   D-R5-pinned filesystem path; the plan's own `:411` says touching `:42` hard-fails the script at
   its `:58` guard. **This is the fail-dangerous one and it lands in Phase 4, the plan's riskiest.**
2. **`:723` and `:1173`** — split each `-> empty` grep in two, so the 3 surviving lines are asserted
   rather than forbidden.
3. **§7.2's allowlist (`:1119-1123`)** — add `^scripts/publish_wiki\.sh$`, **paired with the 3-line
   assertion**. Allowlisting the file alone would blind §7.2 to a real future miss there, which
   `:1134` explicitly forbids. Without this, **Phase 5's DONE gate can never go green.**
4. **§3's arithmetic (`:276`, `:325`)** — 3 lines move CHANGE → KEEP, so `publish_wiki.sh` lands in
   both §3.1 and §3.2 and the 28+23=51 file counts need a footnote, not a silent bump.
5. **`:789`** — *"Fix all five in the same commit as `mkdocs.yml`"* → *"Fix all five in Phase 2."*
   Reword only; **do not delete dragon 1**, whose fail-open finding is correct and is why Phase 2
   existed.
6. **`:3`** — *"**Status:** PLAN. Nothing in this document has been executed."* False since
   `c1fe06f`. Phase 5 owns it at `:750`; do not leave it standing through a plan-repair session.

**After that session: Phase 3** (`:591-631`) — published wiki content, and **the first phase that
goes live to readers**. It fires the wiki hook by design.

**Key files:**
- **`BACKLOG.md`**, the rename item — now carries two new sub-blocks: the three flags to
  `enterprise-migration.md`'s owner, and the two plan defects. The plain-language index row at
  `:51` was updated in the same commit, per that file's own maintenance rule.
- **`docs/planning/repository-rename.md`** — Phase 2 `:545-589` (done), Phase 3 `:591-631`,
  Phase 4 `:633-734`, Phase 5 `:736-757`. §7 is `:1095-1217`. **§7.2's allowlist prints 15 now**
  (was 17; `SECURITY.md` and `CONTRIBUTING.md` left).
- `docs/planning/enterprise-migration.md` — Phase 4 owns **exactly 17** `docs/wiki/claims-model-starter/`
  path lines in it, a mechanically exact count (`grep -c`), and `:678` says so. Four residual
  old-name lines (`:345`, `:919`, `:1250`, `:1372`) belong to Phase 5, classified in `BACKLOG.md`.
- `scripts/publish_wiki.sh` — `:19`, `:24`, `:42` keep the old name **forever** under D-R5;
  `:2`, `:11`, `:23`, `:44`, `:63`, `:72`, `:75` change in Phase 4.

**Gotchas:**
1. **A `-f` on a piped `curl` proves nothing.** The pipeline reports its *last* command's status.
   If you ever assert on `curl … | grep -c`, capture curl's exit separately. Measured this session;
   it is why dragon 1's own prescription failed.
2. **Do not "fix" the three surviving `claims-model-starter` lines in `publish_wiki.sh`.** They are
   D-R5's answer, not a miss. Any sweep that drives that file to zero breaks publishing.
3. **`enterprise-migration.md`'s line numbers moved this session** (+8 in the 800s, +13 by the
   1500s). Re-derive with `grep -n` before citing; do not copy numbers out of Session 228's or this
   session's prose without checking. This is the mistake I made and caught.
4. **The independence-pattern greps at `:363`, `:1319`, `:1363` are deliberately untouched.**
   Dragon 1 forbids rewriting them; the flag in `BACKLOG.md` is the discharge. A future session that
   "completes" them is undoing this session's work.
5. **GitHub redirects the repo, git remotes and the wiki — but not Pages.** Measured again this
   session. That is why four residual old-name command lines still work and are not urgent.
6. **`master` is 5 commits ahead of `origin/master`** and nothing here needs pushing. Sessions 228
   and 229 both left it that way; the push is the operator's call.
7. **Still zsh.** Single-quote every heredoc delimiter. Seventh session running, still free.
8. **`~/Development/mpc_tests/model_project_constructor` is still on the old origin URL and no phase
   owns it** (learning #111, unchanged from Session 228 — I did not touch it). Give it a home in
   Phase 4 step 1.

### What Session 228 Did
**Deliverable:** **The THIRD trim of `SESSION_NOTES.md` — COMPLETE.** Sessions 224 → 221 (891 lines,
4 records) are archived into
[`docs/architecture-history/SESSION_NOTES-S224-through-S221.md`](docs/architecture-history/SESSION_NOTES-S224-through-S221.md),
frozen and byte-for-byte unedited, beside a proof that ships **eight assertions and twenty-eight
mutants**. The live ledger went **1,681 → 826 lines** at the trim commit, and **1,039** once this close-out
record landed in it — that second number is the one the next session actually opens, and both are
under the 1,050 target.

**Started / completed:** 2026-08-20. **Commits:** `ff7f064` (Phase 1B claim — **its own commit, no
trim in it**), `e4ca944` (the trim — **no record edit in it; the proof reports `added: 0`**), and
this close-out. Three commits, exactly as `CLAUDE.md` requires.

**Operator this session:** *"2"* — the trim, chosen over Phase 2 of the repository-rename plan when
Phase 0 offered both. **Phase 2 of the rename is untouched and is still the next thing.**

#### The cut, and why this depth

| Retain | Live file would be | Verdict |
| --- | --- | --- |
| 3 (228→226) | 536 lines | **illegal** — below the 4-session floor |
| **4 (228→225)** | **826 lines** | **CHOSEN** — under the 1,050 target, exactly at the floor |
| 5 (228→224) | ~1,058 lines | rejected — **8 lines over** the target |

Computed for all three depths before choosing, not eyeballed. Retaining four also buys real
hysteresis: at ~200 lines/record the 1,500-line trigger will not fire again for roughly three more
sessions. Session 228's own Phase 1B stub counts toward the four, which is the precedent Session
224 set.

**Losslessness was checked twice, by two toolchains.** The proof's L1 does it in Python; separately,
`sed`/`cat`/`cmp` reconstructed the pre-trim file from the two artifacts — **sha256
`106e8eee…`, byte-identical** to `git show ff7f064:SESSION_NOTES.md`.

#### The proof gained three assertions, and every one came from a review that refuted it

I ran a four-lens adversarial review before committing. It returned **`confirmed: []` — all four
findings refuted.** Every refuter also wrote *"mechanically reproduced"* / *"the mechanics are
accurate"* and then refuted on **severity**: breaks no stated rule, falsifies no written claim,
loses no data. That is the exact split [learning #100](PROJECT_LEARNINGS.md) was filed for, and it
is how the ancestor's L4 came to exist. **All four were acted on. All four improved the deliverable.**

| New | What it pins | Why it exists |
| --- | --- | --- |
| **L5** | the routing table — **bounds AND filenames** — in all three copies (live pointer, shard banner, `CLAUDE.md`), then **anchored against the record ids the named files actually contain** | my first draft parsed only the integers; a probe that swapped two filenames and touched no digit passed silently — the whole failure L5 exists to remove, alive inside L5 |
| **L6** | the shard's banner, byte-for-byte | it was the one part of the shard that was neither frozen nor checked, while asserting in its own text *"Provenance is proved here, not asserted."* A probe rewrote its headline to claim a different session range and everything stayed green |
| **L7** | the shard **on disk today** is still the bytes the proof was written about | **write-once had no enforcement anywhere.** Everything else reads git history at the trim commit |

**L7 was verified against the committed ancestor, not in simulation.** Move `SESSION_NOTES-S220-through-S217.md`
aside and its proof prints *"still present, in the right file"* and **exits 0**. Do the same to the
new shard and the new proof exits **1**. A one-character edit that preserves length and record ids
also exits 1.

**L7 is asymmetric on purpose, and the asymmetry was written by a refutation.** The verifier that
killed the finding ran the decisive counter-experiment: force the ancestor down a worktree-reading
branch and it goes **red today**, because the live file has legitimately changed since its cut —
*"the proof red forever with zero data loss"*, the precise shape `CLAUDE.md` names as the thing to
avoid. That objection is correct and it kills the naive fix. It also specifies the one that works:
compare **only** the write-once artifact, never the ledger that is supposed to change. Learning #116.

#### One defect I shipped and caught myself

**The self-test reported `all 28 mutants caught` while catching most of them for the wrong reason.**
To make L7 reachable before the trim was committed, the harness passed a synthetic 40-zero commit
id; that id made every `git show <sha>:<path>` in L5's reality anchor fail, so **the same two
`L5/4` codes appeared on all 28 rows**, including mutants that touch nothing near those files. The
summary line was green and meaningless. It is visible only in the per-mutant attribution column.
Fixed structurally — L7's applicability now comes from the artifact it compares, so no caller ever
has to invent a value. Learning #113.

#### Measured coverage, not asserted

    L0 (none)  L1 (none)  L2 M10-M13  L3 (none)  L4 (none)  L5 M16-M24  L6 M25,M26  L7 M27,M28

Leave-one-out, re-derived as the last step before commit; the command is in the proof's header.
**All three assertions this cut adds are load-bearing alone.** Four are not, and the header says so
— including that **L4 lost its unique coverage to L5's reality anchor during this very session**
(L5/4 sees a whole-record boundary shift too). L4 is kept deliberately: it states the cut key
directly rather than inferring it. Learning #114.

#### Four describing documents were falsified by this cut, and one cannot be repaired

`CLAUDE.md` (three sites), `README.md`'s repo map, `docs/methodology/PROJECT_CONVENTIONS.md`
(*"Two instances so far"*) and `BACKLOG.md`'s read-cap item were all corrected here — the
[#101](PROJECT_LEARNINGS.md) sweep. **`CLAUDE.md`'s copy is now in the canonical clause form and is
read by L5**, so it can no longer go stale silently — and, as a consequence worth knowing before it
surprises you, **`CLAUDE.md` must be part of any future trim commit or that trim's proof is red from
its first run.**

**The fifth cannot be fixed. The S220 shard's banner says *"the live ledger when N ≥ 221"*, which
this trim falsified.** That file is write-once, its proof predates any assertion that could notice,
and nobody may edit it. A copy of a mutable fact inside a frozen artifact is a landmine armed by the
*next* change — learning #115. The new shard's banner therefore labels its own table a snapshot,
names the live pointer block as the authority, and cites the S220 banner as the observed instance.

#### Verification — everything, with the two that could have lied

- **All three proofs green, all three self-tests green**: S216 9/9, S220 15/15, S224 **28/28**.
  Neither ancestor shard was modified (`git diff` over `docs/architecture-history/` is empty).
- **The rename plan's §7.2 allowlist is unmoved: 17 → 17**, verified by **sorted set difference in
  both directions** (#109), not by count. Nothing appeared; nothing disappeared. The new shard
  contains **0** `claims-model-starter` hits and the live file keeps all **22**, so Phase 2 inherits
  no drift.
- `uv run pytest -q` → **1230 passed, 9 skipped** — identical to Session 227's baseline.
- **Fires nothing.** `publish-tutorial.yml`'s filter is `docs/*.md`, single-level; the shard is two
  levels down. The wiki hook needs `^docs/wiki/claims-model-starter/`; zero such paths touched.
- **`SESSION_RUNNER.md` step 14 intact**: `## ACTIVE TASK` → `### What Session 228 Did` are adjacent.
  Step 18's ghost check is a frontier comparison and cannot false-positive on a trim.

### Session 227 Handoff Evaluation (by Session 228)

**Score: 8/10.**

**What helped, concretely.** The paragraph headed *"⚠ But read this first: the trim trigger has
fired"* is the whole reason this session went cleanly. In five lines it established that the
threshold was crossed, that the decision is **a judgment call with hysteresis and the operator's to
make**, that a trim is **its own deliverable and its own session**, that it needs **three separate
commits**, and that **the trim commit must contain no record edit** — and it said *do not bundle it
with Phase 2*. I did not have to derive any of that, and the operator had a real choice to make in
Phase 0 because Session 227 had framed one.

**What was missing — the deduction.** It pointed at `CLAUDE.md`'s rules rather than walking them,
and two consequences of a trim were nowhere: that the cut falsifies prose in `README.md`,
`PROJECT_CONVENTIONS.md` and `CLAUDE.md` (the project already has **learning #101** about exactly
this, from the previous trim, and the handoff does not cross-reference it), and that a **frozen**
shard's banner would be falsified too — which nobody had noticed and which is now #115. Both are
fair omissions for a session whose deliverable was a rename phase, but a one-line pointer to #101
would have saved a rediscovery.

**What was wrong:** nothing. Every claim I depended on held. Its rename-specific gotchas (the
permanent 404, the unstyled tutorial, the orphaned third clone) were not mine to use but were
precise, and I have carried all of them forward untouched.

**ROI:** clearly positive. One paragraph of a handoff written for a different task correctly framed
this one.

### Session 228 Self-Assessment

**Score: 8.5/10.**

**+** Computed the live-file size at **all three** legal retention depths before choosing, and
rejected the 5-session cut on an 8-line margin rather than eyeballing it.
**+** Proved losslessness **twice with different toolchains**, and reported the sha256 rather than
the word "identical".
**+** **Acted on all four review findings despite `confirmed: []`.** The panel's own reasoning —
not just its facts — supplied L7's asymmetry (#116).
**+** **Found my own harness lying while green.** The fake-sha false attribution was invisible in
the verdict and obvious in the attribution column, and I read the column (#113).
**+** **Re-measured** the coverage matrix instead of restating it, discovered L4 had lost its unique
coverage *to my own new assertion*, and wrote that down rather than leaving a flattering claim (#114).
**+** Verified L7 end-to-end against the **committed ancestor** — the strongest available evidence
that the gap was real and that the fix closes it.
**+** Held the write-once rule under pressure: the S220 banner is wrong, the fix is one `sed`, and I
did not touch it.

**−** **I shipped L5 blind to the destinations.** I wrote the assertion, wrote four mutants for it,
ran a leave-one-out sweep, declared it load-bearing — and every one of those steps was consistent
with an assertion that checks half its claim. The project already had **#102** ("an assertion is
only as falsifiable as its operands are distinguishable") and I did not apply it to the operands of
the *claim* rather than the *fixture*. A review found it; I did not.
**−** **I wrote a false exhaustiveness claim into `CLAUDE.md`** — *"the only one no proof checks"* —
in the same session in which I hand-corrected two other unchecked copies. The counter-evidence was
my own diff.
**−** I ran the #101 sweep for *describing documents* and it covered only mutable files. Frozen
artifacts describe the system too; the S220 banner sat outside a sweep I believed was complete.
**−** The proof was rebuilt from scratch mid-session because I designed L5 before enumerating what a
routing table actually asserts. Ten minutes of enumeration first would have cost less than the rebuild.

**Against the bar:** S224 shipped the 15-mutant ancestor; S225 a 12-mutant matrix; S227 an
irreversible rename with every prediction tested. This session shipped 28 mutants, three new
assertions, a measured rather than asserted coverage matrix, the **first enforcement the write-once
rule has ever had**, and an experiment on the committed ancestor showing the gap was real. It also
shipped a half-blind assertion and a false claim, both caught before commit, one of them not by me.

**What's next: Phase 2 of `docs/planning/repository-rename.md`, and ONLY Phase 2** — unchanged from
Session 227's handoff, which I did not consume. It is the cheapest phase: it touches no file on
`publish-tutorial.yml`'s trigger list and none under `docs/wiki/`, so it fires neither the deploy
nor the wiki hook. Scope: `SECURITY.md:9`, `CONTRIBUTING.md:6`, and eleven lines of
`docs/planning/enterprise-migration.md` — the five `curl` criteria the rename turned into **vacuous
passes** (add `-fL` while there), the two "unchanged" assertions at `:1311`/`:1358`, the independence
pattern at `:363`/`:1308`/`:1351`, and the reword of dragon #21 at `:1436-1439`, whose verbatim *"Do
NOT … re-remote `~/Development/claims-model-starter.wiki`"* forbids the exact action Phase 4
requires. **Reword it; do not delete it** — it is still a live warning about the *enterprise* wiki.
**And before starting, walk §7 backwards against the phases** (Session 227's gotcha 8; it is what
found the orphaned clone, too late).

**The trim trigger will not fire again for roughly two sessions** — 1,039 lines with this record in
it, ~200 lines per record, 1,500 threshold. Do not trim again until it does. And note which number
the rule reads: the cut is sized at the *trim commit* (826 here), but the *trigger* is read at
Phase 0 against the file as it stands, close-out records included.

**Key files:**
- **`docs/architecture-history/SESSION_NOTES-S224-through-S221.md`** (933 lines) + its
  `.verify.sh` (8 assertions, 28 mutants). **Frozen. Do not edit — L7 now catches it.**
- **`docs/planning/repository-rename.md`** — §4 carries the operator's ruling and is closed. Phase 2
  is at `:528-600`; §7.2's allowlist is at `:1097` and still prints **17**.
- `CLAUDE.md` §"`SESSION_NOTES.md` is trimmed" — the retention rule, the three-commit rule, and the
  **canonical routing table that L5 now reads out of this file**.
- `~/gh-pages-pre-rename.bundle` + branch `gh-pages-pre-rename` — still the only copy of the
  pre-rename deployed site; `gh-pages` is parentless.
- `.githooks/post-commit:18` — untouched, still the one **fail-open** line in the system. Bites in
  Phase 4.
- `tests/test_wiki_no_line_citations.py:38` — `WIKI_DIR` built from path **parts**, invisible to a
  path-pattern grep. Phase 4 territory.

**Gotchas:**
1. **`CLAUDE.md` is now load-bearing for the proof.** The fourth trim must put its canonical routing
   table into `CLAUDE.md` **in the trim commit**, or its L5 is red from the first run. This is
   deliberate.
2. **The S220 shard's banner is wrong and must stay wrong.** *"the live ledger when N ≥ 221"* is
   false; the file is write-once. Do not fix it. The live pointer block is the authority.
3. **Two copies of the routing table are still unchecked by anything:** `README.md`'s repo map and
   the shard-naming rule in `docs/methodology/PROJECT_CONVENTIONS.md`. A trim that leaves either
   alone ships a lie.
4. **A record's own text is frozen history.** Session 225's record ends *"there are now **two**
   shards"* — stale, and correct to leave. Editing it registers as an added record and holds the
   proof red forever with zero data loss.
5. **This is still zsh.** Single-quote every heredoc delimiter. Sixth session running, still free.
6. **Every phase stays on a direct commit to `master`.** The hook is blind to merge commits.
7. **The old Pages URL 404s forever, and the tutorial is still unstyled.** Neither is rename damage
   and neither is yours to fix (S227 gotchas 1-2).
8. **`~/Development/mpc_tests/model_project_constructor` is still on the old origin URL and no phase
   owns it** (learning #111). Give it a home in Phase 4 step 1.

