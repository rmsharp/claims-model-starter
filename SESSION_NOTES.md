# Session Notes

**Purpose:** Continuity between sessions. Each session reads this first and writes to it before closing out.

**Archived Sessions 216 → 1 — 206 record headings, 24,564 lines** into
[`docs/architecture-history/SESSION_NOTES-through-S216.md`](docs/architecture-history/SESSION_NOTES-through-S216.md)
— same format, same newest-on-top order, frozen, byte-for-byte unedited. This live file holds
Sessions 222 → 217 only.

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
not by authorship:** Session 216's own handoff evaluation stayed here, inside Session 217's record,
because this file files an evaluation under its author. Expect that seam at every trim boundary.

---

## ACTIVE TASK

### What Session 222 Did
**Deliverable:** Lossless trim of `SESSION_NOTES.md` (25,562 lines, past the 2,000-line agent read
cap — the dashboard's HIGH-risk driver for this project) (IN PROGRESS)
**Started:** 2026-08-17
**Status:** Session claimed. Work beginning.

**Pre-flight finding (recorded here in case this session dies):** the canonical ledger trimmer
`methodology_trim.py` **refuses this file by design.** Its `LEDGERS` table has exactly two entries —
`CHANGELOG.md` and `HANDOFFS.md` — and the dashboard's own comment (`methodology_dashboard.py:360-366`)
states that `READ_CAP_WATCHED` is deliberately wider, "including SESSION_NOTES.md", and that "the
trimmer answers NO_CONFIG on every one of those by design ('there is deliberately no generic fallback:
a generic rule is what would mis-zone a differently-shaped ledger')." So the remedy here is a
project-owned trim that **borrows the trimmer's proof discipline** (L1 concatenation identity scoped to
the records zone, L2 zone pinning, L3 per-record partition by identity+order+bytes), not the trimmer
itself. The tool is also not installed in this repo (it is in 5 sibling projects).

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

### What Session 220 Did
**Deliverable:** **The `opencode` SQL-block variance probe. COMPLETE. The transient that produced the
S219 NO-GO did NOT reproduce in 45 fresh samples; all three failing cells measure 100% at a 3.4× larger
denominator.** **The recorded verdict was deliberately NOT re-scored — `opencode` stays NO-GO.**
**No harness change, no threshold change, no production default change.**

**Started / Completed:** 2026-08-02. **Commits:** this close-out (documentation-only — see "No CHANGELOG
entry" below). **Trigger:** the operator asked what open item #1 actually proposed, then chose "run probe
1st" — S219's "what's next" option 2.

**Workstream:** `docs/methodology/workstreams/AUDIT_WORKSTREAM.md` — measurement against a fixed standard,
as for S216/S218/S219. Its Phase 2 order (define criteria → inventory scope → **read the implementation** →
challenge scope) is what produced the A-vs-B fork below: reading `sql_sweep.py` and `interview_sweep.py`
side by side is what showed the two modules argue *opposite* rationales for the same failure class.

#### The result

| repeat | `sql_parse` | `sql_exec` | `qc_structural` | transients | calls | cost | wall |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 35/35 | 35/35 | 15/15 | 0 | 30 | $1.779 | 17.8 min |
| 2 | 33/33 | 33/33 | 15/15 | 0 | 30 | $1.788 | 19.5 min |
| 3 | 34/34 | 34/34 | 15/15 | 0 | 30 | $1.773 | 16.1 min |
| **pooled** | **102/102 = 100%** | **102/102 = 100%** | **45/45 = 100%** | **0** | **90** | **$5.341** | **53.4 min** |

**Zero transients in 45 samples.** Rule of three bounds the per-sample rate at **≤6.7% (95% confidence)** —
exactly the rate S219 observed at 1/15. Pooled across both sessions: **1 event in 60 samples (1.7%)**.
So a **~1-in-60 blip decided a recorded cutover verdict.** That is an argument *for* the retry-asymmetry
fix, not against it.

#### What was deliberately NOT done

**The verdict was not re-scored.** Three of eight cells is a diagnostic, not a gate run — S217's own
precedent (*"the probe is a diagnostic, not a re-score"*). A 100%/100%/100% result on precisely the cells
that failed is the most tempting possible moment to flip a verdict, and flipping it from a partial sweep
is how a gate stops being a gate. **`opencode` remains NO-GO. Do not quote this section as a GO.**

#### ⚠ The probe could NOT attribute the S219 event — half its purpose went unmet

It was instrumented specifically to capture `str(exc)`, which `sql_sweep.py:146-148` discards (it logs
`type(exc).__name__` only), so a recurrence could be traced to one of the nine `LLMParseError` raise
sites. **No recurrence ⇒ no attribution.** Whether S219's event was transport (timeout / spawn / non-zero
exit / no-assistant-text) or genuine malformed JSON is **still unknown** — and that is exactly the
distinction the retry fix's design fork turns on. I framed the probe as able to resolve that fork; it could
only ever have done so on a recurrence, and I should have said so up front.

#### Two findings filed in `BACKLOG.md`

1. **An unset `ANTHROPIC_API_KEY` scores as 45 model-quality failures.** The first probe attempt returned
   **0/45 on all three thresholds in 36 s at $0**. Cause: `opencode auth list` holds **0 credentials**, and
   the client shells out with **no `env=`** (`opencode_client.py:174`), so `ANTHROPIC_API_KEY` from `.env`
   is the only way an `anthropic/…` model authenticates. Unauthenticated it exits 1 with
   `UnknownError: Unexpected server error … (ref=…)` — naming neither auth nor the variable. The harness
   scores that **identically** to a provider that cannot write SQL.
2. **The retry-asymmetry item now carries the probe data and an explicit A-vs-B implementation fork**
   (retry the whole `LLMParseError` class, mirroring `interview_sweep`, vs. retry only the transport subset
   and keep real JSON-parse failures as misses — the latter needs new exception subtypes in **shipped**
   `packages/` code). `sql_sweep.py:38-43` argues for today's behaviour **deliberately**, so the fix
   overturns a documented decision; the rationale is that the exception type is too coarse to carry the
   policy, not that S218 was careless.

#### Cost model corrected

**The SQL block costs $0.0593/call — 1.9× `opencode`'s global mean of $0.0318.** Nobody had isolated this
before. Estimating SQL-block spend from the global mean understates it by ~47%. Also: **SQL-block latency
p50 27.7 s, p90 62.6 s, max 233.6 s**, against S219's whole-corpus p50 7.7 s / max 129.1 s — the tail lives
in this block, and its max is **1.8× the worst figure S219 recorded**. No §3.4 threshold can see it.

**Spend: $5.341 against a ~$3 estimate (78% over).** The void first run cost $0. Both the 3-repeat scope
and the overrun were put to the operator with costed options — the overrun mid-run, at repeat 1, before the
remaining two-thirds were spent.

### Session 219 Handoff Evaluation (by Session 220)

**Score: 8/10.** The best pre-designed experiment any handoff in this series has left: option 2 specified
the scope, the repeats, *and what each outcome would mean* before I read a line of code. Marked down for a
cost/time estimate that was wrong by 5-7× on wall clock, and two omissions that each cost real time.

**What helped:** (1) **Option 2 as a designed experiment**, not a suggestion — "re-run the SQL block alone
two or three times… if it never recurs, the finding is 'one transient decided a gate'; if it recurs at
~1-in-15, that is a provider-reliability signal in its own right." That is the deliverable, pre-specified,
including the interpretation of both branches. (2) **Key files naming `sql_sweep.py:144-153` and
`interview_sweep.py:82-87,152-180` with "diff these two."** Doing exactly that is what surfaced the A-vs-B
fork and the fact that the two modules argue opposite rationales — the single most useful thing I learned.
(3) **The scratchpad pointer to `full_sweep.py`** — it survived, and I reused its `Meter` and
`install_opencode_meter` verbatim. Saved ~20 minutes and a class of metering bugs. (4) **Gotcha 8
(`last_usage["cost"]`)** meant the meter was right on the first try; the $0.0593/call finding exists
because of it. (5) **Gotcha 6 (`PYTHONPATH=.`)** — correct, applied from the first command. (6) **Gotchas 1
and 2** ("do not quote the GO"; "equally, do not quote the NO-GO as a quality finding") kept me from
mis-stating the verdict in *either* direction — load-bearing, because my result is exactly the kind that
invites a premature re-score.

**What was wrong:** **option 2's estimate, "~$1, ~7 min."** Actual: **$1.78 and 17.8 min per repeat**, and
option 2 called for two or three of them — so **$3.6–5.3 and 36–53 min**, 5-7× the quoted wall time. The
error was applying `opencode`'s whole-corpus p50 (7.7 s) to a block whose calls are the heavy ones, when
S218 had **directly measured this same block at 16.8 min**. S219 had diagnosed that exact confusion in
S218's "2× slower" claim *in the same document*, then reproduced it in its own recommendation. It
propagated into my quote to the operator before I caught it.

**What was missing:** (a) **No pointer that an `opencode` run needs `.env` sourced.** Gotcha 5 discusses
`.env` and says what it does *not* supply, while S219's own driver docstring shows
`set -a && . ./.env && set +a` applied to **both** stages. One clause — "the CLI has no stored credentials;
it inherits `ANTHROPIC_API_KEY`" — would have prevented a void run. This is the same shape as the omission
S219 docked S218 for. (b) **No pointer that `sql_sweep.py` logs only the exception type and discards the
message.** S219 quoted that WARN line verbatim in three documents and never noted that it cannot attribute
the failure — the single most important fact for the successor task, found only by reading the source.

**ROI: high.** The pre-designed experiment and the reusable metered driver were worth more than the wrong
estimate cost.

### Phase 3B: Self-assess — Session 220 — 8/10

- **The +:** (1) **Caught S219's estimate error before spending** and re-quoted to the operator, rather
  than inheriting it — the exact failure S219 committed against S218. (2) **Self-tested the instrument at
  $0 (14/14) before spending**, including a *transparency* check proving the observer changes nothing the
  sweep sees, so these numbers are comparable with S219's. (3) **Did not touch the committed sweep** — the
  probe observes by wrapping the runner, so `sweep_sql_capabilities` ran exactly as the gate runs it.
  (4) **Refused to re-score the verdict** on a result that invites it — the most important call in the
  session and the tempting one to get wrong. (5) **Surfaced the 78% cost overrun mid-run, at repeat 1**,
  with options, instead of continuing silently or quietly truncating to 2. (6) **Converted the void run
  into a filed finding** — it cost $0 and produced the auth-diagnosability defect. (7) **Asserted a
  stray-SDK meter at 0**, so "nothing billed a second provider" is measured rather than assumed.
- **The −:** (1) **The void run was my error** — I inferred from S219's gotcha 5 that `.env` was
  *unnecessary*, when the gotcha only said what `.env` does not supply, and S219's own driver docstring
  showed the opposite. The correct information was in a file I had already read. (2) **I repeated the
  estimate error I had just corrected**: fixed S219's latency-from-global-mean, then projected *cost* from
  the global mean and came in 78% over. Caught at repeat 1, not before spending. (3) **I over-promised the
  attribution.** I told the operator the probe "answers the A-vs-B fork that item #1 cannot currently
  answer" — true only on a recurrence. A null result was always the likely branch and I should have said
  what it would and would not settle. (4) **No `anthropic` control arm.** ~$0.5 would have said whether the
  1-in-60 is provider-specific; S219's 0/15 is a weak existing control and I never considered adding one.
  (5) **Polled the background run four times** when the completion notification alone was sufficient; two
  of those checks returned nothing new.

**No CHANGELOG entry, deliberately.** `docs/methodology/PROJECT_CONVENTIONS.md` §2 gates an entry on
changing shipped code (`src/`, `packages/`, `scripts/`) or `tests/` **test logic**. This session changed
neither — the probe driver is scratch-only and nothing under `tests/` was modified. ⚠ **The convention vs.
precedent conflict S219 flagged is still unresolved** (S216 was measurement-only and *does* carry an
entry). Second session running to follow the written rule. Still worth an operator ruling.

**What's next — five options, all ungated:**

1. **Fix the SQL/QC retry asymmetry** (`BACKLOG.md`). **Recommended** — the probe was explicitly its
   precondition, and the item now carries the 1-in-60 rate plus the A-vs-B fork spelled out. **Read the
   fork before coding: A is a pure test-harness change; B needs new exception subtypes in shipped
   `packages/` code.** Add `{exc}` to `sql_sweep.py`'s two `notify(...)` calls as part of it, so the next
   occurrence is self-attributing — this session proved that gap is real. **Thresholds must not move.**
   The `opencode` re-measure that follows is a *separate* session (~$16.4, ~130 min).
2. **Bundle the auth-diagnosability defect with option 1** — same class (the harness cannot distinguish a
   seam failure from a quality failure), and both touch the same two `notify` lines.
3. **`tests/eval/README.md` drift** — now unfixed for a **sixth** session. **Verified this session, and the
   precise locations differ from how S219 described them:** `:49` is the heading
   *"## Live baseline (measured — harness not yet trustworthy)"*, false since S219 closed that arc
   (`anthropic` now clears all eight); `:51-52` still says the live Anthropic baseline "were deferred (no
   credentials)", stale since S165; and the paragraph at `:86` says the §3.4 thresholds "remain
   **proposed**" and lists **SQL executability** and gap #1b among harness fixes not yet landed — SQL
   executability landed S217/S218. Cheap, $0.
