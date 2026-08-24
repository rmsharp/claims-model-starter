# Backlog

**Open work only.** Completed items move to `CHANGELOG.md` (chronological, session-numbered). Milestone-grouped summaries live in `ROADMAP.md`. **Do not leave checked-off `[x]` items here** — remove the line on completion and record the work in `CHANGELOG.md` per `docs/methodology/README.md` §templates (v2.1 three-file split).

---

## Plain-language index — read this to the operator in Phase 0

**Why this exists.** In Session 223 the operator read a Phase 0 report that listed the open items by
their headings and said: *"I do not understand any of the 9 listed items."* That was a fair
complaint — the items below are written by sessions for sessions, and their headings are opaque
without the shared vocabulary. This section is the translation, **written once so no future session
has to regenerate it**, at the operator's explicit instruction (2026-08-17).

**Maintain it.** When you open, close, or materially change an item below, update its row here in the
same commit. A row that disagrees with its item is worse than no row.

### The vocabulary the headings assume

The pipeline's agents call a **large language model (LLM)**. Three routes to one are wired:
`anthropic` (the direct API — **the default, and what actually runs**), `bedrock` (Amazon's hosting),
and `opencode` (a command-line program fronting ~75 vendors, added so an enterprise standardising on
a different AI CLI is not a rewrite). Before any route becomes the default it must pass a **gate**:
eight measurements against real live calls, costing real money. The code that runs them is the
**eval harness** (`tests/eval/`) — test scaffolding, not shipped product. A **sweep** is one batch
run of it. A **transient** is a momentary glitch (timeout, dropped connection, one garbled reply) as
opposed to the model genuinely being bad at the task.

The eight gate measurements: valid JSON emitted; SQL syntactically valid; SQL actually executes;
agreement with reference answers on claim cycle-time; **never** rating a risk less severe than the
reference (zero tolerance); quality-check queries structurally correct; the interview reaches a
complete picture; **never** ending an interview early (zero tolerance).

### The items, in plain terms

**Five of these are one complaint** — *the measuring instrument cannot reliably tell "the model is
bad" from "something hiccuped."* That is what cost `opencode` its recorded verdict. The largest of
them — four surfaces applying three different glitch policies — **closed in Session 225**; the two
rows below it are the smaller residue that closing it exposed.

| Item (heading below) | In plain terms | Cost / note |
|---|---|---|
| Re-measure `opencode` | `opencode` was recorded NO-GO on a single glitch in 15 samples. Session 220 re-ran 45 samples and it never recurred; Sessions 221 and 225 then fixed the harness to retry a glitch before scoring it — and deliberately did **not** re-run the measurement, because changing your instrument after seeing a number you dislike is how a gate stops being a gate. The verdict on the books rests on an instrument since repaired, now in both halves. | **~$16.40, ~130 min.** The only item that costs real money. Source `.env` first. |
| Two sweeps stay silent about a dropped sample | Closing the transient-policy item (Session 225) left two smaller siblings. The live interview gate is the one measurement surface that still passes the sweep no place to log to, so every retry and exclusion note it produces — including the error text that makes a failure attributable — is discarded. And the driver reports how many samples the governance and SQL sweeps dropped, but not the interview one, so that denominator can shrink invisibly in the report. | Two one-line changes. No money. |
| A glitch means different things per provider | The harness decides "network blip" vs "the model is bad" by looking at the *type* of error raised. Only the two direct-API providers raise the network types; `opencode` runs as a subprocess and reports a spawn failure, a crash and a timeout as the same error a garbled reply produces. So the identical real-world event is discounted for one provider and counted against another. | Pre-existing, affects all three sweeps. Fixing it means changing the adapter's error mapping, not the harness. |
| A bare `KeyError` aborts the whole sweep | If the model returns valid JSON with the *wrong field names*, the code dies on an unhandled error that no part of the harness catches — killing a run that may be an hour in, instead of recording one failure and moving on. | Small. Mirrors a convention the intake agent already ships. |
| No circuit breaker | A run failing for a systemic reason grinds on sample after sample. The retry added in Session 221 tripled the SQL/QC worst case to **~7.5 hours of billed nothing**, and Session 225 added the same tripling to the governance block — so the figure in the item below now **understates** it. | Small. Should abort after ~5 consecutive total failures. |
| Unset `ANTHROPIC_API_KEY` scores as 45 failures | Without the key, every call fails with a generic "Unexpected server error" naming neither authentication nor the variable — and the harness faithfully scores that as *"this model cannot write SQL, 0%."* A misconfiguration is indistinguishable from a bad model. Actually happened; voided a run. | Half-fixed in Session 221 (the cause is now in the log). The message still names nothing. |
| The gate measures only ONE of three dialect prompts | Session 217 told the model which SQL dialect to write for in three places. The gate checks the effect of exactly one of them. | Closing it needs a **new scorer and a new gate key** — a design change, not a wiring fix. |
| `SESSION_NOTES.md` shards past the read cap | Session 222 moved 24,564 lines of history into an archive. When an agent reads a file it **silently stops at 2,000 lines** — no error, no marker. A future session reading that archive gets 8% of it and cannot tell. The dashboard has a watch-list for exactly this, but it is a list of exact filenames and the archive is not on it. **Session 224 made it two archives, Session 228 a third, Session 231 a fourth, Session 235 a fifth and Session 239 a sixth** (933, 790, 976 and 1,057 lines) — the five newer ones read whole today, but are equally unwatched, and every future trim adds one more. | **Operator call.** The fix is one line in shared fleet tooling at `~/Development/methodology`, synced to 13 projects — not this repo's to edit. |
| The wiki publisher can erase the public wiki | The script that publishes the wiki mirrors a source directory with delete-what-is-missing semantics, and checks only that the directory **exists** — not that anything is in it. An empty source publishes an empty wiki, unattended, from a commit hook. | Small. Bundle with the row below. |
| The publish hook stays silent when it declines to publish | The hook decides whether to publish by matching a path prefix. A stale prefix, or any merge commit, makes it exit successfully having done nothing — and say nothing. | Small. Bundle with the row above. |
| Two finished plans still sit in the active-plans folder | `httpx-adapter-migration.md` was fully executed but never archived — and `repository-rename.md` went EXECUTED in the very commit that filed this item, which is the identical case and the heavier one. | Small, but moving either re-points every citation of its path — sweep first, and rule on both together. |
| ⚠ The enterprise fork's "is the clone independent?" check needs an operator ruling | The check that proves an enterprise copy carries no trace of this account greps for four name forms. The rename made one of them stop matching the case the check was built for. Both repairs anyone has proposed can never return zero, so the check has to be **restated**, and that is a call only the operator can make. | **Operator ruling.** The edit is minutes; the decision is the work. |
| Enterprise migration | Handing the project to an enterprise. Landing the branch, closing public exposure, removing LGPL dependencies, and the legal packet are **done**. What remains is the fork into an enterprise host. | Blocked on five decisions only the operator can make: destination host, import strategy, contributor agreement, wiki destination, and what happens to existing releases. |
| `probe_information_schema` says it "never raises" | Filed Session 223. A docstring promises graceful degradation; a third of the function body sits outside the `try` that would deliver it. Same defect class as the one fixed in Session 223. | Small, one file. Half of it is provable by inspection; half is defence-in-depth. |
| A bad `--db-url` fails silently | Filed Session 223. `connect()` builds a message naming the exact cause; the next line catches the error **without binding it** and throws the message away. The run then reports `COMPLETE` and exits 0 with **every quality check unexecuted**. A typo'd port, an unexported shell variable, and a genuine warehouse outage produce byte-identical reports. | Pre-existing and wider than the S223 fix — **not** a reason to revert it. The cheapest two-thirds is small; the third option changes when a pipeline run is allowed to "succeed" and needs an operator ruling. |
| CLI-adapter portability (`opencode` spec) | Not a bug — the umbrella record of the four-phase `opencode` adapter build. **All four phases are DONE.** It stays here as the provenance trail for the measurement items above. | Nothing to execute. |
| `sql_exec` — CLOSED | Historical marker, kept deliberately. Nothing to do. | Nothing to execute. |

**Also standing, not an item below:** `tests/eval/README.md` has three stale statements (`:49`, `:51-52`, `:86`), unfixed for a seventh session. $0, no risk.

---

## Open Items

### CLI-adapter portability — spec the `OpenCodeLLMClient` adapter

**Decision accepted by the operator, 2026-08-01:** extend the LLM provider seam (`LLMProvider` in both agents'
`factory.py` modules — currently `"anthropic"` | `"bedrock"`) with a new `"opencode"` branch, shelling out to the
`opencode` CLI (`github.com/anomalyco/opencode`) rather than calling an SDK directly. OpenCode is itself a
vendor-agnostic multiplexer (75+ model providers via the Vercel AI SDK / Models.dev), so one adapter unlocks many
underlying vendors through OpenCode's own config — the actual goal being prepared for is an enterprise environment
that may standardize on a different AI CLI than Anthropic's. Full research (four candidates compared: OpenCode,
Codex CLI, Gemini CLI, GitHub Copilot CLI — headless-mode syntax, structured-output support, auth mechanics,
portability verdicts, citations) and the decision record live in
`docs/wiki/model_project_constructor/AI-Dependencies.md` §9 and `docs/wiki/model_project_constructor/Architecture-Decisions.md`
AD-11 — read both before starting, so the next session doesn't re-derive the comparison.

