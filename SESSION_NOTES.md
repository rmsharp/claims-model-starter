# Session Notes

**Purpose:** Continuity between sessions. Each session reads this first and writes to it before closing out.

**Third trim (Session 228). Archived Sessions 224 → 221 — 4 record headings, 891 lines** into
[`docs/architecture-history/SESSION_NOTES-S224-through-S221.md`](docs/architecture-history/SESSION_NOTES-S224-through-S221.md)
— same shape, same newest-on-top order, frozen and byte-for-byte unedited. **This live file now
holds Sessions 228 → 225 only** — four sessions, the floor `CLAUDE.md` sets. Its proof is
[`SESSION_NOTES-S224-through-S221.md.verify.sh`](docs/architecture-history/SESSION_NOTES-S224-through-S221.md.verify.sh):
the five inherited assertions plus **L5** (the table below, clause by clause — the numbers against
the cut key, the filenames against what those files actually hold), **L6** (the shard's banner
pinned byte-for-byte) and **L7** (that shard still being, on disk today, the bytes the proof was
written about — the only enforcement `write-once` has ever had).

**Three shards exist now, and none is a prefix of any other.** To place Session N, open the file
this table names. **This block is the authority**, and these four clauses are machine-checked here,
in the shard's banner, and in `CLAUDE.md`:

**N ≤ 216** → `SESSION_NOTES-through-S216.md`; **217 ≤ N ≤ 220** → `SESSION_NOTES-S220-through-S217.md`;
**221 ≤ N ≤ 224** → `SESSION_NOTES-S224-through-S221.md`; **N ≥ 225** → `SESSION_NOTES.md`.

`grep` the shards; `Read` none of them. **Shards stay write-once** — a fourth trim writes a fourth
file; it never appends to one of these three.

**A copy of that table inside a write-once file goes stale at the next cut and cannot be repaired.**
The S220 shard's banner still says *"the live ledger when N ≥ 221"*, which this trim falsified; its
proof predates L5 and will never notice. Treat every shard banner as a snapshot of its own cut. Two
further copies live outside every proof — `README.md`'s repo map and the shard-naming rule in
`docs/methodology/PROJECT_CONVENTIONS.md` — and a trim that leaves either one alone ships a lie.

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

### What Session 230 Did
**Deliverable:** Repair `docs/planning/repository-rename.md` — the six items in `BACKLOG.md`'s
"⚠⚠ Two defects in `repository-rename.md` ITSELF" block, and ONLY that. **NOT Phase 3.** (IN PROGRESS)
**Started:** 2026-08-20
**Status:** Session claimed. Work beginning.

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

### What Session 227 Did
**Deliverable:** **Phase 1 of [`docs/planning/repository-rename.md`](docs/planning/repository-rename.md)
— COMPLETE.** The GitHub repository is now **`rmsharp/model_project_constructor`**, and the published
tutorial site was repaired in the same session and the immediately following push, exactly as K1
requires. Every verification command in the plan's Phase 1 block was run and every one is green.

**Commits:** `6d2a617` (operator ruling on D-R1..D-R5 + Phase 1B claim — **its own commit, fires
nothing**), `c1fe06f` (the four-file site repair — the commit that deploys), and this close-out.
Pushed `2070547..6d2a617` then `6d2a617..c1fe06f`; `origin/master` is at parity.

**Operator this session:** *"accept the 404, go with option A; accept all recommendations for D-R2,
D-R3, D-R4, and D-R5."* Recorded verbatim in the plan's §4 because D-R1 is the only irreversible act
in the plan and that sentence is the whole authorization for it.

#### The irreversible act, and the measurement that makes it interpretable

**The old Pages URL is dead, permanently, and it was measured at the moment it died.** The plan's
central finding is now confirmed **on this repository**, not merely on the two analogue renames
S226 measured:

| Surface | Before | After | Header |
| --- | --- | --- | --- |
| `github.com/rmsharp/claims-model-starter` | 200 | **301** | `Location: …/rmsharp/model_project_constructor` |
| `rmsharp.github.io/claims-model-starter/tutorial/` | 200 | **404** | **no `Location` header at all** |
| `rmsharp.github.io/model_project_constructor/tutorial/` | 404 | **200** | — |

Same host, same rename, same instant: the repo URL forwards and the Pages URL does not. That is §1
happening as designed. **Do not "fix" the 404** — a second rename has the same consequence and also
breaks the redirect chain that 552 lines of historical record depend on.

