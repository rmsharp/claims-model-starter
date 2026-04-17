# Tutorial: Running the Model Project Constructor Pipeline

This tutorial walks you through your first end-to-end pipeline run, from generating an intake report to inspecting the scaffolded project. No API keys or credentials are needed -- everything runs locally with fixture data and an in-memory fake repository.

A second tutorial (forthcoming) covers live LLM-backed interviews and real GitLab/GitHub deployments.

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

## Step 1: Create the intake fixture

The intake agent's input is a YAML file containing a scripted interview -- questions and answers that describe the business problem a model should solve. In production, these answers come from a live conversation with a business stakeholder (via the web UI or CLI). For this tutorial, we provide them as a fixture.

Create a file called `my_intake.yaml` in the project root with the following content:

```yaml
schema: intake_fixture/v1
stakeholder_id: stakeholder_claims_001
session_id: intake_subrogation_001
domain: pc_claims
initial_problem: >-
  Subrogation recovery rates have dropped since rolling out a new claims system;
  we want a model that helps adjusters flag recoverable claims and prompts them
  to capture required evidence during intake.

qa_pairs:
  - question: "Can you describe the business problem in your own words?"
    answer: >-
      Since we deployed the new claims system ~14 months ago our subrogation
      recovery rate dropped roughly 20%. That's millions of dollars a year
      we're not recovering from at-fault parties.
  - question: "What do you believe is causing the drop in recovery?"
    answer: >-
      Adjusters aren't capturing the information we need to pursue subrogation:
      police reports, the other party's insurer, clear fault evidence. The new
      UI makes those fields easy to skip and there's no KPI tying adjuster
      performance to subrogation outcomes.
  - question: "What solution have you been considering?"
    answer: >-
      A prompt-based system embedded in the claims workflow that reminds
      adjusters to collect the required evidence, and a scoring model that
      flags claims likely to succeed in subrogation so we can prioritize them.
  - question: "If a model were to help, what would it predict and on what features?"
    answer: >-
      A binary classification: 1 = subrogation succeeded, 0 = did not. Features
      would include completeness of captured info, adjuster experience, claim
      type, time from incident to filing, damage amount, and evidence of fault.
  - question: "What data do we have available for training?"
    answer: >-
      Our claims datawarehouse has records back to 2020 including outcomes.
      We also have adjuster metadata and the structured intake fields from the
      old and new systems.
  - question: "How would you estimate the annual value of success?"
    answer: >-
      Subrogation recovery is roughly $30M/yr. A 10% lift is ~$3M annually
      and I'd guess we could get somewhere between $2M and $4M.
  - question: "Do any adjuster or claimant attributes we'd use count as protected?"
    answer: >-
      No — we deliberately exclude protected attributes. The model uses claim
      features and adjuster tenure only.

draft_after: 7

draft:
  business_problem: >-
    Subrogation recovery dropped ~20% since deployment of a new claims
    system, primarily because adjusters no longer capture evidence required
    to pursue recovery (police reports, third-party insurer, fault evidence).
    There is no adjuster KPI tying performance to subrogation outcomes and
    the new UI deprioritizes the relevant intake fields.
  proposed_solution: >-
    Embed structured prompts in the claims workflow so adjusters capture the
    required evidence during intake, and surface a per-claim subrogation
    probability score so claims likely to recover are prioritized. Success is
    measured on subrogation recovery rate over a 12-month rolling window.
  model_solution:
    target_variable: successful_subrogation
    target_definition: >-
      Binary outcome: 1 if a claim resulted in a non-zero subrogation recovery
      within 18 months of first notice of loss, 0 otherwise.
    candidate_features:
      - information_completeness_score
      - adjuster_tenure_years
      - claim_type
      - time_from_incident_to_filing_days
      - damage_amount_usd
      - fault_evidence_level
    model_type: supervised_classification
    evaluation_metrics:
      - AUC
      - precision_at_top_decile
      - recall
    is_supervised: true
  estimated_value:
    narrative: >-
      A 10% lift on the current ~$30M/year subrogation recovery yields
      approximately $3M annually. The range below brackets conservative and
      optimistic scenarios.
    annual_impact_usd_low: 2000000
    annual_impact_usd_high: 4000000
    confidence: medium
    assumptions:
      - "Current annual subrogation recovery is approximately $30M."
      - "10% recovery lift is conservative given the proposed levers."
      - "Adjuster compliance with prompts reaches 60%+ within 6 months."

governance:
  cycle_time: tactical
  cycle_time_rationale: >-
    Scores are consumed during claim intake (minutes-to-hours) and adjuster
    workflows change on weekly cadence. Operational would imply streaming
    auto-decisioning, which this system is not.
  risk_tier: tier_3_moderate
  risk_tier_rationale: >-
    Advisory recommendation system only; humans make the subrogation
    decision. No direct consumer-facing impact. Moderate financial exposure.
  regulatory_frameworks:
    - SR_11_7
    - NAIC_AIS
  affects_consumers: true
  uses_protected_attributes: false

review_sequence:
  - ACCEPT
```

The fixture has three sections:

- **`qa_pairs`** -- The interview itself: seven question-answer pairs capturing the business problem, proposed solution, available data, estimated value, and governance considerations. This is what a business stakeholder provides.
- **`draft`** -- The structured report the intake agent assembles from the answers. In a live run the LLM writes this; in a fixture run it is provided directly.
- **`governance`** and **`review_sequence`** -- Risk classification and whether the stakeholder accepts the draft on first review.

---

## Step 2: Generate the IntakeReport JSON

Run the intake agent against the fixture to produce the structured JSON report:

```bash
uv run model-intake-agent --fixture my_intake.yaml --output my_intake_report.json
```

This drives the intake agent through the scripted interview and writes the `IntakeReport` to `my_intake_report.json`. You can inspect it:

```bash
cat my_intake_report.json | python -m json.tool | head -20
```

You should see a JSON object with `"status": "COMPLETE"` and structured fields for the business problem, model solution, estimated value, and governance metadata.

---

## Step 3: Run the pipeline

Now run the full pipeline using the intake report you just generated. The script uses a pre-built `DataReport` fixture (since the data agent needs a database connection for a real run) and an in-memory fake repository client.

```bash
uv run python scripts/run_pipeline.py
```

This will:

1. Load the pre-built `IntakeReport` from `tests/fixtures/subrogation_intake.json` (matching what you generated in Step 2)
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
| `--live` | off | Use a real repo host (see Step 5) |

### Try GitHub CI output

```bash
uv run python scripts/run_pipeline.py --host github
```

The generated project will contain `.github/workflows/ci.yml` instead of `.gitlab-ci.yml`.

---

## Step 4: Inspect the checkpoints

Every inter-agent handoff is persisted as a JSON envelope in the checkpoint directory. After a run, you can inspect what each agent produced:

```bash
ls .orchestrator/checkpoints/run_*/
```

View the intake report that was passed to the data stage:

```bash
cat .orchestrator/checkpoints/run_*/IntakeReport.json | python -m json.tool | head -30
```

View the final project result:

```bash
cat .orchestrator/checkpoints/run_*/RepoProjectResult.result.json | python -m json.tool
```

The checkpoint layout tells you exactly how far a run got:

| Files present | Meaning |
|---|---|
| `IntakeReport.json` only | Failed at intake |
| `+ DataRequest.json + DataReport.json` | Failed at data |
| `+ RepoTarget.json + RepoProjectResult.result.json` | Reached website (check `status` for COMPLETE vs FAILED) |

---

## Step 5: Live run against a real repo host

When you are ready to create an actual repository project, set up credentials and use the `--live` flag.

### 5a: Set up environment variables

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

### 5b: Run with --live

```bash
uv run python scripts/run_pipeline.py --live --host gitlab
```

This will create a real GitLab project at `https://gitlab.com/<namespace>/subrogation_pilot` (or a suffixed name if the project already exists) containing the full model website scaffold.

For GitHub:

```bash
uv run python scripts/run_pipeline.py --live --host github
```

### 5c: Customize the target

Set the `MPC_NAMESPACE` environment variable to control where the project is created. **`MPC_NAMESPACE` must be a path, not a URL** — the GitLab and GitHub adapters look up the group/org by path, so pasting the full URL surfaces as an unhelpful `404`. The orchestrator rejects URL-prefixed values at config-load time:

```bash
# GitLab: top-level group path
export MPC_NAMESPACE="rmsharp-modelpilot"

# GitLab: nested group path
export MPC_NAMESPACE="data-science/model-drafts"

# GitHub: org or personal account
export MPC_NAMESPACE="my-github-org"
```

If you accidentally paste the URL form, the script fails fast before any agent runs:

```
$ MPC_NAMESPACE=https://gitlab.com/rmsharp-modelpilot uv run python scripts/run_pipeline.py --live --host gitlab
ConfigError: MPC_NAMESPACE must be a group path, not a URL; got 'https://gitlab.com/rmsharp-modelpilot'.
Use the path only, e.g. 'rmsharp-modelpilot' instead of 'https://gitlab.com/rmsharp-modelpilot'.
```

For self-hosted GitLab or GitHub Enterprise, set the host URL:

```bash
export MPC_HOST_URL="https://gitlab.internal.company.com"
# or
export MPC_HOST_URL="https://github.mycompany.com/api/v3"
```

---

## Step 6: Real LLM-backed run (Scope B-1)

Steps 1–5 run the full pipeline but use fixture data for the intake and data stages — no Claude calls are made. Step 6 graduates the **data stage** to a real Anthropic-backed data agent while keeping the intake on the fixture. This proves that Claude can actually write SQL for your subrogation request and feed a `DataReport` the website stage can consume.

> **Prerequisite:** `ANTHROPIC_API_KEY` must be set (see §5a). The fixture intake `tests/fixtures/subrogation_intake.json` is still used, so no intake interview is required.

### 6a: Run with `--llm data`

```bash
uv run python scripts/run_pipeline.py \
    --live --host gitlab --llm data \
    --model claude-opus-4-7 \
    --run-id run_b1_$(date +%Y%m%d_%H%M%S)
```