**The spec is DONE (Session 211, 2026-08-01): `docs/planning/opencode-adapter-spec.md`.** It specifies
`OpenCodeLLMClient` for both packages as a **transport-method override** — subclass each package's
`AnthropicLLMClient` and replace only `__init__` plus `_call_json` (intake) / `_call_claude` (data agent), so every
prompt, dataclass builder, and `_extract_json` is inherited and prompt drift across providers is structurally
impossible. It carries the full interface contract, the error-mapping table (spawn failure / non-zero exit /
timeout / no-assistant-text / malformed JSON → `IntakeLLMError`/`LLMParseError`), a grep-based file inventory with
line numbers at `a3f33d8`, the test plan (including the drift guard C4 forces for the *new* duplicated helper
pair), a risk register, and four build phases. **AI-Dependencies.md §9.2's prerequisite is discharged:** the
`--format json` event stream is JSONL of shape `{type, timestamp, sessionID, ...payload}` with types
`text`/`reasoning`/`tool_use`/`step_start`/`step_finish`/`error`, pinned from OpenCode's own emitter source at a
recorded commit — see spec §3.2.

**Phase 1 (the live verification spike) is DONE (Session 212, 2026-08-01)** — `opencode` **v1.18.11** installed
(`npm i -g opencode-ai`), all seven probes run, six verbatim fixtures committed to `tests/fixtures/opencode/`, and
findings recorded as spec **§13 Appendix A** with §3/§4 annotated inline. Cost: $0.1295 over 16 billed calls. All
four `[unverified]` markers resolved — notably the replace-vs-append question behind the spec's largest design
risk: **partial replace**, a custom agent's prompt drops ~4,720 tokens of built-in persona but a constant
**~4,830-token scaffold survives** every call. D2 (folding the system prompt into the user message) was validated
end-to-end: the real `next_question` payload produced schema-valid output that parses with the project's own
unmodified `_extract_json`.

