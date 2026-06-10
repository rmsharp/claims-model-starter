# Monitoring and Operations

## Environment variables

Every secret and configuration parameter is read from the environment via `OrchestratorSettings.from_env()`. No hardcoded hosts, URLs, or credentials exist in the codebase.

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `MPC_HOST` | No | `gitlab` | Target host: `gitlab` or `github` |
| `MPC_HOST_URL` | No | Host-specific default | Override for self-hosted instances |
| `GITLAB_TOKEN` | If GitLab live | -- | PAT with `api` scope |
| `GITHUB_TOKEN` | If GitHub live | -- | PAT with `repo` scope |
| `ANTHROPIC_API_KEY` | For live LLM calls | -- | Claude API authentication |
| `MPC_CHECKPOINT_DIR` | No | `./.orchestrator/checkpoints` | Checkpoint storage root |
| `MPC_LOG_LEVEL` | No | `INFO` | Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL |
| `MPC_NAMESPACE` | No | -- | Target group/org path (e.g. `rmsharp-modelpilot`); must be a path, not a URL |
| `INTAKE_DB_PATH` | No | `./intake_sessions.db` | SQLite file for intake web UI sessions |

Use `OrchestratorSettings.require_host_token()` / `require_anthropic_api_key()` inside runners that make HTTP calls. The settings object is constructable without secrets so tests and dry runs work without them.

## Checkpoint layout

`CheckpointStore(base_dir)` persists every inter-agent handoff as a JSON envelope:

```
<MPC_CHECKPOINT_DIR>/<run_id>/
    IntakeReport.json           # HandoffEnvelope
    DataRequest.json            # HandoffEnvelope
    DataReport.json             # HandoffEnvelope
    RepoTarget.json             # HandoffEnvelope
    RepoProjectResult.result.json   # Terminal result (plain JSON, not envelope)
```

The `.result.json` suffix distinguishes the terminal artifact from envelopes.

### Diagnosing a failed run

Which files are present tells you exactly how far the run got:

| Files present | Pipeline reached |
|--------------|-----------------|
| (empty directory) | Failed before intake |
| `IntakeReport.json` only | Intake succeeded, data agent failed |
| `...DataReport.json` | Data agent succeeded, website agent failed |
| `...RepoProjectResult.result.json` | Pipeline completed |

### Re-running

Resuming is **not** automatic on `run_id` reuse. Re-running with the same `run_id` and no `--resume` flag re-executes every stage and **overwrites** the existing checkpoints — you lose prior work.

To resume an interrupted run, pass `--resume <run_id>`: the CLI reads `<checkpoint_dir>/<run_id>/`, finds the first missing or incomplete envelope via `determine_resume_point`, loads the completed predecessor stages, and re-executes from there. `--resume` overrides `--run-id`, and it rejects when the checkpoint directory is missing or the run is already complete. A fresh `run_id` (the auto-generated default) always starts from scratch.

See `OPERATIONS.md` §5 and the `scripts/run_pipeline.py` `--resume` flag for full details.

## Observability

### Structured logging

The orchestrator uses `make_logged_runner()` to wrap agent runners with structured logging. Log entries include:

- Agent name + run_id + correlation_id
- Status (COMPLETE / FAILED / etc.)
- Duration (milliseconds) of agent call
- Error details for failures (type, message, duration)

Set `MPC_LOG_LEVEL=DEBUG` for verbose output including handoff payloads.

### Metrics

`MetricsRegistry` + `make_measured_runner()` capture:

- `run_count` — total pipeline runs recorded (process-global, via `record_run(status)`)
- `status_counts` — counts by status (COMPLETE, FAILED, etc.)
- `agent_latency` (milliseconds) per agent — `count` / `mean_ms` / `max_ms` aggregates

Access metrics programmatically:

```python
from model_project_constructor.orchestrator.metrics import MetricsRegistry

registry = MetricsRegistry()
# ... run pipeline with measured runners ...
snapshot = registry.snapshot()
print(snapshot.run_count)
print(snapshot.agent_latency)
```

## CI pipeline

The project's own CI (`.github/workflows/ci.yml`) runs four jobs:

| Job | What it checks |
|-----|---------------|
| **Lint** | `ruff check src/ tests/ packages/ scripts/` |
| **Type check** | `mypy` (strict mode, config-driven) |
| **Tests** | `pytest -q` (~795 tests, >95% coverage) |
| **Decoupling** | Data Agent has zero imports from intake schemas |

CI runs on push to `master` and on pull requests.

## Generated project CI

The CI pipeline in the generated repository is simpler:

| Job | What it checks |
|-----|---------------|
| **Lint** | `ruff check` |
| **Test** | `pytest` |
| **Governance** | Schema validation of `model_registry.json` |

## Value Demonstration

The pipeline captures a model's business value across two phases, both surfaced in the generated project:

- **Pre-construction (intake estimate).** The intake interview records an `EstimatedValue` business case — annual impact band, cost of inaction, implementation cost, payback, and value drivers. The Website Agent renders it into `analysis/01_business_understanding.qmd`.
- **Post-production (measurement methodology).** The intake also records a `ValueMeasurementPlan`, and the Data Agent collects a `BaselineSnapshot` of the current-state metric. The Website Agent renders both into the Production Measurement Plan in `analysis/06_implementation_plan.qmd`.

The Production Measurement Plan threads a single coherent argument:

| Step | Section in `06_implementation_plan.qmd` | Source |
|------|------------------------------------------|--------|
| **Baseline** — where the metric stands today | `## Baseline` | `DataReport.baseline_snapshot` (Data Agent) |
| **Counterfactual** — how lift will be isolated | `## Counterfactual Design` | `ValueMeasurementPlan` (intake) |
| **Attribution** — how lift maps back to the model | `## Attribution Method` | `ValueMeasurementPlan` (intake) |
| **Horizon & cadence** — when value is judged | `## Evaluation Horizon`, `## Review Cadence` | `ValueMeasurementPlan` (intake) |
| **Success criteria** — the bar the model must clear | `## Success Criteria` | `ValueMeasurementPlan` (intake) |
| **Decision rights** — who acts on the verdict | `## Decision Rights` | `ValueMeasurementPlan` (intake) |

The baseline figure is interpolated directly into the `.qmd` with a citation footnote pointing back to `reports/data_report.json`, so a stakeholder reading the plan sees the number without losing its provenance.

The **value-review cadence** (from `ValueMeasurementPlan.review_cadence`) is tracked separately from the **model-health monitoring cadence** (from the governance `cycle_time`): the first asks "is the model delivering the projected business value?", the second asks "is the model still statistically healthy?". The generated `governance/ongoing_monitoring.md` lists the business-value baseline metric alongside the model-health metrics so both are visible in one place.

These sections are **TODO scaffolding**, not live telemetry — the generated repo's Data Science team wires the actual production logging (the `## Logging Requirements` section enumerates the fields to instrument).

## Troubleshooting

For diagnostic walkthroughs by failure mode, see `TROUBLESHOOTING.md` in the project root.

Common issues:

| Symptom | Likely cause | Resolution |
|---------|-------------|-----------|
| `ConfigError: GITLAB_TOKEN is required for host='gitlab' but was not set` (or `GITHUB_TOKEN` for `host='github'`) | Missing host API token | Set `GITLAB_TOKEN` or `GITHUB_TOKEN` |
| `RepoNameConflictError` after 5 retries | Project name taken on host | Choose a different name or namespace |
| Checkpoint directory not writable | Permissions | Check `MPC_CHECKPOINT_DIR` path and permissions |
| Data Agent returns `EXECUTION_FAILED` | No database connection | Expected in dry-run mode; queries are still usable |
