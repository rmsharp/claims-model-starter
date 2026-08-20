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

### What Session 231 Did
**Deliverable:** Fourth trim of `SESSION_NOTES.md` — archive the oldest retained records into a
fourth write-once shard under `docs/architecture-history/` with its own proof script (IN PROGRESS)
**Started:** 2026-08-20
**Status:** Session claimed. Work beginning.

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

