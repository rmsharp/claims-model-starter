# Agent Reference

Detailed specifications for each agent in the pipeline.

## Intake Agent

### Purpose

Conducts a guided interview with a business stakeholder to capture the business problem, proposed solution, model solution, estimated value, and value-measurement plan. Acts as an expert data scientist, business analyst, and consultant in the P&C claims domain.

### Input schema

The intake graph has no single config object. The headless facade `IntakeAgent.run_scripted` / `run_with_fixture` seeds the graph state via `initial_state(...)`:

```
initial_state
  stakeholder_id:  str         # session identity (NOT user_id)
  session_id:      str         # LangGraph thread_id
  domain:          str = "pc_claims"
  initial_problem: str | None  # stakeholder's initial description
```

`run_scripted` additionally takes:

```
review_responses:  list[str]                     # required; one per review interrupt
interview_answers: list[str] | None = None       # fixed answers consumed in order
answer_provider:   AnswerProvider | None = None  # answers on demand (live runs)
domain:            str = "pc_claims"
initial_problem:   str | None = None
```

Supply **exactly one** of `interview_answers` / `answer_provider` -- passing both, or neither, raises `ValueError`. A fixed list raises `RuntimeError` if the graph asks more questions than were supplied; an `AnswerProvider` is called with each question actually asked, so it cannot run out -- that is the path used to drive a live model (`tests/eval/stakeholder_sim.py` implements the protocol; `tests/eval/test_eval_live.py` and `tests/eval/shadow_run.py` pass it in).

Source of truth: `initial_state` (`src/model_project_constructor/agents/intake/state.py`) and `run_scripted` (`src/model_project_constructor/agents/intake/agent.py`).

### Output schema

```
IntakeReport
  schema_version:    "1.0.0"
  status:            "COMPLETE" | "DRAFT_INCOMPLETE"
  missing_fields:    list[str]
  business_problem:  str
  proposed_solution: str
  model_solution:    ModelSolution
    target_variable:      str | None
    target_definition:    str
    candidate_features:   list[str]
    model_type:           "supervised_classification" | "supervised_regression" | ...
    evaluation_metrics:   list[str]
    is_supervised:        bool
  estimated_value:   EstimatedValue
    narrative:              str
    annual_impact_usd_low:  float | None
    annual_impact_usd_high: float | None
    confidence:             "low" | "medium" | "high"
    assumptions:            list[str]
    # optional extension fields:
    cost_of_inaction_narrative:        str | None
    annual_cost_of_inaction_usd_low:   float | None
    annual_cost_of_inaction_usd_high:  float | None
    implementation_cost_band_usd_low:  float | None
    implementation_cost_band_usd_high: float | None
    payback_months:                    int | None
    value_drivers:                     list[str]
  value_measurement_plan: ValueMeasurementPlan | None
  governance:        GovernanceMetadata
    cycle_time:                CycleTime
    cycle_time_rationale:      str
    risk_tier:                 RiskTier
    risk_tier_rationale:       str
    regulatory_frameworks:     list[str]
    affects_consumers:         bool
    uses_protected_attributes: bool
  stakeholder_id:    str
  session_id:        str
  created_at:        datetime
  questions_asked:   int  (tracked against 20-question cap)
  revision_cycles:   int
  qa_pairs:          list[QAPair] = Field(default_factory=list)
```

### Behavior

- Asks **one question at a time** (not multiple)
- **Max 20 questions** -- converges toward the five required sections
- Guides the stakeholder with domain expertise -- does not just transcribe answers
- Presents a draft for stakeholder review with up to **3 revision cycles**
- Status is `DRAFT_INCOMPLETE` if the cap is hit with gaps or the stakeholder rejects after 3 revisions

### Interfaces

| Interface | Command / URL |
|-----------|--------------|
| Web UI | `go/modelintake` (FastAPI + SSE + HTMX) |
| CLI | `model-intake-agent --fixture <file.yaml>` |
| Python | `IntakeAgent(llm=make_llm_client()).run_with_fixture("interview.yaml")` (lower-level: `run_scripted(stakeholder_id=, session_id=, interview_answers=, review_responses=)`) |

### Failure modes

- Incomplete interview (checkpoint available for resume)
- Question cap hit with information gaps
- LLM refusal (rare; domain is business-appropriate)

---

## Data Agent

### Purpose

Generates SQL queries to collect relevant data, writes quality-check queries, and confirms expectations about the data. Designed to be reusable as a standalone query-writing tool for analyst teams.

### Input schema

```
DataRequest
  schema_version:      "1.0.0"
  target_description:  str
  target_granularity:  DataGranularity { unit: str; time_grain: "event" | "daily" | "weekly" | "monthly" | "quarterly" | "annual" }
  required_features:   list[str]
  population_filter:   str  (e.g., "auto claims closed in 2020-2024")
  time_range:          str
  source:              "pipeline" | "standalone"   (required)
  source_ref:          str                         (required)
  # optional: database_hint, data_quality_concerns, data_source_inventory,
  #           baseline_metric_name / baseline_metric_definition / baseline_measurement_window
```

