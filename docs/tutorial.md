# Tutorial: Running the Model Project Constructor Pipeline

This tutorial walks you through your first end-to-end pipeline run, from a zero-credential dry run to a live GitLab or GitHub deployment.

---

## What this tool does

The Model Project Constructor is a multi-agent pipeline that takes a business model idea and turns it into a governance-scaffolded repository project. The pipeline has three stages:

1. **Intake Agent** -- Conducts a guided interview with a business stakeholder to capture the business problem, proposed solution, model solution, and estimated value. Produces an `IntakeReport`.

2. **Data Agent** -- Takes the intake report and generates SQL queries to collect relevant data, writes quality-check queries, and confirms expectations about the data. Produces a `DataReport`.

3. **Website Agent** -- Takes both reports and scaffolds a repository project (GitLab or GitHub) containing a draft model website with business understanding, implementation plans, data documentation, and initial model build sections. Produces a `RepoProjectResult`.

The orchestrator (`run_pipeline`) drives the three agents in sequence, persisting inter-agent handoffs as checkpoint envelopes so a failed run can be inspected and recovered.

---

## Prerequisites

### Install the project

```bash
git clone <repo-url> model_project_constructor
cd model_project_constructor
uv sync --extra agents --extra ui --extra dev
```

The `agents` extra installs LangGraph, Anthropic SDK, GitLab/GitHub client libraries, and Typer (CLI). The `ui` extra installs FastAPI and related dependencies for the intake web UI. The `dev` extra adds pytest, mypy, and ruff.

### Verify the install

```bash
uv run pytest -q
```

You should see 422+ tests pass with 97%+ coverage.

---

## Step 1: Dry run with fixture data (no credentials needed)

The fastest way to see the full pipeline in action is to run it with pre-built fixture data and a fake repository client. No API keys, no tokens, no network access required.

### Run the script

```bash
uv run python scripts/run_pipeline.py
```

This will:

1. Load a pre-built `IntakeReport` (subrogation recovery model for a P&C claims organization) from `tests/fixtures/subrogation_intake.json`
2. Load a pre-built `DataReport` (1.28M-row training set with quality checks) from `tests/fixtures/sample_datareport.json`
3. Wire up a `WebsiteAgent` backed by an in-memory `FakeRepoClient`
4. Run the full Intake -> Data -> Website pipeline through the orchestrator
5. Print the result, metrics, checkpoint files, and generated project files

### What you should see

```
============================================================
  Model Project Constructor -- End-to-End Pipeline Run
  Mode: FAKE (dry run)  |  Host: gitlab  |  Run ID: run_a1b2c3d4
============================================================

[1/5] Loading fixture data...
      Intake: successful_subrogation (supervised_classification)
      Data:   1 queries, 2 confirmed expectations
[2/5] Building pipeline config...
      Target: data-science/model-drafts on https://gitlab.com
      Checkpoints: .orchestrator/checkpoints
[3/5] Wiring runners...
      Runners ready.
[4/5] Running pipeline...

[5/5] Pipeline complete.

============================================================
  RESULT
============================================================
  Status:  COMPLETE
  Project: https://fake.host.test/data-science/model-drafts/subrogation-pilot

  Metrics:
    Total runs:  1
    Status dist: {'COMPLETE': 1}
    intake: 0ms avg (1 call(s))
    data: 0ms avg (1 call(s))
    website: 4ms avg (1 call(s))

  Checkpoints (.orchestrator/checkpoints/run_a1b2c3d4):
    DataReport.json (5,507 bytes)
    DataRequest.json (1,183 bytes)
    IntakeReport.json (3,123 bytes)
    RepoProjectResult.result.json (3,153 bytes)
    RepoTarget.json (485 bytes)

  Generated project: https://fake.host.test/data-science/model-drafts/subrogation-pilot
  Files (38):
    .gitignore
    .gitlab-ci.yml
    README.md
    analysis/01_business_understanding.qmd
    ...
    src/subrogation_pilot/models.py
    tests/test_models.py
```

### Command-line options

