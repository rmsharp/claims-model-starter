#!/usr/bin/env bash
# SESSION_NOTES-pointer-collapse.verify.sh — the proof for Session 246's COLLAPSE of the five
# oldest pointer blocks in SESSION_NOTES.md's front matter.
#
#   bash <this>              prove the collapse changed exactly what it declared, and nothing else
#   bash <this> --self-test  prove this proof can FAIL (46 mutants; exit 2 if any survives)
#
# THIS IS NOT A TRIM AND NOT A SHARD PROOF. No record moved, no shard was written, no session was
# archived. Read `SESSION_NOTES-S241-through-S239.md.verify.sh` for the L-series; this file is a
# sibling of that lineage, not a member of it, and its assertions are lettered C0-C6 on purpose.
# Session 245 had to write a paragraph recording that its L14 was NOT the L14 a previous trim had
# drafted and rejected, so that a later trim would not resurrect the dead one believing it live. A
# second numbering costs nothing and removes that whole failure mode.
#
# WHAT THIS EXISTS TO PROVE. Operator ruling (a), 2026-08-25: Session 245 measured the retention
# rule's 1,050-line target converging on its four-record floor, projected the ninth trim at
# 1,101-1,248 lines while holding the floor, and put three remedies up. This is the chosen one --
# collapse 176 lines of frozen pointer prose into one table of cut keys and proof paths. (The
# removed size is derived by C0/SIZE; the added size is printed by a plain run, and is stated
# in no comment here -- the first draft said "42-line" and "17 mutants" and both were stale
# and read by nothing, which is this file's own subject matter and a review found them.)
#
# THE PREMISE THAT MADE IT SAFE WAS DERIVED, NOT INHERITED. Session 245 wrote that "each earlier
# proof reads its artifacts at its own commit, so compressing them disturbs nothing." That sentence
# is the entire justification for this deliverable and no assertion anywhere reads it. Session 246
# tested it: corrupt the fifth trim's block in the working tree, run all eight shard proofs -- all
# eight GREEN. Then the stronger form: corrupt the LIVE pointer block, the one that block and
# CLAUDE.md both call "the authority" -- its routing clause, its archived span and its size figures
# -- and all eight stay GREEN again. Every shard proof resolves its `before`/`after` from
# `git log --diff-filter=A` on its own shard and reads SESSION_NOTES.md at that commit; the
# working-tree copy is used only by the fallback branch that fires when a trim is not yet
# committed. So the premise holds, and it holds for a reason bigger than the premise:
#
#   FROM THE MOMENT A TRIM COMMIT LANDS, THE FRONT MATTER AN AGENT ACTUALLY OPENS IS READ BY
#   NOTHING. Fourteen assertions guard eight historical snapshots. The live file guards nothing.
#
# C6 is the first assertion in this repository to read that copy. It closes the hole for this table
# only -- deliberately: the general fix is a deliverable, not a side effect, and it is written out
# in Session 246's handoff rather than described.
#
# THE EIGHT ASSERTIONS
#
#   C0 PIN         OLD_BLOCKS -- the 176 removed lines, embedded below verbatim -- occurs exactly
#                  once in SESSION_NOTES.md at the declared pre-collapse commit, and is exactly 176
#                  lines. This is a PIN, not a derivation, and is labelled as one: the literal was
#                  generated from the artifact, so C0 cannot discover that the removal was wrong.
#                  What it does is make either copy impossible to change alone, which is the same
#                  service L6 performs for a shard banner. It also makes this file a second home
#                  for the removed prose, so "nothing was lost" does not rest on git alone.
#   C1 CONFINEMENT the post-collapse front matter is the pre-collapse front matter with exactly one
#                  OLD_BLOCKS -> NEW_TABLE replacement and the 3 declared substitutions, and
#                  nothing else. They are whole PARAGRAPHS, not fragments: a fragment substitution
#                  leaves the surrounding text wrapped for the sentence it replaced, and the first
#                  draft of this collapse shipped 132- and 153-character lines into a file hand-
#                  wrapped at 100 because of it. It also missed one falsified sentence entirely --
#                  the eighth block's "The seven blocks below" -- which paragraph-level anchors
#                  make hard to do, because the anchor IS the paragraph that has to stay true. Each substitution's anchor must occur exactly once in `before`
#                  (the L2/b0 lesson: a declaration that has gone stale against the file it claims
#                  to describe is worse than no declaration).
#   C2 RECORDS     the records zone is byte-identical across the collapse: same bytes, same order,
#                  same count, zero added. CLAUDE.md's two-commits rule says a trim commit carries
#                  no record edit; a collapse commit carries none either, and this is where that is
#                  enforced rather than promised.
#   C3 DERIVED     for each of the 5 rows: the archived record-heading count, the archived line
#                  count and the shard's total are MEASURED from that shard at its own add-commit,
#                  and the row's entire markdown line is then COMPOSED from the measurements and
#                  required to occur verbatim, exactly once, in NEW_TABLE. The table's figures are
#                  therefore derived rather than typed -- L12's lesson, taken one step further:
#                  L12 held declared integers against prose, C3 builds the prose from the integers.
#   C4 PROVENANCE  for each row: the declared trim sha IS the commit that added that shard; the
#                  declared "left live" span IS what SESSION_NOTES.md held at that commit; and both
#                  the shard and its .verify.sh exist on disk.
#   C5 ASSERTIONS  for each row: the assertion set that trim CONTRIBUTED, derived by parsing
#                  `^def L<N>(` out of that trim's proof AT ITS OWN ADD-COMMIT and subtracting its
#                  predecessor's set, equals the declared "added" column. Read at the add-commit,
#                  never from disk, for the reason L14 gives: L10 proves disk == add-commit, so
#                  reading disk would make this silently depend on L10 holding.
#   C6 LIVE        the WORKING TREE's SESSION_NOTES.md carries every composed table ROW exactly
#                  once and the table's opening line exactly once, and no longer contains
#                  OLD_BLOCKS. No L-series assertion reads the working-tree front matter; this one
#                  does, so the table stays guarded as the file grows and as later trims prepend
#                  blocks above it.
#                    PER ROW, NOT PER BLOCK, and a review is why. The first draft required the
#                    whole 48-line block verbatim. C1 pins that same literal against `after`, which
#                    artifacts() resolves at addcommit(SELF) -- FOREVER. So once a commit lands on
#                    top and amending is gone, ANY correction to the table's PROSE is red in one
#                    direction or the other: fix the file and C6 fails, fix the file and the
#                    literal and C1 fails. There was no green state containing a corrected table.
#                    Rows are the load-bearing half and C3 derives them, so C6 guards those and
#                    lets the prose be repaired the way this lineage repairs prose -- by a later
#                    session's declared substitution.
#   C7 COMPLETENESS every present-tense "**The N blocks below are frozen**" claim in the surviving
#                  front matter, with N DERIVED as the number of trim blocks that actually follow
#                  it. C1 gives confinement -- nothing changed beyond what was declared. It is
#                  silent on whether everything the collapse FALSIFIED was declared, and that list
#                  is hand-written. The first draft of this collapse proved the gap is real: it
#                  declared two members of that family and left the third, the eighth block's
#                  "**The seven blocks below**", standing and false with C0-C6 green. M42 is its
#                  mutant. This is L14/complete's argument in a different field: prove the list
#                  complete rather than assert it.
#
# WHAT IT DOES NOT PROVE. It does not prove the collapse was WISE -- that was the operator's call.
# It does not prove the surviving prose is TRUE. It does not re-prove any of the eight cuts: each
# has its own proof pinned to its own commit; run those too. And it says nothing about the rest of
# the front matter, which remains unguarded.
#
# ------------------------------------------------------------------------------------------------
# THE NEUTER SWEEP, MEASURED AND PUBLISHED -- BOTH LEVELS. Session 245 shipped the whole-assertion
# loop and left the per-arm one outstanding, and said so in its header rather than publishing a
# stale table. Both were run here, on the committed artifacts, with the exit code checked every
# time: 0 or 2, never 1. An early-`return [...]` guard is neutered to `return []`, never to `pass`
# -- the non-type-preserving form is what silently reported sixty arms as unreachable in Session
# 245 and cost that session a finding.
#
#   WHOLE ASSERTION -- neuter one function at a time; every one of the eight is load-bearing:
#     C0 -> M20, M26, M36, M39, M40                C1 -> M3, M4, M5
#     C2 -> M7, M8                                 C3 -> M9-M11, M18, M25, M29, M37, M38, M41
#     C4 -> M21, M22, M24, M30, M45                C5 -> M19, M32, M33
#     C6 -> M16, M17, M34, M35, M43                C7 -> M44
#
#   PER ARM -- 35 failure-emitting `out.append` statements inside C0-C7; 17 uniquely catch a
#   mutant. TWENTY-SIX of the 46 mutants exist only because a sweep or a review found the arm they
#   cover unreachable, which is the whole argument for running both: M21-M25 gave C4 and C3/ROW
#   their first unique coverage; M26-M36 reached one guard each; M37-M44 came from an adversarial
#   review of a GREEN, twice-swept proof; M45-M46 restored coverage that the review's own new arms
#   had taken away.
#
#   THE 18 ARMS WITH NO UNIQUELY-CATCHING MUTANT, measured and grouped by cause. Do not trust this
#   list after editing anything -- it was re-measured four times in one session and moved each time.
#
#   * MUTANT TAKEN BY A SIBLING ADDED IN THE SAME REVISION -- the seventh trim named this shape
#     (L12/absent and L13/absent losing theirs to their own new siblings) and it recurred here
#     three ways. C3/SESSION and C3/ORDINAL: every mutation of a declared row field also changes
#     the line C3/ROW composes, so ROW fires alongside. C0/SIZE: M26 moves DECLARED_OLD_LINES, and
#     C0/FIGURE requires that same integer in the table's prose, so FIGURE fires with it.
#     C1/b0 ANCHOR and C1/b0 SUBSTITUTION: M27 and M28 duplicate a literal, which now duplicates
#     table rows too, so C3/SET fires. C4/LEFT-LIVE-unreadable: C3/SESSION reads the same blob.
#     C6/opening-line: M16 removes the whole table, so the per-row arm fires first.
#   * REACHABLE, NEVER ALONE -- guards that fire only in company: C3/unreadable (M29),
#     C3/no-headings, C5/no-`def L<N>` (M33), C7/unparseable-count-word (M46). Each is exercised;
#     none is the sole objector, because a world broken enough to reach it breaks a sibling too.
#   * PROVABLY SUBSUMED -- C1 TABLE MISSING: `want` contains the table by construction, so
#     CONFINEMENT must fire with it; it is a better message ahead of a byte-offset diff.
#     C2's three arms are mutually shadowing (RECORD ORDER is guarded by `if not out`, so exactly
#     one of the three always fires); C2 as a whole uniquely catches M7 and M8.
#   * C3/SET's two arms cover each other: an undeclared row is both un-composed and a count
#     mismatch. Kept as two because they name different causes on failure.
#
# A green --self-test whose mutants never exercise a new arm is the same lie as a green run. That
# sentence is this lineage's, and this proof is NOT the first to honour it: the SIXTH trim's arm
# sweep found two unreachable arms of its own, and the SEVENTH's published a full table -- 55 arms,
# 26 with a uniquely-catching mutant, 29 without, each of the 29 named with its reason. Read that
# table (SESSION_NOTES-S238-through-S236.md.verify.sh, under "TWENTY-NINE ARMS"); it is more
# thorough than this one and it is where the taxonomy of subsumed arms comes from. The EIGHTH trim
# is the one that dropped the discipline -- it shipped with the sweep outstanding and asked its
# successor to run it. This proof runs it, at both levels, for its own seven assertions.
#
# The seventh trim also measured a trap this sweep walked into and recovered from: the arm sweep is
# structurally blind to an early return ON SUCCESS, and neutering an early-return GUARD to `pass`
# rather than `return []` makes the run die instead of surviving -- which scores as "caught" and
# hides the arm. C6's `is MISSING` guard did exactly that here until the neuter was made
# type-preserving. That is the same defect Session 245 lost sixty arm results to.

