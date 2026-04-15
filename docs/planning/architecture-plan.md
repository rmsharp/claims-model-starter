# Architecture Plan: Model Project Constructor

**Status:** Draft v1.0
**Date:** 2026-04-14
**Session:** 2
**Predecessor:** `docs/planning/architecture-approaches.md` (Session 1)

---

## 1. Context

### Problem

A claims organization within a P&C insurance company needs a repeatable way to turn a business stakeholder's rough model idea into a governance-ready GitLab project that a data science team can pick up and refine. Today this work is ad hoc: stakeholders describe a problem, analysts hand-write queries, data scientists start from scratch, and governance documentation is bolted on at the end.

The Model Project Constructor automates Steps 2–5 of a 6-step pipeline (see `initial_purpose.txt`):

1. Business has an idea (human)
2. **Intake Agent** — guided interview; produces `IntakeReport`
3. **Data Agent** — query generation + quality checks; produces `DataReport`
4. **Website Agent** — draft model website; scaffolds GitLab project
5. **Website Agent (continued)** — delivers GitLab project with governance scaffolding
6. Data science team refines the draft (human)

### Hard Constraints

| # | Constraint | Source |
|---|-----------|--------|
| C1 | Each agent produces a **structured report** (not free-form text), parseable by the next agent | `CLAUDE.md` agent design principles |
| C2 | Handoffs are **explicit**; the receiving agent needs nothing beyond the handoff payload | `CLAUDE.md` |
| C3 | Intake agent asks **one question at a time**, max 10 questions | `initial_purpose.txt:20` |
| C4 | Data Agent must be **reusable as a standalone query tool** for analysts | `initial_purpose.txt:84-87` |
| C5 | Website Agent output is a **draft**, not a finished product | `CLAUDE.md` agent design principles |
| C6 | Code that ends up in the delivered repo must eventually live in **unit-tested Python or R functions**, not inline notebook cells | User directive (2026-04-10) |
| C7 | Governance artifacts must be **proportional to risk tier + cycle time**, first-line ownership of evidence | Model Governance framework (SR 11-7, EU AI Act, ASOP 56) |
| C8 | All generated model work must be **inventory-registered at inception** | Model Governance framework |

### What This Plan Covers

- Agent boundaries, responsibilities, and failure modes (§4)
- Pydantic schemas with field-level detail for every handoff (§5)
- Handoff envelope protocol with versioning (§6)
- Data Agent standalone reuse interface (§7)
- Governance integration — what is captured at intake, what is scaffolded in the generated repo (§8)
- Technology stack with specific libraries and models (§9)
- LangGraph orchestration pattern (§10)
- Generated GitLab repo structure (§11)
- Error handling strategy (§12)
- Failure mode analysis per agent (§13)
- Implementation phases with session boundaries and completion criteria (§14)

### What This Plan Does NOT Cover (Explicit Scope Boundary)

- Step 1 (business idea generation) — human-driven, out of scope
- Step 6 (data science team refinement) — human-driven, out of scope
- Production deployment/operations of generated models — the pipeline generates a draft repo; operating the resulting models is the data science team's responsibility
- Second-line/third-line review automation — governance review is a human process; the pipeline produces evidence, not approvals
- Legacy Excel/Earnix extraction — that tooling exists in the `model_governance` project for existing models; this pipeline creates new models

---

## 2. Decision Summary

Chosen approaches from `architecture-approaches.md`:

| # | Critical Feature | Chosen Approach | Rationale |
|---|------------------|-----------------|-----------|
| 1 | Pipeline Orchestration | **Sequential Script** | Prove the 3-agent flow end-to-end with minimal infrastructure; upgrade to state machine later without changing agent interfaces |
| 2 | Tech Stack & LLM | **LangGraph + Claude** (Sonnet for Intake, Opus for Website) | Framework-provided checkpointing and human-in-the-loop for the long-lived interview; same Claude family already in use for development |
| 3 | Schema Design | **Pydantic with Envelope Pattern** | All-Python project; fast iteration; JSON Schema export available if non-Python consumers arise |
| 4 | EDA & Model Building | **Code Generation Only** (Quarto + tested Python/R functions) | No LLM-generated code executes against corporate databases; data science team renders the Quarto documents; matches C6 |

**Additional decision (not in approaches doc): Governance integration is a first-class concern.** The intake captures cycle-time classification and risk tier; the generated repo is scaffolded with governance artifacts proportional to those dimensions.

---

## 3. High-Level Architecture

```
                                   ┌────────────────────┐
  Stakeholder ──(web UI)──────────▶│   Intake Agent     │
                                   │   (Claude Sonnet)  │
                                   └─────────┬──────────┘
                                             │
                                             │ IntakeReport
                                             │ (HandoffEnvelope)
                                             ▼
                                   ┌────────────────────┐
                                   │   Data Agent       │
      Analyst ──(standalone)──────▶│   (Claude Sonnet)  │
       (DataRequest only)          └─────────┬──────────┘
                                             │
                                             │ DataReport
                                             │ (HandoffEnvelope)
                                             ▼
                                   ┌────────────────────┐
                                   │   Website Agent    │
                                   │   (Claude Opus)    │
                                   └─────────┬──────────┘
                                             │
                                             │ GitLabProject
                                             ▼
                                        GitLab Instance
                                   (governance-scaffolded repo)
```

**Orchestrator responsibilities:**
- Sequentially invoke the three agents
- Persist each handoff to disk (`runs/<run_id>/intake.json`, `data.json`, `website.json`) as checkpoints
- Construct the `HandoffEnvelope` wrapper and validate the payload against the target agent's expected schema
- Run the **adapter function** that maps `IntakeReport` → `DataRequest` (see §7)
- Surface errors from any agent to the operator and mark the run `FAILED` with a specific phase

**Key architectural property preserved:** Agents never import each other. All inter-agent contracts go through the `schemas/` package. This is what makes the orchestration choice (Sequential Script → State Machine → Event-Driven) upgradeable without touching agent code.

---

## 4. Agent Boundaries

### 4.1 Intake Agent

**Responsibility:** Conduct a guided interview with a business stakeholder and produce an `IntakeReport`.

**Inputs:**
- `InterviewSessionConfig` — user ID, session ID, initial problem statement (optional one-liner), domain hint (default: `"pc_claims"`)