| Option | Default | Description |
|--------|---------|-------------|
| `--run-id ID` | Auto-generated | Unique identifier for this run |
| `--host gitlab\|github` | `gitlab` | Target host platform |
| `--checkpoint-dir PATH` | `.orchestrator/checkpoints` | Where checkpoint envelopes are written |
| `--live` | off | Use a real repo host (see Step 3) |

### Try GitHub CI output

```bash
uv run python scripts/run_pipeline.py --host github
```

The generated project will contain `.github/workflows/ci.yml` instead of `.gitlab-ci.yml`.

---

## Step 2: Inspect the checkpoints

Every inter-agent handoff is persisted as a JSON envelope in the checkpoint directory. After a run, you can inspect what each agent produced:

```bash
ls .orchestrator/checkpoints/run_*/
```

Each file is a `HandoffEnvelope` (or a `.result.json` for the terminal artifact):

```bash
# View the intake report that was passed to the data stage
cat .orchestrator/checkpoints/run_*/IntakeReport.json | python -m json.tool | head -30

# View the final project result
cat .orchestrator/checkpoints/run_*/RepoProjectResult.result.json | python -m json.tool
```

The checkpoint layout tells you exactly how far a run got:

| Files present | Meaning |
|---|---|
| `IntakeReport.json` only | Failed at intake |
| `+ DataRequest.json + DataReport.json` | Failed at data |
| `+ RepoTarget.json + RepoProjectResult.result.json` | Reached website (check `status` for COMPLETE vs FAILED) |

---

## Step 3: Live run against a real repo host

When you are ready to create an actual repository project, set up credentials and use the `--live` flag.

### 3a: Set up environment variables

Copy the template and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env`:

```bash
# For GitLab:
MPC_HOST=gitlab
GITLAB_TOKEN=glpat-xxxxxxxxxxxxxxxxxxxx

# Or for GitHub:
# MPC_HOST=github
# GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# For real LLM-backed agents (not needed for fixture-based runs):
# ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Load the environment (choose one method):

```bash
# Option A: direnv (if you use it)
echo "dotenv" > .envrc && direnv allow

# Option B: manual export
export $(grep -v '^#' .env | xargs)

# Option C: source a wrapper
source <(grep -v '^#' .env | sed 's/^/export /')
```

### 3b: Run with --live

```bash
uv run python scripts/run_pipeline.py --live --host gitlab
```

This will create a real GitLab project at `https://gitlab.com/<namespace>/subrogation_pilot` (or a suffixed name if the project already exists) containing the full model website scaffold.

For GitHub:

```bash
uv run python scripts/run_pipeline.py --live --host github
```

### 3c: Customize the target

Set the `MPC_NAMESPACE` environment variable to control where the project is created:

```bash
# GitLab: nested group path
export MPC_NAMESPACE="data-science/model-drafts"

# GitHub: org or personal account
export MPC_NAMESPACE="my-github-org"
```

For self-hosted GitLab or GitHub Enterprise, set the host URL:

```bash
export MPC_HOST_URL="https://gitlab.internal.company.com"
# or
export MPC_HOST_URL="https://github.mycompany.com/api/v3"
```

---

## Step 4: Run individual agents

Each agent can also be run standalone. This is useful for testing or when you want to produce intake/data reports with a real LLM before feeding them into the pipeline.

### Intake Agent (with fixture)

```bash
uv run model-intake-agent --fixture tests/fixtures/subrogation.yaml \
    --output my_intake_report.json
```

This drives the intake interview with scripted answers from the fixture file and writes the `IntakeReport` to `my_intake_report.json`.

### Intake Agent (web UI)

```bash
export ANTHROPIC_API_KEY=sk-ant-...
uv run uvicorn model_project_constructor.ui.intake.app:app --port 8000
```

Then open `http://localhost:8000` to conduct a live interview via the web UI.

### Data Agent

```bash
uv run python -m model_project_constructor_data_agent run \
    --request my_data_request.json \
    --output my_data_report.json \
    --fake-llm
```

