# Wiki ↔ Code Accuracy Audit

**Date:** 2026-06-10 · **Session:** 134 · **Auditor:** Claude (Opus 4.8) via multi-agent workflow
**Subject:** Does the GitHub Wiki (`docs/wiki/claims-model-starter/`, 22 pages) accurately and completely reflect the current code — all features, the pipeline structure, and how to use it?
**Code under audit:** `master` @ `084a832` (Session 133) · **Wiki last edited:** `2b548a4` (Session 114) — **39 commits behind HEAD**

---

## 1. Audit Summary

**Verdict: No — the wiki is materially out of date with the code.** It was frozen at Session 114 and four architectural overhauls have landed since (E4 provider factory, O1 `STAGE_ORDER`, O3 `REPO_PLATFORMS` registry, O4 Literal-derived prompts), none of which appear anywhere in the 22 pages. Beyond omissions, several pages now make claims that are the *inverse* of reality and would cause concrete harm (data loss, broken procedures, copy-paste snippets that raise at runtime).

| Sub-question | Verdict | Basis |
|---|---|---|
| Fully reflects all **current features**? | **No** | E4 / O1 / O3 / O4 have **zero** wiki coverage; 6 of 8 post-S114 features under-documented |
| **Pipeline structure** documented accurately? | **Mostly** | Pipeline shape, governance flow, and GitHub-as-a-target are sound; but a few structural claims are now wrong (adapter-factory contradiction, `STAGE_ORDER` instructions that break the build) |
| **Usage** documentation current? | **Partially** | Resume mechanism documented backwards (causes data loss), latency unit wrong, fabricated env-var symptom, multiple runtime-breaking schema snippets |

**Headline numbers:** 22 pages reviewed · **94 candidate discrepancies flagged → 79 confirmed real** after adversarial verification (15 false-positives discarded) · severity split **16 high / 25 medium / 38 low** · **6 of 8** post-S114 features under-documented.

**Bottom line:** A wiki-refresh session is clearly warranted. The damage is uneven — `Agent-Reference`, `Extending-the-Pipeline`, and `Monitoring-and-Operations` need substantive rewrites; `Worked-Examples`, `Schema-Reference`, and `Security-Considerations` mostly need line-citation refreshes. Fix the actively-harmful contradictions first (data-loss/broken-procedure), then the undocumented E4/O3 features, then the long tail of stale numbers and citations.

---

## 2. Method

A read-only multi-agent audit (125 subagents). No file was modified during the audit.

1. **Publish-parity pre-check.** Confirmed the live GitHub Wiki is byte-identical to the `docs/wiki/` source (rsync dry-run: 0 drift; clone 0 ahead/0 behind `origin`). So this audit is about *content accuracy*, not sync — the stale content is genuinely what readers see.
2. **Per-page review (22 agents).** One agent per page read the page in full, read the corresponding code (each page mapped to specific source files), and classified every *technical* claim as `stale` / `missing-from-wiki` / `incomplete` / `accurate`, citing exact `file:line` on **both** sides. Narrative, design-rationale, and roadmap prose were explicitly out of scope.
3. **Adversarial verification (per finding).** Each flagged discrepancy was re-checked by an independent agent whose default verdict was *false-positive* — confirmed real only when the contradiction was citable on both sides. This discarded 15 of 94 candidates (16%).
4. **Completeness sweep (8 agents).** One agent per post-S114 feature grepped the entire wiki for any mention and judged coverage (`fully` / `partially` / `not-at-all`).
5. **Synthesis.** A final agent produced the verdict on the three sub-questions from the verified findings + coverage gaps only (no re-auditing).

**Why the wiki froze:** `git log -- docs/wiki/claims-model-starter/` shows the last content change was `2b548a4` (S114, schema-versioning resync). Every commit since — including all of E4/O1/O3/O4 — left the wiki source untouched, and the post-commit auto-publish hook only fires when a commit touches the wiki source, so there was nothing to trigger a refresh.

---

## 3. The Two Failure Classes

The 79 confirmed findings fall into two distinct classes, and they need different remedies:

**Class A — Now-false claims (56 `stale` + 18 `incomplete`).** The wiki describes a system that no longer exists. Worst offenders are *actively misleading*: a reader who follows them loses work or writes code that doesn't run. These are the high-severity items in §4.

**Class B — Undocumented features (5 `missing-from-wiki` + the 6 coverage gaps in §5).** Shipped, user-facing capabilities (most notably the `--provider` flag) that a reader cannot discover from the wiki at all.

A recurring root cause spans both classes: **hardcoded line-number citations** ("verbatim from `anthropic_client.py:35-51`") that drift silently as files grow. O3 inserting `REPO_PLATFORMS` ahead of existing code shifted citations across `Security-Considerations`, `Worked-Examples`, and `Intake-Interview-Design` by tens of lines. See §8 for the recurrence-prevention recommendation.

---

## 4. High-Severity Findings (16) — fix these first

These cause concrete harm: data loss, build-breaking instructions, or copy-paste snippets that raise at runtime. Full replacement text is included so a fix-session can apply them directly.

#### H1. `Agent-Reference` — Intake input is `InterviewSessionConfig` with fields user_id, session_id, problem_statement.