**Outputs:**
- `IntakeReport` (validated Pydantic model, see §5.1)

**Behavior contract:**
- Asks one question at a time
- Maximum 10 questions (hard cap)
- Drives toward the four required sections: Business Problem, Proposed Solution, Model Solution, Estimated Value
- Additionally drives toward **two governance-mandatory sections**: Cycle-Time Classification and Risk Tier Assessment (see §8)
- Presents the draft back to the stakeholder for review before finalizing
- Terminates on: stakeholder confirmation, hard 10-question cap with incomplete state (marks report `status=DRAFT_INCOMPLETE`), or explicit abort

**Failure modes:**

| Mode | Trigger | Recovery |
|------|---------|----------|
| Incomplete interview | Stakeholder abandons mid-session | Checkpoint persisted; resume via session ID |
| Cap hit with gaps | 10 questions used, required fields still missing | Return `IntakeReport` with `status=DRAFT_INCOMPLETE` and `missing_fields` populated; orchestrator halts |
| Stakeholder rejects draft | Stakeholder says the draft doesn't match their understanding | Up to 3 revision cycles allowed; after that, mark incomplete |
| LLM refusal / safety block | Claude declines to produce output | Log; surface to operator; halt run |

---

### 4.2 Data Agent

**Responsibility:** Generate SQL queries to collect data for the model described in the intake, plus quality-check queries, plus a data summary report. Also usable **standalone** by analysts with no intake context.

**Inputs (pipeline mode):**
- `DataRequest` — produced by the orchestrator's adapter from `IntakeReport`

**Inputs (standalone mode):**
- `DataRequest` — constructed directly by an analyst (web form, CLI, or Python call)

**Both modes produce the same output.** The agent has a single entry point, `run(request: DataRequest) -> DataReport`. It has **no dependency on `IntakeReport`**.

**Outputs:**
- `DataReport` (validated Pydantic model, see §5.2)

**Behavior contract:**
- Generates one or more primary data-collection SQL queries
- Generates quality-check queries for each primary query (null rates, distribution, ranges, row counts, join integrity)
- Attempts to **execute** quality-check queries against the live database (read-only) to confirm expectations
- Primary queries are **not executed** — they are handed off as artifacts
- Produces a natural-language summary of findings (confirmed expectations, unconfirmed expectations, data-quality concerns)
- Produces a **datasheet** (per Gebru 2021) for each primary query's result set: provenance, composition, limitations, known biases

**Failure modes:**

| Mode | Trigger | Recovery |
|------|---------|----------|
| Database unreachable | Connection fails | Skip execution; return `DataReport` with `qc_status=NOT_EXECUTED` and queries only |
| QC query errors | Syntax or permission error on QC query | Log; mark that specific QC as `ERROR`; proceed with others |
| Primary query invalid SQL | `sqlparse` parse fails | Retry once with the error message in prompt; if still invalid, return with `primary_query_status=INVALID` |
| Ambiguous request | `DataRequest` is missing target or granularity | Return `DataReport` with `status=INCOMPLETE_REQUEST` and list missing fields; orchestrator halts |

---

### 4.3 Website Agent

**Responsibility:** Produce a draft model website as a repository-host project (GitLab today, GitHub via Phase C of the abstraction plan). The website scaffolds the four required sections plus governance artifacts. Code is generated as Quarto documents that call functions in separate, unit-tested modules.

> **Naming note (Phase A of `github-gitlab-abstraction-plan.md`):** the Website Agent's adapter boundary is now neutral. The `RepoClient` Protocol, `RepoTarget` schema, and `RepoProjectResult` schema replace the Phase-4B `GitLab*` names. `PythonGitLabAdapter` is the concrete GitLab implementation and keeps its name; `PyGithubAdapter` arrives in Phase C.

**Inputs:**
- `IntakeReport`
- `DataReport`
- `RepoTarget` — destination config (`host_url`, `namespace`, project name, visibility)

**Outputs:**
- `RepoProjectResult` — project URL, opaque string `project_id`, commit hash of initial push, list of created files, governance manifest

**Behavior contract:**
- Creates a repository on the configured host via the `RepoClient` adapter (currently `PythonGitLabAdapter` over `python-gitlab`)
- Generates repo contents per the structure in §11
- All analysis code lives in two places:
  - `src/` — Python/R modules with unit-testable functions
  - `analysis/*.qmd` — Quarto documents that import from `src/` and render narratives
- Scaffolds but does **not render** the Quarto documents (consistent with Code Generation Only EDA)
- Scaffolds all governance artifacts proportional to intake-declared risk tier and cycle time (§8)
- Commits initial scaffolding in logical chunks with clear messages (not one giant commit)
- Registers the model in the governance registry (`governance/model_registry.json`)

**Failure modes:**

| Mode | Trigger | Recovery |
|------|---------|----------|
| Repo host API error | Auth failure, rate limit, network | Retry with exponential backoff (3 attempts); surface to operator |
| Repo project name conflict | Name already exists | Append suffix `-v2`, `-v3`, etc.; max 5 attempts |
| Incomplete inputs | `IntakeReport` or `DataReport` has `status != COMPLETE` | Halt; orchestrator reports which predecessor failed |
| Quarto scaffold lint errors | Generated `.qmd` has syntax issues | Pass through; mark file `status=DRAFT_NEEDS_REVIEW` in manifest; do not block commit |

---

## 5. Pydantic Schemas

All schemas live in `src/model_project_constructor/schemas/v1/`. Each has a `schema_version` literal field (`"1.0.0"`) and inherits from a shared base that enforces the envelope contract (§6).

### 5.1 `IntakeReport`

