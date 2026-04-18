# Getting Started

## Prerequisites

- Python 3.11 or later
- [uv](https://docs.astral.sh/uv/) package manager
- Git

For live runs (optional):
- An Anthropic API key (`ANTHROPIC_API_KEY`)
- A GitLab personal access token with `api` scope (`GITLAB_TOKEN`), or
- A GitHub PAT with `repo` scope (`GITHUB_TOKEN`)

## Installation

```bash
git clone <repo-url> model_project_constructor
cd model_project_constructor
uv sync --extra agents --extra ui --extra dev
```

| Extra | What it installs |
|-------|-----------------|
| `agents` | LangGraph, Anthropic SDK, GitLab/GitHub client libraries, Typer CLI |
| `ui` | FastAPI, Uvicorn, SSE-Starlette (intake web UI) |
| `dev` | pytest, mypy, ruff (testing and code quality) |

## Verify the install

```bash
uv run pytest -q
```

You should see 440+ tests pass with ~97% coverage.

## First dry run (no API keys needed)

### 1. Create an intake fixture

Create `my_intake.yaml` in the project root with a scripted interview. See `docs/tutorial.md` for the full fixture content. The fixture describes a business problem, proposed solution, model solution (target variable, features, model type), estimated value, and governance metadata.

### 2. Generate an IntakeReport from the fixture

```bash
uv run model-intake-agent --fixture my_intake.yaml --output my_intake_report.json
```

### 3. Run the pipeline

```bash
uv run python scripts/run_pipeline.py --host gitlab
```

This runs all three agents in sequence using fixture data and a fake repository client. No network calls are made.

### 4. Inspect the output

```bash
ls .orchestrator/checkpoints/
```

Each checkpoint file is a JSON envelope containing the handoff between agents. The final `RepoProjectResult.result.json` lists every file the website agent would have committed.

## Live run (with API keys)

```bash
cp .env.example .env
# Edit .env with your keys
uv run python scripts/run_pipeline.py --live --host github
```

See [Monitoring and Operations](Monitoring-and-Operations) for environment variable details.

## What's next

- [Pipeline Overview](Pipeline-Overview) -- Understand the agent flow
- [Generated Project Structure](Generated-Project-Structure) -- See what gets created
- `docs/tutorial.md` -- Full 6-step walkthrough with inline fixture content
