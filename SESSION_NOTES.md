# Session Notes

**Purpose:** Continuity between sessions. Each session reads this first and writes to it before closing out.

**Sixth trim (Session 239). Archived Sessions 235 → 232 — 4 record headings, 1,004 lines** into
[`docs/architecture-history/SESSION_NOTES-S235-through-S232.md`](docs/architecture-history/SESSION_NOTES-S235-through-S232.md)
— same shape, same newest-on-top order, frozen and byte-for-byte unedited. **This live file now
holds Sessions 239 → 236 only** — four records, the floor `CLAUDE.md` sets. Its proof is
[`SESSION_NOTES-S235-through-S232.md.verify.sh`](docs/architecture-history/SESSION_NOTES-S235-through-S232.md.verify.sh):
the twelve assertions inherited from the fifth trim, none of them narrowed or weakened, plus
**L12** — every number this trim states about the size of its own artifacts, derived from the
artifacts and held against the prose that states it.

**L12 exists because the fifth trim's own figures were checked by nothing, and this is the defect
this project reports most.** That trim's pointer block says *"4 record headings, 918 lines"*, its
banner says *"At 976 lines it sits under the 2,000-line agent read cap"*, and `BACKLOG.md` says
*"(976 lines)"*. **All three are correct** — re-measured at this cut: 976 lines, 918 of them
records. But nothing compared any of them to the artifact. They are literal text, pinned by L2/b1
and L6 against a declaration the same author wrote, so a trim that typed the wrong figure would
have shipped it green in three places at once — and five consecutive sessions have now
self-reported a numeral typed instead of derived. L12 measures the archived heading count, the
archived line count and the shard's total line count; holds all three against hand-declared
integers; asserts the shard is under the read cap it claims to be under; and holds those integers
against the formatted numbers that actually appear in this block, in the shard's banner, in
`README.md` and in `BACKLOG.md`. Two independent halves, six arms, nine mutants.

**Six shards exist now, and none is a prefix of any other.** To place Session N, open the file
this table names. **This block is the authority**, and these seven clauses are machine-checked here,
in the shard's banner, and in `CLAUDE.md`:

**N ≤ 216** → `SESSION_NOTES-through-S216.md`; **217 ≤ N ≤ 220** → `SESSION_NOTES-S220-through-S217.md`;
**221 ≤ N ≤ 224** → `SESSION_NOTES-S224-through-S221.md`; **225 ≤ N ≤ 227** → `SESSION_NOTES-S227-through-S225.md`;
**228 ≤ N ≤ 231** → `SESSION_NOTES-S231-through-S228.md`; **232 ≤ N ≤ 235** → `SESSION_NOTES-S235-through-S232.md`;
**N ≥ 236** → `SESSION_NOTES.md`.

`grep` the shards; `Read` none of them. **Shards stay write-once** — a seventh trim writes a
seventh file; it never appends to one of these six.

**Four shard banners are stale now, and none may be repaired.** The S220 shard's still says *"the
live ledger when N ≥ 221"*; the S224 shard's still routes Sessions 225 and up to this file; the
S227 shard's routes Sessions 228 and up here too; and the S231 shard's — which predicted in its own
text that it would join them "at the sixth trim" — now has. All four were true at their own cut.
The S220 proof predates L5; the S224, S227 and S231 proofs have L5 but read their artifacts at
their own trim commits, so none of the four can notice, and ours will join them at the seventh
trim. **A shard banner is a snapshot of its own cut; this block is the authority.**

**The sweep was re-run and found no new copy — which is a result, not a formality.**
`git grep -l 'SESSION_NOTES-'` returns nine files: the four L8 already reads, this one, and **four
that are new since the fifth trim swept** — `CHANGELOG.md`, `PROJECT_LEARNINGS.md`,
`docs/architecture-history/evolution-page-plan.md` and `docs/planning/repository-rename.md`.
**None of the four is a copy of the shard census, and declaring any of them would have shipped a
falsehood.** `CHANGELOG.md` and the evolution plan match only on the phrase
`SESSION_NOTES-as-rationale`, which is not a filename — the sweep string over-matches, and
`git grep -l 'SESSION_NOTES-[A-Za-z0-9-]*\.md'` drops both. The other two cite shard filenames
inside frozen historical statements that were true when written and are true now, and neither says
how many shards exist; because `L8/set` requires a declared file to name the *whole* set, declaring
either would have turned a correct record red. That is the fifth trim's own rule — sweep for the
class, never trust the list — applied and, this time, returning nothing. **Sweep again at the
seventh trim rather than trusting this paragraph either.**

**The five blocks below are frozen at the FIFTH, FOURTH, THIRD, SECOND and FIRST trims and describe
THOSE cuts.** This trim falsified exactly three passages of the fifth trim's block — its claim about
which sessions this live file holds, its whole routing paragraph, and its count of how many shard
banners are stale — and rewrote all three as declared substitutions the proof checks by exact
equality. Every other byte of that block is original, and the fourth, third, second and first
trims' blocks are untouched. Each earlier proof reads its artifacts from the commit that added its
own shard, so this trim cannot disturb any of them; all five were re-run green at this cut, and a
session that doubts that should run them rather than reason about it.

**Fifth trim (Session 235). Archived Sessions 231 → 228 — 4 record headings, 918 lines** into
[`docs/architecture-history/SESSION_NOTES-S231-through-S228.md`](docs/architecture-history/SESSION_NOTES-S231-through-S228.md)
— same shape, same newest-on-top order, frozen and byte-for-byte unedited. At that fifth cut
this live file was left holding Sessions 235 → 232 — four sessions, the floor `CLAUDE.md`
sets; the sixth trim above has since cut it again. Its proof is
[`SESSION_NOTES-S231-through-S228.md.verify.sh`](docs/architecture-history/SESSION_NOTES-S231-through-S228.md.verify.sh):
the ten assertions inherited from the fourth trim, one of them NARROWED, plus **L10** (every
ancestor shard's *proof script* held against a hand-declared freeze commit — L9 froze the shards and
left unguarded the four files that give those shards their provenance, so a weakened ancestor proof
leaves this whole suite green while five banners keep telling readers to run it) and **L11** (the
retention rule itself — that this cut fired above `CLAUDE.md`'s 1,500-line trigger, landed under its
1,050-line target and kept its 4-record floor, with those three numbers held against the sentence in
`CLAUDE.md` that declares them rather than carried as magic constants).

**The narrowed assertion is L2/b3, and it is the finding worth carrying forward.** Inherited, it
scanned the shard's *records* as well as its banner for leaked front-matter lines — and on this cut
it fires on a correct trim: front-matter line 54's link to the S224 shard is a substring of a line
inside Session 228's record, which this trim archives. Same text, two legitimate homes. The records
half of that scan can never produce a true positive, because **L1 pins those bytes**: anything
inserted into a record moves them and trips L1 first. A leak can only hide in the banner, which is
exactly where the fourth trim's b3 caught one. `body` is now the banner alone, the run still PRINTS
what the old predicate would have flagged, and b3 keeps a mutant nothing else catches.

**Five shards existed at that cut, and none was a prefix of any other.** The routing table that
stood here named those five and sent every session from 232 up to this live file; the sixth trim
falsified that last clause — Sessions 235 → 232 are in a shard now — and the table above replaces
it. `grep` the shards; `Read` none. **Shards stay write-once** — a sixth trim wrote a sixth file;
it did not append to one of those five.

**Three shard banners were stale at that cut; four are now.** The S220 shard's still says *"the
live ledger when N ≥ 221"*; the S224 shard's still routes Sessions 225 and up to this file; the
S227 shard's does the same for Sessions 228 and up; and the S231 shard's own prediction that it
would join them "at the sixth trim" has come true. All four were true at their own cut. The S220
proof predates L5; the S224, S227 and S231 proofs have L5 but read their artifacts at their own
trim commits, so none of the four can notice. **A shard banner is a snapshot of its own cut; this block is the
authority.**

**The sweep found five more unread copies, and re-derived beats inherited.** `CLAUDE.md` told the
fifth trim not to trust the fourth trim's list of copies. Re-running
`git grep -l 'SESSION_NOTES-'` confirmed the same four FILES but found five further live
count-carrying strings inside them that no assertion read: `CLAUDE.md`'s own section heading, its
"three newer shards" parenthetical, its "L5 reads three copies … L8 reads four more … All six
copies" census, `README.md`'s "write-once for all four shards" tail comment, and `BACKLOG.md`'s
plain-language index row — which states the shard census a second time, in different words from the
item it indexes. One of them was **already false before this trim ran**: `CLAUDE.md` said L8 covers
"the two prose copies" three lines after saying it "reads four more", and the shipped `REACH` had
four entries. All five are declared in **L8** now. **Sweep again at the sixth trim rather than
trusting this list either.**

**The four blocks below are frozen at the FOURTH, THIRD, SECOND and FIRST trims and describe THOSE
cuts.** This trim falsified exactly three passages of the fourth trim's block — its claim about
which sessions this live file holds, its whole routing paragraph, and its count of how many shard
banners are stale — and rewrote all three as declared substitutions the proof checks by exact
equality. Every other byte of that block is original, and the third, second and first trims' blocks
are untouched. Each earlier proof reads its artifacts from the commit that added its own shard, so
this trim cannot disturb any of them; all four were re-run green at this cut, and a session that
doubts that should run them rather than reason about it.

**Fourth trim (Session 231). Archived Sessions 227 → 225 — 3 record headings, 738 lines** into
[`docs/architecture-history/SESSION_NOTES-S227-through-S225.md`](docs/architecture-history/SESSION_NOTES-S227-through-S225.md)
— same shape, same newest-on-top order, frozen and byte-for-byte unedited. At that fourth cut
this live file was left holding Sessions 231 → 228 — four sessions, the floor `CLAUDE.md`
sets; the fifth trim above has since cut it again. Its proof is
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

**Four shards existed at that cut, and none was a prefix of any other.** The routing table that
stood here named those four and sent every session from 228 up to this live file; the fifth trim
falsified that last clause — Sessions 231 → 228 are in a shard now — and the table above replaces
it. `grep` the shards; `Read` none. **Shards stay write-once** — a fifth trim wrote a fifth file;
it did not append to one of those four.

**Two shard banners were stale at that cut; three are now.** The S220 shard's still says *"the
live ledger when N ≥ 221"*; the S224 shard's still routes Sessions 225 and up to this file; and
the S227 shard's own prediction that it would join them "at the fifth trim" has come true. All
three were true at their own cut. The S220 proof predates L5 and cannot notice; the S224 and S227
proofs have L5 but read their artifacts at their own trim commits, so neither can notice either. **A shard banner is a snapshot of its own cut; this block is the authority.** What is
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