**Note:** Every Data Agent schema extends a `StrictBase` configured with `extra="forbid"`, so unknown or legacy field names (e.g. `target_variable`, `granularity`, `features`, `population`) raise a validation error rather than being silently ignored.

**Note:** The Data Agent has no dependency on `IntakeReport`. The orchestrator adapts the intake report into a `DataRequest` at the boundary. This is enforced by a CI test.

### Output schema

```
DataReport
  schema_version:           "1.0.0"
  status:                   "COMPLETE" | "INCOMPLETE_REQUEST" | "EXECUTION_FAILED"
  request:                  DataRequest  (echoed from input)
  primary_queries:          list[PrimaryQuery]
    name:                    str
    sql:                     str
    purpose:                 str
    expected_row_count_order: "tens" | "hundreds" | "thousands" | "millions"
    quality_checks:          list[QualityCheck]
      check_name:        str
      check_sql:         str
      expectation:       str
      execution_status:  "PASSED" | "FAILED" | "ERROR" | "NOT_EXECUTED"
      result_summary:    str
      raw_result:        dict | None
    datasheet:               Datasheet  (Gebru 2021)
    inventory_entries_used:  list[str]
  summary:                  str  (natural-language summary)
  confirmed_expectations:   list[str]
  unconfirmed_expectations: list[str]
  data_quality_concerns:    list[str]
  created_at:               datetime
  baseline_snapshot:        BaselineSnapshot | None
```

### Behavior

- Generates SQL queries targeting the specified data
- Writes quality-check queries per primary query
- Produces Gebru 2021 datasheets per primary query
- Attempts read-only execution against a live database (if available)
- Produces a natural-language summary

### Interfaces

| Interface | Command |
|-----------|---------|
| CLI (run) | `model-data-agent run --request request.json --output report.json` |
| CLI (discover) | `model-data-agent discover --db-url <url> --output inventory.json` (probes information_schema into a DataSourceInventory) |
| Python | `DataAgent(llm=make_llm_client()).run(data_request)` |
| Pipeline | Called by orchestrator with adapted `DataRequest` |

### Failure modes

- `INCOMPLETE_REQUEST` -- insufficient information to generate useful queries
- `EXECUTION_FAILED` -- queries generated but could not be validated against a database
- Invalid SQL (bounded retry: 1 attempt)

---

## Website Agent

### Purpose

Takes both reports and scaffolds a complete repository project on GitLab or GitHub with a draft model website, tested Python modules, and governance artifacts proportional to risk.

### Input schemas

```
IntakeReport     (from Intake Agent)
DataReport       (from Data Agent)
RepoTarget
  schema_version:    "1.0.0"
  host_url:          str  (required; API base URL -- defaults resolved by the CLI from the REPO_PLATFORMS registry)
  namespace:         str  (GitLab group path or GitHub org/owner)
  project_name_hint: str
  visibility:        "private" | "internal" | "public"  (default "private")
```

Host selection is **not** a `RepoTarget` field. The target host is chosen with the CLI `--host` flag (`"gitlab"` | `"github"`), validated against the `REPO_PLATFORMS` registry in `orchestrator/config.py`, which also supplies the default `host_url` for that host.

### Output schema

```
RepoProjectResult
  status:              "COMPLETE" | "PARTIAL" | "FAILED"
  project_url:         str
  project_id:          str  (host-opaque: GitLab int, GitHub "owner/name")
  initial_commit_sha:  str
  files_created:       list[str]
  governance_manifest: GovernanceManifest
    model_registry_entry:  dict
    artifacts_created:     list[str]
    risk_tier:             RiskTier
    cycle_time:            CycleTime
    regulatory_mapping:    dict[str, list[str]]
  failure_reason:      str | None  (populated when status is "PARTIAL" or "FAILED")
```

### Behavior

- **Phase 4A (base scaffold):** Renders README, pyproject.toml, src/ modules, analysis/ notebooks, queries/, tests/, reports/, data/
- **Phase 4B (governance scaffold):** Renders governance/ artifacts proportional to risk tier, CI config, pre-commit config, datasheets
- Creates the repository via `RepoClient.create_project()`
- Commits all files in a single atomic operation via `RepoClient.commit_files()`
- Retries on name conflicts with `-v2`, `-v3`, ... suffixes (up to 5 attempts)

### Interfaces

| Interface | Command |
|-----------|----------|
| CLI | `python -m model_project_constructor.agents.website --intake <intake.json> --data <data.json> --host gitlab` |
| Python | `WebsiteAgent(repo_client).run(intake_report, data_report, repo_target)` |

### Host adapters

| Adapter | Library | Authentication |
|---------|---------|---------------|
| `GitLabAdapter` | `httpx` (direct REST calls) | Token-based |
| `GitHubAdapter` | `httpx` (direct REST calls) | Token-based |
| `FakeRepoClient` | (none) | Test/dry-run -- no network |

### Failure modes

- `PARTIAL` -- repository created but some files failed to commit
- `FAILED` -- repository creation failed (permissions, network, name collision after 5 retries)
- Host API errors (bounded retry: 3 attempts with backoff)
