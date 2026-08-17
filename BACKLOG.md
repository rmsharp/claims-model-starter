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
   what makes the first-attempt rate recoverable.
2. **Do not lower `SQL_PARSE_VALID_MIN` or `QUALITY_CHECKS_STRUCTURAL_MIN`** (learning #82). Four
   sessions running have refused to calibrate a bar to a number.
3. **Source `.env`** — `set -a && . ./.env && set +a`. Without it every sample fails at $0 in ~36 s and
   the harness scores that as 45 model-quality failures (see the item below).

### The three live measurement blocks still apply three different transient policies

**Filed Session 221, deliberately not fixed there** — that session's deliverable was the SQL/QC half,
and widening it mid-session is the scope creep `SAFEGUARDS.md` exists to prevent. Session 221 closed the
SQL-vs-interview asymmetry and, in doing so, established that the problem is wider than the two blocks
`BACKLOG` had named:

| block | on a transient seam error | gate keys it feeds |
| --- | --- | --- |
| `interview_sweep.py:82-87,152-180` | retry 3x, then **exclude** | `interview_convergence` (0.95), `interview_premature` (≤0) |
| `sql_sweep.py` (S221) | retry 3x, then **score** a parse miss / **exclude** a transport miss | `sql_parse` (1.00), `sql_exec` (0.95), `qc_structural` (1.00) |
| `shadow_run.py:97-111` (governance loop) | **no retry** — scored an immediate non-agreement | `governance_cycle_time_agreement` (0.90), `governance_laxer_miss` (**≤0**) |
| `test_eval_live.py`'s governance test | **no handler at all** — the seam error aborts the gate | same two keys |

The governance rows are the sharp end: `GOVERNANCE_LAXER_MISSES_MAX = 0` is a **zero-tolerance** bar fed
by an un-retried transient, which is precisely the S219 shape that cost a cutover verdict. Worse, the
driver and the assertion gate disagree with *each other* — one scores the error, the other dies on it.

**Sketch:** give the governance loop the same treatment (`_call_with_retries` in `sql_sweep.py` is
already generic over the call; a shared helper is the obvious home, but note S221's finding that the
transient *tuples* cannot be shared — `interview_sweep`'s members are `RuntimeError` subclasses from the
intake package, `sql_sweep`'s is a `ValueError` from the data-agent wheel). Add a handler to
`test_eval_live.py`'s governance test so the two surfaces agree. **`interview_sweep.py` must stay
byte-stable** unless the session explicitly owns re-validating the recorded interview numbers.

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

### No circuit breaker on a systematically-failing live sweep

**Filed Session 221.** The retry the same session added tripled the worst case: a sweep's 30 calls
become up to 90 when every sample exhausts. Against `DEFAULT_TIMEOUT_S = 600.0`
(`opencode_client.py`), a timeout-shaped systematic failure goes from ~2.5 h to ~7.5 h before the run
reports anything. The cheap, already-diagnosed signature to break on is the one from the item below —
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

### Rename the repository `claims-model-starter` → `model_project_constructor`

**Operator ask, 2026-08-17 (Session 221), filed not executed.** Rename the GitHub repository
`rmsharp/claims-model-starter` to **`model_project_constructor`** and update every reference to the
old name **in currently exposed documentation**. The local working directory and the import package
are already `model_project_constructor`; only the *published* repository still carries the old name.

**The name form is underscores, and it is deliberate.** The operator corrected an initial
hyphenated reading (`model-project-constructor`) to `model_project_constructor` within the same
session. Note the divergence this creates and do **not** "fix" it: the PyPI-style distribution names
stay hyphenated (`pyproject.toml:2` `model-project-constructor`,
`packages/data-agent/pyproject.toml:2` `model-project-constructor-data-agent`), the import package
and the repository are underscored. Three naming conventions, one project, on purpose.

#### Evidence-based inventory (run 2026-08-17, Session 221; live at filing time)

**644 hits across 50 tracked files.** Counted per grep pattern, not as one total (learning #8) —
each form has a different fix:

| # | Pattern | Hits | What it is |
| --- | --- | --- | --- |
| 1 | `docs/wiki/claims-model-starter` | 509 | the wiki **source directory** path (25 pages) |
| 2 | `claims-model-starter.wiki` | 89 | the wiki **clone** name/URL (`<repo>.wiki.git`) |
| 3 | `github.com/rmsharp/claims-model-starter` | 35 | repository and wiki-page URLs |
| 4 | `rmsharp.github.io/claims-model-starter` | 25 | the **GitHub Pages** site URL |
| 5 | `Claims Model Starter` (title case) | 2 | published wiki titles — `_Sidebar.md:1`, `Home.md:1` |
| 6 | `claims_model_starter` (underscore) | 0 | this form does not exist; do not grep for it |

**Exposed surfaces — these change.** Everything below is either live config, an executable path, or
documentation a reader can reach today:

| File | Lines | What |
| --- | --- | --- |
| `mkdocs.yml` | `:3`, `:4`, `:5` | `site_url`, `repo_url`, `repo_name` — the Pages site moves |
| `README.md` | `:7`, `:9` | the repo-naming sentence itself, and the published-tutorial URL |
| `SECURITY.md` | `:9` | security-advisory URL |
| `CONTRIBUTING.md` | `:6` | Contributing wiki-page URL |
| `docs/tutorial.md` | `:218` | Intake-Interview-Design wiki URL |
| `scripts/publish_wiki.sh` | `:2`, `:11`, `:19`, `:23-24`, `:42`, `:44`, `:63`, `:72`, `:75` | `WIKI_CLONE` default, clone URL, `SOURCE_DIR`, **and the remote-URL guard** that greps for the literal `claims-model-starter.wiki` |
| `.githooks/post-commit` | `:3`, `:18` | the `git diff-tree \| grep '^docs/wiki/claims-model-starter/'` trigger |
| `tests/test_wiki_no_line_citations.py` | `:7`, `:38` | `WIKI_DIR` constant |
| `THIRD-PARTY-LICENSES` | `:50` | wiki path reference |
| `docs/style/statistical_terms.md` | `:7`, `:103`, `:137`, `:165` | wiki path references |
| `docs/methodology/PROJECT_CONVENTIONS.md` | `:11`, `:24`, `:25`, `:42` | wiki path references (project-owned, editable) |
| `executive-summaries/stakeholder-readiness-dossier.qmd` | `:57`, `:95` | wiki path references |
| `BACKLOG.md` | `:17` | wiki path reference (this file) |
| `docs/wiki/claims-model-starter/*.md` | 8 files, 12 hits | **published wiki content**: `_Sidebar.md`, `Home.md`, `Changelog.md`, `Contributing.md`, `Development-Workflow.md`, `Evolution.md`, `License.md`, `Software-Bill-of-Materials.md` |
| `docs/planning/enterprise-migration.md` | 43 hits | **an active plan, not history** — see dragon 3 |
| `docs/planning/opencode-adapter-spec.md`, `docs/planning/httpx-adapter-migration.md` | 5 hits | active plans |

**Historical records — these keep the old name.** Precedent: the SR 11-7 → SR 26-2 rename
(Session 144, `bfd9f36`) whose commit message states it outright — *"Historical records (root
CHANGELOG, SESSION_NOTES, architecture-history, audits, wiki Changelog Phase 4B entry,
banner-anchored Evolution) deliberately retain the old name."* Learning #32 is the general rule and
learning #60 says to derive this scope from the precedent diff, so **run
`git show --stat bfd9f36` before starting**:

`CHANGELOG.md` (117) · `SESSION_NOTES.md` (**0** since the Session 222 trim — its 293 hits moved
into `docs/architecture-history/SESSION_NOTES-through-S216.md` and are counted in the next entry) ·
`docs/architecture-history/*` (**418 across 21 files**, of which the shard is 293; was 125 across 20
before the trim) · `audits/*` (12) · `PROJECT_LEARNINGS.md` (2) · `prs-export.json`,
`releases-export.json` (1 each — frozen GitHub API exports, not prose).

**Session 222 note.** The trim moved hits between files; it changed no per-pattern total, so the
pattern table above stands unedited. It also does not change the rename's *scope* — the shard is a
historical record and keeps the old name, per the same S144 precedent. Two corrections while
re-deriving: **the headline "644 hits across 50 tracked files" was already low at filing time** —
`git grep -c` at the filing commit `5d906e9` gives **659 across 50**, and the same 659/50 holds at
`8bc3ef3`, at `f91f8e0` and post-trim. Re-derive rather than copy at execution time:
`git grep -c "claims-model-starter" -- . | awk -F: '{s+=$NF} END {print s}'`.

#### Sub-decisions the executing session must settle first

1. **Does the wiki source directory rename too?** `docs/wiki/claims-model-starter/` →
   `docs/wiki/model_project_constructor/`. It drives pattern #1 (509 hits) and is the difference
   between a ~60-hit change and a ~570-hit change. **Recommended: yes** — the directory is named
   after the repository, and the publish script pairs it with a clone whose name is derived from the
   repository (`<repo>.wiki.git`), so leaving it stale splits one name across two conventions.
   It is a `git mv` of 25 files plus four executable references (`publish_wiki.sh:44`,
   `post-commit:3,18`, `test_wiki_no_line_citations.py:38`); the remaining path hits are prose.
2. **Do the published wiki titles change?** `_Sidebar.md:1` "**Claims Model Starter**" and
   `Home.md:1` "# Claims Model Starter Wiki" are reader-visible branding, not paths. Renaming the
   repository does not automatically mean rebranding the wiki — **ask the operator.**
3. **Is this one session or two?** The exposed-documentation sweep and the wiki-directory `git mv`
   are separable. If sub-decision 1 is "yes", strongly prefer **two sessions**: sweep first, `git mv`
   second, so a bisect can separate a prose change from a path change.

#### ⚠ Dragons

1. **`SESSION_RUNNER.md:209` names `docs/wiki/claims-model-starter/` — and that file must not be
   edited.** It is synced from the canonical methodology repo and local edits block future syncs
   (`CLAUDE.md` → Project-Specific Methodology Adaptations). If sub-decision 1 is "yes", that line
   goes stale and **the correction belongs in `CLAUDE.md`'s adaptations section**, which exists as
   the customization seam for exactly this. Do not edit the synced file to "fix" it.
2. **`scripts/publish_wiki.sh:72-75` is a guard, not a comment.** It refuses to publish unless the
   clone's `origin` URL contains the literal string `claims-model-starter.wiki`. Rename the repo
   without updating it and **wiki publishing fails closed** — which is the safe direction, but it
   will fail on the very commit that lands the rename, via the `post-commit` hook.
3. **`docs/planning/enterprise-migration.md` is mid-execution and holds 43 hits**, including live
   `curl` verification commands against `rmsharp.github.io/claims-model-starter/…` (`:831-833`,
   `:1356`, `:1520`). Those are executable acceptance criteria for Phases C2/C4, not prose. Either
   update them in the same commit or the enterprise-migration executor runs stale checks. Also note
   that plan's **whole purpose is to fork this repository into an enterprise clone** — sequencing a
   rename against it is an operator call, not an implementer's.
4. **Out-of-repo surfaces the sweep cannot reach.** The wiki clone at
   `~/Development/claims-model-starter.wiki` (also tracked as its own project by the methodology
   dashboard, currently 16/100) must be re-cloned or have its remote re-pointed; the dashboard's
   project list will show the old name until it is. Any local clone needs
   `git remote set-url origin`.
5. **GitHub's redirect softens but does not remove the break.** Renaming leaves a permanent redirect
   from the old URL, so existing links and clones keep working — which means a half-done sweep will
   *look* fine indefinitely. Do not treat "the links still work" as evidence the sweep is complete.
   The Pages URL and the wiki clone URL are the parts that genuinely move.

#### Completion criteria

- `grep -rIl "claims-model-starter" . | grep -v '^\./\.git/'` returns **only** the historical-record
  files enumerated above — every remaining hit classified, none unclassified.
- `gh repo view --json nameWithOwner` → `rmsharp/model_project_constructor`.
- `curl -sf https://rmsharp.github.io/model_project_constructor/tutorial/` → HTTP 200.
- `scripts/publish_wiki.sh` runs clean against the re-pointed clone (it is idempotent; a no-op run is
  a pass).
- `uv run pytest tests/test_wiki_no_line_citations.py` passes (its `WIKI_DIR` still resolves).

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