```python
from typing import Literal
from pydantic import BaseModel, Field
from datetime import datetime

CycleTime = Literal["strategic", "tactical", "operational", "continuous"]
RiskTier = Literal["tier_1_critical", "tier_2_high", "tier_3_moderate", "tier_4_low"]
ModelType = Literal[
    "supervised_classification", "supervised_regression",
    "unsupervised_clustering", "unsupervised_anomaly",
    "time_series", "reinforcement", "other"
]

class ModelSolution(BaseModel):
    target_variable: str | None      # None if unsupervised
    target_definition: str            # How the target is computed/observed
    candidate_features: list[str]    # Narrative-level, not schema-level
    model_type: ModelType
    evaluation_metrics: list[str]    # e.g., ["AUC", "precision@k"]
    is_supervised: bool

class EstimatedValue(BaseModel):
    narrative: str                   # Prose explanation of the value logic
    annual_impact_usd_low: float | None
    annual_impact_usd_high: float | None
    confidence: Literal["low", "medium", "high"]
    assumptions: list[str]

class GovernanceMetadata(BaseModel):
    cycle_time: CycleTime
    cycle_time_rationale: str
    risk_tier: RiskTier
    risk_tier_rationale: str
    regulatory_frameworks: list[str]  # e.g., ["SR_11_7", "NAIC_AIS", "EU_AI_ACT_ART_9"]
    affects_consumers: bool           # Determines EU AI Act applicability
    uses_protected_attributes: bool   # Determines fairness-testing requirements

class IntakeReport(BaseModel):
    schema_version: Literal["1.0.0"] = "1.0.0"
    status: Literal["COMPLETE", "DRAFT_INCOMPLETE"]
    missing_fields: list[str] = []
    # Four required business sections (from initial_purpose.txt)
    business_problem: str
    proposed_solution: str
    model_solution: ModelSolution
    estimated_value: EstimatedValue
    # Governance sections (added for automated governance scaffolding)
    governance: GovernanceMetadata
    # Metadata
    stakeholder_id: str
    session_id: str
    created_at: datetime
    questions_asked: int               # Track against 10-question cap
    revision_cycles: int = 0           # Track against 3-revision cap
```

**Why these fields:** The four business sections come directly from `initial_purpose.txt:25-44`. The `GovernanceMetadata` block is driven by the governance framework — without it, the generated repo cannot scaffold proportional governance artifacts. `status` and `missing_fields` allow the orchestrator to halt cleanly on incomplete intake.

### 5.2 `DataRequest` (Data Agent input)

```python
class DataGranularity(BaseModel):
    unit: str                          # e.g., "claim", "policy", "customer"
    time_grain: Literal["event", "daily", "weekly", "monthly", "quarterly", "annual"]

class DataRequest(BaseModel):
    schema_version: Literal["1.0.0"] = "1.0.0"
    # Core ask (all required)
    target_description: str            # What we're trying to observe/predict
    target_granularity: DataGranularity
    required_features: list[str]       # Narrative-level
    population_filter: str             # Prose description of the population
    time_range: str                    # e.g., "2022-01-01 to 2024-12-31"
    # Optional context
    database_hint: str | None          # Preferred schema/database if known
    data_quality_concerns: list[str] = []  # Known issues to check for
    # Provenance (distinguishes pipeline vs standalone mode)
    source: Literal["pipeline", "standalone"]
    source_ref: str                    # run_id if pipeline, user identifier if standalone
```

**Critical:** `DataRequest` does not import from `IntakeReport`. This is what decouples the Data Agent for reuse (constraint C4).

### 5.3 `DataReport`

```python
class QualityCheck(BaseModel):
    check_name: str
    check_sql: str
    expectation: str                   # What "passing" looks like in prose
    execution_status: Literal["PASSED", "FAILED", "ERROR", "NOT_EXECUTED"]
    result_summary: str                # Prose summary of result
    raw_result: dict | None = None     # Structured result if available

class PrimaryQuery(BaseModel):
    name: str                          # e.g., "subrogation_training_set"
    sql: str
    purpose: str                       # Prose: what this query returns and why
    expected_row_count_order: Literal["tens", "hundreds", "thousands", "millions"]
    quality_checks: list[QualityCheck]
    datasheet: "Datasheet"             # See below

class Datasheet(BaseModel):
    """Per Gebru 2021 'Datasheets for Datasets'."""
    motivation: str                    # Why does this dataset exist?
    composition: str                   # What does it contain?
    collection_process: str            # How was it collected?
    preprocessing: str                 # What transformations are applied?
    uses: str                          # Intended uses and limitations
    known_biases: list[str]
    maintenance: str                   # Who owns it, update cadence

class DataReport(BaseModel):
    schema_version: Literal["1.0.0"] = "1.0.0"
    status: Literal["COMPLETE", "INCOMPLETE_REQUEST", "EXECUTION_FAILED"]
    request: DataRequest               # Echo the request for traceability
    primary_queries: list[PrimaryQuery]
    summary: str                       # Natural-language summary
    confirmed_expectations: list[str]
    unconfirmed_expectations: list[str]
    data_quality_concerns: list[str]
    created_at: datetime
```

### 5.4 `RepoTarget` and `RepoProjectResult`

> **Post-Phase-A names.** These replace the Phase-4B `GitLabTarget` / `GitLabProjectResult` types. `project_id` widened from `int` to `str` so the same shape fits GitLab (stringified integer) and GitHub (`"owner/name"`). `GovernanceManifest` is unchanged — already neutral.

```python
class RepoTarget(BaseModel):
    schema_version: Literal["1.0.0"] = "1.0.0"
    host_url: str                      # e.g., "https://gitlab.example.com"
    namespace: str                     # e.g., "data-science/model-drafts"
    project_name_hint: str             # Derived from intake if not set
    visibility: Literal["private", "internal", "public"] = "private"

class GovernanceManifest(BaseModel):
    model_registry_entry: dict         # Mirrors governance/model_registry.json
    artifacts_created: list[str]       # Paths of governance files created
    risk_tier: RiskTier
    cycle_time: CycleTime
    regulatory_mapping: dict[str, list[str]]  # framework -> artifacts satisfying it

class RepoProjectResult(BaseModel):
    schema_version: Literal["1.0.0"] = "1.0.0"
    status: Literal["COMPLETE", "PARTIAL", "FAILED"]
    project_url: str
    project_id: str                    # host-opaque: GitLab str(int), GitHub "owner/name"
    initial_commit_sha: str
    files_created: list[str]
    governance_manifest: GovernanceManifest
    failure_reason: str | None = None
```

---

## 6. Handoff Envelope Protocol

### Envelope

Every inter-agent handoff is wrapped in a `HandoffEnvelope`:

```python
class HandoffEnvelope(BaseModel):
    envelope_version: Literal["1.0.0"] = "1.0.0"
    run_id: str                        # Orchestrator-assigned run ID
    source_agent: Literal["intake", "data", "website", "orchestrator"]
    target_agent: Literal["intake", "data", "website"]
    payload_type: str                  # e.g., "IntakeReport", "DataRequest"
    payload_schema_version: str        # e.g., "1.0.0"
    payload: dict                      # Raw payload (validated downstream)
    created_at: datetime
    correlation_id: str                # Same across all envelopes in one run
```

**Validation flow (two-step):**
1. Receiving agent validates the envelope itself
2. Receiving agent looks up `(payload_type, payload_schema_version)` in the **schema registry** and validates `payload` against the matching Pydantic class

### Schema Registry

```python
# src/model_project_constructor/schemas/registry.py
REGISTRY: dict[tuple[str, str], type[BaseModel]] = {
    ("IntakeReport", "1.0.0"): v1.IntakeReport,
    ("DataRequest", "1.0.0"): v1.DataRequest,
    ("DataReport", "1.0.0"): v1.DataReport,
    ("GitLabTarget", "1.0.0"): v1.GitLabTarget,
    ("GitLabProjectResult", "1.0.0"): v1.GitLabProjectResult,
}

def load_payload(envelope: HandoffEnvelope) -> BaseModel:
    cls = REGISTRY[(envelope.payload_type, envelope.payload_schema_version)]
    return cls.model_validate(envelope.payload)
```

### Versioning Rules

- **Minor bump (1.0.0 → 1.1.0):** Adding an optional field. Both versions coexist in the registry.
- **Major bump (1.0.0 → 2.0.0):** Removing or renaming a required field, or changing semantics. Migration function required in `schemas/migrations/`.
- The registry never removes old versions for a minimum of two major releases (prevents breaking in-flight runs mid-upgrade).

### Persistence

Each envelope is persisted to `runs/<run_id>/<source>_to_<target>.json` as a checkpoint. On orchestrator restart, the latest persisted envelope determines where to resume.

---

## 7. Data Agent Reuse Interface

This is the single most constraint-driven piece of the design (constraint C4).

### Principle

**The Data Agent has exactly one public entry point: `run(request: DataRequest) -> DataReport`.** It does not import `IntakeReport`. The adapter that converts `IntakeReport` into `DataRequest` is owned by the **orchestrator**, not by the Data Agent.

### Adapter Function (Orchestrator-Owned)

```python
# src/model_project_constructor/orchestrator/adapters.py
def intake_report_to_data_request(report: IntakeReport, run_id: str) -> DataRequest:
    return DataRequest(
        target_description=report.model_solution.target_definition,
        target_granularity=DataGranularity(
            unit=_infer_unit(report),       # derived from problem/population
            time_grain=_infer_time_grain(report),
        ),
        required_features=report.model_solution.candidate_features,
        population_filter=_derive_population(report.business_problem),
        time_range=_derive_time_range(report.estimated_value),
        source="pipeline",
        source_ref=run_id,
    )
```

The inference helpers (`_infer_unit`, `_infer_time_grain`, etc.) may themselves call an LLM. They are **not** part of the Data Agent's code — they are part of the orchestrator.

### Three Entry Points for the Data Agent

All three construct a `DataRequest` and call `DataAgent.run()`:

1. **Pipeline mode (used by orchestrator):** Orchestrator calls the adapter, then `DataAgent.run()`.
2. **CLI mode (used by analysts):** `model-data-agent run --request request.json` — request file constructed by analyst.
3. **Python API mode (used by analysts in notebooks/scripts):** `from model_project_constructor.agents.data import DataAgent; DataAgent().run(request)`.

The CLI and Python API are packaged as a **separate installable subpackage**: `model-project-constructor-data-agent`. This enforces the decoupling physically — the standalone package cannot import from the orchestrator.

### Test that enforces decoupling

```python
# tests/test_data_agent_decoupling.py
def test_data_agent_does_not_import_intake_report():
    import ast, pathlib
    data_agent_src = pathlib.Path("src/model_project_constructor/agents/data").rglob("*.py")
    for path in data_agent_src:
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                imported = ast.unparse(node)
                assert "IntakeReport" not in imported, f"{path} imports IntakeReport"
                assert "intake_report" not in imported, f"{path} imports intake_report"
```

This test runs in CI and fails the build if anyone introduces a coupling.

---

## 8. Governance Integration

Governance is not a separate agent or a bolt-on — it is woven through intake capture and repo scaffolding.

### 8.1 What Intake Captures

The `GovernanceMetadata` block in `IntakeReport` captures:

| Field | How It's Elicited | Downstream Use |
|-------|-------------------|----------------|
| `cycle_time` | Intake agent asks about update frequency, decision tempo | Determines monitoring cadence in generated repo |
| `risk_tier` | Intake agent asks about impact, reversibility, scope | Determines checklist depth, review requirements |
| `regulatory_frameworks` | Intake agent asks domain-specific questions mapped to frameworks | Determines which regulatory mapping artifacts to scaffold |
| `affects_consumers` | Direct question | Triggers EU AI Act mapping if true |
| `uses_protected_attributes` | Direct question | Triggers fairness-testing scaffolding if true |

The intake agent has a **governance sub-prompt** (separate from the interview prompt) that classifies the first four business sections into these governance fields. The stakeholder reviews the governance classification as part of the draft-review step and can override.

### 8.2 What the Generated Repo Contains

Proportional to `risk_tier` + `cycle_time`, the Website Agent scaffolds:

**Always (every risk tier):**
- `governance/model_registry.json` — registry entry with cycle time, risk tier, owner, created date
- `governance/model_card.md` — per Mitchell 2019
- `governance/change_log.md` — initialized with creation entry
- `data/datasheet_<query_name>.md` — one per primary query, per Gebru 2021
- `.pre-commit-config.yaml` — basic governance hooks (schema validation on registry)
- `.gitlab-ci.yml` — minimal pipeline (lint + unit tests + registry validation)

**Tier 3 (moderate) and above, additionally:**
- `governance/three_pillar_validation.md` — template for conceptual soundness / ongoing monitoring / outcomes analysis
- `governance/ongoing_monitoring.md` — scaffolded with cycle-time-appropriate cadence
- `governance/deployment_gates.md` — checklist of gates for staged rollout

