# Session Notes

**Purpose:** Continuity between sessions. Each session reads this first and writes to it before closing out.

**Second trim (Session 224). Archived Sessions 220 → 217 — 5 record headings, 774 lines** into
[`docs/architecture-history/SESSION_NOTES-S220-through-S217.md`](docs/architecture-history/SESSION_NOTES-S220-through-S217.md)
— same shape, same newest-on-top order, frozen and byte-for-byte unedited. **This live file now
holds Sessions 224 → 221 only** — four sessions, the floor `CLAUDE.md` sets. Its proof is
[`SESSION_NOTES-S220-through-S217.md.verify.sh`](docs/architecture-history/SESSION_NOTES-S220-through-S217.md.verify.sh):
four inherited assertions plus an L4 pinning the cut point, its own key, its own `--self-test`.

**Two shards exist now, and neither is a prefix of the other.** To place Session N: **N ≤ 216** →
the S216 shard; **217 ≤ N ≤ 220** → the S220 shard; **N ≥ 221** → below, in this file. `grep` both;
`Read` neither. **Shards are write-once** — a third trim writes a third file, it does not append.

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

### What Session 224 Did
**Deliverable:** Second lossless trim of `SESSION_NOTES.md`. The live file stands at 1,448 lines
against `CLAUDE.md`'s 1,500-line trim trigger with ~52 lines of headroom, and this session's own
close-out (~184 lines at observed density) crosses it. Retire the oldest records into a **new
write-once shard** under `docs/architecture-history/` with its own cut key, beside a re-runnable
`.verify.sh` that ships its own falsification test (`--self-test`), and cut the live file to
≤ 1,050 lines while retaining no fewer than 4 sessions. Documentation only — no production code.
(IN PROGRESS)
**Started:** 2026-08-18
**Status:** Session claimed. Work beginning.
**Three commits, per `CLAUDE.md`:** this claim is committed alone, the trim lands alone with **no**
record edit in it, and the close-out follows. A bundled record edit registers as an added record and
holds the proof red forever.

### What Session 223 Did
**Deliverable:** **`sql_dialect_from_url` honours its own contract. COMPLETE.** A non-numeric port in
a `--db-url` degrades to `None` like every other unparseable URL instead of raising a bare
`ValueError` at two production seams. **One line of logic changed** in shipped package code;
everything else is tests and documentation. **No threshold, no default, no pipeline behaviour
changed.**

**Started / Completed:** 2026-08-17. **Commits:** `38d1dea` (Phase 1B claim, its own commit),
`2733df0` (the fix), `99e9abf` (rulings + index + findings), this close-out. **Trigger:** the
operator read the Phase 0 report, said *"I do not understand any of the 9 listed items"*, and after
the translation picked item #5 — plus two carried asks.

**Workstream:** `docs/methodology/workstreams/DEVELOPMENT_WORKSTREAM.md`. Its Phase 2 **Step 6**
("verify assumptions — *this function is only called from X*, verify with grep") is what produced the
session's two most useful findings, both of which contradicted a written claim.

#### The fix, and how the filed remedy was incomplete