set -euo pipefail
exec python3 - "$@" <<'PYEOF'
import copy, re, subprocess, sys
from collections import Counter

LIVE = "SESSION_NOTES.md"
SELF = "docs/architecture-history/SESSION_NOTES-pointer-collapse.verify.sh"
ARCH = "docs/architecture-history/"

# ---- the declared pre-collapse commit. Hand-supplied. C1's `before` is read from it (or from the
#      collapse commit's parent once that exists, which must agree with it). ----
PRE = "ddd5660"

RECORD_START = re.compile(r"^### What Session (\S+) Did$")
DEF_L = re.compile(r"^def (L\d+)\(", re.M)
TABLE_ROW = re.compile(r"^\| \d+ \| ")
BLOCK_HEAD = re.compile(r"^\*\*(\w+) trim \(Session \d+\)", re.M)
# The family of present-tense positional claims a collapse can falsify. C7 derives their number.
BLOCKS_BELOW = re.compile(r"\*\*The (\w+) blocks? below (?:are|is) frozen", re.M)
SPELLED = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven",
           8: "eight", 9: "nine", 10: "ten"}
WORD = {v: k for k, v in SPELLED.items()}
WORD["The"] = 1

DECLARED_OLD_LINES = 176        # C0: how many lines the collapse removed

OLD_BLOCKS = """**Fifth trim (Session 235). Archived Sessions 231 → 228 — 4 record headings, 918 lines** into
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

"""