Use `--fake-llm` for a dry run without Anthropic credentials, or omit it for real LLM-generated queries.

### Website Agent

```bash
uv run python -m model_project_constructor.agents.website \
    --intake my_intake_report.json \
    --data my_data_report.json \
    --fake
```

Use `--fake` for an in-memory dry run. For a live host:

```bash
uv run python -m model_project_constructor.agents.website \
    --intake my_intake_report.json \
    --data my_data_report.json \
    --host gitlab \
    --host-url https://gitlab.com \
    --namespace data-science/model-drafts \
    --private-token "$GITLAB_TOKEN"
```

---

## Step 5: Using the orchestrator programmatically

For integration into larger systems, use the `run_pipeline` function directly:

```python
from pathlib import Path

from model_project_constructor.agents.website.agent import WebsiteAgent
from model_project_constructor.agents.website.fake_client import FakeRepoClient
from model_project_constructor.orchestrator import (
    MetricsRegistry,
    PipelineConfig,
    make_logged_runner,
    make_measured_runner,
    run_pipeline,
)
from model_project_constructor.schemas.v1.data import DataReport
from model_project_constructor.schemas.v1.intake import IntakeReport
from model_project_constructor.schemas.v1.repo import RepoTarget

# Load your reports (from files, LLM agents, or any other source)
intake = IntakeReport.model_validate_json(Path("intake.json").read_text())
data = DataReport.model_validate_json(Path("data.json").read_text())

# Configure the run
config = PipelineConfig(
    run_id="my_run_001",
    repo_target=RepoTarget(
        host_url="https://gitlab.com",
        namespace="data-science/model-drafts",
        project_name_hint="my_model_project",
        visibility="private",
    ),
    checkpoint_dir=Path(".orchestrator/checkpoints"),
)

# Build a website runner (fake or real)
client = FakeRepoClient()
agent = WebsiteAgent(client, ci_platform="gitlab")

# Optional: add observability
metrics = MetricsRegistry()

result = run_pipeline(
    config,
    intake_runner=lambda: intake,
    data_runner=lambda _req: data,
    website_runner=make_logged_runner(
        make_measured_runner(agent.run, agent_name="website", registry=metrics),
        agent_name="website",
        run_id=config.run_id,
        correlation_id=config.correlation_id,
    ),
)

print(f"Status: {result.status}")
if result.project_url:
    print(f"Project: {result.project_url}")
```

---

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| `ConfigError: GITLAB_TOKEN is required` | Missing credentials in `--live` mode | Set `GITLAB_TOKEN` or `GITHUB_TOKEN` in your environment |
| `ConfigError: ANTHROPIC_API_KEY is required` | Agent runner needs LLM access | Set `ANTHROPIC_API_KEY` for real LLM-backed runs |
| `ModuleNotFoundError: langgraph` | Missing `agents` extra | Run `uv sync --extra agents` |
| Pipeline halts at `FAILED_AT_INTAKE` | Intake report has `DRAFT_INCOMPLETE` status | Check the intake fixture or re-run the intake interview |
| Pipeline halts at `FAILED_AT_DATA` | Data report has non-COMPLETE status | Check data agent logs or the `DataReport.status` field |
| Project name conflict on live host | Project already exists in namespace | The website agent auto-suffixes; check the `project_url` in the result |

For detailed failure-mode diagnostics, see `TROUBLESHOOTING.md`.

---

## What the generated project contains

A successful run creates a repository project with:

| File | Purpose |
|------|---------|
| `README.md` | Project overview with business context |
| `.gitlab-ci.yml` or `.github/workflows/ci.yml` | CI pipeline for the model project |
| `docs/business_understanding.md` | Business problem and proposed solution |
| `docs/implementation_plan.md` | Implementation and measurement plan |
| `data/README.md` | Data documentation (queries, validation, EDA) |
| `src/` | Initial model build scaffolding |
| `governance/` | Governance artifacts (proportional to risk tier) |

The project is a **draft scaffold** for a data science team to refine -- it contains reasonable defaults and marks areas that need human judgment.