- **Wiki** `Agent-Reference.md:13-18`: Intake input is `InterviewSessionConfig` with fields user_id, session_id, problem_statement.
- **Reality** `src/model_project_constructor/agents/intake/agent.py:48-72`: No InterviewSessionConfig type exists. The intake graph is seeded via initial_state(stakeholder_id, session_id, domain, initial_problem); the facade IntakeAgent.run_with_fixture / run_scripted take stakeholder_id/session_id/interview_answers/review_responses/domain/initial_problem. The identity field is stakeholder_id, not user_id, and there is no problem_statement field (it's initial_problem).
- **Fix:**

Replace the Agent-Reference.md:11-18 "Input schema" block so it reflects the actual seed/facade surface (there is no config object). Suggested replacement:

```
### Input schema

The intake graph has no single config object. The headless facade `IntakeAgent.run_scripted` / `run_with_fixture` seeds the graph state via `initial_state(...)`:

initial_state
  stakeholder_id:  str         # session identity (NOT user_id)
  session_id:      str         # LangGraph thread_id
  domain:          str = "pc_claims"
  initial_problem: str | None  # stakeholder's initial description

run_scripted additionally takes:
  interview_answers: list[str]
  review_responses:  list[str]
```

Source of truth: src/model_project_constructor/agents/intake/state.py:61 (initial_state) and src/model_project_constructor/agents/intake/agent.py:48 (run_scripted). Apply the same correction to Pipeline-Overview.md:49 (drop the `InterviewSessionConfig` name; say "seeded via initial_state with stakeholder ID, session ID, domain, and initial problem"). Also update the Interfaces row Agent-Reference.md:63 `IntakeAgent().run(config)` — there is no `run(config)` method; the public methods are `run_scripted(...)` and `run_with_fixture(path)`.

#### H2. `Agent-Reference` — IntakeReport.estimated_value has fields low_estimate, high_estimate, confidence, assumptions.

- **Wiki** `Agent-Reference.md:34-38`: IntakeReport.estimated_value has fields low_estimate, high_estimate, confidence, assumptions.
- **Reality** `src/model_project_constructor/schemas/v1/intake.py:46-59`: EstimatedValue has narrative, annual_impact_usd_low, annual_impact_usd_high, confidence (Literal['low','medium','high']), assumptions, plus optional cost_of_inaction_narrative, annual_cost_of_inaction_usd_low/high, implementation_cost_band_usd_low/high, payback_months, value_drivers. There are no fields named low_estimate or high_estimate.
- **Fix:**

Update Agent-Reference.md:34-38 to match the EstimatedValue schema. Replace the four-field block with: `estimated_value: EstimatedValue` -> `narrative: str`, `annual_impact_usd_low: float | None`, `annual_impact_usd_high: float | None`, `confidence: "low" | "medium" | "high"`, `assumptions: list[str]`, and note the optional extension fields (`cost_of_inaction_narrative`, `annual_cost_of_inaction_usd_low`/`_high`, `implementation_cost_band_usd_low`/`_high`, `payback_months`, `value_drivers`). At minimum, rename `low_estimate`->`annual_impact_usd_low` and `high_estimate`->`annual_impact_usd_high`, add the required `narrative` field, and correct `confidence` from `str` to the `low|medium|high` Literal.

#### H3. `Agent-Reference` — Python interface for the intake agent is `IntakeAgent().run(config)`.

- **Wiki** `Agent-Reference.md:63`: Python interface for the intake agent is `IntakeAgent().run(config)`.
- **Reality** `src/model_project_constructor/agents/intake/agent.py:44-46`: IntakeAgent.__init__ requires an `llm` argument (IntakeAgent(llm=...)); there is no zero-arg constructor and no `run(config)` method. The public methods are run_with_fixture(fixture_path) and run_scripted(stakeholder_id=, session_id=, interview_answers=, review_responses=, ...).
- **Fix:**

Update Agent-Reference.md:63 to reflect the real API. Replace the Python interface cell with the actual constructor + method, e.g.: `IntakeAgent(llm=...).run_with_fixture("interview.yaml")` (fixture-driven path), and optionally note the lower-level `run_scripted(stakeholder_id=, session_id=, interview_answers=, review_responses=)`. The constructor must show the required `llm` (an IntakeLLMClient); there is no zero-arg form and no `run(config)`.

#### H4. `Agent-Reference` — DataRequest fields are target_variable, target_definition, granularity, features, population, time_range.

- **Wiki** `Agent-Reference.md:82-89`: DataRequest fields are target_variable, target_definition, granularity, features, population, time_range.
- **Reality** `packages/data-agent/src/model_project_constructor_data_agent/schemas.py:46-69`: DataRequest fields are target_description, target_granularity (a DataGranularity object with unit + time_grain enum), required_features, population_filter, time_range, plus required source (Literal['pipeline','standalone']) and source_ref, and optional database_hint, data_quality_concerns, data_source_inventory, and three baseline_metric_* fields. Names target_variable/granularity/features/population do not exist; schema uses extra='forbid' so a request built from the wiki would fail validation.
- **Fix:**

Replace the Agent-Reference.md:82-89 input-schema block with the current shape. For example:

DataRequest
  schema_version:      "1.0.0"
  target_description:  str
  target_granularity:  DataGranularity { unit: str; time_grain: "event"|"daily"|"weekly"|"monthly"|"quarterly"|"annual" }
  required_features:   list[str]
  population_filter:   str   (e.g., "auto claims closed in 2020-2024")
  time_range:          str
  source:              "pipeline" | "standalone"   (required)
  source_ref:          str                         (required)
  # optional: database_hint, data_quality_concerns, data_source_inventory, baseline_metric_name/definition + baseline_measurement_window

Also add a one-line note that StrictBase uses extra='forbid', so unknown/legacy field names raise a validation error. Source of truth: packages/data-agent/src/model_project_constructor_data_agent/schemas.py:46-69 (DataRequest) and 41-43 (DataGranularity).

#### H5. `Agent-Reference` — DataReport.primary_queries items (PrimaryQuery) have name, sql, quality_checks, datasheet; QualityCheck has...

- **Wiki** `Agent-Reference.md:98-105`: DataReport.primary_queries items (PrimaryQuery) have name, sql, quality_checks, datasheet; QualityCheck has name, sql, expected_result.
- **Reality** `packages/data-agent/src/model_project_constructor_data_agent/schemas.py:71-111`: PrimaryQuery has name, sql, purpose, expected_row_count_order (Literal tens/hundreds/thousands/millions), quality_checks, datasheet, inventory_entries_used. QualityCheck has check_name, check_sql, expectation, execution_status (Literal PASSED/FAILED/ERROR/NOT_EXECUTED), result_summary, raw_result — not name/sql/expected_result.
- **Fix:**

Update the code-fenced schema at Agent-Reference.md:98-105 to match schemas.py. For PrimaryQuery list under primary_queries: name: str; sql: str; purpose: str; expected_row_count_order: "tens"|"hundreds"|"thousands"|"millions"; quality_checks: list[QualityCheck]; datasheet: Datasheet (Gebru 2021); inventory_entries_used: list[str]. For QualityCheck: check_name: str; check_sql: str; expectation: str; execution_status: "PASSED"|"FAILED"|"ERROR"|"NOT_EXECUTED"; result_summary: str; raw_result: dict|None. (Optionally also reconcile the surrounding DataReport block, which omits schema_version, request, summary, created_at, and baseline_snapshot — outside the cited lines, but the same staleness.)

#### H6. `Agent-Reference` — Website RepoTarget has host ('gitlab'|'github'), namespace, project_name, visibility, host_url (str|None ov...

- **Wiki** `Agent-Reference.md:146-152`: Website RepoTarget has host ('gitlab'|'github'), namespace, project_name, visibility, host_url (str|None override for self-hosted).
- **Reality** `src/model_project_constructor/schemas/v1/repo.py:12-17`: RepoTarget has schema_version, host_url (a required str, not optional), namespace, project_name_hint (not project_name), and visibility. There is NO `host` field on the schema — host selection is a CLI flag (--host) resolved against the REPO_PLATFORMS registry, not a RepoTarget field. host_url is required, the opposite of the documented 'str | None'.
- **Fix:**

Rewrite the RepoTarget block at Agent-Reference.md:146-151 to match repo.py exactly:

RepoTarget
  schema_version:    "1.0.0"
  host_url:          str  (required; API base URL — defaults are resolved by the CLI from the REPO_PLATFORMS registry)
  namespace:         str  (GitLab group path or GitHub org/owner)
  project_name_hint: str
  visibility:        "private" | "internal" | "public"  (default "private")

Remove the `host` row entirely and add a note: host selection is not a RepoTarget field — it is the CLI `--host` flag ("gitlab" | "github"), validated against the REPO_PLATFORMS registry, which also supplies the default host_url. Rename project_name -> project_name_hint, change host_url from "str | None (override for self-hosted)" to required str, and add the schema_version field.

#### H7. `Contributing` — Current snapshot: 131 test functions across tests/ subdirectories (agents/intake/, agents/data/, agents/web...

- **Wiki** `Contributing.md:98`: Current snapshot: 131 test functions across tests/ subdirectories (agents/intake/, agents/data/, agents/website/, orchestrator/, schemas/, ui/intake/, data_agent_package/, fixtures/, scripts/, plus the top-level test_data_agent_decoupling.py).
- **Reality** `tests/ (705 functions total; e.g. tests/test_llm_json_parity.py, tests/test_vocab_guard.py, tests/orchestrator/test_stage_order.py, tests/agents/intake/test_factory.py)`: The suite now contains 705 test functions (grep -rhE '^\s*(async )?def test_' over tests/, with counts: orchestrator 201, website 137, data_agent_package 135, intake 83, schemas 81, ui/intake 22, scripts 17, data 16, plus 13 across three top-level files). The '131' figure was the count at wiki commit 2b548a4; 39 commits have landed since, adding many tests.
- **Fix:**

Update Contributing.md:98 to: "Current snapshot: **705 test functions** across `tests/` subdirectories (`orchestrator/` 201, `agents/website/` 137, `data_agent_package/` 135, `agents/intake/` 83, `schemas/` 81, `ui/intake/` 22, `scripts/` 17, `agents/data/` 16), plus 13 across the top-level files `test_data_agent_decoupling.py`, `test_llm_json_parity.py`, and `test_vocab_guard.py`." Better still, replace the hardcoded number with the reproducing command so it cannot drift again, e.g. "Run `grep -rhE '^\\s*(async )?def test_' tests/ | wc -l` for the current count (705 at time of writing)." Also drop `fixtures/` from the subdir enumeration since it contains no test functions.

#### H8. `Data-Guide` — Python API usage shown as `DataAgent().run(data_request)` (constructor called with no arguments).

- **Wiki** `Data-Guide.md:110-111`: Python API usage shown as `DataAgent().run(data_request)` (constructor called with no arguments).
- **Reality** `packages/data-agent/src/model_project_constructor_data_agent/agent.py:36`: DataAgent.__init__ requires `llm: LLMClient` as a mandatory positional argument (db is optional). `DataAgent()` with no args raises TypeError; a reader copying this snippet cannot construct the agent. A correct call needs a client, e.g. via make_llm_client('anthropic').
- **Fix:**

Update Data-Guide.md:110-111 to pass a constructed LLM client. Replace the two lines with:

from model_project_constructor_data_agent import DataAgent, make_llm_client
report = DataAgent(llm=make_llm_client("anthropic")).run(data_request)

(make_llm_client defaults provider to "anthropic", so make_llm_client() also works; naming it keeps the snippet self-documenting and mirrors the CLI --provider path.) Optionally add a one-line note that real use needs the anthropic API key in the environment, matching the lazy-import client construction.

#### H9. `Extending-the-Pipeline` — "There is no adapter factory. The Website Agent receives the RepoClient instance directly from its caller.....

- **Wiki** `Extending-the-Pipeline.md:142-144`: "There is no adapter factory. The Website Agent receives the RepoClient instance directly from its caller... The scripts/run_pipeline.py entry point selects the adapter via the --host flag. A new host value requires updating that selection code path."
- **Reality** `src/model_project_constructor/orchestrator/config.py:56,59-69,72-84,94-105; scripts/run_pipeline.py:295-297; src/model_project_constructor/agents/website/cli.py:177`: An adapter factory now exists. Overhaul O3 added PlatformSpec.adapter_factory to the REPO_PLATFORMS registry; each host's spec carries a Callable[..., RepoClient] (_make_gitlab_adapter / _make_github_adapter). Both the pipeline script and the website CLI build the adapter via REPO_PLATFORMS[host].adapter_factory(host_url=..., private_token=...), NOT a hand-written --host branch. Adding a host means adding one PlatformSpec entry to the registry, not editing a selection code path.
- **Fix:**

Rewrite Extending-the-Pipeline.md:142-144 ("Wiring and selection") to describe the registry-driven factory instead of a hand-written --host branch. Suggested replacement:

"### Wiring and selection

Adapter selection is driven by the `REPO_PLATFORMS` registry in `src/model_project_constructor/orchestrator/config.py`. Each `PlatformSpec` carries an `adapter_factory: Callable[..., RepoClient]` that lazy-imports its SDK and constructs the adapter via the uniform `(*, host_url, private_token)` signature. Both live entry points build the client the same way — `client = REPO_PLATFORMS[host].adapter_factory(host_url=..., private_token=...)` (`scripts/run_pipeline.py:295` and `agents/website/cli.py:177`); there is no if/elif `--host` dispatch.

To add a host you do NOT edit a selection code path: add one `PlatformSpec` entry to `REPO_PLATFORMS` (with `default_api_url`, `token_env_var`, and a `_make_<host>_adapter` factory) and add the host string to the `HostLiteral` alias (the import-time `assert_vocab_parity` guard pins the two together). `cli.VALID_HOSTS` and the pipeline argparse `choices` are already derived from `REPO_PLATFORMS.keys()`, so they update automatically. The Website Agent still receives the constructed `RepoClient` directly from its caller — see `agents/website/agent.py`.

Note: `run_pipeline.build_repo_target` retains a `host == \"github\"` branch (`run_pipeline.py:122`), but that selects the default *namespace* (deployment policy), not the adapter; you may optionally add a per-host namespace default there."

#### H10. `Extending-the-Pipeline` — "The pipeline has four designed extension surfaces: adding a new agent, adding a new repository-host adapte...

- **Wiki** `Extending-the-Pipeline.md:3`: "The pipeline has four designed extension surfaces: adding a new agent, adding a new repository-host adapter, adding a new governance artifact, and adding a new regulatory framework. Each surface has an explicit boundary — a Protocol, a registry, or a tier-gate function."
- **Reality** `src/model_project_constructor/agents/intake/factory.py:30-64; packages/data-agent/src/model_project_constructor_data_agent/factory.py:31-64; scripts/run_pipeline.py:447-455; packages/data-agent/src/model_project_constructor_data_agent/cli.py:106-110`: A fifth extension surface now exists and is not documented: adding a new LLM provider. Overhaul E4 introduced make_llm_client factories in BOTH agents (intake and data), each gated by an LLMProvider = Literal["anthropic"] whose member set is single-sourced via typing.get_args, plus a --provider CLI flag. Adding a provider = one new client module + one branch in make_llm_client + one member in the LLMProvider Literal — the same 'explicit boundary' shape (a factory + a Literal) the page documents for the other four surfaces.
- **Fix:**

Two coordinated edits. (1) On Extending-the-Pipeline.md:3, change "four designed extension surfaces" to "five", and add "adding a new LLM provider" to the enumeration; keep the boundary clause but widen it to acknowledge the factory ("a `Protocol`, a registry, a tier-gate function, or a provider factory"). (2) Add a new section "## 6. Extension surface: adding a new LLM provider" mirroring the §3 adapter pattern, documenting: the two PARALLEL (not shared) factories — src/model_project_constructor/agents/intake/factory.py and packages/data-agent/.../factory.py — each with `LLMProvider = Literal["anthropic"]` single-sourced via `get_args`; the recipe (one new client module implementing IntakeLLMClient/LLMClient, one branch in make_llm_client, one member in the LLMProvider Literal, in BOTH packages); the lazy-import convention that keeps the seam anthropic-free at import time; and the two CLI surfaces (run_pipeline.py --provider and the data-agent CLI --provider). Cross-reference and update Intake-Interview-Design.md:265,273 so the older "implement IntakeLLMClient directly" prose points at the new factory seam rather than implying the call sites must be edited. Optionally add a Changelog [Unreleased] entry for the E4 provider factory.

#### H11. `Intake-Interview-Design` — Quotes the interviewer system prompt as 'verbatim from src/model_project_constructor/agents/intake/anthropi...

- **Wiki** `Intake-Interview-Design.md:16-18`: Quotes the interviewer system prompt as 'verbatim from src/model_project_constructor/agents/intake/anthropic_client.py:35-51', ending at '...decision rights for retire/retrain.'
- **Reality** `src/model_project_constructor/agents/intake/anthropic_client.py:42-110`: The interviewer system prompt is materially longer than the quoted text and lives at different lines. `_INTERVIEWER_BASE` spans lines 42-71 and continues PAST 'retire/retrain' with a full data-source-discovery probing block (probe for concrete named systems: Guidewire ClaimCenter, Duck Creek Claims, policy admin, billing, subrogation tools, fraud/SIU scoring, CRM, EDW/data lake; surface owning team + refresh cadence). `SYSTEM_INTERVIEWER` (line 110) then APPENDS `_STATISTICAL_TERMS_NOTE` (lines 80-108), a statistical-terminology glossary (probability vs likelihood, statistical vs practical significance, two senses of bias, P&C senses of risk, accuracy vs precision, overfitting, class imbalance). The actual SYSTEM_INTERVIEWER the agent sends is roughly triple the quoted length.
- **Fix:**

On Intake-Interview-Design.md:16, (1) drop the word "verbatim" — replace with "the opening of the interviewer system prompt (`SYSTEM_INTERVIEWER`)"; (2) fix the citation: the assembled prompt is `SYSTEM_INTERVIEWER = _INTERVIEWER_BASE + _STATISTICAL_TERMS_NOTE` at `anthropic_client.py:110`, where `_INTERVIEWER_BASE` is lines 42-71 and `_STATISTICAL_TERMS_NOTE` is lines 80-108; (3) either show the full prompt or explicitly mark the quote as the opening excerpt and add two sentences noting (a) the prompt continues with a data-source-discovery probing block that names concrete P&C systems (Guidewire ClaimCenter, Duck Creek Claims, policy/billing/subrogation/SIU/CRM, EDW/data lake) plus owning-team and refresh-cadence — the part that makes intake feed the data agent — and (b) `SYSTEM_INTERVIEWER` appends a statistical-terminology glossary (`_STATISTICAL_TERMS_NOTE`) so drafts use precise terminology. A faithful citation pattern already exists for the governance prompt on line 26 (`anthropic_client.py:121-128` → actually 128-135 now, worth re-checking separately).

#### H12. `Monitoring-and-Operations` — Metrics capture `agent_latency` (seconds) per agent.

- **Wiki** `Monitoring-and-Operations.md:69`: Metrics capture `agent_latency` (seconds) per agent.
- **Reality** `src/model_project_constructor/orchestrator/metrics.py:39 (and :87, :137)`: Latency is recorded and stored in MILLISECONDS, not seconds. `record_agent_latency(self, agent, duration_ms)` and `LatencySamples` is documented as 'Running aggregates for one agent's latency (milliseconds)'; the measured-runner multiplies perf_counter delta by 1000.
- **Fix:**

Edit Monitoring-and-Operations.md:68 to change "`agent_latency` (seconds) per agent" to "`agent_latency` (milliseconds) per agent — count / mean_ms / max_ms aggregates", matching LatencySamples and record_agent_latency(agent, duration_ms). Optionally fix the wiki_ref line number to 68.

#### H13. `Monitoring-and-Operations` — Re-run with the same `run_id` to load existing checkpoints and resume from the next agent. A fresh `run_id`...

- **Wiki** `Monitoring-and-Operations.md:48`: Re-run with the same `run_id` to load existing checkpoints and resume from the next agent. A fresh `run_id` starts from scratch.
- **Reality** `src/model_project_constructor/orchestrator/pipeline.py:318,176; scripts/run_pipeline.py:49,466`: Resumption is NOT automatic on run_id reuse. `run_pipeline` resumes only when `config.resume_from` is set, which defaults to None; with `resume_from=None`, `_should_run` returns True for every stage, so all stages re-execute. The supported resume path is the explicit `--resume <run_id>` CLI flag in scripts/run_pipeline.py, and a plain same-run_id re-run overwrites the prior checkpoints (checkpoints.py docstring: 'Re-running a pipeline with the same run_id overwrites the previous checkpoint').
- **Fix:**

Replace the "### Re-running" body (Monitoring-and-Operations.md:46-48) with the actual mechanism, e.g.: "Resuming is NOT automatic on run_id reuse. Re-running with the same `run_id` and no `--resume` flag re-executes every stage and OVERWRITES the existing checkpoints (you lose prior work). To resume an interrupted run, pass `--resume <run_id>`: the CLI reads `<checkpoint_dir>/<run_id>/`, finds the first missing/incomplete envelope via `determine_resume_point`, loads the completed predecessor stages, and re-executes from there. `--resume` overrides `--run-id`, and rejects when the checkpoint directory is missing or the run is already complete. A fresh `run_id` (the default, auto-generated) always starts from scratch. See OPERATIONS.md §5 and scripts/run_pipeline.py `--resume` for full details." Optionally cross-link the existing "Diagnosing a failed run" file-presence table to the `--resume` flag.

#### H14. `Monitoring-and-Operations` — Troubleshooting symptom `MPC_HOST_TOKEN not set` -> Missing env var -> Set GITLAB_TOKEN or GITHUB_TOKEN.

- **Wiki** `Monitoring-and-Operations.md:138`: Troubleshooting symptom `MPC_HOST_TOKEN not set` -> Missing env var -> Set GITLAB_TOKEN or GITHUB_TOKEN.
- **Reality** `src/model_project_constructor/orchestrator/config.py:231-234,94-105`: There is no `MPC_HOST_TOKEN` env var and no error string of that form. The token is read from the per-host env var in REPO_PLATFORMS (GITLAB_TOKEN / GITHUB_TOKEN), and `require_host_token` raises `"{var} is required for host={self.host!r} but was not set"` where var is GITLAB_TOKEN or GITHUB_TOKEN.
- **Fix:**

Replace the fabricated symptom in Monitoring-and-Operations.md:138 with the real ConfigError text emitted by require_host_token (config.py:233). Change the row to: | `ConfigError: GITLAB_TOKEN is required for host='gitlab' but was not set` (or GITHUB_TOKEN for host='github') | Missing host API token | Set `GITLAB_TOKEN` or `GITHUB_TOKEN` |. This mirrors TROUBLESHOOTING.md:202 and lets operators successfully grep their logs for the actual string.

#### H15. `Schema-Reference` — The IntakeReport schema block lists its complete field set: schema_version, status, missing_fields, busines...

- **Wiki** `Schema-Reference.md:195-214`: The IntakeReport schema block lists its complete field set: schema_version, status, missing_fields, business_problem, proposed_solution, model_solution, estimated_value, value_measurement_plan, governance, stakeholder_id, session_id, created_at, questions_asked, revision_cycles.
- **Reality** `src/model_project_constructor/schemas/v1/intake.py:88-94,116`: IntakeReport has an additional field `qa_pairs: list[QAPair] = Field(default_factory=list)` carrying the raw interview transcript, and a new nested class `QAPair(StrictBase){question: str; answer: str}`. Neither the field nor the class appears anywhere on the page.
- **Fix:**

In docs/wiki/claims-model-starter/Schema-Reference.md: (1) Add `qa_pairs: list[QAPair] = Field(default_factory=list)` as the final field inside the IntakeReport code block (after line 213, before the fence on line 214). (2) Add a `QAPair` schema entry near the IntakeReport section showing `class QAPair(StrictBase): question: str; answer: str`, with a one-line note that it carries the raw interview transcript and is consumed by `intake_qa_pairs_to_inventory` in orchestrator/adapters.py. (3) Add a bullet in the IntakeReport notes (lines 216-219): "`qa_pairs`: optional (defaults to empty); the raw question/answer transcript, scanned by the interview-derived DataSourceInventory producer." (4) Update the §13 key-files table (line 641) intake.py row to include `QAPair`.

#### H16. `Schema-Reference` — The DataRequest schema block enumerates its fields as: schema_version, target_description, target_granulari...

- **Wiki** `Schema-Reference.md:244-257`: The DataRequest schema block enumerates its fields as: schema_version, target_description, target_granularity, required_features, population_filter, time_range, database_hint, data_quality_concerns, data_source_inventory, source, source_ref.
- **Reality** `packages/data-agent/src/model_project_constructor_data_agent/schemas.py:63-65`: DataRequest also declares three baseline-projection fields between data_source_inventory and source: `baseline_metric_name: str | None = None`, `baseline_metric_definition: str | None = None`, `baseline_measurement_window: str | None = None` (projected from the upstream ValueMeasurementPlan; 'all three present together or all three None'). They are absent from the wiki block.
- **Fix:**

In the DataRequest code block (Schema-Reference.md:244-257), insert the three fields between `data_source_inventory` (line 254) and `source` (line 255), preserving their grouping and the invariant comment, e.g.:

    data_source_inventory: DataSourceInventory | None = None

    # Projected from the upstream IntakeReport.value_measurement_plan
    # (the data agent cannot import IntakeReport; the orchestrator adapter
    # copies them in). All three present together or all three None.
    baseline_metric_name: str | None = None
    baseline_metric_definition: str | None = None
    baseline_measurement_window: str | None = None

    source: Literal["pipeline", "standalone"]

Then add one bullet to the prose under the block (after the data_source_inventory bullet at line 261): note that baseline_metric_* are the request-side inputs that drive the data agent's baseline-collection path and produce DataReport.baseline_snapshot (cross-reference the BaselineSnapshot section at line 389 and ValueMeasurementPlan at line 153). This closes the gap between the documented intake-side ValueMeasurementPlan, the request-side carrier, and the report-side BaselineSnapshot.


---

## 5. Feature Coverage Gaps (post-S114)

Coverage of the 8 features that landed after the wiki froze. **6 of 8 are under-documented.** (The two that *are* well-covered — GitHub-as-a-target and `--fake-llm` offline mode — are the reassuring counter-evidence that the wiki was accurate as of S114.)

| Feature (landed after S114) | Coverage | Sev | Gap |
|---|---|---|---|
| E4 `--provider` flag + `make_llm_client` factory | **not-at-all** | medium | A full grep of the wiki tree (docs/wiki/claims-model-starter/, 22 pages) returns zero hits for `--provider`, `make_llm_client`, `LLMProvider`, or `KNOWN_PROVIDERS`. Three places that should carry this feature are silent or now stale: 1. CLI-flag docs are… |
| O1 `STAGE_ORDER` + `run_pipeline` decomposition | **not-at-all** | medium | All O1 machinery landed in Sessions 120-122 (commits ac9d383, 623b833, b2e174b), entirely after the wiki snapshot at 2b548a4 (Session 114), so none of it is documented. Undocumented surface: (1) STAGE_ORDER as the single source of stage… |
| O3 `REPO_PLATFORMS` adapter registry | **not-at-all** | high | The registry-based adapter routing introduced in O3 is undocumented, and the wiki actively contradicts the shipped code. Extending-the-Pipeline.md:144 says verbatim: "There is no adapter factory. ... The scripts/run_pipeline.py entry point selects the adapter… |
| GitHub repo support (target platform) | **fully** | medium | The headline question — is GitHub documented as a target platform? — is answered comprehensively: the original GitLab-only vision has already been superseded throughout the wiki, which presents "GitLab or GitHub" consistently across at least eight pages,… |
| O4 Literal-derived prompt enumerations | **not-at-all** | medium | O4 landed in two commits (6d68380 intake, b767122 data-agent) AFTER the wiki froze at 2b548a4 (Session 114), so no wiki page describes it. The wiki documents the schema Literals themselves — Schema-Reference.md lists CycleTime, RiskTier, ModelType,… |
| `--fake-llm` / fixture offline mode | **fully** | low | The offline/fake-mode feature is well and accurately documented: FakeRepoClient, the fixture-driven default ("no API keys needed" / "no network calls"), --live as the opt-in to real hosts, and FixtureLLMClient/intake fixture mode all appear across… |
| data-agent `discover` subcommand | **partially** | medium | The standalone wheel half is fully documented (install instructions, console-script `model-data-agent run`, Python API, decoupling rationale, SBOM entry). The `discover` subcommand half is only acknowledged by name in two one-line references and is not… |
| Checkpoint / resume / metrics / logging | **partially** | high | Three sub-features, three different states. (1) CHECKPOINT PERSISTENCE — fully and accurately documented (on-disk layout, .result.json suffix, MPC_CHECKPOINT_DIR, the files-present diagnosis table). (2) STRUCTURED LOGGING — fully documented;… |

**Most important gap:** the **E4 `--provider` flag + `make_llm_client` factory** is a shipped, user-facing CLI feature with *zero* wiki coverage — `--provider`, `make_llm_client`, and `LLMProvider` return zero hits across all 22 pages. It belongs in Getting-Started, Pipeline-Overview, Data-Guide, Security-Considerations (it's the network boundary deciding which endpoint receives interview answers/SQL), and as a 5th extension surface in Extending-the-Pipeline.

---

## 6. Per-Page Damage Map

Pages ranked worst → fine. (Pages not listed had no confirmed technical discrepancies.)

| Page | Verdict | Confirmed | Headline issue |
|---|---|---:|---|
| `Agent-Reference` | **badly stale** | 11 | Intake input type, `EstimatedValue`, `IntakeReport`, `DataRequest`, `QualityCheck`, `DataReport`, `RepoTarget`, and all agent Interfaces blocks are wrong; copy-paste snippets fail at runtime |
| `Monitoring-and-Operations` | **badly stale** | 8 | Resume documented backwards (data loss), latency unit seconds→ms, fabricated `MPC_HOST_TOKEN` symptom, misdescribed metrics/logging |
| `Security-Considerations` | **stale + omission** | 7 | E4 provider seam (a network boundary) undocumented; many `file:line` cites drifted after O3; `MPC_NAMESPACE` missing |
| `Worked-Examples` | **citation drift** | 6 | Behavioral prose accurate, but ~6 `governance_templates.py` line ranges drifted ~33 lines |
| `Schema-Reference` | **incomplete + drifted** | 5 | Omits `IntakeReport.qa_pairs`/`QAPair` and the `DataRequest.baseline_metric_*` fields; inline-Literal structure drifted (O4) |
| `Intake-Interview-Design` | **stale** | 5 | "Verbatim" interviewer prompt quote is ~⅓ of the real prompt at wrong lines; E4 seam absent |
| `Extending-the-Pipeline` | **badly stale** | 5 | "There is no adapter factory" (O3 added one); missing 5th (LLM provider) surface and the `STAGE_ORDER` step; wrong test filename |
| `Contributing` | **stale** | 5 | Test count off ~5.4× (131 vs 705); wrong test filename; local lint/typecheck commands drift from CI |
| `Evolution` | **stale** | 4 | Governance enum vocab wrong; `data-agent`→`model-data-agent` entrypoint; §8 figures far out of date |
| `Glossary` | **incomplete** | 4 | `IntakeReport` gloss omits `value_measurement_plan` (contradicts its own next entry); Run ID wrongly called a UUID |
| `Getting-Started` | **partially stale** | 3 | Stale test count (440+ vs 795); "with API keys" live-run never exercises Anthropic (needs `--llm`) |
| `Architecture-Decisions` | **stale rationale** | 3 | AD-2 (declined provider abstraction) and AD-5 ("only a new adapter") superseded by E4 + O3 |
| `Development-Workflow` | **stale** | 2 | Attributes the constructor's ruff rules to the scaffold (ships none); overstates JSON-parse gate as "schema validation" |
| `Generated-Project-Structure` | **incomplete** | 2 | `06_implementation_plan` omits the Production Measurement Plan; `data_loading.py` row incomplete |
| `Software-Bill-of-Materials` | **minor stale** | 2 | Coverage floor 94% vs 95%; `docs` optional-dependency extra (mkdocs) undocumented |
| `Home` | **minor stale** | 1 | Says generated content is "notebook files"; generator emits Quarto `.qmd`, not `.ipynb` |
| `Pipeline-Overview` | **stale** | 1 | Frames resume as "(in future)" though it ships; repeats nonexistent `InterviewSessionConfig` |
| `Changelog` | **stale** | 1 | `[Unreleased]` empty; E4/O1/O3/O4 (Sessions 114–133) unlogged, incl. the user-facing `--provider` flag |

---

## 7. Prioritized Remediation Plan

Ordered by harm-reduction. Each is a candidate unit of work for a future wiki-refresh session (likely 2–3 sessions total given the volume; **do not bundle** — see SESSION_RUNNER FM #18).

1. **Fix the actively-misleading contradictions that cause data loss / broken procedures first:** rewrite `Extending-the-Pipeline.md:142-144` to describe the `REPO_PLATFORMS` adapter factory (it currently says "There is no adapter factory"), and rewrite `Monitoring-and-Operations.md:46-48` to document the `--resume` flag (same-`run_id` reuse OVERWRITES checkpoints; it does not auto-resume).
2. **Fix the runtime-breaking `Agent-Reference.md` schema/interface blocks** so copy-pasted snippets work: the nonexistent `InterviewSessionConfig` + `IntakeAgent().run(config)` (L13-18,63), `EstimatedValue.low/high_estimate` (L34-38), `DataRequest.target_variable/...` (L82-89), `QualityCheck.name/sql/expected_result` (L98-105), the `RepoTarget.host` block (L146-152); add a Website Agent Interfaces table.
3. **Fix the operator-facing factual errors in `Monitoring-and-Operations.md`:** `agent_latency` unit seconds→milliseconds (L68), the fabricated `MPC_HOST_TOKEN` symptom→the real `ConfigError` string (L138), and the misdescribed metrics/structured-logging surfaces (L55-69).
4. **Document the E4 provider seam everywhere it belongs:** add `--provider`/`make_llm_client` coverage to Getting-Started, Pipeline-Overview, Data-Guide, and Security-Considerations; add a 5th "add a new LLM provider" extension surface to `Extending-the-Pipeline.md:3`; update `Intake-Interview-Design.md:265,273` and AD-2 so the provider-swap recipe includes the `LLMProvider` Literal + factory branch.
5. **Document the O3 `REPO_PLATFORMS` registry** (registry/`PlatformSpec`/`adapter_factory`/`HostLiteral` + `assert_vocab_parity` steps) in Extending-the-Pipeline §3 and update AD-5; **document the O1 `STAGE_ORDER` single-source step** (and fix the `FAILED_AT_<STAGE>` hand-threading instructions that now break the build via import-time drift guards); add an **O4 note** that Literal-backed prompt enums are edited at the schema, not the prompt prose.
6. **Complete the `Schema-Reference` field-by-field reference:** add `IntakeReport.qa_pairs` + `QAPair` and the three `DataRequest.baseline_metric_*` fields; correct the inline-Literal → named-alias structure for `Confidence`/`CounterfactualDesign`/`ReviewCadence`.
7. **Fix the developer-workflow drift:** update Contributing + Monitoring-and-Operations so local lint includes `scripts/` and typecheck is bare `mypy`; correct the test filename (`test_registry.py` → `test_envelope_and_registry.py` at `Contributing.md:170` and `Extending-the-Pipeline.md:250`); replace hardcoded test counts (131 / 440+ → ~795, ideally a reproducing command).
8. **Correct the remaining stale facts:** `Evolution.md` governance enum vocab (`cycle_time`/`risk_tier`) and the `data-agent` → `model-data-agent` entrypoint; `Development-Workflow.md` ruff-rules attribution and "schema validation" wording; `Software-Bill-of-Materials.md` 94%→95% and the missing `docs` extra; Glossary `IntakeReport`/Run ID/Checkpoint entries; `Generated-Project-Structure.md` `06_implementation_plan` cell.
9. **Backfill `Changelog.md` `[Unreleased]`** with the Sessions 114–133 changes (E4 `--provider` factory, O1 `STAGE_ORDER`, O3 `REPO_PLATFORMS`, O4 Literal enums), led by the user-facing `--provider` flag.
10. **Sweep the drifted line citations** in `Worked-Examples.md`, `Security-Considerations.md`, `Intake-Interview-Design.md`, and `Schema-Reference.md`.

---

## 8. Recurrence Prevention

The single largest source of low-severity findings is **hardcoded `file:line` citations that drift as code grows**. A page that says "verbatim from `anthropic_client.py:35-51`" is wrong the moment that file gains a line above 35. Two options, in increasing robustness:

- **Symbol references** instead of line numbers — cite `SYSTEM_INTERVIEWER` / `REPO_PLATFORMS` / `EstimatedValue`, which `grep` can locate regardless of line drift.
- **Publish-time line-number generation** — a snippet-include mechanism that pulls live line ranges at wiki-publish time (the publish hook already exists; it could be extended).

Either would convert "drifted citation" from a recurring manual-sweep chore into a structural non-issue, and would let the auto-publish hook keep citations honest.

---

## Appendix A — All 79 Confirmed Findings

Grouped by page, severity-ordered. Each was adversarially verified (citable on both sides). "Fix pointer" is a concise direction; full replacement text for the 16 high-severity items is in §4.


### Agent-Reference (11)

| Sev | Type | Wiki ref | Code ref | Issue → reality | Fix pointer |
|-----|------|----------|----------|-----------------|-------------|
| high | stale | `Agent-Reference.md:13-18` | `src/model_project_constructor/agents/intake/agent.py:48-72` | Intake input is `InterviewSessionConfig` with fields user_id, session_id, problem_statement. → No InterviewSessionConfig type exists. The intake graph is seeded via initial_state(stakeholder_id, session_id, domain, initial_problem); the ... | Replace the Agent-Reference.md:11-18 "Input schema" block so it reflects the actual seed/facade surface (there is no config object). Suggested replacement: |
| high | stale | `Agent-Reference.md:34-38` | `src/model_project_constructor/schemas/v1/intake.py:46-59` | IntakeReport.estimated_value has fields low_estimate, high_estimate, confidence, assumptions. → EstimatedValue has narrative, annual_impact_usd_low, annual_impact_usd_high, confidence (Literal['low','medium','high']), assumptions, plus o... | Update Agent-Reference.md:34-38 to match the EstimatedValue schema. Replace the four-field block with: `estimated_value: EstimatedValue` -> `narrative: str`, `annual_impact_usd_low: float | None`, ... |
| high | stale | `Agent-Reference.md:63` | `src/model_project_constructor/agents/intake/agent.py:44-46` | Python interface for the intake agent is `IntakeAgent().run(config)`. → IntakeAgent.__init__ requires an `llm` argument (IntakeAgent(llm=...)); there is no zero-arg constructor and no `run(config)` method. The public methods are run_with... | Update Agent-Reference.md:63 to reflect the real API. Replace the Python interface cell with the actual constructor + method, e.g.: `IntakeAgent(llm=...).run_with_fixture("interview.yaml")` (fixtur... |
| high | stale | `Agent-Reference.md:82-89` | `packages/data-agent/src/model_project_constructor_data_agent/schemas.py:46-69` | DataRequest fields are target_variable, target_definition, granularity, features, population, time_range. → DataRequest fields are target_description, target_granularity (a DataGranularity object with unit + time_grain enum), required_fe... | Replace the Agent-Reference.md:82-89 input-schema block with the current shape. For example: DataRequest schema_version: "1.0.0" target_description: str target_granularity: DataGranularity { unit: ... |
| high | stale | `Agent-Reference.md:98-105` | `packages/data-agent/src/model_project_constructor_data_agent/schemas.py:71-111` | DataReport.primary_queries items (PrimaryQuery) have name, sql, quality_checks, datasheet; QualityCheck has name, sql, expected_result. → PrimaryQuery has name, sql, purpose, expected_row_count_order (Literal tens/hundreds/thousands/mill... | Update the code-fenced schema at Agent-Reference.md:98-105 to match schemas.py. For PrimaryQuery list under primary_queries: name: str; sql: str; purpose: str; expected_row_count_order: "tens"|"hun... |
| high | stale | `Agent-Reference.md:146-152` | `src/model_project_constructor/schemas/v1/repo.py:12-17` | Website RepoTarget has host ('gitlab'\|'github'), namespace, project_name, visibility, host_url (str\|None override for self-hosted). → RepoTarget has schema_version, host_url (a required str, not optional), namespace, project_name_hint ... | Rewrite the RepoTarget block at Agent-Reference.md:146-151 to match repo.py exactly: RepoTarget schema_version: "1.0.0" host_url: str (required; API base URL — defaults are resolved by the CLI from... |
| medium | incomplete | `Agent-Reference.md:23-47` | `src/model_project_constructor/schemas/v1/intake.py:97-117` | IntakeReport's listed fields are status, business_problem, proposed_solution, model_solution, estimated_value, governance, questions_asked, revision_cycles. → IntakeReport also has schema_version='1.0.0', missing_fields, value_measuremen... | Update the IntakeReport Output schema block at Agent-Reference.md:22-47 to match intake.py:97-117. Add the missing top-level fields: schema_version: "1.0.0", missing_fields: list[str], value_measur... |
| medium | incomplete | `Agent-Reference.md:96-108` | `packages/data-agent/src/model_project_constructor_data_agent/schemas.py:129-139` | DataReport top-level fields are status, primary_queries, confirmed_expectations, unconfirmed_expectations, data_quality_concerns. → DataReport also has schema_version, request (the echoed DataRequest), summary (the natural-language summa... | Update the DataReport schema block at Agent-Reference.md:96-108 to add the five missing top-level fields so it matches schemas.py:129-139. Specifically add: schema_version: "1.0.0"; request: DataRe... |
| medium | incomplete | `Agent-Reference.md:123-124` | `packages/data-agent/src/model_project_constructor_data_agent/cli.py:74-216` | Data Agent CLI is `model-data-agent run --request request.json --output report.json`; Python is `DataAgent().run(data_request)`. → The CLI has TWO subcommands, `run` and `discover` (the latter probes information_schema into a DataSourceI... | Update the Data Agent "Interfaces" table on Agent-Reference.md:123-124 and add coverage of the new surface: (1) Document both CLI subcommands — keep `model-data-agent run --request request.json --o... |
| medium | incomplete | `Agent-Reference.md:176-185` | `src/model_project_constructor/agents/website/cli.py:48-115` | Website Agent interfaces: only Web UI/CLI rows are not shown; CLI implied via `RepoClient.create_project()` / Python `WebsiteAgent`. → The website CLI is invoked via `python -m model_project_constructor.agents.website run --intake ... --... | Add an `### Interfaces` table to the Website Agent section (after "Behavior", around line 178) matching the Intake/Data agents' format, e.g.: | Interface | Command | |-----------|---------| | CLI (... |
| low | incomplete | `Agent-Reference.md:157-168` | `src/model_project_constructor/schemas/v1/repo.py:28-36` | RepoProjectResult fields: status, project_url, project_id, initial_commit_sha, files_created, governance_manifest. → RepoProjectResult also has schema_version and failure_reason (str\|None). failure_reason is materially load-bearing — it... | In the RepoProjectResult output-schema block (Agent-Reference.md:157-168), add a line for the load-bearing field, e.g. directly after governance_manifest/before or after files_created: `failure_rea... |

### Architecture-Decisions (3)

| Sev | Type | Wiki ref | Code ref | Issue → reality | Fix pointer |
|-----|------|----------|----------|-----------------|-------------|
| medium | incomplete | `Architecture-Decisions.md:29-33` | `src/model_project_constructor/orchestrator/config.py:94-114` | AD-5 documents the RepoClient host abstraction: a protocol with adapter implementations (PythonGitLabAdapter, PyGithubAdapter, FakeRepoClient); adding a new host requires only a new adapter, no changes to the agent. → The protocol + thre... | Update AD-5 (Architecture-Decisions.md:33) so the "adding a new host" sentence reflects the O3 registry. Replace "Adding a new host (e.g., Bitbucket) requires only a new adapter -- no changes to th... |
| medium | stale | `Architecture-Decisions.md:11-15` | `src/model_project_constructor/agents/intake/factory.py:30-64` | AD-2 documents the LLM-framework decision: LangGraph for orchestration with the Anthropic SDK used directly because 'the project only uses Claude -- the abstraction would add complexity without benefit.' → Both agents now construct their... | Reclassify from missing-from-wiki to stale: the topic is NOT missing — AD-2 already documents the LLM/SDK abstraction decision, and the provider seam is the direct evolution of that same decision, ... |
| low | stale | `Architecture-Decisions.md:63` | `src/model_project_constructor/agents/website/nodes.py:208` | All generated files are committed in a single commit_files() call with the commit message `feat: scaffold model project`. → The single atomic commit is real, but the literal message passed to commit_files() is `feat: scaffold model proje... | On Architecture-Decisions.md:63, change the backtick-quoted message to match nodes.py:208 verbatim: replace `feat: scaffold model project` with `feat: scaffold model project (intake + data + govern... |

### Changelog (1)

| Sev | Type | Wiki ref | Code ref | Issue → reality | Fix pointer |
|-----|------|----------|----------|-----------------|-------------|
| medium | missing-from-wiki | `Changelog.md:11` | `src/model_project_constructor/agents/intake/factory.py:35` | ## [Unreleased] section is empty (no entries) — the most recent recorded change is the v0.2.0 release dated 2026-06-04 (Session 111). → Four notable architectural features have landed on master since the wiki was last edited (commit 2b54... | Backfill the empty `## [Unreleased]` block at Changelog.md:11 with the audience-relevant changes that landed since v0.2.0 (Sessions 114-133), led by the user-facing one: "Added: `--provider` CLI fl... |

### Contributing (5)

| Sev | Type | Wiki ref | Code ref | Issue → reality | Fix pointer |
|-----|------|----------|----------|-----------------|-------------|
| high | stale | `Contributing.md:98` | `tests/ (705 functions total; e.g. tests/test_llm_json_parity.py, tests/test_vocab_guard.py, tests/orchestrator/test_stage_order.py, tests/agents/intake/test_factory.py)` | Current snapshot: 131 test functions across tests/ subdirectories (agents/intake/, agents/data/, agents/website/, orchestrator/, schemas/, ui/intake/, data_agent_package/, fixtures/, scripts/, plus the top-level test_data_agent_decouplin... | Update Contributing.md:98 to: "Current snapshot: **705 test functions** across `tests/` subdirectories (`orchestrator/` 201, `agents/website/` 137, `data_agent_package/` 135, `agents/intake/` 83, `... |
| medium | stale | `Contributing.md:170` | `tests/schemas/test_envelope_and_registry.py:1` | tests/schemas/test_registry.py — every REGISTRY entry round-trips through HandoffEnvelope -> load_payload. → There is no tests/schemas/test_registry.py. The REGISTRY round-trip / load_payload invariant tests live in tests/schemas/test_en... | In docs/wiki/claims-model-starter/Contributing.md line 170, change `tests/schemas/test_registry.py` to `tests/schemas/test_envelope_and_registry.py`. The same wrong filename also appears at docs/wi... |
| medium | stale | `Contributing.md:61` | `.github/workflows/ci.yml:23` | Run locally: uv run ruff check src/ tests/ packages/ (the local lint command, repeated in §3 pre-push hint and §7 PR-workflow gate list). → CI lints a fourth path, scripts/: '.github/workflows/ci.yml:23' runs `uv run ruff check src/ test... | Append ` scripts/` to all three local ruff invocations so they match ci.yml:23. (1) Contributing.md:61 -> `uv run ruff check src/ tests/ packages/ scripts/` (and, for consistency, line 62's `ruff f... |
| low | stale | `Contributing.md:98` | `tests/test_llm_json_parity.py:1, tests/test_vocab_guard.py:1` | Snapshot lists only 'the top-level test_data_agent_decoupling.py' among top-level test files. → Two additional top-level test files now exist that the snapshot omits: tests/test_llm_json_parity.py (5 functions) and tests/test_vocab_guard... | Update Contributing.md:98 so the enumeration of top-level test files is complete and the count is current. Replace "...plus the top-level `test_data_agent_decoupling.py`)." with a list of all three... |
| low | stale | `Contributing.md:77` | `.github/workflows/ci.yml:34, pyproject.toml:97` | Type check run locally: uv run mypy src/ (and the §7 gate block / §3 pre-push hint repeat `uv run mypy src/`). → CI runs `uv run mypy` with no path argument ('.github/workflows/ci.yml:34'); the checked packages are fixed by [tool.mypy] p... | Replace `uv run mypy src/` with bare `uv run mypy` at all three sites — Contributing.md:77 (§2.2 Run locally block), Contributing.md:116 (§3 pre-push hint), and Contributing.md:208 (§7 PR gate bloc... |

### Data-Guide (4)

| Sev | Type | Wiki ref | Code ref | Issue → reality | Fix pointer |
|-----|------|----------|----------|-----------------|-------------|
| high | stale | `Data-Guide.md:110-111` | `packages/data-agent/src/model_project_constructor_data_agent/agent.py:36` | Python API usage shown as `DataAgent().run(data_request)` (constructor called with no arguments). → DataAgent.__init__ requires `llm: LLMClient` as a mandatory positional argument (db is optional). `DataAgent()` with no args raises TypeE... | Update Data-Guide.md:110-111 to pass a constructed LLM client. Replace the two lines with: from model_project_constructor_data_agent import DataAgent, make_llm_client report = DataAgent(llm=make_ll... |
| medium | incomplete | `Data-Guide.md:106-107` | `packages/data-agent/src/model_project_constructor_data_agent/cli.py:74-117` | Standalone CLI invocation: `model-data-agent run --request request.json --output report.json` (only --request and --output documented for the run command). → The `run` command also accepts `--db-url` (execute quality checks against a liv... | Expand the standalone CLI example in Data-Guide.md (lines 105-114) to document all run-command flags, foregrounding `--db-url` because of its tie to the "Run quality checks before using primary que... |
| low | missing-from-wiki | `Data-Guide.md:101-114` | `packages/data-agent/src/model_project_constructor_data_agent/factory.py:31-64` | The page never mentions the `--provider` CLI flag or the make_llm_client factory seam. → E4 added a `--provider` option (default 'anthropic') to both `run` and `discover`, routed through factory.make_llm_client; the known-provider list i... | In Data-Guide.md, extend the "The Data Agent as a standalone tool" section (after line 114) with a short subsection on backend selection. State that both `run` and `discover` accept a `--provider` ... |
| low | incomplete | `Data-Guide.md:120-124` | `packages/data-agent/src/model_project_constructor_data_agent/schemas.py:154` | Three producer classes can populate an inventory today: Curated, Automated, Interview. → ProducerMetadata.producer_type is Literal["curated", "automated", "interview", "external_catalog"] — a fourth value, external_catalog, exists in the... | Reconcile the two pages without overclaiming. Preferred: keep Data-Guide.md:120 honest about implementations but acknowledge the fourth enum value. Change line 120 to e.g. "The `producer_type` enum... |

### Development-Workflow (2)

| Sev | Type | Wiki ref | Code ref | Issue → reality | Fix pointer |
|-----|------|----------|----------|-----------------|-------------|
| medium | stale | `Development-Workflow.md:97` | `src/model_project_constructor/agents/website/templates.py:161` | Code quality standards: 'ruff -- Linting and formatting. Rules: E (pycodestyle errors), F (pyflakes), I (isort), UP (pyupgrade), B (bugbear), SIM (simplification).' Presented as part of 'The generated project includes:'. → The generated ... | Edit Development-Workflow.md:97 to stop attributing the constructor's own rule set to the scaffold. Either (a) drop the explicit enumeration: "**ruff** -- Linting and formatting (ruff check + ruff-... |
| low | stale | `Development-Workflow.md:91` | `src/model_project_constructor/agents/website/governance_templates.py:640` | 'CI pipeline that runs lint, tests, and governance schema validation'; 'The CI pipeline runs `ruff check`, `pytest`, and governance schema validation on every push'; pre-commit does 'model registry schema validation'. → The CI 'governanc... | Replace "schema validation" with a parse/well-formedness description in all three spots (the job/hook name `model-registry-schema` can stay, since it is the artifact's identifier): - Line 14: "CI p... |

### Evolution (4)

| Sev | Type | Wiki ref | Code ref | Issue → reality | Fix pointer |
|-----|------|----------|----------|-----------------|-------------|
| medium | stale | `Evolution.md:37` | `src/model_project_constructor/schemas/v1/common.py:23` | Governance artifacts are emitted proportional to `cycle_time` ∈ {rapid, standard, extended}, with Tier 3 + extended producing the full set and Tier 1 + rapid the minimal scaffolding. → The CycleTime schema Literal has never been {rapid, ... | On Evolution.md:37, replace the enumerated vocab to match the schema. Change "`risk_tier` ∈ {low, medium, high} and `cycle_time` ∈ {rapid, standard, extended}" to "`risk_tier` ∈ {tier_1_critical, t... |
| medium | stale | `Evolution.md:37` | `src/model_project_constructor/schemas/v1/common.py:25` | The pipeline emits governance artifacts proportional to `risk_tier` ∈ {low, medium, high}; "a low-stakes internal tool does not need SR 11-7 paperwork, but a million-dollar-impact classifier does" (§1), and §2/§5 describe `risk_tier` ∈ {... | Edit Evolution.md:37 to replace the false enum with the real schema vocabulary. Change "proportional to `risk_tier` ∈ {low, medium, high} and `cycle_time` ∈ {rapid, standard, extended}" to "proport... |
| low | stale | `Evolution.md:197` | `CHANGELOG.md:25` | §8 Current state: "Today (2026-04-18, commit f09ea57, 46 sessions in) ... 446 tests pass at 97.27% coverage; CI is green across lint, typecheck, test, and decoupling jobs." and the codebase-structure bullets describe the system as it sta... | Do NOT auto-rewrite §8 — the page's own convention (Evolution.md:3 banner + :183) makes this a user-triggered full-rewrite document, so a piecemeal number bump would violate its stated discipline a... |
| low | stale | `Evolution.md:87` | `packages/data-agent/pyproject.toml:21` | §4: "The package added `AnthropicLLMClient`, a Typer CLI (`data-agent` as an entrypoint), and Python API docs." → The data-agent console-script entrypoint is `model-data-agent` (packages/data-agent/pyproject.toml:21: `model-data-agent = ... | Change `data-agent` to `model-data-agent` on Evolution.md:87, i.e. "a Typer CLI (`model-data-agent` as an entrypoint)". This matches packages/data-agent/pyproject.toml:21 and the package's USAGE.md... |

### Extending-the-Pipeline (5)

| Sev | Type | Wiki ref | Code ref | Issue → reality | Fix pointer |
|-----|------|----------|----------|-----------------|-------------|
| high | stale | `Extending-the-Pipeline.md:142-144` | `src/model_project_constructor/orchestrator/config.py:56,59-69,72-84,94-105; scripts/run_pipeline.py:295-297; src/model_project_constructor/agents/website/cli.py:177` | "There is no adapter factory. The Website Agent receives the RepoClient instance directly from its caller... The scripts/run_pipeline.py entry point selects the adapter via the --host flag. A new host value requires updating that selecti... | Rewrite Extending-the-Pipeline.md:142-144 ("Wiring and selection") to describe the registry-driven factory instead of a hand-written --host branch. Suggested replacement: "### Wiring and selection ... |
| high | missing-from-wiki | `Extending-the-Pipeline.md:3` | `src/model_project_constructor/agents/intake/factory.py:30-64; packages/data-agent/src/model_project_constructor_data_agent/factory.py:31-64; scripts/run_pipeline.py:447-455; packages/data-agent/src/model_project_constructor_data_agent/cli.py:106-110` | "The pipeline has four designed extension surfaces: adding a new agent, adding a new repository-host adapter, adding a new governance artifact, and adding a new regulatory framework. Each surface has an explicit boundary — a Protocol, a ... | Two coordinated edits. (1) On Extending-the-Pipeline.md:3, change "four designed extension surfaces" to "five", and add "adding a new LLM provider" to the enumeration; keep the boundary clause but ... |
| medium | stale | `Extending-the-Pipeline.md:130-144` | `src/model_project_constructor/orchestrator/config.py:94-114,179-194; src/model_project_constructor/agents/website/cli.py:44; scripts/run_pipeline.py:406` | §3 'Files to add or edit' for a new repo-host adapter lists: new <host>_adapter.py module, re-export in website/__init__.py, optional dependency in pyproject, tests, and CI template — and (in 'Wiring and selection') updating the run_pipe... | Update §3 of Extending-the-Pipeline.md. In "Files to add or edit", add steps for the single-source registry: (a) add a `PlatformSpec(default_api_url=..., token_env_var=..., adapter_factory=_make_<h... |
| low | stale | `Extending-the-Pipeline.md:66,74` | `src/model_project_constructor/orchestrator/pipeline.py:51-53,60-65,106-145` | Runner type aliases are 'declared at src/model_project_constructor/orchestrator/pipeline.py:48-50' and PipelineStatus 'at pipeline.py:52-57'. → After the O1 run_pipeline decomposition, IntakeRunner/DataRunner/WebsiteRunner are at pipelin... | On Extending-the-Pipeline.md line 66: change "pipeline.py:48-50" to "pipeline.py:51-53". On line 74: change "PipelineStatus at pipeline.py:52-57" to "PipelineStatus at pipeline.py:60-65". Additiona... |
| low | stale | `Extending-the-Pipeline.md:154,171,176,193,226,140,177` | `src/model_project_constructor/agents/website/governance_templates.py:72,110,147,803-838,938` | Governance function/registry line citations: build_governance_files at governance_templates.py:770-853, _tier_at_least at :47-54, _FRAMEWORK_ARTIFACTS at :77-111, build_regulatory_mapping at :114-129, ci_platform dispatch at :801-804, is... | Update the seven line anchors in Extending-the-Pipeline.md to the current locations and do NOT repeat the finding's incorrect "~600 lines added" rationale. Specifically: line 154 ":770-853" -> ":80... |

### Generated-Project-Structure (2)

| Sev | Type | Wiki ref | Code ref | Issue → reality | Fix pointer |
|-----|------|----------|----------|-----------------|-------------|
| medium | incomplete | `Generated-Project-Structure.md:124` | `templates.py:464-595` | The 06_implementation_plan narrative contains: "Annual impact estimate, confidence, assumptions". → render_qmd_implementation_plan emits the three top fields (impact band, confidence, assumptions) and then appends a full Production Measu... | Update the 06_implementation_plan cell at Generated-Project-Structure.md:124 to mention the appended Production Measurement Plan, mirroring how the 01 cell (line 119) enumerates its sub-sections. S... |
| low | incomplete | `Generated-Project-Structure.md:107` | `templates.py:194-226` | src module table: data_loading.py -- Key function `load_primary()`. → render_data_loading emits not only load_primary() but also a read_sql(query_name) helper and a module-level PRIMARY_QUERY_NAMES: list[str] constant seeded from the Dat... | Edit Generated-Project-Structure.md:107 to list read_sql() alongside load_primary() in the Key function column, matching the multi-function style already used for models.py. Suggested cell: `read_s... |

### Getting-Started (3)

| Sev | Type | Wiki ref | Code ref | Issue → reality | Fix pointer |
|-----|------|----------|----------|-----------------|-------------|
| medium | stale | `Getting-Started.md:34` | `pyproject.toml:65` | You should see 440+ tests pass with ~97% coverage. → The suite now has 795 passing tests (coverage 97.28%). `uv run pytest -q` -> '795 passed'; with coverage 'Total coverage: 97.28%'. The '~97% coverage' half is accurate; the '440+' test... | Update Getting-Started.md:34 to the current baseline, e.g. "You should see 795+ tests pass with ~97% coverage." Apply the same edit to README.md:128 ("All 795+ tests should pass with coverage above... |
| medium | incomplete | `Getting-Started.md:64` | `scripts/run_pipeline.py:273-300` | Live run (with API keys): `uv run python scripts/run_pipeline.py --live --host github` ... [implying ANTHROPIC_API_KEY is exercised]. → `--live` only swaps the WEBSITE stage to a real repo host (build_website_runner). Intake and Data sti... | Update Getting-Started.md to separate the two orthogonal dimensions (live repo host vs. real LLM calls) and introduce the --llm flag. Concretely: (1) Under the "## Live run (with API keys)" section... |
| low | stale | `Getting-Started.md:58` | `scripts/run_pipeline.py:628` | ls .orchestrator/checkpoints/ ... Each checkpoint file is a JSON envelope. → Checkpoint envelopes for a run are written under a per-run subdirectory `.orchestrator/checkpoints/<run_id>/`, not flat in `.orchestrator/checkpoints/`. `ls .or... | Change the inspect step so the listed directory matches the files described. Replace Getting-Started.md line 59 `ls .orchestrator/checkpoints/` with a command that descends into the run-id subdirec... |

### Glossary (4)

| Sev | Type | Wiki ref | Code ref | Issue → reality | Fix pointer |
|-----|------|----------|----------|-----------------|-------------|
| medium | incomplete | `Glossary.md:24` | `src/model_project_constructor/schemas/v1/intake.py:106` | IntakeReport = "Structured output of the Intake Agent: business problem, proposed solution, model solution, estimated value, governance metadata." → IntakeReport carries SIX top-level content sections, not five: business_problem, propose... | Edit Glossary.md:24 to add the value measurement plan as a content section, e.g.: "IntakeReport | Structured output of the Intake Agent: business problem, proposed solution, model solution, estimat... |
| low | stale | `Glossary.md:29` | `scripts/run_pipeline.py:401` | Run ID = "UUID assigned by the orchestrator to a single pipeline execution. All checkpoints for one run share the same run ID." → The default run_id is generated as an argparse default in the CLI script run_pipeline.py, not by 'the orche... | Rewrite Glossary.md:29 to: "Run ID — A free-form string identifier for a single pipeline execution. The CLI (`scripts/run_pipeline.py`) auto-generates a default of the form `run_<8 hex chars>` (e.g... |
| low | incomplete | `Glossary.md:28` | `src/model_project_constructor/orchestrator/pipeline.py:208` | Checkpoint = "A persisted JSON envelope ... Used for inspection and potential resumption." → Resumption is no longer merely 'potential' — it is implemented. The orchestrator reads checkpoints back to compute a resume point (determine_res... | Update Glossary.md:28 to reflect that resumption is implemented, e.g.: "| **Checkpoint** | A persisted JSON envelope representing a completed inter-agent handoff. Used for inspection and for resump... |
| low | incomplete | `Glossary.md:77` | `src/model_project_constructor/agents/intake/factory.py:30` | Technology terms section glosses RepoClient (a Protocol for repository operations) but defines no term for the LLM-client/provider seam. → Since the wiki baseline (Session 114), the E4 overhaul added a provider seam: an IntakeLLMClient p... | Add one (optionally two) rows to the "Technology terms" table in docs/wiki/claims-model-starter/Glossary.md, parallel to the existing RepoClient row at line 77, e.g.: | **IntakeLLMClient / LLMClien... |

### Home (1)

| Sev | Type | Wiki ref | Code ref | Issue → reality | Fix pointer |
|-----|------|----------|----------|-----------------|-------------|
| low | stale | `Home.md:34` | `src/model_project_constructor/agents/website/templates.py:788` | "AI-generated content is materialised as static markdown, SQL, and notebook files at construction time." → The generated repository emits .qmd (Quarto) analysis narratives, .sql query files, and .md reports/README files. There are no Jup... | Edit Home.md:34 to name the actual artifact format: replace "materialised as static markdown, SQL, and notebook files at construction time." with "materialised as static markdown, SQL, and Quarto (... |

### Intake-Interview-Design (5)

| Sev | Type | Wiki ref | Code ref | Issue → reality | Fix pointer |
|-----|------|----------|----------|-----------------|-------------|
| high | stale | `Intake-Interview-Design.md:16-18` | `src/model_project_constructor/agents/intake/anthropic_client.py:42-110` | Quotes the interviewer system prompt as 'verbatim from src/model_project_constructor/agents/intake/anthropic_client.py:35-51', ending at '...decision rights for retire/retrain.' → The interviewer system prompt is materially longer than t... | On Intake-Interview-Design.md:16, (1) drop the word "verbatim" — replace with "the opening of the interviewer system prompt (`SYSTEM_INTERVIEWER`)"; (2) fix the citation: the assembled prompt is `S... |
| medium | missing-from-wiki | `Intake-Interview-Design.md:252-266` | `src/model_project_constructor/agents/intake/factory.py:30-64` | The factory / provider seam is never mentioned. 'Programmatic use' instantiates `IntakeAgent(AnthropicLLMClient())` and 'Extending' lists swapping the client by implementing the protocol; 'Key files' has no factory row. → A new `factory.... | Three edits to Intake-Interview-Design.md: (1) In "Programmatic use" (lines 252-263), change the construction to route through the factory: `from model_project_constructor.agents.intake import Inta... |
| low | stale | `Intake-Interview-Design.md:243` | `src/model_project_constructor/ui/intake/app.py:51-62` | The FastAPI web UI 'reuses the same compiled graph but supplies a live `AnthropicLLMClient` and a `SqliteSaver` checkpointer'. → The web UI no longer hard-wires `AnthropicLLMClient`. `_default_llm_factory` calls `make_llm_client('anthrop... | Update Intake-Interview-Design.md:243 to route the description through the E4 provider seam, e.g.: "reuses the same compiled graph but builds its LLM client via the provider factory `make_llm_clien... |
| low | stale | `Intake-Interview-Design.md:26-28` | `src/model_project_constructor/agents/intake/anthropic_client.py:128-135` | Governance system prompt quoted as verbatim from `anthropic_client.py:121-128`, hand-listing the cycle_time and risk_tier enum members in prose. → `SYSTEM_GOVERNANCE` is now at lines 128-135, and the enum members are DERIVED at runtime v... | Update Intake-Interview-Design.md:26 line cite from `anthropic_client.py:121-128` to `anthropic_client.py:128-135`. Soften the parenthetical so it does not imply the enum values are hand-listed: e.... |
| low | stale | `Intake-Interview-Design.md:103` | `src/model_project_constructor/agents/intake/anthropic_client.py:147-234` | draft_report 'asks the LLM to emit a full draft (nodes.py draft node + anthropic_client.py:173-217)'. → The draft JSON-shape instructions are now the module constant `_DRAFT_REPORT_INSTRUCTIONS` at lines 147-177 (pulled out of the method... | Repoint the line cite to the two actual locations after the O4 refactor. Change Intake-Interview-Design.md:103 from "(`nodes.py` draft node + `anthropic_client.py:173-217`)" to "(`nodes.py` draft n... |

### Monitoring-and-Operations (8)

| Sev | Type | Wiki ref | Code ref | Issue → reality | Fix pointer |
|-----|------|----------|----------|-----------------|-------------|
| high | stale | `Monitoring-and-Operations.md:69` | `src/model_project_constructor/orchestrator/metrics.py:39 (and :87, :137)` | Metrics capture `agent_latency` (seconds) per agent. → Latency is recorded and stored in MILLISECONDS, not seconds. `record_agent_latency(self, agent, duration_ms)` and `LatencySamples` is documented as 'Running aggregates for one agent'... | Edit Monitoring-and-Operations.md:68 to change "`agent_latency` (seconds) per agent" to "`agent_latency` (milliseconds) per agent — count / mean_ms / max_ms aggregates", matching LatencySamples and... |
| high | stale | `Monitoring-and-Operations.md:48` | `src/model_project_constructor/orchestrator/pipeline.py:318,176; scripts/run_pipeline.py:49,466` | Re-run with the same `run_id` to load existing checkpoints and resume from the next agent. A fresh `run_id` starts from scratch. → Resumption is NOT automatic on run_id reuse. `run_pipeline` resumes only when `config.resume_from` is set,... | Replace the "### Re-running" body (Monitoring-and-Operations.md:46-48) with the actual mechanism, e.g.: "Resuming is NOT automatic on run_id reuse. Re-running with the same `run_id` and no `--resum... |
| high | stale | `Monitoring-and-Operations.md:138` | `src/model_project_constructor/orchestrator/config.py:231-234,94-105` | Troubleshooting symptom `MPC_HOST_TOKEN not set` -> Missing env var -> Set GITLAB_TOKEN or GITHUB_TOKEN. → There is no `MPC_HOST_TOKEN` env var and no error string of that form. The token is read from the per-host env var in REPO_PLATFOR... | Replace the fabricated symptom in Monitoring-and-Operations.md:138 with the real ConfigError text emitted by require_host_token (config.py:233). Change the row to: | `ConfigError: GITLAB_TOKEN is r... |
| medium | stale | `Monitoring-and-Operations.md:66-69` | `src/model_project_constructor/orchestrator/metrics.py:80-91,56-62` | `MetricsRegistry` + `make_measured_runner()` capture: `run_count` per agent; `agent_latency` (seconds) per agent; Pipeline-level timing. → `run_count` is a single global pipeline-run counter incremented by `record_run(status)`, NOT a per... | Rewrite the bullet list at Monitoring-and-Operations.md:67-69 to match the code/OPERATIONS §3.2: "- `run_count` — total pipeline runs recorded (process-global, via `record_run(status)`); - `status_... |
| medium | stale | `Monitoring-and-Operations.md:55-59` | `src/model_project_constructor/orchestrator/logging.py:84-114` | Structured logging log entries include: Run ID and agent name; Start/end timestamps; Status; Error details. → The logged context does not include start/end timestamps. `make_logged_runner` emits `agent.start`/`agent.end`/`agent.error` wi... | Update Monitoring-and-Operations.md:56-59 to match OPERATIONS.md §3.1 and the code. Replace the bullet list with the actual structured-context fields, e.g.: - agent + run_id + correlation_id (bound... |
| medium | incomplete | `Monitoring-and-Operations.md:7-16` | `src/model_project_constructor/orchestrator/config.py:209-210,254-272` | Environment-variable table (rows: MPC_HOST, MPC_HOST_URL, GITLAB_TOKEN, GITHUB_TOKEN, ANTHROPIC_API_KEY, MPC_CHECKPOINT_DIR, MPC_LOG_LEVEL, INTAKE_DB_PATH). → `OrchestratorSettings.from_env` also reads `MPC_NAMESPACE` (target group/org p... | Add an MPC_NAMESPACE row to the env-var table in Monitoring-and-Operations.md (after the INTAKE_DB_PATH row at line 16, or grouped with the host-target vars near MPC_HOST). Suggested row, mirroring... |
| low | stale | `Monitoring-and-Operations.md:91` | `.github/workflows/ci.yml (test job: uv run pytest -q)` | Tests job: `pytest -q` (440+ tests, >95% coverage). → `uv run pytest --co` collects 795 tests (the CI test job runs `uv run pytest -q`). '440+' is still technically a true floor but understates the suite by ~80%. | On Monitoring-and-Operations.md:91, update the count from "440+ tests" to the current "~795 tests" (or "800+ tests"), keeping the rest of the cell intact: "| **Tests** | `pytest -q` (~795 tests, >9... |
| low | stale | `Monitoring-and-Operations.md:85-92` | `.github/workflows/ci.yml (lint: ruff check src/ tests/ packages/ scripts/; typecheck: uv run mypy)` | The project's own CI runs Lint (`ruff check src/ tests/ packages/`), Type check (`mypy src/`), Tests, Decoupling. → The lint job now runs `ruff check src/ tests/ packages/ scripts/` (adds `scripts/`), and the typecheck job runs bare `uv ... | Update the two CI-job table rows in Monitoring-and-Operations.md to match ci.yml. Line 89 Lint -> `ruff check src/ tests/ packages/ scripts/`. Line 90 Type check -> `mypy` (config-driven, strict mo... |

### Pipeline-Overview (1)

| Sev | Type | Wiki ref | Code ref | Issue → reality | Fix pointer |
|-----|------|----------|----------|-----------------|-------------|
| low | stale | `Pipeline-Overview.md:79` | `src/model_project_constructor/orchestrator/pipeline.py:208-285` | An orchestrator drives the chain and persists inter-agent handoffs as checkpoint envelopes; a failed run can be inspected and (in future) resumed. → Resume-from-checkpoint is implemented, not future. pipeline.py exposes determine_resume_... | Edit Pipeline-Overview.md:79 to remove the "(in future)" qualifier and document the shipped resume flow. Replace the sentence with, e.g.: "If any agent returns a non-`COMPLETE` status, the pipeline... |

### Schema-Reference (5)

| Sev | Type | Wiki ref | Code ref | Issue → reality | Fix pointer |
|-----|------|----------|----------|-----------------|-------------|
| high | incomplete | `Schema-Reference.md:195-214` | `src/model_project_constructor/schemas/v1/intake.py:88-94,116` | The IntakeReport schema block lists its complete field set: schema_version, status, missing_fields, business_problem, proposed_solution, model_solution, estimated_value, value_measurement_plan, governance, stakeholder_id, session_id, cre... | In docs/wiki/claims-model-starter/Schema-Reference.md: (1) Add `qa_pairs: list[QAPair] = Field(default_factory=list)` as the final field inside the IntakeReport code block (after line 213, before t... |
| high | incomplete | `Schema-Reference.md:244-257` | `packages/data-agent/src/model_project_constructor_data_agent/schemas.py:63-65` | The DataRequest schema block enumerates its fields as: schema_version, target_description, target_granularity, required_features, population_filter, time_range, database_hint, data_quality_concerns, data_source_inventory, source, source_... | In the DataRequest code block (Schema-Reference.md:244-257), insert the three fields between `data_source_inventory` (line 254) and `source` (line 255), preserving their grouping and the invariant ... |
| medium | stale | `Schema-Reference.md:51-52,135,161-165,171` | `src/model_project_constructor/schemas/v1/intake.py:24-34,50,67,73` | The schemas/v1/common module defines three Literal-string enums; the value-section vocabularies on EstimatedValue/ValueMeasurementPlan are inline Literals (e.g. confidence: Literal["low","medium","high"], counterfactual_design: Literal[.... | In Schema-Reference.md §4, update the EstimatedValue and ValueMeasurementPlan code blocks to reflect the named aliases. Two acceptable options: (a) Add a short subsection before EstimatedValue (aro... |
| low | stale | `Schema-Reference.md:33,53,64,82` | `src/model_project_constructor/schemas/v1/common.py:10-40` | CycleTime is at common.py line 25; RiskTier at lines 27-32; ModelType at lines 34-42; StrictBase at common.py:12-23. → Actual locations: StrictBase is lines 10-21, CycleTime line 23, RiskTier lines 25-30, ModelType lines 32-40. The cited... | Update the four line citations in Schema-Reference.md to match common.py: line 33 comment to "# src/model_project_constructor/schemas/v1/common.py:10-21"; line 53 heading to "### CycleTime (line 23... |
| low | stale | `Schema-Reference.md:17` | `src/model_project_constructor/schemas/v1/intake.py:97-117` | IntakeReport is at schemas/v1/intake.py:86-105. → IntakeReport now spans intake.py:97-117 (the file grew because the named Literal aliases at 24-34 and the QAPair class at 88-94 were added ahead of it). | In Schema-Reference.md:17, change the File cell of the IntakeReport row from `schemas/v1/intake.py:86-105` to `schemas/v1/intake.py:97-116` (matching the project's class-def-line through last-field... |

### Security-Considerations (7)

| Sev | Type | Wiki ref | Code ref | Issue → reality | Fix pointer |
|-----|------|----------|----------|-----------------|-------------|
| medium | missing-from-wiki | `Security-Considerations.md:80-99` | `src/model_project_constructor/agents/intake/factory.py:35-64` | Both agents construct anthropic.Anthropic() with no explicit args ... Both default to claude-sonnet-4-6 and expose a `model` argument for override. (LLM network boundary described as hardwired-Anthropic; no mention of a provider selectio... | In §2.1 (Anthropic / the LLM), keep the existing accurate statements but add a short paragraph after Security-Considerations.md:87 documenting the E4 provider seam, e.g.: "LLM client construction r... |
| low | stale | `Security-Considerations.md:20` | `src/model_project_constructor/orchestrator/config.py:166` | The orchestrator reads secrets exclusively via OrchestratorSettings.from_env() at src/model_project_constructor/orchestrator/config.py:78-129. → from_env is defined at config.py:166 (the @classmethod body runs ~166-220), not lines 78-129... | Update Security-Considerations.md:20 to cite the current location of `from_env`: change "`...config.py:78-129`" to "`src/model_project_constructor/orchestrator/config.py:165-220`" (the @classmethod... |
| low | stale | `Security-Considerations.md:53-58` | `src/model_project_constructor/orchestrator/config.py:222-235` | Reproduces require_host_token body as: var = "GITLAB_TOKEN" if self.host == "gitlab" else "GITHUB_TOKEN"; raise ConfigError(...). Cited as config.py:131-149. → require_host_token is now at config.py:222-235 and no longer uses the inline ... | Update Security-Considerations.md §1.3 to match current source. Change the cite comment on line 53 to `# src/model_project_constructor/orchestrator/config.py:222-240` and replace the reproduced req... |
| low | stale | `Security-Considerations.md:26-39` | `src/model_project_constructor/orchestrator/config.py:209-210` | The complete env-var matrix (table lists MPC_HOST, MPC_HOST_URL, GITLAB_TOKEN, GITHUB_TOKEN, ANTHROPIC_API_KEY, MPC_CHECKPOINT_DIR, MPC_LOG_LEVEL, INTAKE_DB_PATH). → config.from_env also reads and validates MPC_NAMESPACE (config.py:209-2... | Add a row for MPC_NAMESPACE to the matrix at Security-Considerations.md (between the MPC_HOST_URL row at line 33 and the GITLAB_TOKEN row at line 34, mirroring OPERATIONS.md:24-26 ordering), e.g.: ... |
| low | stale | `Security-Considerations.md:84-85` | `src/model_project_constructor/agents/intake/anthropic_client.py:274` | Intake Agent file:line for SDK construction + default model: src/.../agents/intake/anthropic_client.py:32, 134-146. Data Agent: packages/data-agent/.../anthropic_client.py:52, 99-111. → Intake: DEFAULT_MODEL is at anthropic_client.py:39 ... | Update the table line citations in Security-Considerations.md:84-85 to the current line numbers (no prose change needed; the claude-sonnet-4-6 default is still correct). Line 84 -> `src/model_proje... |
| low | stale | `Security-Considerations.md:154-160` | `packages/data-agent/src/model_project_constructor_data_agent/anthropic_client.py:459` | Prompts sent to Anthropic (packages/data-agent/.../anthropic_client.py:113-235) ... _dump_qc_status at packages/data-agent/.../anthropic_client.py:449-460 formats check_name: execution_status — result_summary. → The prompt-building metho... | Update Security-Considerations.md:154 to cite the current span — e.g. "(anthropic_client.py:123-364)" — and note the six LLM-calling methods (generate_primary_queries, generate_quality_checks, summ... |
| low | stale | `Security-Considerations.md:41-44` | `src/model_project_constructor/ui/intake/app.py:77` | Only two places outside config.py read env vars directly: ui/intake/app.py:75 (INTAKE_DB_PATH) and scripts/run_pipeline.py:114-119 (demo defaults). → INTAKE_DB_PATH is read at ui/intake/app.py:77 (not :75). run_pipeline.py reads os.envir... | Update Security-Considerations.md:43-44 to: "- src/model_project_constructor/ui/intake/app.py:77 — INTAKE_DB_PATH for the FastAPI web UI. - scripts/run_pipeline.py:119, 123, 126, 290 — demo script ... |

### Software-Bill-of-Materials (2)

| Sev | Type | Wiki ref | Code ref | Issue → reality | Fix pointer |
|-----|------|----------|----------|-----------------|-------------|
| medium | incomplete | `Software-Bill-of-Materials.md:26` | `pyproject.toml:41` | The Model Project Constructor's optional-dependency extras are: agents (--extra agents), ui (--extra ui), and dev (--extra dev). No other extras are listed. → pyproject.toml defines a fourth optional-dependencies group `docs` containing ... | Add a new subsection to Part 1 of Software-Bill-of-Materials.md, after the "Development tools (`--extra dev`)" table (i.e. after line 56), e.g.: ### Documentation tooling (`--extra docs`) | Package... |
| low | stale | `Software-Bill-of-Materials.md:54` | `pyproject.toml:65` | pytest-cov is used for 'Coverage reporting (94% minimum)'. → The coverage gate is configured at 95%, not 94%: addopts includes --cov-fail-under=95. | In Software-Bill-of-Materials.md:54, change the Purpose cell from `Coverage reporting (94% minimum)` to `Coverage reporting (95% minimum)` to match `--cov-fail-under=95` in pyproject.toml:65 and th... |

### Worked-Examples (6)

| Sev | Type | Wiki ref | Code ref | Issue → reality | Fix pointer |
|-----|------|----------|----------|-----------------|-------------|
| low | stale | `Worked-Examples.md:172` | `src/model_project_constructor/agents/website/governance_templates.py:803` | build_governance_files is at src/model_project_constructor/agents/website/governance_templates.py:770-853. → def build_governance_files begins at line 803 and its body runs 803-886; the cited range 770-853 no longer points at the functio... | In Worked-Examples.md:172 change the citation from `governance_templates.py:770-853` to `governance_templates.py:803-886` (def at 803, `return files` at 886). Also correct the companion drifted cit... |
| low | stale | `Worked-Examples.md:183` | `src/model_project_constructor/agents/website/governance_templates.py:846` | Tier-3+ artifacts (three_pillar_validation.md, ongoing_monitoring.md, deployment_gates.md) are emitted at governance_templates.py:812-823. → The tier-3+ block (_tier_at_least(risk_tier, 'tier_3_moderate')) that emits three_pillar_validat... | In docs/wiki/claims-model-starter/Worked-Examples.md, update line 183 from "Tier-3+ (`governance_templates.py:812-823`):" to "Tier-3+ (`governance_templates.py:846-855`):". While editing this secti... |
| low | stale | `Worked-Examples.md:189` | `src/model_project_constructor/agents/website/governance_templates.py:880` | Consumer-facing artifact eu_ai_act_compliance.md is emitted at governance_templates.py:847-851. → The affects_consumers branch emitting governance/eu_ai_act_compliance.md is now at lines 880-884; lines 847-851 actually fall inside the ti... | In /Users/rmsharp/Development/model_project_constructor/docs/wiki/claims-model-starter/Worked-Examples.md:189, change the citation from `governance_templates.py:847-851` to `governance_templates.py... |
| low | stale | `Worked-Examples.md:254` | `src/model_project_constructor/agents/website/governance_templates.py:857` | Tier-2+ artifacts (impact_assessment.md, regulatory_mapping.md) are emitted at governance_templates.py:824-841. → The tier-2+ block (_tier_at_least(risk_tier, 'tier_2_high')) emitting impact_assessment.md and regulatory_mapping.md (via b... | In Worked-Examples.md:254, change "Tier-2+ (`governance_templates.py:824-841`):" to "Tier-2+ (`governance_templates.py:857-873`):". Note the two adjacent ranges on the same page likely also drifted... |
| low | stale | `Worked-Examples.md:259` | `src/model_project_constructor/agents/website/governance_templates.py:875` | Tier-1-only artifacts (lcp_integration.md, audit_log/README.md) are emitted at governance_templates.py:842-846. → The tier-1 block (_tier_at_least(risk_tier, 'tier_1_critical')) emitting lcp_integration.md and audit_log/README.md is now ... | In docs/wiki/claims-model-starter/Worked-Examples.md:259, change "Tier-1 only (`governance_templates.py:842-846`):" to "Tier-1 only (`governance_templates.py:875-878`):". (For consistency, the adja... |
| low | stale | `Worked-Examples.md:264` | `src/model_project_constructor/agents/website/governance_templates.py:889` | Fairness scaffolds (fairness_audit.qmd, fairness/__init__.py, fairness/audit.py, test_fairness.py) are at governance_templates.py:856-904, triggered by uses_protected_attributes=true. → The fairness scaffolds are split across build_analy... | Update Worked-Examples.md:264 to cite the two functions that actually emit the fairness scaffolds, e.g.: "Fairness scaffolds (`build_analysis_files` at `governance_templates.py:889-909` and `build_... |


---

## Appendix B — Audit Provenance

- **Workflow:** `wiki-vs-code-accuracy-audit` · run `wf_8eebc0d5-72d` · task `we99jsxey`
- **Scale:** 125 subagents · 1,144 tool uses · ~3.99M subagent tokens · ~16 min wall-clock
- **Structure:** 22 page-review agents → adversarial verify per finding → 8 completeness-sweep agents → 1 synthesis agent
- **Verification discipline:** every reported discrepancy passed an independent skeptic whose default verdict was *false-positive*; 15 of 94 candidates (16%) were discarded as not-real, leaving 79 confirmed.
- **Scope boundary:** technical/factual claims only. Narrative, design rationale, roadmap aspiration, and changelog *history* were explicitly excluded from "drift."
- **Code baseline:** `master` @ `084a832` (S133) · **Wiki baseline:** `2b548a4` (S114).
- **Reproduce the headline counts:** `git log --oneline 2b548a4..HEAD | wc -l` (39 commits since wiki froze); test count `grep -rhE '^\s*(async )?def test_' tests/ | wc -l`.