NEW_TABLE = """**The first five trims are one table now (Session 246).** Their pointer blocks stood here — 176
lines, the fifth trim's down to the first's — until the front matter became the half of this file
that grows: Session 245 measured the retention rule's 1,050-line target converging on its four-record
floor, put three remedies to the operator, and this is the one chosen. **Nothing was archived and no
record moved.** Each collapsed block is still readable byte-for-byte in two places — at commit
`ddd5660`, and embedded verbatim in the proof named below, which asserts those two are equal. Every
measurement in the table — every span, count, line total, trim commit and assertion credit — is
DERIVED from the artifacts at their own add-commits, and the proof COMPOSES each row's line from
those measurements rather than comparing against it. Two fields are declarations the proof checks
rather than measurements it takes: the ordinal, which is definitional, and the trim's session
number, which it re-derives as the newest record this file held at that commit.

| # | trim | archived | rec | lines | shard, under `docs/architecture-history/` | shard | left live | added |
|--:|------|----------|----:|------:|------------------------------------------|------:|-----------|-------|
| 1 | S222 `a9510ca` | 216 → 1 | 206 | 24,564 | `SESSION_NOTES-through-S216.md` | 24,590 | 222 → 217 | L0, L1, L2, L3 |
| 2 | S224 `07e1ab9` | 220 → 217 | 5 | 774 | `SESSION_NOTES-S220-through-S217.md` | 804 | 224 → 221 | L4 |
| 3 | S228 `e4ca944` | 224 → 221 | 4 | 891 | `SESSION_NOTES-S224-through-S221.md` | 933 | 228 → 225 | L5, L6, L7 |
| 4 | S231 `f3fea4e` | 227 → 225 | 3 | 738 | `SESSION_NOTES-S227-through-S225.md` | 790 | 231 → 228 | L8, L9 |
| 5 | S235 `a7512cb` | 231 → 228 | 4 | 918 | `SESSION_NOTES-S231-through-S228.md` | 976 | 235 → 232 | L10, L11 |

*`archived` is the session span that left this file and `rec` how many record headings went with it;
`lines`, the lines they took; `shard`, that file's total; `left live`, what this file was left
holding at that cut; `added`, the assertions that trim contributed to the inherited set. Each
shard's proof is its own path with `.verify.sh` appended.*

The proof is
[`SESSION_NOTES-pointer-collapse.verify.sh`](docs/architecture-history/SESSION_NOTES-pointer-collapse.verify.sh),
and its assertions are lettered **C0–C6** rather than numbered: this is not a trim, they are not the
`L`-series, and Session 245 had to record an `L14` collision to stop a later trim resurrecting a
rejected assertion under a live name. **C6 holds this table against the WORKING TREE; no `L`-series
assertion holds any PROSE against it** — which is the finding worth carrying forward on its own.
Every shard proof resolves its prose operands from its own trim commit: the live file *and*
`CLAUDE.md`, `README.md`, `BACKLOG.md` and `PROJECT_CONVENTIONS.md` are all read as they stood
**then**. What the `L`-series does read from disk is the shards and the proof scripts, by `L7`,
`L9` and `L10` — bytes, not claims. So the moment a trim lands, every
prose copy this apparatus exists to keep in step stops being checked — this front matter, the block
above that calls itself "the authority", and all four files `L8` reaches. Session 246 measured it,
with a control: corrupt the live pointer block's routing clause and figures, or `CLAUDE.md`'s shard
census, or `BACKLOG.md`'s, or `PROJECT_CONVENTIONS.md`'s, and all eight proofs stay green; edit an
ancestor shard on disk and they go red. Session 245's gotcha 2 — that those four are read *live* —
held only while its own trim was uncommitted. C6 closes this for the table above and nothing else.
**The rest is the ninth trim's, and it is the largest hole this lineage has.**

**Cutting is by byte position, never by authorship.** This ledger files a handoff evaluation under
its author, so Session N's evaluation of N−1 sits inside N's record and every cut so far has split
one from its subject. Expect that seam at every boundary. What these five trims found, argued and
rejected stays in their own blocks at the commits above; what they left BINDING is in `CLAUDE.md`'s
two `SESSION_NOTES.md`-is-trimmed bullets, which no collapse touches. **`grep` the shards; `Read`
none** — the first is 24,590 lines, an agent `Read` stops at 2,000 with no error and no marker, and
nothing watches any of them.

"""

FRONT_SUBST = (
    ("""**The seven blocks below are frozen at the SEVENTH through FIRST trims and describe THOSE cuts.**
This trim falsified exactly four passages of the seventh trim's block — which sessions this live
file holds, its routing paragraph, its count of stale shard banners, and its claim that the
ancestor figures are still unread — and rewrote all four as declared substitutions the proof checks
by exact equality. Every other byte of that block is original and the older six are untouched. Each
earlier proof reads its artifacts at its own shard's commit, so none is disturbed; all seven were
re-run green at this cut.
""",
     """**The two blocks below are frozen at the SEVENTH and SIXTH trims and describe THOSE cuts; the five
older ones are the table beneath them (Session 246).** This trim falsified exactly four passages of
the seventh trim's block — which sessions this live file holds, its routing paragraph, its count of
stale shard banners, and its claim that the ancestor figures are still unread — and rewrote all
four as declared substitutions the proof checks by exact equality. Every other byte of that block
is original and the older six were untouched at that cut. Each earlier proof reads its artifacts at
its own shard's commit, so none is disturbed; all seven were re-run green at this cut.
"""),
    ("""**The six blocks below are frozen at the SIXTH, FIFTH, FOURTH, THIRD, SECOND and FIRST trims and
describe THOSE cuts.** This trim falsified exactly three passages of the sixth trim's block — which
sessions this live file holds, its routing paragraph, and its count of stale shard banners — and
rewrote all three as declared substitutions the proof checks by exact equality. Every other byte of
that block is original and the older five are untouched. Each earlier proof reads its artifacts at
its own shard's commit, so none is disturbed; all six were re-run green at this cut.

""",
     """**The block below is frozen at the SIXTH trim and describes THAT cut; the five older ones are the
table beneath it (Session 246).** This trim falsified exactly three passages of the sixth trim's
block — which sessions this live file holds, its routing paragraph, and its count of stale shard
banners — and rewrote all three as declared substitutions the proof checks by exact equality. Every
other byte of that block is original and the older five were untouched at that cut. Each earlier
proof reads its artifacts at its own shard's commit, so none is disturbed; all six were re-run
green at this cut.

"""),
    ("""**The five blocks below are frozen at the FIFTH, FOURTH, THIRD, SECOND and FIRST trims and describe
THOSE cuts.** This trim falsified exactly three passages of the fifth trim's block — its claim about
which sessions this live file holds, its whole routing paragraph, and its count of how many shard
banners are stale — and rewrote all three as declared substitutions the proof checks by exact
equality. Every other byte of that block is original, and the fourth, third, second and first
trims' blocks are untouched. Each earlier proof reads its artifacts from the commit that added its
own shard, so this trim cannot disturb any of them; all five were re-run green at this cut, and a
session that doubts that should run them rather than reason about it.
""",
     """**The five blocks that stood below this one — the FIFTH trim's down to the FIRST's — are the table
beneath it now (Session 246); each is still readable at its own commit.** This trim falsified
exactly three passages of the fifth trim's block — its claim about which sessions this live file
holds, its whole routing paragraph, and its count of how many shard banners are stale — and rewrote
all three as declared substitutions the proof checks by exact equality. Every other byte of that
block is original, and the fourth, third, second and first trims' blocks were untouched at that
cut. Each earlier proof reads its artifacts from the commit that added its own shard, so this trim
"""),
)

# ---- the five collapsed trims. Hand-declared; C3/C4/C5 measure every field from git and compare.
#      (ordinal, trim session, trim sha, archived span, headings, archived lines,
#       shard basename, shard total lines, live span left behind, assertions that trim added) ----
ROWS = (
    (1, "222", "a9510ca", ("216", "1"),   206, 24564,
     "SESSION_NOTES-through-S216.md",       24590, ("222", "217"), ("L0", "L1", "L2", "L3")),
    (2, "224", "07e1ab9", ("220", "217"),    5,   774,
     "SESSION_NOTES-S220-through-S217.md",    804, ("224", "221"), ("L4",)),
    (3, "228", "e4ca944", ("224", "221"),    4,   891,
     "SESSION_NOTES-S224-through-S221.md",    933, ("228", "225"), ("L5", "L6", "L7")),
    (4, "231", "f3fea4e", ("227", "225"),    3,   738,
     "SESSION_NOTES-S227-through-S225.md",    790, ("231", "228"), ("L8", "L9")),
    (5, "235", "a7512cb", ("231", "228"),    4,   918,
     "SESSION_NOTES-S231-through-S228.md",    976, ("235", "232"), ("L10", "L11")),
)

ROOT = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                      capture_output=True, text=True, check=True).stdout.strip()
MISSING = object()


def blob(ref):
    r = subprocess.run(["git", "show", ref], capture_output=True, cwd=ROOT)
    if r.returncode:
        return None
    return r.stdout.decode("utf-8")          # bytes -> str; never $(...) which eats trailing newlines


