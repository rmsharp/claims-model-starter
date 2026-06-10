# Pipeline Overview

## Architecture

The pipeline is a sequential chain of three LLM-backed agents, each producing a structured report that becomes the next agent's input. An orchestrator drives the chain and persists inter-agent handoffs as checkpoint envelopes.

```
Stakeholder
    |
    v
[Intake Agent]  -- guided interview (max 20 questions)
    | IntakeReport
    v
[Data Agent]    -- SQL generation + quality checks
    | DataReport
    v
[Website Agent] -- repository scaffolding + governance
    | RepoProjectResult
    v
GitLab/GitHub repository (draft model website)
    |
    v
Data Science Team (human refinement)
```

## Handoff protocol

Every inter-agent boundary uses a `HandoffEnvelope`:

```
HandoffEnvelope
  envelope_version: "1.0.0"
  run_id:           orchestrator-assigned UUID
  source_agent:     "intake" | "data" | "website"
  target_agent:     "intake" | "data" | "website"
  payload_type:     e.g. "IntakeReport"
  payload_schema_version: e.g. "1.0.0"
  payload:          validated Pydantic model (JSON)
  created_at:       ISO timestamp
  correlation_id:   trace ID
```

A schema registry maps `(payload_type, schema_version)` to the Pydantic class for two-step validation: first the envelope, then the payload.

## Agent summary

### Intake Agent

- **Input:** seeded via `initial_state` with stakeholder ID, session ID, domain, and initial problem (no config object)
- **Output:** `IntakeReport`
- **Behavior:** Asks one question at a time (max 20), drives toward five sections (business problem, proposed solution, model solution, estimated value, and a value measurement plan) plus governance metadata. Presents a draft for stakeholder review with up to 3 revision cycles.
- **Interfaces:** Web UI (`go/modelintake`), CLI (`model-intake-agent`), Python API
- **Status values:** `COMPLETE`, `DRAFT_INCOMPLETE`

### Data Agent

- **Input:** `DataRequest` (target, granularity, features, population, time range; optionally a `DataSourceInventory`)
- **Output:** `DataReport`
- **Behavior:** Generates SQL queries, writes quality-check queries, confirms data expectations, produces natural-language summary and Gebru 2021 datasheets per query. When `DataRequest.data_source_inventory` is set, the query-generation prompt includes a summarized inventory block and each `PrimaryQuery.inventory_entries_used` records which catalogued tables the SQL references. When the upstream `IntakeReport` carries a `value_measurement_plan`, the agent also generates and executes a baseline query and records the current-state metric on `DataReport.baseline_snapshot` (it executes the measurement; intake defines it).
- **Interfaces:** CLI (`model-data-agent run`, `model-data-agent discover`), Python API, pipeline mode
- **Status values:** `COMPLETE`, `INCOMPLETE_REQUEST`, `EXECUTION_FAILED`
- **Design note:** Intentionally decoupled from `IntakeReport` -- usable as a standalone query tool for analyst teams. A CI test enforces zero imports of intake schemas.

### Website Agent

- **Input:** `IntakeReport` + `DataReport` + `RepoTarget`
- **Output:** `RepoProjectResult`
- **Behavior:** Creates a repository, scaffolds `.qmd` analysis notebooks and `src/` Python modules, generates governance artifacts proportional to risk tier, commits all files in a single atomic operation. Renders the intake's business case (impact band, cost of inaction, payback) into `analysis/01_business_understanding.qmd` and a structured Production Measurement Plan (baseline, counterfactual, attribution, success criteria) into `analysis/06_implementation_plan.qmd`.
- **Status values:** `COMPLETE`, `PARTIAL`, `FAILED`

## Orchestrator

The orchestrator (`orchestrator/pipeline.py`) calls each agent's runner function in sequence:

1. **INTAKE** -- produces `IntakeReport` (or loads from checkpoint)
2. **DATA** -- adapts `IntakeReport` to `DataRequest` (optionally deriving a `DataSourceInventory` from `IntakeReport.qa_pairs` when `--inventory-from-intake` is set, via `intake_qa_pairs_to_inventory` in `orchestrator/adapters.py`), produces `DataReport`
3. **WEBSITE** -- combines both reports with `RepoTarget`, produces `RepoProjectResult`

If any agent returns a non-`COMPLETE` status, the pipeline halts. Checkpoints are persisted after each successful step, so a failed run can be inspected and resumed. Pass `--resume <run_id>` to reload from the checkpoint and re-execute from the first incomplete stage.

## Error handling

- Each agent returns a structured report with a `status` field -- no exceptions for expected failures.
- The orchestrator does not retry failed agents. The operator reviews the checkpoint and re-runs.
- Agents have bounded internal retries (e.g., 1 retry for invalid SQL, 3 with backoff for host API errors).
- Every handoff is persisted as a JSON file under `MPC_CHECKPOINT_DIR/<run_id>/`.

See [Agent Reference](Agent-Reference) for detailed schemas and behavior.
