# Agent Reference

Detailed specifications for each agent in the pipeline.

## Intake Agent

### Purpose

Conducts a guided interview with a business stakeholder to capture the business problem, proposed solution, model solution, and estimated value. Acts as an expert data scientist, business analyst, and consultant in the P&C claims domain.

### Input schema

```
InterviewSessionConfig
  user_id:         str
  session_id:      str
  problem_statement: str  (stakeholder's initial description)
```

### Output schema

```
IntakeReport
  status:           "COMPLETE" | "DRAFT_INCOMPLETE"
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
    low_estimate:   float
    high_estimate:  float
    confidence:     str
    assumptions:    list[str]
  governance:        GovernanceMetadata
    cycle_time:                CycleTime
    risk_tier:                 RiskTier
    regulatory_frameworks:     list[str]
    affects_consumers:         bool
    uses_protected_attributes: bool
  questions_asked:   int  (tracked against 10-question cap)
  revision_cycles:   int
```

### Behavior

- Asks **one question at a time** (not multiple)
- **Max 10 questions** -- converges toward the four required sections
- Guides the stakeholder with domain expertise -- does not just transcribe answers
- Presents a draft for stakeholder review with up to **3 revision cycles**
- Status is `DRAFT_INCOMPLETE` if the cap is hit with gaps or the stakeholder rejects after 3 revisions

### Interfaces

| Interface | Command / URL |
|-----------|--------------|
| Web UI | `go/modelintake` (FastAPI + SSE + HTMX) |
| CLI | `model-intake-agent --fixture <file.yaml>` |
| Python | `IntakeAgent().run(config)` |

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
  target_variable:  str
  target_definition: str
  granularity:      str  (e.g., "claim-level", "policy-level")
  features:         list[str]
  population:       str  (e.g., "auto claims closed in 2020-2024")
  time_range:       str
```

**Note:** The Data Agent has no dependency on `IntakeReport`. The orchestrator adapts the intake report into a `DataRequest` at the boundary. This is enforced by a CI test.

### Output schema

```
DataReport
  status:                "COMPLETE" | "INCOMPLETE_REQUEST" | "EXECUTION_FAILED"
  primary_queries:       list[PrimaryQuery]
    name:                str
    sql:                 str
    quality_checks:      list[QualityCheck]
      name:              str
      sql:               str
      expected_result:   str
    datasheet:           Datasheet  (Gebru 2021)
  confirmed_expectations:   list[str]
  unconfirmed_expectations: list[str]
  data_quality_concerns:    list[str]
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
| CLI | `model-data-agent run --request request.json --output report.json` |
| Python | `DataAgent().run(data_request)` |
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
  host:          "gitlab" | "github"
  namespace:     str  (GitLab group path or GitHub org/owner)
  project_name:  str
  visibility:    "private" | "internal" | "public"
  host_url:      str | None  (override for self-hosted)
```

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
```

### Behavior

- **Phase 4A (base scaffold):** Renders README, pyproject.toml, src/ modules, analysis/ notebooks, queries/, tests/, reports/, data/
- **Phase 4B (governance scaffold):** Renders governance/ artifacts proportional to risk tier, CI config, pre-commit config, datasheets
- Creates the repository via `RepoClient.create_project()`
- Commits all files in a single atomic operation via `RepoClient.commit_files()`
- Retries on name conflicts with `-v2`, `-v3`, ... suffixes (up to 5 attempts)

### Host adapters

| Adapter | Library | Authentication |
|---------|---------|---------------|
| `PythonGitLabAdapter` | `python-gitlab` | Token-based |
| `PyGithubAdapter` | `PyGithub` | Token-based |
| `FakeRepoClient` | (none) | Test/dry-run -- no network |

### Failure modes

- `PARTIAL` -- repository created but some files failed to commit
- `FAILED` -- repository creation failed (permissions, network, name collision after 5 retries)
- Host API errors (bounded retry: 3 attempts with backoff)