def worktree(rel):
    try:
        with open("%s/%s" % (ROOT, rel), encoding="utf-8", newline="") as fh:
            return fh.read()
    except OSError:
        return MISSING


def addcommit(rel):
    return subprocess.run(["git", "log", "--diff-filter=A", "-1", "--format=%H", "--", rel],
                          capture_output=True, text=True, cwd=ROOT).stdout.strip()


def scan(lines):
    inside = False
    for i, raw in enumerate(lines):
        s = raw.rstrip("\r\n")
        if s.startswith("```") or s.startswith("~~~"):
            yield i, s, inside
            inside = not inside
            continue
        yield i, s, inside


def zones(text):
    """-> (front, [record, ...]). A record is a heading-delimited BYTE SPAN, never a session."""
    lines = text.splitlines(keepends=True)
    st = [i for i, s, ins in scan(lines) if not ins and RECORD_START.match(s)]
    if not st:
        return text, []
    bounds = st + [len(lines)]
    return "".join(lines[:st[0]]), ["".join(lines[a:b]) for a, b in zip(st, bounds[1:])]


def ids(text):
    _f, recs = zones(text)
    return tuple(RECORD_START.match(r.splitlines()[0]).group(1) for r in recs)


def row_line(ordinal, sess, sha, span, rec, arch_lines, shard, total, live, added):
    """The row's markdown line, COMPOSED from the values -- never matched loosely against the
    table. C3 feeds this the MEASURED numbers, so a typed figure cannot survive."""
    return ("| %d | S%s `%s` | %s → %s | %d | %s | `%s` | %s | %s → %s | %s |"
            % (ordinal, sess, sha, span[0], span[1], rec, format(arch_lines, ","),
               shard, format(total, ","), live[0], live[1], ", ".join(added)))


def rows_of(text):
    return [l for l in text.split("\n") if TABLE_ROW.match(l)]


def declared_front(before_front, old_blocks, new_table, subst):
    """The front matter this collapse is ALLOWED to produce."""
    out = before_front.replace(old_blocks, new_table, 1)
    for old, new in subst:
        out = out.replace(old, new, 1)
    return out


def gather(rows):
    """Everything read from git, once. Ancestor shards and proofs are read AT THEIR OWN
    ADD-COMMITS, never from disk -- L9/L10 prove disk == add-commit, so reading disk would make
    these assertions silently depend on those two holding."""
    world = {}
    for row in rows:
        shard = row[6]
        rel = ARCH + shard
        prel = rel + ".verify.sh"
        ssha = addcommit(rel)
        psha = addcommit(prel)
        world[shard] = {
            "addsha": ssha,
            "shard": blob("%s:%s" % (ssha, rel)) if ssha else None,
            "live": blob("%s:%s" % (ssha, LIVE)) if ssha else None,
            "proof": blob("%s:%s" % (psha, prel)) if psha else None,
            "shard_disk": worktree(rel),
            "proof_disk": worktree(prel),
        }
    return world


# =====================================================================================
# The assertions. Each returns a list of failure strings; empty == holds.
# =====================================================================================

def C0(pre_live, old_blocks, declared_lines, new_table):
    """A PIN, not a derivation -- see the header. It makes the two copies of the removed prose
    impossible to change alone, and gives this file custody of the second one."""
    out = []
    if pre_live is None:
        return ["C0 PIN: the declared pre-collapse commit %s does not hold %s -- the declaration "
                "is wrong, or the history was rewritten" % (PRE, LIVE)]
    n = pre_live.count(old_blocks)
    if n != 1:
        out.append("C0 PIN: the 176 removed lines occur %d times in %s at %s (want exactly 1) -- "
                   "the embedded copy is not the text that was removed" % (n, LIVE, PRE))
    got = old_blocks.count("\n")
    if got != declared_lines:
        out.append("C0 SIZE: the embedded removed text is %d lines; the collapse declares %d"
                   % (got, declared_lines))
    # L12's shape: hold the derived integer against the FORMATTED figure the prose prints. The
    # first draft of this table stated "176 lines" and "`ddd5660`" and neither was read by
    # anything -- the exact class the header calls this project's most self-reported defect,
    # reintroduced inside the block that replaces the collapsed prose. Found by review.
    for what, lit in (("removed-line count", str(declared_lines)), ("pinned commit", "`%s`" % PRE)):
        if new_table.count(lit) != 1:
            out.append("C0 FIGURE: the table states the %s %s %d times (want exactly 1) -- the "
                       "prose and the declaration have parted company"
                       % (what, lit, new_table.count(lit)))
    return out


def C1(before_front, after_front, old_blocks, new_table, subst):
    out = []
    if before_front.count(old_blocks) != 1:
        out.append("C1/b0 ANCHOR: the removed text occurs %d times in the pre-collapse front "
                   "matter (want exactly 1)" % before_front.count(old_blocks))
    for k, (old, _new) in enumerate(subst, 1):
        if before_front.count(old) != 1:
            out.append("C1/b0 SUBSTITUTION %d NOT UNIQUELY ANCHORED: its source text occurs %d "
                       "times in the pre-collapse front matter (want exactly 1) -- the declaration "
                       "has gone stale against the file it claims to describe"
                       % (k, before_front.count(old)))
    if new_table not in after_front:
        out.append("C1 TABLE MISSING: the declared table is not in the post-collapse front matter "
                   "verbatim -- 176 lines removed and nothing put in their place")
    want = declared_front(before_front, old_blocks, new_table, subst)
    if after_front != want:
        i = next((n for n, (a, b) in enumerate(zip(after_front, want)) if a != b),
                 min(len(after_front), len(want)))
        out.append("C1 CONFINEMENT: the front matter changed beyond the declared collapse + the %d "
                   "declared substitutions; first divergence at character %d (%d B got vs %d B "
                   "declared)" % (len(subst), i, len(after_front.encode()), len(want.encode())))
    return out


def C2(before_recs, after_recs):
    """A collapse commit carries no record edit -- the same rule CLAUDE.md sets for a trim commit,
    enforced here rather than promised."""
    out = []
    if before_recs != after_recs:
        b, a = Counter(before_recs), Counter(after_recs)
        for r in (b - a).elements():
            out.append("C2 RECORD LOST OR EDITED: %r" % r.splitlines()[0][:90])
        for r in (a - b).elements():
            out.append("C2 RECORD ADDED by the collapse commit: %r" % r.splitlines()[0][:90])
        if not out:
            out.append("C2 RECORD ORDER: the records zone holds the same records in a different "
                       "order (%d records)" % len(after_recs))
    return out