4. **`sql_dialect_from_url` `ValueError` on a non-numeric port** — one-line fix + regression test, hits two
   production seams (`cli.py:129`, `scripts/run_pipeline.py:175`). Filed S218, still open.
5. **Enterprise migration** — C4 (the fork) or C2, both ungated. C4 needs D9/D5/D4/D8/D16 from the operator
   live at session start.

**Key files:**
- `tests/eval/PHASE_E_AGREEMENT_REPORT.md` §"Update — Session 220" — the numbers, what they establish, and
  the four things they do **not**. **Read before quoting any verdict.** Header provenance list at `:12-21`
  updated to include S220.
- `tests/eval/sql_sweep.py:144-153` (primary-query handler) **and `:163-171` (the QC handler — the BACKLOG
  entry named only the first; both need the fix)**. `:38-43` is the docstring that argues for today's
  behaviour deliberately.
- `tests/eval/interview_sweep.py:82-87,152-180` — the sibling that retries. Diff against the above.
- `tests/eval/eval_thresholds.py:25` (`SQL_PARSE_VALID_MIN = 1.00`), `:36`
  (`QUALITY_CHECKS_STRUCTURAL_MIN = 1.00`), `:26` (`SQL_EXECUTABLE_MIN = 0.95`). **Do not lower them.**
- `packages/data-agent/src/model_project_constructor_data_agent/opencode_client.py:174` — the
  `subprocess.run(argv, **kwargs)` with no `env=`. Why `.env` is load-bearing.
- `BACKLOG.md` §"The SQL/QC sweep does not retry transients" (updated) and §"An unset `ANTHROPIC_API_KEY`
  scores as 45 model-quality failures" (new).
- Scratch, not committed: `…/29b217be-…/scratchpad/probe.py` (the driver — 14 self-tests at `selftest`,
  observer + meters), `probe_result.json` (raw record, 45 samples), `probe_result_VOID_noauth.json` (the
  void run, kept as the evidence for finding 1), `probe.log`.
