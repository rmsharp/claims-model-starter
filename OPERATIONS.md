# Operations runbook

Operator-facing runbook for running the Model Project Constructor
pipeline in a live environment. Audience: whoever is on the hook when a
run fails or a pilot needs to be re-kicked. For the system design see
`docs/planning/architecture-plan.md`; for diagnostic walkthroughs by
failure mode see `TROUBLESHOOTING.md`.

---

## 1. Environment variables

Every secret and every deployment-variable parameter is read from the
environment via `OrchestratorSettings.from_env()` — see
`src/model_project_constructor/orchestrator/config.py`. There are no
hardcoded hosts, URLs, or credentials anywhere in the codebase. Copy
`.env.example` to `.env` and populate the values appropriate for your
deployment, then load it (e.g. via `python-dotenv`, direnv, or your
orchestration layer's secret injection) before running the pipeline.

| Variable | Required | Default | Notes |
|---|---|---|---|
| `MPC_HOST` | no | `gitlab` | `gitlab` or `github`. |
| `MPC_HOST_URL` | no | host-specific | `https://gitlab.com` or `https://api.github.com`. Override for self-hosted / enterprise instances. |
| `MPC_NAMESPACE` | no | host-specific (script-level) | Target group/org path where the Website Agent creates the project. **Must be a path, never a URL** — e.g. `rmsharp-modelpilot` or `data-science/model-drafts`, not `https://gitlab.com/rmsharp-modelpilot`. Rejected at config-load time (`ConfigError`) if it starts with `http://` or `https://`. |
| `GITLAB_TOKEN` | yes (if `MPC_HOST=gitlab` and live) | — | Personal access token with `api` scope and create-project permission on the target namespace. |
| `GITHUB_TOKEN` | yes (if `MPC_HOST=github` and live) | — | PAT with `repo` scope on the target owner/org. |
| `ANTHROPIC_API_KEY` | yes (for any runner that calls Claude) | — | Required by the Intake Agent web UI, any live interview, and the Data Agent's QC generation. |
| `MPC_CHECKPOINT_DIR` | no | `./.orchestrator/checkpoints` | Root for the `CheckpointStore`. Each run lands in a subdirectory named after its `run_id`. |
| `MPC_LOG_LEVEL` | no | `INFO` | Stdlib level name: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`. |
| `INTAKE_DB_PATH` | no | `./intake_sessions.db` | SQLite file for the intake web UI's live session state. Only read by the UI. |

Use `OrchestratorSettings.require_host_token()` /
`require_anthropic_api_key()` inside runners that actually make HTTP
calls — the settings object is constructable without these so that
tests and preview runs can skip them.

---

## 2. Checkpoint layout

`CheckpointStore(base_dir)` writes every inter-agent handoff as a
JSON envelope plus a terminal plain-JSON result. For a run with
`run_id="run_abc"` and `MPC_CHECKPOINT_DIR=/var/lib/mpc/checkpoints`:

```
/var/lib/mpc/checkpoints/run_abc/
    IntakeReport.json          # HandoffEnvelope(payload_type=IntakeReport)
    DataRequest.json           # HandoffEnvelope(payload_type=DataRequest)
    DataReport.json            # HandoffEnvelope(payload_type=DataReport)
    RepoTarget.json            # HandoffEnvelope(payload_type=RepoTarget)
    RepoProjectResult.result.json   # terminal result (not an envelope)
```

The `.result.json` suffix is load-bearing: it guarantees the terminal
artifact cannot collide with an envelope even if a registered payload
type happens to be named `RepoProjectResult`. Envelopes conform to
`schemas/envelope.py`; the terminal result is a plain
`RepoProjectResult` Pydantic dump.

Which files are present tells you exactly how far a run got:

| Files present | Interpretation |
|---|---|
| `IntakeReport.json` only | Halted at intake; see `failure_reason` in the run's `PipelineResult` or the intake report's `status` field. |
| `IntakeReport.json`, `DataRequest.json`, `DataReport.json` | Halted at data; the Data Agent produced a non-`COMPLETE` report. |
| Plus `RepoTarget.json` and `RepoProjectResult.result.json` | Website phase reached. Check the result's `status` to distinguish `COMPLETE` from `FAILED`. |

The full `PipelineResult` is NOT persisted to disk — the orchestrator
returns it in-process. If you need the terminal status after a crash,
reconstruct it from the checkpoint files.

---

## 3. Observability integration

The orchestrator ships with two optional modules that wrap agent
runners; `pipeline.py` itself has no observability imports, so
instrumentation is opt-in per deployment.

### 3.1 Structured logging (`orchestrator/logging.py`)

`make_logged_runner(runner, *, agent_name, run_id, correlation_id)`
returns a wrapped callable that emits three event types via stdlib
`logging` to the `model_project_constructor.orchestrator` namespace:

| Event | Level | Context fields |
|---|---|---|
| `agent.start` | INFO | `agent`, `run_id`, `correlation_id` |
| `agent.end` | INFO | plus `duration_ms`, `status` |
| `agent.error` | ERROR | plus `duration_ms`, `error_type`, `error_message` |

All structured fields land on the log record's `extra={"context": ...}`
dict. To produce JSON logs, install a JSON formatter on the
`model_project_constructor.orchestrator` logger — for example
`python-json-logger`:

```python
import logging
from pythonjsonlogger import jsonlogger

handler = logging.StreamHandler()
handler.setFormatter(jsonlogger.JsonFormatter(
    "%(asctime)s %(name)s %(levelname)s %(message)s"
))
logging.getLogger("model_project_constructor.orchestrator").addHandler(handler)
```

### 3.2 Metrics (`orchestrator/metrics.py`)

`MetricsRegistry` is a thread-safe in-memory counter store with three
surfaces:

- `record_run(status)` — increment run count and status distribution.
- `record_agent_latency(agent, duration_ms)` — accumulate latency
  samples per agent.
- `snapshot() -> MetricsSnapshot` — immutable view for dashboards /
  assertions.

Wrap each runner with `make_measured_runner(runner, agent_name=...,
registry=...)`. Typical deployment:

```python
from model_project_constructor.orchestrator import (
    MetricsRegistry,
    make_logged_runner,
    make_measured_runner,
    run_pipeline,
)

metrics = MetricsRegistry()

def instrument(runner, name, config):
    return make_logged_runner(
        make_measured_runner(runner, agent_name=name, registry=metrics),
        agent_name=name,
        run_id=config.run_id,
        correlation_id=config.correlation_id,
    )

intake_runner  = instrument(real_intake_runner,  "intake",  config)
data_runner    = instrument(real_data_runner,    "data",    config)
website_runner = instrument(real_website_runner, "website", config)

result = run_pipeline(
    config,
    intake_runner=intake_runner,
    data_runner=data_runner,
    website_runner=website_runner,
)
metrics.record_run(result.status)
```

A Prometheus exporter is a post-pilot concern; for now, snapshot the
registry periodically and emit it to whatever observability surface
your deployment already has.

---

## 4. Running the pipeline

### 4.1 Against fake hosts (no credentials)

```bash
uv run python -m model_project_constructor.agents.website \
    --intake tests/fixtures/subrogation_intake.json \
    --data tests/fixtures/sample_datareport.json \
    --fake
```

This validates the scaffolding end-to-end without touching any live
host. It is the recommended smoke test before a live run and is run
by CI on every commit.

### 4.2 Against a live GitLab instance

```bash
export MPC_HOST=gitlab
export MPC_HOST_URL=https://gitlab.example.com
export GITLAB_TOKEN=...
export ANTHROPIC_API_KEY=...

uv run python -m model_project_constructor.agents.website \
    --intake intake.json \
    --data data.json \
    --host gitlab \
    --host-url "$MPC_HOST_URL" \
    --namespace data-science/model-drafts \
    --private-token "$GITLAB_TOKEN"
```

### 4.3 Against a live GitHub / GitHub Enterprise

```bash
export MPC_HOST=github
export MPC_HOST_URL=https://api.github.com      # or your GHE API URL
export GITHUB_TOKEN=...
export ANTHROPIC_API_KEY=...

uv run python -m model_project_constructor.agents.website \
    --intake intake.json \
    --data data.json \
    --host github \
    --namespace acme \
    --private-token "$GITHUB_TOKEN"
```

GitHub does not support nested namespaces; pass a single owner / org
as `--namespace`.

### 4.4 Scope B: real LLM-backed pipeline via `scripts/run_pipeline.py`

`scripts/run_pipeline.py` is the canonical end-to-end driver. It is
what CI exercises (with fakes) and what operator runs for smoke testing
and pilot runs. It accepts a `--llm` flag that selects which stages use
the real Anthropic API:

| `--llm` | Intake | Data | Cost per run | Determinism |
|---|---|---|---|---|
| `none` (default) | fixture | fixture | free | fully deterministic |
| `data` (B1) | fixture | real Anthropic | ~$0.10–$0.50 (model-dependent) | non-deterministic data stage |
| `both` (B2) | real Anthropic (scripted answers) | real Anthropic | ~$0.15–$0.75 | non-deterministic intake + data |

#### 4.4.1 B1 — real data agent (intake stays fixture)

Typical live B1 invocation against public GitLab:

```bash
export ANTHROPIC_API_KEY=...
export GITLAB_TOKEN=...
export MPC_HOST=gitlab
export MPC_HOST_URL=https://gitlab.com
export MPC_NAMESPACE=your-group/subgroup          # path only, NOT a URL

uv run python scripts/run_pipeline.py \
    --live --host gitlab --llm data \
    --model claude-opus-4-7 \
    --run-id run_b1_$(date +%Y%m%d_%H%M%S)
```

#### 4.4.2 B2 — real intake (scripted answers) + real data

B2 drives `IntakeAgent.run_scripted` with real Anthropic-generated
questions and fixture-supplied answers. The fixture's `draft_after`
field is a no-op in this mode — only the real LLM decides when it has
enough information — so the fixture needs enough `qa_pairs` to cover the
LLM's questions. Use a fixture with **at least `MAX_QUESTIONS` qa_pairs**
(currently `MAX_QUESTIONS=20` at `intake/state.py:57`) to guarantee the
graph terminates: if the LLM hasn't flipped `believe_enough_info` by
turn `MAX_QUESTIONS`, the graph drafts anyway with
`missing_fields=["questions_cap_reached"]` → `DRAFT_INCOMPLETE`. See
`tests/fixtures/subrogation_b2.yaml` for a working example (15 qa_pairs,
pre-answering latency SLA / recovery-per-claim / fairness-plan).

```bash
set -a; source .env; set +a

uv run python scripts/run_pipeline.py \
    --live --host gitlab --llm both \
    --model claude-opus-4-7 \
    --intake-fixture tests/fixtures/subrogation_b2.yaml \
    --run-id run_b2_$(date +%Y%m%d_%H%M%S)
```

If the fixture runs out of answers before the LLM is satisfied (and
before turn 10), or if Anthropic raises (rate limit, bad JSON), the
inline `_draft_incomplete_from_exception` adapter converts the error
into a `DRAFT_INCOMPLETE` `IntakeReport` and the orchestrator halts
cleanly with `FAILED_AT_INTAKE`. The run exits non-zero but leaves a
checkpoint envelope documenting the failure.

Flags:

- `--llm {none,data,both}` — `none` runs the fixture pipeline, `data`
  runs B1 (real data only), `both` runs B2 (real intake + real data).
- `--intake-fixture PATH` — required when `--llm=both`. YAML fixture
  supplying scripted answers and stakeholder/session identity. Ignored
  otherwise.
- `--model ID` — overrides the Anthropic model for BOTH the intake
  and data agents. Default is `claude-opus-4-7`. Other options include
  `claude-sonnet-4-6` (~5× cheaper) and `claude-haiku-4-5-20251001`
  (fastest, lowest quality).
- `--db-url URL` — optional; passes a SQLAlchemy URL so quality checks
  execute against a real read-only store. Omit for pilot runs.
- `--run-id ID` — embed a timestamp suffix when invoking repeatedly
  so checkpoint envelopes stay disambiguated across runs.

#### 4.4.3 Verify the LLM actually ran

Inspect the data envelope (B1 or B2):

```bash
python -c "
from pathlib import Path
import json
env = json.loads(
    Path('.orchestrator/checkpoints/<run_id>/DataReport.json').read_text()
)
report = env['payload']
print('status:', report['status'])
print('queries:', len(report['primary_queries']))
print('sql_preview:', report['primary_queries'][0]['sql'][:120])
"
```

If `sql_preview` differs from `tests/fixtures/sample_datareport.json`,
the real LLM ran. For B2, also inspect the intake envelope: the
`business_problem` + `proposed_solution` prose will differ from
`tests/fixtures/subrogation_intake.json` when Claude drafted, and
`questions_asked` will be between 1 and 10 for a real interview
(a DRAFT_INCOMPLETE stub reports `questions_asked: 0`).

---

## 5. Resume after a partial run

The orchestrator does not resume-in-place — a crashed run cannot be
continued from the middle. The intended recovery is:

1. Inspect `$MPC_CHECKPOINT_DIR/<run_id>/` to understand how far the
   run got. See §2 above.
2. Read the relevant envelope with `CheckpointStore.load_payload`:
   ```python
   from pathlib import Path
   from model_project_constructor.orchestrator import CheckpointStore

   store = CheckpointStore(Path("/var/lib/mpc/checkpoints"))
   intake = store.load_payload("run_abc", "IntakeReport")
   data   = store.load_payload("run_abc", "DataReport")   # if present
   ```
3. Decide: either fix the upstream problem and re-run with a fresh
   `run_id` (clean slate), or stub the already-complete stages with
   runners that return the loaded payloads and re-run with the SAME
   `run_id` to overwrite the halted state.

Phase 6 deliberately ships the second option as a manual recipe, not
automated resume logic — the architecture-plan §12 explicitly notes
that retry is the caller's decision.

---

## 6. Common pre-flight checks

Before every live run:

```bash
# Type check + lint + full test suite + decoupling test.
uv run pre-commit run --all-files
uv run mypy src/
uv run pytest -q
```

A green pre-flight run is a precondition for any live invocation; do
not skip these because "it worked yesterday." Phase 6 added a
repo-level CI workflow (`.github/workflows/ci.yml`) that runs exactly
this matrix on every push.