def C3(rows, world, new_table):
    """Measure, compose, then require. The table's numbers are built from the artifacts."""
    out, composed, seen = [], [], 0
    for (ordinal, sess, sha, span, rec, arch_lines, shard, total, live, added) in rows:
        w = world.get(shard)
        if not w or w["shard"] is None:
            out.append("C3 `%s`: not readable at its own add-commit -- nothing to measure" % shard)
            continue
        lines = w["shard"].splitlines()
        heads = [i for i, s, ins in scan(lines) if not ins and RECORD_START.match(s)]
        if not heads:
            out.append("C3 `%s`: no record headings -- grammar mismatch" % shard)
            continue
        m_rec, m_total, m_arch = len(heads), len(lines), len(lines) - heads[0]
        for what, got, want in (("record headings", m_rec, rec),
                                ("archived lines", m_arch, arch_lines),
                                ("shard total lines", m_total, total)):
            if got != want:
                out.append("C3 SIZE `%s`: measured %d %s at %s; the table declares %d"
                           % (shard, got, what, w["addsha"][:7], want))
        got_sess = ids(w["live"])[0] if w["live"] and ids(w["live"]) else None
        if got_sess != sess:
            out.append("C3 SESSION `%s`: the newest record this file held at %s is Session %s; "
                       "the table credits the trim to Session %s"
                       % (shard, w["addsha"][:7], got_sess, sess))
        if ordinal != seen + 1:
            out.append("C3 ORDINAL `%s`: it is row %d of the table but numbered %d"
                       % (shard, seen + 1, ordinal))
        seen += 1
        want_line = row_line(ordinal, sess, sha, span, m_rec, m_arch, shard, m_total, live, added)
        composed.append(want_line)
        n = new_table.count(want_line)
        if n != 1:
            out.append("C3 ROW `%s`: the row composed from the MEASURED figures occurs %d times in "
                       "the table (want exactly 1):\n           %s" % (shard, n, want_line))
    # SET: containment per declared row is not enough -- a review inserted a sixth row naming a
    # shard that does not exist and every assertion stayed green, because C3 iterated ROWS and
    # never the table. This is L8/set and L14/complete's lesson, one lineage over.
    present = [l for l in new_table.split("\n") if TABLE_ROW.match(l)]
    extra = [l for l in present if l not in composed]
    for l in extra:
        out.append("C3 SET: the table carries a row no declared trim composes: %s" % l[:110])
    if len(present) != len(rows):
        out.append("C3 SET: the table has %d data rows; %d trims are declared"
                   % (len(present), len(rows)))
    # COMPOSED, not searched: `count("five") >= 1` passed M41 because the word occurs twice in
    # this table's prose, so mangling one left the other. The phrase is built from len(ROWS).
    for shape in ("**The first %s trims are one table now", "What these %s trims found"):
        lit = shape % SPELLED.get(len(rows), "?")
        if new_table.count(lit) != 1:
            out.append("C3 FIGURE: the table states its own row count as %r %d times (want "
                       "exactly 1)" % (lit, new_table.count(lit)))
    return out


def C4(rows, world):
    out = []
    for (_o, _s, sha, span, _r, _al, shard, _t, live, _a) in rows:
        w = world.get(shard)
        if not w or not w["addsha"]:
            out.append("C4 `%s`: git knows no commit that ADDED this shard" % shard)
            continue
        if w["addsha"][:len(sha)] != sha:
            out.append("C4 PROVENANCE `%s`: the table names trim commit %s; the commit that added "
                       "this shard is %s" % (shard, sha, w["addsha"][:7]))
        if w["shard"] is not None:
            got = ids(w["shard"])
            if not got or (got[0], got[-1]) != span:
                out.append("C4 SPAN `%s`: it holds Sessions %s -> %s; the table says %s -> %s"
                           % (shard, got[0] if got else "?", got[-1] if got else "?",
                              span[0], span[1]))
        if w["live"] is None:
            out.append("C4 LEFT-LIVE `%s`: %s is unreadable at %s" % (shard, LIVE, sha))
        else:
            got = ids(w["live"])
            if not got or (got[0], got[-1]) != live:
                out.append("C4 LEFT-LIVE `%s`: at %s the live file held Sessions %s -> %s; the "
                           "table says %s -> %s" % (shard, sha, got[0] if got else "?",
                                                    got[-1] if got else "?", live[0], live[1]))
        for kind, key in (("shard", "shard_disk"), ("proof", "proof_disk")):
            if w[key] is MISSING:
                out.append("C4 GONE `%s`: the %s the table sends readers to is not on disk"
                           % (shard, kind))
    return out


def C5(rows, world):
    """What each trim CONTRIBUTED, derived by parsing its own proof at its own add-commit."""
    out = []
    prev = frozenset()
    for (_o, sess, _sha, _sp, _r, _al, shard, _t, _lv, added) in rows:
        w = world.get(shard)
        if not w or w["proof"] is None:
            out.append("C5 `%s`: its proof is not readable at its add-commit" % shard)
            prev = frozenset()
            continue
        have = frozenset(DEF_L.findall(w["proof"]))
        if not have:
            out.append("C5 `%s`: its proof defines no `def L<N>(` -- grammar mismatch" % shard)
            prev = frozenset()
            continue
        gained = tuple(sorted(have - prev, key=lambda x: int(x[1:])))
        if gained != tuple(added):
            out.append("C5 ASSERTIONS `%s` (Session %s): that proof adds %s over its predecessor; "
                       "the table says %s" % (shard, sess, list(gained), list(added)))
        prev = have
    return out


def C6(live_wt, old_blocks, new_table):
    """The only assertion in this repository that reads the WORKING-TREE front matter."""
    if live_wt is MISSING:
        return ["C6 LIVE: %s is not on disk" % LIVE]
    out = []
    for r in rows_of(new_table):
        n = live_wt.count(r)
        if n != 1:
            out.append("C6 LIVE: a table row occurs %d times in the working tree's %s (want "
                       "exactly 1): %s" % (n, LIVE, r[:110]))
    head = new_table.split("\n")[0]
    if live_wt.count(head) != 1:
        out.append("C6 LIVE: the table's opening line occurs %d times in the working tree's %s "
                   "(want exactly 1) -- the block was removed or duplicated"
                   % (live_wt.count(head), LIVE))
    if old_blocks in live_wt:
        out.append("C6 LIVE: the 176 collapsed lines are STILL in the working tree's %s -- the "
                   "collapse is declared but not applied" % LIVE)
    return out


def C7(after_front):
    """COMPLETENESS, where C1 gives only confinement. C1 proves nothing changed beyond what was
    declared; it is silent on whether everything the collapse FALSIFIED was declared, and the
    substitution list is exactly the hand-written list PROJECT_LEARNINGS #126 warns about. The
    first draft of this collapse proved it: it declared the two "**The N blocks below are frozen**"
    sentences in the blocks it was cutting toward and left the third -- the eighth block's "**The
    seven blocks below**" -- standing and false, with C0-C6 green. So derive that family's number
    instead of declaring it: for each such claim, count the trim blocks that actually follow it."""
    out = []
    heads = [m.start() for m in BLOCK_HEAD.finditer(after_front)]
    for m in BLOCKS_BELOW.finditer(after_front):
        word = m.group(1)
        want = sum(1 for h in heads if h > m.start())
        got = WORD.get(word.lower(), WORD.get(word))
        if got is None:
            out.append("C7 COMPLETENESS: unparseable count word %r in a positional claim at "
                       "character %d" % (word, m.start()))
        elif got != want:
            out.append("C7 COMPLETENESS: %r claims %d block(s) below it; %d trim block(s) actually "
                       "follow. A collapse falsified this sentence and did not declare it."
                       % (after_front[m.start():m.start() + 62], got, want))
    return out


def check(before, after, live_wt, rows, subst, old_blocks, new_table, pre_live, world,
          declared_lines=DECLARED_OLD_LINES):
    bf, br = zones(before)
    af, ar = zones(after)
    fails = []
    fails += C0(pre_live, old_blocks, declared_lines, new_table)
    fails += C1(bf, af, old_blocks, new_table, subst)
    fails += C2(br, ar)
    fails += C3(rows, world, new_table)
    fails += C4(rows, world)
    fails += C5(rows, world)
    fails += C6(live_wt, old_blocks, new_table)
    fails += C7(af)
    return fails