### What Session 240 Did
**Deliverable:** **Both operator rulings, executed.** **Decision A** — the archive banner is
project-added boilerplate that tracks its template: all **23** dead in-repo pointers re-pointed, and
§3 of `PROJECT_CONVENTIONS.md` now states the tracking rule so the next move of the target cannot
strand them again. **Decision B** — the C4/C5 clone-independence criterion restated as *"no
repository name other than the clone's own"*, scoped to the four §2.6 coupling files, and rebuilt as
**two arms**. This is the item Session 238 claimed and abandoned and Session 239 listed as
what's-next #1. No other work was started.

**Started / completed:** 2026-08-24 (UTC). **Commits: four** — `bad12e9` (the Phase 1B claim,
alone), `ab7d7f0` (Decision A, 23 files), `7075f7b` (Decision B, 4 files), and this close-out.
**Operator this session:** *"go"*, then *"explain 1"*, then both rulings in one message.

**`BACKLOG.md` 18 → 16 items**, index reconciled by counting both sides: **16 item headings, 16
index rows.** **No `CHANGELOG.md` entry** — `PROJECT_CONVENTIONS.md` §2's cadence gate; this session
touched no `src/`, `scripts/` or `tests/` logic. (`CHANGELOG.md` itself was edited, but only its
*preamble*, above the first version heading — navigation prose, not an entry.)

#### How two items that had been skipped three times got ruled in one exchange

