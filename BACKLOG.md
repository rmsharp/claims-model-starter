# Backlog

**Open work only.** Completed items move to `CHANGELOG.md` (chronological, session-numbered). Milestone-grouped summaries live in `ROADMAP.md`. **Do not leave checked-off `[x]` items here** — remove the line on completion and record the work in `CHANGELOG.md` per `docs/methodology/README.md` §templates (v2.1 three-file split).

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
`docs/wiki/claims-model-starter/AI-Dependencies.md` §9 and `docs/wiki/claims-model-starter/Architecture-Decisions.md`
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

### `sql_dialect_from_url` raises `ValueError` on a non-numeric port — breaks its own contract

**Found Session 218** while scoping the re-measure (adversarial blast-radius pass); **filed, not fixed**, by
operator decision — the session stayed scoped to measurement. Small and self-contained.

`packages/data-agent/src/model_project_constructor_data_agent/db.py` — `sql_dialect_from_url` catches only
`sa.exc.ArgumentError`, but `sa.make_url` calls `int()` on the port segment and raises a **bare `ValueError`**
for a non-numeric one. `ArgumentError` is not a `ValueError` subclass (`ArgumentError -> SQLAlchemyError ->
Exception`), so it escapes. Verified live:

```
sql_dialect_from_url("postgresql://u:p@host:$DB_PORT/claims")
  -> ValueError: invalid literal for int() with base 10: '$DB_PORT'
sql_dialect_from_url("not a url at all")   -> None      # the ArgumentError path works
```

**Why it matters:** the function's own docstring promises the opposite — "Returns `None` for a URL SQLAlchemy
cannot parse, so a malformed `--db-url` degrades to today's dialect-silent prompt **rather than raising here** —
the URL's real failure surfaces at `ReadOnlyDB.connect`, which is the error path callers already handle." Two
**production** seams pass a user-supplied URL straight in: `cli.py:129` (`db.dialect`) and
`scripts/run_pipeline.py:175` (`sql_dialect_from_url(db_url)`). A user whose `--db-url` carries an unexpanded
env-var port (`...@host:$DB_PORT/db`) or ODBC-style extras gets an uncaught `ValueError` instead of the clean
`DBConnectionError` the design intends. It is also evaluated *before* the DB is connected, so it pre-empts the
error path that was supposed to report it.

**Fix:** widen to `except (sa.exc.ArgumentError, ValueError)` — one line — plus a regression test for the
non-numeric-port case. Note `ValueError` is the broader catch and subsumes nothing else here that should
propagate; the function is parse-only and has no other failure mode worth surfacing.

**Not a blocker for the eval**: the eval DB URL is a well-formed `sqlite:///` path, so no measurement is
affected.

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

### The SQL/QC sweep does not retry transients — the interview sweep does (gap #1c, half-applied)

**Found Session 219, and it decided a cutover verdict.** The two live measurement blocks apply opposite
policies to the same class of failure — a transient malformed/truncated LLM response:

| block | policy on a transient LLM/seam error | effect on the rate |
| --- | --- | --- |
| `interview_sweep.py:82-87,152-180` | retry up to 3 attempts, then **exclude** the sample with a logged note | does not count against the rate |
| `sql_sweep.py:144-153` | **no retry** — record one parse miss + one exec miss + one QC miss, continue | counts as three immediate failures |