# =====================================================================================
def artifacts():
    sha = addcommit(SELF)
    if sha:
        before, after = blob("%s^:%s" % (sha, LIVE)), blob("%s:%s" % (sha, LIVE))
        parent = subprocess.run(["git", "rev-parse", "%s^" % sha], capture_output=True,
                                text=True, cwd=ROOT).stdout.strip()
        src = "the collapse commit %s (parent %s)" % (sha[:7], parent[:7])
        note = None if parent[:len(PRE)] == PRE else (
            "DECLARATION: the collapse commit's parent is %s; PRE declares %s" % (parent[:7], PRE))
    else:
        before, after = blob("HEAD:%s" % LIVE), worktree(LIVE)
        head = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                              text=True, cwd=ROOT).stdout.strip()
        src = "HEAD %s vs the working tree (collapse not yet committed)" % head[:7]
        note = None if head[:len(PRE)] == PRE else (
            "DECLARATION: HEAD is %s; PRE declares %s" % (head[:7], PRE))
    return before, after, worktree(LIVE), blob("%s:%s" % (PRE, LIVE)), src, note


def self_test(before, after, live_wt, pre_live, world):
    bf, _br = zones(before)
    af, ar = zones(after)
    W = lambda f: {k: (dict(v) | f(k, dict(v))) for k, v in world.items()}

    r1 = list(ROWS[1])
    r1[4] = 6                                                    # heading count
    rows_m9 = (ROWS[0], tuple(r1)) + ROWS[2:]
    r2 = list(ROWS[2]); r2[5] = 890                              # archived lines
    rows_m10 = ROWS[:2] + (tuple(r2),) + ROWS[3:]
    r3 = list(ROWS[3]); r3[7] = 791                              # shard total
    rows_m11 = ROWS[:3] + (tuple(r3),) + ROWS[4:]
    r4 = list(ROWS[4]); r4[2] = "deadbee"                        # trim sha
    rows_m13 = ROWS[:4] + (tuple(r4),)
    r5 = list(ROWS[0]); r5[8] = ("222", "218")                   # left-live span
    rows_m14 = (tuple(r5),) + ROWS[1:]
    r6 = list(ROWS[2]); r6[9] = ("L5", "L6")                     # assertions added
    rows_m15 = ROWS[:2] + (tuple(r6),) + ROWS[3:]
    r7 = list(ROWS[1]); r7[0] = 9                                # ordinal
    rows_m25 = (ROWS[0], tuple(r7)) + ROWS[2:]

    # M27/M28 must leave C1 CONFINEMENT satisfied while breaking only the uniqueness guard, so
    # `after` is REBUILT from the mutated `before` rather than patched. A b0 arm that only ever
    # fires alongside CONFINEMENT is a message, not an assertion; these two make it an assertion.
    def rebuilt(before_text):
        f, r = zones(before_text)
        return declared_front(f, OLD_BLOCKS, NEW_TABLE, FRONT_SUBST) + "".join(r)

    dup_blocks = before.replace(OLD_BLOCKS, OLD_BLOCKS + OLD_BLOCKS, 1)
    dup_subst = before.replace(FRONT_SUBST[0][0], FRONT_SUBST[0][0] * 2, 1)

    def with_table(nt):
        """A consistent world in which the table really is `nt`: `after` rebuilt from `before`
        and the working tree rebuilt from `after`. Without this, every table mutant trips C1 and
        proves nothing about C0/FIGURE, C3/SET or C3/FIGURE."""
        f, r = zones(before)
        a = declared_front(f, OLD_BLOCKS, nt, FRONT_SUBST) + "".join(r)
        return a, a

    FAKE_ROW = ("| 6 | S999 `deadbee` | 999 → 998 | 7 | 1,234 | "
                "`SESSION_NOTES-S999-through-S998.md` | 1,300 | 999 → 997 | L99 |\n")
    t_extra = NEW_TABLE.replace("| 5 | S235", FAKE_ROW + "| 5 | S235", 1)
    t_176 = NEW_TABLE.replace("stood here — 176", "stood here — 999", 1)
    t_pre = NEW_TABLE.replace("`ddd5660`", "`deadbee`", 1)
    t_five = NEW_TABLE.replace("The first five trims", "The first 5 trims", 1)
    a_extra, l_extra = with_table(t_extra)
    a_176, l_176 = with_table(t_176)
    a_pre, l_pre = with_table(t_pre)
    a_five, l_five = with_table(t_five)

    r8 = list(ROWS[3]); r8[1] = "230"                            # trim session number
    rows_m37 = ROWS[:3] + (tuple(r8),) + ROWS[4:]
    after_c7 = after.replace("**The block below is frozen at the SIXTH trim",
                             "**The four blocks below are frozen at the SIXTH trim", 1)
    # M44 must satisfy C1 to prove C7 is not redundant with it: the false claim is planted in
    # `before` and `after` is REBUILT, so the front matter is exactly what the declaration says
    # it should be and C7 is the only objector. M42 mutates the artifact alone and C1 sees it.
    # Every positional claim in `before` sits INSIDE a substitution anchor, so mutating one there
    # trips C1/b0 and proves nothing. Plant a fresh false claim at the end of the front matter,
    # outside every anchor, and rebuild `after`: C0-C6 are then all satisfied and C7 alone objects.
    b_c7 = before.replace("\n---\n\n## ACTIVE TASK",
                          "\n**The two blocks below are frozen at nothing at all.**\n\n---\n\n## ACTIVE TASK", 1)
    f_c7, r_c7 = zones(b_c7)
    a_c7 = declared_front(f_c7, OLD_BLOCKS, NEW_TABLE, FRONT_SUBST) + "".join(r_c7)

    first_row = row_line(*ROWS[0])
    assert first_row in NEW_TABLE, "self-test fixture missing: composed row 1 absent from the table"
    table_typo = NEW_TABLE.replace(first_row, first_row.replace("24,564", "24,563"), 1)

    a_rec = ar[0]
    mutants = [
        ("M1  the embedded copy of the removed prose altered by one character",
         before, after, live_wt, ROWS, FRONT_SUBST,
         OLD_BLOCKS.replace("Fifth trim", "F1fth trim", 1), NEW_TABLE, pre_live, world),
        ("M2  declared substitution 3 not applied (stale 'the older five are untouched')",
         before, after.replace(FRONT_SUBST[2][1], FRONT_SUBST[2][0], 1), live_wt, ROWS,
         FRONT_SUBST, OLD_BLOCKS, NEW_TABLE, pre_live, world),
        ("M3  an UNDECLARED extra front-matter edit alongside the declared ones",
         before, after.replace("`grep` the shards; `Read` none.",
                               "`grep` the shards; `Read` nothing.", 1), live_wt, ROWS,
         FRONT_SUBST, OLD_BLOCKS, NEW_TABLE, pre_live, world),
        ("M4  a substitution's anchor absent from `before` (declaration gone stale)",
         before.replace(FRONT_SUBST[1][0], "REPLACED BY AN EARLIER EDIT\n", 1), after, live_wt,
         ROWS, FRONT_SUBST, OLD_BLOCKS, NEW_TABLE, pre_live, world),
        ("M5  the table dropped from the post-collapse front matter",
         before, after.replace(NEW_TABLE, "", 1), live_wt, ROWS, FRONT_SUBST, OLD_BLOCKS,
         NEW_TABLE, pre_live, world),
        ("M6  one character flipped inside a retained record",
         before, after.replace(a_rec, a_rec.replace("e", "3", 1), 1), live_wt, ROWS, FRONT_SUBST,
         OLD_BLOCKS, NEW_TABLE, pre_live, world),
        ("M7  a record deleted by the collapse commit",
         before, after.replace(ar[1], "", 1), live_wt, ROWS, FRONT_SUBST, OLD_BLOCKS, NEW_TABLE,
         pre_live, world),
        ("M8  a record ADDED by the collapse commit (bundled record edit)",
         before, after + ar[0], live_wt, ROWS, FRONT_SUBST, OLD_BLOCKS, NEW_TABLE, pre_live, world),
        ("M9  a row's heading count typed rather than measured",
         before, after, live_wt, rows_m9, FRONT_SUBST, OLD_BLOCKS, NEW_TABLE, pre_live, world),
        ("M10 a row's archived line count off by one",
         before, after, live_wt, rows_m10, FRONT_SUBST, OLD_BLOCKS, NEW_TABLE, pre_live, world),
        ("M11 a row's shard total off by one",
         before, after, live_wt, rows_m11, FRONT_SUBST, OLD_BLOCKS, NEW_TABLE, pre_live, world),
        ("M12 the TABLE's own figure edited away from the measurement",
         before, after, live_wt, ROWS, FRONT_SUBST, OLD_BLOCKS, table_typo, pre_live, world),
        ("M13 a row names the wrong trim commit",
         before, after, live_wt, rows_m13, FRONT_SUBST, OLD_BLOCKS, NEW_TABLE, pre_live, world),
        ("M14 a row's 'left live' span wrong (blind to C3, which reads sizes)",
         before, after, live_wt, rows_m14, FRONT_SUBST, OLD_BLOCKS, NEW_TABLE, pre_live, world),
        ("M15 a row credits the wrong assertions to its trim",
         before, after, live_wt, rows_m15, FRONT_SUBST, OLD_BLOCKS, NEW_TABLE, pre_live, world),
        ("M16 the table absent from the WORKING TREE (committed, then reverted on disk)",
         before, after, (live_wt.replace(NEW_TABLE, "", 1) if live_wt is not MISSING else live_wt),
         ROWS, FRONT_SUBST, OLD_BLOCKS, NEW_TABLE, pre_live, world),
        ("M17 the collapse declared but NOT applied to the working tree",
         before, after,
         (live_wt.replace(NEW_TABLE, OLD_BLOCKS, 1) if live_wt is not MISSING else live_wt),
         ROWS, FRONT_SUBST, OLD_BLOCKS, NEW_TABLE, pre_live, world),
        ("M18 an ancestor shard EDITED after its own add-commit (C3/C4 read the commit, not disk)",
         before, after, live_wt, ROWS, FRONT_SUBST, OLD_BLOCKS, NEW_TABLE, pre_live,
         W(lambda k, v: {"shard": (v["shard"] + "\ntrailing\n") if k == ROWS[1][6] else v["shard"]})),
        ("M19 an ancestor PROOF weakened at its add-commit (an assertion deleted)",
         before, after, live_wt, ROWS, FRONT_SUBST, OLD_BLOCKS, NEW_TABLE, pre_live,
         W(lambda k, v: {"proof": (v["proof"].replace("\ndef L9(", "\ndef _L9(", 1))
                         if k == ROWS[3][6] else v["proof"]})),
        ("M20 the declared PRE commit does not hold the removed prose",
         before, after, live_wt, ROWS, FRONT_SUBST, OLD_BLOCKS, NEW_TABLE,
         (pre_live.replace(OLD_BLOCKS, "", 1) if pre_live else pre_live), world),
        # --- C4 and C3/ROW were SHADOWED until these five. C3 composes its row line from the
        # --- declared sha/span/live, so mutating a DECLARATION trips C3 too and C4 caught nothing
        # --- alone. These mutate the WORLD (what git reports) instead, which C3's measurements
        # --- survive: exactly the shape Session 224's L2/b0 and Session 228's L5/2 both missed.
        ("M21 git reports a different commit as the one that ADDED a shard (C4/PROVENANCE alone)",
         before, after, live_wt, ROWS, FRONT_SUBST, OLD_BLOCKS, NEW_TABLE, pre_live,
         W(lambda k, v: {"addsha": "0badc0de" + v["addsha"][8:]
                         if k == ROWS[2][6] else v["addsha"]})),
        ("M22 a shard holds a different session span, same size (C4/SPAN alone)",
         before, after, live_wt, ROWS, FRONT_SUBST, OLD_BLOCKS, NEW_TABLE, pre_live,
         W(lambda k, v: {"shard": v["shard"].replace("### What Session 220 Did",
                                                     "### What Session 209 Did", 1)
                         if k == ROWS[1][6] else v["shard"]})),
        ("M23 the live file held a different span at that trim commit (C4/LEFT-LIVE alone)",
         before, after, live_wt, ROWS, FRONT_SUBST, OLD_BLOCKS, NEW_TABLE, pre_live,
         W(lambda k, v: {"live": v["live"].replace("### What Session 231 Did",
                                                   "### What Session 199 Did", 1)
                         if k == ROWS[3][6] else v["live"]})),
        ("M24 a shard the table routes readers to is GONE from disk (C4/GONE alone)",
         before, after, live_wt, ROWS, FRONT_SUBST, OLD_BLOCKS, NEW_TABLE, pre_live,
         W(lambda k, v: {"shard_disk": MISSING if k == ROWS[4][6] else v["shard_disk"]})),
        ("M25 a row's ordinal wrong -- read by nothing but the composed line (C3/ROW alone)",
         before, after, live_wt, rows_m25, FRONT_SUBST, OLD_BLOCKS, NEW_TABLE, pre_live, world),
        # --- ten more, one per ARM the neuter sweep found unreachable. Each targets a single
        # --- failure-emitting statement; the residual six are documented in the header as
        # --- genuinely subsumed (a better message ahead of a guaranteed-firing sibling).
        ("M26 the DECLARED removed-line count wrong while the text is right (C0/SIZE alone)",
         before, after, live_wt, ROWS, FRONT_SUBST, OLD_BLOCKS, NEW_TABLE, pre_live, world,
         {"declared_lines": 175}),
        ("M27 the removed text occurs TWICE in `before`, `after` rebuilt (C1/b0 ANCHOR alone)",
         dup_blocks, rebuilt(dup_blocks), live_wt, ROWS, FRONT_SUBST, OLD_BLOCKS, NEW_TABLE,
         pre_live, world, {}),
        ("M28 substitution 1's anchor occurs TWICE, `after` rebuilt (C1/b0 SUBST alone)",
         dup_subst, rebuilt(dup_subst), live_wt, ROWS, FRONT_SUBST, OLD_BLOCKS, NEW_TABLE,
         pre_live, world, {}),
        ("M29 a shard unreadable at its own add-commit (C3 guard)",
         before, after, live_wt, ROWS, FRONT_SUBST, OLD_BLOCKS, NEW_TABLE, pre_live,
         W(lambda k, v: {"shard": None if k == ROWS[0][6] else v["shard"]}), {}),
        ("M30 git knows no commit that ADDED a shard (C4 guard)",
         before, after, live_wt, ROWS, FRONT_SUBST, OLD_BLOCKS, NEW_TABLE, pre_live,
         W(lambda k, v: {"addsha": "" if k == ROWS[1][6] else v["addsha"]}), {}),
        ("M31 the live file unreadable at a trim commit (C4/LEFT-LIVE guard)",
         before, after, live_wt, ROWS, FRONT_SUBST, OLD_BLOCKS, NEW_TABLE, pre_live,
         W(lambda k, v: {"live": None if k == ROWS[2][6] else v["live"]}), {}),
        ("M32 an ancestor proof unreadable at its add-commit (C5 guard)",
         before, after, live_wt, ROWS, FRONT_SUBST, OLD_BLOCKS, NEW_TABLE, pre_live,
         W(lambda k, v: {"proof": None if k == ROWS[4][6] else v["proof"]}), {}),
        ("M33 an ancestor proof that defines no assertions at all (C5 grammar guard)",
         before, after, live_wt, ROWS, FRONT_SUBST, OLD_BLOCKS, NEW_TABLE, pre_live,
         W(lambda k, v: {"proof": "# emptied\n" if k == ROWS[0][6] else v["proof"]}), {}),
        ("M34 SESSION_NOTES.md gone from the working tree entirely (C6 guard)",
         before, after, MISSING, ROWS, FRONT_SUBST, OLD_BLOCKS, NEW_TABLE, pre_live, world, {}),
        ("M36 the declared PRE commit does not hold SESSION_NOTES.md at all (C0 guard)",
         before, after, live_wt, ROWS, FRONT_SUBST, OLD_BLOCKS, NEW_TABLE, None, world, {}),
        ("M35 the table AND the collapsed prose both present on disk (C6 second arm alone)",
         before, after, (live_wt + OLD_BLOCKS) if live_wt is not MISSING else live_wt,
         ROWS, FRONT_SUBST, OLD_BLOCKS, NEW_TABLE, pre_live, world, {}),
        # --- seven more, every one of them found by an adversarial review of a GREEN, self-tested,
        # --- twice-swept proof. That is the third time this lineage has measured a review beating
        # --- the author's own sweeps (PROJECT_LEARNINGS #178), and the lenses that paid were again
        # --- the ones aimed at what the PROSE claims, not at the bytes.
        ("M37 the trim's session number wrong (C3/SESSION -- derived from the live file, not typed)",
         before, after, live_wt, rows_m37, FRONT_SUBST, OLD_BLOCKS, NEW_TABLE, pre_live, world, {}),
        ("M38 an UNDECLARED sixth row naming a shard that does not exist (C3/SET)",
         before, a_extra, l_extra, ROWS, FRONT_SUBST, OLD_BLOCKS, t_extra, pre_live, world, {}),
        ("M39 the table's own '176 lines' moved away from the derived count (C0/FIGURE)",
         before, a_176, l_176, ROWS, FRONT_SUBST, OLD_BLOCKS, t_176, pre_live, world, {}),
        ("M40 the table names a different pinned commit than PRE (C0/FIGURE)",
         before, a_pre, l_pre, ROWS, FRONT_SUBST, OLD_BLOCKS, t_pre, pre_live, world, {}),
        ("M41 the table stops spelling its own row count (C3/FIGURE)",
         before, a_five, l_five, ROWS, FRONT_SUBST, OLD_BLOCKS, t_five, pre_live, world, {}),
        ("M42 a positional 'N blocks below' claim falsified and NOT declared (C7)",
         before, after_c7, live_wt, ROWS, FRONT_SUBST, OLD_BLOCKS, NEW_TABLE, pre_live, world, {}),
        ("M44 a positional claim false in BOTH before and after -- C1 satisfied, C7 alone objects",
         b_c7, a_c7, live_wt, ROWS, FRONT_SUBST, OLD_BLOCKS, NEW_TABLE, pre_live, world, {}),
        # --- two arms lost their unique mutants to arms added in the SAME revision, which is the
        # --- shape the seventh trim named (L12/absent and L13/absent losing theirs to their own
        # --- new siblings). C3/SESSION reads ids[0] of the same blob C4/LEFT-LIVE reads, so M23
        # --- and M31 stopped being C4's alone; M45 moves the OLDEST id, which C3/SESSION cannot see.
        ("M45 the live file's OLDEST retained id differs at a trim commit (C4/LEFT-LIVE alone)",
         before, after, live_wt, ROWS, FRONT_SUBST, OLD_BLOCKS, NEW_TABLE, pre_live,
         W(lambda k, v: {"live": v["live"].replace("### What Session 217 Did",
                                                   "### What Session 117 Did", 1)
                         if k == ROWS[0][6] else v["live"]}), {}),
        ("M46 a positional claim whose count word is not a number at all (C7 grammar guard)",
         before,
         after.replace("**The block below is frozen at the SIXTH trim",
                       "**The umpteen blocks below are frozen at the SIXTH trim", 1),
         live_wt, ROWS, FRONT_SUBST, OLD_BLOCKS, NEW_TABLE, pre_live, world, {}),
        ("M43 one table ROW reverted on disk while the commit keeps it (C6 per-row)",
         before, after,
         (live_wt.replace("| 3 | S228", "| 3 | S288", 1) if live_wt is not MISSING else live_wt),
         ROWS, FRONT_SUBST, OLD_BLOCKS, NEW_TABLE, pre_live, world, {}),
    ]
    mutants = [m if len(m) == 11 else m + ({},) for m in mutants]
    bad = []
    for name, b, a, lw, rows, sub, ob, nt, pl, wd, opt in mutants:
        fails = check(b, a, lw, rows, sub, ob, nt, pl, wd, **opt)
        if not fails:
            bad.append(name)
            print("  SURVIVED  %s" % name)
        else:
            codes = sorted({f.split(":")[0].split(" (")[0] for f in fails})
            print("  caught    %-72s -> %s" % (name, ", ".join(codes)))
    if bad:
        print("\nSELF-TEST FAILED: %d mutant(s) survived. This proof cannot be trusted." % len(bad))
        sys.exit(2)
    print("\nSELF-TEST OK: all %d mutants caught." % len(mutants))