- S219's scratch driver survives at `…/16073e42-…/scratchpad/full_sweep.py` with `result_opencode.json` /
  `result_anthropic.json`. **Reusable — do not rebuild the meters.**

**Gotchas:**
1. **Do not quote S220 as a GO.** Three of eight cells is a diagnostic. **The recorded verdict is NO-GO**,
   unchanged since S219. (S219 gotchas 1 and 2 both still apply verbatim.)
2. **Source `.env` for any `opencode` run** — `set -a && . ./.env && set +a`. The CLI holds **0 stored
   credentials** and inherits `ANTHROPIC_API_KEY` from the parent environment. Without it you get 0/45 on
   every SQL threshold in 36 s at $0, and the error message names neither auth nor the variable.
   **This corrects the reading S219's gotcha 5 invites** — that gotcha is true about what `.env` does *not*
   supply, and says nothing about whether it is needed.
3. **`OPENCODE_EVAL_MODEL=anthropic/claude-sonnet-4-6` inline, plus `PYTHONPATH=.`** (S219 gotchas 5, 6 —
   re-verified; both still correct).
4. **Cost the SQL block at $0.0593/call, not the $0.0318 global mean.** 30 calls per 5-sample sweep ≈
   **$1.78 and ~18 min**. Do not project block cost or latency from a whole-run figure — the blocks are not
   alike (learning #89).
5. **Before believing any live rate, check calls > 0 and spend > 0.** A 0% across every threshold at
   implausible speed is an environment failure, not a quality finding (learning #91).
6. **The S219 transient is still unattributed** — no recurrence in 45 samples, so nobody knows which of the
   nine raise sites fired. Do not assume it was malformed JSON; the same type covers timeout and spawn
   failure.
7. **Background runs survive past the documented 600000 ms `Bash` ceiling** (S219 gotcha 7, re-confirmed —
   a 53-min run completed under `run_in_background`, and the completion notification fired reliably on both
   the successful run *and* the failed one).

### What Session 219 Did
**Deliverable:** **The first full eight-cell same-session sweep. COMPLETE. `opencode` flips GO → NO-GO;
the incumbent `anthropic` clears all eight for the first time.** **No production default changed, no
threshold changed, no harness changed.**

**Started / Completed:** 2026-08-02. **Commits:** this close-out (documentation-only — see "No CHANGELOG
entry" below). **Trigger:** the operator agreed to S218's "what's next" option 1, **explicitly limited to
sub-decision (a), the measurement**; (b), flipping `DEFAULT_LLM_PROVIDER`, was excluded by them and was not
touched.

**Workstream:** `docs/methodology/workstreams/AUDIT_WORKSTREAM.md` — a quality-gate review against a fixed
standard. Its Phase 2 order (define criteria → inventory scope → **read the implementation** → challenge
scope) is what produced both the scope correction and the root-cause diagnosis; the implementation read
(`sql_sweep.py`) is where the whole finding lives.

#### The result

| provider | scope | calls | wall | cost |
| --- | --- | --- | --- | --- |
| `anthropic` (baseline) | governance + SQL/QC fresh; interview carried from **S170** | 55 | 11.3 min | **$0.903** (token-derived, 55/55) |
| `opencode` (candidate) | **all eight cells fresh** | 515 | 130.5 min | **$16.396** (measured, 515/515) |

**`opencode`: NO-GO** — fails `sql_parse` (96.7%, bar 100%) and `qc_structural` (93.3%, bar 100%).
**`anthropic`: passes all eight** (governance 25/25, SQL 18/18 parse + 18/18 exec, QC 15/15).

#### ⚠ The NO-GO is one un-retried transient — read this before acting on it

All three sub-threshold numbers come from a **single** logged event:
`# WARN sql/property_severity[3/5]: LLMParseError on primary queries -> parse+exec+qc fail`.
`sql_sweep.py:144-153` scores one `LLMParseError` as one parse miss + one exec miss + one QC miss, **with no
retry**. Back it out and every artifact the provider actually produced was valid: **29/29 parse, 29/29
executable** (zero execution errors — the S216 dialect failure class is still gone), **14/14 QC**.

The same run hit **two** transient `IntakeLLMError`s in the interview block. Those were **retried and
recovered**, because `interview_sweep._TRANSIENT_ERRORS` retries up to 3 attempts then *excludes*. So the two
blocks apply **opposite policies to the same failure class**, and against two zero-tolerance 100% bars one
blip decides the verdict. This is gap #1c, fixed for interviews at S169 and never applied to the sibling.
**Filed in `BACKLOG.md`; deliberately NOT fixed here** — a harness change made after seeing a disliked number
is how a gate stops being a gate (learning #86).

#### What is now settled, and what is not

- **The incumbent passes all eight for the first time**: 5/8 fail (S165) → 3/8 (S170) → 1/8 (S175–S216) →
  **0/8**, six of eight cells fresh. The harness-trustworthiness arc opened at S165 is closed.
- **`opencode`'s cost is measured, not estimated**: $16.396 over 515/515 priced calls, read from
  `last_usage["cost"]` (the `step_finish` event). Mean **$0.0318/call**, vindicating S216's $0.0310 estimate.
  **S218's ~$1.00 char-derived estimate is superseded**, and its stated reason for it ("no usage is
  reachable") was wrong — the production client has exposed real cost since S213 (learning #88).
- **Latency**: `opencode` p50 **7.7 s**, p90 18.9 s, **max 129.1 s**. S218's "2× slower" was an artifact of
  measuring the SQL block alone (its calls are the heavy ones); across the full corpus `opencode` tracks
  S216's p50 7.8 s. **The 129 s tail is real and no §3.4 threshold can see it.**
- **NOT settled — one run per provider.** The verdict now turns on a single stochastic event and nobody has
  checked whether it reproduces.
- **NOT settled — `anthropic`'s two interview cells are S170** and have not been re-measured since.
- **`bedrock` remains PENDING** — no AWS credentials, unchanged since S164.

#### Spend: $17.30 against a ~$16.3 estimate (6% over)

`opencode` issued **515** calls where the S216-derived projection was ~475. Scope was the operator's choice
from three costed options, put to them **after** I found and corrected my own mis-quote (below).

### Session 218 Handoff Evaluation (by Session 219)

**Score: 8/10.** Strong, and two of its gotchas paid for themselves in the first ten minutes. Marked down for
one wrong provenance claim, one omission that was the exact structural sibling of the omission S218 itself
docked S217 for, and a cost figure that propagated into an operator decision before I caught it.

**What helped:** (1) **The six "what this does NOT establish" items, especially #1** — "five of eight cells
are carried forward; if the cutover is going to be taken, measure all eight in one session." That *is* this
session; it defined the deliverable precisely and told me exactly which cells were stale. (2) **Gotcha 4 —
`opencode` needs BOTH `OPENCODE_EVAL_MODEL` and the binary, and `.env` supplies neither, while
`AWS_BEARER_TOKEN_BEDROCK` cannot accidentally opt `bedrock` in.** Used verbatim on every live command;
verified true; removed a real wrong-account billing risk. (3) **Gotcha 5 — the scratch driver needs
`PYTHONPATH=.`** Correct, applied from the first command, saved the predicted round trip. (4) **Key files
naming `tests/eval/sql_sweep.py` as the new owner of the SQL statistics** — that is exactly where the root
cause turned out to live; reading it is what produced the diagnosis. (5) **Gotcha 2 — `SQL_EXECUTABLE_MIN` is
still 0.95 and must not be lowered; if a future run drops below it, the first question is n, not the bar.**
Load-bearing when my run *did* drop below two bars: it kept me off the thresholds. (Directionally right but
incomplete — the answer here was neither n nor the bar, it was retry policy.) (6) **Its own self-assessed
minus #2** ("`opencode`'s cost is still an estimate… I did not reach for the event stream") pointed straight
at `last_usage` and closed itself in ~10 minutes. Learning #88 exists because S218 wrote its gap down honestly.

**What was wrong:** **the carried-forward provenance.** S218 recorded `interview_convergence` /
`interview_premature` among cells "carried forward from S216". For `opencode` that is right; for `anthropic`
it is not — S216 explicitly declined to re-pay the baseline's interview sweep ("at ceiling and stable since
S170"), so those cells are **S170**, and the agreement-table rows were untagged. A re-measure session depends
on exactly this kind of provenance claim, and I only caught it by re-reading the record rather than trusting
the handoff.

**What was missing:** (a) **No pointer that the SQL/QC block has no retry policy.** S218 worked inside
`sql_sweep.py`, *wrote the docstring for the `LLMParseError` handler*, and did not note that its sibling
retries while it does not. One line would have let me predict this failure mode before spending $16 — and it
is precisely the omission S218 docked S217 for ("here is the next task" vs "here is what the next task will
run into"). (b) **"A full sweep is S216-shaped, ~$14/100 min" is wrong for a full sweep** — S216 never re-paid
the baseline interview block. I inherited the framing and repeated it to the operator (learning #87).

**ROI:** high. Gotchas 4 and 5 paid immediately; the non-establishments list defined the session.

### Phase 3B: Self-assess — Session 219 — 8.5/10

- **The +:** (1) **Caught my own cost mis-quote before any money moved** and put three costed scopes back to
  the operator rather than proceeding on a number I no longer believed or silently narrowing the work.
  (2) **Refused to fix the harness defect that would have restored the GO** — the single most important call
  in the session, and the tempting one to get wrong. (3) **Diagnosed the failure to one line and proved what
  it was not**: every artifact the provider produced was valid, so the report says what the number *means*.
  (4) **Meter self-tested 10/10 at $0 before spending**, replaying the committed fixture through the real
  client — which is why `opencode`'s cost is a measurement and not a third consecutive estimate.
  (5) **Verified provenance against the record instead of trusting the handoff**, which found S218's
  S170-vs-S216 error. (6) **Ran the cheap stage first** to validate the pipeline before the 130-min one.
  (7) **Armed a watcher that fires on death as well as success** — silence would otherwise have been
  indistinguishable from progress. (8) **Followed the CHANGELOG convention when it cost me** a finished entry
  I had already written (below). (9) **Fixed doc drift that would have mis-executed a real cutover** — the
  `cli.py` row listed one hardcoded provider default where the code has two.
- **The −:** (1) **I mis-quoted the sweep cost to the operator** (~$14 for a full both-provider sweep) by
  inheriting S218's framing without checking what S216's $13.99 bought. Caught before spending, but only
  after it had already informed their choice to proceed. (2) **Still 6% over the corrected estimate** — I
  projected 475 calls from S216's 451 on a provider whose call count is model-chosen and *known* unstable
  (learning #74 is about exactly this metric), and added no margin. (3) **One run per provider, again.**
  Having concluded that the verdict hangs on a single stochastic event, I did not propose the cheap targeted
  re-run (SQL block only, ~$1, ~7 min) that would have tested whether 29/30 reproduces. That is the obvious
  next experiment and I left it for my successor instead of costing it out. (4) **I set the `opencode` run's
  `Bash` timeout to 600000 ms** — below the ~105 min it needed — then armed a watcher to cover a risk I had
  created myself; the `anthropic` run had 1800000. (5) **Loaded the `Monitor` tool, read its docs, and
  concluded I did not need it** — that determination was available before loading.

**No CHANGELOG entry, deliberately.** `docs/methodology/PROJECT_CONVENTIONS.md` §2 gates an entry on changing
shipped code (`src/`, `packages/`, `scripts/`) or `tests/` **test logic**. This session changed neither — only
markdown. I wrote a full entry, then removed it on reading the convention. ⚠ **Note for a future session:**
S216 was also measurement-only ("no `src/` change at all") and *does* carry an entry, so the convention and
the precedent disagree. I followed the written rule. Worth an operator ruling rather than silent drift.

**What's next — four options, all ungated:**

1. **Fix the SQL/QC retry asymmetry, then re-measure** (`BACKLOG.md`, the new item). This is the natural
   successor and the one this session sets up. Give `sweep_sql_capabilities` the `interview_sweep` treatment
   (`_TRANSIENT_ERRORS`, bounded retries, exclude-with-note, an `excluded_transient` counter so exclusions
   stay visible). **Harness change only — the thresholds must not move.** Then re-run `opencode` (~$16.4,
   ~130 min): a GO from the fixed harness would be the first resting on eight same-session cells *and*
   symmetric retry policy. ⚠ This changes a recorded verdict, so it must be its own session with the fix and
   the re-measure clearly separated.
2. **Cheap variance probe first (~$1, ~7 min).** Before any harness change, re-run the SQL block alone for
   `opencode` (`sweep_sql_capabilities`, 15 samples) two or three times and see whether the `LLMParseError`
   reproduces. If it never recurs, the finding is "one transient decided a gate"; if it recurs at ~1-in-15,
   that is a provider-reliability signal in its own right and worth recording separately. **Recommended
   before option 1** — it is the measurement my minus #3 says I should have proposed.
3. **`tests/eval/README.md` drift** — still unfixed for a fifth session, and now wrong in a new way: its
   line 49 heading and the paragraph at line 86 list "SQL executability" as an outstanding harness fix and
   `interview_convergence` as not green. Both were already false; the file now also predates a verdict
   reversal. Cheap, $0.
4. **Enterprise migration** — C4 (the fork) or C2, both ungated. C4 needs D9/D5/D4/D8/D16 from the operator
   live at session start.

**Key files:**
- `tests/eval/PHASE_E_AGREEMENT_REPORT.md` §"Update — Session 219" — the numbers, the cause, and what the run
  does *not* establish. **Read before quoting any verdict.** Agreement table at ~`:457` re-scored with S219
  provenance; cutover-procedure table at ~`:498` corrected.
- `tests/eval/sql_sweep.py:144-153` — the no-retry `LLMParseError` handler. **The whole finding.**
- `tests/eval/interview_sweep.py:82-87,152-180` — the sibling that *does* retry. Diff these two.
- `tests/eval/eval_thresholds.py:25` (`SQL_PARSE_VALID_MIN = 1.00`) and `:36`
  (`QUALITY_CHECKS_STRUCTURAL_MIN = 1.00`) — the zero-tolerance bars that turn one transient into a verdict.
  **Do not lower them.** (`SQL_EXECUTABLE_MIN = 0.95` sits at `:26` and passed at 96.7%.)
- `BACKLOG.md` §"The SQL/QC sweep does not retry transients" — the filed item, with the fix sketched.
- Scratch, not committed: `…/scratchpad/full_sweep.py` (metered driver, three stages),
  `test_meters.py` (10 self-tests, $0), `result_anthropic.json`, `result_opencode.json` (raw records).

**Gotchas:**
1. **Do not quote "opencode is GO at 8/8" — that verdict is superseded.** S218's GO rested on five S216 cells
   and did not reproduce. The current verdict is **NO-GO**.
2. **Equally, do not quote the NO-GO as a quality finding.** Every query and QC list the provider produced was
   valid. The gate failed on retry policy, not output.
3. **`SQL_PARSE_VALID_MIN` and `QUALITY_CHECKS_STRUCTURAL_MIN` are both 1.00.** With no retry policy, any
   transient fails them outright. Four sessions running have refused to lower a bar to make a number; do not
   be the first.
4. **`anthropic`'s interview cells are S170, not S216** — S218's handoff says otherwise and is wrong. If you
   need a fully fresh baseline, that block is ~420 calls and ~$8-9, and nobody has paid it since S170.
5. **A live `opencode` run needs `OPENCODE_EVAL_MODEL=anthropic/claude-sonnet-4-6` inline plus the binary**;
   `.env` supplies neither. Sourcing `.env` opts in `anthropic` only and cannot bill the abandoned AWS account.
   (S218 gotcha 4, re-verified.)
6. **The scratch driver needs `PYTHONPATH=.`** (S218 gotcha 5, re-verified.)
7. **`Bash` documents a 600000 ms timeout ceiling.** The 130-min `opencode` run completed anyway under
   `run_in_background`, so background tasks appear exempt — but I would not rely on it. Arm a watcher that
   reports **death as well as success**, or the run's silence is unreadable.
8. **Real `opencode` cost is free to collect** — `OpenCodeLLMClient.last_usage["cost"]` after each `_run`.
   Do not rebuild a char-derived estimate; S218's stated reason for one was incorrect.
9. **`origin/master` is 6 commits behind local, 7 once this close-out lands.** Verified with
   `git log origin/master..HEAD --oneline | wc -l`, not counted by hand. Stale since before S216.

### What Session 218 Did

### What Session 218 Did
**Deliverable:** **Re-measured `sql_exec` under Session 217's dialect fix and re-scored the Phase E cutover
verdict. COMPLETE. Both providers PASS; the `opencode` verdict flips NO-GO → GO.** **No production default
changed, no threshold changed.**

**Started / Completed:** 2026-08-02. **Commits:** `4e2c8ec` (harness: N≥5 sampling for the SQL block),
`36550f6` (the measurement + verdict + two filed findings), plus this close-out.
**Trigger:** the operator replied `1` to the Phase 0 report — option 1 of Session 217's three "what's next"
options. Same one-character selection pattern Sessions 209–217 handled.

**Workstream:** `docs/methodology/workstreams/AUDIT_WORKSTREAM.md` — a quality-gate review against a fixed
standard (the eight §3.4 thresholds). Its "define criteria → inventory scope → read the implementation →
challenge scope" order is what produced the scoping analysis below; `DEVELOPMENT_WORKSTREAM.md` governed the
harness sub-task, as it did in Session 215.

#### The result

| provider | `sql_parse` | `sql_exec` | `qc_structural` | calls | wall | cost |
| --- | --- | --- | --- | --- | --- | --- |
| `anthropic` | 18/18 | **18/18** | 15/15 | 30 | 7.2 min | **$0.63** (token-derived, 30/30 calls) |
| `opencode` | 34/34 | **34/34** | 15/15 | 30 | 16.8 min | ~$1.00 (char-derived estimate) |

**Zero execution errors on either provider.** No `DATEDIFF`, `PERCENTILE_CONT … WITHIN GROUP`, `MEDIAN` or
`ILIKE`. The failure class that made this threshold fail since Session 165 is gone. `anthropic` clears
`sql_exec` for the first time since it was first measured; the `opencode` verdict, from the **unmodified**
`evaluate_cutover`, flips **NO-GO → GO** at 8/8.

**Total spend $1.63 against the $1–4 authorized**, vs $13.99 for the full sweep — because 93% of that sweep
is the interview block, which the dialect fix provably cannot reach.

#### Two scope decisions were the operator's

I put both to them with a recommendation and the evidence, after the Phase 2 inventory. They chose the
**sampled-SQL-only scope** over a full sweep, a single-pass re-run, or sampled-plus-full; and **file** the bug
found during scoping rather than fix it, keeping the session scoped to measurement.

#### The harness change, and why it was the load-bearing part

The SQL/QC block was the only one of the three measurement blocks that did **not** sample. Governance runs
5 cases × N≥5; the interview sweep runs 4 cases × N≥5; the SQL block ran its 3 primary cases **once each**.
That put `sql_exec` on a ~5 model-chosen-query denominator against a ≥95% bar — pass-only-if-perfect, where
one miss reads as a 20-point drop — and `qc_structural` on **three booleans** against a 100% bar. It is why
S216 and S217 each measured this metric and each had to write "do not quote this as a rate" instead of a
result.

`4e2c8ec` gives the SQL block the same N≥5 sampling, extracted as `tests/eval/sql_sweep.py` so the shadow
driver and the live assertion tier share one implementation — the `interview_sweep.py` precedent, closing the
same drift seam S169 closed for interviews. **No threshold moved. The denominator did** (learning #82).

Extracting it also surfaced that the two live SQL tests each paid for their own `generate_primary_queries`
calls over the same corpus — and that the QC one built its client **without** `sql_dialect`, so it was still
measuring the pre-S217 dialect-blind prompt while its sibling measured the fixed one. Both are now one test
over one sweep. Also added `eval_scoring.sql_execution_error`, so a failure's *text* is available while
`sql_executes` stays the gate's single boolean truth (discharging S216 gotcha 3 structurally rather than by
rebuilding the capture by hand a third time).

#### ⚠ What the GO does NOT establish — read before acting on it

1. **Only three of the eight cells are fresh.** `json_parse`, both governance rows and both interview rows
   are **carried forward from S216**. That is defended, not assumed: they come from the *intake* client, built
   by a factory that accepts no `sql_dialect`, and nothing under `agents/intake/` imports the data-agent
   package. Three adversarial refutation lenses failed to produce any path by which the dialect note moves one
   of those values. **If the cutover is actually going to be taken, measure all eight in one session.**
2. **One run per provider.** n is 18 and 34 queries rather than ~5 — enough to make a 95% bar decidable — but
   run-to-run variance is still unmeasured.
3. **`opencode`'s cost is an estimate, not a measurement.** Its subprocess transport never touches
   `messages.create`, so no `usage` block is reachable; ~$1.00 is char-derived at ~3.6 chars/token.
   `anthropic`'s $0.63 *is* token-derived from usage on all 30 calls.
4. **Latency got ~2× worse and no threshold objects.** `opencode` p50 **33.5 s** / max 84.8 s vs `anthropic`
   p50 **18.0 s** / max 38.5 s, same model. A cutover carries that.
5. **`bedrock` is still PENDING** — no AWS credentials, unchanged since S164.
6. **Only one of the three dialect-injected prompts is measured for dialect effect** (see below).

### Session 217 Handoff Evaluation (by Session 218)

**Score: 9/10.** Genuinely excellent. Its gotchas were load-bearing three separate times, its "this is NOT a
re-score" framing was repeated in enough places that I could not have misread it, and every technical
citation I checked held. Marked down for one arithmetic slip and one omission that cost real money.

**What helped:** (1) **Gotcha 1 — "the 2/5 → 4/4 probe is NOT a threshold re-score", stated three times in
three places.** This is the single most valuable thing in the handoff. A weaker framing would have let me open
by quoting 4/4 as a PASS and skip the measurement entirely. (2) **Gotcha 5 — `ANTHROPIC_API_KEY` lives in
`.env`, not the ambient shell.** Used verbatim (`set -a && . ./.env && set +a`) on every live command; saved
the round trip it predicted. (3) **Gotcha 6 — the mypy gate is bare `uv run mypy`, not `mypy .`.** Verified
true; saved me from re-reading 134 pre-existing `tests/` errors as a regression, which is exactly the ~2
minutes S217 lost. (4) **Gotcha 2 — the agreement table's `sql_exec` row is stale-by-construction.** Correct,
and it told me precisely what I was allowed to overwrite vs. preserve as history. (5) **Gotcha 3 — `opencode`
has never run with the dialect instruction, and its D2 fold is where a system-string instruction might land
differently.** This named the single most interesting unknown, and it is the one I measured: it landed fine,
34/34. (6) **Every key-file citation verified correct** — `eval_thresholds.py:26`, the three `_dialect_note`
injection points (185/224/337), `test_shadow_run.py`, `db.py`. I checked rather than trusted (FM #11) and
found no drift. (7) **The self-assessment's own minus #1** ("I did not instrument the probe's cost") is what
made me build and *test* a cost meter before spending — learning #84 exists because S217 wrote down its own
gap honestly.

**What was missing — the deduction:** (a) **Gotcha 8's count is wrong.** It says `origin/master` is "2 commits
behind local (`9c9fe35` + this one)". It was **3** — S216's close-out `3f9e553` was also unpushed, which the
same gotcha's second sentence half-acknowledges without correcting the number. Trivial in effect, but it is a
number in a handoff that does not survive `git status`. (b) **No pointer that the SQL block does not sample.**
S217 worked inside `measure_provider`, read the governance loop's `for _ in range(n_samples)` directly above
the SQL block it was editing, and wrote a handoff whose entire "what's next" #1 is a re-measure — without
noting that the metric to be re-measured has a denominator of ~5 and no sampling. One line would have saved
the whole scoping investigation. This is the difference between "here is the next task" and "here is what the
next task will run into." (c) **"Needs operator spend authorization — S216's comparable run was $13.99" framed
the cost as fixed.** It is not: the cost is a function of scope, and 93% of that sweep was unreachable from the
change S217 had just made — a fact S217 was better placed than anyone to know, having just established the
blast radius. Recommending the full sweep by default is what would have cost 8× more for a *smaller* sample.

**What was wrong:** the commit-count in gotcha 8 (above). Nothing technical. Notably, S217 introduced a real
defect (`sql_dialect_from_url` raising `ValueError`) that its own handoff did not know about — that is a miss,
but not a handoff-quality miss, and its "parse-only, works before `connect()`" note is what let me find it.

**ROI:** very high. Gotchas 1, 5 and 6 each paid for themselves within the session.

### Phase 3B: Self-assess — Session 218 — 8.5/10

- **The +:** (1) **Scoped by blast radius instead of by the default entry point**, turning a $13.99/100-min
  run into a $1.63/24-min run that produced a *larger* sample on the metric in question (learning #83).
  (2) **Fixed the measurement rather than the number** — the threshold is untouched; `sql_exec` passes because
  the denominator went from ~5 to 18/34. Lowering `SQL_EXECUTABLE_MIN` was available and explicitly refused,
  three sessions running. (3) **Verified the carry-forward claim adversarially before relying on it**, and
  then read the refutations properly rather than accepting their verdict flags — all three "REFUTED" but on
  failure-mode coupling, not value coupling (learning #85). (4) **Found and independently verified a real
  production bug** in S217's code (`ValueError` on a non-numeric port, reachable at two seams with a
  user-supplied `--db-url`) — and did **not** fix it, because that was the operator's call. (5) **Tested the
  cost meter against a fake before spending**, which caught that usage is unreachable at `_call_claude`; the
  paid run therefore produced a real token-derived figure instead of repeating S217's "no figure" gap
  (learning #84). (6) **Dry-ran the driver at $0 first**, applying S217's own "it crashed before spending,
  which was luck, not design" self-criticism. (7) **RED-proved the load-bearing test** — forcing `range(1)`
  fails 5 of 9 new tests including the sampling test itself. (8) **Reported the GO with six explicit
  non-establishments and changed no default** — a green result is the moment to be *more* careful, not less.
  (9) **Extracted rather than duplicated**, closing the same drift seam S169 closed, and in doing so found the
  QC live test had been silently measuring the pre-fix prompt.
- **The −:** (1) **I polled background tasks repeatedly instead of yielding**, which advanced no wall-clock
  time and burned calls during the 17-min `opencode` run. The watcher was already armed; I did not trust it.
  (2) **`opencode`'s cost is still an estimate.** S216 got a real per-call figure from OpenCode's own
  `step_finish` events, which expose `cost`/`tokens` — my meter reads the SDK seam that provider never
  touches, and I did not reach for the event stream. I knew the limitation before spending and shipped it
  anyway rather than spending ~10 minutes to parse what was already in the JSONL. (3) **One run per provider,
  no repeat.** Having argued that n is what makes this metric trustworthy, I then produced a single sample per
  provider and left run-to-run variance unmeasured — a second `anthropic` run would have cost $0.63.
  (4) **The initial blast-radius workflow returned 648K subagent tokens for what became ~6 load-bearing
  facts**, repeating the over-sweep S217 docked itself for. The adversarial pass earned its keep (it found the
  `ValueError`); the four-way inventory was wider than needed. (5) **I did not characterize *why* `opencode`
  writes ~1.9× as many queries as `anthropic`** (34 vs 18) — the same unexamined mechanism S216 flagged and
  left open. It no longer costs it anything now that they all execute, but it is still unexplained.

**What's next — three options, all ungated:**

1. **Decide the cutover** (the natural successor, and the one this session sets up). `opencode` is GO at 8/8.
   Taking it means (a) a full eight-threshold fresh sweep in one session — recommended before acting, since
   five cells are carried forward — and (b) changing `DEFAULT_LLM_PROVIDER`, which is an operator decision, not
   a measurement outcome. **Weigh the ~2× latency**, which no threshold captures. Cost: a full sweep is
   S216-shaped, ~$14/100 min.
2. **The `tests/eval/README.md` drift, now actively contradicting the committed record.** Its heading
   `## Live baseline (measured — harness not yet trustworthy)` (**line 49**) and the paragraph starting
   **line 86** still list **"SQL executability"** (line 91) as an outstanding harness fix and
   `interview_convergence` as not green. Both are now false. Note the blockquoted `Status (Session N)` entries
   above it are a *historical log* and are fine as-is — it is the heading and the non-quoted paragraph that
   assert current status. Also check line 250 ("SQL executability fairness"). ⚠ **I made half of this
   staleness worse and did not fix it** — deferred for a fourth session running to hold "1 and done", but it
   is now a document that contradicts `36550f6`. Cheap, $0.
3. **Enterprise migration** — C4 (the fork) or C2, both ungated. C4 needs D9/D5/D4/D8/D16 from the operator
   live at session start.

Also open and cheap: the filed `sql_dialect_from_url` `ValueError` bug (one line + a regression test).

**Key files:** `tests/eval/sql_sweep.py` — **new**; owns the SQL measurement's statistics, shared by
`shadow_run.measure_provider` and the live tier. `tests/eval/test_sql_sweep.py` — **new**; 9 tests at $0 via a
fake runner, RED-proved. `tests/eval/eval_scoring.py:99-118` — `sql_execution_error` (the failure text) with
`sql_executes` derived from it. `tests/eval/PHASE_E_AGREEMENT_REPORT.md` §"Update — Session 218" — the numbers
and the six non-establishments; **read that before quoting the GO**. `tests/eval/eval_thresholds.py:26` —
`SQL_EXECUTABLE_MIN = 0.95`, still not lowered, now actually met.
`packages/data-agent/src/model_project_constructor_data_agent/db.py` — `sql_dialect_from_url`, the filed bug.
Scratch driver (not committed): `…/scratchpad/sql_remeasure.py` plus `result_anthropic.json` /
`result_opencode.json` — the raw run records.

**Gotchas:**
1. **The GO rests on five carried-forward cells.** Fresh rows are marked `S218` in the agreement table; the
   rest are `S216`/`S175`/`S176`. Do not describe this as "a full re-measure" — it deliberately was not one.
2. **`SQL_EXECUTABLE_MIN` is still 0.95 and still must not be lowered.** It now passes. If a future run drops
   below it, the first question is n, not the bar (learning #82).
3. **`opencode` runs ~2× slower per call** (p50 33.5 s vs 18.0 s) and no §3.4 threshold can see it. If the
   cutover is taken, that ships.
4. **A live `opencode` run needs BOTH `OPENCODE_EVAL_MODEL` and the binary**, and `.env` supplies neither —
   `OPENCODE_EVAL_MODEL=anthropic/claude-sonnet-4-6` must be set inline. `.env` *does* supply
   `AWS_BEARER_TOKEN_BEDROCK`, but `provider_creds_available("bedrock")` checks only `AWS_ACCESS_KEY_ID` /
   `AWS_PROFILE` / `~/.aws/credentials`, so sourcing `.env` opts in `anthropic` **only** and cannot
   accidentally bill the abandoned AWS account.
5. **The scratch driver needs `PYTHONPATH=.`** — `tests.eval` is not importable otherwise, and the failure is
   an immediate `ModuleNotFoundError` (cheap, but budget the round trip).
6. **The eval's `_dialect_note` reaches three prompts; the gate measures the effect of one.**
   `generate_primary_queries` is parsed *and executed*; `qc_structural` only checks
   `len(qc_lists) == n_primary_queries` and never parses the QC SQL; `generate_baseline_query` is **never
   called by the eval at all** (`grep -rn generate_baseline_query tests/eval/` → zero `.py` hits; the
   `kind: baseline` corpus case is filtered out of every live path). Filed in `BACKLOG.md`.
7. **S217's gotchas 1-6 are now superseded or discharged**, except gotcha 4 (subclass keyword forwarding —
   still true and still a silent failure mode if you add a constructor keyword). Gotcha 1's "not a re-score"
   no longer applies: this *is* the re-score. Gotcha 7's `tests/eval/README.md` half is **still unfixed** and
   is now worse — see "what's next" #2.
8. **`origin/master` is 5 commits behind local, 6 once this close-out lands** — S216's `3f9e553`, S217's
   `9c9fe35` + `52075ae`, and this session's `4e2c8ec` + `36550f6` (+ this one). Verified with
   `git log origin/master..HEAD --oneline | wc -l`, not counted by hand — S217's gotcha 8 got this number
   wrong by one. Stale since before S216.

### What Session 217 Did
**Deliverable:** **Fixed the root cause behind the failing `sql_exec` threshold — the data agent now knows
which SQL dialect it is writing for. COMPLETE.** **No threshold changed, no cutover verdict re-scored, no
recorded rate edited.**

**Started / Completed:** 2026-08-02. **Commits:** `9c9fe35` (the fix + tests), plus this close-out.
**Trigger:** the operator replied `1` to the Phase 0 report — option 1 of Session 216's two "what's next"
options. The same one-character selection pattern Sessions 209–216 handled.

**Workstream:** `docs/methodology/workstreams/DEVELOPMENT_WORKSTREAM.md`, read in full before any edit. Its
Phase 2 order (read the code you will modify → then the tests → then the docs) is what surfaced that the DB is
already in scope at the point the prompt is built.

**Two scope decisions were the operator's, not mine.** Session 216 named two candidate fixes and scoped
neither, so after the Phase 2 inventory I put both to the operator with a recommendation and the evidence
behind it. They chose **fix A — the dialect-aware prompt** over the warehouse-target-DB alternative, and
**deterministic tests + a cheap live probe** over both "$0, no evidence" and "full re-measure".

#### What was actually wrong — and it was not only an eval problem

The data agent generated SQL for a dialect nobody named, so it inferred one, and it inferred a **warehouse**.
Session 216 framed this as "`sql_exec` measures the harness, not the model" — correct about the *metric*, but
that framing hides the more important half: **the same silence ships to production.** An organization on
Snowflake, PostgreSQL or SQL Server got whatever dialect the model picked. The failure is quiet by
construction: the SQL parses, returns, and only fails at execution. That is why the eval-only variant (pass
`sql_dialect` on the harness client alone — the smallest possible diff) was **explicitly rejected**: it would
have made the eval flatter the shipped behaviour rather than measure it. Learning #79.

The dialect is **derived** from the database the caller already configured, never configured separately:

```
ReadOnlyDB.dialect / sql_dialect_from_url   parse-only: sa.make_url(url).get_backend_name()
  -> make_llm_client(provider, sql_dialect=...)
  -> AnthropicLLMClient(sql_dialect=...)     [bedrock + opencode inherit the prompts, forward the kwarg]
  -> _dialect_note() into the SYSTEM string of generate_primary_queries,
     generate_quality_checks, generate_baseline_query
```

Parse-only is load-bearing: `generate_queries` is the **first** node in the graph and the DB is not connected
until `execute_qc`, so a dialect that needed a live connection would arrive too late to reach the prompt.
There is deliberately **no `--sql-dialect` flag** — a second source of truth is a second thing to get wrong;
deriving it makes "agent points at PostgreSQL, prompt says SQLite" unrepresentable rather than merely
discouraged.

#### The 6-call A/B that verified it — and what it does NOT establish

Same model (`claude-sonnet-4-6`), same three `kind: primary` corpus cases, same seeded SQLite DB, one session,
run twice:

| arm | `sql_dialect` | executable | parse-valid |
| --- | --- | --- | --- |
| dialect-blind (the prompt S216 measured) | `None` | **2/5** | 5/5 |
| dialect-aware (as shipped) | `sqlite` | **4/4** | 4/4 |

Every blind failure is the predicted class, and the probe surfaced a **fourth** offender S216's list did not
contain: **`ILIKE`** (PostgreSQL), alongside `DATEDIFF` and `PERCENTILE_CONT … WITHIN GROUP`. That *widens* the
diagnosis — the problem was never three specific functions, it was that the model had to guess. Parse-validity
is 100% in both arms, which is exactly why this failed silently for ~50 sessions.

**This is a diagnostic, not a re-score, and the next session must not quote it as one.** n is tiny; the
denominator is still model-chosen (S216 gotcha 2 stands, so 4/4 is **not** "100% ≥ 95% PASS"); only
`anthropic` was measured; single run, so variance is unknown. `SQL_EXECUTABLE_MIN` is still 0.95, the recorded
60.0% / 42.9% still stand in the agreement table, and the `opencode` **NO-GO still stands**.

**Cost: not instrumented.** 6 calls with a small payload — well under the ~$0.30–0.50 the operator authorized,
but I did not capture per-call usage, so I am not reporting a figure. That is a gap, not an estimate.

### Session 216 Handoff Evaluation (by Session 217)

**Score: 9/10.** The best handoff in this run. Its diagnosis *was* my Phase 2 — I inherited a solved
attribution problem and spent the session on the fix instead of re-deriving the cause. Marked down for one
framing omission that would have produced the wrong fix if I had accepted it, and for repeating the estimate
gap it had itself docked S215 for.

**What helped:** (1) **The diagnosis itself.** S216 captured the real DB exception per generated query and
named the cause. Without it this session is a diagnosis session, not a fix session. (2) **Gotcha 2** —
"`sql_exec` cannot be compared across providers as a rate; its denominator is model-chosen; report numerator
and denominator." Followed literally in the probe and in every doc line I wrote; it is why the record says
2/5 and 4/4 rather than 40% and 100%. (3) **Gotcha 3** — "`sql_executes` catches bare `Exception` and returns
`False`; capture the exception text or you will re-derive this diagnosis from scratch." I built
`execute_capturing_error` into the probe *because of this line*, and it is what surfaced `ILIKE` — a finding
that would otherwise have collapsed to one bit. (4) **"Do not lower `SQL_EXECUTABLE_MIN`"**, stated in three
places, framed the entire task as fix-the-cause-not-the-score. (5) **Every key-file citation verified correct**
— `eval_thresholds.py:26`, `eval_scoring.py:99-106`, `eval_cutover.py:237-248` all land exactly where claimed.
I checked all three rather than trusting them (FM #11), and unlike S216's experience with S215, found nothing
wrong. (6) **Naming two candidate fixes** gave the operator a real choice instead of one I had invented.

**What was missing — the deduction:** (a) **It framed the defect as harness-only.** "`sql_exec` measures the
harness, not the model" is true of the metric and misleading about the system: the same unstated dialect ships
to production, one inference from S216's own sentence "nothing in the data-agent prompt names the dialect."
A session that accepted the framing would have shipped the eval-only fix and left the product defect in place.
(b) **No scoping signal on the two candidates** — "neither scoped" was accurate but left unstated that one is
a prompt change and the other needs a new dependency plus a re-authored corpus and reference SQL
(`julianday()` is SQLite-only). I built that comparison before the operator could choose. This is the same
cost/estimate gap S216 docked S215 for, repeated. (c) **No pointer to where the dialect would come from.**
`ReadOnlyDB` already holds the URL and `build_graph` already receives the db — one line naming that would have
shortened Phase 2 materially.

**What was wrong:** nothing found. All three key-file citations verified against bytes; gotcha 7's
`origin/master` claim was consistent with what I found at start (1 ahead, being S216's own close-out).

**ROI:** very high. Gotcha 3 alone converted a one-bit failure into a named fourth root cause.

### Phase 3B: Self-assess — Session 217 — 8/10

- **The +:** (1) **Fixed the root cause, not the metric** — and specifically rejected the eval-only variant
  that would have turned the threshold green while leaving the product defect shipping. (2) **Verified the
  blast radius rather than assuming it** — an 8-agent adversarial inventory established that
  `generate_primary_queries` has exactly one implementation and that **no test asserts prompt text**, which I
  then re-confirmed by hand before editing. (3) **Designed the cheapest experiment that isolates the cause** —
  6 calls, not a $14 sweep, and it varies only the suspected cause (learning #78). (4) **Dry-ran the probe at
  $0 before spending**, directly applying S216's own "it crashed before spending, which was luck, not design"
  self-criticism. (5) **Held the line on scope** — no threshold lowered, no verdict re-scored, no recorded
  rate edited, despite having a green-looking result in hand. (6) **Covered the silent-failure modes with
  tests**: subclass keyword forwarding (invisible if dropped) and a factory test parametrized over
  `KNOWN_PROVIDERS` so a fourth provider cannot ship dialect-blind. (7) **Gave the shadow driver its first
  $0 tests** — the path whose untestedness let S215's defect survive. (8) **Marked the agreement table's
  `sql_exec` row stale-by-construction** rather than editing history or leaving it to be misquoted.
- **The −:** (1) **I did not instrument the probe's cost**, on a session whose scope was explicitly defined by
  a spend ceiling. Reporting "well under $1" instead of a number is exactly the gap I docked S216 for one
  section above. (2) **I ran `uv run mypy .` first and read 134 errors as a possible regression** before
  checking that the project's gate is `uv run mypy` with a configured package list; ~2 minutes lost to not
  reading the config first. (3) **The probe measured `anthropic` only.** `opencode` is the provider whose
  cutover this unblocks, and its D2 prompt-role fold is exactly the mechanism that might absorb a system-string
  instruction differently — that is a real unknown I am handing on rather than closing. (4) **I did not
  characterize why the two arms produced different query counts** (5 vs 4). It is probably noise at n=3 cases,
  but it is the same model-chosen-denominator effect S216 flagged and I left it unexamined. (5) The workflow I
  used for the inventory produced ~730K subagent tokens for what was ultimately ~8 load-bearing facts; the
  adversarial verify pass earned its keep (it caught several off-by-one citations) but the sweep was wider than
  the task needed.

**What's next — three options, all ungated:**

1. **Re-measure `sql_exec` under the fix** (the natural successor). A full `shadow_run.measure_provider` sweep
   re-scores the threshold for `anthropic` and `opencode` and would reopen the `opencode` cutover verdict.
   **Needs operator spend authorization** — S216's comparable run was $13.99 / 99.5 min. Read
   `PHASE_E_AGREEMENT_REPORT.md` §"Update — Session 217" first; do **not** treat this session's 4/4 as a PASS.
2. **Enterprise migration** — C4 (the fork) or C2, both ungated. C4 needs D9/D5/D4/D8/D16 from the operator
   live at session start.
3. **The non-Anthropic `opencode` run** that discharges `AI-Dependencies.md` §6.7's model-family
   diversification. Unblocked since S216; a second measurement, not a re-run.

**Key files:** `packages/data-agent/src/model_project_constructor_data_agent/db.py` —
`sql_dialect_from_url` + `ReadOnlyDB.dialect` (parse-only; works before `connect()`).
`.../anthropic_client.py` — `_dialect_note()` and the three injection points; `sql_dialect=None` reproduces the
old prompt byte for byte. `.../factory.py` — the `sql_dialect=` kwarg on all three provider branches.
`tests/eval/test_shadow_run.py` — **new**; the first $0 coverage of the shadow driver's wiring.
`tests/eval/PHASE_E_AGREEMENT_REPORT.md` §"Update — Session 217" — the probe, and an explicit list of what it
does not establish. `tests/eval/eval_thresholds.py:26` — `SQL_EXECUTABLE_MIN = 0.95`, still not to be lowered.

**Gotchas:**
1. **The 2/5 → 4/4 probe is NOT a threshold re-score.** Tiny n, model-chosen denominator, `anthropic` only,
   single run. Quoting 4/4 as "100% PASS" would manufacture a green report by a different route than lowering
   the constant. The agreement table still carries S216's numbers and the standing NO-GO — deliberately.
2. **The agreement table's `sql_exec` row is stale-by-construction.** Both recorded rates were measured with a
   dialect-blind prompt that no longer exists. The row is left unedited as a faithful historical record; a
   bullet under the table says so. Do not cite it as current provider SQL quality.
3. **`opencode` has never been run with the dialect instruction.** Its D2 fold delivers the system string as
   user text inside OpenCode's agent framing — the one provider where a system-string instruction might land
   differently. Unknown, and the most interesting thing about a re-measure.
4. **Adding a constructor keyword to `AnthropicLLMClient` requires forwarding it in BOTH subclasses.** They
   inherit the prompts but re-declare `__init__` with explicit `super()` keywords. An unforwarded keyword fails
   silently — output still builds and parses. Pinned by per-subclass tests plus a `KNOWN_PROVIDERS`-parametrized
   factory test (learning #80).
5. **`ANTHROPIC_API_KEY` is not in the ambient shell** — it lives in the repo's `.env`. Live work needs
   `set -a && . ./.env && set +a`. My first probe attempt died on auth **before spending anything**; that was
   the intended failure mode, not luck, but budget a round trip for it.
6. **The project's mypy gate is `uv run mypy` (bare), not `mypy .`.** `[tool.mypy] packages = [...]` scopes it
   to the two source packages; `mypy .` additionally lints `tests/` and reports 134 pre-existing errors that are
   **not** a regression. Do not "fix" them.
7. **Session 216's gotchas 2, 3 and 5 all still apply verbatim.** Gotcha 1 is now superseded (the `opencode`
   column is measured *and* the prompt it was measured against has changed); gotcha 6's real half —
   `tests/eval/README.md:57-59` and `:67-76` still describing `interview_convergence` as blocked — **is still
   unfixed**, deliberately out of scope for a third session running.
8. **`origin/master` is 2 commits behind local** as of this close-out (`9c9fe35` + this one). Session 216's
   close-out was also unpushed at my start.