`BACKLOG.md` prescribed `except (sa.exc.ArgumentError, ValueError)`. **That was correct** — the first
filed remedy in four sessions that survived pricing intact (contrast learning #94). But its
*characterisation* was too narrow, and only measurement showed it.

A 24-case probe against SQLAlchemy 2.0.49 established the failure surface instead of reading it:

| | outcome | note |
| --- | --- | --- |
| structurally unparseable, wrong-type (`None`, `int`) | `ArgumentError` | already handled |
| **five** port shapes — unexpanded env var, alphabetic, **empty** (`@host:/`), float, IPv6-with-either | **bare `ValueError`** | the bug; BACKLOG named **one** |
| negative port, 20-digit port, whitespace port, newline in URL | **parse fine** | why the fix stops short of range validation |

The empty-port case is the same shell template with the variable set to `""` — as plausible as the
one that was filed. **`ArgumentError` is not a `ValueError` subclass** (`-> SQLAlchemyError`), so the
library's own error type does not cover the library's own failure mode.

#### The over-catch was invisible to a complete-looking suite

Mutating in **three** directions, not one:

| mutant | tests killed |
| --- | --- |
| `except sa.exc.ArgumentError:` (the original bug) | **10** |
| `except ValueError:` (drops the old arm) | **3** |
| `except Exception:` (over-catch) | **0 → 1** |

The over-catch mutant **survived the first suite that looked finished**. Silently returning `None` for
a genuine defect drops the dialect from the prompt and reintroduces wrong-database SQL — the exact
failure the module exists to prevent. One monkeypatch test closed it. **A widened `except` has two
bounds and mutation testing only finds the one you thought about** (learning #96).

**Neither production seam had regression coverage.** `tests/scripts/test_run_pipeline_adapter.py` and
`tests/data_agent_package/test_cli.py` both exercised these seams with well-formed URLs only and
**would not have caught this**. Both new cases die under the reverted catch — verified, not assumed.

#### ⚠ Adversarial review refuted my own write-up — read this before quoting the fix

3 claims raised, **1 confirmed, 2 refuted.** The confirmed one was mine:

**I wrote a falsehood into the CHANGELOG, inherited from a recon agent and never run.** I claimed the
post-fix path reaches `Status: FAILED_AT_DATA`. **There is no such off-ramp for any DB problem.**
Verified by reading the code myself: `nodes.py:118-120` catches `DBConnectionError` **without binding
it**, `agent.py:147` returns `status="COMPLETE"` unconditionally, and `pipeline.py:460` halts only on
a non-COMPLETE report. Corrected in four places, with the correction *stated* rather than quietly
patched. This is failure mode #11 (claims from memory) in its agent-mediated form: **a subagent's
finding is a claim, not a measurement.**

**The reviewer's own headline claim — "the fix is incomplete" — was then refuted by the verify pass**,
which ran the control arm the first pass omitted: with the catch reverted, `--db-url 'not-a-url'` (an
`ArgumentError` case the fix does not touch) *also* yields `COMPLETE`/exit 0. So the silence is a
property of the DB error path, **not of this diff**. Filed as its own item with that control recorded,
explicitly flagged **not a reason to revert S223**.

**What the fix therefore buys: consistency, not diagnosability.** Pre-fix this one case crashed with
the cause in the traceback; post-fix it is quiet like every other bad URL. That is the right trade —
a raw `ValueError` out of prompt construction is not a diagnostic — but it is a trade, and the
docstring, both test docstrings, the CHANGELOG and the BACKLOG all now say so.

#### Two operator asks, both landed

1. **CHANGELOG cadence — SETTLED** in `PROJECT_CONVENTIONS.md` §2. Measurement-only sessions get no
   entry; the written gate was right; **S216 was the deviation and is neither backfilled nor
   amended** (append-only ledger). Un-asked for four sessions; now un-askable.
2. **Plain-language index** at the top of `BACKLOG.md` — vocabulary, the five-items-are-one-complaint
   grouping, one row per open item with real cost, and a maintenance rule. **12 rows against 12 open
   headings, cross-checked.**

#### ⚠ What this does NOT establish

1. **The silent-failure item is filed, not fixed.** A pipeline run against a bad `--db-url` still
   reports `COMPLETE` at exit 0 with **every quality check unexecuted**. Its option (c) changes when
   a run may report success — an operator ruling, not an implementer's.
2. **`discovery.py`'s escape (1) has no measured trigger.** Read from source. Escape (2) needs none.
3. **No live call was made and no eval number moved.** `opencode` is still NO-GO.
4. **`ruff format` is still not applied** and the tree is not formatter-clean. That is correct — CI
   runs `ruff check` only. Do not "fix" it.

### Session 222 Handoff Evaluation (by Session 223)

**Score: 9/10.** The most useful handoff in this series, and the first whose highest-value content was
a *warning about itself*. Marked down only for a self-report that its own BACKLOG entry contradicts.

**What helped.** (1) **The trimmed ledger itself.** S222's deliverable *was* my Phase 0: reading
SESSION_NOTES cost one paginated read instead of a silent truncation. The pointer block's "`grep` that
shard; never `Read` it" is the single most load-bearing sentence, because the failure it prevents is
**invisible** — I would not have known I was missing 24,564 lines. (2) **"Run `--self-test` before
trusting a green run."** I ran the proof during Phase 0 (green, `added: 0`), and the framing —
*"a proof that has never been falsified proves less than it appears to"* — is verbatim why I mutated
my own fix in **three** directions instead of one, which is what caught the over-catch. Directly
traceable to this sentence. (3) **The three-commit rule in `CLAUDE.md`**, applied without thinking
about it. (4) **Gotcha 5** ("a record is a byte span, never a session") stopped me miscounting records
during the close-out. (5) **Explicit non-establishments**, which I copied as a section.

**What was wrong — one thing, and it is small.** S222's "what's next" #1 says the shard read-cap item
has **"nothing filed yet — file it first."** It *was* filed, by S222 itself, at `BACKLOG.md` — the
entry even reads "**Filed Session 222 by the session that created it**." A close-out written against
the plan rather than the tree. Cost me one grep; cost a less careful successor a duplicate item.

**What was missing.** Nothing I needed. The five options were accurate and correctly costed, and the
operator picked outside them again — which is now the third session running, and is a signal about the
*options*, not about the handoffs: they are written for an implementer and the operator reads them as
a menu. **The plain-language index this session added is the first structural answer to that.**

**ROI: high.** Two disciplines transferred directly into the deliverable's quality.

### Phase 3B: Self-assess — Session 223 — 8/10

- **The +:** (1) **Measured the failure surface instead of reading it** — a 24-case probe found the
  trigger is five classes wide, not one, and found the four shapes that *don't* raise, which is what
  kept the fix from over-reaching into range validation. (2) **Mutated in three directions and found
  the one I hadn't thought of** — the `except Exception` over-catch survived a suite I would otherwise
  have called done. (3) **Reverted my own tooling damage**: `ruff format` reflowed three unrelated
  functions; I caught it, checked CI, found no formatter gate, and restored a 1-line logic diff.
  (4) **Ran an adversarial pass on my own work and acted on it against my own interest** — it found a
  falsehood I had written. (5) **Verified the confirmed finding myself** by reading `nodes.py`,
  `agent.py` and `pipeline.py`, rather than accepting the agent's word. (6) **Kept the refutation**:
  when the verify pass overturned the reviewer's framing, I recorded the control experiment instead of
  quietly keeping the more dramatic version. (7) **Filed two findings rather than fixing them.**
- **The −:** (1) **I propagated a recon agent's unverified claim into a CHANGELOG entry.** The
  `FAILED_AT_DATA` sentence was never run by me or by the agent that wrote it. Caught by my own review,
  but it was committed-adjacent — one step from shipping as fact. **This is the session's real error.**
  (2) **I designed the review to mutate the file under review in the shared working tree**, then ran my
  own measurement against it concurrently and got a false pre-fix reproduction that looked exactly like
  "the fix doesn't work." `isolation: 'worktree'` existed and I did not use it. A state guard caught it
  on the second attempt — after the first had already misled me. (3) **I ran `ruff format` reflexively**
  in an unfamiliar-to-me lint setup without checking what CI enforces. (4) **Three broken shell
  harnesses in a row** on the final mutation sweep — a `\Q\E` that corrupted the replacement, then twice
  assuming POSIX word-splitting in **zsh**, where unquoted `$VAR` does not split. Four wasted round
  trips on a check I had already done correctly by hand earlier. (5) **The first CLI test under-asserted**
  relative to its own name — it omitted `exit_code == 0`. The reviewer was right that it could be
  stronger even though the claim was refuted as a defect.

**Phase 3C note:** no workstream document was edited — `docs/methodology/workstreams/` is third-party
synced material (`NOTICE` §1, `CLAUDE.md`). Learnings **#96–98** went to `PROJECT_LEARNINGS.md` and
`CLAUDE.md`'s count was updated 95 → 98. `PROJECT_CONVENTIONS.md` **was** edited — the one
project-owned file in `docs/methodology/`, re-verified before touching it.

**CHANGELOG entry written** — this session changed `packages/` and `tests/` logic, which
`PROJECT_CONVENTIONS.md` §2 gates an entry on. **The convention-vs-precedent conflict flagged by
S219/S220/S221/S222 is now CLOSED by operator ruling** and recorded in §2; do not re-open it.

**What's next — five options, all ungated:**

1. **The `KeyError` guard** (`BACKLOG.md`). **Recommended.** Shipped-package code, mirrors a shipped
   intake convention at `intake/anthropic_client.py:439-440`, small and well-specified — and it is the
   same root cause as the `discovery.py` item this session filed, so doing them together is defensible
   if you want one slightly larger session instead of two small ones.
2. **`probe_information_schema`** (`BACKLOG.md`, new this session) — fix escape (2) with confidence;
   treat escape (1) as defence-in-depth. One file, ~20-40 lines, 3-5 tests. Not twinned, so no parity
   battery to satisfy.
3. **The silent `--db-url` failure** (`BACKLOG.md`, new this session). Options (a)+(b) are small;
   **(c) needs your ruling first** because it changes when a pipeline run is allowed to report success.
4. **Re-measure `opencode` under the fixed harness** (`BACKLOG.md`) — **~$16.4, ~130 min, its own
   session.** Source `.env` first; quote `transient_retries` beside every rate.
5. **The three transient policies** (`BACKLOG.md`) — the governance loop's zero-tolerance bar is still
   fed by an un-retried transient. Recommended *before* spending $16 measuring with the instrument.

**Key files:**
- `packages/data-agent/src/model_project_constructor_data_agent/db.py:22-79` — the fix. **The
  docstring's ⚠ paragraph is the important part**: it states what the degradation does *not* buy.
- `tests/data_agent_package/test_db.py` — 23 tests. `test_unexpected_error_propagates_rather_than_degrading`
  exists because the `except Exception` mutant survived without it. **Do not delete it as redundant.**
- `BACKLOG.md` — **the plain-language index is at the top**; read it to the operator in Phase 0 and
  update a row whenever you change its item.
- `docs/methodology/PROJECT_CONVENTIONS.md` §2 — the CHANGELOG ruling. Settled; do not re-ask.
- `PROJECT_LEARNINGS.md` #96 (three-direction mutation), #97 (worktree-isolate mutating reviewers),
  #98 (run the real lint gate).

**Gotchas:**
1. **A subagent's finding is a claim, not a measurement.** A recon agent told me the post-fix path
   reaches `FAILED_AT_DATA`; it does not, and I put it in a CHANGELOG entry before checking. **Read
   the file the agent cites before repeating what it says.**
2. **Do not run mutating review agents in the shared tree while measuring.** Use
   `isolation: 'worktree'`, or guard every measurement with a file-state check **before and after** —
   a mutation can land mid-run. I have a false reproduction to show for skipping this.
3. **`ruff format` is NOT a project gate.** CI runs `ruff check src/ tests/ packages/ scripts/` and
   nothing else. The tree is deliberately not formatter-clean; running it reflows unrelated code.
4. **This is zsh, not bash.** Unquoted `$VAR` holding space-separated paths does **not** word-split.
   `uv run pytest $TESTS` silently runs nothing and prints "no tests ran" — which reads like a
   filtering mistake, not a shell bug. Inline the paths or use an array.
5. **The fix buys consistency, not diagnosability.** A bad `--db-url` still reports `COMPLETE` at exit
   0. Do not cite this fix as "bad database URLs are now handled properly" — the item is open.
6. **`SESSION_NOTES.md` is 1,448 lines against a 1,500-line trim trigger** (`CLAUDE.md`) — **52 lines
   of headroom, well under one session's ~184.** The next close-out crosses it. Read the retention
   rule *and* gotcha 4 of S222's record before trimming: three commits, cut to ≤1,050, floor of 4
   sessions, and **do not borrow the canonical trimmer's trigger** — at this density its stop
   condition is unsatisfiable and would trim to empty.

### What Session 222 Did
**Deliverable:** **`SESSION_NOTES.md` trimmed 25,578 → 1,033 lines. COMPLETE, and the move is
*proved* lossless, not asserted.** Sessions 216 → 1 (206 record headings, 24,564 lines, 4,073,396 B)
moved verbatim into `docs/architecture-history/SESSION_NOTES-through-S216.md`, beside a re-runnable
`.verify.sh` that ships its own falsification test. **The dashboard's HIGH risk flag on this project
cleared to medium** (health unchanged at 95/100). **Zero production code touched; documentation-only.**

**Started / Completed:** 2026-08-17. **Commits:** `f91f8e0` (Phase 1B claim, deliberately its own
commit), `a9510ca` (the trim), this close-out. **Trigger:** operator ask — "lossless trim of
SESSION_NOTES.md" — which was *not* among S221's five "what's next" options.

**Workstream:** `docs/methodology/workstreams/DEVELOPMENT_WORKSTREAM.md`. Its Phase 2 Step 3 ("read
the code you will modify — not the documentation, not the tests") is what produced the session's
governing finding, below: the remedy this task appears to call for does not exist, and only reading
the tool shows why.

#### The finding that shaped everything: the canonical tool refuses this file *on purpose*

`methodology_trim.py` is the fleet's lossless ledger trimmer. Its `LEDGERS` table holds exactly two
entries — `CHANGELOG.md` and `HANDOFFS.md` — and it answers `NO_CONFIG` for anything else. That is
not an oversight to patch. `methodology_dashboard.py:360-366` states the reason and names this file
specifically: `READ_CAP_WATCHED` is *deliberately wider*, "including SESSION_NOTES.md", and "the
trimmer answers NO_CONFIG on every one of those **by design** ('there is deliberately no generic
fallback: a generic rule is what would mis-zone a differently-shaped ledger')." It goes further —
naming the trimmer as the remedy for a file it refuses "would be a pointer the adopter cannot follow."

**So the refusal is a specification.** This session borrowed the tool's *discipline* and none of its
*config*: `methodology_trim.py` was not edited, not installed, and not run. It is also, notably, not
installed in this repo at all — it is present in 5 of the 13 fleet projects.

Three eras of grammar in one file justified that refusal empirically: a file-tail
`### Session N ARCHIVED ACTIVE TASK` zone (froze at S112), an inline-at-top demotion marker era
(S114–S178), and the current bare-consecutive-records era (S179–). A generic rule would have
mis-zoned at least one of them.

#### What "lossless" was made to mean

Not "it's in git." Not a whole-file checksum — **the manual whole-file procedure this replaces passed
while a paragraph was permanently lost**, because moving text from a live file into an archive is
*exactly* byte-preserving under concatenation. And a whole-file check is unsatisfiable here anyway:
the live file gained a pointer block, the shard gained a banner. So four scoped assertions, all
re-derived from git, none of them trusting the partition that produced the trim:

| | asserts | why it is not redundant |
| --- | --- | --- |
| **L0** | no trailing file-scoped block below the last record | in a newest-on-top ledger the footer sits exactly where the cut takes from; `footer_mode=none` must mean "I looked" |
| **L1** | `retained ++ archived == before`, scoped to the records zone | the primary byte-level detector; operand order is load-bearing (newest-on-top ⇒ retained first) |
| **L2** | front matter changed *only* by the declared pointer insertion, no line leaked into the shard | **the only** catcher for two of the nine mutants |
| **L3** | per-record identity, order, and byte-equality | names *which* record moved or was edited; classifies added vs absent |

**`--self-test` is the anti-vacuity gate, and it is the part I would defend hardest.** A green proof
tells you nothing broke; it does not tell you the proof *can* break. The canonical tool's own first
build printed three OKs while silently dropping a record, because it asserted over
`records[:k] ++ records[k:] == records` — an identity that can never fire. So every assertion here
runs on **re-parsed artifacts**, and the proof ships 9 mutants. **All 9 caught.** The self-test prints
*every* assertion that fires per mutant, not just the first, specifically so no reader concludes L3 is
an independent second opinion when L1 is doing the work.

#### Two operator decisions, both taken before any file was written

1. **Retention: through S217 (6 sessions, 1,014 lines).** **Measured after this close-out: 1,240
   lines** — 760 under the cap, ≈**4.1 sessions** of headroom at the observed 184 lines/session.
   (I predicted ~1,186; the close-out ran longer than modelled. Use 1,240, not the prediction.)
   Rejected 10 sessions (re-fires next session) and 4 (thin for Phase 3A, and puts the boundary
   beside the S218 duplicate stub).
2. **Shard location: `docs/architecture-history/`, not the fleet's `docs/archive/`.** Decisive
   evidence: all **328** of `enterprise-migration.md`'s grep-gate hits sit in the archived region and
   stay excluded by that plan's existing `^docs/architecture-history/` filter. **Delta zero, zero
   edits to a mid-execution plan**, one of whose occurrences is annotated *"do not narrow it."*
   `docs/archive/` would have created 328 new gate failures.

#### ⚠ What this does NOT establish

1. **The proof is a byte claim, not a judgement.** It says every byte of the pre-trim records zone is
   present, in the right file, unedited and in order. It says **nothing** about whether S217 was the
   right cut, whether the pointer text is accurate, or whether any record's content is true.
2. **The shard is 24,564 lines and *nothing watches it*.** `READ_CAP_WATCHED` is an exact-path set
   that does not contain it; it is not LOC-discounted and triggers no "large files" row. A future
   session that `Read`s it gets the exact silent truncation this session removed, relocated. The only
   guards are prose — the pointer block's second paragraph, the shard banner, and `CLAUDE.md`. **There
   is no automated catch. This is the deliverable's real residual risk.**
3. **Nothing was cleaned up.** Zero transform. The 5 duplicate zero-body stubs, the deliberate
   mojibake at old-line 7,901, the lone tab, all 20,335 non-ASCII characters — carried verbatim.
   Tidying them in the trim commit would have made "the move was verbatim" unfalsifiable.
4. **No `CHANGELOG.md` entry**, per `PROJECT_CONVENTIONS.md` §2's cadence gate: no `src/`, `packages/`,
   `scripts/` or `tests/` logic changed. ⚠ The convention-vs-precedent conflict S219/S220/S221 each
   flagged is now **un-asked for a fourth session** — S216 was measurement-only and *does* carry an
   entry. Worth an operator ruling.

#### Three commits, not one — and this is now a written rule

The trim commit contains **no record edit**, so the proof reports `added by the trim commit: 0` and
stays green permanently. This is not fastidiousness: **5 of the 20 proofs shipped across this
operator's fleet currently FAIL with zero data loss**, because the session bundled its own close-out
into the archive commit. This project's protocol *guarantees* that shape unless it is designed out —
Phase 1B and Phase 3 both write to the newest retained record. Hence claim / trim / close out as three
commits, recorded in `CLAUDE.md`.

### Session 221 Handoff Evaluation (by Session 222)

**Score: 6/10.** Among the best-*formed* handoffs in this series — its structure is the template I
imitated — but its ROI for *this* session was near zero, and it shares in a 202-session-wide blind
spot that this session's task existed to fix.

**What helped.** (1) **Gotcha 7 — "A green suite is not evidence a new tunable is pinned. Mutate the
default and re-run — that is how three of this session's defects were found."** This is the single
highest-ROI sentence I inherited, and it is *why this deliverable ships `--self-test` at all*. I was
building a proof with no test suite behind it; S221's gotcha is what turned "write the assertions"
into "write the assertions and then prove they can fail." Traceable, direct, load-bearing.
(2) **Learning #94 (price a filed remedy before executing it)**, which S221 coined, is exactly the
move that produced this session's governing finding — I priced "add a `LedgerSpec` for
SESSION_NOTES.md" and found the refusal was deliberate. (3) **The handoff's own form** — key files
with paths, numbered gotchas, explicit non-establishments — is what I copied above.

**What was missing — and it is systemic, not S221's alone.** The handoff offers five "what's next"
options. **None is the 25,562-line ledger that makes every session's `Read` of the continuity file
silently truncate**, and which was this project's *only* HIGH-risk dashboard row. Verified, not
asserted: `grep -icE "read cap|read-cap|2,?000-line"` over the entire 202-session archive returns
**2 hits, both inside the banner I wrote today**. Against **23** mentions of the HIGH-risk flag. So
for 202 sessions the flag was seen, reported, and never traced to its cause. S221 inherits a share of
that, not the whole of it.

**The irony worth recording.** The discipline that produces these handoffs — six mandatory elements,
explicit non-establishments, numbered gotchas — is precisely what grew the file past the cap.
Handoff quality and ledger readability were in direct tension for ~100 sessions and no session costed
it. The retention rule now in `CLAUDE.md` is the first thing that does.

**What was wrong:** nothing. No claim in S221's handoff that I exercised proved inaccurate.

**ROI: low for this session, through no fault of its content.** The operator pivoted outside its five
options. Its transferable value was two general-purpose disciplines, not any of its specifics.

### Phase 3B: Self-assess — Session 222 — 8.5/10

- **The +:** (1) **Read the tool before designing around it** and found the refusal was deliberate —
  the alternative (adding a `LedgerSpec` to canonical third-party material) would have been wrong on
  licence grounds *and* on design grounds, and it was the obvious first move. (2) **Shipped a proof
  that can fail, and proved it** — 9 mutants, all caught, with the per-mutant assertion breakdown
  printed so the proof cannot be over-read. (3) **Designed out the failure mode before hitting it**:
  the three-commit split was chosen from evidence (5 of 20 fleet proofs are red for exactly this
  reason) rather than discovered. (4) **Independently re-derived every load-bearing number** from the
  research pass — sha256, 25,578/4,153,325, 213 headings/208 ids, the cut at 1,015, and the byte sum —
  before writing a byte. (5) **Verified two things myself instead of asking**: mkdocs publish scope
  (fail-closed allowlist ⇒ no leak) and the `PROJECT_CONVENTIONS.md` licence question (`NOTICE` says
  12 files, the directory holds 13; `git log` shows in-project authorship). (6) **Corrected a
  predecessor's number rather than copying it** — the rename inventory's "644 hits across 50 files"
  was already low at filing time; `git grep` at `5d906e9` gives 659/50. (7) **Wrote down what the
  deliverable does not establish**, including a residual risk with no automated catch.
- **The −:** (1) **The shard's read-cap exposure is real and I mitigated it only with prose.** I moved
  a silent-truncation hazard rather than eliminating it; three warnings in three files is weaker than
  one line in `READ_CAP_WATCHED`, which lives in a file I do not own. I did not file a backlog item to
  close it properly — see "What's next" #1. (2) **L3's ORDER clause is never the sole catcher** in the
  self-test; L1 fires first on every reordering mutant. L3 earns its place by *naming* what moved, not
  by independent detection, and I only made that visible after a second pass. (3) **I let the research
  agents establish the anomaly inventory** (the 16 headless sessions, the 7 `should do` headings, the
  20B/20A ids) and verified rather than derived it — the same shape as S221's self-criticism #3.
  (4) **One avoidable round-trip**: `Path.read_text(newline=…)` is 3.13-only and failed on first run;
  a 10-second check of the interpreter version would have caught it. (5) **This close-out is ~150
  lines in the file I just trimmed** — I tightened it, but the tension named above is one I am also
  contributing to.

**Phase 3C note:** no workstream document was edited. `docs/methodology/workstreams/` is third-party
synced material (`NOTICE` §1, `CLAUDE.md`) and must stay byte-identical; learning **#95** went to
`PROJECT_LEARNINGS.md`, which `CLAUDE.md` designates as this project's learnings home, and rows
#35/#39/#42 were annotated. `PROJECT_CONVENTIONS.md` **was** edited — it is the one file in
`docs/methodology/` that is project-owned, verified before touching it. This is compliance with 3C,
not a skip.

**What's next — five options, all ungated:**

1. **Close the shard's read-cap exposure properly** (nothing filed yet — file it first). The shard is
   24,564 lines and no tooling watches it; the mitigation shipped today is prose in three files. The
   real fix lives in `methodology_dashboard.py`'s `READ_CAP_WATCHED` / the canonical trimmer, i.e.
   **upstream in `~/Development/methodology`, not here** — which makes it an operator call, not an
   implementer's. **Recommended first**, because it is the one thing this session knowingly left open.
2. **Re-measure `opencode` under the fixed harness** (`BACKLOG.md`) — S221's option 1, still the
   natural successor to the eval thread. **~$16.4, ~130 min, its own session.** Source `.env` first;
   quote `transient_retries` beside every rate; do not compare to S219/S220 numbers.
3. **Close the third and fourth transient policies** (`BACKLOG.md`) — the governance loop in
   `shadow_run.py:97-111` and the handler-less governance test. S221 recommended this *before*
   spending $16 measuring with the instrument.
4. **The `KeyError` guard** (`BACKLOG.md`) — shipped-package code, mirrors an existing intake
   convention, small and well-specified.
5. **The repository rename** (`BACKLOG.md`) — its inventory is now accurate post-trim (see the
   Session 222 note in that item). Read the three sub-decisions and five dragons first.

**Key files:**
- `docs/architecture-history/SESSION_NOTES-through-S216.md` — the shard. **`grep` it. Never `Read`
  it.** Its banner states what it holds and what was not altered.
- `docs/architecture-history/SESSION_NOTES-through-S216.md.verify.sh` — the proof. Run it before
  trusting anything about the archive; run `--self-test` before trusting the proof. Its header
  explains why four assertions replace one checksum.
- `CLAUDE.md` → "**`SESSION_NOTES.md` is trimmed (Session 222)**" — the retention rule, the
  three-commit rule, the declared grammar, and the two `SESSION_RUNNER.md` steps that need **no**
  override (14 and 18 — stated so nobody re-litigates them).
- `PROJECT_LEARNINGS.md` **#95** (refusal-as-specification + the four transferable rules); #35/#39/#42
  annotated.
- `docs/methodology/PROJECT_CONVENTIONS.md` §3 — the ledger-shard exception to "append-only logs do
  not move."

**Gotchas:**
1. **Three commits, always: claim → trim → close out.** A record edit bundled into a trim commit
   registers as an added record and holds the proof red forever *with zero data loss*. The proof
   treats `added != 0` as a **FAIL** (a deliberate divergence from the canonical tool, which
   downgraded it to a note because the canonical repo bundles by practice).
2. **The `^### Session .* ARCHIVED ACTIVE TASK` grep in Learnings #35/#39/#42 now returns EMPTY**
   against the live file. All **58** headings are in the shard. Empty output reads as "not found"; it
   means "moved." Do not re-create the zone.
3. **Shards are write-once.** The trim script aborts if the target exists. A second trim writes a new
   cut key; it never appends to `SESSION_NOTES-through-S216.md`.
4. **Do not borrow the canonical trimmer's *trigger*** — only its proof. At this file's ~184-lines-
   per-record density its stop condition is unsatisfiable at *every* retention depth including one
   record, so a trimmer using it would trim to empty and still report the trigger unmet. The rule in
   `CLAUDE.md` (fire above 1,500, cut to ≤1,050, floor of 4 sessions) is a level with hysteresis, and
   it is labelled as judgement.
5. **A record is a heading-delimited byte span, never a session.** 16 sessions have no heading at all,
   5 headings are duplicate zero-body stubs, one record swallows ten sessions. None of that is
   special-cased and none of it needs to be — but any future statement of the form "record N is
   Session N's work" is false, and was false before the trim too.
6. **Derive a cut index from a session id, never type a line number.** `KEEP_THROUGH` is the only
   tunable in the trim script; a hardcoded line number mis-cuts the instant a session is appended.
7. **Regenerating the proof is not free.** Its pointer block is lifted verbatim from the live file at
   generation time, so re-running the generator after the pointer changes would silently re-baseline
   L2. If the pointer text must change, change it *and* re-run `--self-test`.

### What Session 221 Did
**Deliverable:** **The SQL/QC retry asymmetry (gap #1c's other half) is FIXED. COMPLETE.** The sweep now
retries a transient before scoring it, under a **two-tier** policy that is deliberately *not* the
byte-for-byte mirror `BACKLOG.md` prescribed. **Plus** the operator's second ask: a BACKLOG item for
renaming the repository to `model_project_constructor`, filed with a live grep inventory.
**No threshold changed, no production code changed, `interview_sweep.py` is byte-identical, and NO
recorded verdict was re-scored — `opencode` stays NO-GO.**

**Started / Completed:** 2026-08-17. **Commits:** `5d906e9` (rename backlog item + Phase 1B stub),
`752e79b` (the fix), this close-out. **Trigger:** the operator picked S220's "what's next" option 1
and added the rename filing.

**Workstream:** `docs/methodology/workstreams/DEVELOPMENT_WORKSTREAM.md`. Its Phase 2 Step 3 ("read the
code you will modify — not the documentation, not the tests") is what produced the design fork below:
the BACKLOG's remedy reads fine and is wrong, and only tracing it against `eval_scoring.CapabilityRate`
shows why.

#### The design, and why it deviates from the filed remedy

| class | retried? | on exhaustion | why |
| --- | --- | --- | --- |
| `LLMParseError` (`_TRANSIENT_SCORED`) | 3 attempts | **scored a miss**, as before | the denominator must not shrink |
| `APITimeoutError` / `APIConnectionError` (`_TRANSIENT_EXCLUDED`) | 3 attempts | **excluded** + counted | no model output exists to judge |
| everything else, incl. `APIStatusError` | no | propagates | a real API/harness bug must surface (FM #18) |

`BACKLOG.md` specified *exclude on exhaustion*, mirroring `interview_sweep`. **That inverts the gate.**
Exclusion drops the sample while every survivor is clean by construction, so a provider failing 14 of 15
samples scores **1/1 = 100% and PASSES** a bar it fails 6.7% of today. At the S220-measured 1-in-60 rate,
three failures running is ~1-in-216,000 — so an exhaustion is never a transient in practice, it is
systematic, which is exactly what the gate exists to catch. The path is also the live tier's **only**
observation of live JSON emission (`shadow_run.py` hardcodes `json_parse` to 1.0). **The operator was
shown that arithmetic and chose this branch**; both fork questions went to them before any code was
written.

**The transport tier is new coverage, not a policy tweak.** `grep -rn "APIConnectionError\|APITimeoutError"
packages/data-agent/src/` → **0**. Before this, an SDK timeout in the SQL block propagated out and
**aborted the whole live run** — the hole S171 closed for `interview_sweep`, never applied here.

**Design B (exception subtypes in shipped code) was priced and rejected.** Blocked by
`tests/test_llm_json_parity.py:425`, which asserts pairwise `not issubclass` across seam error classes —
a subtype breaks it *by construction*, and its docstring calls that invariant "intentional and
load-bearing (plan §2.3)". It also cannot classify `opencode_client.py:284`, where an unset API key and a
genuine provider blip emit the same message. Blast radius: **18** raise sites (not the 9 the BACKLOG
claims — verified), 25 `IntakeLLMError` twins, 59 tests across 9 files.

#### Adversarial review found three real defects in my own code — all fixed pre-commit

18 agents, 14 claims, **11 refuted on evidence, 3 confirmed**, each reproduced by mutating the module,
not argued:

1. **`excluded` was last-attempt-wins.** A sample raising `LLMParseError` twice then timing out was
   **excluded** despite two observed model-quality failures. Measured: 6 observed parse failures across
   3 samples scored **0** misses and **PASSED** the 1.00 bar — the exact hole I rejected design A for,
   reintroduced through the back door. Now any scored failure beats an exclusion.
2. **`_MAX_TRANSIENT_RETRIES = 2` was unpinned.** Every retry test injected the bound, so mutating the
   default to 0 reverted **both** live call sites to S218 best-of-1 with 1187 tests green.
3. **`transient_retries` was unpinned** on the exhaustion path and across the whole QC seam.

All four mutants now die (verified by re-running each mutation). Tests 9 → 24.

#### ⚠ What this costs, stated because no diff will show it

**Best-of-3 turns a per-sample failure rate `p` into `p³` against unchanged bars.** A provider whose true
rate is 20% goes from a 3.5% chance of clearing `sql_parse` to **88.6%**. That is a real loss of
detection power, invisible in `eval_thresholds.py`. `transient_retries` is reported so the first-attempt
rate stays recoverable. **Post-fix numbers are NOT comparable with S219's or S220's best-of-1.**
Also: the gate now retries a class production retries **zero** times (`except LLMParseError` appears
nowhere in `packages/` — verified), and worst-case spend/wall-clock **triples** (30 calls → 90).

#### Four findings filed, deliberately not fixed

1. **Re-measure `opencode` under the fixed harness** (~$16.4, ~130 min) — its own session.
2. **Three blocks, three policies.** `shadow_run.py`'s governance loop is a *third* policy (no retry,
   scored a non-agreement against `GOVERNANCE_LAXER_MISSES_MAX = 0`, a zero-tolerance bar fed by an
   un-retried transient — the exact S219 shape), and `test_eval_live.py`'s governance test is a *fourth*
   (no handler; it aborts). The driver and the assertion gate disagree with each other.
3. **A bare `KeyError` aborts the whole sweep.** `anthropic_client.py:203-215` builds `PrimaryQuerySpec`
   from `item["name"]` etc. with no guard, so a well-formed array of wrong-keyed objects raises an
   exception no tier of the taxonomy catches. **The intake twin already guards this** at
   `intake/anthropic_client.py:439-440` — the fix mirrors a shipped convention.
4. **No circuit breaker** on a systematically-failing sweep; the retry made the worst case 3× worse.

#### The rename item (second deliverable, `5d906e9`)

Filed with a live inventory: **644 hits / 50 files**, counted **per grep pattern** (learning #8) because
each form has a different fix — wiki source path 509, wiki clone name 89, repo URL 35, Pages URL 25,
title-case prose 2, underscore form **0**. Exposed surfaces enumerated with line numbers; historical
records keep the old name per the S144 `SR 11-7 → SR 26-2` precedent (`bfd9f36`) and learning #32. Five
dragons, **two of which bite on the landing commit itself**: `publish_wiki.sh:72-75` is a guard that
greps for the literal old wiki-clone name (wiki publishing fails closed, via the post-commit hook), and
`SESSION_RUNNER.md:209` names the wiki path but is synced-from-canonical and must not be edited — that
correction belongs in `CLAUDE.md`'s adaptations seam.

**Phase 3C note:** no workstream document was edited. `docs/methodology/` is third-party synced material
(`NOTICE` §1, `CLAUDE.md`) and must stay byte-identical; learnings #92–94 went to `PROJECT_LEARNINGS.md`,
which `CLAUDE.md` designates as this project's learnings home. This is compliance with 3C, not a skip.

**CHANGELOG entry written** — unlike S219/S220 this session changed `tests/` test logic, which
`docs/methodology/PROJECT_CONVENTIONS.md` §2 gates an entry on. ⚠ **The convention-vs-precedent conflict
S219 and S220 both flagged is still unresolved** and now un-asked for a third session: S216 was
measurement-only and *does* carry an entry, while S219/S220 followed the written rule and did not. Worth
an operator ruling.

### Session 220 Handoff Evaluation (by Session 221)

**Score: 8/10.** The most operationally useful handoff in this series — one line in it prevented me from
shipping half a fix — but its recommended *remedy* was wrong on the branch that decides whether the gate
works, and I would have shipped an inverted gate had I implemented it as written.

**What helped:** (1) **"`sql_sweep.py:144-153` (primary-query handler) **and `:163-171` (the QC handler —
the BACKLOG entry named only the first; both need the fix)**."** The BACKLOG genuinely names only the
primary seam; implementing from it alone fixes half the bug. This single parenthetical is the highest-ROI
sentence in the handoff. (2) **"Read the fork before coding: A is a pure test-harness change; B needs new
exception subtypes in shipped `packages/` code."** Correct framing, and it let me price B in one pass
instead of discovering the blocker mid-implementation. (3) **"Add `{exc}` to `sql_sweep.py`'s two
`notify(...)` calls as part of it… this session proved that gap is real."** Cheap, specific, done.
(4) **"Thresholds must not move"** repeated in three places — the frame held all session. (5) **Gotcha 1
("Do not quote S220 as a GO… the recorded verdict is NO-GO")** was load-bearing for every `PHASE_E`
edit: my result *invites* a re-score and the gotcha is what kept the verdict untouched. (6) **Gotcha 6
("do not assume it was malformed JSON; the same type covers timeout and spawn failure")** is what made me
price a transport tier at all — without it I would have shipped the `LLMParseError` tier alone and left
the run-aborting hole open. (7) **The re-measure cost (~$16.4, ~130 min) and the $0.0593/call SQL-block
figure** transferred straight into the new BACKLOG item.

**What was wrong:** **the prescribed remedy inverts the gate.** `BACKLOG.md:241-243` specified
"exclude-with-note on exhaustion, and an `excluded_transient` count" — and exclusion on a 1.00 bar lets a
provider failing 14 of 15 samples score 1/1 and PASS. To S220's credit it *named* the cost ("converts a
genuine 'model emits garbage JSON three times running' into an exclusion") — but as one line of a
tradeoff, not as the gate inversion it is, and it then recommended that branch anyway. It also inherited
`interview_sweep`'s exclusion as validated precedent; that precedent is **unaudited** —
`grep -rn excluded_transient` finds exactly one non-test consumer, inside an assertion f-string that
never prints on a PASS. **Also wrong: "nine `LLMParseError` raise sites"** (S219's number, repeated by
S220). The real count is **18** — 10 in `anthropic_client.py`, 8 in `opencode_client.py` — which matters
because it is the denominator for pricing design B.

**What was missing:** (a) **That `sql_sweep` catches no SDK transport error at all**, so an
`APITimeoutError` aborts the entire live run. Findable in the file the handoff points at, in the module
whose retry policy is the subject, and it is a strictly larger hole than the one being fixed. (b) **That
`test_eval_live.py` passes no `on_event`**, which makes S220's own `{exc}` recommendation half-effective
— the notes it adds are discarded inside the assertion gate, the surface that most needs them.

**ROI: high.** The QC-handler pointer alone repaid the read; gotcha 6 produced the transport tier.

### Phase 3B: Self-assess — Session 221 — 8/10

- **The +:** (1) **Did not implement the filed remedy on autopilot** — priced it, found it inverts the
  gate, and put the arithmetic to the operator with the alternative before writing code. (2) **Both fork
  decisions went to the operator, pre-code**, with the numbers rather than a preference. (3) **Fixed both
  seams**, not just the one the BACKLOG names. (4) **Adversarially reviewed my own diff and found three
  real defects**, one of which reintroduced — through a subtle last-wins assignment — the exact hole I
  had rejected design A for. Every one was reproduced by mutation and every fix re-verified by killing
  the mutant. (5) **Measured the pre-change baseline directly** (stash → run → pop) instead of quoting
  the CHANGELOG's number, which would have been wrong (1175, not 1166). (6) **Wrote down what the fix
  costs** — the p→p³ shift, the production-divergence, the 3× worst-case spend — in the docstring, the
  CHANGELOG, the README and the report, rather than only what it buys. (7) **Refused to re-score the
  verdict** and tagged the two FAIL cells "pre-fix harness" instead.
- **The −:** (1) **The last-wins bug was mine**, and it is the *same class* of error as the one I had
  just spent the session arguing about — I reasoned carefully about which branch each class takes and
  then wrote a loop that only remembers the last one. Caught by review, not by me. (2) **I shipped the
  first draft with three mutation-survivable gaps**, including the default-bound one, which means my own
  test suite would not have noticed the fix being turned off. "24 tests, all green" was not evidence.
  (3) **I did not verify the "nine raise sites" figure before the workflow did it for me** — I carried a
  predecessor's number into my own planning for the first half of the session. (4) **The doc sweep found
  more stale sites than I would have found alone** (the `json_parse` escape-hatch paragraph in
  particular); left to myself I would have updated the obvious three files and missed it. (5) **I asked
  the operator two questions in one round-trip but only after ~20 minutes of analysis** — the transport
  question was answerable much earlier and could have been folded into an earlier check-in.

**What's next — five options, all ungated:**

1. **Re-measure `opencode` under the fixed harness** (`BACKLOG.md`). The natural successor: this session
   built the instrument and deliberately did not use it. **~$16.4, ~130 min, its own session.** Source
   `.env` first. Quote `transient_retries` alongside every rate, and do not compare the result to S219's
   numbers — different instrument.
2. **Close the third and fourth transient policies** (`BACKLOG.md`) — the governance loop in
   `shadow_run.py:97-111` and the handler-less governance test. **Recommended if you want the harness
   consistent before spending $16 measuring with it**, since the governance keys are the ones with a
   zero-tolerance bar. `_call_with_retries` is already generic over the call; note the transient *tuples*
   cannot be shared.
3. **The `KeyError` guard** (`BACKLOG.md`) — shipped-package code, mirrors an existing intake convention,
   small and well-specified.
4. **`tests/eval/README.md` drift** — now a **seventh** session unfixed. S220's verified locations
   (`:49`, `:51-52`, `:86`) still stand; this session added a new "Transient-failure policy" paragraph
   nearby but deliberately did not touch the stale ones. Cheap, $0.
5. **The repository rename** (`BACKLOG.md`, new) — read its three sub-decisions and five dragons first;
   sub-decision 3 recommends splitting it into two sessions.

**Key files:**
- `tests/eval/sql_sweep.py` — `_TRANSIENT_SCORED` / `_TRANSIENT_EXCLUDED` / `_TRANSIENT_ERRORS` and
  `_call_with_retries`. **The module docstring carries the full rationale, including what the fix costs.
  Read it before changing the policy.**
- `tests/eval/test_sql_sweep.py` — 24 tests. `test_the_default_retry_bound_is_what_the_live_call_sites_get`
  and the two `test_mixed_class_exhaustion_*` tests exist because mutants survived without them.
- `tests/eval/PHASE_E_AGREEMENT_REPORT.md` §"Update — Session 221" — what the fix does and the six things
  it does **not** establish. **Read before quoting any verdict.**
- `BACKLOG.md` — four new items plus the amended auth-diagnosability item and the rename item.
- `PROJECT_LEARNINGS.md` #92 (accumulate, don't last-win), #93 (pin the default), #94 (price a filed
  remedy before executing it); #86's Source cell amended with what closing it revealed.

**Gotchas:**
1. **Do not quote any post-S221 SQL/QC number against S219's or S220's.** Best-of-3 vs best-of-1 —
   different instrument. Report `transient_retries` beside every rate.
2. **`opencode` is still NO-GO.** The fix did not re-score anything; the two FAIL cells are tagged
   "pre-fix harness" precisely so nobody reads them as current.
3. **`_MAX_TRANSIENT_RETRIES` is the only knob the live gate actually uses** — both call sites omit the
   keyword. It is pinned by exactly one test; if you change it, that test is the one that should fail.
4. **Exclusion is one-directional by design:** any `LLMParseError` among a sample's attempts makes it
   scored, whatever landed last. Do not "simplify" that back to reading the final exception.
5. **`interview_sweep.py` must stay byte-identical** unless the session owns re-validating the recorded
   interview numbers. This session did not touch it.
6. **The retry cannot pass `previous_error`** — it would inject "Return corrected SQL this time" and turn
   `sql_parse` into a repaired-query metric behind an unchanged 1.00 bar. `functools.partial` binds a
   zero-argument call to make that structurally impossible; a test pins it.
7. **A green suite is not evidence a new tunable is pinned.** Mutate the default and re-run — that is how
   three of this session's defects were found (learnings #92, #93).