Session 169 fixed this for interviews (gap #1c) and the sibling block never got the treatment. Because
`SQL_PARSE_VALID_MIN` and `QUALITY_CHECKS_STRUCTURAL_MIN` are both **1.00**, a single blip is sufficient
to fail the gate outright.

**This is not hypothetical.** The Session 219 sweep hit exactly one `LLMParseError`
(`sql/property_severity[3/5]`) and two transient `IntakeLLMError`s. The interview transients were retried
and recovered (100%); the SQL one was scored as three failures and **produced the `opencode` NO-GO** —
`sql_parse` 29/30, `qc_structural` 14/15 — while every query and QC list the provider actually produced
was valid (29/29 parse, 29/29 executable, 14/14 QC).

**Quantified by the Session 220 variance probe: the deciding event is a ~1-in-60.** Three unmodified
`sweep_sql_capabilities` runs against live `opencode` (45 samples, 90 calls, $5.34, 53 min) hit **zero**
transients and scored **`sql_parse` 102/102, `sql_exec` 102/102, `qc_structural` 45/45 — 100% on all
three**. Rule of three bounds the per-sample rate at **≤6.7% (95%)**; pooled with S219 it is **1 event in
60 samples**. So a 1-in-60 blip decided a recorded cutover verdict, which is the argument for this item
rather than against it. **The verdict was deliberately NOT re-scored** (three of eight cells; S217's
"a probe is a diagnostic, not a re-score" precedent). See `tests/eval/PHASE_E_AGREEMENT_REPORT.md`
§"Update — Session 220".

⚠ **The probe could not attribute the S219 event, because it never recurred.** It was instrumented to
capture `str(exc)` (which `sql_sweep.py:146-148` discards, logging only the type) precisely so a
recurrence could be traced to one of the nine `LLMParseError` raise sites. **Whoever implements this fix
still does not know whether S219's event was transport (timeout/spawn/exit) or genuine malformed JSON** —
and that is exactly the distinction the A-vs-B design choice below turns on. Cheapest way to close it:
add `{exc}` to the two `notify(...)` calls as part of the fix, so the next occurrence is self-attributing.

**Two ways to implement it — this is a real fork, not a detail.** `LLMParseError` is raised at nine sites
covering five conditions (spawn failure / non-zero exit / timeout / no-assistant-text / malformed JSON —
the adapter spec's error-mapping table), and `IntakeLLMError` is its structural twin in the intake package
for the same five. **(A)** Retry the whole class, mirroring `interview_sweep` exactly: pure test-harness
change, matches the S169 precedent, but converts a genuine "model emits garbage JSON three times running"
into an exclusion. **(B)** Retry only the transport/process subset and keep real JSON-parse failures as
misses: says what is actually meant, but the exception type cannot distinguish them today, so it needs new
exception subtypes in **shipped** `packages/` code (or fragile message-sniffing) and implicitly reopens
gap #1c on the interview side. Note `sql_sweep.py:38-43` argues for today's behaviour **deliberately** —
so this item overturns a documented decision, and the rationale is that *the exception type is too coarse
to carry the policy*, not that S218 was careless.

**Fixing it is a harness change that will move a recorded verdict, so it must be its own session, and the
thresholds must not move with it.** Give `sweep_sql_capabilities` the `interview_sweep` treatment: a
`_TRANSIENT_ERRORS` tuple, bounded retries, exclude-with-note on exhaustion, and an `excluded_transient`
count on `SqlSweepResult` so exclusions stay visible rather than silently shrinking the denominator.
Then re-measure `opencode` — a GO produced by the fixed harness would be the first one resting on eight
same-session cells *and* symmetric retry policy. **Do not lower `SQL_PARSE_VALID_MIN` or
`QUALITY_CHECKS_STRUCTURAL_MIN`** — three sessions running have refused to calibrate a bar to a number,
and this is a denominator/policy defect, not a bar that is too strict (learning #82).

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
retry-asymmetry item above — the harness cannot tell a seam failure from a quality failure — and the two
should probably be fixed together.

**Sketch:** have `OpenCodeLLMClient.__init__` (or the eval credential probe in `tests/eval/`) fail fast
with a named error when the selected model's provider prefix has neither a stored credential nor the
corresponding key in the environment. Cheaper interim: add `{exc}` to `sql_sweep.py`'s two `notify(...)`
calls so the message reaches the log, where `ref=…` at least makes the cause searchable.

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
