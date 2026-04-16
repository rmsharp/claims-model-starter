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

Re-run with the same `run_id` to load existing checkpoints and resume from the next agent. A fresh `run_id` starts from scratch.

## Observability

### Structured logging

The orchestrator uses `make_logged_runner()` to wrap agent runners with structured logging. Log entries include:

- Run ID and agent name
- Start/end timestamps
- Status (COMPLETE / FAILED / etc.)
- Error details for failures

Set `MPC_LOG_LEVEL=DEBUG` for verbose output including handoff payloads.

### Metrics

`MetricsRegistry` + `make_measured_runner()` capture:

- `run_count` per agent
- `agent_latency` (seconds) per agent
- Pipeline-level timing

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
| **Lint** | `ruff check src/ tests/ packages/` |
| **Type check** | `mypy src/` (strict mode) |
| **Tests** | `pytest -q` (422+ tests, >94% coverage) |
| **Decoupling** | Data Agent has zero imports from intake schemas |

CI runs on push to `master` and on pull requests.

## Generated project CI

The CI pipeline in the generated repository is simpler:

| Job | What it checks |
|-----|---------------|
| **Lint** | `ruff check` |
| **Test** | `pytest` |
| **Governance** | Schema validation of `model_registry.json` |

## Troubleshooting

For diagnostic walkthroughs by failure mode, see `TROUBLESHOOTING.md` in the project root.

Common issues:

| Symptom | Likely cause | Resolution |
|---------|-------------|-----------|
| `MPC_HOST_TOKEN not set` | Missing env var | Set `GITLAB_TOKEN` or `GITHUB_TOKEN` |
| `RepoNameConflictError` after 5 retries | Project name taken on host | Choose a different name or namespace |
| Checkpoint directory not writable | Permissions | Check `MPC_CHECKPOINT_DIR` path and permissions |
| Data Agent returns `EXECUTION_FAILED` | No database connection | Expected in dry-run mode; queries are still usable |