**Tier 2 (high) and above, additionally:**
- `governance/impact_assessment.md` — template for pre-deployment impact review
- `governance/regulatory_mapping.md` — explicit mapping of artifacts to regulatory requirements (SR 11-7, applicable NAIC/EU AI Act articles, ASOP 56)

**Tier 1 (critical), additionally:**
- `governance/lcp_integration.md` — Life Cycle Process review integration pathway
- `governance/audit_log/` — timestamped audit evidence directory scaffolded

**If `uses_protected_attributes=true`, additionally:**
- `analysis/fairness_audit.qmd` — scaffolded bias/fairness testing narrative
- Fairness test stubs in `src/fairness/`

**If `affects_consumers=true` and EU deployment in scope, additionally:**
- `governance/eu_ai_act_compliance.md` — explicit Article 9–15 mapping

### 8.3 Cycle-Time-Driven Monitoring Cadence

The Website Agent writes the monitoring cadence into `governance/ongoing_monitoring.md` based on `cycle_time`:

| Cycle Time | Default Cadence |
|------------|-----------------|
| strategic (multi-year) | Annual review |
| tactical (quarterly-annual) | Quarterly review |
| operational (weekly-monthly) | Monthly monitoring |
| continuous (daily or faster) | Automated continuous monitoring + monthly human review |

### 8.4 What Governance Is NOT Automated