**`gh repo rename` rewrote `origin` by itself.** The plan hedged (*"gh may rewrite origin; CONFIRM,
do not assume"*). It does: `git remote -v` reported the new URL with no `set-url` needed. Hedge
resolved to a measured fact; the next executor can skip that branch.

#### What actually shipped

`c1fe06f` — **three files, four changes**, not the "exactly four files" the plan says (see defects
below):

| File | Lines | What |
| --- | --- | --- |
| `mkdocs.yml` | `:3`,`:4`,`:5` | `site_url` / `repo_url` / `repo_name` — deploy trigger |
| `README.md` | `:9` | the advertised tutorial URL |
| `README.md` | `:7` | **rewritten, not substituted** (dragon 6) |
| `docs/tutorial.md` | `:218` | wiki page URL — also a deploy trigger |

`README.md:7` existed to explain a naming divergence, and the rename changed *which* divergence
there is. I verified all three naming facts first-hand before writing the replacement rather than
copying the plan's table: `pyproject.toml:2` = `model-project-constructor`, `src/model_project_constructor/`,
`packages/data-agent/pyproject.toml:2` = `model-project-constructor-data-agent`. The sentence now
says the repository, source tree and import package agree, and only the PyPI distribution names keep
hyphens — which is PEP 503 normalization, not an anomaly. **Do not "fix" those hyphens.**

#### Verification — all green, with the two that could have lied

- **Both deploy stages ran** (dragon 5: a green `publish-tutorial` run proves only half).
  `publish-tutorial.yml` run `32335373755`, success, 15s. Legacy `pages/builds/latest` →
  `status: "built"`, commit `cc66dea`, `2026-08-20T05:23:20Z` — newer than the pre-rename `1b9ce68`.
- **`gh-pages` was force-replaced**, `1b9ce68...cc66dea (forced update)`, deployed from `c1fe06f`.
  It is parentless (`rev-list --count` = 1), so **there is no ordinary revert**. The pre-deploy state
  is bundled at **`~/gh-pages-pre-rename.bundle`** (29 KB, `git bundle verify` → "records a complete
  history") and also at local branch `gh-pages-pre-rename`.
- **Sitemap clean in BOTH forms** (gotcha 4 — `git grep` cannot read the `.gz`): `sitemap.xml` → 0
  old-name hits, `sitemap.xml.gz` → 0. It now advertises exactly two URLs, both new.
- **All 7 deployed blobs clean**, `.gz` decompressed per §7.4 check 1.
- **The §7.2 allowlist went 20 → 17, verified by set difference, not by count.** Exactly
  `README.md`, `mkdocs.yml`, `docs/tutorial.md` left; **nothing appeared**. (Pre-execution it printed
  exactly the 20 paths the plan lists — no drift, so §2 did not need re-deriving.)
- **The stylesheet is still 404, and that is NOT rename damage.** Baseline recorded before the rename:
  `page=200 css=404`. After: identical. The deployed tree has no `assets/` directory at all — dragon
  10, pre-existing, filed in §8.1, deliberately not fixed here.
- `uv run pytest -q` → **1230 passed, 9 skipped**, coverage 97.98% — exactly the plan's prediction.
  `ruff` clean; `mypy` clean across 68 source files.
- Both clones still fetch: this repo on the new remote, the wiki clone **over its stale remote via
  redirect** — which is correct, K2 keeps it stale until Phase 4.
- **The ruling commit fired nothing**, confirming dragon 5's claim that `docs/*.md` is a *single-level*
  trigger: `docs/planning/repository-rename.md` changed and no run appeared.

#### Three defects found in the plan while executing it — none fixed, all filed here

1. **"Exactly four files" is three files, four changes.** `mkdocs.yml`, `README.md` (twice),
   `docs/tutorial.md`. Cosmetic, but an executor who counts files will hunt for a fourth.
2. **§7.4 check 3 has no owning phase for the third clone.** It requires all three clones' origins to
   carry the new name, and dragon 9 names `~/Development/mpc_tests/model_project_constructor`
   *specifically so it would not be forgotten*. Phase 4 step 1 re-points **only** the wiki clone;
   nothing re-points that one. **It is still on the old URL today** (works via redirect). This is
   learning **#111** and it needs a home in Phase 4 or 5.
3. Step 0's *"master is 2 commits ahead"* was 4 by execution time — expected drift, the plan pins
   everything to `59615e2` and says so. Noted only so nobody reads it as an error.

### Session 226 Handoff Evaluation (by Session 227)

**Score: 9/10.** The highest this project has scored a handoff, and it earned it on the hardest kind
of session to hand off: one whose central act cannot be undone. Execution was close to mechanical —
**zero surprises, zero stakeholder corrections, and not one load-bearing claim failed under test.**

**What helped, concretely — every one of these changed what I did:**
- **Gotcha 5 ("record the baseline before Phase 1").** This is the single highest-value line in the
  handoff. The stylesheet is 404 *after* the rename, and without the pre-measurement I had exactly
  two honest readings available — "the irreversible act broke it" and "assume it was already
  broken" — on the one commit where the first is unrecoverable. The baseline turned that into
  arithmetic. Now learning #110.
- **Gotcha 1 ("re-run the allowlist before touching anything; it must print exactly 20").** It did.
  That one command licensed everything downstream, because it proved the plan had not drifted.
- **Dragon 5's third workflow.** I would have checked `publish-tutorial.yml`, seen green, and stopped
  at half the pipeline. The `pages/builds/latest` call is the other half and it is not discoverable
  from `.github/workflows/`.
- **Gotcha 4 (`git grep` cannot read `sitemap.xml.gz`).** Both forms checked; both 0.
- **The parentless-`gh-pages` warning + the bundle recipe.** `rev-list --count` = 1 confirmed it, and
  the forced update landed exactly as described. The backup existed *before* the deploy, not after.
- **Gotcha 8 ("this is still zsh; single-quote your heredoc delimiters").** Every heredoc this session
  used `<<'PYEOF'` / `<<'MSGEOF'`. **Zero** quoting round-trips, fourth session running.
- **Gotcha 9 ("no phase earns a CHANGELOG entry")** — settled in advance, so a decision that could
  have written a permanent wrong entry into an append-only ledger never had to be made under time
  pressure with the site down.
- **Dragon 6.** A `sed` here would have shipped a sentence whose only remaining content was an
  unexplained hyphen/underscore difference. The handoff named it *and* named the replacement's shape.

**What was wrong or missing — two things, one real:**
1. **§7.4 check 3 is orphaned** (defect 2 above). The plan states a criterion, names the surface in a
   dragon so it "would not be forgotten", and then assigns it to no phase. Naming a hazard is not
   scheduling its fix. This is the one deduction that matters.
2. **"Exactly four files"** is three. Cosmetic.

**ROI:** overwhelmingly positive. The plan cost one session to write; it made an irreversible,
multi-surface change take one session with no rework, no false alarms, and a defensible record of
what was destroyed on purpose.

### Session 227 Self-Assessment

**Score: 8.5/10.**

**+** Ran the drift check **before touching anything**, and verified the criterion's movement by
**set difference in both directions** rather than by count — 20 → 17 is also consistent with four
repaired and one newly broken. Learning #109.
**+** Measured the irreversible consequence at the instant it happened, and captured the fact that
makes it interpretable: the old repo URL 301s **with** a `Location` header while the old Pages URL
404s **without** one. A bare pair of status codes would have proved much less.
**+** Verified the three naming facts first-hand (`pyproject.toml`, `src/`, `packages/`) before
rewriting `README.md:7`, instead of transcribing the plan's table — FM #11 applied to a plan's own
evidence, not just to my memory.
**+** Resolved a hedge into a fact rather than leaving it hedged: `gh repo rename` **does** rewrite
`origin`.
**+** **Held scope.** Found the orphaned third clone and did **not** re-point it — one
`git remote set-url` away, entirely safe, and out of Phase 1's scope. Filed it instead.
**+** Kept the ruling/claim commit and the deploying commit separate, so the parentless deploy is
bisectable to a three-file change.

**−** **I did not run `mkdocs build --strict` locally before pushing the commit that triggers a
forced, parentless, non-revertible deploy.** I validated that `mkdocs.yml` *parses* and that its three
values were right — which is strictly weaker than proving the site builds. It worked; that is luck
standing in for a check, on the one commit in the whole plan where being wrong is expensive.
**−** My first `comm` ran on **unsorted input**. It printed the right three files and warned. On
differently-ordered input it would have been silently wrong, and I would have shipped an unverified
delta as a verified one. I re-ran it sorted, both directions — but I should not have needed the
warning to notice.
**−** I read the plan's Phase 1 block, its dragons and its §7 — but I did not walk §7 *backwards
against the phases* until after the work was done, which is how the orphaned clone surfaced late.
Ten minutes at the start would have found it before the first command, not after the last.

**Against the bar:** S226 shipped a plan whose finding reversed the task's premise; S225 shipped a
12-mutant matrix. This session shipped the execution that plan called for, with every prediction
tested rather than assumed, three defects found *in the plan* while following it, and the one
irreversible act in the project's history documented with before/after measurements on both sides.
Comparable in rigour, smaller in invention — which is what an execution phase should be.

**What's next: Phase 2 of `docs/planning/repository-rename.md`, and ONLY Phase 2.** It is the
cheapest phase in the plan and deliberately so: it touches **no** file on `publish-tutorial.yml`'s
trigger list and **no** file under `docs/wiki/`, so it fires neither the deploy nor the wiki hook.
Scope: `SECURITY.md:9`, `CONTRIBUTING.md:6`, and eleven lines of
`docs/planning/enterprise-migration.md` — the five `curl` criteria that the rename has turned into
**vacuous passes** (add `-fL` while there), the two "unchanged" assertions at `:1311`/`:1358`, the
independence pattern at `:363`/`:1308`/`:1351`, and the reword of dragon #21 at `:1436-1439`, whose
verbatim *"Do NOT ... re-remote `~/Development/claims-model-starter.wiki`"* forbids the exact action
Phase 4 requires. Reword it; do not delete it — it is still a live warning about the **enterprise**
wiki.

**⚠ But read this first: the trim trigger has fired.** `SESSION_NOTES.md` now exceeds the 1,500-line
threshold in `CLAUDE.md`. That is a **judgment call with hysteresis**, and it is the operator's to
make: a trim is its own deliverable and its own session (three separate commits — claim, trim,
close-out — and the trim commit must contain **no** record edit). Do **not** bundle it with Phase 2.

**Key files:**
- **`docs/planning/repository-rename.md`** — §4 now carries the operator's ruling verbatim and is
  **closed**. Phase 2 is at `:528-600`. §7.2's allowlist is at `:1097` and currently prints **17**.
- `~/gh-pages-pre-rename.bundle` + local branch `gh-pages-pre-rename` — the only copy of the
  pre-rename deployed site. `gh-pages` is parentless; this bundle *is* the undo.
- `docs/planning/enterprise-migration.md` — Phase 2's real work; eleven lines across six sites.
- `.githooks/post-commit:18` — untouched, still the one **fail-open** line in the system. It does not
  bite until Phase 4, but it is the hazard that ends the plan badly if it is forgotten.
- `scripts/publish_wiki.sh` — untouched. `:101` already emits the NEW name; **do not "fix" it.**
- `tests/test_wiki_no_line_citations.py:38` — `WIKI_DIR` is built from path **parts**, so a
  path-pattern grep cannot see it. Phase 4 territory, and the single line whose omission reddens the
  suite.

**Gotchas:**
1. **The old Pages URL 404s forever. That is the plan working, not a defect.** Anyone who "fixes" it
   by renaming back destroys the redirect chain 552 lines of history depend on, and does **not** get
   the URL back.
2. **The published tutorial is still unstyled** — page 200, stylesheet 404, identical before and
   after the rename. Pre-existing (no `assets/` tree on `gh-pages` at all). Filed in §8.1. Do not
   attribute it to the rename, and do not fix it inside a rename phase.
3. **`~/Development/mpc_tests/model_project_constructor` is still on the old origin URL** and **no
   phase owns it.** Give it a home in Phase 4 step 1 alongside the wiki clone's `set-url`.
4. **The wiki clone's stale origin is deliberate** (K2) — it must stay stale until Phase 4 changes it
   in the same breath as `publish_wiki.sh:72`'s guard literal. It fetches fine via redirect.
5. **Every phase stays on a direct commit to `master`.** The hook is blind to merge commits.
6. **This is still zsh.** Single-quote every heredoc delimiter. Fifth session running, still free.
7. **Do not `mkdir` the wiki destination in Phase 4.** `git mv` only — an empty-but-existing
   `SOURCE_DIR` passes all five guards and `rsync -a --delete` then wipes and **pushes** the live
   public wiki.
8. **Before Phase 2, walk §7 backwards against the phases** and name the phase+step that makes each
   criterion green. That walk is what found defect 2 here, and it found it too late.

### What Session 226 Did
**Deliverable:** **`docs/planning/repository-rename.md` — the PLAN for renaming
`rmsharp/claims-model-starter` -> `model_project_constructor`. COMPLETE.** 1,120 lines: a freshly
re-derived inventory pinned to a commit, a per-file change/keep classification, **five** operator
decisions, five one-session phases with falsifiable per-phase criteria, and **twelve dragons**.

**Nothing was renamed.** No `gh repo rename`, no `git mv`, no reference rewritten, no remote
re-pointed. `git status` at close-out shows only this file, `PROJECT_LEARNINGS.md`, and the plan.

**Started / completed:** 2026-08-19. **Commits:** `59615e2` (Phase 1B claim, its own commit),
`ef9c8e9` (plan checkpoint), and this close-out.

**Operator this session:** *"rename repository ; use planning session if needed."* The "if needed"
was answered by evidence, and the evidence went the other way from the filed estimate: the sweep is
**smaller** than filed (114 lines, not 667) and the **consequences are larger** (one is permanent).

#### The headline: renaming this repository permanently kills its published tutorial URL

**GitHub does not redirect GitHub Pages project-site URLs after a repository rename.** It redirects
the repo URL, `git clone`/`fetch`/`push`, issues, **the wiki**, stars and followers — Pages is the
single documented exception. Two GitHub docs pages say so, quoted verbatim in §1 of the plan.
`gh api repos/.../pages` confirms `cname: null`, so the one mitigation GitHub recommends (a custom
domain) is absent here.

So `https://rmsharp.github.io/claims-model-starter/tutorial/` — the URL advertised at `README.md:9`,
this project's only public tutorial link — **404s forever the moment the rename lands.** That
collides with `enterprise-migration.md:549`'s **decision D6**, answered by the operator 2026-07-27:
*"refresh and keep public, indefinitely."*

**This was not in the filed backlog item**, whose dragon 5 said the redirect "softens but does not
remove the break." For the Pages URL there is no redirect to soften anything. It is now **operator
decision D-R1** with three costed options; §1.1 also evaluates and **rejects** the obvious rescue
(park a stub repo at the old name) because GitHub's docs say reusing the old name destroys **every
other** redirect — and 552 lines of this repository's historical record depend on those.

#### The inventory: both filed counts were wrong, and mine is pinned to a commit

| Source | Claimed | Actual | Verdict |
| --- | --- | --- | --- |
| `BACKLOG.md` table (S221, `5d906e9`) | 644 / 50 | 659 / 50 | already known stale |
| **Ruling commit `2033e95` (S225)** | **667 / 52** | **665 / 51** | **not reproducible at ANY commit by ANY method** |
| This session, pinned at `59615e2` | **666 / 51** | 666 / 51 | reproducible: `git grep -c "claims-model-starter" 59615e2 -- .` |

I tried matching lines, raw occurrences, working-tree grep, untracked-inclusive grep, and all
fourteen commits from `5d906e9` to `HEAD`. **667/52 exists nowhere.** The paragraph that produced it
was itself a warning not to inherit stale numbers — see learning **#105**.

**The useful number is neither 666 nor 667. It is 114.** Split, with arithmetic that reconciles both
ways: **114 lines / 23 files change; 552 lines / 28 files keep** (114+552 = 666; 23+28 = 51). Of the
114, only **51** depend on the wiki-directory decision, and **~42** of those are real edits.

#### Four things nobody had found, each verified first-hand

1. **`.githooks/post-commit:18` is the one FAIL-OPEN mechanism in the whole system** (dragon 4). Every
   other guard exits 1 loudly; this one `exit 0`s in silence. Rename the wiki directory and leave its
   `grep '^docs/wiki/claims-model-starter/'` prefix stale, and every future wiki edit silently never
   publishes. The rename commit itself still fires (a rename shows as both paths in `diff-tree` —
   verified against `35ccbd9`), so you get **one reassuring success** and the failure starts on the
   *next* wiki edit, in a different session. **And it has already happened here:** merge `ff04c02`
   changed five wiki pages and `git diff-tree --no-commit-id --name-only -r` returned **0 lines**
   (with `-m`: 5) — the hook published nothing and said nothing.
2. **`publish_wiki.sh` can wipe and push the live public wiki** (dragon 3). Its five guards are
   *existence* checks; nothing inspects `SOURCE_DIR`'s contents, and `:92` is
   `rsync -a --delete`. An empty-but-existing source directory passes every guard, deletes all 25
   pages, commits, and pushes. `git mv` never produces that state — but `man git-mv`'s single-source
   form refuses an existing destination, so an executor who hits that error reaches for
   `mkdir` + multi-source, which does. The plan makes "never `mkdir` the destination" an absolute rule.
3. **The string is overloaded** (dragon 7). Three live wiki lines say *"generated claims-model-starter
   projects"*, meaning the pipeline's **output**, not this repository. A blind replace renames a
   different concept. The label is already false: `src/` and `packages/` contain **zero** occurrences,
   and generated names come from `derive_project_name`/`derive_project_slug` at runtime.
4. **The published tutorial site is already broken** (dragon 10). `origin/gh-pages` holds 7 files and
   **no `assets/` tree**, while `tutorial/index.html` links `../assets/stylesheets/main.*.css`.
   Measured live: page **200**, stylesheet **404**. Pre-dates the rename — so `curl -> 200` cannot
   detect a broken deploy, and the executor must not read the 404 as rename damage. Filed as
   out-of-scope (§8.1), not fixed.

#### The cross-plan collision is worse than "five URLs need updating"

`docs/planning/enterprise-migration.md` is mid-execution and the rename **inverts three of its
assertions into vacuous passes** (dragon 1). Phase A1's containment proof is three `curl`s expecting
**404** from `rmsharp.github.io/claims-model-starter/...`; after the rename the whole host path 404s,
so all three pass **while proving nothing**. A fourth (`:1356`) expects **200** and flips to a loud
false failure.

Two more, both found by the fan-out and verified by me:
- **`:1311` and `:1358`** assert the wiki clone's origin is *"unchanged"* — which Phase 4 changes.
- **Dragon #21 at `:1436-1439` says verbatim "Do NOT delete or re-remote
  `~/Development/claims-model-starter.wiki`"** — the exact action the rename requires. The conflict
  is textual, not substantive (its stated reason is "keep the original's auto-publish working," which
  re-pointing *preserves*), but a C4 executor reading it mid-fork will correctly refuse. Phase 2
  rewords it.
- **The C4/C5 clone-independence grep loses its repo-name alternative and cannot get it back.** Its
  own comment warns that a narrowed pattern "can pass -> 0 while a hardcoded `claims-model-starter`
  string survives in the clone's publish_wiki.sh" — and the rename renames exactly that string. The
  naive repair is unusable: `model_project_constructor` matches **1,916 lines across 183 files**. The
  plan recommends scoping by path instead, and says to flag it rather than silently rewrite another
  plan's criteria.

#### Method: 9 agents — 5 discovery lenses, 3 refuters, 1 completeness critic — all verified by hand

The sequencing refuter **killed my first phase order** and it was right: I had the rename as a
commit-free phase with `mkdocs.yml` deferred to the next session, which leaves the public site dead
across a session boundary. The order cannot be inverted either (pushing `mkdocs.yml` first publishes
a canonical URL that does not exist). **Phase 1 is now rename + site fix in one session, one push.**

A discovery lens caught a real bug in **my own** inventory: I counted pattern 2 as
`claims-model-starter.wiki` **as a regex**, so the unescaped `.` also matched
`claims-model-starter/wiki` page URLs — 104/11 instead of the literal **95/7**, with the 9 extras
needing a *different* fix. Learning **#106**.

**The completeness critic earned its slot after the refuters had already run**, which is the
argument for keeping it: it found that `origin/gh-pages` ships a **gzipped** `sitemap.xml.gz` that no
`grep` can read, that it is served live, that it carries the two dead URLs, and that **my own**
completion criterion therefore passed while the live site still advertised the old path. The gh-pages
census is 28 occurrences across 5 files, not the 25/4 every earlier lens reported. Learning **#108**.

Per learning #104 I adjudicated every finding rather than trusting rankings, and I re-derived every
number the agents reported — including the analogue renames, the gz blob, the annotated tag messages,
and the merge-commit precedent. Several agent claims did not survive that check and are not in the
plan; one I could not confirm (git **push** continuity over a stale remote — `git-receive-pack`
returns 401 unauthenticated) is marked documented-not-measured in §1 rather than asserted.

### Session 225 Handoff Evaluation (by Session 226)

**Score: 7/10.** It scheduled the right work, pointed at the right precedent, and its gotchas changed
my behaviour four times. It also shipped a fabricated number inside the paragraph warning against
fabricated numbers.

**What helped, concretely:**
- **Gotcha 7 ("this is still zsh; single-quote your heredoc delimiters").** Every heredoc this
  session used `<<'PYEOF'` / `<<'PLANEOF'`. **Zero** quoting round-trips across ~15 heredocs. Third
  session running that this pays; keep writing it down.
- **Gotcha 5 / learning #104 ("cap the verification, never the adjudication").** This is why I read
  all ~100 discovery findings rather than the top-ranked ones — and the pattern-2 regex bug, the
  fail-open hook, and the `rsync` wipe were **not** the top-ranked findings.
- **The ruling's six-item checklist.** Five of six were real and it named the right precedent
  (`bfd9f36`) and the right learning (#60). A genuinely good scaffold; I resolved all six and added
  six more.
- **Learning #32's pointer** decided the wiki `Changelog.md:124` ruling in one read instead of a
  debate.

**What was wrong — three claims, all falsified:**
1. **"667 references across 52 files."** Reproducible at no commit, by no method. Filed as fresh
   truth in `BACKLOG.md:51` and `SESSION_NOTES.md:239`, replacing a number correctly flagged as stale.
2. **"418 of the 667 hits are in `docs/architecture-history/`, including *both* `SESSION_NOTES`
   shards."** The S220 shard contains **zero** occurrences. Verified:
   `git grep -c claims-model-starter -- 'docs/architecture-history/SESSION_NOTES-S220*'` -> nothing.
3. **"The commit that renames the wiki source directory is the commit that disarms its own
   publisher."** Not as stated. `gh repo rename` does not alter the local clone's stored origin
   string, so `publish_wiki.sh:72` still matches; the guard only trips if you re-point the clone. And
   the guard fails **closed and loud** — while the mechanism that actually fails **open and silent**
   (the hook trigger) went unmentioned. The handoff warned about the safe half and missed the
   dangerous half.

**What was missing:** the Pages non-redirect (the single most important fact about this task); the
fail-open trigger; the `rsync` wipe path; the overloaded name; the already-broken stylesheet; the
third clone at `~/Development/mpc_tests/model_project_constructor`; and that `WIKI_DIR` is assembled
from path *parts* and is therefore invisible to the path-pattern grep the item told me to use.

**ROI: strongly positive.** The scaffold saved more time than the three false claims cost, because
all three were cheap to falsify — one `git grep` each. The lesson is not "trust less," it is
**"a handoff number without its command is a rumour"** (#105).

### Session 226 Self-Assessment

**Score: 8.5/10.**

**+** Found the one fact that changes the decision (Pages does not redirect) and sourced it to
GitHub's own documentation rather than to recollection — then confirmed it twice, on two pages.
**+** Pinned the inventory to a commit and showed the reproducing command, so the next session can
falsify me in one line instead of re-deriving. Caught that both prior counts were wrong, including
the "corrected" one.
**+** **Falsified my own completion criterion before shipping it.** §7.2 prints 20 paths today; it is
red and must go green, and the 20 are listed. A criterion never observed failing proves nothing
(#99/#102 applied at the plan level rather than the test level).
**+** Verified every load-bearing mechanism against the artifact instead of reasoning about it:
`man githooks` for the exit-code semantics, `35ccbd9` for `diff-tree`'s rename shape, `ff04c02` for
the merge-commit blindness, live `curl` for the stylesheet, `git check-ignore` for the dossier
artifacts.
**+** Accepted an adversarial refutation that cost me a restructure rather than defending the draft.
**+** Upgraded the central claim from documented to **measured** when a lens produced a better method
than mine: `apache/incubator-superset` → `apache/superset` gives the contrast live — the old **repo**
URL 301s to the new one while the old **Pages** URL 404s with no `Location` header, same host, same
instant. `facebook/jest` → `jestjs/jest` corroborates. I re-ran both myself rather than citing the
agent.
**+** Held scope: found four real defects and **filed all four instead of fixing any** (§8.1).

**−** My first phase order had the defect the refuter found, and I should have caught it myself: I
wrote both "Pages does not redirect" and "rename in one phase, fix `site_url` in the next" and did
not connect them. **The fact was in my own §1 two hours before the refuter used it against my §5.**
**−** I shipped a regex where I needed a literal (pattern 2) — in an inventory whose entire value is
exactness, and after the project has already learned this class of lesson.
**−** Three arithmetic errors in my own subtotal tables, caught only because I re-added them. The
totals were right; the group subtotals were not.
**−** **The completeness critic found a fail-open in my own completion criteria, after three
refuters missed it.** My §7.4 check was `curl …/sitemap.xml | grep -c` → 0 — and `sitemap.xml.gz` is
served alongside it, carries the same two dead URLs, is preferred by crawlers, and **no `grep` can
read it**. I wrote learning #108 ("observe the criterion red before shipping it") and then shipped a
criterion I had not run against the artifact's full blob list. Corrected, but I did not find it.

**Against the bar:** S225 shipped 3 learnings and a 12-mutant matrix; S224 shipped a proof with a
new assertion class. This session shipped a plan whose central finding **reverses the premise of the
task** and whose completion criterion is falsifiable and observed-red. Comparable, and honest about
the gap.

**What's next — EXECUTION IS BLOCKED ON FIVE OPERATOR DECISIONS.** Do not open a Phase 1 session
until D-R1 is answered; the other four can be answered at that session's start.

| # | Question | Recommendation |
| --- | --- | --- |
| **D-R1** | The Pages URL dies permanently (§1). Accept the 404, buy a custom domain, or don't rename? | **Accept** — pre-UAT, no active tracker, no established external audience. **The only irreversible decision in the plan.** |
| **D-R2** | Rename `docs/wiki/claims-model-starter/` too? | **Yes.** 51 of the 114 change-side lines plus a `git mv` of 25 pages. Changes **nothing** about the published wiki — `publish_wiki.sh:92` rsyncs *contents*. |
| **D-R3** | Rebrand the wiki titles (`Home.md:1`, `_Sidebar.md:1`)? | **Yes** — the wiki is *already* self-inconsistent (sidebar says "Claims Model Starter", `License.md:3` says "Model Project Constructor"). **These two files carry zero hyphenated hits and are outside the 51.** |
| **D-R4** | Sequence against the enterprise fork? | **Rename first.** Fork is gated on B2; the collision is five falsified assertions the plan already fixes. |
| **D-R5** | Wiki clone: re-point in place, or `mv` the directory? | **In place.** The `mv` costs 26 dashboard snapshots, a Claude Code state dir, and two docstrings in another project's repo — for cosmetics. |

**Then Phase 1 of `docs/planning/repository-rename.md`, and ONLY Phase 1.** Five phases, five
sessions. Phase 1 is `gh repo rename` **plus** the four-file site commit **in one session, one push**
— they cannot be split (K1), and an earlier draft that split them was killed by adversarial review.

**Key files:**
- **`docs/planning/repository-rename.md`** — the deliverable. 1,245 lines. Read §1 first: it may
  change the operator's answer to "should we rename at all." §5's K-table (K1-K8) is the compressed
  form of every ordering constraint; if you read nothing else, read that.
- `scripts/publish_wiki.sh` — 10 old-name lines. **`:101` already emits the NEW name — do not
  "fix" it.** Guards at `:53`/`:58`/`:72`/`:80`/`:86` all fail closed; `:92`'s `rsync -a --delete` has
  no contents check (plan dragon 3).
- `.githooks/post-commit:18` — **the single fail-open line in the system** (plan dragon 4). Zero test
  coverage; `git grep -ln "post-commit\|publish_wiki" -- tests/` returns nothing.
- `tests/test_wiki_no_line_citations.py:38` — `WIKI_DIR` is built from path **parts**, so
  `grep "docs/wiki/claims-model-starter"` **does not match it** while `:60` asserts `is_dir()`.
- `docs/planning/enterprise-migration.md` — `:831`,`:832`,`:833`,`:1520` become **vacuous passes**;
  `:1356` becomes a false failure; `:1311`/`:1358` and dragon #21 at `:1436-1439` **forbid the action
  Phase 4 requires**.
- `mkdocs.yml:3-5` and `.github/workflows/publish-tutorial.yml:6-10` — the deploy trigger that pins
  the whole sequence.

**Gotchas:**
1. **Re-run the §7.2 allowlist before touching anything. It must print exactly the 20 paths listed in
   the plan.** A different set means the plan drifted and §2 must be re-derived first.
2. **All counts are pinned to `59615e2`, deliberately the commit before the plan existed.** The plan
   itself adds ~98 hits and a 52nd file, in `docs/planning/` — the *live* bucket. It is exempt
   (allowlist group 2); do not "classify" it in Phase 5.
3. **Use `grep -F` for `claims-model-starter.wiki`.** As a regex the `.` also matches
   `claims-model-starter/wiki` page URLs: 104/11 vs the literal 95/7, and the 9 extras need a
   *different* fix. Learning #106.
4. **`git grep` cannot read `sitemap.xml.gz`**, which is served live and carries the dead URL. Any
   sitemap check that omits the `.gz` is fail-open. §7.4 checks both. Learning #108.
5. **The published tutorial is already unstyled** — page 200, stylesheet 404, measured 2026-08-19,
   pre-dating any rename. Record the baseline before Phase 1 or you will blame the rename for it.
6. **Do not `mkdir` the wiki destination directory.** `git mv` only. An empty-but-existing
   `SOURCE_DIR` passes all five guards and `rsync -a --delete` then wipes and **pushes** the live
   public wiki (plan dragon 3).
7. **Every phase stays on a direct commit to `master`.** The hook is blind to merge commits — proven
   here, not theorised: `ff04c02` changed five wiki pages and published nothing.
8. **This is still zsh.** Single-quote every heredoc delimiter. Five sessions running; it has cost
   zero round-trips for the two that wrote it down.
9. **No phase earns a `CHANGELOG.md` entry.** `PROJECT_CONVENTIONS.md` §2 exempts "docstring or
   **path strings**", which is every `scripts/`/`tests/` edit here. `CHANGELOG.md` is append-only —
   a wrong entry is permanent. Settled in the plan so nobody re-litigates it.
10. **`SESSION_NOTES.md` is 1,461 lines after this record** — under the >1,500 trim trigger but close.
    The next session will likely cross it. `CLAUDE.md`'s trim section has the rule; there are **two**
    shards to grep, never `Read`.

**Four defects found while planning and deliberately NOT fixed** (plan §8.1, file as backlog items):
the unstyled Pages site; `publish_wiki.sh`'s missing contents check; the fail-open hook; and
`docs/planning/httpx-adapter-migration.md` sitting un-archived against `PROJECT_CONVENTIONS.md` §3
(archiving it would shrink this rename's scope by one file).

### What Session 225 Did
**Deliverable:** **The eval harness's governance measurement now applies one transient policy across
both of its live surfaces. COMPLETE.** `BACKLOG.md`'s "three live measurement blocks / three
different transient policies" item is closed: the two hand-written governance loops — the
measure-and-report driver and the assertion gate — are replaced by a shared
`tests/eval/governance_sweep.py`. **Harness only. No `src/`, no `packages/`, no threshold, no live
call, no verdict re-scored.**

**Started:** 2026-08-19. **Completed:** 2026-08-19. **Commits:** `90a50d5` (Phase 1B claim, its own
commit), `2f853f7` (the fix), `fcb4366` (acting on the adversarial review), `27c2007` (the documents
that describe the structure), and this close-out.

**Gate: 1230 passed + 9 live-skipped @ 97.98% coverage** (was 1202, Session 223 baseline — +28 tests);
`uv run ruff check src/ tests/ packages/ scripts/` and `uv run mypy` both clean. Plus a **12-mutant
matrix over `governance_sweep.py`, 12/12 caught** — which is not the same claim as the green suite,
and the difference mattered (below).

#### The defect, as read in the code rather than inherited from the backlog's summary

| surface | before | after |
| --- | --- | --- |
| `shadow_run.measure_provider` | caught `IntakeLLMError`, **no retry**, scored an immediate non-agreement | shared sweep: retry → score |
| `test_eval_live`'s governance test | **no handler at all** — the seam error aborted the gate | shared sweep: retry → score |
| both | **no transport handler**, and `classify_governance` wraps none | retry → exclude, counted |

The third row is the one the backlog did not name and the one that mattered most.
`AnthropicLLMClient._call_json` (`anthropic_client.py:363-370`) calls `messages.create` **bare**, so an
`APITimeoutError` raised after the SDK exhausts its own retries propagated past *both* governance
surfaces and **aborted a ~2.5-hour live run mid-measurement**. That is the hole S171 closed for
interviews and S221 for SQL/QC. I found it by reading `_call_json`, not by trusting the item.

#### The design decision, and why it went the way it did

An exhausted `IntakeLLMError` is **scored** a non-agreement, not excluded — the opposite of what
`interview_sweep` does with the *same exception class*. That is deliberate and is the crux of the
whole item. Excluding shrinks a denominator whose survivors are clean by construction, so a provider
failing 24 of 25 samples would score 1/1 = 100% and **pass**. An interview sample is a whole
multi-turn run that a seam failure leaves with no report to judge; a governance sample is one call
whose failure **is** the measured capability. `sql_sweep` made the same call for the same reason in
S221; I followed it, and it also preserves `shadow_run`'s existing semantics, so the retry is the only
semantic change on that surface.

**A seam failure never increments `laxer_misses`.** No prediction means no risk tier, and fabricating a
miss against `GOVERNANCE_LAXER_MISSES_MAX = 0` would turn one blip into a NO-GO — the exact S219 shape
the item exists to remove. `shadow_run` already behaved this way; it is now tested at both the sweep
level and the driver level.

#### The review found three false claims of mine, and the mutants found a fourth

23 agents, 5 lenses, 3-refuter majority panels. **24 findings; my verification cap of 6 left 18
unverified, and adjudicating those 18 by hand produced more real defects than the verified 6 did** —
see learning **#104**, which is the most transferable thing in this session.

**Three docstrings I wrote were false:**
1. "All three blocks now apply one transient policy." They do not — `interview_sweep` *excludes* an
   exhausted seam error where the other two *score* it. The true, checkable claim is the weaker one:
   **no hand-written measurement loop remains.** Learning **#103**.
2. "This driver's SQL call site had the S221 missing-sink defect for three sessions." It has passed
   `on_event=_warn` since `4e2c8ec` (S218) — the sink-less site was `test_eval_live`'s, which that
   file already says at `:164-165`. I invented a history that the repo contradicted in the file I was
   editing.
3. `_warn`'s enumeration omitted the interview sweep it also serves.

**⚠ And then a mutant caught a fourth, after the review.** I closed a finding that the summary-line
test asserted labels but no values — then ran a 12-mutant matrix, and the mutant *swapping the two
fractions* **survived**: I had set both `cycle_matches` and `risk_acceptable` to 2/3, so the swap
rendered identically. The assertion I had just written specifically to catch that was unfalsifiable
because its operands coincided. **This is S224's failure exactly one session later, one layer down**
— #99 says every assertion needs a mutant; #102 says the mutant cannot reach the assertion if the
fixture's values are degenerate. Only running the mutants found it. 11/12 → fix → 12/12.

**Two findings the panel KILLED were true on the facts** (learning #100, applied): a transport
exclusion leaves a *rate* unbiased but can only move the zero-tolerance `governance_laxer_miss`
**count** toward PASS; and the tiers key on exception *class*, so `opencode`'s subprocess adapter —
which maps spawn failure, non-zero exit and timeout onto `IntakeLLMError` — lands its transport
failures in the **scored** tier where an SDK provider's are excluded. Both are now documented; the
second is **filed as a new backlog item**, because fixing it means changing the adapter's error
mapping, not the harness.

#### Scope held

`interview_sweep.py` and `sql_sweep.py` are **byte-stable**. Hoisting one generic `_call_with_retries`
into a shared module is a cross-module refactor `SAFEGUARDS.md` gates behind plan mode, so the
near-duplicate is documented as a deferral in its own docstring rather than smuggled into a fix. Two
review findings that were real but out of scope were **filed, not fixed**.

### Session 224 Handoff Evaluation (by Session 225)

**Score: 9/10.** Its content was about a trim and my task was an eval-harness fix, so almost none of it
applied by subject — and it still moved my behaviour four separate times, which is the better test.

**What helped, measurably:**
- **Gotcha 7 ("this is zsh; single-quote your heredoc delimiters").** I used `<<'PYEOF'` / `<<'PY'`
  for every heredoc in this session and spent **zero** round trips on quoting failures, against the
  four S224 burned and the ones S223 burned before it. A gotcha that costs one line to write and
  saves four round trips is the highest-ROI thing in the file.
- **"Use an odd panel and a majority rule next time"** — S224 designed a 2-agent panel under
  `kills >= 1` and one API death silently made a finding single-vote. I ran 3-refuter panels under a
  strict majority, and one finding split 2/3 vs 3/3 across two lenses, which is exactly the case a
  1-vote rule would have decided wrongly.
- **Learning #97's state guard**, applied as a control: `sha256` over all five artifacts before
  launching 23 agents, re-checked after. All five matched.
- **Learning #99** — I built the assertion×mutant matrix *because* S224 paid for that lesson. It then
  caught me anyway, one layer down. The learning worked; my application of it was incomplete.

**What was missing:** nothing it could have known. It correctly said "the backlog is unchanged by this
session" and deferred to S223's ordering rather than re-deriving it — honest, and the ordering was
right. The one thing no handoff in this series has carried is **how to size a review fan-out**; S224
recorded the panel-shape lesson but not the cap lesson, and I paid for the second. That is now #104.

**What was wrong:** nothing. Every claim I checked held.

**ROI: very high**, and unusually so given zero subject overlap.

### Phase 3B: Self-assess — Session 225 — 8/10

- **The +:** (1) **I read the seam before trusting the backlog** and found the transport hole the item
  did not name — the largest real defect closed this session. (2) **Test-first**, and the new module's
  tests were red for the right reason before it existed. (3) **I ran the mutants instead of trusting a
  green suite**, which is the only reason the degenerate-fixture defect was found at all. (4) **I
  adjudicated all 18 capped findings by hand** rather than treating the cap as a verdict, and that is
  where three of my four false claims came from. (5) **I acted on two findings the panel killed**,
  because their facts held and only the severity ruling went against them. (6) **Scope held under
  pressure**: three real, adjacent, one-line defects were filed rather than fixed. (7) The existing
  `test_shadow_run` wiring test caught my eager method binding immediately, and **I fixed the test
  double rather than contorting the driver** to please it.
- **The −:** (1) **I shipped three false statements in docstrings** — including one in the module
  docstring of the file the live gate lives in — and an outsider found all three. Two of them
  contradicted text *in the same file I was editing*. **This is the session's real error.** (2) **I
  reproduced S224's exact failure mode one session later**: I wrote both an assertion and its mutant
  and did not check that the second could reach the first. (3) **I set the verification cap to 6
  before seeing a single finding**, ranked by severity labels the finders assigned on incompatible
  scales; the capped pile was richer than the verified one. (4) **I over-claimed uniformity because
  the refactor's motivation was uniformity** — the slogan became the docstring without being checked
  against the siblings. (5) I did not re-read `interview_sweep.py`'s exhaustion branch before writing
  the "all three" sentence, though I had read it 40 minutes earlier — **failure mode #11 exactly**,
  and the fix was four lines of `grep`.

**Versus the bar:** S221 closed one asymmetry and filed the wider one; S223 fixed one contract and
filed its sibling; both shipped a fix plus a filing. This closes the wider one, files two more, and
adds a falsification step (the mutant matrix) that neither predecessor ran on its own work. That meets
the bar on the deliverable. It falls short of S224 on docstring discipline: S224 shipped one uncovered
assertion, and I shipped three false claims plus one uncovered assertion.

**Phase 3C:** learnings **#102-104** appended to `PROJECT_LEARNINGS.md`; `CLAUDE.md`'s count updated
101 → 104. **No workstream document edited** — `docs/methodology/workstreams/` is third-party synced
material (`NOTICE` §1). `PROJECT_LEARNINGS.md` **#86** was edited: its source column still said "Filed
in `BACKLOG.md`" in the present tense about the gap this session closed, and the learning itself
carried the same "one policy" over-reach I shipped, so both were corrected.

**`CHANGELOG.md` entry written** — `PROJECT_CONVENTIONS.md` §2 gates on changes to `src/`, `packages/`,
`scripts/` or `tests/` **logic**, and this session changed `tests/` logic. (S222's and S224's trims
took no entry because they touched none of those; do not read this as a cadence change.)

**⚠ OPERATOR RULING (2026-08-19, after this session closed out) — the next session is the
repository rename, and it is a PLANNING session.**

> *"set rename of repository as the next session ; it may take a planning session because of the
> blast radius of a rename"*

**Do not start renaming anything.** The deliverable is `docs/planning/repository-rename.md` —
a plan document with a **freshly re-derived** evidence-based inventory and per-phase completion
criteria. Then close out. Execution is a separate session (FM #18; `SAFEGUARDS.md`: "renames cascade,
they are never quick"; and "never rename/move files as part of a quick fix").

**The filed inventory is STALE — re-run it, do not inherit it.** `BACKLOG.md`'s table was counted
2026-08-17 (Session 221) at **644 hits across 50 tracked files**. Today the same patterns give
**667 across 52**. Four sessions of `CHANGELOG.md`, `SESSION_NOTES.md` and a second archive shard
have landed since. `SESSION_RUNNER.md` is explicit that a plan listing files it did not search for is
an assumption, not an inventory — and this one has already drifted 23 hits.

**What the planning session must resolve, at minimum:**
1. **The two traps that spring on the landing commit itself.** `scripts/publish_wiki.sh`'s remote-URL
   guard greps for the literal `claims-model-starter.wiki` and **fails closed**, and
   `.githooks/post-commit` triggers on the literal path `docs/wiki/claims-model-starter/`. The commit
   that renames the wiki source directory is therefore the commit that disarms its own publisher.
   Sequence this explicitly — which lands first, and what the recovery is if the hook fires mid-way.
2. **`docs/wiki/claims-model-starter/` is a directory rename of 25 published pages** (509 of the
   hits), and renaming it changes what auto-publishes. Decide whether the live GitHub Wiki is
   republished from the new path, and what happens to the existing `claims-model-starter.wiki` clone
   at `~/Development/`.
3. **The historical/live split.** 418 of the 667 hits are inside `docs/architecture-history/`,
   including **both** `SESSION_NOTES` shards — those **keep the old name** per the SR 11-7 → SR 26-2
   precedent (`bfd9f36`). **Run `git show --stat bfd9f36` before starting** (learning #60). Note the
   shards are write-once and one is 24,590 lines: `grep` them, never `Read` them.
4. **One reference lives in a synced file that must not be edited** — find it, and decide the
   customization-seam workaround rather than editing it.
5. **The name form is underscores** and the three-convention divergence is deliberate: PyPI
   distribution names stay hyphenated, the import package and repository are underscored. Do not
   "fix" it.
6. **`mkdocs.yml:3-5` moves the published Pages site URL.** Decide whether the old URL is left to
   404, redirected, or is a GitHub-side automatic redirect — and note D6 (2026-07-27) keeps that site
   public **indefinitely**, so a dead URL is a permanent dead URL, not a temporary one.

**Everything below is the pre-existing ordering, now superseded as the next pick.** It stays because
the rename is one session (planning) plus N (execution), and this is what follows.

**What's next — the backlog moved.** One item closed, two filed. S223's ordering for what remains
still stands and I am not re-deriving it:

1. **The `KeyError` guard** (`BACKLOG.md`) — small, well-specified, mirrors a shipped intake
   convention; twinnable with the `probe_information_schema` item, same root cause. **Now the cheapest
   real item on the list.**
2. **`probe_information_schema`** — one file, ~20-40 lines, 3-5 tests, not twinned.
3. **The two surfaces that stay silent** (filed this session) — two one-line changes, and the first of
   them (`test_eval_live.py:221` passing no `on_event`) is the last instance of a defect class this
   session and S221 both closed elsewhere. **Cheapest item in the repo; do it as a warm-up or bundle
   it with nothing.**
4. **The silent `--db-url` failure** — (a)+(b) small; **(c) needs an operator ruling.**
5. **Re-measure `opencode`** — **~$16.40, ~130 min, its own session.** Source `.env` first. **Read its
   updated caveat 1 before quoting anything**: governance's non-comparable span is **S216-S220**, a
   different span from the SQL/QC cells' S219-S220.

**Key files:**
- `tests/eval/governance_sweep.py` — the new module. Its docstring argues the scored-vs-excluded split
  and states the two asymmetries (count-vs-rate under exclusion; per-provider exception classes). **If
  you touch the exhaustion tiers, the mutant matrix below is how you check yourself.**
- `tests/eval/sql_sweep.py` — the sibling this copies. `_call_with_retries` is a near-duplicate by
  design; the two differ **only** in the module-level transient tuples. If you ever unify them, that
  invariant is what to assert first.
- `tests/eval/interview_sweep.py` — the sibling that **differs**. It excludes an exhausted seam error.
  Do not "fix" that to match; read its docstring first.
- `/private/tmp/.../scratchpad/mutants.py` — the 12-mutant matrix. **Scratch, not committed, and it
  will be gone.** Re-derive it from the assertion list rather than hunting for it; it took ~15 minutes
  and found a defect the whole review missed.
- `tests/eval/PHASE_E_AGREEMENT_REPORT.md` — the Session 225 update block supersedes the S221 block's
  caveat 6. Older blocks are **frozen**; add a new dated block, do not edit one.

**Gotchas:**
1. **Do not claim the three sweeps share one transient policy.** They share the *absence of
   hand-written loops*. All three retry and all three exclude an exhausted **transport** error;
   `interview_sweep` excludes an exhausted **seam** error where the other two score it, and that is
   correct. I shipped the stronger claim and a 3/3 panel killed it.
2. **`governance_laxer_miss` is a COUNT against a maximum of 0, not a rate.** An exclusion cannot bias
   a rate but can only move a count toward PASS. Read it with `governance_excluded_transient`. Every
   surface that quotes one must quote the other.
3. **Two providers are judged by different rules and it is not fixed.** `opencode` maps transport
   failures onto `IntakeLLMError`, so they are *scored* where an SDK provider's are *excluded*. Filed.
   Do not compare a scored-exhaustion count across providers without naming this.
4. **A green suite is not a falsified suite, and asserting a value is not enough** — the operands must
   differ. My summary test asserted all six values and still could not see two of them swapped,
   because both rendered `2/3`. Give every slot a distinct value, then run the swap mutant.
5. **Cap the verification in a review fan-out, never the adjudication.** 18 of my 24 findings fell past
   the cap and were richer than the 6 that did not. Read every dropped item yourself. Learning #104.
6. **`shadow_run.measure_provider` binds `intake.classify_governance` as a bound method**, so the
   attribute is dereferenced before the corpus is walked. A corpus-emptying test double must therefore
   be client-shaped; a bare `object()` raises. This is a feature — it fails fast — but it will bite the
   next person who stubs that client.
7. **This is still zsh.** Single-quote every heredoc delimiter. Four sessions running have paid for
   this; I did not, because S224 wrote it down.
8. **`SESSION_NOTES.md` is at 1,148 lines after this record** — under the >1,500 trim trigger, roughly
   two more sessions of runway at this density. Not your problem yet; `CLAUDE.md`'s trim section is
   where the rule lives, and there are now **two** shards to grep, never `Read`.