What changes vs. `--live` alone:

- The data runner is now `DataAgent(AnthropicLLMClient(model=...)).run`, not a lambda serving the fixture `sample_datareport.json`.
- Claude generates primary queries, quality checks, a summary, and one datasheet per primary query.
- Cost: ~$0.10–$0.50 per run depending on model (see §6c).
- Runtime: adds 30–90 s vs. the fake run.

The intake stage is unchanged from Step 5 — fixture-driven. To graduate the intake to a real LLM as well, see §6e (`--llm both`).

### 6b: Verify the data side actually ran against the API

Read the `DataReport.json` envelope and confirm the SQL differs from the fixture:

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

The fixture's first query opens with `SELECT claim_id, ...`; a live Claude run produces model-generated SQL that varies by prompt and model. If your preview looks identical to the fixture, something is wrong — rerun with a fresh `--run-id` to rule out checkpoint staleness.

### 6c: Model selection

Override the default with `--model`:

| Model ID | Strength | Cost (relative) |
|---|---|---|
| `claude-opus-4-7` (default) | highest quality; best for first-impression pilot runs | 5× |
| `claude-sonnet-4-6` | fast, cost-effective; fine for iterating | 1× |
| `claude-haiku-4-5-20251001` | cheapest, fastest; may miss subtle semantics | 0.2× |

For production, tune by running each model on a representative request and inspecting the generated SQL. For the first pilot run, `claude-opus-4-7` removes "was it the model?" as a confounding variable when judging output quality.

### 6d: Optional: connect a read-only database

By default `--db-url` is omitted and the data agent **generates** quality checks but does not **execute** them. To execute:

```bash
uv run python scripts/run_pipeline.py \
    --live --host gitlab --llm data \
    --db-url sqlite:///path/to/readonly.db \
    --run-id run_b1_db_$(date +%s)
```

The URL follows SQLAlchemy syntax (`postgresql://user:pass@host/db`, `sqlite:///path`, etc.). When connected, the `DataReport.confirmed_expectations` field will be populated based on real query results instead of the standard "database unreachable" line. Scope B-1 deliberately defaults to disconnected — the pilot's goal is to prove Claude's query generation, not debug SQL connectivity at the same time.

### 6e: Scripted-answers intake (`--llm both`, Scope B-2)

`--llm both` drives a real Claude-backed intake interview with answers pulled from a YAML fixture. Claude generates the questions and decides when it has enough information to draft; the fixture supplies the stakeholder's answers verbatim.

```bash
uv run python scripts/run_pipeline.py \
    --live --host gitlab --llm both \
    --model claude-opus-4-7 \
    --intake-fixture tests/fixtures/subrogation_b2.yaml \
    --run-id run_b2_$(date +%Y%m%d_%H%M%S)
```

How it differs from `--llm data`:

- The intake runner is `IntakeAgent(AnthropicLLMClient(model=...)).run_scripted(...)`. Claude asks its own questions, decides when to flip `believe_enough_info`, drafts the four required sections, and classifies governance.
- The fixture's `draft_after` field is a **no-op** in this mode — only the LLM decides when to stop interviewing. The fixture just supplies answers. Provide at least as many `qa_pairs` as `MAX_QUESTIONS` (see `src/model_project_constructor/agents/intake/state.py:57`) to guarantee the graph terminates.
- `--model` applies to **both** stages. Mixed-model runs (e.g. haiku for intake, opus for data) are not supported.
- Cost: ~$0.15–$0.75 per run (intake ~5–12 Claude calls + data as before).
- Runtime: 60–90 s for intake + 2–5 min for data.

**Failure behavior.** If the fixture runs out of answers before Claude is satisfied, or if Claude raises (rate limit, bad JSON, network), the inline `_draft_incomplete_from_exception` adapter converts the error into a `DRAFT_INCOMPLETE` `IntakeReport` so the pipeline halts with `PipelineResult.status == "FAILED_AT_INTAKE"` rather than crashing. Inspect `.orchestrator/checkpoints/<run_id>/IntakeReport.json` to see the error code in `missing_fields[0]`.

**Verify the intake side ran.** The intake envelope's `business_problem` + `proposed_solution` prose will differ from `tests/fixtures/subrogation_intake.json`, and `questions_asked` will be between 1 and `MAX_QUESTIONS` for a real interview (the DRAFT_INCOMPLETE stub emitted by the adapter reports `questions_asked: 0`).

---

## Step 7: Using the orchestrator programmatically

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
| `analysis/` | Quarto notebooks: business understanding, data, EDA, feature engineering, initial models, implementation plan, extensions |
| `data/` | Data documentation and datasheets |
| `queries/` | SQL queries (primary + quality checks) |
| `reports/` | Intake and data reports in JSON and Markdown |
| `src/` | Initial model build scaffolding (data loading, features, models, evaluation) |
| `tests/` | Test stubs for each source module |
| `governance/` | Governance artifacts (proportional to risk tier): model card, deployment gates, monitoring plan, regulatory compliance |

The project is a **draft scaffold** for a data science team to refine -- it contains reasonable defaults and marks areas that need human judgment.