**⚠ Phase 1 also produced seven corrections to the spec (Appendix A.4), one of them a safety defect.** Hazard
H4's claim that "the default is already safe" is **false**: without `--auto`, a live run listed the sandbox, **read
a file and disclosed its contents**, exit 0. The tool-denying agent definition (with `read: deny`) is therefore
**mandatory, not defence-in-depth**, and the "caller supplied their own agent ⇒ adapter writes nothing" escape
hatch in §4.4 must be removed or hard-gated. Also corrected: stderr is empty on the error path (so §4.7's
`{stderr_tail}` message yields `""` — build it from the stdout `error` event's `name`/`message`/`ref`);
`step_finish` exposes `reason`/`tokens`/`cost`, which restores the truncation guard §3.3 declared impossible;
blind concatenation of `text` events picks up narration on multi-step runs; a malformed agent file fails as
usage-help-on-stderr with empty stdout; the sandbox needs a **runtime npm install** (so npm reachability is a
deployment prerequisite, sharpening §11 Q3); and sessions persist prompt/response text in a **global SQLite DB**
that survives sandbox deletion.

**Phase 2 (both clients, both factory branches, the registry entry, the deterministic tier) is DONE (Session 213,
2026-08-01)** — `"opencode"` is a live provider in both packages, shipped with all seven Appendix A corrections
applied. See `CHANGELOG.md`'s 2026-08-01 entry. Gate: **1100 passed + 8 live-skipped @ 97.79%**, mypy and ruff
clean. **Two as-built deviations**, both recorded in the spec: §4.4/§5.1's `agent=` escape hatch was **removed**
(not merely hard-gated) in favour of `agent_name`, which renames the generated tool-denying definition rather than
substituting a caller-owned one — so no constructor path reaches an unlocked agent; and §5.3's twin helpers take
the parsed event list rather than raw `stdout`.

**⚠ The adapter is wired but entirely unmeasured.** `anthropic` remains the default everywhere, and it must stay
that way: spec risk #1 (parses fine, quality silently degrades under the D2 prompt-role change) is untouched, and
no data-agent method has been exercised against OpenCode at all.

**Phase 3 (eval wiring + documentation) is DONE (Session 214, 2026-08-01)** — `"opencode"` is a candidate in the
Phase E cutover gate with all eight thresholds PENDING, and thirteen wiki pages plus `README.md`, `OPERATIONS.md`,
`.env.example` and the published `docs/tutorial.md` now describe a shipped third provider. Gate: **1110 passed + 12 live-skipped @ 97.79%**, mypy and ruff clean. **One deliberate
deviation from spec §7.4, chosen by the operator before implementation:** the credential probe requires the
`opencode` binary **and** `OPENCODE_EVAL_MODEL`, not the binary alone. Binary-only was unsafe — the binary is
installed globally on this machine and `addopts` carries no `-m 'not live'`, so it would have turned every
`uv run pytest -q` here into a billable live run while CI still looked hermetic. The same variable is the pinned
model id (new `provider_eval_model`, threaded through `test_eval_live.py` and `shadow_run.py`), which makes D6's
"every evaluated run passes an explicit model" true and discharges Phase 4's "operator names the model to pin"
pre-flight. Both the spec's §7.4 and its Phase 3 entry carry the correction inline.

**Phase 3b (unplanned — the eval harness could not drive the provider at all) is DONE (Session 215, 2026-08-01)**
— `a0c3930`. Phase 4 was blocked and nobody knew, because the live tier skips so no test could see it. The
stakeholder simulator reached through to `intake_client._client.messages.create`, which for this provider is the
`_UNUSED_SDK_CLIENT` placeholder that raises by design; the resulting bare `AttributeError` is not in
`interview_sweep._TRANSIENT_ERRORS`, so a shadow run would have **billed ~31 live calls and then aborted with no
report**, leaving `interview_convergence` and `interview_premature` unmeasurable. A second defect on the same path
would have run the simulated-stakeholder half of every interview on **no model** while the interviewer half ran
pinned. Fixed with a transport-shape-resolved `TextCompleter` seam; no production code touched; +11 hermetic
tests. Gate: **1121 passed + 12 live-skipped @ 97.79%**, mypy and ruff clean. See `CHANGELOG.md`'s 2026-08-01
entry and spec §9 Phase 3b.

**Phase 4 (the live shadow run + cutover decision) is DONE (Session 216, 2026-08-02) — verdict NO-GO,
`anthropic` stays primary.** 451 live calls pinned to `anthropic/claude-sonnet-4-6` (the baseline's own model id,
so the A/B isolates the transport change per §11 Q2), $13.99, 99.5 min, plus a 31-call same-session `anthropic`
governance+SQL refresh. **7 of 8 thresholds PASS; `sql_exec` FAILs at 42.9%.**

**The result that matters: spec risk #1 did not materialize.** The D2 prompt-role fold degraded nothing
measurable — `opencode` ties the baseline on governance (`cycle_time` 100%, laxer 0), `qc_structural` (100%),
`sql_parse` (100%), and **both interview thresholds** (`convergence` 100% at 20/20, `premature` 0). Cost profile
now quantified (risk #12): mean $0.0310/call, p99 latency 105.8 s, 4.4% of calls >60 s taking 14% of spend, only
8.4% of calls getting any prompt-cache read. See `tests/eval/PHASE_E_AGREEMENT_REPORT.md` §"Update — Session 216".

### `sql_exec` — CLOSED (Session 218): cause fixed S217, re-measured S218, both providers PASS

**Resolved.** Session 218 re-measured under the dialect fix at an N≥5-sampled denominator:
**`anthropic` 18/18 and `opencode` 34/34 executable, zero execution errors** — no `DATEDIFF`,
`PERCENTILE_CONT ... WITHIN GROUP`, `MEDIAN` or `ILIKE`. The entire S216 failure class is gone.
`SQL_EXECUTABLE_MIN` was never lowered; the SQL block simply got the same N≥5 sampling every other
capability already had (`4e2c8ec`, extracted to `tests/eval/sql_sweep.py`). 60 live calls, $0.63
measured + ~$1.00 estimated, 24 min. **The `opencode` cutover verdict flipped NO-GO → GO** — but
five of its eight cells are carried forward from S216, and **no production default was changed**.
See `tests/eval/PHASE_E_AGREEMENT_REPORT.md` §"Update — Session 218", including its six explicit
non-establishments. **What remains open is the cutover *decision*, not the measurement:** if the
swap is going to be taken, one session should measure all eight thresholds fresh.

The original entry follows as the historical record.

#### (historical) dialect cause FIXED (Session 217); the re-measure is what remains

**The root cause is closed.** Session 216 diagnosed `sql_exec` as a SQL *dialect* mismatch — both providers
emit competent *warehouse* SQL (`DATEDIFF(...)`, `PERCENTILE_CONT(...) WITHIN GROUP`, `MEDIAN(...)`), the eval
runs it on SQLite, and nothing in the data-agent prompt named the dialect. **Session 217 fixed it at the source
(`9c9fe35`), choosing the prompt fix over the warehouse-target-DB alternative:** the dialect is derived from the
database the caller configured (`ReadOnlyDB.dialect` / `sql_dialect_from_url`, parse-only, no connection) and
injected into the three SQL-emitting prompts. This also fixes **production**, where the same silence shipped —
the CLI and `scripts/run_pipeline.py` now derive it from `--db-url`. A 6-call live A/B on `anthropic` measured
**2/5 executable dialect-blind vs 4/4 dialect-aware**, and surfaced a fourth offender S216 had not seen:
**`ILIKE`**. Parse-validity was 100% in both arms — which is why it failed silently.

**What remains open — the re-measure, which this session deliberately did NOT do.** The probe is a diagnostic,
not a re-score: tiny n, model-chosen denominator, `anthropic` only, single run. **`SQL_EXECUTABLE_MIN` stays
0.95, the recorded 60.0% / 42.9% rates stand, and the `opencode` NO-GO stands.** Re-scoring means a full
`shadow_run.measure_provider` sweep (S216's cost `anthropic` + `opencode`: $13.99 / 99.5 min) and is a separate,
operator-authorized session. **Do not "fix" this by lowering `SQL_EXECUTABLE_MIN`** — the §5 rule is encoded in
`evaluate_cutover` and must not be relaxed to produce a green report.

**Still note when re-measuring:** the metric's denominator is model-chosen (how many queries the model writes),
so the rate moves run to run and the provider ordering *reverses* — sweep `anthropic` 3/5 = 60.0% vs `opencode`
3/7 = 42.9%; diagnostic re-run `anthropic` 2/4 = 50.0% vs `opencode` 4/7 = 57.1%. Report numerator and
denominator, never a bare rate. Reopening the `opencode` cutover decision is downstream of the re-measure.

**Still open on the adapter:** spec §11 Q1 (`DEFAULT_MODEL` shipped as `None`) — reversible in one line. The
non-Anthropic measurement that discharges `AI-Dependencies.md` §6.7's model-family diversification is a **second**
run and is now unblocked, since the transport itself is cleared on 7/8.

### The gate measures only ONE of the three dialect-injected prompts

**Found Session 218**, recorded rather than fixed (scope). Session 217 injected the dialect note into three
methods — `generate_primary_queries`, `generate_quality_checks`, `generate_baseline_query`. The Phase E gate
exercises the effect of exactly one:

| method | called by the gate? | scored how |
| --- | --- | --- |
| `generate_primary_queries` | yes | `sql_parse` + `sql_exec` — SQL is parsed **and executed**, so a dialect miss is visible |
| `generate_quality_checks` | yes | `qc_structural` only, which is `len(qc_lists) == n_primary_queries` — the QC SQL is **never parsed or executed** |
| `generate_baseline_query` | **never called** | no gate key exists |

`grep -rn "generate_baseline_query" tests/eval/` returns zero hits in any `.py`. The `kind: baseline` corpus case
(`subrogation_recovery_rate`, `corpus/sql_cases.yaml`) is filtered out of every live path by
`if case.kind != "primary": continue`; its only consumers are two deterministic oracle self-tests that score the
**human-authored** `reference_sql`, no LLM involved. So baseline-query dialect correctness is unmeasured, and QC
dialect correctness is unmeasured. Closing either means a new scorer (parse/execute the QC SQL) and, for the
baseline case, a gate key that does not exist yet — a design change, not a wiring fix.

### Re-measure `opencode` under the fixed (retry-symmetric) harness

**Unblocked by Session 221**, which closed the retry asymmetry that produced the S219 NO-GO. That
session deliberately **did not re-score** the verdict — a harness change made after seeing a disliked
number is how a gate stops being a gate (learning #86) — so the recorded verdict is still **NO-GO** and
the two failing cells in `tests/eval/PHASE_E_AGREEMENT_REPORT.md` are pre-fix numbers.

A GO produced by the fixed harness would be the first one resting on eight same-session cells **and** a
symmetric retry policy. Cost at S219's measured rates: **~$16.4, ~130 min** for the full eight-cell
`opencode` sweep (the SQL block alone is ~$1.78 / ~18 min per 5-sample pass — cost it at $0.0593/call,
not the $0.0318 global mean). **Its own session**, and read these before quoting anything it produces:

1. **Post-fix numbers are not comparable with S219's or S220's.** Best-of-3 turns a per-sample failure
   rate `p` into `p³` against unchanged bars. Quote `transient_retries` alongside every rate — it is
   what bounds the first-attempt rate. **Session 225 widened this**: the governance block now retries
   too, so the governance cells are non-comparable with **S216-S220**, a different span from the
   SQL/QC cells' S219-S220. Do not quote one rule for both. The same session added
   `governance_excluded_transient`, `governance_seam_failures` and `governance_transient_retries` to
   the driver's output — record all three, and remember that an exclusion can only move the
   zero-tolerance `governance_laxer_miss` **count** toward PASS.
2. **Do not lower `SQL_PARSE_VALID_MIN` or `QUALITY_CHECKS_STRUCTURAL_MIN`** (learning #82). Four
   sessions running have refused to calibrate a bar to a number.
3. **Source `.env`** — `set -a && . ./.env && set +a`. Without it every sample fails at $0 in ~36 s and
   the harness scores that as 45 model-quality failures (see the item below).

### Two live surfaces stay silent about a dropped or retried sample

**Filed Session 225**, found by the adversarial review of that session's own change and deliberately
not fixed there — the deliverable was the governance transient policy, and both of these are the
*interview* block, which the closed item pinned byte-stable. Two one-line changes, no money, no
threshold.

1. **`test_eval_live.py`'s interview gate passes no `on_event`.** `sweep_interview_convergence(
   load_interview_cases(), run_one)` at `tests/eval/test_eval_live.py:221` leaves `notify` at its
   no-op default, so every retry and exclusion note the sweep produces is discarded inside the gate
   that most needs them. This is the *identical* defect Session 221 fixed for the SQL test and
   Session 225 fixed for the governance test — the same file now has two call sites with a sink and
   one without. `shadow_run` has always passed `_warn` here (`shadow_run.py:157-159`), so only the
   assertion gate is blind.
2. **`shadow_run` reports no interview exclusion counter.** `measure_provider`'s returned mapping
   carries `sql_excluded_transient` and `governance_excluded_transient` but nothing for the
   interview sweep, even though `InterviewSweepResult.excluded_transient` exists and is populated.
   The interview denominator can therefore shrink invisibly in the agreement report — the exact
   condition `tests/eval/README.md` tells readers to check for. (The live *assertion* already prints
   it in its failure message; the *report* does not.)

**Both are diagnosability, not correctness:** no rate or count changes, and no verdict turns on
either. They are filed because a sink-less call site is how the Session 219 event became permanently
unattributable.

### The transient tiers key on exception class, so a glitch means different things per provider

**Filed Session 225** (reproduced by two independent refuters during that session's review, then
ruled out of scope by the panel — the mechanism is real, the severity ruling was "not this session's
defect"). **Pre-existing and wider than any one sweep: all three apply it.**

Every sweep splits transients into a *scored* tier (a seam error — the model produced something
unusable) and an *excluded* tier (a transport error — no model output exists to judge). The split is
made on the **exception class**, and only the SDK-backed providers (`anthropic`, `bedrock`) raise the
transport classes: `AnthropicLLMClient` lets `APITimeoutError` / `APIConnectionError` out of
`_call_json` unwrapped, which is what the excluded tier catches.

`OpenCodeLLMClient` is a subprocess adapter. Per the adapter spec's error-mapping table it converts
**spawn failure, non-zero exit, timeout, no-assistant-text and malformed JSON** all into
`IntakeLLMError` / `LLMParseError`. So for `opencode` a dropped connection or a killed process is
**scored a model-quality miss**, where the same real-world event on `anthropic` is *excluded*. Two
providers are judged by different rules on the same corpus against the same thresholds — and
`opencode` is the provider whose recorded verdict is NO-GO.

**This is not a reason to distrust the S216-S220 numbers on its own** — no measured event has been
attributed to it, and the exhaustion path requires three consecutive failures. It is a reason not to
compare a scored-tier count across providers without saying so.

**Sketch:** the fix belongs in the adapter, not the harness — give the subprocess client a distinct
exception for transport-shaped failures (spawn/exit/timeout) so the existing tier split can see them,
rather than teaching each sweep about provider internals. That changes shipped package code under
`mypy --strict`, so it is its own session. Until then, any surface quoting a scored-exhaustion count
should name the provider.

### A bare `KeyError` from a well-formed-but-wrong-keyed model response aborts the whole sweep

**Filed Session 221** (found while pricing the exception taxonomy), **not fixed** — it is shipped
package code under `mypy --strict`, out of scope for a harness session.

`packages/data-agent/src/model_project_constructor_data_agent/anthropic_client.py:203-215` builds
`PrimaryQuerySpec(name=str(item["name"]), sql=str(item["sql"]), purpose=…, expected_row_count_order=…)`
with **no guard**. A model that returns a well-formed JSON array of objects with the wrong keys raises a
bare `KeyError` — not an `LLMParseError` — so it is caught by no tier of the sweep's transient taxonomy
and **kills the run mid-sweep** instead of scoring one miss. The same gap sits at `:401-407`
(`rank_candidate_tables`).

**The intake twin already does this correctly:** `src/model_project_constructor/agents/intake/anthropic_client.py:439-440`
wraps the identical pattern in `_build_draft`. So the fix is to mirror an existing, shipped convention —
wrap in `try/except KeyError` and re-raise as `LLMParseError` — not to invent one. Add a regression test
per call site; the wheel's error-mapping tests live in `tests/data_agent_package/test_anthropic_client.py`.

### A bad or unreachable `--db-url` fails silently: exit 0, `COMPLETE`, and the message naming the cause is discarded

**Found Session 223** by the adversarial review of the `sql_dialect_from_url` fix — the reviewer asked
whether degrading to `None` is *safe*, which requires the real error to be reported somewhere, and
measured that it is not. **Filed, not fixed:** the remedy changes `DataReport` status semantics, which
gates the orchestrator's `FAILED_AT_DATA` halt — a design change across two packages, not a bug fix.

**The message exists and is thrown away.** `ReadOnlyDB.connect` builds exactly the right text:

```
DBConnectionError: cannot connect to 'postgresql://user:pw@host:$DB_PORT/claims':
  invalid literal for int() with base 10: '$DB_PORT'
```

Then `packages/data-agent/.../nodes.py:118-120` does `except DBConnectionError: return {"db_executed": False}`
— **without binding the exception**, so the text is unrecoverable. `agent.py:138-142` appends the fixed
string `"database unreachable at QC execution time; quality checks not executed"`, and `agent.py:147`
returns `status="COMPLETE"` unconditionally (the only non-COMPLETE statuses are `INCOMPLETE_REQUEST`
for a vacuous request and `EXECUTION_FAILED` when a node *raises* — and this path deliberately does
not raise). `src/model_project_constructor/orchestrator/pipeline.py:460` halts with `FAILED_AT_DATA`
only `if executed and data_report.status != "COMPLETE"`, so it never fires here.

**Measured consequences.** The data-agent CLI prints `wrote report.json (COMPLETE)` and exits 0. The
full pipeline prints `Status: COMPLETE`, generates all 38 project files, and exits 0. The report from
`@host:$DB_PORT/claims` is **byte-identical** (modulo `created_at`) to the report from a well-formed
but unreachable `@warehouse.invalid:5432/claims`. So three very different situations — a typo'd port,
an unexported shell variable, and a genuine warehouse outage — are indistinguishable to the operator
and to CI, and **every quality check silently goes unexecuted while the run reports success.**

**⚠ This is pre-existing and wider than the Session 223 fix — established by control, not by
assertion.** The reviewer who found it framed it as "the S223 fix is incomplete"; a second pass
**refuted that framing** by running the arm the first pass omitted. With the catch reverted to the
pre-fix `except sa.exc.ArgumentError:`, `--db-url 'not-a-url'` — an `ArgumentError` case that was
*always* caught and that the S223 change does not touch — produces the same `wrote report.json
(COMPLETE)`, exit 0, and the same canned concern. Post-fix, the reports from all three inputs
(bad port / `not-a-url` / well-formed-but-unreachable) are byte-identical modulo `created_at`. So
the indistinguishability is a property of the DB error path, not of that diff.

What S223 changed is only that the non-numeric-port case stopped being *uniquely* fatal and joined
the silent majority. Pre-fix it at least crashed with the cause in the traceback. **Do not read that
as an argument for reverting S223** — a raw `ValueError` traceback out of prompt construction is not
a diagnostic, and the inconsistency was the filed bug. It *is* the argument for closing this item.

**Options, ascending cost.** (a) Bind the exception at `nodes.py:119` and carry `str(e)` into
`data_quality_concerns` instead of the canned string — smallest, keeps `COMPLETE`, makes the cause
visible in the report. (b) Additionally warn at the derivation site when a non-`None` `--db-url`
yields a `None` dialect, so the *parse* failure is distinguishable from the *connect* failure.
(c) Give the report a status that makes `pipeline.py:460` halt — most correct, and the one with real
blast radius: runs that silently "succeed" today would start failing, which is the point but is an
operator-visible behaviour change and needs their ruling first. **Recommended: (a) + (b), leaving (c)
as a separate decision.**

### `probe_information_schema` says it "never raises" and can raise — same defect class as the S218/S223 one

**Found Session 223** by the blast-radius sweep that accompanied the `sql_dialect_from_url` fix — an
explicit search for *other* instances of that defect class. **Filed, not fixed:** one deliverable per
session, and this is a different function in a different module. It is the **only** same-class site
the sweep found in shipped code; everything else it flagged (`_extract_json`, the `_build_draft`
pairs, the `opencode_client._run` twins) was ruled LEAVE because those functions make no
graceful-degradation promise in a docstring, which is the third criterion of the class.

`packages/data-agent/src/model_project_constructor_data_agent/discovery.py:70` promises: *"Returns a
valid `DataSourceInventory` — never raises for probe failures."* Two escapes:

1. **Too-narrow `except` (read from source, not run).** The guard at `:80` is
   `except (SQLAlchemyError, NotImplementedError, RuntimeError)`, around `db.get_information_schema(...)`.
   That call reaches `ReadOnlyDB._reflect_entity` (`db.py:129-176`), which does unguarded dict
   subscripts — `fk["referred_table"]`, `fk["constrained_columns"]`, `fk["referred_columns"]`
   (`:150-152`), `col["name"]`, `col["type"]` (`:158`, `:162`) — on inspector-returned dicts. A
   dialect whose reflection dicts omit a key raises `KeyError`, which is not in the tuple.
2. **No `except` at all (provable from the code as written, and the larger half).** Lines `:96` and
   `:98-118` sit **outside** the try entirely. `:96` calls `_entry_from_reflection`, which subscripts
   `table["name"]`/`table["entity_kind"]` and constructs a pydantic model (`ValidationError`). `:99`
   calls `llm.rank_candidate_tables(...)`, which reaches `anthropic_client.py:395-408` and can raise
   `LLMParseError`, `KeyError` on `item["fully_qualified_name"]`, `ValueError`/`TypeError` from
   `float(item["relevance_score"])`, and any SDK error from `_call_claude`. **The only caller,
   `cli.py:204-209`, wraps it in `try:`/`finally:` with no `except` clause** — so
   `mpc-data discover --rank-with-llm` against a malformed LLM response is an uncaught traceback out
   of a function whose docstring says it never raises. This is the same shape as the defect closed in
   Session 223, and it shares a root cause with the `KeyError` item above.

**Sketch:** move `:96` and `:98-118` inside the existing try and widen the tuple — `KeyError` at
minimum, or `Exception`, since the handler already stringifies the error into `ProducerMetadata.notes`
so nothing is silently lost. ~20-40 changed lines plus 3-5 tests, one file, no public API change, no
caller change. **Honest caveat carried from the finding:** escape (1) is read-from-source and has no
measured trigger — unlike the `make_url` bug, nobody has produced a dialect that omits a reflection
key. Escape (2) needs no trigger; it is unguarded by inspection. Fix (2) with confidence; treat (1)
as defence-in-depth.

⚠ `discovery.py` is **not** twinned with an intake copy, so `tests/test_llm_json_parity.py`'s
pairwise battery does not force a matching edit — unlike most of this package's error-handling code.

### No circuit breaker on a systematically-failing live sweep

**Filed Session 221. Arithmetic revised Session 225 — the original figure now understates it.**
The S221 retry tripled the SQL/QC block: a sweep's 30 calls become up to 90 when every sample
exhausts. Against `DEFAULT_TIMEOUT_S = 600.0` (`opencode_client.py`), a timeout-shaped systematic
failure goes from ~2.5 h to ~7.5 h before the run reports anything. **Session 225 gave the governance
block the same retry**, so its 25 calls (5 cases x N_SAMPLES) become up to 75 on the same failure —
the worst case is now the sum over three blocks, not one. Note the ceiling is bounded by the timeout,
not by the retry count alone; the point stands either way and the number in this paragraph should be
re-derived, not quoted, when the breaker is built. The cheap, already-diagnosed signature to break on is the one from the item below —
a run whose calls are failing at $0 is an environment fault, not a measurement. **Sketch:** abort the
sweep with a named error after K consecutive exhausted samples (K ≈ 5), so the operator gets the
diagnosis in one minute instead of seven hours of billed nothing.

### An unset `ANTHROPIC_API_KEY` scores as 45 model-quality failures (`opencode` diagnosability)

**Found Session 220**, cost $0 to find and voided one probe run; **filed, not fixed** — that session was
measurement-only. Not a blocker: every committed live path already sources `.env`.

Running the SQL sweep against `opencode` **without `ANTHROPIC_API_KEY` in the environment** returns
**0/45 on `sql_parse`, `sql_exec` and `qc_structural` in 36 seconds at $0**, with every sample logging
`LLMParseError on primary queries -> parse+exec+qc fail`. Three facts combine:

1. `opencode auth list` reports **0 stored credentials** — the CLI has no auth of its own here.
2. `packages/data-agent/.../opencode_client.py:174` shells out via `subprocess.run(argv, **kwargs)` with
   **no `env=`**, so the child inherits the parent environment; `ANTHROPIC_API_KEY` is the only way an
   `anthropic/…` model authenticates.
3. Unauthenticated, the CLI exits 1 with
   `UnknownError: Unexpected server error. Check server logs for details. (ref=…)` — **a message that
   names neither auth nor the missing variable**, and which reads like a provider-side outage.

**Why it matters:** a misconfigured environment and a provider that genuinely cannot write SQL produce
**the same 0% on the same three gate keys**, and the fast-and-free signature (36 s, $0, 45/45) is only
obvious if someone thinks to check call count and spend. This is the same diagnosability class as the
retry asymmetry closed in Session 221 (see that `CHANGELOG.md` entry) — the harness cannot tell a seam
failure from a quality failure.

**Half-fixed, Session 221.** The cheap interim landed: both `sql_sweep.py` `notify(...)` calls now carry
`str(exc)`, so the `ref=…` reaches the log and the cause is searchable. **The item stays open** — the
message still names neither auth nor the variable, so a reader must already know what they are looking
at. Session 221 also **worsened the cost profile of this exact scenario**: the doomed run's call count
rises 45 → 135 as every sample burns its full retry budget (still ~$0 and fast, since the CLI fails in
under a second — but see the circuit-breaker item above, which this scenario is the motivating case for).

**Sketch:** have `OpenCodeLLMClient.__init__` (or the eval credential probe in `tests/eval/`) fail fast
with a named error when the selected model's provider prefix has neither a stored credential nor the
corresponding key in the environment.

### The `SESSION_NOTES.md` shard is past the agent read cap and nothing watches it

**Filed Session 222 by the session that created it**, deliberately not fixed there — the fix lives
upstream in a repository this project does not own.

`docs/architecture-history/SESSION_NOTES-through-S216.md` is **24,564 record lines** (24,590 total). An
agent `Read` of it truncates at 2,000 lines with **no error and no missing-data marker** — the exact
defect the trim was scoped to remove, relocated rather than eliminated. **Sessions 224, 228, 231, 235 and 239 widened this:**
there are now **six** unwatched shards. The second, `SESSION_NOTES-S220-through-S217.md` (804 lines), the
third, `SESSION_NOTES-S224-through-S221.md` (933 lines), the fourth,
`SESSION_NOTES-S227-through-S225.md` (790 lines), the fifth,
`SESSION_NOTES-S231-through-S228.md` (976 lines), and the sixth,
`SESSION_NOTES-S235-through-S232.md` (1,057 lines), are all under the cap today, so they read
whole — but they are unwatched for the same reason, and being under the cap is a property of a cut's size,
not a protection. Every future trim adds another unwatched path. (The 924 figure this item carried for the
third shard was wrong; 933 is the measured `wc -l`.) Verified: `READ_CAP_WATCHED`
(`methodology_dashboard.py:287-288`, consumed at `:1481`) is an **exact-path membership test** over
`SESSION_NOTES.md`, `CHANGELOG.md`, `HANDOFFS.md` and three `BACKLOG.md` locations. The shard is in
none of them, is not LOC-discounted as a framework doc (`FRAMEWORK_SEED_DOCS` is root-anchored,
`:684-690`), and raises no "large files" row either (that check gates on `ext in SOURCE_EXTS`,
`:2929-2936`). **So no tooling will ever warn about it.**

**What ships today is prose, and prose only:** the pointer block's second paragraph in
`SESSION_NOTES.md`, the corresponding paragraph of each shard's own banner, and the `CLAUDE.md`
adaptations subsection. Warnings in prose are weaker than one entry in a watched set — and the count
of files carrying them grows by one at every trim, which is the wrong direction.

**Why it was not fixed in Session 222.** The remedy is a `READ_CAP_WATCHED` entry (or a glob) in
`methodology_dashboard.py`, which lives at `~/Development/methodology` and is synced to 13 projects.
Editing it here is forbidden (`CLAUDE.md`; `NOTICE` §1) and editing it upstream is a change to shared
fleet tooling — **an operator call, not an implementer's**, and a different repository's session.

**Options, in ascending cost:** (a) add the shard's path to `READ_CAP_WATCHED` upstream — smallest,
but hardcodes one adopter's filename into fleet tooling; (b) make the watch a **glob** over
`docs/archive/**` and `docs/architecture-history/SESSION_NOTES-through-*.md` — generalises to every
adopter that ever shards a ledger, and is the shape the dashboard's own comment implies it wanted;
(c) accept prose-only and record the acceptance. **Recommended: (b)**, upstream, its own session in
the methodology repo. Note (b) also fixes the same blind spot for the 5 fleet projects that already
have shards under `docs/archive/`.

### `publish_wiki.sh` will wipe and push the live wiki from an empty source directory — unattended, from a git hook

**Filed Session 234 (Phase 5), from `repository-rename.md` §8.1 finding 2 (dragon 3). Re-verified at `HEAD`.**

`scripts/publish_wiki.sh:92` is `rsync -a --delete --exclude='.git/' "$SOURCE_DIR/" "$WIKI_CLONE/"`,
followed by `git add -A` (`:94`), a commit (`:102`) and `git push origin master` (`:104`). Its guards
check tools on PATH (`:46-51`), source directory **exists** (`:53-56`), clone exists (`:58-69`),
clone remote URL (`:71-77`), clone on `master` (`:79-84`) and clone clean (`:86-90`). `:53` tests
`[ ! -d "$SOURCE_DIR" ]` — **existence, not non-emptiness**. An existing-but-empty or
half-populated `docs/wiki/model_project_constructor/` passes every guard, `rsync --delete` empties
the clone, and the push publishes the deletion. It runs **unattended from `.githooks/post-commit`**.

**Fix:** one assertion before `:92` — count `*.md` under `SOURCE_DIR` and abort below a floor.
**Cost: small.** Bundle with the item below — same subsystem, same session.

### `.githooks/post-commit` fails open — a stale prefix or a merge commit silently publishes nothing

**Filed Session 234 (Phase 5), from `repository-rename.md` §8.1 finding 3 (dragon 4). Re-verified at `HEAD`.**

`.githooks/post-commit:18` decides whether to publish with
`git diff-tree --no-commit-id --name-only -r HEAD | grep -q '^docs/wiki/model_project_constructor/'`.
Two ways it exits 0 having done nothing, and says nothing either time: the prefix goes **stale**
(exactly the hazard Phase 4 had to move it through), and **any merge commit** — `diff-tree` on a
merge prints nothing without `-m`/`-c`, which is why every phase of the rename was pinned to a
direct commit on `master` (plan constraint K7). Either way wiki publishing stops quietly.

**Fix:** announce the decision not to publish instead of exiting 0 in silence. **Cost: small.**
Bundle with the item above.

### Two delivered plans are still filed under `docs/planning/` — `httpx-adapter-migration.md` and `repository-rename.md`

**Filed Session 234 (Phase 5), from `repository-rename.md` §8.1 finding 4.**
`docs/methodology/PROJECT_CONVENTIONS.md` §3: active plans live at `docs/planning/`, and when a
plan's primary scope is delivered it moves to `docs/architecture-history/`. This one's scope is
delivered and it has not moved.

**§8.1's framing is spent — do not carry it forward.** It said the file's *"2 old-name hits would
become historical the moment it is archived — which would shrink this rename's scope by one file.
Worth doing before execution if it is cheap."* Session 233's `1865fc2` rewrote both in place, so the
count is **0** and there is no rename saving left to collect. What remains is filing hygiene, plus
the question the move actually raises: archiving it re-points every citation of its path.
**Cost: small, but do the referrer sweep first** (`git grep -l 'httpx-adapter-migration'`), and it
needs an operator call on whether it moves at all.

**And it is now two files, not one.** `docs/planning/repository-rename.md` went **EXECUTED** in the
same commit that filed this item, so it is the identical case — a delivered plan still sitting in the
active-plans folder. It is the heavier of the two: it is cited from `CLAUDE.md`, `SESSION_NOTES.md`,
`enterprise-migration.md` and its own §7.2 allowlist, and **moving it would change a path that its own
completion criterion matches on**. Rule on both together, or on neither.

### ⚠ OPERATOR DECISION — the C4/C5 clone-independence criterion needs restating, and both proposed repairs are unsatisfiable

**Re-filed Session 234 (Phase 5). Raised by Session 229 as flag 1 against
[`docs/planning/enterprise-migration.md`](docs/planning/enterprise-migration.md); it was filed
inside the rename item, which Phase 5 deleted. It is still open, and it is not the rename plan's
call to make** (`repository-rename.md` §8 and dragon 1).

The criterion sits at `enterprise-migration.md:363`, `:1319` and `:1363` — **anchor on content, not
on those numbers, which drift every session**: `grep -n "a narrower pattern can pass"
docs/planning/enterprise-migration.md`. It greps
`'rmsharp|rmsharp\.github\.io|github\.com/rmsharp|claims-model-starter'` over the enterprise clone
and expects **0**. Its own comment says why it must stay wide: *"a narrower pattern can pass '→ 0'
while a hardcoded `claims-model-starter` string survives in the clone's publish_wiki.sh."*

**After the rename that hardcoded string is `model_project_constructor.wiki`, which no alternative
matches.** The URL alternatives still fire, so the check degrades rather than collapses — what it
stops catching is a bare, un-URL'd repository name, which is precisely the case its own comment
names.

- Adding `model_project_constructor` as a fifth alternative is **unsatisfiable: 1,980 lines across
  187 files** — it is the import package, the `src/` tree and the distribution stem.
- Dragon 1's own recommended repair — scope by path to `scripts/`, `.githooks/`, `mkdocs.yml` and
  `tests/` — is **also unsatisfiable: 350 hits, 284 of them legitimate
  `from model_project_constructor…` imports in `tests/`.**
- **Both figures were measured by Session 229 on 2026-08-20 and are quoted as of then, not as of
  now** — four commits and two rename phases have landed since, and dragon 1 records a third reading
  (1,916/183) from Session 226. **Re-derive before ruling; do not inherit** (learning #105). The
  numbers are quoted because their *order of magnitude* is the argument — every candidate pattern
  matches thousands of legitimate lines — and no ruling turns on the third digit. A criterion that can never return 0 is
  not a criterion, which is the objection dragon 1 raises against the fifth-alternative fix and
  which applies to its own proposal with a wider margin.
- **The path set that does work** is four of the files in `enterprise-migration.md` §2.6's
  host-and-identity coupling table — `scripts/publish_wiki.sh`, `.githooks/post-commit`,
  `mkdocs.yml`, `tests/test_wiki_no_line_citations.py` — the four where a hardcoded repository name
  is always a defect. (§2.6's table is longer than four; the rest couple on other literals.) Post-Phase-4 that set legitimately contains ~16 hits of the **new** name, so the criterion
  has to be restated as **"no repository name other than the clone's own"**, not "no name at all".

**The ask:** rule on that restatement. **Cost: the ruling is the work; the edit is minutes.**

### Enterprise migration (`docs/planning/enterprise-migration.md`)

Land the `feat/bedrock-mantle-migration` branch on `origin/master`, converge the three
documentation surfaces, and provision a one-time enterprise clone of the repository + wiki.
**Goals 1 and 2 (land the branch, close the public exposure) are complete** — Phases A1–A4 done
(Sessions 186–189, `41ab834`/`b27cc98`/A3's `35ccbd9`/A4's landing PR #2 → `master@9cabe0e`).
**Correction:** the prior version of this entry (written by Session 188) claimed A4 was still
open and that a later session would mark "Goals 1–2 done" here — that update never actually
landed (Session 189's close-out claimed it did; `git log -- BACKLOG.md` shows no commit between
Session 188's `35ccbd9` and this one touched this file). Fixed by Session 190.

**Plan-revision session done (Session 194, 2026-07-28):** `enterprise-migration.md` §1.3 now
reconciles the operator's 2026-07-27 sequencing decision (D3 + the "platform team" bucket — D4,
D5, D8, D9, D14, D15, D16 — resolved post-fork, inside the clone, not reported back to this
repository; the "security" bucket, D10/D13, is unaffected and stays live) with the plan's phase
gates, §3 Decision Register, dragon #20, §6, and §7. The phase list below reflects the revised
plan; the bullets below are a summary — `enterprise-migration.md` is authoritative.

**Phase C4's gate is now fully satisfied (Session 195, 2026-07-28):** B2 (below) is DONE. C4 can
run as soon as the operator supplies D9 (destination host), D5 (import strategy), D4 (DCO), D8
(wiki destination), and D16 (release disposition) live at that session's start — see
`enterprise-migration.md` Phase C4's "Before step 1" note and dragons #22/#24. This repository does
not pre-answer those five; whoever runs C4 gets them from the operator directly.

- **B1 — The legal packet.** **D3-independent core: DONE (Session 190)** — wiki LGPL mislabeling
  fixed, root `SECURITY.md`/`CODEOWNERS`/`THIRD-PARTY-LICENSES`/baseline `CONTRIBUTING.md`/`NOTICE`
  added, D1 attribution in place. **Full B1 (the corporate DCO/CLA mechanism section) is no longer
  a session this repository schedules** — per §1.3, it depends on D3/D4/D9, all deferred post-fork;
  it will be authored inside the enterprise clone, not here. B1's D3-independent core is the actual
  gate on Phase C4, and it's satisfied.
- **B2 — Import readiness.** **DONE (Session 195).** `.gitleaksignore` + classification table +
  secrets attestation + external-asset register at `audits/2026-07-28-b2-import-readiness.md`;
  `releases-export.json`/`prs-export.json` at repo root. The three GitLab pilot projects
  (`subrogation-pilot`, `-v2`, `-v3`) and the two GitHub Releases + tags are registered with a named
  disposition (undecided/D16 for the Releases and pilot projects — recreate-vs-pointer and
  migrate-vs-leave stay live D16/operator calls, not pre-decided). **The three `.env` credential
  rotations, originally flagged here as not done: RESOLVED as not required (Session 198)** — the
  rationale ("so the clone never depends on personal dev credentials") was wrong; Phase C4 step 1's
  `git clone --mirror` already carries zero credential values, so rotation was neither necessary
  nor sufficient. See `docs/planning/enterprise-migration.md` §1.4 and Phase C4 step 9 (corrected):
  the real requirement is provisioning `<enterprise-clone>` with enterprise-owned credentials at
  C4 time, not rotating the personal ones beforehand — no pre-fork action needed. The 162 MB
  `.git`/loose-objects fact from §2.9 is pre-existing repo state, not a B2 action item — `git clone
  --mirror` (C4 step 1) repacks on push regardless.
- **B3 — LGPL removal.** **DONE** (both LGPL SDKs removed via `docs/planning/httpx-adapter-migration.md`,
  Sessions 191–193 — see `CHANGELOG.md`'s 2026-07-27/2026-07-28 entries). D11 is moot; no further action.
- **C1 — Bedrock enterprise correctness.** **Narrowed by §1.3.** **D10 RESOLVED (Session 199):
  Regional. D13 RESOLVED (Session 200):** `require_sigv4` sub-scope only (guard completeness + env
  wiring), not `http_client`. **`bedrock-enterprise.md` §0's three security questions RESOLVED
  (Session 201, 2026-07-29, operator):** Guardrails not mandated, FIPS not mandated (mantle path
  confirmed correct — the plan's scope, which assumed "no" to both, was right), runtime quota
  expected yes (established enterprise account) but not independently verified. **Phase C1's own
  bundled scope is DONE (Session 202, 2026-07-29):** fixed the stale/false `base_url` claims in
  `bedrock-enterprise.md` §4 (it wrongly said the override "does not yet" exist, and wrongly cited
  `ANTHROPIC_BASE_URL` — the SDK's Bedrock-mantle client actually reads a different, mantle-specific
  var, `ANTHROPIC_BEDROCK_MANTLE_BASE_URL`, verified against the installed SDK 0.94.1 source);
  documented that var in `.env.example` and §7; extracted the §3 IAM policy into two standalone
  applyable JSON artifacts — `docs/deployment/bedrock-mantle-execution-role-permissions.json` (the
  real permissions policy) and `docs/deployment/bedrock-mantle-execution-role-trust.json` (the
  trust policy, `Principal` left an explicit D14-blocked placeholder, not guessed). **Phase C1 is
  now fully complete** — no scope remains; D14's trust-relationship fill-in is the enterprise
  clone's own post-fork work, per §1.3.
- **C2 — Runtime, network, and data-at-rest readiness.** **Narrowed by §1.3.** **D13 RESOLVED
  (Session 200) — D13 was this phase's only gate, so C2 is now fully ungated and schedulable.**
  D15's dependency (index-variable documentation) is carved out and deferred post-fork.
- **C2b — Deployment artifact.** **Out of scope for this repository (§1.3)** — its only gate (D14)
  is unanswerable here; this is now the enterprise clone's own future work, not a session this
  repository will schedule.
- **C3 — CI and supply-chain hardening** (targets the enterprise clone's own CI). Gated on **C4
  complete only** — D9/D15 no longer need a written answer here, but the operator must supply both
  live at C3's session start (same pattern C4 uses for D9/D5/D4). Still a session this repository
  schedules, even though its edits land inside `<enterprise-clone>`.
- **C3b — Generated-project CI portability.** **DONE (Session 205, 2026-07-29).** New `CIHostConfig`
  dataclass (base image, index URL, action prefix, pre-commit repo — default to today's public
  values) threaded through `governance_templates.py` → `WebsiteAgent` → the website agent CLI →
  `scripts/run_pipeline.py`'s new `MPC_CI_*` env vars, so pipeline-generated projects can target
  enterprise-internal hosts instead of Docker Hub / the public GitHub Actions marketplace / public
  PyPI / the public `astral-sh/ruff-pre-commit` mirror. Verified: fake-mode run with all four env
  vars set → 0 public-host matches across 39 generated files; unset → public values unchanged.
  See `docs/planning/enterprise-migration.md` Phase C3b for the full breakdown.
- **C4 — Enterprise clone provisioning ("the fork").** Gated on **A1–A4 complete (done), B1's
  D3-independent core complete (done), and B2 complete (done, Session 195) — the gate is fully
  satisfied**. D4/D5/D8/D9/D16 no longer need written answers here; the operator supplies them live
  at C4's session start.
- **C5 — Fork independence verification.** Gated on **C4 complete only** — D16 no longer a written
  pre-req; C5 records whatever the operator decided, live, inside the clone (not back into this
  repository's own tracking).
- **Executive summary / stakeholder readiness dossier — DONE (Session 196).** Requested by the
  operator, 2026-07-28; produced Session 196, 2026-07-28/29. Delivered as
  `executive-summaries/stakeholder-readiness-dossier.qmd` (+ reproducible `.html`/`.pdf` renders,
  gitignored per the `business-value-capture` precedent — the `.qmd` is the committed source of
  truth), covering all three requested sections: (1) business benefit of the pipeline, with an
  honest evidence/limits split (real engineering smoke-test traction vs. no claims-team adoption
  yet); (2) legal safety, re-derived fresh against D1/D2/D3 and the §2.7 licence table (MIT
  consistent, zero LGPL/GPL/AGPL, third-party methodology material under a documented permission
  grant) plus two open items surfaced independently — the generated-project license gap and the
  published wiki's own lack of a license (**both closed, Session 197** — see the dossier's own
  "Open items and owners" table); (3) enterprise-environment readiness across security,
  testing, data readiness, and Bedrock readiness, each split into resolved vs. genuinely open with
  named owners cross-referenced to the plan's §3 decision register and C1-C3 phases. Built via a
  research → draft → 4-lens adversarial verify → fix workflow; verify found 1 blocking gap (the
  wiki-license omission) and 4 minor gaps (an unsubstantiated third disposition option, and three
  "Unassigned"-owner claims that actually duplicate already-scoped C2/C3 phase items) — all fixed
  and spot-checked live before commit (commit counts, license files, LGPL-freedom, wiki license
  absence, and test-collection count independently re-verified, not just trusted from the
  sub-agent). **Phase-structure decision (resolved by this session, as the prior note left open):
  standalone document, not a new lettered A/B/C phase** — it does not gate or get gated by any
  phase; Phase C4's gate (A1–A4, B1-core, B2) remains independently satisfied. Recommendation
  stated in the document: proceed to the fork, carrying the open-items table forward.

**Open decisions this repository still tracks:** none, from either the D-numbered register or
`bedrock-enterprise.md` §0's three (non-D-numbered) security questions — **everything in the
security bucket is now answered.** **D10 (Bedrock endpoint Regional vs Global) is RESOLVED (Session
199, 2026-07-29): Regional** — operator accepted the recommendation; recorded in
`enterprise-migration.md`'s Decision Register and `bedrock-enterprise.md` §5, with the hard-block
residency SCP templated at `docs/deployment/bedrock-residency-scp.json` (specific region allowlist
still an open platform-team placeholder). **D13 (wire `require_sigv4`/`http_client` to app/env) is
RESOLVED (Session 200, 2026-07-29)** — its `require_sigv4` sub-scope only: the guard now checks
both SDK-recognized bearer-token env vars (`AWS_BEARER_TOKEN_BEDROCK` and `ANTHROPIC_AWS_API_KEY`,
was only the first) and defaults from a new `BEDROCK_REQUIRE_SIGV4` env var when not passed
explicitly; recorded in `enterprise-migration.md`'s Decision Register and `bedrock-enterprise.md`
§7. `http_client` wiring remains undone, as the recommendation itself deferred it pending
TLS-inspection confirmation. **`bedrock-enterprise.md` §0's three security questions are RESOLVED
too (Session 201, 2026-07-29, operator):** Guardrails not mandated, FIPS not mandated (mantle path
confirmed correct), runtime quota expected yes (established enterprise account) but **not
independently verified** — that verification needs live access to the actual enterprise account
and is carried forward as a flag, not a blocker, since C1's own remaining scope makes no live AWS
calls. **Phase C1 is now fully complete (Session 202, 2026-07-29)** — its own bundled scope (the
stale `base_url`/`ANTHROPIC_BASE_URL` doc fix, the §3 IAM-permissions-policy extraction into
applyable JSON artifacts) is done; see the C1 bullet above for the full breakdown. No scope remains
in this repository for C1. **Phase C2's gate was already cleared by D13 alone** (D13 was C2's sole
listed gate) — C2's own
scope (htmx vendoring, intake UI auth posture, the `MPC_HOST_URL` gap, plaintext-at-rest,
`run_pipeline.py:450`) is itself untouched but no longer blocked from starting.

**Decisions no longer tracked here (§1.3):** D1, D2, D6, D7, D11, D12 are already answered;
**D3, D4, D5, D8, D9, D14, D15, D16** are resolved by the operator after Phase C4 runs, inside the
enterprise clone, live — not written up in this repository's Decision Register, `BACKLOG.md`, or
`SESSION_NOTES.md`. Whoever runs C3/C4/C5 must get the relevant answers directly from the operator
at that session's start (`enterprise-migration.md` §4's "Before step 1" notes and dragon #22/#24).
See `docs/planning/enterprise-migration.md` §3 for the full Recommendation-column text, preserved
as forward context for whoever eventually answers these inside the clone.

---

Most recently completed: **`httpx-adapter-migration`** (`docs/planning/httpx-adapter-migration.md`)
— all three phases DONE and LANDED (Phase 1 GitLab: Session 191; Phase 2 GitHub: Session 193; Phase
3 optional rename: Session 203). Zero direct dependencies are LGPL as of Session 193's `9aad76b`.
Full per-commit breakdown in `CHANGELOG.md`'s 2026-07-27/2026-07-28/2026-07-29 entries.

Previously completed: **harden the `cycle_time` cadence definitions and corpus**
(gap #2 robustness follow-up) — Session 177 refined `CYCLE_TIME_DEFINITIONS` to
discriminate `tactical`/`operational` on **output purpose** (not run frequency) and
added the role≠frequency corpus case `claim_workqueue_triage` (live cycle_time 60/60 =
100%, gate assert PASS). The operator **deferred** the optional event-driven/episodic
`CycleTime` member (YAGNI — no corpus case needs it; a schema-`Literal` change with a
larger blast radius); reopen only if such a case arises. See `CHANGELOG.md` and
`tests/eval/PHASE_E_AGREEMENT_REPORT.md`.
