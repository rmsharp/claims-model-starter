# Getting Started

## Prerequisites

- Python 3.11 or later
- [uv](https://docs.astral.sh/uv/) package manager
- Git

For live runs (optional):
- An Anthropic API key (`ANTHROPIC_API_KEY`) -- or one of two alternative backends. **AWS Bedrock** (`--provider bedrock`, or `INTAKE_LLM_PROVIDER=bedrock` for the intake web UI) needs AWS credentials resolvable from the standard credential chain (IAM role, SSO login, or profile) plus a region (`AWS_REGION`); it has no single API-key env var. **The OpenCode CLI** (`--provider opencode`) needs the `opencode` binary on `PATH` (`npm i -g opencode-ai`), an explicitly chosen model -- it pins no default, so pass `--model <provider>/<model>` or configure one in your own `opencode.json` -- and whatever credential that tool itself is set up to use; this project reads none. Neither alternative is validated here: `bedrock` has **never been exercised against a live endpoint**, and `opencode` runs but its **output quality is unmeasured**. Every measured result in this project is `anthropic`-only, so verify either in your own environment before depending on it.
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

You should see 900+ tests pass with ~97% coverage.

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
ls .orchestrator/checkpoints/<run_id>/
```

where `<run_id>` is the run identifier shown in the pipeline output (or passed via `--run-id`). For example:

```bash
ls .orchestrator/checkpoints/run_a1b2c3d4/
```

Each checkpoint file is a JSON envelope containing the handoff between agents. The final `RepoProjectResult.result.json` lists every file the website agent would have committed.

## Live run (with API keys)

The pipeline has two independent dimensions: where the generated repository is pushed (fake vs. real host) and which LLM to use (fixture data vs. real API calls). By default, only the website stage's target is configurable; the intake and data agents use fixture data.

### Live repository host

```bash
cp .env.example .env
# Edit .env with your keys
uv run python scripts/run_pipeline.py --live --host github
```

This pushes the generated project to a real GitHub/GitLab host, but the Intake and Data agents still use fixture data (no Anthropic API cost). You still need `GITLAB_TOKEN` or `GITHUB_TOKEN` in `.env`.

### Real LLM calls (Intake + Data agents)

To run the Intake and Data agents against the real Anthropic API, add `--llm=both` (or `--llm=data` for just the Data agent) and supply `--intake-fixture` for the interview answers:

```bash
uv run python scripts/run_pipeline.py --live --host github --llm both --intake-fixture tests/fixtures/subrogation.yaml
```

This requires `ANTHROPIC_API_KEY` in `.env` in addition to the repo host token. See the script's help (`uv run python scripts/run_pipeline.py --help`) for all LLM mode options and the `--provider` flag to swap the LLM backend (e.g. `--provider bedrock`, which authenticates from the AWS credential chain instead of `ANTHROPIC_API_KEY`).

See [Monitoring and Operations](Monitoring-and-Operations) for environment variable details.

## What's next

- [Pipeline Overview](Pipeline-Overview) -- Understand the agent flow
- [Generated Project Structure](Generated-Project-Structure) -- See what gets created
- `docs/tutorial.md` -- Full 6-step walkthrough with inline fixture content
