# Troubleshooting

Diagnostic walkthroughs for each `FAILED_AT_*` halt path in the
orchestrator pipeline. Each section tells you what to inspect, where the
files are, and what to do next. For the operational runbook see
`OPERATIONS.md`; for the system design see `docs/planning/
architecture-plan.md` §12 (orchestration) and §14 (phases).

---

## Common diagnostics

Regardless of which stage failed, start here:

1. **Find the run's checkpoint directory:**
   ```
   $MPC_CHECKPOINT_DIR/<run_id>/
   ```
   Default: `.orchestrator/checkpoints/<run_id>/`.

2. **List what's on disk:**
   ```bash
   ls -la "$MPC_CHECKPOINT_DIR/<run_id>/"
   ```
   Which files exist tells you how far the run got (see `OPERATIONS.md`
   §2 for the full matrix).

3. **Check the structured logs.** If you wrapped runners with
   `make_logged_runner`, look for `agent.error` events at level
   `ERROR` in the `model_project_constructor.orchestrator` logger. The
   `context` dict includes `error_type`, `error_message`, and
   `duration_ms`.

4. **Check metrics.** If you used `MetricsRegistry`, call
   `registry.snapshot()` to see the status distribution and per-agent
   latency at a glance.

---

## FAILED_AT_INTAKE

**What happened:** The Intake Agent returned an `IntakeReport` with
`status != "COMPLETE"` (usually `DRAFT_INCOMPLETE`).

**Checkpoint state:** Only `IntakeReport.json` is present.

**What to inspect:**

```python
from pathlib import Path
from model_project_constructor.orchestrator import CheckpointStore

store = CheckpointStore(Path("<checkpoint_dir>"))
intake = store.load_payload("<run_id>", "IntakeReport")
print(intake.status)          # e.g. "DRAFT_INCOMPLETE"
print(intake.missing_fields)  # list of fields the stakeholder didn't provide
```

**Root causes:**
- The stakeholder didn't answer enough questions (the agent hit its
  10-question cap before converging on all 4 required sections).
- The fixture used in a scripted run was incomplete or missing fields.

**Resolution:**
- If live: run a new intake interview with the stakeholder, focusing on
  the `missing_fields`. Feed the completed report back into the pipeline
  as a new run.
- If fixture: fix the fixture file and re-run.

---

## FAILED_AT_DATA

**What happened:** The Data Agent returned a `DataReport` with
`status != "COMPLETE"` (e.g. `EXECUTION_FAILED`, `INCOMPLETE_REQUEST`).

**Checkpoint state:** `IntakeReport.json`, `DataRequest.json`, and
`DataReport.json` are present. `RepoTarget.json` is NOT written
(the pipeline halts before the website stage).

**What to inspect:**

```python
store = CheckpointStore(Path("<checkpoint_dir>"))
request = store.load_payload("<run_id>", "DataRequest")
report  = store.load_payload("<run_id>", "DataReport")
print(report.status)
print(report.data_quality_concerns)
print(report.summary)
for q in report.primary_queries:
    print(q.name, q.status, q.sql)
```

**Root causes:**
- `EXECUTION_FAILED`: a SQL query failed against the database. Check
  `report.primary_queries` for individual query statuses and error
  messages. Common causes: table doesn't exist, column renamed, read-
  only credential lacks permission on a specific schema.
- `INCOMPLETE_REQUEST`: the `DataRequest` built by the adapter was
  too ambiguous for the Data Agent. Check
  `request.target_description` and `request.required_features`.
- Database connectivity: the `db_url` or read-only credential was
  wrong or expired.

**Resolution:**
- Fix the upstream problem (database access, query logic, or the
  intake report's `target_definition`).
- Re-run with a fresh `run_id`. The intake stage is deterministic
  for fixtures, so you can stub it with the checkpoint:
  ```python
  intake = store.load_payload("<old_run_id>", "IntakeReport")
  result = run_pipeline(
      new_config,
      intake_runner=lambda: intake,
      data_runner=real_data_runner,
      website_runner=real_website_runner,
  )
  ```

---

## FAILED_AT_WEBSITE

**What happened:** The Website Agent returned a `RepoProjectResult`
with `status != "COMPLETE"` (usually `FAILED` or `PARTIAL`).

**Checkpoint state:** All envelope files AND
`RepoProjectResult.result.json` are present. The terminal result is
persisted even on failure so you can inspect the partial project.

**What to inspect:**

```python
import json
from pathlib import Path

result_path = Path("<checkpoint_dir>/<run_id>/RepoProjectResult.result.json")
result = json.loads(result_path.read_text())
print(result["status"])
print(result["failure_reason"])
print(result["files_created"])     # partial list if PARTIAL
print(result["project_url"])       # may be set even on FAILED if the project was created
```

**Root causes:**
- `FAILED`: the repo host rejected the commit or project creation.
  Common causes: expired token, namespace doesn't exist, name
  collision (project already exists), permission error.
- `PARTIAL`: the project was created but some files failed to commit
  (e.g. the governance tier required an artifact that hit a template
  error). Check `files_created` against the expected set.
- Timeout: the repo host was too slow. Check `duration_ms` in the
  `agent.end` or `agent.error` log event.

**Resolution:**
- Fix the host-side issue (token, permissions, namespace).
- If the project was partially created, delete the partial project on
  the host before re-running. The Website Agent creates idempotent
  commits but does NOT delete existing projects.
- Re-run with a fresh `run_id`, stubbing the intake and data stages
  with the previous checkpoints if they were fine:
  ```python
  intake = store.load_payload("<old_run_id>", "IntakeReport")
  data   = store.load_payload("<old_run_id>", "DataReport")
  result = run_pipeline(
      new_config,
      intake_runner=lambda: intake,
      data_runner=lambda _req: data,
      website_runner=real_website_runner,
  )
  ```

---

## Unhandled exceptions (pipeline crash)

If the pipeline raises an unhandled exception (as opposed to returning
a `FAILED_AT_*` status), the `PipelineResult` was never constructed.
The checkpoint files written before the crash are still on disk.

**What to inspect:**
- The exception traceback from the caller's error handler.
- The `agent.error` structured log event (if runners were instrumented
  with `make_logged_runner`).
- The checkpoint directory — files stop at whichever stage was running
  when the crash happened.

**Resolution:**
- Treat as a bug. The pipeline is designed to capture all agent-level
  failures as status codes and only crash on true infrastructure
  failures (disk full, network timeout, serialization error in the
  checkpoint store, etc.).
- File a bug report with the traceback and the checkpoint directory
  contents.

---

## Quick reference

| Symptom | First action |
|---|---|
| `ConfigError: GITLAB_TOKEN is required` | Set `GITLAB_TOKEN` in the environment or `.env` file. |
| `ConfigError: MPC_HOST must be 'gitlab' or 'github'` | Check the `MPC_HOST` env var for typos. |
| Run completes but no project on host | Check `result.status` — it may be `FAILED_AT_WEBSITE` with a descriptive `failure_reason`. |
| All checkpoints present but `status=FAILED` | Read `RepoProjectResult.result.json → failure_reason`. Usually a host-side permission issue. |
| No checkpoint directory at all | The pipeline crashed before the first agent returned. Check the traceback and `agent.error` log events. |
| Tests pass locally, CI fails | Check that CI has `uv` available and runs `uv sync --extra agents --extra dev` before `pytest`. See `.github/workflows/ci.yml`. |