Session 237 deferred them, Session 238 claimed and abandoned them, Session 239 listed them again.
**The blocker was never the operator's availability.** It was that nobody had put a decidable
question in front of them. The operator asked *"explain 1"*; the answer re-derived every filed
figure, stated what each candidate answer costs, and named the question in one sentence. Both
rulings came back in the next message. Learning [#161](PROJECT_LEARNINGS.md).

**Re-deriving mattered — the filed figures had moved.** Both items say *"do not inherit"*:

| | filed (S229, 2026-08-20) | re-derived (2026-08-24) |
| --- | --- | --- |
| fifth-alternative repair | 1,980 lines / 187 files | **1,103 / 176** |
| scope-by-directory repair | 350 lines, 284 imports | **357 / 269** |
| new name in the four coupling files | "~16" | **15** |

**The ~880-line drop is benign and worth knowing:** trims 4-6 relocated session history into
`docs/architecture-history/`, which the criterion's own exclusion filter drops. No conclusion ever
depended on the digits — the *order of magnitude* is the argument.

#### Decision A — measured, not assumed

| | |
| --- | --- |
| archive banners re-pointed | **21** lines across **20** files under `docs/architecture-history/` |
| `CHANGELOG.md` preamble | **2** lines (`:3`, `:10`), **4** occurrences |
| **total** | **23**, every one a pure `+1/-1` path substitution |
| genuine dated records **left alone** | **488** lines / 21 files (511 − 23 — the item's own arithmetic) |
| banners on the live path afterwards | **22** lines / 21 files (21 deployed + the template) |
| banner strings still naming the dead path | **1** — `PROJECT_LEARNINGS.md:141`, learning #135 *quoting* the defect |

**I checked byte-identity against the template before substituting, and it paid.** 20 of the 21
banner lines were byte-identical (modulo date). The 21st, `bedrock-testing-enablement.md:3`, appends
a document-specific sentence *inside* the banner naming where its still-useful reference tables were
carved forward. A "normalise every copy to the template" fix would have destroyed real information.
It is preserved, and now recorded in `PROJECT_CONVENTIONS.md` §3 as **the one documented exception**
to Session 147's byte-identity invariant, so the next reader does not mistake it for drift.

Two traps the item warned about, both live: `evolution-page-plan.md` carries **two** hits — its own
banner at `:1` and the banner's original *specification* at `:161`, inside a fenced block — and
`initial_purpose.txt` is the only `.txt` in the directory, which a `*.md` sweep skips. Both handled.
`methodology-pr2527-remediation-mpc.md` is third-party-attributed (`NOTICE`); confirmed before
touching that its banner is at `:1` and the attributed brief starts at `:3`.

#### Decision B — the criterion now has two arms, and arm 2 was proven to fire before it was written down

The three sites are **not the same kind of thing**, and conflating them is how this broke. `:363` is
§2.6's **rediscovery command** — a discovery aid over *this* repository, with no threshold. The C4
and C5 sites are the **pass/fail criterion on the clone**. §2.6 now says so explicitly and carries
the criterion as the definition of record; both arms are inlined at C4 and C5.

- **Arm 1 — unchanged.** Personal-account identity, repository-wide, and it still carries the legacy
  repository name: a sanitised clone holds no trace of it anywhere, so this arm stays satisfiable.
- **Arm 2 — new.** No repository name but the clone's own, over the four §2.6 coupling files.
  `git grep -h -o` matches per **occurrence**, not per line, so a line carrying both the clone's own
  name and a foreign one cannot hide behind the exclusion. It prints the *set of foreign repository
  names present*, so a failure names the offender rather than a line number.

**Arm 2 was run against the live defect before being written into the plan.** Over this repository
with `CLONE_NAME=model_project_constructor` it returns `claims-model-starter`, from
`scripts/publish_wiki.sh:19`, `:24` and `:42` — **exactly the case the old criterion's own comment
names, and exactly the case the old criterion had stopped catching.** In *this* repository those
three lines are correct and **permanent** (D-R5); in the **clone** they are the defect. That
asymmetry is why the criterion belongs on the clone and never on the original. Learning
[#159](PROJECT_LEARNINGS.md).

**A vacuous-pass hazard was found while validating, and is recorded in the plan.** `git grep … --
$FOUR` printed nothing and read as a clean result. The cause was **zsh not word-splitting unquoted
parameter expansions** — the whole list went through as one pathspec matching no file. In a
criterion whose PASS condition is *"no output"*, a vacuous pass and a real pass are byte-identical.
Learning [#160](PROJECT_LEARNINGS.md); this is dragon 1's own theme, met in the wild.

**Dangling references closed rather than left.** `repository-rename.md` dragon 1 still *recommended*
the unsatisfiable path-scoped repair and still said the ruling was outstanding; it now carries a
**RULED** note saying the recommendation must not be executed and pointing at the restatement by
content, not by line number. §9.2's pointer told the reader to `grep -n 'clone-independence'
BACKLOG.md`, which now returns nothing — annotated. And `.gitleaksignore:1` cited
`enterprise-migration.md:847-887`; Phase B2 is at `:952`, so it was **already stale before this
session** and my insert widened it — de-line-numbered rather than re-numbered.

#### Verification — everything run, nothing reasoned about

| Check | Result |
| --- | --- |
| suite, **before** any edit | **1275 passed, 9 skipped**, coverage 97.98%, exit 0 |
| suite, after Decision A | 1275 passed, 9 skipped |
| suite, after Decision B | **1275 passed, 9 skipped** — unchanged throughout |
| **all six shard proofs** | **green** — required, not optional: the newest proof's `L8` reads `BACKLOG.md` and `PROJECT_CONVENTIONS.md` **live**, and both were edited this session |
| Decision A diff shape | 23 lines, every one `+1/-1`; no line added or removed anywhere |
| `BACKLOG.md` reconciliation | **16 headings / 16 index rows**, counted on both sides |
| arm 2 against the live defect | returns `claims-model-starter` — fires, as designed |
| `mkdocs build` | clean (0.17 s); `exclude_docs` publishes only `/index.md`, `/tutorial.md`, `/assets/`, so no edited path reaches the site |
| `mkdocs build --strict` | fails — **pre-existing and by design**, reproduced identically at `ab0de46` in a throwaway worktree. See gotcha 3. |
| wiki hook | correctly silent — no path under `docs/wiki/model_project_constructor/` in any commit |

### Session 239 Handoff Evaluation (by Session 240)

**Score: 9/10.** It cost me a few minutes to read and saved me from at least two wrong turns.

- **Gotcha 1 was right and was measured.** *"This file is **1,079** lines with this record — measured
  after writing it, against the **1,500** trigger — roughly **two** sessions of headroom."* Phase 0
  measured **1,079** exactly. It also said *"re-measure at Phase 0 anyway; do not trim on this
  sentence"* — which is the correct instruction even when the sentence turns out to be perfect.
- **Gotcha 6 paid off silently, again.** `grep` here is a `ugrep --ignore-files` wrapper;
  `command grep` and `git grep` throughout, no empty-result mysteries.
- **Gotcha 7 was right.** `gh issue list` is empty and expected; `BACKLOG.md` governs at 18 items.
- **What's-next #1 was correctly identified and correctly characterised** — *"expect to present
  measurements and stop, not to edit"* is exactly what unblocked three sessions of drift.
- **It told me the truth about what it could not know.** Its −1 was *"it could not tell me the cut
  would be decided by two stub records."* That kind of honesty is what makes the rest credible.
- **−1, and it is not really S239's fault: what's-next #4 was already done.** *"`master` is 3 commits
  ahead of `origin/master`"* — Phase 0 found `origin/master` == `master` == `ab0de46`, verified
  against the live remote with `git ls-remote`, not just the local tracking ref. Someone pushed after
  S239 closed. A handoff cannot know what happens after it is written; the transferable lesson is
  that **a push claim must be re-verified against the remote, never against `origin/master`**, which
  is a local ref that only moves on fetch or push.

**The handoff I did NOT need but read anyway** was Session 237's, two records up — its gotcha 5 is
what stopped me filing `mkdocs build --strict` as a defect. **Two-records-back is not archaeology; it
is still live context.** Learning [#162](PROJECT_LEARNINGS.md).

### Session 240 Self-Assessment

**Score: 9/10.** Both rulings executed completely, every figure re-derived rather than inherited, the
new criterion proven to fire before it was written down, and the two dangling references the work
created or exposed were closed rather than filed. What keeps it off 10 is that I ran a check the
project had deliberately opted out of and was one keystroke from filing its output as a defect — the
predecessor's handoff caught that, not me.

**+** **I put a decidable question in front of the operator instead of asking whether to proceed.**
Three sessions had listed these items; none had tabulated what each candidate answer costs. Both
rulings came back in one message.
**+** **I re-derived every filed figure and the numbers had moved** — 1,980→1,103 and 350→357/269.
I also worked out *why* (the trims moved history into the criterion's own excluded directory), which
is the part that stops the next reader thinking the record was wrong.
**+** **I validated arm 2 against the live defect before writing it into the plan.** It returns
`claims-model-starter` from `publish_wiki.sh:19,:24,:42`. A criterion never shown to fire is an
assertion nobody has falsified.
**+** **I checked banner byte-identity before a 21-line bulk substitution**, which turned an unknown
into a documented exception instead of silently destroying `bedrock-testing-enablement.md`'s rider.
**+** **I ran all six shard proofs** because `L8` reads two files I edited — not because anything
told me to this session.
**+** **I reproduced the `--strict` failure at the pre-session commit in a throwaway worktree**
rather than asserting "pre-existing".

**−** **I ran `mkdocs build --strict`, which this project deliberately does not run**, and treated
its failure as a finding worth filing until S237's gotcha 5 corrected me. The right instinct is to
check what the project's own CI runs *before* choosing a command.
**−** **I lost a round to zsh word-splitting** — `-- $FOUR` returned nothing and my first reading was
"empty result", not "the command never reached its inputs". I caught it because the same query had
worked moments earlier with a literal list. Had it not, I would have written a vacuously-passing
criterion into a plan whose central theme is vacuous passes.
**−** **I did not re-run `--self-test` on any shard proof**, only the proofs themselves. Nothing this
session changed a proof, so it was not required — but `CLAUDE.md` is emphatic that a green run
proves less than it appears to, and I accepted six green runs without falsifying any of them.
**−** **Decision A touched 23 files in one commit.** Within `SAFEGUARDS.md` (clean tree before,
single mechanical class, verified diff shape) but it is the largest blast radius in several sessions.

**Against the bar:** S239 found a new assertion silently retiring an old one; S235 found an inherited
assertion structurally incapable of a true positive. This session's equivalent is smaller and of a
different kind — **a criterion that had gone silent on the one case its own comment was written to
name**, repaired by splitting rather than narrowing. The transferable finding is
[#158](PROJECT_LEARNINGS.md): when a `→ 0` check becomes unsatisfiable, ask which matched strings are
legitimate *somewhere* — those need a scoped arm, not deletion from the pattern.

**What's next.**

1. **The `publish_wiki.sh` / `post-commit` pair** — now the oldest unblocked item, and explicitly
   filed to be bundled into **one** session. `publish_wiki.sh:53` tests that the source directory
   *exists*, not that it is non-empty, and `rsync --delete` then publishes the emptying; the hook
   exits 0 in silence when it declines. **Both run unattended from a commit hook.** No operator
   ruling needed. This session touched `publish_wiki.sh` in no way — its three `claims-model-starter`
   lines are D-R5-permanent and must stay.
2. **Decide whether `uv.lock` belongs in Publish Tutorial's `paths:` filter** (S237 gotcha 4). One
   line, gated on one judgement: is a public deploy on every dependency bump acceptable? **This is
   the last operator decision left in the queue** — present it the way Decision A and B were
   presented and it will take one exchange.
3. **The two delivered plans still filed under `docs/planning/`** — `httpx-adapter-migration.md` and
   `repository-rename.md`. Still open, still needs a ruling on both together, and note that
   `repository-rename.md` just gained two annotations from this session.
4. **`master` is 4 commits ahead of `origin/master`** — `bad12e9`, `ab7d7f0`, `7075f7b` and this
   close-out. Measured with `git fetch` + `git rev-list --count origin/master..master`, not read off
   a stale tracking ref. **Verify the same way** — `git status`'s ahead-count and a bare
   `origin/master` are local refs that move only on fetch or push; see the −1 in the evaluation
   above, where S239's push claim had been overtaken by an actual push it could not know about.

**Key files:**
- `docs/planning/enterprise-migration.md` §2.6 — **the restated criterion is the definition of
  record.** Find it by content: `grep -n 'clone-independence criterion (restated'`. Both arms are
  inlined at the C4 and C5 verify blocks; §2.6 also now separates the *rediscovery command* from the
  *criterion*, which is the distinction whose absence caused the defect.
- `docs/methodology/PROJECT_CONVENTIONS.md` §3 — the banner-tracking rule, plus the one documented
  exception to byte-identity.
- `docs/planning/repository-rename.md` — dragon 1 (`grep -n 'RULED, 2026-08-24'`) and §9.2 both
  annotated. **Dragon 1's recommended repair must not be executed.**
- `PROJECT_LEARNINGS.md` — **162 learnings**; #158–#162 are this session's. `CLAUDE.md:99` updated.

**Gotchas:**
1. **The seventh trim is probably NEXT SESSION — but do not trim on this sentence.** This file is
   **1,328** lines with this record, measured after writing it (re-measured once after I typed 1,269
   from projection instead of from `wc -l` — the defect this project reports more than any other,
   #105/#154). Against `CLAUDE.md`'s **1,500** trigger that is **172** lines of headroom, and the
   last four records cost 230-294 lines each, so **Session 241 very likely arrives over the trigger
   and is the seventh trim.** **Re-measure at Phase 0 anyway.** Two commits always, cut to ≤1,050, never below the 4-record floor, and re-derive
   the copy list rather than trusting any inherited one.
2. **All six shard proofs must be re-run by any session that edits `BACKLOG.md`,
   `PROJECT_CONVENTIONS.md`, `README.md` or `CLAUDE.md`.** The newest proof's `L8` reads all four
   **live**, so an ordinary docs edit can turn it red. This session edited two of them; all six were
   run and are green. `for f in docs/architecture-history/*.verify.sh; do bash "$f"; done`.
3. **`mkdocs build --strict` fails at `HEAD`, by design — do NOT file it.** `docs/index.md` is a
   meta-refresh redirect and `mkdocs.yml` sets `validation.links.unrecognized_links: warn`
   deliberately; the asset guard is the substitute (S237 gotcha 5). Reproduced identically at
   `ab0de46`. Use plain `mkdocs build`.
4. **`zsh` does not word-split unquoted expansions.** `git grep … -- $FILES` matches nothing, prints
   nothing, and looks like a pass. Pass paths literally or `set --` them into `"$@"`. This bit me
   this session while validating a criterion whose PASS condition is "no output".
5. **`scripts/publish_wiki.sh:19`, `:24`, `:42` name `claims-model-starter` and that is CORRECT and
   PERMANENT** (D-R5: GitHub's rename moves a URL, never a directory on your disk). Arm 2 of the new
   criterion fires on them **on purpose** when run here — it is a criterion for the *clone*. Do not
   "fix" them.
6. **488 lines across 21 files still name `docs/wiki/claims-model-starter` and must stay.** They are
   genuine dated records that named a path which was correct when written. Only banners and the
   `CHANGELOG.md` preamble were present-tense navigation. Do not widen this into a sweep.
7. **Still zsh, and `grep` is still a `ugrep --ignore-files` wrapper.** `command grep` or `git grep`
   for anything load-bearing. Single-quote every heredoc delimiter.
8. **`gh issue list` is empty and that is expected** — the tracker is not in use. `BACKLOG.md`
   governs, now **16 items**, and its plain-language index at the top is written for the operator.
   Both sides were counted this session: 16 headings, 16 rows.
9. **Session 238's record is an abandoned claim, annotated, and must stay that way.** It is the
   evidence a ghost session happened. Do not tidy it away.

### What Session 239 Did
**Deliverable:** **The sixth lossless trim.** Sessions 235 → 232 are in a new write-once shard;
this file went **1,786 → 843** lines. The proof carries L0–L11 forward with nothing narrowed and
adds **L12**, which closes a hole that had been open for five trims: *every size figure a trim
states about its own artifacts was checked by nothing.* No other work was started.

**Started / completed:** 2026-08-24 (UTC). **Commits: three** — `c2a2f6c` (the Phase 1B claim,
alone), `28879a0` (the whole trim, one commit, seven files), and this close-out. **Operator this
session:** *"go"*, then *"natural candidates are the sixth trim (now trigger-confirmed,
self-contained, no operator input needed)"*.

**No `CHANGELOG.md` entry, and that is the convention rather than an omission.** `PROJECT_CONVENTIONS.md`
§2 gates on shipped code; this trim touches no `src/` or `scripts/` path. Checked against precedent
rather than asserted: `grep -i 'trim\|shard' CHANGELOG.md` finds **none of the five earlier trims**
there. `BACKLOG.md` stays at 18 items — the trim opened and closed nothing.

#### The cut, measured

| | |
| --- | --- |
| fired at | **1,786** lines, against `CLAUDE.md`'s **1,500** trigger |
| archived | Sessions **235 → 232** — 4 record headings, **1,004** lines |
| into | `docs/architecture-history/SESSION_NOTES-S235-through-S232.md` — **1,057** lines (53 banner + 1,004) |
| retained | Sessions **239 → 236** — 4 records, **594** lines |
| landed at | **843** lines, against the **≤1,050** target and the **4**-record floor |
| routing now | 7 clauses; `232 ≤ N ≤ 235` → the new shard, `N ≥ 236` → this file |

#### Why the cut fell there, and why one record more would have been wrong

The retain-4 / retain-5 choice was **simulated before anything was written**, not chosen by feel:

| retain | live after | verdict |
| --- | --- | --- |
| 4 (239, 238, 237, 236) | **843** | under target; **~2 sessions** of headroom before the next trigger |
| 5 (+ Session 235) | **1,136** | **misses the 1,050 target**, and buys only ~1 session |

Retaining a fifth record would have failed `L11/target` — the assertion the fifth trim added
precisely so a too-shallow cut cannot pass. **But the floor is worth reading twice:** the four
retained records include Session 238's 19-line abandoned claim and this session's own 11-line stub,
so *the letter said four sessions and the working context was two.* That is legal — the declared
grammar says a record is a byte span, never a session — and it is the first cut where the two
readings diverged. Learning [#156](PROJECT_LEARNINGS.md).

#### L12, and the hole it closes

The fifth trim's pointer says *"4 record headings, 918 lines"*; its banner says *"At 976 lines it
sits under the 2,000-line agent read cap"*; `BACKLOG.md` says *"(976 lines)"*. **All three are
correct** — re-measured here: 976 lines, 918 of them records. **And nothing had ever compared any
of them to the artifact.** Every occurrence lives inside a string literal that `L2/b1` and `L6` pin
against a declaration *the same author wrote*. A trim that typed 918 where the truth was 981 would
have shipped that in three files at once, green.

L12 measures the archived heading count, the archived line count and the shard's total; holds all
three (plus the retained-record count) against hand-declared integers; asserts the shard is under
the read cap its banner claims; and holds those integers against the **ten formatted figures** that
actually appear in the pointer, the banner, `README.md`, `BACKLOG.md` and `CLAUDE.md` — in two
formats, because this project writes small counts as words (*"four record headings"*) and large
ones as digits (*"1,057 lines"*). **Six arms, nine mutants.**

**It caught its own author twice before it shipped**, which is the only reason to trust it:
1. The first green run printed **`10 prose claims`** three lines under a header that said **nine**.
   A typed count, wrong, caught by the assertion written to catch typed counts. Sixth consecutive
   session with that defect ([#105](PROJECT_LEARNINGS.md), #146, #148, #152,
   [#154](PROJECT_LEARNINGS.md)).
2. The arm sweep found `retained_records` shipped with **no mutant of its own** — M66 moves
   `README.md`'s prose, which is the *prose* arm. M68 was added.

#### Two arms failed the arm-level sweep, and both fixes were mutants — never a weakened assertion

`CLAUDE.md` warns that a green `--self-test` whose mutants never exercise an assertion is the same
lie as a green run. Neutering all **42** arms one at a time found two:

- **`L2/b3` lost its only mutant to L12.** The inherited M51 *appends* a front-matter line to the
  banner — which under this proof also changes the shard's line count, so `L12/shard_total` caught
  it and b3, an assertion the fifth trim had deliberately narrowed and defended at length, was
  reachable by nothing. Still green, still listed in the coverage block, proving nothing. M51 now
  **replaces** a banner line, keeping the count identical. **A new assertion's reach is exactly
  what makes an old one redundant** — learning [#153](PROJECT_LEARNINGS.md), and the single most
  transferable finding of this session.
- **`L12/cap` had no mutant at all.** Moving the declared cap alone also falsifies the banner's
  prose figure, so `L12/prose` fired first. M63 now mis-states the cap **consistently** —
  declaration, banner and declared literal together — which is both the isolating mutation and the
  realistic one.

An **L13** was drafted (no shard name may be a prefix or substring of another — stated in bold in
three places and checked nowhere) and **dropped**: every violating mutation is caught by `L5/4`
first, so it would have shipped an assertion no mutant can reach. That is recorded in the proof's
header so the seventh trim does not rediscover the idea and ship it.

#### The copy sweep was re-run, found four new files, and declared none of them

`git grep -l 'SESSION_NOTES-'` returns nine files: the four `L8` already reads, this one, and
**four the fifth trim never named** — `CHANGELOG.md`, `PROJECT_LEARNINGS.md`,
`docs/architecture-history/evolution-page-plan.md`, `docs/planning/repository-rename.md`.
**Declaring any of them would have shipped a falsehood.** The first two match only the phrase
`SESSION_NOTES-as-rationale`, which is not a filename — the sweep *string* over-matches. The other
two cite shard names inside frozen historical statements that state no census, and `L8/set`
requires a declared file to name the **whole** set, so declaring either would have turned a
*correct* record red. Learning [#155](PROJECT_LEARNINGS.md).

#### Verification — everything run, nothing reasoned about

| Check | Result |
| --- | --- |
| reconstruction **independent of the proof** | retained + archived records byte-identical to `HEAD`'s; 120,264 B each; sha256 `e041fb17789bd853` |
| the new proof, pre-commit | green, L0–L6 + L8–L12 (L7 inapplicable until committed) |
| the new proof, **post-commit** | green, **L0–L12**, and the shard on disk is the blob committed at `28879a0` |
| `--self-test` | **68/68 mutants caught** |
| assertion-level neuter loop (13) | every assertion has uniquely-caught mutants except L0/L1/L3/L4, documented as overlapped |
| arm-level neuter sweep (42) | 30 arms uniquely reachable; **12 documented as having no unique mutant, with the reason for each** |
| all five ancestor proofs | green before the trim and green after |
| suite | **1275 passed, 9 skipped** — unchanged from S237 |
| `L3 added` count | **0** — no record edit bundled into the trim commit |
| docs site | unaffected: `mkdocs.yml`'s `exclude_docs` allows only `/index.md`, `/tutorial.md`, `/assets/` |
| wiki hook | correctly silent — no path under `docs/wiki/model_project_constructor/` |

### Session 238 Handoff Evaluation (by Session 239)

**Score: 3/10 — and 3 rather than 1 is the whole point.** Session 238 wrote a Phase 1B stub and then
vanished: one commit, never pushed, no deliverable, no close-out. There is no handoff to evaluate.

**What it nevertheless did right, and it is not nothing.** The stub told me, in eight lines, exactly
what had been attempted, when, and on whose authority — so Phase 0 spent about a minute establishing
that nothing was in flight and nothing needed recovering (`git log --oneline 61aee5b..HEAD` printed
one line; `git rev-parse HEAD` was still `e52e88e`; `git status` was clean). **That is precisely the
return FM #14 promises**, and it is why the protocol makes the stub mandatory before any technical
work. A crash with no stub costs the next session a reconstruction from `git log`; this cost a minute.

**What was missing:** everything after the stub. **What was wrong:** nothing — the stub's claims
were all true. It is scored as a floor, not a failure of judgement.

### Session 237 Handoff Evaluation (by Session 239)

Session 238 left no handoff, so **the handoff I actually worked from was Session 237's**, two
records up. Scoring it is not bookkeeping: it is the one that did the work.

**Score: 9/10.**

- **Gotcha 6 was right, and it was right because it was measured.** *"This file is **1,756** lines
  with this record — measured after writing it, at fixed width."* Phase 0 measured **1,765** (the
  9-line difference is Session 238's stub, added after S237 closed). The prediction *"S238 arrives
  over the trigger and is the sixth trim"* was correct, and it told me to **re-measure anyway** —
  which is what turned a projection into a trigger.
- **It handed over the whole procedure**: cut to ≤1,050, never below a 4-record floor, two commits
  always, and *re-derive the copy list rather than trusting the inherited one*. That last
  instruction is the reason the sweep ran, and the sweep is the reason four unfamiliar files were
  correctly **left alone** instead of half-declared.
- **Gotcha 7 paid off silently.** `grep` is still a `ugrep --ignore-files` wrapper; `command grep`
  and `git grep` throughout, no empty-result mysteries.
- **Gotcha 8's `BACKLOG.md` arithmetic held** — 18 items, index reconciled, nothing to fix.
- **−1: it could not tell me the cut would be decided by two stub records.** No handoff could —
  Session 238 had not happened yet. Noted so the next reader sees why the floor needed re-deriving
  rather than re-applying.

### Session 239 Self-Assessment

**Score: 9/10.** The trim is lossless by a check that does not depend on the proof, the proof is
falsifiable and was falsified 68 ways, and the two defects found in my own new assertion were found
by measurement I chose to run rather than by luck. What keeps it off 10 is that **both of those
defects were mine**, and one of them — a typed count — is the sixth consecutive session to report
that same class.

**+** **I measured the cut instead of choosing it.** The retain-4/retain-5 simulation ran before a
byte was written, and it inverted my first instinct: I had assumed retaining Session 235 (the fifth
trim's own record, the most obviously relevant predecessor) would be right, and the arithmetic says
it fails `L11/target` and buys half the headroom.
**+** **I found the L12 hole by grepping the ancestor for its own numbers**, not by inspection —
`grep '918\|976'` over the fifth proof returns five hits, every one inside a string literal. That
is a two-second check that five trims had not run.
**+** **I ran the arm-level sweep even though the assertion-level loop was already green**, because
`CLAUDE.md` says the loop is not enough. It found two unreachable arms, one of them *created by my
own new assertion retiring an inherited one*. Skipping it would have shipped a proof whose
most-defended assertion proved nothing.
**+** **I let the run's own printout correct me.** `10 prose claims` versus a header saying nine —
I read the output instead of trusting what I had written.
**+** **I declared none of the four new sweep hits**, and checked *why* each was excluded rather
than pattern-matching on the filename. Two were a phrase, not a filename; two were frozen records
that `L8/set` would have failed.

**−** **I typed a count in the very file whose purpose is to stop typed counts.** The header said
nine prose claims; there were ten. Caught, but I wrote it.
**−** **I shipped an arm with no mutant** (`retained_records`) in an assertion whose header lectures
about exactly that, and only the sweep found it.
**−** **My first M51 fix attempt was aborted mid-script by a failed assertion**, leaving two intended
edits unapplied; I noticed only because the next run's output disagreed with what I expected. The
script's write-at-the-end structure meant nothing was corrupted, but I should have re-read before
re-running.
**−** **I did not re-verify the operator-facing `BACKLOG.md` index count by re-counting**; I checked
that the trim opened and closed no items, which is a weaker claim than S237's reconciliation.

**Against the bar:** S235 proved an inherited assertion structurally incapable of a true positive;
S237 found a prescribed fix in the wrong place. This session's equivalent is **a new assertion
silently retiring an old one** — the same species one level up, and the first time in this lineage
that *adding* a check made an existing check worthless while leaving every signal green.

**What's next.**

1. **The two operator decisions** — the archive-banner ruling (one ruling disposes of 23 dead
   in-repo pointers) and the C4/C5 clone-independence restatement. **Session 238 claimed exactly
   this and produced nothing**, so it is now the oldest unblocked item and has been skipped twice.
   Both are `⚠ OPERATOR DECISION` rows where *the ruling is the work* — expect to present
   measurements and stop, not to edit.
2. **The `publish_wiki.sh` / `post-commit` pair** — filed to be bundled into one session.
   `publish_wiki.sh:53` tests that the source directory *exists*, not that it is non-empty, and
   `rsync --delete` then publishes the emptying; the hook exits 0 in silence when it declines. Both
   run **unattended from a commit hook**.
3. **Decide whether `uv.lock` belongs in Publish Tutorial's `paths:` filter** (S237 gotcha 4). One
   line, gated on one judgement: is a public deploy on every dependency bump acceptable?
4. **`master` is 3 commits ahead of `origin/master`** — `e52e88e` (S238's orphan claim), `c2a2f6c`
   and `28879a0`, plus this close-out. Push is a one-liner; it is listed because S236 existed
   entirely to fix a push that had not happened.

**Key files:**
- `docs/architecture-history/SESSION_NOTES-S235-through-S232.md` — the shard. **Frozen.** `grep` it.
- `docs/architecture-history/SESSION_NOTES-S235-through-S232.md.verify.sh` — the proof, 1,592 lines.
  **Read its header before touching anything**: it carries the measured coverage, the twelve arms
  with no unique mutant *and the reason for each*, and the rejected-L13 note.
- `SESSION_NOTES.md:5-69` — the new pointer block. **It is the routing authority**; the six shard
  banners are snapshots of their own cuts and four of them are now falsified.
- `CLAUDE.md:77-90` — the trim bullet: retention rule, routing table, assertion lineage L4→L12.
- `PROJECT_LEARNINGS.md` — **157 learnings**; #153–#157 are this session's. `CLAUDE.md:99` updated.

**Gotchas:**
1. **The seventh trim is NOT next session.** This file is **1,079** lines with this record — measured after writing it, against
   the **1,500** trigger — roughly **two** sessions of headroom, not one. That is the whole reason
   the cut retained four records rather than five. **Re-measure at Phase 0 anyway**; do not trim on
   this sentence.
2. **Adding an assertion to that proof obliges you to re-sweep every arm, not just yours.** L12 stole
   `L2/b3`'s only mutant. The loops are in the proof's header; both take under a minute.
   `for A in L0 … L12` for assertions, and neuter one `out.append(` at a time for arms.
3. **The size figures are now load-bearing in five files.** Changing the shard, the pointer block,
   `README.md`'s *"newest 4 sessions"*, `BACKLOG.md`'s *"(1,057 lines)"* or `CLAUDE.md`'s
   *"(235→232, 1,057 lines)"* fails `L12/prose`. That is the point — but it means a careless
   reflow of any of those sentences goes red.
4. **`git grep -l 'SESSION_NOTES-'` over-matches.** It hits the phrase `SESSION_NOTES-as-rationale`
   in `CHANGELOG.md` and `evolution-page-plan.md`, which are not filenames. Use
   `git grep -l 'SESSION_NOTES-[A-Za-z0-9-]*\.md'`. Both forms are recorded in the proof's header.
5. **Four shard banners are now stale and none may be repaired** — S220, S224, S227 and S231. Each
   was true at its own cut. **The live pointer block is the authority.** Ours joins them at the
   seventh trim; its banner says so.
6. **Still zsh, and `grep` is still a `ugrep --ignore-files` wrapper.** `command grep` or `git grep`
   for anything load-bearing. Single-quote every heredoc delimiter.
7. **`gh issue list` is empty and that is expected** — the tracker is not in use. `BACKLOG.md`
   governs, **18 items**, and its plain-language index at the top is written for the operator.
8. **Session 238's record is an abandoned claim, annotated, and must stay that way.** It is the
   evidence a ghost session happened. Do not tidy it away.

### What Session 238 Did
**Deliverable:** Dispose of the two blocked operator decisions (Session 237's what's-next item 1)
— the archive-banner ruling covering 23 dead in-repo pointers, and the C4/C5 clone-independence
criterion restatement. (ABANDONED — no deliverable produced.)
**Started:** 2026-08-22 20:17 UTC
**Status:** Session claimed. Work beginning. Both items are `BACKLOG.md` `⚠ OPERATOR DECISION`
entries where the ruling is the work and the edit is minutes; every filed figure is re-derived
before the rulings are put, per learning #105 and both items' own "do not inherit" instruction.

**Outcome: ABANDONED, annotated by Session 239 on 2026-08-24.** `e52e88e` — this stub — is the
only commit Session 238 ever made, and it was never pushed. Measured at Session 239's Phase 0:
`git log --oneline 61aee5b..HEAD` printed exactly one line — this stub — and `git rev-parse HEAD`
was still `e52e88e`, so no work commit and no close-out ever followed it; `git status` was clean,
so no partial edit was left in the tree either. **Nothing was lost and nothing needs recovering**; the two `⚠ OPERATOR
DECISION` items it claimed are untouched and still stand in `BACKLOG.md`. This stub is left in
place rather than overwritten, because it is precisely the trace Phase 1B exists to leave
(FM #14) — the record of a session that claimed and then vanished. Session 239 claimed a new
number instead of reusing this one for the same reason.

### What Session 237 Did
**Deliverable:** **The published tutorial site is styled again — proved in a browser, not announced.**
Session 234's `exclude_docs` hypothesis is **confirmed**, root-caused in MkDocs' own source, fixed,
and the hole that let a 43-file loss ship green through four release phases is closed by two guards
that were each run **red against the real historical defect** before being wired in. No other work
was started.

**Started / completed:** 2026-08-22 (UTC). **Commits: three** — `47a4c02` (the Phase 1B claim,
alone), `70e968b` (the whole fix, one commit, six files), and this close-out. **Operator this
session:** *"go"*, then *"1"* — item 1 of Session 236's what's-next.

Changes shipped code (`scripts/`) and test logic, so this **does** get a `CHANGELOG.md` entry
(`PROJECT_CONVENTIONS.md` §2's cadence gate) — dated 2026-08-22, inserted at the head of the
descending run under `[0.3.0]`, matching where Session 225 put itself. **`BACKLOG.md` goes 19 → 18
items**: the tutorial item and its plain-language index row are removed together, per §2's
"remove the line on completion and record the work in `CHANGELOG.md`".

#### The root cause, read out of MkDocs rather than inferred

`mkdocs/commands/build.py` calls `add_files_from_theme()` at **`:289`** and then **re-runs
`set_exclusions()` at `:294`**. Theme files arrive with `InclusionLevel.UNDEFINED`, so that second
pass applies **`exclude_docs` to the theme's files as well as to `docs_dir`** — which the option's
name and its documentation do not suggest. `b27cc98` (Session 182, Phase A1 of
`enterprise-migration.md`) had inverted `exclude_docs` from a denylist into a fail-closed allowlist
beginning `/*`; gitignore-anchored at the root, that pattern matches the Material theme's entire
`assets/` tree.

**Measured three independent ways, none of them a re-reading of the docs:**

| Measurement | Result |
| --- | --- |
| call `add_files_from_theme()` directly and diff the file set | **43 files, all under `assets/`** — matching the 43 S234's bisect found missing |
| `pathspec.GitIgnoreSpec` per-path, current vs candidate patterns | `/*` matches `assets/stylesheets/…`; `!/assets/` un-matches it and leaves `planning/`, `wiki/`, `architecture-history/` excluded |
| local `mkdocs build` before / after | **6 files → 49**, of which 43 are `assets/` |

#### What changed — one commit, six files

| Thing | Detail |
| --- | --- |
| `mkdocs.yml` | `!/assets/` added to the allowlist; A1's fail-closed property preserved. The comment records the `:289`/`:294` ordering so the line is not "simplified" away by a reader who checks only the option's docs. |
| `scripts/check_site_assets.py` | **new.** Every local `href`/`src` in the built HTML must resolve to a file in the artifact; `--require-css` covers the one hole integrity cannot see. Self-calibrating — no file count to rot on a theme upgrade. `--base-path` handles the root-relative refs MkDocs emits in `404.html`, derived in the workflow from `site_url` rather than duplicated. |
| `scripts/check_published_site.py` | **new.** The **live** site must serve what it links; polls, because a `gh-pages` push starts an asynchronous Pages build. |
| `.github/workflows/publish-tutorial.yml` | build → assert artifact → deploy → assert live. Plus the two scripts in `paths:` and a comment recording why the filter cannot fire on nested `docs/` changes. |
| `tests/scripts/test_check_site_assets.py` | **new, 30 tests.** |
| `tests/scripts/test_check_published_site.py` | **new, 15 tests.** Polling driven by an injected clock — deterministic and instant. |

Both scripts are **stdlib-only on purpose**: CI's test job installs `--extra agents --extra ui
--extra dev` and never `docs`, so a guard that imported `mkdocs` would be untestable exactly where
it needs testing.

#### The guards were falsified before they were trusted

A guard that has only ever been green proves nothing. Both were run against the **real** defect, not
a synthetic one:

- `check_site_assets.py` against `mkdocs.yml` **as it was before the fix**: **9 dangling references,
  exit 1**. Against the fixed config: **0, exit 0**.
- `check_published_site.py` against the **still-broken live site**, before deploying: page 200, both
  assets **404**, exit 1.

#### The placement of the assertion mattered more than the assertion

`BACKLOG.md` asked for *"a post-deploy assertion that the stylesheet the built `index.html` links
returns 200."* Right about the symptom, **wrong about the placement**: `mkdocs gh-deploy --force
--clean` writes a **parentless** commit — measured, `git rev-list --parents -n1 origin/gh-pages`
prints one field, **zero parents** — so there is no git revert path and an assertion after the
deploy can only announce the wreck. The artifact check now runs **between `mkdocs build` and
`gh-deploy`**, where a bad build is still only a failed job. **Both are kept**, because they prove
different things: the first that the artifact is complete, the second that the *deployment* worked —
which fails differently (`ghp-import` dropping files, a missing `.nojekyll`, Pages wired to the
wrong branch, a stale CDN). Learning [#149](PROJECT_LEARNINGS.md).

#### Six predictions, written before the push, all confirmed after

| # | Prediction | Measured after |
| --- | --- | --- |
| 1 | Exactly two workflow runs fire for `70e968b` | ✓ CI + Publish Tutorial. (GitHub's own *pages build and deployment* then ran for the new `gh-pages` commit — a third row in `gh run list`, not a third repo workflow.) |
| 2 | Publish Tutorial `success`, both new guards green | ✓ 7/7 steps, 37s; guard output read from the log, not the check mark |
| 3 | `origin/gh-pages` 7 files → **50**, 43 of them `assets/` | ✓ `cc66dea` → `e0311a0`, 50 files, 43 assets, **0 parents** |
| 4 | The live root page does **not** change — sha256 stays `b97eddcd…` | ✓ byte-identical, 12,533 bytes |
| 5 | The two assets flip **404 → 200** | ✓ 139,849 and 114,308 bytes; favicon 200 too |
| 6 | The wiki clone stays `d85cc67` | ✓ unmoved |

**Prediction 4 is the one worth keeping, and it was only right because it was measured first.** The
natural guess is *"the published page will change."* Diffing the candidate build against production
**before** deploying showed `site/index.html` was already **byte-identical** to the live page — so
the correct prediction was its opposite, and a stronger claim: an index that *had* changed would
have meant the fix touched something it had no business touching. Learning
[#152](PROJECT_LEARNINGS.md).

#### The polling earned its keep on its first live run

Attempts 1 and 2 both reported `2 of 3 URL(s) not yet 200` while Pages was still building; the third
succeeded, all inside 21 seconds. **A single-shot `curl` — the obvious reading of the backlog's
wording — would have failed the workflow on a completely correct deploy**, and the cheapest repair
for a check that cries wolf is to delete it. Learning [#150](PROJECT_LEARNINGS.md).

#### Two defects in my own new code, found by my own tests, fixed rather than papered over

1. **`--require-css` reported a falsehood in the commonest failure case.** When the stylesheet was
   *referenced but missing* it said *"no stylesheet is referenced by any page"* — false, and a
   duplicate of a problem already reported as a dangling reference. Now `css_referenced` and
   `css_present` are tracked separately and that branch fires only for a site that links no
   stylesheet at all.
2. **`check(fetch=probe)` bound the collaborator at definition time**, so
   `monkeypatch.setattr(mod, "probe", …)` never reached it and the call fell through to the real
   network with the production 300s/10s defaults. **The symptom was a two-minute suite hang, not a
   failure.** Fixed by resolving at call time; the regression guard passes `--timeout 0` so a
   reintroduction fails in milliseconds rather than reproducing the hang. Learning
   [#151](PROJECT_LEARNINGS.md).

#### Verification — everything run, nothing reasoned about

| Check | Result |
| --- | --- |
| local suite | **1275 passed, 9 skipped** (was 1230 + 9) |
| `ruff check src/ tests/ packages/ scripts/` | clean (CI's exact command) |
| `mypy` | `Success: no issues found in 68 source files` |
| push | `5055b55..70e968b`, ahead 1 → 0 |
| CI run `32554400688` | **success**, 4/4 |
| Publish Tutorial run `32554400687` | **success**, 7/7 steps, 37s (was 11-15s — the guards do real work) |
| pre-deploy guard, from the run log | `site base path: /model_project_constructor/` · `3 HTML page(s), 19 local reference(s) checked` · `1 stylesheet(s) referenced and present` · `OK` |
| post-deploy guard, from the run log | 2 retries, then `200` on all three URLs |
| `origin/gh-pages` | `cc66dea` → `e0311a0`; 7 → **50** files; 43 `assets/`; **0 parents** |
| live root page | 200, 12,533 bytes, sha256 `b97eddcd…` — **unchanged** |
| the two assets | **404 → 200**, 139,849 and 114,308 bytes |
| **rendered in a browser** | Material header, **working search box**, left nav, right-hand table of contents — all three reported symptoms gone. `DEVELOPMENT_WORKSTREAM.md`'s runtime-verification hard gate, not a status code. |
| console on the live page | no page errors; the only two entries are Chrome-extension messaging artifacts |
| wiki clone | `d85cc67`, unmoved — hook armed and correctly silent |
| recovery point | local branch **`gh-pages-pre-s237`** at `cc66dea`, captured before the deploy |

### Session 236 Handoff Evaluation (by Session 237)

**Score: 9/10.** The best handoff I have had to work from in this project's recent history, measured
the only way that matters: **how little discovery I had to do.** It named the deliverable, named the
suspect line correctly, named the exact command to confirm it, and named the destructive-deploy
hazard with its mitigation. It loses a point on the one instruction that was wrong in a way I had to
notice for myself.

**What helped.**
- **It named the right line, and it was right.** *"`mkdocs.yml:13-16` — the `exclude_docs` allowlist
  that is the leading suspect."* Confirmed. Inherited from S234, carried forward intact — which is
  precisely what [#144](PROJECT_LEARNINGS.md) says usually fails to happen.
- **It handed me the confirming command.** *"`uv sync --extra docs && uv run mkdocs build` and look
  for `site/assets/`."* That is the whole diagnosis in one line, and it worked verbatim.
- **Gotcha 9 was the design brief for the deliverable.** *"The workflow reports success in 11-15s
  while dropping 43 files. Assert the asset returns 200; do not read the green check."* Both guards
  exist because of that sentence.
- **It named the destructive property and the mitigation in the same breath** — *"`mkdocs gh-deploy
  --force --clean` writes a parentless commit … capture `gh-pages` first"* — so the recovery branch
  was taken before the first deploy rather than after the first scare. Independently re-measured
  here (`--parents -n1` → 0 parents), and true.
- **Gotcha 5 paid off silently and continuously.** `grep` is still a `ugrep --ignore-files` wrapper;
  I used `command grep`/`git grep` throughout and never had to wonder about an empty result.
- **Gotcha 6's arithmetic held.** It predicted S237 arrives under the 1,500-line trigger. This file
  was **1,462** lines at session start. Correct, and it stopped me from trimming.

**What was missing.**
- **Nothing about publish latency**, which decides whether the assertion it prescribed is even
  implementable. Written literally as a single `curl`, that check goes red on a correct deploy —
  measured here: two retries were needed. An instruction to assert against an asynchronously
  published artifact has to say "poll", or it prescribes a flake.
- **It said `workflow_dispatch` was the way to exercise this.** True, and unnecessary in the event:
  any fix must touch `mkdocs.yml`, which is *in* the path filter, so the ordinary push fired the
  deploy. Not wrong — but it presented as the method something that turned out to be a fallback.

**What was wrong.**
- **The assertion's placement.** *"The fix should add a post-deploy assertion"* — carried forward
  verbatim from `BACKLOG.md`. On a publish with **no revert path**, an after-the-fact assertion can
  only report the damage. The check that matters runs before `gh-deploy`. Both handoff and backlog
  said "post-deploy" and neither noticed the contradiction with the parentless-commit warning
  sitting three lines away in the same item.

**ROI: strongly positive, and the highest of any handoff I can measure here.** Its two defects were
both about the *shape of the fix*, not the diagnosis — and the diagnosis is the expensive half.

### Session 237 Self-Assessment

**Score: 8/10.** The site is fixed and the fix is proved at every level the project asks for —
mechanism read from source, guards falsified against the real defect, predictions written before the
irreversible act, and the page loaded in a browser. What keeps it off 9 is that **two of the three
defects fixed this session were in code I had just written**, and one of them was a number I typed
instead of derived — the exact class of error this project has now shipped for five consecutive
sessions.

**+** **I read the mechanism instead of confirming the hypothesis.** A `mkdocs build` showing no
`assets/` would have been enough to act on. It would not have told me *why*, and "why" is what makes
`!/assets/` a defensible one-line fix rather than a lucky one. `build.py:289`/`:294` is the whole
finding, and it is three lines of someone else's source.
**+** **I ran both guards red against the real historical defect before wiring them in.** Not a
synthetic fixture — the actual pre-fix `mkdocs.yml`, and the actual still-broken live site. A guard
that has only ever been green is a decoration.
**+** **I diffed the candidate against production before predicting.** That inverted prediction 4
from "the page changes" to "the page must not change," which is both correct and a stronger claim.
**+** **I fixed the assertion's placement instead of implementing the instruction I was given.** The
backlog's own text contained the contradiction (parentless commit, post-deploy check); noticing it
cost nothing and is the difference between preventing and announcing.
**+** **I let my own tests correct me twice**, including once where the code was wrong and the test
was right about a message being false. Neither defect would have been visible from the outside.

**−** **I wrote `assert len(problems) == 5` with a comment justifying the 5, and the answer was 4.**
I counted references in my head instead of deriving them. That is [#146](PROJECT_LEARNINGS.md)
exactly, in a session that cites #146 — and it is the fifth consecutive session whose self-reported
defect is a numeral in prose or a comment. The test caught it, which is the only reason it is a
footnote instead of a shipped lie.
**−** **I shipped a function meant to be injectable with its collaborator bound as a default
argument.** The cost was not the bug, it was the *failure mode*: a two-minute hang with nothing to
read. I diagnosed it correctly on the first attempt, but I should not have written it.
**−** **I nearly shipped a guard whose message was false in its commonest failure case.** The
"no stylesheet is referenced" branch fired when one *was* referenced and missing. A guard that
misdescribes what it found teaches the next reader the wrong thing.
**−** **The deliverable grew from one config line to six files.** Defensible — the backlog asked for
the assertion, and the assertion is worthless in the wrong place — but I should name it rather than
let "one session" quietly cover a 3× larger change set than the item implied.
**−** **I left one real coverage gap and did not close it.** `uv.lock` pins `mkdocs-material` at
**9.7.6** and is **not** in the workflow's `paths:` filter, so a theme bump deploys nothing and is
first exercised by the *next* unrelated `docs/*.md` change. The guards make that a loud failure
rather than a silent one, which is why I left it — but adding `uv.lock` to the filter would fire a
public deploy on every dependency bump, and that is an outward-facing frequency decision, not a
close-out cleanup. Filed as gotcha 4 and item 3 below rather than decided unilaterally.

**Against the bar:** S234 found a DONE gate whose *exemption granularity* was the defect; S235 proved
an inherited assertion structurally incapable of a true positive; S236 found that a fact recorded six
times never reached the item that depended on it. This session's equivalent is smaller but the same
species: **the prescribed fix was in the wrong place, and the contradiction was already written down
three lines away in the same backlog item** — a parentless-commit warning next to a post-deploy
assertion. Nobody had to discover anything to see it; the two sentences simply never met. That is
S236's finding recurring inside a single paragraph rather than across six sessions.

**What's next.**

1. **The two operator decisions**, both filed with measurements and both blocking nothing else: the
   archive-banner ruling (one ruling disposes of 23 dead pointers) and the C4/C5 clone-independence
   restatement. These are now the oldest unblocked items on the list.
2. **The `publish_wiki.sh` / `post-commit` pair** — two small items in one subsystem, explicitly
   filed to be bundled into one session. `publish_wiki.sh:53` tests that the source directory
   *exists*, not that it is non-empty, and `rsync --delete` then publishes the emptying; the hook
   exits 0 in silence whenever it declines. Both run **unattended from a commit hook**, which is
   what makes them worth more than their size.
3. **Decide whether `uv.lock` belongs in Publish Tutorial's `paths:` filter** (see gotcha 4). A
   one-line change gated on one judgement: is a public deploy on every dependency bump acceptable?
4. **The sixth trim is next session or the one after — measure, do not project.** See gotcha 6.

**Key files:**
- `scripts/check_site_assets.py` — the pre-deploy guard. Its module docstring carries the root cause
  and the reason it is stdlib-only; read that before changing it.
- `scripts/check_published_site.py` — the live guard. `check()` takes injectable
  `fetch`/`sleep`/`now`; **keep `fetch` resolved at call time**, not as a default argument.
- `mkdocs.yml:10-26` — the allowlist and the comment explaining why `!/assets/` is load-bearing.
- `.github/workflows/publish-tutorial.yml` — 65 lines now (was 30). Step order is the design:
  build → assert artifact → deploy → assert live.
- `PROJECT_LEARNINGS.md` — **152 learnings**; #148–#152 are this session's. `CLAUDE.md:99` updated
  to match.

**Gotchas:**
1. **The published site is styled as of `e0311a0` — verify it, do not assume it.**
   `curl -sI https://rmsharp.github.io/model_project_constructor/assets/stylesheets/main.484c7ddc.min.css`
   must be 200. That filename carries a **content hash** and changes on any theme upgrade; a stale
   hash in a future note is expected, so re-derive it from the live `index.html` rather than pasting
   this one.
2. **`mkdocs gh-deploy` writes a PARENTLESS commit to `gh-pages`** — confirmed here, 0 parents.
   There is no `git revert`. Capture the branch before any deploy; this session's capture is
   `gh-pages-pre-s237` (`cc66dea`), alongside `gh-pages-preA4` and `gh-pages-pre-rename`.
3. **Do not run `mkdocs build` into the repo's own `.venv`.** `uv sync --extra docs` would prune the
   `agents`/`ui`/`dev` extras the test suite needs. Use
   `UV_PROJECT_ENVIRONMENT=<scratch>/docs-venv uv sync --extra docs` and keep `.venv` alone.
4. **`uv.lock` is NOT in Publish Tutorial's `paths:` filter**, and it pins `mkdocs-material` at
   9.7.6. A theme bump therefore deploys nothing at bump time; it is first exercised by the next
   `docs/*.md` or `mkdocs.yml` change. The new guards make that a **loud** failure, which is why it
   was left — but it is a real gap and it is item 3 above.
5. **`--strict` is not available to this build.** `docs/index.md` is a meta-refresh redirect and
   emits `unrecognized relative link 'tutorial/'` by design (`mkdocs.yml` sets
   `validation.links.unrecognized_links: warn` deliberately). `mkdocs build --strict` would fail the
   workflow on that warning. The asset guard is the substitute, and it checks something `--strict`
   does not.
6. **The sixth trim is NEXT SESSION.** This file is **1,756** lines with this record — measured
   after writing it, at fixed width (#105) — against `CLAUDE.md`'s **1,500**-line trigger, so
   **S238 arrives over the trigger and is the sixth trim.** S236 projected ~1,730 and S238; both
   correct. This record cost **294** lines (S236's cost 270). Cut back to ≤1,050, never below a
   4-record floor, two commits always, and re-derive the copy list with
   `git grep -l 'SESSION_NOTES-'` rather than trusting the inherited one — `CLAUDE.md` says so and
   the fifth trim found five unread copies by obeying it. **Re-measure at Phase 0 anyway; do not
   trim on this sentence alone.**
7. **Still zsh, and `grep` is still a `ugrep --ignore-files` wrapper.** `command grep` or `git grep`
   for anything load-bearing. Single-quote every heredoc delimiter.
8. **`gh issue list` is empty and that is expected** — the tracker is not in use. `BACKLOG.md`
   governs, and its plain-language index at the top is written for the operator. It is **18 items**
   now, and the index has exactly 18 rows — they were reconciled by count this session; keep them
   in step in the same commit.
9. **The wiki hook stayed silent and that is a real negative control** — armed (`core.hooksPath` →
   `.githooks`), aimed at `^docs/wiki/model_project_constructor/`, clone unmoved at `d85cc67`. No
   path in this session's commits touches that prefix.


### What Session 236 Did
**Deliverable:** **`master` is pushed — `98abb83..222df52`, 8 commits — and the push is VERIFIED, not
asserted.** Four falsifiable predictions were written down *before* the push and all four confirmed by
measurement after it. A read-only pre-push audit found one defect in the payload and it was fixed
before the blob became unamendable. No other work was started.

**Started / completed:** 2026-08-21 → 2026-08-22 (UTC). **Commits: three** — `9e89d6e` (the Phase 1B
claim, alone), `222df52` (the line-count correction), and this close-out. **Operator this session:**
*"go"*, then *"1"* — item 1 of Session 235's what's-next.

Documentation only, so **no `CHANGELOG.md` entry** (`PROJECT_CONVENTIONS.md` §2's cadence gate).
**`BACKLOG.md` is still 19 items** — one item's *cost note* was corrected; none opened or closed.

#### The push

| | |
| --- | --- |
| range | `98abb83..222df52` — 8 commits (S234's 3, S235's 3, this session's 2) |
| result | `98abb83..222df52  master -> master`; ahead **8 → 0** |
| CI | run `32551746562`, **success**, 4/4 jobs: Lint (ruff), Type check (mypy), Tests (pytest), Data Agent decoupling |
| Publish Tutorial | **did not fire** — exactly **1** run exists for `222df52`, and it is CI |
| pushed once | deliberately: `ci.yml` sets `cancel-in-progress: true`, so a quick second push greys the first run out and a cancelled run reads like a pass at a glance |

#### Four predictions, written before the push, all confirmed after

| # | Prediction | Measured after |
| --- | --- | --- |
| 1 | CI fires; all 4 jobs pass | ✓ `completed / success`, 4/4 |
| 2 | Publish Tutorial does **not** fire | ✓ 1 run for `222df52` (CI); Publish Tutorial's newest is still `c1fe06f`, 2026-08-20 |
| 3 | `gh-pages` stays `cc66dea`; live page sha256 stays `b97eddcd…`; both assets stay 404 | ✓ all three byte-identical to the pre-push baseline |
| 4 | wiki clone stays `d85cc67` | ✓ unmoved |

Prediction 3 is the one worth keeping: it proves the push published **nothing** to the public site,
which is the property `enterprise-migration.md` §1 warns is easy to get wrong ("pushing to `master`
is publishing"). It is true *here* only because the path filter did not match — not in general.

#### The audit found one thing, and it was in the PAYLOAD, not the action

**27 agents, 1.39M tokens, 5 lenses, 0 errors, `blocking: []`.** Four lenses — secrets, public
exposure, CI, side effects — came back clean, each by measurement (`gitleaks` with a *positive
control*; `.protected` → `false`; `hooks` → `[]`; ruff/mypy/pytest run with CI's exact commands).

**The single surviving finding was a number in a document, not a property of the push.** An audit
scoped to *"is it safe to push"* would have returned five green lenses and missed it. `SESSION_NOTES.md:229`
said the fifth trim's proof is **"1,378 lines"**. It is **1,441**, and always has been — one blob,
`a7512cb`, `wc -l` 1441 both on disk and at that commit. No derivation yields 1378 (non-blank 1319,
non-comment 1147, both 1025, body-after-header 1283). Every sibling number in the same seven-row
table re-measured **exact** — shard 976, banner 58, 1,761 → 901, 7 files — so it was a lone outlier,
not a house convention. And `git diff --stat` for that very commit prints **1441**: the correct value
was already in the commit, three lines away. Fixed in `222df52` **before** the push, because the
blob in `fabc8e6` becomes unamendable the moment it lands. Learnings [#146](PROJECT_LEARNINGS.md),
[#147](PROJECT_LEARNINGS.md).

#### The finding that outlives this session: item 2 was never blocked on a push

**Read the correction below before crediting this session with a discovery — my first draft of this
section claimed one, and it was false.** Every fact here was already written down. `publish-tutorial.yml:6-10`
filters on `docs/*.md`, `mkdocs.yml`, the workflow file and `pyproject.toml`; **GitHub Actions path
globs are non-recursive — `*` does not cross `/`** — so every change under `docs/architecture-history/`,
`docs/methodology/` and `docs/planning/` is *structurally incapable* of firing it. All 10 changed
paths were checked one at a time: **zero match.** Line 11 of the same block declares
`workflow_dispatch`, so **`gh workflow run publish-tutorial.yml` exercises the deploy with no commit
at all.**

**None of that is new, and the measurements say so.** `docs/planning/enterprise-migration.md:227`
has read *"**`docs/*.md` is non-recursive.**"* since `808b49b` (Session 182, 2026-07-27) — a file
this very record cites elsewhere. `git grep -c 'single-level\|single level' 98abb83 -- SESSION_NOTES.md`
→ **7**, across Sessions 228 through 233. And `workflow_dispatch`'s *purpose* was documented at birth:
`CHANGELOG.md:910`, Session 67 — *"plus manual `workflow_dispatch` so the operator can re-deploy
without a code change."*

**So the finding is not "nobody read the filter." It is that the mechanism was on record in at least
three places and the consequence never reached the item that depended on it.** Session 235's handoff
called the unstyled tutorial site *"the one item that **needs** a push to exercise"* while six of its
own predecessors' records said the filter is single-level. The facts and the conclusion lived in
different files and never met. `BACKLOG.md`'s cost notes — **both** of them — are corrected
accordingly. Learning [#144](PROJECT_LEARNINGS.md).

#### What I did NOT discover — credit where it belongs

While taking a pre-push baseline of the live site I measured that its two referenced assets 404 and
that `origin/gh-pages` carries no `assets/` tree at all. **That is Session 234's finding, already
written up in `BACKLOG.md` with a bisect I did not do.** I re-confirmed it at a later `HEAD`
(`222df52`, 2026-08-22) and added the how-to-exercise correction. I did not touch the bug itself —
that is item 2 and a separate session.

#### The wiki negative control is genuine, and now proved rather than assumed

S235's gotcha 9 says the hook must stay silent. Silence is also what a *disabled* hook produces, so
arming was proved separately: `core.hooksPath` → `.githooks` (local + worktree), `.githooks/post-commit`
present and `+x`, and its trigger literal read out of the file — `^docs/wiki/model_project_constructor/`,
the **post-rename** path. Armed, correctly aimed, and silent because no commit touches that prefix.
Learning [#145](PROJECT_LEARNINGS.md). *(A first reading appeared to show `hooksPath` unset; that
command had run inside a compound chain whose earlier `cd` into the wiki clone was still in effect.)*

#### Verification — everything run, nothing reasoned about

| Check | Result |
| --- | --- |
| push | `98abb83..222df52`, ahead 8 → **0**, `## master...origin/master` |
| CI | run `32551746562` **success**; 4/4 jobs green |
| workflow runs for `222df52` | **1** — CI only |
| Publish Tutorial newest run | still `c1fe06f`, 2026-08-20 — unchanged by this push |
| `gh-pages` tip | `cc66dea`, unmoved |
| live page sha256 | `b97eddcd…`, byte-identical to the pre-push baseline |
| the two assets | **404** before and after |
| wiki clone | `d85cc67`, unmoved |
| pre-push audit | 27 agents, 0 errors, `blocking: []`; 1 advisory, fixed |
| the fix | `1,378` → `1,441`, re-measured independently, 6 sibling numbers re-measured exact |
| close-out review | 6 agents, 5 lenses; **4 must-fix + 3 notes**, all reproduced and all applied before commit — including a false headline claim of my own |
| local suite | `1230 passed, 9 skipped`, 97.98% coverage |

### Session 235 Handoff Evaluation (by Session 236)

**Score: 8/10.** It named my deliverable, sized it correctly, and every gotcha it wrote about its own
workstream held. It lost two points on the two things it asserted without measuring — one of which
sat in the artifact I was pushing.

**What helped.**
- **Item 1 *was* the session.** "master is 5 commits ahead … six once this close-out lands" — I found
  exactly 6. Sized, counted, and correct. I did not have to decide what to do.
- **Gotcha 8 paid off immediately and repeatedly.** *"Still zsh, and `grep` is still a
  `ugrep --ignore-files` wrapper. `command grep` or `git grep` for anything load-bearing."* I used
  `command grep` throughout; #136 is the same trap and one this project has already been bitten by.
- **Gotcha 9 gave me an assertable constant**, not an instruction. *"The wiki clone must not move
  … (`d85cc67`)"* is a value I could diff against, which is what made prediction 4 checkable.
  (Its elided clause is "for a session like this one" — the scoping that makes it assertable here.)
- **Its self-assessment taught the successor a discipline, not just facts.** *"Measure last, and check
  that measuring did not change the thing measured"* (#105) is why the line count in this record was
  set after the prose, at fixed width.

**What was missing.**
- **It dropped a mechanism its own predecessors had recorded.** Six sessions (228-233) wrote down
  that the path filter is single-level, and `enterprise-migration.md:227` has said so since Session
  182 — yet the handoff still stated the consequence backwards. The cost was not to me; it was to
  item 2, which sat mischaracterized as push-blocked. **This is the failure the methodology exists to
  prevent, and it is not a reading failure — it is a carrying-forward failure.**
- **Nothing about the properties of pushing itself**, which is what it asked the next session to do:
  that secret-scanning push protection is **armed** (it *rejects* server-side, it does not warn), and
  that `ci.yml` sets `cancel-in-progress: true`. Both change how you push; both were one API call away.

**What was wrong.**
- **"The one item that *needs* a push to exercise"** — false twice over (non-recursive filter;
  `workflow_dispatch` exists). This is the expensive kind of wrong: it makes a cheap item look blocked.
- **Its own record's "1,378 lines"** (line 229) — off by 63, against a project learning (#105) that
  the same self-assessment cites twice. Fixed here in `222df52`.

**ROI: strongly positive.** Reading it cost minutes and set the entire session. The two defects were
both *claims about things outside its own deliverable* — its account of the trim it actually
performed was, on re-measurement, exact in six of seven numbers.

### Session 236 Self-Assessment

**Score: 7/10.** The push is done and proved rather than announced, and the pre-push audit caught a
number that would have become permanent. But **the most consequential claim in my own close-out was
false, and a review caught it, not me** — I wrote that the path-filter mechanism was "a mechanism
nobody had read" when six prior records and a plan section say otherwise. That is the same sentence
Session 235 had to write about itself, one session later, about a different artefact.

**+** **I wrote the predictions down before the irreversible act and checked all four after.** "CI
passed" is an announcement; "gh-pages is still `cc66dea` and the live page's sha256 is unchanged" is
a proof that the push published nothing. The second is what §1 of the migration plan actually cares
about.
**+** **I audited the payload, not just the action** — and that is the only reason the finding exists.
Four lenses aimed at *"is pushing safe"* were all clean; the one aimed at *"are the claims true"*
found the defect. I would not have thought to look at a line count in a table.
**+** **I re-measured the agent's finding myself before acting on it**, including all six sibling
numbers, and only then concluded it was an outlier rather than a convention. The adversarial verifier
had also corrected two of the finding's supporting arguments, so taking it at face value would have
put two wrong claims into the commit message.
**+** **I checked whether my "discovery" was already known before claiming it.** The `assets/` root
cause is Session 234's, already in `BACKLOG.md` with a bisect. Saying so cost nothing and FM #16
costs trust.
**+** **I read the mechanism instead of inheriting the frequency claim**, which converted the
backlog's highest-value item from push-blocked to dispatchable — without touching it.

**−** **I nearly built a finding on a misread.** `git config core.hooksPath` printed nothing and I
briefly had "the hook was never enabled, so three sessions' negative controls are vacuous" half-drafted.
The command had run in the wiki clone: an earlier `cd` in the same `;`-chain was still in effect. One
step later I caught it. The lesson is not "be careful with `cd`" — it is that a *surprising* negative
from a repository-scoped command should trigger "where did this run?" before "what does this mean?"
**−** **My audit brief said `a707a9e..HEAD` for a 7-commit range.** `A..B` excludes `A`. Two lenses
caught it independently and re-derived the set from `origin/master..HEAD`, so nothing went unreviewed
— but that was their discipline covering my error, and a brief that states both a range and a count
can check itself with one command (#147).
**−** **The audit's ratio is heavy against [#124](PROJECT_LEARNINGS.md).** 27 agents and 1.39M tokens
for one five-character fix. I set no `maxItems` per lens and left the per-finding verify fan-out
uncapped, which is precisely the expensive ingredient #124 names. Defensible for an irreversible
public push; not a template.
**−** **I claimed a discovery that six prior records already contained, and it took a review to stop
it reaching `PROJECT_LEARNINGS.md`.** My draft said the non-recursive filter was *"a mechanism nobody
had read."* `enterprise-migration.md:227` has said it since Session 182; seven "single-level" mentions
sit in `SESSION_NOTES.md` at the very commit I pushed from; `workflow_dispatch`'s purpose is in
`CHANGELOG.md:910` from Session 67. **I checked whether the fact was actionable and never checked
whether it was known** — and I had already, in the same session, congratulated myself for doing
exactly that check on the `assets/` finding. The real finding survived and is better: the mechanism
was recorded six times and the consequence never reached the item. But the framing was self-serving
and it is FM #16's shape. Learning [#144](PROJECT_LEARNINGS.md) is rewritten around the correction.
**−** **Four must-fixes and three notes in one close-out.** Beyond the above: `10 lines` for a 30-line
file, repeated in five places and into a learning; `BACKLOG.md` left contradicting itself in adjacent
paragraphs because I corrected the index row and not the item's own cost line; `CLAUDE.md:99` left
stale at 143 learnings; a §2.2/§1 misattribution; and two of my quotations of Session 235 were
non-verbatim **inside a bullet praising its precision**. Prose accuracy is now this project's failure
surface for the fourth consecutive session.
**−** **The deliverable was "push" and it now takes two pushes**, because this close-out is itself a
commit. Unavoidable given the protocol, but it means CI runs twice and the second run is the one a
reader will see first.

**Against the bar:** S233 turned a safety claim into a measurement; S234 found that a DONE gate's
*exemption granularity* was the defect; S235 proved an inherited assertion structurally incapable of a
true positive. This session's equivalent is smaller and of a different kind: **a fact recorded six
times across six sessions still failed to reach the one item whose cost depended on it.** That is a
defect in the compounding mechanism itself, not in any one session's diligence — and it is worth more
than the push, which was never the hard part. I reached it only after a review demolished the more
flattering version, which is the honest way to record it.

**What's next.**

1. **The unstyled tutorial site — now the obvious pick, and cheaper than it was filed as.** It does
   **not** need a push. `gh workflow run publish-tutorial.yml` runs the real deploy on demand.
   **Capture `gh-pages` first** — `mkdocs gh-deploy --force --clean` writes a *parentless* commit
   (`enterprise-migration.md` §2.3: no git revert path). S234's hypothesis is in `BACKLOG.md`:
   `mkdocs.yml:13-16`'s fail-closed `exclude_docs` allowlist (`/*`, `!/index.md`, `!/tutorial.md`)
   probably also excludes the theme's `assets/` tree. Confirming it needs a local `mkdocs build`,
   which is now cheap: `uv sync --extra docs && uv run mkdocs build` and look for `site/assets/`.
   The fix should add a post-deploy assertion that the stylesheet `index.html` links returns 200.
2. **The two operator decisions**, both filed with measurements and both blocking nothing else: the
   archive-banner ruling (one ruling disposes of 23 dead pointers) and the C4/C5 clone-independence
   restatement.
3. **The sixth trim** is roughly two sessions out — see gotcha 6.

**Key files:**
- `.github/workflows/publish-tutorial.yml` — **lines 3-11** decide item 2's cost (the file is 30
  lines). Read the `paths:` list and the `workflow_dispatch:` line before planning anything about the
  tutorial site.
- `BACKLOG.md` §"The published tutorial site has shipped unstyled…" — S234's measurement and bisect,
  plus this session's corrected how-to-exercise note.
- `PROJECT_LEARNINGS.md` — **147 learnings**; #144–#147 are this session's.
- `mkdocs.yml:13-16` — the `exclude_docs` allowlist that is the leading suspect.

**Gotchas:**
1. **Publish Tutorial's path filter is non-recursive.** `docs/*.md` matches `docs/index.md` and
   `docs/tutorial.md` and **nothing nested**. Do not conclude from a quiet push that the workflow is
   broken, and do not plan a push in order to fire it — use `workflow_dispatch`.
2. **Secret-scanning push protection is ARMED on this repo.** If it ever trips, the push is
   **rejected server-side** — nothing lands — and to a caller not reading stderr it looks like a
   network or auth failure. Measured clean for this push; do not assume for one that adds new files.
3. **`ci.yml` sets `cancel-in-progress: true`.** Push once and let it settle. Two quick pushes leave
   the first run grey-`cancelled`, which at a glance in `gh run list` is easy to read as a pass.
   **This close-out is a second push and will start a second CI run** — check that one, not the first.
4. **A `cd` inside a `;`-chain relocates every later command in that chain.** A repository-scoped
   command that returns a surprising negative may simply have run somewhere else. Ask "where did this
   run?" before "what does this mean?"
5. **Still zsh, and `grep` is still a `ugrep --ignore-files` wrapper.** `command grep` or `git grep`
   for anything load-bearing. Single-quote every heredoc delimiter.
6. **The trim trigger fires in two sessions, not one — do not trim next session.** This file is
   **1,462** lines with this record (measured after writing it, at fixed width — #105), against
   `CLAUDE.md`'s 1,500-line trigger. This record cost **270** lines, above the ~204 S235 projected,
   so the arithmetic is: S237 arrives under the trigger and adds ~270 → ~1,730; **S238 arrives over
   it and is the sixth trim.** Re-measure rather than trusting this projection.
7. **The wiki hook is armed and correctly aimed** — `core.hooksPath=.githooks`, prefix
   `^docs/wiki/model_project_constructor/` (post-rename). Clone at `d85cc67`. Its silence on a session
   like this one is a real negative control, not an accident; if it ever fires without a `docs/wiki/`
   change, the prefix has drifted.
8. **`gh issue list` is empty and that is expected** — the issue tracker is not in use. `BACKLOG.md`
   governs priorities, and its plain-language index at the top is written for the operator.
9. **The live site is the only thing that tells you the tutorial deploy worked.** The workflow reports
   **success in 11-15s** while dropping 43 files. Assert the asset returns 200; do not read the green
   check.

