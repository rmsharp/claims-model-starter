# Are the ledger budgets worth what they cost?

**Status:** ANALYSIS — options presented, nothing ruled, nothing re-tuned, no prose corrected.
**Session:** 248, 2026-08-26, at `b95c39e`. Per the operator assignment recorded at `c6aa37b` and filed
as `BACKLOG.md:62`. **Deliverable:** this document (`SESSION_RUNNER.md` FM #18 — the plan is the
deliverable; every repair named below is a *proposal*).

**How to read the numbers.** Each figure is tagged **[M]** measured by a command I ran this session,
**[W]** measured by a delegated sweep and spot-checked by me, or **[C]** claimed in existing prose and
**not** re-derived. Reproduction commands are in Appendix A. This convention is not decoration: the
defect this project self-reports more than any other is a numeral typed instead of derived
([#105](../../PROJECT_LEARNINGS.md), #146, #148, #152, #154, #186), and a document arguing about that
failure must not commit it.

---

## 0. The verdict

The assignment said to derive the load-bearing premise before arguing either side. I did, and it is
false — but the *interesting* result is not that it is false. It is that correcting it dissolves the
problem the budgets were invented to solve, and replaces it with a smaller, sharper one.

> **`CLAUDE.md:81` sets the trim trigger at "1,500 lines (75% of the 2,000-line agent read cap)".
> Measured: the cap is not 2,000 lines. It is 25,000 TOKENS, truncation is announced in full, and the
> rest of the file stays addressable.** A 3,000-line file came back whole [M]. A 101-line file was cut
> at line 10 [M]. `SESSION_NOTES.md` was cut at line 744 of 1,702, with the banner *"PARTIAL view …
> (48549 tokens, cap 25000) … Do NOT answer from this page alone"* [M].

**The structural consequence, which no session in this lineage has stated.** Truncation is *ordered*:
it delivers the file from the top down. The ledger is newest-on-top. So **what a `Read` delivers is
determined by the size of the front matter plus the newest few records — not by the length of the
file.** Appending a thousand more lines at the bottom would not change that by one byte.
**How many records that is has since been re-measured downward — see §12, which was written after this
document was first committed and corrects it to ONE.**

**Trimming the tail therefore does nothing for the problem the trimming exists to solve.** The
quantity that actually binds is the front matter — which is the one thing the apparatus itself
manufactures, at an accelerating rate (+19, +19, +36, +48, +58, +61, +72, **+87** lines per trim [M]).

Three further results, each independently requiring a ruling:

1. **The retention rule is already unsatisfiable.** `{target ≤ 1,050} ∧ {floor ≥ 4 records} ∧ {measured
   density ≈ 235 lines/record}` is an **empty constraint set** [M/W]. No cut of the file today
   satisfies both target and floor. **The ninth trim cannot be run compliantly without a ruling.**
2. **The value is at trim time, not in normal operation** — and the first draft of this document got
   that wrong in the challenge's favour. An **untouched ancestor** proof, re-run unchanged after its
   trim, has caught a real defect **zero** times, and that is *structural*: every shard proof resolves
   its prose operands from its own trim commit, so only `L7`/`L9`/`L10`'s disk reads can ever fire.
   **But the inherited set, run against a NEW cut, has genuinely gone red on real defects** [M] —
   `L6` at Session 231 (three builder/proof drifts; learning #127 says *"Only the plain run showed the
   failure"*) and `L12` at Session 245 (*"the shard went 785 → 792, and four files still said 785"*,
   `SESSION_NOTES.md:1013`). **That is where the enforcement lives, and it is not nothing.**
3. **Eight defects sit live at HEAD right now, with all nine proofs green and 25/25 census tests
   passing** — including one where the live ledger and the proof's own pinned literal *agree with each
   other and are both wrong* about how many assertions that proof has, and one that is a genuine **code**
   bug inside a frozen proof, unrepairable (§6, point 3).

**And the defence is stronger than any previous session has argued it**, on two points that the
challenge cannot dismiss and that Session 247's framing missed entirely:

- **The founding data-loss event is real, documented, and I read it** [M]:
  `~/Development/methodology/starter-kit/methodology_trim.py:19-21` — *"The manual procedure this
  replaces proved whole-file byte identity under concatenation, and that proof passed while a paragraph
  was silently lost (`020ba3f` — the pre-v3.0 scope footer of the root CHANGELOG, still missing
  today)."* The apparatus is a response to an observed failure in which **the naive proof passed**. That
  is not paranoia, and it is the reason `L0`–`L3` are record-scoped rather than whole-file.
- **The ledger is not starving the product, because there is no product work to starve.** All six
  pipeline steps exist and are wired end to end — 53 modules across intake UI, intake agent, data agent,
  website agent and orchestrator [M] — at **1,338 passing tests and 97.98% coverage** [C, S247]. The
  product is **feature-complete and awaiting adoption**, and `gh issue list` is empty by design until
  UAT. "Zero product sessions in 22" is real [W] but it is *not* evidence of crowding out.

**Recommendation.** Not "keep", not "abandon". **Split the apparatus in two and fund the halves
differently:** keep the losslessness core (`L0`–`L3`), which answers to an observed failure; stop paying
the per-trim tax on the description layer (`L4`–`L14`), which has never caught anything in normal
operation and mostly polices prose the trims themselves generate. Then **replace the file-length target
with a front-matter budget**, which is the constraint that actually binds. Options in §8;
I would rule for **A + D + E, then F**.

---

## 1. The premise, measured

### 1.1 The probes

Five, this session, this harness (Claude Code, Opus 5 1M-context, macOS, 2026-08-26), all read-only.
**Probes C and E deliberately break the `grep`-never-`Read` rule** — that violation *is* the
measurement, and it is the only way to test the rule's own justification. [M for all five]

| # | file | shape | result |
|---|------|-------|--------|
| A | `probe_lines.txt` | 3,000 lines / 21,000 B | **returned whole.** The documented "up to 2000 lines by default" **did not bind** |
| B | `probe_bytes.txt` | 101 lines / 199,700 B | **cut at line 10.** `PARTIAL view … lines 1-10 of 101 total (199405 tokens, cap 25000)` |
| C | `SESSION_NOTES.md` | 1,702 lines / 128,972 B | **cut at line 744 (43.7%).** `(48549 tokens, cap 25000)` |
| D | `SESSION_NOTES-S241-through-S239.md` | 792 lines / 57,269 B | **returned whole**, no marker |
| E | `SESSION_NOTES-through-S216.md`, `offset=24586 limit=4` | 24,590 lines / 4,074,951 B | lines 24,586–24,589 returned exactly — **the last line of the largest shard is directly addressable** |

### 1.2 What they establish

- **The binding limit is tokens, not lines.** A 3,000-line file passed; a 101-line file did not.
- **Truncation is loud.** It reports the partial view, total lines, total tokens, the cap, the exact
  pagination call to make next, and an instruction not to answer from the page alone. The repository
  asserts the exact opposite in six live places (§1.4).
- **Nothing is unreachable.** Probe E addresses line 24,589 of a 24,590-line file. The live ledger is two
  `Read` pages; the largest shard is ~62 (**derived** from the measured 2.657 B/token ratio of the
  identical corpus — not separately measured, and labelled so).
- **Documentation and behaviour disagree, and behaviour wins.** The `Read` tool still documents "up to
  2000 lines by default". A delegated sweep read that sentence and concluded the premise "still holds";
  probe A falsifies it directly. *Recorded because it is this document's own subject matter happening in
  real time: a quoted document beat a measurement until the measurement was run.*

### 1.3 The consequence that matters: truncation is ordered

Probe C's 744 delivered lines are not a random 44% — they are the **first** 744: the entire front
matter (283), this session's claim stub (9), Session 247's complete record (304), and 148 lines of
Session 246's. That is every byte `SESSION_RUNNER.md` Step 14 asks a session to read (`## ACTIVE
TASK` → newest record), plus the previous session's full handoff, which Phase 3A requires.

**So the invariant worth protecting is not "the file fits in one `Read`". It is "the front matter plus
the K newest records fit in one `Read`", and K is the working context a session actually needs** — 2 by
Step 14 and Phase 3A, 3 if you honour [#162](../../PROJECT_LEARNINGS.md) ("two-records-back is not
archaeology; it is still live context").

**At the moment probe C ran, K = 2 was satisfied and K = 3 was not.** ~~That is the operative figure.~~
**SUPERSEDED within the hour, by this session's own close-out — see §12.1. The measured value is now
K = 1.** The original reading is left visible because *how* it went stale is the finding.

Total file length does not appear in that sentence. **Trimming the tail cannot change it; only shrinking
the front matter can.** The precise budget should be *measured by probe*, not computed from a line
count — per-section token density differs, and "derive, don't declare" is this project's own rule. §12.1
does exactly that and prices every region in tokens.

### 1.4 Evidence-based inventory of the false premise

Required by `SESSION_RUNNER.md`'s planning checklist, because correcting it is a text migration. Two
claim families: the cap's **value** and its **silence**. [M]

| | cap-value | silence | files |
|---|---:|---:|---|
| **Live, repairable** | 8 | 6 | 5 |
| **Frozen — write-once, pinned by `L9`/`L10`, unrepairable** | 11 | 32 | 16 |
| **total** | **19** | **38** | **21** |

Six sites in four files assert it as fact — the actual repair set:

| site | text |
|---|---|
| `CLAUDE.md:81` | `**1,500 lines** (75% of the 2,000-line agent read cap)` — **the retention rule's own rationale** |
| `BACKLOG.md:50` | `silently stops at 2,000 lines — no error, no marker` |
| `BACKLOG.md:62` | `nothing has re-derived that cap since Session 222` — *this item; now answerable* |
| `BACKLOG.md:465` | `truncates at 2,000 lines with no error and no missing-data marker` |
| `PROJECT_CONVENTIONS.md:73` | `past the 2,000-line agent read cap is silently truncated on every Read, with no error and no missing-data marker` |
| `SESSION_NOTES.md:277` | `an agent Read stops at 2,000 with no error and no marker` |

`tests/test_session_notes_census.py:336` and `:361` name the phrase inside the guard's `FROZEN`
allowlist and must be re-matched if the wording changes, or the companion staleness test fires.
`SESSION_NOTES.md:185` and `:1519` **quote frozen banner text inside historical records and must not be
repaired.** One false positive: `docs/wiki/model_project_constructor/Changelog.md:32` is about LLM
`max_tokens`.

**The 43 frozen occurrences can never be corrected.** They join the six stale shard banners the project
already documents as permanently-false-but-unrepairable — so a correction must say so explicitly in the
live copies, or the next reader will trust a banner.

### 1.5 Honest limits

- **One harness, one day.** Session 222's harness may genuinely have had a 2,000-line cap, and the tool
  *documentation* still says so — the figure was not invented, and what is now false is that the cap is
  *silent* and that 2,000 *lines* is operative. **The correction should therefore state the method, not
  the number**: "re-run Appendix A" is durable where "25,000 tokens" is not.
- The cap governs one call, not a session. The real cost of exceeding it is **one extra announced tool
  call** — not data loss.
- A marker is a mitigation, not immunity: an agent that ignores it still answers from 44% of the file.

---

## 2. The budgets in the unit that binds

| budget | as declared | in tokens [M, 28.53 tok/line] | vs the 25,000-token cap |
|---|---|---|---|
| agent read cap | 2,000 lines | **25,000 tokens ≈ 876 lines** | 1.00× |
| trim trigger | > 1,500 lines | ≈ 42,800 | **1.71× — fires long after the cap is breached** |
| trim target | ≤ 1,050 lines | ≈ 29,950 | **1.20× — a compliant post-trim file still truncates** |
| retention floor | ≥ 4 records | — | — |
| record density | ~184 lines/record [C] | **203–235 measured, window-dependent** [M/W] | — |

Post-trim totals: 1,033 / 707 / 826 / 840 / 901 / 843 / **1,050** / **1,014** [M]. The last two land
above 876 lines. **The system's success state has been a file that still truncates** — which matters
less than it sounds, per §1.3, and that is the point.

---

## 3. The retention rule is already infeasible

### 3.1 All three inputs have moved

**Front matter at each trim commit** [M — `git show <sha>:SESSION_NOTES.md`]:

| | pre | T1 S222 | T2 S224 | T3 S228 | T4 S231 | T5 S235 | T6 S239 | T7 S242 | T8 S245 | collapse S246 | HEAD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| lines | 8 | 27 | 46 | 82 | 130 | 188 | 249 | 321 | 408 | **283** | 283 |
| delta | | +19 | +19 | +36 | +48 | +58 | +61 | +72 | **+87** | **−125** | 0 |

Monotonically accelerating; a fit gives `Δk ≈ 9.83k + 5.75`, last three averaging **+73.3** [W]. The
collapse returned exactly 125 lines — **1.7 trims of headroom.**

**Density has roughly doubled** [M]:

| era | records | lines/record |
|---|---:|---:|
| S216 shard (Sessions 216→1) | 206 | **119.2** |
| the six S221–S241 shards | 21 | **231.2** |
| live file, 6 closed records | 6 | **234.8** (median 241.5) |
| `CLAUDE.md:81`'s claim [C] | — | **~184** |

The ~184 entered at `a9510ca` (Session 222) and **has never been re-derived in the 26 sessions since**
[W]. It reconstructs as the mean of the nine newest substantive pre-first-trim records (183.56 [W]) —
true once. **No window of this ledger measures 184 today.** For retention arithmetic the right window is
the records a cut would *retain* — the closed live records, 234.8.

### 3.2 The constraint set is empty

`1,050 − 283 = 767` lines of record headroom; `767 / 234.8 = 3.27` → **the target admits three records.
The floor is four.** [M]

| retain | at claimed 184 | at measured 234.8 | verdict |
|---:|---:|---:|---|
| 4 | 1,019 | **1,222** | over target by 172 |
| 5 | 1,203 | **1,457** | over target by 407 |
| 6 | 1,387 | 1,692 | over the *trigger* |

**Not a projection — the cut available today** [M]. Floor-4 record lines available: S248 stub 9 +
S247 304 + S246 253 + S245 252 = **818**. The landing depends on the front matter *after* the cut, and
**every trim adds its own pointer block inside the trim commit** (S245: fm 321 → 408 across
`9330203`→`4ab6306`), so 283 is a lower bound, not the figure:

| front matter assumed | landing | over the 1,050 target by |
|---|---:|---:|
| 283 — no growth at all (lower bound, counterfactual) | 1,101 | **51** |
| 356 — last three trims' average, +73 | 1,174 | **124** |
| 377 — fitted `Δk ≈ 9.83k + 5.75`, +94 | 1,195 | **145** |

**Every row is over, and the 818 counts a 9-line stub as one of the four.** The largest cut landing
≤1,050 retains three records and violates the floor.

**Front matter cannot be collapsed far enough to rescue it.** Floor-5 under the target needs
`fm ≤ 1,050 − 5(234.8) = −124` — **negative** [W]. Floor-4 needs `fm ≤ 110.7`; the three uncollapsed
pointer blocks measure **96 + 72 + 56 = 224** lines against the collapsed table's **51 lines for five
trims** [M], so folding all three would land fm near 90 — achievable **once**, and undone immediately by
the next trim's own block. **The collapse mechanism is exhausted as a route to a
higher floor.**

### 3.3 The target has never been met by four *complete* records

Every historical post-trim total complies — and each counts the trimming session's own Phase-1B stub as
one of the four [W]. Trim 7 retained spans `8, 225, 249, 247`; trim 8 retained `6, 170, 231, 199`. Trim
8 landed at 1,014 with a **6-line** S245 stub; that stub is **252 lines** today, so the same four
records now total 1,260 — **210 over target, before Session 246 existed.**

**`L11/target` is evaluated at exactly the moment that makes it pass.** Not gaming — Session 239
recorded both readings ([#156](../../PROJECT_LEARNINGS.md)) — but the rule has been measuring something
other than it appears to for at least two trims.

### 3.4 Consequence

`SESSION_NOTES.md` was **1,701 lines against a >1,500 trigger** when this section was written and is
**1,924** now [M] — this document's own close-out record added 223 of them, which is §12.1's point. The
ninth trim is due and **cannot be compliant.** Its only moves are to violate `L11/target`, violate `L11/floor`, or edit `CLAUDE.md`'s
numbers so `L11` follows the new declaration — which `L11/figure` permits by design and which is
precisely the re-tune this session is forbidden to make. **A ruling is on the critical path.**

---

## 4. The cost

### 4.1 Sessions

Sessions 216–247, every record located and read [W, spot-checked]:

| window | ledger-apparatus sessions |
|---|---|
| all 32 | **10** (31%) — 222, 224, 228, 231, 235, 239, 242, 245, 246, 247 |
| last 20 | **8** (40%) |
| last 10 | **5** (50%) |
| longest consecutive run | **3** — S245→246→247, and it is the *current* run |
| product/pipeline sessions since S225 | **0 of 22** |

**That last line must not be read as crowding out, and §6.1 explains why.** Those 22 sessions are 8
ledger and **14** other [W, corrected on adversarial re-derivation — the first two trims fall in the
*earlier* era, so the recent-era ledger share is 8/22 = 36.4%, not 45.5%]. The 14 were the
five-phase repository rename, the wiki-publishing fix campaign, the tutorial-site repair and two
convention rulings — real infrastructure. Borderline calls in Appendix B.

### 4.2 Artifacts

| | lines [M] |
|---|---:|
| eight shard proofs (305 / 409 / 802 / 1,142 / 1,441 / 1,592 / 1,942 / 2,174) | 9,807 |
| collapse proof | 1,129 |
| census guard `tests/test_session_notes_census.py` | 921 |
| **machinery** | **11,857** |
| eight shards (24,590 / 804 / 933 / 790 / 976 / 1,057 / 644 / 792) | 30,586 |
| live ledger | 1,701 |
| **guarded data** | **32,287** |

Assertion/mutant growth per trim: 4/9 → 5/15 → 8/28 → 10/50 → 12/59 → 13/68 → 14/84 → 15/95, plus
C0–C7 with 46 and the guard's 7 checks with 17 — **471 mutants** [W].

**Two framings, and the denominator decides the argument.** Machinery : live ledger = **6.97 : 1**.
Machinery : all guarded data = **0.37 : 1**, one proof line per 2.72 ledger lines — unremarkable
overhead for verified data. The sharpest formulation [W]: **framing B is right about what is *verified*;
framing A is right about what is *read* — nothing reads the shards, so the working cost is borne against
a 1,701-line file.**

Two notes the defence is entitled to: **7,633 of the 9,807 shard-proof lines are superseded ancestor
copies** kept only because `L9`/`L10` enforce write-once — a storage cost, not a maintenance cost;
recurring authorship is ~2,200 lines per trim, not 11,857. And **280 of the live ledger's 1,701 lines
(16.5%) are apparatus prose**, not session records [W] — the machinery is inside the thing it measures.

---

## 5. The defence, at full strength

The operator asked that this side be argued at least as hard. Two of its strongest points were never
made in the framing that prompted this session.

**1. The founding failure is observed, not hypothetical — and the naive proof passed.** [M, quoted from
`~/Development/methodology/starter-kit/methodology_trim.py:19-21`]

> *"The manual procedure this replaces proved whole-file byte identity under concatenation, and that
> proof passed while a paragraph was silently lost (`020ba3f` — the pre-v3.0 scope footer of the root
> CHANGELOG, still missing today)."*

Moving a paragraph from the live file into the shard is *exactly byte-preserving under concatenation*,
so the whole-file check **had** to pass. That passage credits `L1` (concatenation identity scoped to the
records zone), `L2` (zone pinning) and `L3` (per-record partition) by name — **the record-scoped core is
exactly what that loss bought** — and it is a complete
answer to "you have never lost anything, so why bother": the loss happened, in a sibling repository,
under the check the sceptic would have accepted. **Caveats stated plainly:** it was a different repo, a
manual procedure, a weaker proof, and a single event — but it is real, and it is the only genuine
data-loss event in the lineage.

**2. The ledger is not displacing product work, because the product is finished.** [M] All six pipeline
steps exist and are wired: intake UI (4 modules), intake agent (13), data agent (16, its own package
and `pyproject.toml`), website agent (13), orchestrator (7) — 53 modules, with `STAGE_ORDER`, halt paths
and checkpoint resume. 1,338 passing tests at 97.98% coverage [C]. `gh issue list` is empty **by design
until UAT**. The opportunity-cost argument in §6 is therefore much weaker than the raw session census
makes it look, and Session 247's report did not say so.

**3. Losslessness is proven, not asserted.** 30,586 lines in write-once shards, byte-verified, with 471
mutants proving the proofs can fail. Most projects' "we archived the old notes" is an unverified claim.

**4. The work has been this project's R&D lab for verification discipline.** 74 of 206 learnings [M]
use trim/shard/proof/assertion vocabulary, and several are general and have transferred: *compose, don't
compare*; *a mutant that cannot reach an assertion is a green lie*; *derive the number, never type it*;
*a working-tree assertion is safe iff its subject is immutable*. Session 241 applied the mutation
discipline to `scripts/publish_wiki.sh` and it caught **four real code defects in a fix whose own subject
was fail-open bugs.**

**5. The apparatus detects the one thing that would really destroy the archive.** `L9` and `L10` read
the **working tree** — unlike every prose assertion, which reads its own trim commit. Deleting or
relocating a shard or an ancestor proof is caught unconditionally [W]. That is a narrow guarantee, and
it is a real one.

**6. The ledger demonstrably compounds.** The last six handoffs scored 9, 9, 9, 9, 8, 9 [C]; three
consecutive sessions converted a predecessor's what's-next into a deliverable within three exchanges.
This session's assignment, scope and central question came from Session 247's handoff.

### 5.1 Where the defence does not reach

- **"A plain run catches regressions *in normal operation*."** It does not. An untouched ancestor
  proof, re-run unchanged between trims, has caught a real defect **zero** times [W, re-derived: all
  nine `*.verify.sh` exit 0 today on a tree this session has already edited], and §6 point 2 shows why
  that is structural rather than lucky. **The correct claim — which is stronger than "zero" and which
  this document's first draft got wrong in the challenge's favour — is that the inherited set fires at
  TRIM TIME, against the new cut.** Verified instances [M]: `L6`/S231 (three builder-vs-proof drifts;
  learning #127 — *"Only the plain run showed the failure"*), `L12`/S245 (*"the shard went 785 → 792,
  and four files still said 785"*). Two more caught their own authors on a new assertion's first run
  (`L12`/S239 twice; `L13`/S242 — *"the pointer block said 'eight sentences' while …"*). Two were false
  positives (`b3`/S231 first run; `b3`/S235 on a correct trim). **So: the apparatus is inert between
  trims and live during them.**
- **"Truncation is a data-integrity failure *here*."** No trim has risked loss, and it is checkable:
  **the pre-trim ledger is byte-recoverable from git at all eight trims** [M — 25,578 / 1,462 / 1,681 /
  1,530 / 1,761 / 1,786 / 1,561 / 1,648 lines, each with a stable sha256]. Every trim's losslessness was
  also reconstructed independently of its own proof, by sha256 [W]. **The proofs guard against a botched
  shard going *undetected*, not against data being *lost*.**
- **"S242 found 15 defects."** [C] — **not re-derivable** [W]. No per-finding list exists in the ledger,
  the proof, `CHANGELOG.md` or `PROJECT_LEARNINGS.md`; the record's table has 5 rows and its self-found
  section 3 bullets; `SESSION_NOTES.md:1676` implies 12 while `PROJECT_LEARNINGS.md` #178 says "11 of the
  15". Reconstruction reaches 11–15. **S246's "six" *is* re-derivable.** A headline defence statistic is
  itself an underived number.

---

## 6. The challenge, at full strength

**1. Zero catches between trims, in 26 sessions** (§5.1). The apparatus is inert except during the
few hours a trim is uncommitted. Whatever it is worth, **it is not worth it continuously** — which is
an argument about *cadence and packaging*, not about deleting it.

**2. The proofs are blind to prose the moment a trim commits.** Every shard proof resolves its prose
operands from its own trim commit. Corrupt `CLAUDE.md`'s census, `BACKLOG.md`'s,
`PROJECT_CONVENTIONS.md`'s or the live routing clause and **all nine stay green**; only editing an
ancestor shard on disk turns them red [C, S246/S247 — consistent with my own green run today on an
edited tree].

**3. Eight defects are live at HEAD with everything green.** I verified each [M]:

| # | site | says | measured |
|---|---|---|---|
| 1 | `CLAUDE.md:87` | collapse proof ships **36 mutants** | **46** `M`-labels; the proof's own header says 46 |
| 2 | `CLAUDE.md:87` | assertions **C0–C6** | **C0–C7** (8 `def C…`); `README.md:136` says C0–C7 and is right |
| 3 | `CLAUDE.md:58` | live file holds the newest **4** sessions | **7** record headings |
| 4 | `CLAUDE.md:81` | **~184** lines/record | **234.8**; no window measures 184 |
| 5 | `SESSION_NOTES.md:256` | *"lettered **C0–C6**"* | same error, second copy |
| 6 | `…pointer-collapse.verify.sh:395` | *"lettered **C0–C6**"* — **inside the pinned `NEW_TABLE` literal** | same error, third copy |
| 7 | `…S238-through-S236.md.verify.sh:1792` [W] | *"the six an adversarial review forced"* | **seven** mutants (M78–M84) follow. Unrepairable — `L10` pins it |
| 8 | `…S235-through-S232.md.verify.sh:1548` | `if any(f.startswith("L1") for f in fails)` | a **code** bug, not prose: the prefix also matches `L10`–`L14`. Learning #177; shipped by S239, found by S242 three sessions later, **live and unrepairable today** |

**#5 and #6 together are the most instructive result in this document.** `C1` pins `NEW_TABLE` against
the live front matter — so **the two copies agree with each other and are both wrong**, while `C6`
checks only the five table rows and the block's opening line. That is Session 235's learning #140,
*"two copies agreeing is not verification"*, reproduced verbatim **inside the proof written to prevent
it**, and green today.

**4. Most defects the apparatus finds are defects the apparatus created.** The reviews that found six
(and reportedly fifteen) defects found them in the trim's *own newly written* front-matter prose —
prose that exists only because the trim wrote it. Each trim adds ~73–87 lines of count-carrying text,
and the next assertion exists to police it. **The value is real; the workload is endogenous.**

**5. The parameters are self-defeating.** Front matter grows superlinearly and density has doubled —
*both* because each session's record now documents the previous session's proof machinery.

**6. The cheap mechanism is *most* of the yield — but not all of it, and the gap is instructive.**
Session 239 shipped **no** adversarial review; an arm-level neuter loop and a careful read of its own
program's output found four defects at a fraction of the cost of Session 235's 97-agent, ~7.0M-token
review [W]. **But it also missed one** — the `startswith("L1")` prefix bug in its own proof (row 8
above), which survived three sessions until Session 242's review found it and is unrepairable today
[M]. **So the cheap loop is high-yield and not sufficient**, which is a real argument against Option F
in its strongest form and is recorded here rather than smoothed over.

### 6.1 Where the challenge overreaches

- **"7:1 machinery to data"** picks the flattering denominator; against everything verified it is 0.37:1.
- **"11,857 lines to maintain"** is wrong: 7,633 are frozen ancestors that need only keep passing.
- **"Ledger work crowds out the product"** is **refuted** — the product is feature-complete and awaiting
  UAT (§5, point 2). This was the challenge's most rhetorically effective claim and it does not survive.
- **"Zero catches means zero value"** is a non-sequitur, and §5 point 1 gives the counterexample the
  whole design answers to.
- **"The read cap is avoidable by discipline"** is true but weaker than it sounds: the discipline is
  `grep`, never `Read`, and this session broke it twice deliberately. A rule that must be broken to be
  tested is a rule people break.

---

## 7. What is settled, and what is not

**Settled** — the cap's unit and loudness, and that truncation is ordered so file length is the wrong
invariant (§1); that the retention rule is currently unsatisfiable (§3); that the apparatus is inert
between trims and live during them (§5.1); that git makes loss impossible *here* (§5.1); that seven live
prose errors coexist with a fully green apparatus (§6, point 3); that the product is not being starved
(§5).

**Not settled** — the counterfactual. Nobody can measure how many bad cuts *did not happen* because a
proof was going to run. Prevention-by-construction is unfalsifiable in both directions, and `020ba3f`
shows the failure mode is real while showing nothing about its rate here. Any ruling is a judgement
about how much to pay for an unmeasurable good. **That judgement is the operator's, which is why this
document stops at options.**

---

## 8. Options

Independent unless noted. **Cost** in sessions. "Breaks" cites the mechanism.

| | option | mechanism | buys | breaks / costs |
|---|---|---|---|---|
| **A** | **Correct the premise** | Rewrite the 6 live sites (§1.4) to state measured behaviour **and the method**; record that 43 frozen occurrences stay wrong, as the stale banners do. | Removes a false foundation from the rule's own rationale; makes `BACKLOG.md:62` answerable. | ~⅓ session. `L11/declared`+`L11/figure` read `CLAUDE.md:81`'s exact sentence, so the **next** trim's proof must declare the new text. The guard's `FROZEN` strings at `:336`/`:361` must be re-matched or the staleness test fires. |
| **B** | **Raise the target** to ≥1,225, keep floor 4 | One numeral; `L11` follows. | Makes the ninth trim legal now. | ~1 session. **Buys ~one trim**; density growth re-breaks it. Bounded below by `283 + 4(234.8) = 1,222`. |
| **C** | **Lower the floor** to 3 | One numeral. `283 + 3(234.8) = 987` fits. | Cheapest legal cut. | A session sees two predecessors plus itself. **Buys ~one trim.** |
| **D** | **Replace the file-length target with a FRONT-MATTER budget** — *the option §1.3 implies* | Declare the invariant as *"front matter + the K newest records must return in one `Read`"*, K = 3, **verified by probe** rather than computed. Retire the total-length target and trigger, or demote them to housekeeping. | **Targets the constraint that actually binds.** Immune to record-density growth and to file length. Ends the §3.3 stub artefact. Makes "the rule went infeasible" impossible. | ~1 session. Requires accepting that the live file grows without bound between (much rarer) trims. `L11` must be rewritten to compose from a probe, and needs its own mutant. |
| **E** | **Collapse-on-write** | Every trim writes its pointer block **as a table row**, never as prose; the trim's rationale lives in that session's record instead. | Kills the growth driver at source: measured at HEAD, the collapsed table costs **51 lines for five trims (~10/trim)** against **96 / 72 / 56** for the three surviving prose blocks (~75/trim) [M]. Makes D's budget durable. | ~1 session for the mechanism, ~free after. Relocates rationale into records, which are themselves trimmed — arguably correct, but the saving is a *relocation*, not a deletion. Needs a `C`-series extension. |
| **F** | **End the assertion-per-trim convention** | New assertions on **evidence of a real gap**, not on schedule. Anything that must hold *between* trims goes in the always-on CI guard — the only artifact that reads the working tree. | Converts a trim from a full session to a fraction. Keeps the mechanism that actually fires — the inherited set run against each new cut (§5.1) — and drops the one that has only ever caught its own author. | ~0 to declare. **Loses the forcing function behind most of the adversarial-review yield, and §6, point 6 shows the cheap substitute is high-yield but NOT sufficient** — it missed a code bug that is live and unrepairable. `L15` is already named and deferred on the record; F is the decision not to build it. **The one option I list as *consider*, not *rule for*.** |
| **G** | **Cap record length** (~120–150 lines) | Detail moves to `PROJECT_LEARNINGS.md` or a per-session file. | Density is the master variable and doubled unlegislated (119 → 235). Roughly halves the cadence at zero apparatus cost. | **In direct tension with `SESSION_RUNNER.md:180`** — handoffs are scored and *"write notes that would earn a 9 or 10"*; the 9s and 10s **are** the long ones [W]. Risks damaging the one thing that demonstrably works. |
| **H** | **Stop trimming; let the file grow** | Delete trigger/target/floor; keep existing shards. | Now *defensible* rather than reckless: truncation is announced, ordered, paginable; git guarantees recoverability; §1.3 shows length does not affect what a `Read` delivers. | Leaves eight shards and nine proofs as orphaned history, and abandons `L9`/`L10`'s live guarantee (§5, point 5) as the archive stops being maintained. Effectively D without the front-matter discipline — **and the front matter is the part that actually binds.** |

**Rejected on mechanism, not taste** [W]:

- **Raise the floor to 6 or 8.** Floor 6 needs target ≥ 1,692; floor 8 needs 2,162 — impossible under
  any cap-derived ceiling.
- **Trim on a size *rate*.** `CLAUDE.md:81` already records the canonical rate rule as unsatisfiable at
  this density; at the measured 234.8 it is *more* so. A re-scaled rate rule is degenerate — the file's
  whole dynamic range is `(2000 − 283)/234.8 ≈ 7.3` records. **[Session 249 — annotated, not rewritten]** that arithmetic takes 2,000 lines as the ceiling, which §1 of this document falsifies. The rejection stands on the degeneracy argument rather than on the figure; **recompute before citing the 7.3.**
- **Move retired records out of the repository.** `L9`/`L10` read the working tree, so relocation is the
  one change this apparatus detects unconditionally; retiring them discards the losslessness guarantee
  that is the defence's strongest asset. The wiki is public, a separate objection.

---

## 9. Recommendation

**Rule for A, then D, then E, and consider F — as four separate sessions. Decline B and C as one-trim
patches. Decline G. Decline H.**

**The organising idea: split the apparatus and fund the halves differently.**

- **The losslessness core (`L0`–`L3`) answers to an observed failure** in which the naive proof passed
  (`020ba3f`). **Keep it, unconditionally.** It is cheap, it is finished, and it is the part with a real
  counterexample behind it.
- **The description layer (`L4`–`L14`) has caught nothing in normal operation**, is blind to the prose
  it guards the moment a trim commits, and mostly polices text the trims themselves generate — while
  seven errors sit live at HEAD with all of it green. **Stop paying a per-trim tax on it** (Option F),
  and put anything that must hold between trims in the CI guard, which is the only thing that reads the
  working tree.

**Why A first.** The rule's stated rationale is false and everything downstream inherits it. It is the
cheapest item and blocks nothing — do it first so the next ruling is made on true premises.

**Why D over B and C.** B and C each buy exactly one trim and guarantee this conversation recurs. D
changes *which quantity is governed*, from a number that does not affect what a session reads to the one
that does. It is the only option that makes "the budgets went stale" structurally impossible.

**Why E with D.** D sets a front-matter budget; E is what keeps it. Measured, prose blocks cost six times
what table rows cost. Without E, D's budget is breached by the next trim's own pointer block.

**Why F is narrow, and why that matters.** F ends the mandate to invent a *new* assertion at every
trim. **It does not stop running the inherited set against each new cut** — and §5.1 shows that is
precisely where the real catches happened (`L6`/S231, `L12`/S245). So F keeps the mechanism that
demonstrably fires and drops the one that has only ever caught its own author. The genuine cost is that
the assertion-per-trim convention is also the forcing function behind most of the adversarial-review
yield — and §6, point 6 now cuts **both** ways: Session 239's cheap loop found four defects for a tiny
fraction of the cost, **and missed a code bug that is still live and unrepairable.** That is why F is the
one item I list as *consider* rather than *rule for*. **If the operator is unwilling to decouple review
discipline from trims, decline F and accept the cadence** — that is coherent, and on this evidence I
would not argue against it.

**Why not G.** It is the highest-leverage untried lever and I am declining it on the strongest available
counter-evidence: the handoffs that score 9 and 10 are the long ones, and handoff quality is the
mechanism that demonstrably compounds. Legislating record length would be scored as a regression by the
very system that produces the records.

**Why not H.** The ledger is the one mechanism here that demonstrably compounds; abandoning maintenance
strands 30,586 verified lines and gives up `L9`/`L10`'s unconditional deletion guarantee. H is right only
if the operator concludes the compounding is not worth one session in three — which the evidence does
not force.

**What I am least confident about.** The counterfactual (§7). If prevention-by-construction is doing
most of the work, F is wrong and the cadence is the price of the discipline. I cannot measure it, and I
have not pretended to.

---

## 10. Here be dragons

1. **`L11` follows the declaration.** Changing `CLAUDE.md:81`'s numerals makes the next trim's proof
   legal by construction — by design, but it means **a budget can be re-tuned silently by editing
   prose.** Record any ruling in `CHANGELOG.md` or `PROJECT_CONVENTIONS.md`, not only in `CLAUDE.md`.
2. **Option A perturbs `L11`'s declared literal**, which the next trim's proof must carry forward.
   Sequence A **before** the ninth trim, never during it.
3. **The census guard's number-words cap at 16** [M — `SPELLED`/`ORDINAL`,
   `tests/test_session_notes_census.py:113-124`]. **A seventeenth shard raises `KeyError`.** At ~1 shard
   per 3 sessions that is ~27 sessions away, and it is a one-line fix — but it is a latent hard failure
   nobody has filed.
4. **The guard goes red at the ninth trim by design** and prints the exact replacement sentence per
   claim. Update prose first, then re-run. It is **not** a shard proof: the
   `for f in docs/architecture-history/*.verify.sh` loop does not run it.
5. **The guard scans only `CLAUDE.md`, `README.md`, `BACKLOG.md`, `PROJECT_CONVENTIONS.md`** [M —
   `PROSE_FILES`, `:104`]. `SESSION_NOTES.md` is **not** scanned. Editing `BACKLOG.md` near shard
   vocabulary trips it; that is the design.
6. **Probes C and E deliberately break `grep`-never-`Read`.** Re-running Appendix A is read-only and
   safe; do not let the technique leak into ordinary work.
7. **`grep` here is a `ugrep --ignore-files` wrapper.** `command grep` or `git grep` for every count.
8. **`SESSION_NOTES.md:185` and `:1519` quote frozen banner text.** They look like repair targets. They
   are not.
9. **Density figures move under you.** Everything in §3 was measured at `b95c39e`. Re-derive at Phase 0 —
   this document's whole subject is figures that were true once.

---

## 11. Completion criteria, per option

Each is **one session**. Close out when its criterion passes. Do not bundle.

- **A — premise corrected.** DONE = the 6 sites state measured behaviour + method; the frozen count is
  stated in the live copies; `uv run pytest tests/test_session_notes_census.py` green; all nine
  `*.verify.sh` green. VERIFY: `git grep -n '2,000-line agent read cap'` returns only frozen paths and
  the guard's allowlist.
- **B / C — one numeral.** DONE = `CLAUDE.md:81` updated, ruling recorded outside `CLAUDE.md`, and a
  worked simulation in the record showing the next cut satisfies target ∧ floor. VERIFY: rerun §3.2.
- **D — front-matter invariant.** DONE = `CLAUDE.md:81` states the K-newest-records invariant; a probe
  script demonstrates it holds at HEAD; `L11` rewritten to compose from the probe, with its own mutant.
  VERIFY: `--self-test` catches every mutant **and** the new arm is not deletable with the suite green.
- **E — collapse-on-write.** DONE = the ninth trim's pointer block is a table row; front matter measured
  at the trim commit is ≤ the declared budget; `C`-series extended with a mutant.
- **F — convention ended.** DONE = `CLAUDE.md`'s trim bullet no longer requires a new assertion per trim
  and states what replaces the review forcing function; `L15`'s deferral is recorded as a decision, not
  a backlog item. VERIFY: prose only.
- **G — record budget.** DONE = declared in `PROJECT_CONVENTIONS.md` with the overflow destination named,
  **and** an explicit note reconciling it with `SESSION_RUNNER.md:180`. VERIFY: measure the next three
  records against it.

---

## Appendix A — reproduction

```sh
# read-cap probes (read-only; C and E deliberately Read files the rules say to grep)
awk 'BEGIN{for(i=1;i<=3000;i++) printf "L%05d\n", i}' > /tmp/probe_lines.txt
awk 'BEGIN{pad=sprintf("%*s",1990," "); gsub(/ /,"x",pad);
          for(i=1;i<=100;i++) printf "B%05d%s\n", i, pad}' > /tmp/probe_bytes.txt
#   Read each with DEFAULT parameters; record whether a PARTIAL-view marker appears and where it cuts.

# density, front matter, record spans
command grep -n '^### What Session .* Did$' SESSION_NOTES.md   # spans between consecutive hits
command wc -l SESSION_NOTES.md

# front-matter growth
for s in a9510ca 07e1ab9 e4ca944 f3fea4e a7512cb 28879a0 e7d5b03 4ab6306 2b8c9c9; do
  git show $s:SESSION_NOTES.md | command grep -n -m1 '^### What Session .* Did$'; done

# git recoverability of every pre-trim state
for s in a9510ca 07e1ab9 e4ca944 f3fea4e a7512cb 28879a0 e7d5b03 4ab6306; do
  git show $s^:SESSION_NOTES.md | command wc -l; done

# the premise inventory
git grep -n -E '2,?000-line (agent )?read cap'
git grep -n -E 'no error,? (and )?no (missing-data )?marker|truncates in silence|stops at 2,000'

# the live prose errors
command grep -c '^def C[0-9]' docs/architecture-history/SESSION_NOTES-pointer-collapse.verify.sh   # 8
command grep -o '"M[0-9]\+ ' docs/architecture-history/SESSION_NOTES-pointer-collapse.verify.sh | sort -u | command wc -l   # 46
command grep -n 'C0–C6' SESSION_NOTES.md docs/architecture-history/SESSION_NOTES-pointer-collapse.verify.sh CLAUDE.md
command grep -c '^### What Session .* Did$' SESSION_NOTES.md   # 7

# the founding precedent
sed -n '17,30p' ~/Development/methodology/starter-kit/methodology_trim.py

# the apparatus, plain-run
for f in docs/architecture-history/*.verify.sh; do bash "$f" >/dev/null && echo "green $f"; done
uv run pytest tests/test_session_notes_census.py -q
```

## Appendix B — classification notes

- **Session 236** is classified `docs_or_methodology_other` (stated deliverable: a verified push) though
  its only content commit corrected ledger-apparatus prose. Reclassifying makes all-32 = 11 and
  last-20 = 9; last-10 and the longest run are unaffected.
- **Session 240**'s 23 re-pointed archive banners sit under `docs/architecture-history/` but are template
  boilerplate across 20 unrelated documents, not shard apparatus.
- **Session 238** produced no deliverable; classified by the work it claimed.
- **Session 224 (trim 2) fired at 1,448 lines — below the 1,500 trigger** [W]. It predates `L11`
  (Session 235). A finding, not an accusation.
- **`SESSION_NOTES.md:877` says the front matter "is now 397 lines" while `:871` in the same record says
  408** [W]; measured 408 at `4ab6306`. Frozen in a record, not repairable.
- **Session 247's handoff calls the `post-merge` hook "the oldest unblocked backlog item"** [C]. Measured
  [W]: the oldest unblocked item is *"The gate measures only ONE of the three dialect-injected prompts"*,
  `BACKLOG.md:204`, filed Session 217/218. Minor, and orthogonal to this analysis.


---

## 12. Addendum — what a completeness critic found after this document was committed

This section was added at `97fc164`+1, after an adversarial completeness pass over the committed
document. **It corrects four claims and adds four findings.** It is appended rather than folded in
because *when* each figure went stale is the document's own subject.

### 12.1 The headline measurement was stale before the ink dried — because of this document

`SESSION_NOTES.md` was 1,701 lines when §1.3's probe ran. Writing this session's close-out record took
it to **1,924 lines / 145,307 B ≈ 54,688 tokens — 2.19× the cap** [M]. A default `Read` now returns
**lines 1–748 of 1,925**, and line 748 sits **inside Session 247's record**, in the middle of the
OPERATOR ASSIGNMENT's budget table [M].

> **K = 1, not 2.** One `Read` of the live ledger delivers the front matter, this session's record, and
> ~233 of Session 247's 304 lines. **Everything after is beyond the horizon — including the paragraph
> naming the evidence this session was told to gather, the "argue both sides" block, the "bias to
> correct for" warning, and all nine of Session 247's gotchas** (among them `command grep`, which this
> document calls load-bearing in every count it published).

**The instruction that shaped this session is now outside the one-`Read` window of the file that carries
it, and the session that put it there is this one.** That is the strongest available demonstration of
§1.3's thesis and the sharpest possible instance of the defect this document diagnoses.

### 12.2 Region costs, measured in tokens — and Option E is worth ~7×, not ~2×

§2 converted budgets using one whole-file average and never measured a region. Measured by reading an
N-fold-duplicated copy and dividing the reported total [M]:

| region | lines | tokens | % of the 25,000 cap |
|---|---:|---:|---:|
| **front matter** | 283 | **8,578** [M] | **34.3%** |
| — 8th-trim pointer block | 96 | 2,915 | 11.7% |
| — 7th-trim block | 72 | 2,192 | 8.8% |
| — 6th-trim block | 56 | 1,761 | 7.0% |
| — collapsed 1st–5th table | 51 | 1,654 | 6.6% |
| Session 248 record | 232 | **6,360** [M] | 25.4% |

**A prose pointer block costs 2,289 tokens per trim; a collapsed table row costs 331 — a factor of
6.9.** §8 prices Option E in *lines* (96/72/56 vs 51, ~2×) and therefore **understates it by more than
three-fold.** E is the highest-leverage item in the table, not the third.

### 12.3 Three more files are over the cap, and the fleet watch is aimed correctly but measures lines

The document probed only `SESSION_NOTES.md`. The protocol mandates others [M]:

| file | lines | ~tokens | vs cap | line-based watch says |
|---|---:|---:|---:|---|
| `SESSION_NOTES.md` | 1,924 | 54,688 | **2.19×** | fine (< 2,000) |
| `BACKLOG.md` | 768 | 25,212 | **1.01×** — already truncating | fine |
| `PROJECT_LEARNINGS.md` | 219 | **104,629** | **4.19×** | fine |
| `CHANGELOG.md` | 1,607 | **241,418** | **9.66×** | fine |

`~/Development/methodology/tools/methodology_dashboard.py:287-289` sets
`READ_CAP_WATCHED = frozenset(("SESSION_NOTES.md", "CHANGELOG.md", "HANDOFFS.md") + _BACKLOG_LOCATIONS)`
and fires on `w["lines"] > READ_CAP_LINES` with `READ_CAP_LINES = 2000`. **`CHANGELOG.md` is watched, is
9.66× the real cap, and reports fine.** The instrument is pointed at the right files and measuring the
wrong quantity — this document's thesis, one directory over, unstated until now.

**`PROJECT_LEARNINGS.md` is the sharpest case:** `CLAUDE.md:101` directs every session to read it; it is
4.19× the cap, mean line length 1,264 B, and has **no budget, no trim rule, no shard, no proof and no
watch.** A default `Read` delivers roughly a quarter of it. **A ruling on the ledger budgets that ignores
this file has fixed the smaller problem.**

### 12.4 `CLAUDE.md` is over the budget it cites, and the overage is entirely this apparatus

`CLAUDE.md` is **25,997 B** against the *"~200 lines / ~25 KB"* budget its own line 101 cites as the
reason `PROJECT_LEARNINGS.md` was extracted [M]. Lines 77–89 — the trimmed-file section — are
**17,060 B, 65.6% of the file**, injected into **every** session before any file is opened. Measured at
each trim commit, `CLAUDE.md` grew 9,822 → 25,997 B (**+165%**) while non-apparatus content went from
9,822 to 8,937 — **essentially 100% of its growth since Session 222 is the ledger apparatus.** §4 counts
storage the apparatus barely pays and omits the only cost paid *every session*.

### 12.5 Two more live defects — the count is ten, not eight

| # | site | says | measured |
|---|---|---|---|
| 9 | `CLAUDE.md:82` | the dashboard's `READ_CAP_WATCHED` *"is an exact-path set containing none"* | it contains **`SESSION_NOTES.md`**. True of the *shards* only; false as written |
| 10 | `CLAUDE.md:101` | `CLAUDE.md` is kept *"within its size budget (~25 KB)"* | **25,997 B** — over the budget in the sentence that cites it |

### 12.6 Corrections to my own arguments — three, all against my conclusions

- **§6 point 4 ("most defects the apparatus finds are defects the apparatus created") is measurably
  false for a substantial subset.** Four counter-instances, none trim-generated: Session 231 found
  `BACKLOG.md`'s `924` where the shard measures 933; Session 245 found `README.md`'s *"+17 others"*
  where `git ls-files` measures 19; Session 246 found `README.md`'s census off by one; Session 247 found
  `README.md`'s per-directory test counts stale by 131. **The trim is the only scheduled
  whole-repository consistency audit this project has, and it repeatedly finds defects in files it did
  not write.** That is a defence point and I under-argued it.
- **§6.1's "crowds out the product is refuted" is too strong — "weakened" is right.** Feature-complete is
  not the same as no work: **nine code/harness defects filed between Sessions 218 and 225 are untouched**,
  and the last commit to `src/` or `packages/` is Session 223's `2733df0`. Two are severe on their face —
  a bad `--db-url` yields `Status: COMPLETE`, exit 0, all project files generated **with every quality
  check silently unexecuted**; and a systematically-failing sweep can burn *"~7.5 hours of billed
  nothing"*.
- **§5 point 5 omits its one real caveat: the proofs are not automated.** `.github/workflows/ci.yml` runs
  `ruff`, `mypy` and `pytest` — **no `.verify.sh`**. `L9`/`L10`'s working-tree guarantee holds only when a
  session remembers a 2.8-second loop. **The fix is one CI line**, and it belongs in whatever is ruled.
- **And "the apparatus is inert between trims" is true of the `L`-series but false of the apparatus as of
  Session 247** — `tests/test_session_notes_census.py` runs on every push, reads the working tree, and is
  a direct descendant of the trim discipline. §5.1 under-credits this repository's newest artifact.

### 12.7 Where §1.3 proves too much, stated plainly

If truncation is ordered and what a `Read` delivers is fixed by the front matter plus the newest
records, then **no trim ever fixed a `Read` problem** — Session 222's 25,578-line ledger delivered the
same top-of-file content a 1,033-line one does. Taken seriously, §1.3 retroactively voids the stated
justification for all eight cuts, and therefore for the 30,586 shard lines and 10,936 proof lines §5
point 3 defends. **That cuts against Option H's dismissal as much as it cuts for Option D**, and the
document asserted the reframing without following it there. It is followed here.

**Net effect on §9's recommendation:** unchanged in order (**A, then D, then E, consider F**) but **E
rises sharply** on §12.2's re-pricing, **D must be widened** to cover `PROJECT_LEARNINGS.md`,
`BACKLOG.md` and `CHANGELOG.md` (§12.3), and **one CI line adding the proof loop** should be bundled
into whichever option is ruled first (§12.6).