- Second-line review decisions (human)
- Approval signatures (human)
- Outcomes analysis (requires production data, which doesn't exist at pipeline time)
- Backtesting against live data (data science team's responsibility)

The pipeline produces **evidence templates and scaffolds**, not filled-in evidence.

---

## 9. Technology Stack

### 9.1 Core

| Component | Choice | Version | Notes |
|-----------|--------|---------|-------|
| Language | Python | 3.11+ | `StrEnum`, `TypedDict` improvements |
| Package manager | `uv` | latest | Fast, lockfile-based; already standard in the org |
| Schema validation | `pydantic` | 2.x | v2 for performance, `model_validate` API |
| Agent framework | `langgraph` | 0.2.x | State machines with checkpointing |
| LLM SDK | `anthropic` | latest | Direct SDK; LangGraph wraps it |
| SQL parsing | `sqlparse` | latest | Read-only validation of generated SQL |
| DB access | `sqlalchemy` | 2.x | Read-only credential; connection pool |
| GitLab | `python-gitlab` | latest | Project creation, file commits |
| Quarto | `quarto-cli` | 1.5+ | Not a Python dep; required at runtime for rendering (by data science team, not pipeline) |
| CLI | `typer` | latest | Standalone Data Agent CLI |
| Testing | `pytest` + `pytest-asyncio` | latest | Async for LangGraph flows |

### 9.2 LLM Models

| Agent | Model | Rationale |
|-------|-------|-----------|
| Intake Agent | `claude-sonnet-4-6` | Conversational quality, fast turn-taking for interview |
| Data Agent | `claude-sonnet-4-6` | SQL generation + tool use; Opus is overkill for structured output |
| Website Agent | `claude-opus-4-6` | Long-context synthesis of intake + data + governance into a scaffolded repo |

All three models support 200K+ context and native tool use.

### 9.3 Web UI (Intake Agent)

The intake interview requires a web UI accessible at `go/modelintake`:

- **Backend:** FastAPI with Server-Sent Events (SSE) for streaming agent responses
- **Frontend:** Minimal HTML + HTMX (no SPA build toolchain)
- **Session persistence:** SQLite (sessions table)

**Why SSE over WebSocket:** SSE works through most corporate proxies without configuration. WebSocket's operational overhead is not justified here — the interview is half-duplex (stakeholder question → agent response).

**Why HTMX:** Avoids a frontend build pipeline entirely. A single HTML template + HTMX fragments is sufficient for a form-based interview. The data science team can read the template without knowing React.

---

## 10. LangGraph Orchestration Pattern

Although the top-level orchestrator is a Sequential Script, **each agent internally uses LangGraph** for state management and checkpointing. This gives us:

- Checkpoint/resume per agent (the Intake Agent's long-lived interview is the main beneficiary)
- Human-in-the-loop interrupts (stakeholder review of the draft intake report)
- Structured state that survives crashes

### Intake Agent LangGraph

```
  ┌──────────┐       ┌────────────┐       ┌──────────────┐
  │  START   │──────▶│ ASK_NEXT_Q │──────▶│ WAIT_FOR_ANS │
  └──────────┘       └────────────┘       └──────┬───────┘
                          ▲                       │
                          │                       ▼
                     ┌────┴──────┐          ┌──────────┐
                     │  NOT DONE │◀─────────│ EVALUATE │
                     └───────────┘          └────┬─────┘
                                                 │ DONE
                                                 ▼
                                          ┌──────────────┐
                                          │ DRAFT_REPORT │
                                          └──────┬───────┘
                                                 │
                                                 ▼
                                          ┌──────────────┐
                                          │ AWAIT_REVIEW │◀── interrupt
                                          └──────┬───────┘
                                                 │
                                                 ▼
                                          ┌────────────┐
                                          │  FINALIZE  │──▶ END
                                          └────────────┘
```

The `AWAIT_REVIEW` node uses LangGraph's `interrupt` mechanism; the stakeholder's response resumes the graph.

### Data Agent LangGraph

```
  START ─▶ GENERATE_QUERIES ─▶ GENERATE_QC ─▶ EXECUTE_QC ─▶ SUMMARIZE ─▶ DATASHEET ─▶ END
                   │                              │
                   │ SQL invalid                  │ DB down
                   ▼                              ▼
              RETRY_ONCE                     SKIP_EXECUTION
```

### Website Agent LangGraph

```
  START ─▶ CREATE_PROJECT ─▶ SCAFFOLD_BASE ─▶ SCAFFOLD_GOVERNANCE ─▶
           SCAFFOLD_ANALYSIS ─▶ SCAFFOLD_TESTS ─▶ INITIAL_COMMITS ─▶ END
                                                     │
                                                     │ GitLab error
                                                     ▼
                                                 RETRY_BACKOFF
```

Each node is a pure function over state. This makes unit testing straightforward.

---

## 11. Generated Repository Structure

> **Naming note.** The section title previously said "Generated GitLab Repo Structure." Post-Phase-A the Website Agent is host-neutral at the adapter boundary; the CI template filename (`.gitlab-ci.yml`) is still GitLab-specific and stays that way until Phase B of `github-gitlab-abstraction-plan.md` adds `.github/workflows/ci.yml` as a per-host sibling.


```
<project_name>/
├── .gitignore
├── .gitlab-ci.yml                        # minimal pipeline: lint + unit + registry validation
├── .pre-commit-config.yaml               # hooks: pydantic validate, ruff, registry schema
├── README.md                             # generated from IntakeReport business problem
├── pyproject.toml                        # uv-managed; pins Python 3.11+
├── src/
│   ├── <project_slug>/
│   │   ├── __init__.py
│   │   ├── data_loading.py               # functions that execute Data Agent SQL
│   │   ├── features.py                   # feature engineering functions (unit-tested)
│   │   ├── models.py                     # model training functions (unit-tested)
│   │   └── evaluation.py                 # evaluation functions (unit-tested)
│   └── fairness/                         # only if uses_protected_attributes=true
├── analysis/
│   ├── 01_business_understanding.qmd     # narrative from IntakeReport
│   ├── 02_data.qmd                       # narrative from DataReport; calls data_loading
│   ├── 03_eda.qmd                        # scaffolded EDA; calls functions in src/
│   ├── 04_feature_engineering.qmd        # calls features.py
│   ├── 05_initial_models.qmd             # calls models.py, evaluation.py
│   ├── 06_implementation_plan.qmd        # narrative from IntakeReport
│   └── 99_extensions.qmd                 # Website Agent's suggested extensions
├── queries/
│   ├── primary/                          # from DataReport.primary_queries
│   │   └── <query_name>.sql
│   └── quality/                          # from DataReport.primary_queries[*].quality_checks
│       └── <check_name>.sql
├── tests/
│   ├── test_data_loading.py              # smoke tests, schema assertions
│   ├── test_features.py                  # scaffolded unit tests
│   ├── test_models.py                    # scaffolded unit tests
│   └── test_evaluation.py                # scaffolded unit tests
├── governance/
│   ├── model_registry.json               # always
│   ├── model_card.md                     # always
│   ├── change_log.md                     # always
│   ├── three_pillar_validation.md        # tier 3+
│   ├── ongoing_monitoring.md             # tier 3+
│   ├── deployment_gates.md               # tier 3+
│   ├── impact_assessment.md              # tier 2+
│   ├── regulatory_mapping.md             # tier 2+
│   ├── lcp_integration.md                # tier 1
│   ├── eu_ai_act_compliance.md           # if affects_consumers
│   └── audit_log/                        # tier 1
├── data/
│   ├── datasheet_<query_name>.md         # one per primary query
│   └── README.md                         # data dictionary
└── reports/
    ├── intake_report.json                # the IntakeReport
    ├── intake_report.md                  # human-readable rendering
    ├── data_report.json                  # the DataReport
    └── data_report.md                    # human-readable rendering
```

**Why Quarto + `src/` split:** Satisfies constraint C6 — all code that ends up in the repo is callable from unit tests because it lives in `src/`, not inline in a notebook cell. The `.qmd` files are narratives that call the tested functions. This is the upgrade path from the user's rejection of Jupyter notebooks.

**Why reports in both JSON and Markdown:** JSON is the machine contract for future automation; Markdown is what humans read.

---

## 12. Error Handling Strategy

### Per-Agent Contract

Each agent's public `run()` method returns a report whose `status` field indicates success or a specific failure mode. **Agents do not raise exceptions to the orchestrator for expected failures** — they return a report with `status != COMPLETE`. Exceptions are reserved for unexpected programming errors.

### Orchestrator Halt Logic

```python
def run_pipeline(config: PipelineConfig) -> PipelineResult:
    intake = intake_agent.run(config.interview_config)
    _persist(run_id, "intake", intake)
    if intake.status != "COMPLETE":
        return PipelineResult(status="FAILED_AT_INTAKE", last_report=intake)

    data_request = intake_report_to_data_request(intake, run_id)
    data = data_agent.run(data_request)
    _persist(run_id, "data", data)
    if data.status != "COMPLETE":
        return PipelineResult(status="FAILED_AT_DATA", last_report=data)

    project = website_agent.run(intake, data, config.gitlab_target)
    _persist(run_id, "website", project)
    if project.status != "COMPLETE":
        return PipelineResult(status="FAILED_AT_WEBSITE", last_report=project)

    return PipelineResult(status="COMPLETE", project_url=project.project_url)
```

### Retry Policy

- **Agent internal retries** (LangGraph node level): bounded, e.g., 1 retry for invalid SQL, 3 retries with backoff for GitLab API.
- **Orchestrator does not retry agents.** A failed agent halts the run; the operator reviews and re-runs from the last checkpoint.
- **No partial success at the orchestrator level.** Either the pipeline produces a complete GitLab project or it does not. Partial scaffolding is explicitly avoided to prevent confusion about what's real vs. draft.

### Resumption

Every handoff is checkpointed. Re-running with the same `run_id` loads the latest checkpoint and resumes from the next agent. This is the upgrade path to the State Machine orchestrator later.

---

## 13. Failure Mode Analysis

Consolidated across agents:

| Failure | Blast Radius | Detection | Recovery |
|---------|-------------|-----------|----------|
| Intake stakeholder abandons | Single run | Session timeout (2 hours) | Checkpoint preserved; resume via session ID |
| Intake hits 10-question cap incomplete | Single run | Report `status=DRAFT_INCOMPLETE` | Operator reviews; may re-run with a warmer starter prompt |
| Intake draft rejected 3 times | Single run | Revision counter | Mark incomplete; escalate to operator |
| Data Agent DB unreachable | Single run (QC skipped) | Connection error | Return report with `qc_status=NOT_EXECUTED`; proceed |
| Data Agent invalid SQL | Single run | `sqlparse` parse error | Retry once; if still invalid, halt |
| Data Agent ambiguous request | Single run | `DataRequest` missing fields detected during run | Return `status=INCOMPLETE_REQUEST` with missing fields |
| Website GitLab auth failure | Single run | HTTP 401 | Halt; operator fixes token |
| Website GitLab rate limit | Single run | HTTP 429 | Exponential backoff, 3 attempts |
| Website project name conflict | Single run | HTTP 409 | Append suffix, retry up to 5 times |
| Website partial commit (network drop mid-commit) | Single run, possible orphan project | Missing commit SHA in response | Operator reviews GitLab; may delete orphan and retry |
| LLM safety refusal | Single run | Empty or refusal response | Log; halt; operator reviews prompt |
| LLM rate limit | Single run | HTTP 429 from Anthropic | Exponential backoff, 3 attempts; then halt |
| Schema validation failure mid-pipeline | Single run | Pydantic validation error | Halt; log the field path and value; operator fixes the agent or schema |

**No failure propagates across runs.** Each run has its own checkpoint directory.

---

## 14. Implementation Phases

**Each phase is one session. Close out when done. Do not bundle.**

### Phase 1: Repo Skeleton + Schemas (1 session)

**What DONE looks like:**
- `pyproject.toml` with dependencies and package layout
- `src/model_project_constructor/schemas/v1/` contains all Pydantic models from §5
- `src/model_project_constructor/schemas/registry.py` contains the registry and `load_payload()` helper
- `HandoffEnvelope` defined
- All schemas have unit tests that cover: required fields, optional fields, literal constraints, serialization round-trip

**Verification commands:**
- `uv run pytest tests/schemas/ -v` — all green
- `uv run python -c "from model_project_constructor.schemas.v1 import IntakeReport"` — imports cleanly
- `uv run python -c "from model_project_constructor.schemas.registry import REGISTRY; print(len(REGISTRY))"` — prints expected count

**Session boundary:** This phase is one session. Close out when done.

---

### Phase 2: Data Agent (2 sessions)

**Sub-phase 2A (session 1): Data Agent core + LangGraph**

**What DONE looks like:**
- `src/model_project_constructor/agents/data/` contains the LangGraph flow from §10
- `DataAgent.run(request: DataRequest) -> DataReport` works end-to-end against a test SQLite DB with seeded data
- SQL parse validation uses `sqlparse`
- Datasheet generation works for one seeded query
- **The decoupling test from §7 passes** (no imports of `IntakeReport`)

**Verification commands:**
- `uv run pytest tests/agents/data/ -v`
- `uv run python -m model_project_constructor.agents.data --help` (CLI smoke test)
- `uv run pytest tests/test_data_agent_decoupling.py` — specifically validates decoupling

**Session boundary:** Close out. Sub-phase 2B is next session.

**Sub-phase 2B (session 2): Data Agent standalone package + CLI + Python API**

**What DONE looks like:**
- Standalone subpackage `model-project-constructor-data-agent` with its own `pyproject.toml`
- `typer`-based CLI: `model-data-agent run --request request.json --output report.json`
- Python API documented in a `USAGE.md` with three examples
- Standalone package installs independently and does not require the orchestrator package

**Verification commands:**
- `uv pip install -e packages/data-agent` — installs cleanly in a fresh venv
- `model-data-agent run --request tests/fixtures/sample_request.json` — produces a valid `DataReport`
- Import test: `python -c "from model_project_constructor_data_agent import DataAgent"`

**Session boundary:** Close out.

---

### Phase 3: Intake Agent + Web UI (2 sessions)

**Sub-phase 3A (session 1): Intake Agent core + LangGraph + CLI**

**What DONE looks like:**
- `src/model_project_constructor/agents/intake/` contains the LangGraph flow from §10
- Interview runs in a terminal via CLI with synthetic stakeholder responses from a fixture
- Produces a valid `IntakeReport` (including `GovernanceMetadata`) from a seeded conversation
- 10-question cap enforced; 3-revision cap enforced
- Governance sub-prompt produces sensible `cycle_time` / `risk_tier` classifications for 3 test scenarios

**Verification commands:**
- `uv run pytest tests/agents/intake/ -v`
- `uv run python -m model_project_constructor.agents.intake --fixture tests/fixtures/subrogation.yaml` produces a `COMPLETE` report

**Session boundary:** Close out.

**Sub-phase 3B (session 2): Web UI for Intake**

**What DONE looks like:**
- FastAPI app with SSE endpoint for interview
- Minimal HTMX frontend: question display + answer input + draft review page
- Session persistence in SQLite
- Resume-by-session-id works across server restart

**Verification commands:**
- `uv run uvicorn model_project_constructor.ui.intake:app` starts
- Manual test: complete an interview end-to-end in the browser
- `curl` smoke tests for SSE endpoint

**Session boundary:** Close out.

---

### Phase 4: Website Agent (2 sessions)

**Sub-phase 4A (session 1): Website Agent core + GitLab integration (no governance scaffolding yet)**

**What DONE looks like:**
- `src/model_project_constructor/agents/website/` contains the LangGraph flow from §10
- Given seeded `IntakeReport` + `DataReport` + `GitLabTarget`, creates a project on a **test GitLab instance** with the base repo structure (no governance artifacts yet)
- All `.qmd` files generated; all `src/` modules generated with function stubs; unit test files generated
- `GitLabProjectResult` returned with project URL and commit SHA

**Verification commands:**
- `uv run pytest tests/agents/website/ -v`
- Manual: run against test GitLab; clone the resulting project; `uv run pytest` passes in the generated project

**Session boundary:** Close out.

**Sub-phase 4B (session 2): Governance scaffolding**

**What DONE looks like:**
- Website Agent scaffolds governance artifacts proportional to `risk_tier` and `cycle_time` per §8
- Three test fixtures exercise tier 1, tier 2, tier 3 paths
- `GovernanceManifest` correctly lists all artifacts created
- Regulatory mapping populated based on `regulatory_frameworks`

**Verification commands:**
- `uv run pytest tests/agents/website/test_governance.py -v`
- Manual: generate one tier-1 project and verify all expected governance files exist

**Session boundary:** Close out.

---

### Phase 5: Orchestrator + Adapters + End-to-End (1 session)

**What DONE looks like:**
- `src/model_project_constructor/orchestrator/` contains:
  - `pipeline.py` with `run_pipeline(config)` from §12
  - `adapters.py` with `intake_report_to_data_request()` and inference helpers
  - `checkpoints.py` for envelope persistence
- End-to-end test with a seeded intake fixture produces a real GitLab project on test instance
- Halt behavior verified for each `FAILED_AT_*` path

**Verification commands:**
- `uv run pytest tests/orchestrator/ -v`
- `uv run pytest tests/e2e/ -v` — full pipeline run with fixtures
- Manual: run with the subrogation example fixture; clone the resulting project; verify all sections present

**Session boundary:** Close out.

---

### Phase 6: Production Hardening (1 session)

**What DONE looks like:**
- Observability: structured logging with `run_id`, `correlation_id` throughout
- Metrics: counts of runs, status distribution, per-agent latency
- Configuration: all secrets via environment or `.env`, no hardcoded credentials
- Documentation: `README.md`, `OPERATIONS.md`, `TROUBLESHOOTING.md`
- CI pipeline on this repo: lint, unit tests, decoupling test, type check (`mypy`)

**Verification commands:**
- `uv run pre-commit run --all-files`
- `uv run mypy src/`
- CI pipeline green on a PR

**Session boundary:** Close out. Pipeline is ready for pilot.

---

**Total: 9 sessions (1 planning + 8 implementation).** The planning session is this one.

---

## 15. Alternatives Considered

See `docs/planning/architecture-approaches.md` for full pros/cons of each alternative.

| Feature | Alternative | Why Rejected |
|---------|-------------|--------------|
| Orchestration | State Machine with persistent workflow | Overkill for first iteration; upgrade path preserved by interface-first design |
| Orchestration | Event-Driven with message broker | Highest infrastructure complexity; not justified for 3-agent linear pipeline |
| Tech Stack | OpenAI Agents SDK + GPT-4o | Executing LLM-generated code against corp databases is a security concern (and EDA is code-gen-only here anyway); OpenAI vendor lock-in |
| Tech Stack | Custom Python + mixed models | Two LLM providers doubles API keys, billing, prompt styles; LangGraph's checkpointing is more valuable than per-agent model optimization at this stage |
| Schemas | JSON Schema + code generation | Verbose; cross-field validation awkward; code gen can drift — not worth it for all-Python project |
| Schemas | Markdown + frontmatter | Dual source of truth (prose vs frontmatter); awkward as API request body for future Data Agent REST endpoint |
| EDA | Sandboxed subprocess execution | Security review burden; constraint C6 requires tested functions anyway |
| EDA | Containerized execution | Requires Docker in all environments; not justified when code is generated only |

---

## 16. Impact Analysis

| System | Impact | Action Required |
|--------|--------|-----------------|
| GitLab instance | Will host generated projects | Need a test group and a service account with `create_project` permission |
| Corporate LLM gateway | Must allow Anthropic API calls | Verify Claude Sonnet and Opus are approved |
| Corporate database | Data Agent needs read-only credential | Provision read-only service account for QC execution |
| Model governance team | Generated repos appear in registry | Notify governance team; agree on registry hand-off process |
| Data science team | Will receive generated draft projects | Agree on what "draft" means vs. "finished"; set expectations |
| Analyst teams | Data Agent usable standalone | Announce once Phase 2B ships; provide usage docs |

**What does NOT change:**
- Existing model governance framework and policies (this pipeline emits artifacts conforming to the framework, it does not redefine the framework)
- Existing legacy-model extraction tooling (Excel, Earnix) — those remain for existing models
- Corporate data platform — read-only access only

---

## 17. Verification Plan

### Functional

- Unit tests per phase's completion criteria
- End-to-end test with three fixtures: subrogation prediction (tier 2, supervised classification), fraud detection (tier 1, affects consumers), claim severity forecasting (tier 3, regression)
- All three fixtures produce a cloneable GitLab project whose `pytest` passes

### Non-Functional

- **Decoupling test (§7) runs in CI** — the single most important structural guarantee
- **Schema registry completeness test** — every payload type referenced in any agent is in the registry
- **Governance artifact matrix test** — for each (tier × `affects_consumers` × `uses_protected_attributes`) combination, the expected artifacts are present in the generated repo

### Operational

- Resumption test: kill the orchestrator mid-run; re-run with same `run_id`; verify it resumes from the correct checkpoint
- GitLab auth failure test: revoke token; verify clean halt with actionable error message
- LLM rate limit test: mock 429; verify backoff-retry-halt sequence

---

## 18. Open Questions

These are decisions deferred because they do not block the first implementation phase but must be resolved before Phase 6:

1. **Operator interface:** CLI or lightweight web dashboard for kicking off pipeline runs and reviewing results? Proposed default: CLI first, dashboard in Phase 6.
2. **Retention policy for `runs/`:** How long are checkpoint files kept? Proposed: 90 days.
3. **Who owns the governance registry in the generated repo?** The Website Agent initializes it; after that, is the data science team or the governance team the steward? Needs discussion with governance team during pilot.
4. **LLM cost ceiling per run:** Set a per-run token budget to prevent runaway Intake Agent loops? Proposed: `max_tokens` limit in LangGraph state.
5. **Intake agent behavior when the stakeholder is in the wrong domain** (e.g., wants to build a model unrelated to P&C claims): refuse politely or proceed? Proposed: refuse with a clear explanation and suggest alternatives.

---

## 19. Verification Checklist (per ARCHITECTURE_WORKSTREAM.md)

- [x] Every component has a defined responsibility (§4: three agents + orchestrator)
- [x] Every interface has input, output, and error contracts defined (§4 tables, §5 schemas, §12 error strategy)
- [x] Dependency graph has no circular dependencies (§7: Data Agent does not depend on Intake; decoupling test enforces this)
- [x] Failure modes are analyzed for each critical component (§4 per-agent + §13 consolidated)
- [x] Migration path exists — not applicable (greenfield)
- [x] Performance assumptions verified — not applicable at this stage (first iteration; no load targets yet)
- [x] Alternatives are documented with honest pros/cons (§15, references `architecture-approaches.md`)
- [x] Scope boundary is explicit (§1 "What This Plan Does NOT Cover")
- [x] Per-phase completion criteria stated (§14)
- [x] Session boundaries explicit in each phase (§14)

---

**End of plan.**