before, after, live_wt, pre_live, source, note = artifacts()
if before is None or after is None:
    sys.exit("cannot read %s from git" % LIVE)
world = gather(ROWS)

if "--self-test" in sys.argv:
    print("--self-test: mutating the artifacts AND the declarations, asserting each is caught.\n")
    self_test(before, after, live_wt, pre_live, world)
    sys.exit(0)

fails = check(before, after, live_wt, ROWS, FRONT_SUBST, OLD_BLOCKS, NEW_TABLE, pre_live, world)
_bf, br = zones(before)
_af, ar = zones(after)

print("source : %s" % source)
if note:
    print("WARNING: %s" % note)
print("scope  : a COLLAPSE, not a trim -- 0 records moved, 0 shards written, 0 sessions archived")
print("removed: %d lines of pointer prose, embedded verbatim in this file and pinned to %s"
      % (DECLARED_OLD_LINES, PRE))
print("added  : a %d-line table; front matter %d -> %d lines"
      % (NEW_TABLE.count("\n"), _bf.count("\n"), _af.count("\n")))
print("records: %d before, %d after; added by the collapse commit: %d"
      % (len(br), len(ar), max(0, len(ar) - len(br))))
print("rows   : %d trims, every figure measured from its shard at its own add-commit and the row "
      "line COMPOSED\n         from the measurements" % len(ROWS))
print("front  : one collapse + %d declared substitutions, all checked by exact equality"
      % len(FRONT_SUBST))
print("checked: C0, C1, C2, C3, C4, C5, C6, C7  <- C6 reads the WORKING-TREE prose; the L-series\n"
      "         reads prose only at its own trim commit (it does read shards and proofs from disk)")

if fails:
    print("\nFAIL:")
    for f in fails:
        print("  " + f)
    sys.exit(1)

print("\nOK: C0-C7 hold.")
print("    The 176 lines this collapse removed are still readable, byte-for-byte, at %s and in" % PRE)
print("    this file; the front matter changed by exactly that one replacement plus %d declared"
      % len(FRONT_SUBST))
print("    substitutions and nothing else; not one record was touched; and every figure in the")
print("    table was measured from the shard it describes, at that shard's own add-commit, with")
print("    the row's markdown line composed from the measurement rather than compared to it.")
print("    It says NOTHING about whether collapsing was wise -- that was the operator's call --")
print("    nor whether the surviving prose is true. It does not re-prove any of the eight cuts:")
print("    each has its own proof pinned to its own commit. Run those eight as well.")
print("    A green proof that has never been --self-test'ed proves less than it appears to.")

PYEOF
