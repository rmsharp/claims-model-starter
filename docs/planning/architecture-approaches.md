# Architecture Approaches: Model Project Constructor

## Context

The Model Project Constructor is a 3-agent pipeline (Intake -> Data -> Website) that turns a business idea into a GitLab project containing a draft model website. Domain: P&C insurance claims. The pipeline has clear sequential dependencies, explicit handoff reports between agents, and a reusability requirement for the Data Agent as a standalone query tool.

This document examines the critical architectural features and proposes 2-3 approaches for each, with pros/cons grounded in the project's specific constraints.

---

## Critical Feature 1: Pipeline Orchestration

How the three agents are wired together, how execution flows, and how failures are handled.

### Approach A: Sequential Script Orchestrator

A single `pipeline.py` calls each agent as a function in sequence. Handoff objects are Pydantic models passed as return values. Checkpoints are JSON files on disk.

```
pipeline.run() -> intake_agent.run() -> data_agent.run() -> website_agent.run()
```

**Pros:**
- ~50-80 lines of orchestration. Any developer reads the whole flow in minutes
- Debugging with breakpoints in a single process
- No infrastructure beyond Python
- Fastest path to a working end-to-end pipeline

**Cons:**
- No crash recovery -- manual checkpoint-resume only
- No built-in observability (logging/tracing are DIY)
- The Intake Agent's interview may span hours/days, holding a process open
- Adding agents or branching later requires restructuring

**Best for:** Proving the concept quickly. Small team (1-2 people), infrequent runs.

### Approach B: State Machine with Persistent Workflow

Pipeline runs are rows in a database (SQLite or Postgres) with states: `INTAKE_PENDING -> INTAKE_IN_PROGRESS -> INTAKE_COMPLETE -> DATA_PENDING -> ... -> WEBSITE_COMPLETE | FAILED`. A `WorkflowEngine` (~200-300 lines) manages transitions, validates handoffs, and persists state.

**Pros:**
- Runs survive crashes and restarts -- resume from last completed state
- Targeted retry: re-run only the failed step
- Full audit trail (every state transition with timestamps) -- valuable in a regulated insurance environment
- Naturally handles the Intake Agent's long-lived interview (state persists across sessions)
- Status API/CLI gives operators visibility

**Cons:**
- Database dependency (even if just SQLite)
- More conceptual overhead -- developers must understand both agent logic and state machine semantics
- Dead-letter timeout tuning per agent is operational burden
- Overkill if the pipeline runs once a week

**Best for:** Regular operation (multiple runs/month) where losing a half-complete run is costly (stakeholder interview time) and auditability matters.

### Approach C: Event-Driven with Message Passing

Each agent runs as an independent service. A message broker (Redis Streams for single-machine, RabbitMQ for team) mediates. Agents subscribe to predecessor completion events.

**Pros:**
- True decoupling -- agents developed, tested, deployed independently
- Data Agent standalone deployment is a natural consequence, not an afterthought
- Adding agents = subscribing to an event (no existing agent changes)
- Built-in retry via message redelivery

**Cons:**
- Highest infrastructure complexity (broker, multiple services, Docker Compose)
- Debugging requires tracing events across services
- Every agent must be idempotent (handle redelivered messages)
- Schema versioning becomes critical operational burden
- Significant overkill for a 3-agent linear pipeline running a few times/month

**Best for:** A platform of AI agents, not just this one pipeline. Makes sense only if the organization plans multiple pipelines or the Data Agent's standalone deployment is a primary product.

---

## Critical Feature 2: Technology Stack & LLM Integration

What models, frameworks, and tools power the agents.

### Approach A: LangGraph + Claude

LangGraph for agent orchestration (state machines with typed state, built-in checkpointing, human-in-the-loop). Claude Sonnet for the Intake Agent (conversational turns), Claude Opus for the Website Agent (complex reasoning over long context).

- **Interview:** FastAPI + WebSocket, LangGraph's `interrupt_before`/`interrupt_after` for human-in-the-loop pauses
- **SQL execution:** Read-only SQLAlchemy tool registered in LangGraph, `sqlparse` validation
- **GitLab:** `python-gitlab` library
- **EDA/Models:** Code generation only -- agent produces Jupyter notebooks committed to GitLab, not executed in pipeline

**Pros:**
- LangGraph's state machine formalism enforces handoff protocol structurally
- Built-in checkpointing -- agent failures are recoverable without restart
- Data Agent extractable as LangGraph subgraph for standalone use
- Claude's tool-use and 200K context fit the Website Agent's synthesis task well
- Project already uses Claude Code -- same model family reduces context-switching

**Cons:**
- LangGraph learning curve and rapid API churn -- risk in a slow-upgrade corporate environment
- LangChain ecosystem dependency (some enterprise teams find it over-abstracted)
- Code-generation-only EDA means the delivered GitLab project has no actual plots/metrics -- data science team must run the notebooks first
- WebSocket adds operational complexity over simpler alternatives

**Best for:** Teams comfortable with LangGraph who want framework-provided checkpointing and human-in-the-loop without building it from scratch.

### Approach B: Minimal Framework (OpenAI Agents SDK + GPT-4o)

OpenAI's Agents SDK for orchestration (lightweight: agent definitions, tool registration, handoffs, guardrails). GPT-4o for all agents.

- **Interview:** FastAPI + SSE (simpler than WebSocket, works through corporate proxies)
- **SQL execution:** GPT-4o function calling with strict schema for `execute_sql` tool
- **GitLab:** Direct `httpx` calls to GitLab API
- **EDA/Models:** Direct execution in sandboxed subprocess -- generated code is run, outputs (plots, metrics) committed to GitLab

**Pros:**
- GPT-4o's strict JSON mode guarantees structured output at every handoff
- SSE simpler and more proxy-friendly than WebSocket
- Direct EDA execution means delivered GitLab project contains actual results (plots, metrics, model performance)
- Agents SDK is thin enough to understand completely
- Cheaper per token for high-volume Intake Agent conversations

**Cons:**
- Executing LLM-generated code against corporate databases is a security review concern even with sandboxing
- OpenAI vendor lock-in -- Agents SDK ties to OpenAI specifically
- No built-in checkpointing -- recovery from mid-pipeline failures is manual
- Agents SDK is newer and less battle-tested

**Best for:** Teams where GPT-4o is already approved by corporate IT, and where delivered results (not just code) in the GitLab project is important.

### Approach C: No Framework -- Custom Python + Mixed Models

Framework-free custom orchestrator. Each agent uses the best model for its task:
- **Intake Agent:** Claude Sonnet (conversational quality, domain expertise)
- **Data Agent:** GPT-4o (strict function calling for SQL generation)
- **Website Agent:** Claude Opus (complex reasoning, long context synthesis)

- **Interview:** Streamlit chat UI (~50 lines of Python, production-quality, no frontend build tooling)
- **SQL execution:** SQLAlchemy + audit logging of all generated queries
- **GitLab:** `python-gitlab` wrapped in thin service class
- **EDA/Models:** Containerized execution in Docker (pre-built data science image, resource limits, network restricted to DB host only)

**Pros:**
- Best-of-breed model per agent -- highest quality at each step
- No framework dependency -- plain Python any developer can maintain when team rotates
- Streamlit eliminates frontend engineering entirely
- Docker container is the strongest security boundary for code execution
- Delivered GitLab project contains actual results with strong isolation
- Each agent independently deployable

**Cons:**
- Two LLM providers = two API keys, billing relationships, prompt engineering styles, rate limit strategies
- No built-in checkpointing, tracing, or retry -- must build from scratch
- Streamlit has scaling limitations for concurrent users (requires multiple instances behind load balancer)
- Docker requirement may not be met in all corporate environments

**Best for:** Teams that prioritize long-term maintainability, avoid framework lock-in, and have Docker available. Strong when model quality per agent matters more than operational simplicity.

---

## Critical Feature 3: Schema Design & Handoff Protocol

How reports are structured, validated, versioned, and passed between agents.

### Approach A: Pydantic Models with Envelope Pattern

Python-native Pydantic models define all schemas. A universal `HandoffEnvelope` carries metadata (version, source/target agent, timestamp) alongside the payload. Each agent validates incoming data by constructing the Pydantic model.

**Data Agent decoupling:** Adapter function (owned by orchestrator) maps `IntakeReport` -> `DataRequest`. Data Agent never imports `IntakeReport`. Standalone users provide `DataRequest` directly.

**Versioning:** `schema_version` field + registry dict mapping (name, version) -> Pydantic class. Minor bumps add optional fields; major bumps change required fields.

```python
class IntakeReport(BaseModel):
    business_problem: str
    proposed_solution: str
    model_solution: ModelSolution  # target, features, model_type, metrics
    estimated_value: EstimatedValue  # narrative, impact_usd, confidence
```

**Pros:**
- Zero ceremony for an all-Python project -- schemas and agents in same language
- Pydantic exports JSON Schema automatically if non-Python consumers arise later
- Detailed validation errors (field path, expected type, actual value)
- Adapter pattern is explicit and unit-testable
- Fastest to iterate during architecture phase

**Cons:**
- Python-only at runtime (JSON Schema export is a workaround, not native)
- Envelope adds two validation steps per handoff (envelope + payload)
- Field renames are breaking changes even if data is identical
- Adapter functions are glue code that must be maintained per schema change

**Best for:** All-Python project, small team, fast iteration during architecture design. Good default starting point.

### Approach B: JSON Schema as Source of Truth + Code Generation

Standalone `.json` schema files in a `schemas/` directory. Language-agnostic by design. Python types generated from schemas for convenience but schema files are authoritative. Shared concepts (`TargetVariable`, `CandidateFeature`) extracted into `schemas/common/` and referenced via `$ref`.

**Data Agent decoupling:** Separate `schemas/data_request/v1.0.0.json` that `$ref`s common definitions. Data Agent validates against its own schema, never the intake schema.

**Versioning:** Directory-based: `schemas/intake_report/v1.0.0.json`, `v1.1.0.json`. Manifest file maps schemas to supported versions. Migration scripts in `schemas/migrations/`.

**Pros:**
- Language-agnostic -- Data Agent reusable from non-Python contexts (CLI, web form, other orchestrator)
- Schemas are diffable plain files, visible in git history
- `$ref` composition enforces single definition for shared concepts
- JSON Schema is a well-known standard with broad tooling
- Schema files can be included in the delivered GitLab project

**Cons:**
- Verbose -- ~70 lines of JSON for a simple structure
- Cross-field validation awkward in JSON Schema (`if`/`then`/`else` is hard to read) -- requires two-layer validation
- Code generation adds a build step that can drift from schemas
- `$ref` resolution across files varies between libraries -- known friction point

**Best for:** When the Data Agent will genuinely be called by non-Python consumers, or when schemas as first-class diffable artifacts matters to the team.

### Approach C: Markdown with YAML Frontmatter + Validation Sidecar

Handoff documents are human-readable Markdown with YAML frontmatter carrying structured metadata. Pydantic validates the frontmatter; section-heading checks validate the body. The intake report looks like what the LLM naturally produces (prose under `## Business Problem`, `## Model Solution`, etc.) with machine-readable fields extracted into frontmatter.

**Data Agent decoupling:** Two input modes -- pipeline mode (parses intake Markdown) and standalone mode (simpler Markdown with `DataRequest` frontmatter). Normalization layer maps both to same internal structure.

**Versioning:** `version` field in frontmatter + versioned Python modules (`schemas/v1/intake_report.py`).

**Pros:**
- Handoff documents are human-readable without tooling -- data science team reads Markdown, not JSON
- LLMs produce Markdown naturally -- no JSON serialization layer on either side
- File-based handoff (directory of Markdown + SQL files) maps directly to GitLab project structure
- Standalone Data Agent input is a Markdown file an analyst could write by hand
- Matches the example output format in `initial_purpose.txt` (lines 48-80)

**Cons:**
- Dual source of truth: frontmatter may contradict the prose body
- YAML frontmatter parsing requires `python-frontmatter` dependency
- Deeply nested objects in YAML are hard to read and easy to mis-indent
- Awkward as API request body if Data Agent later gets a REST endpoint
- Test fixtures are complete Markdown documents, not simple JSON payloads

**Best for:** When handoff documents serve dual purpose (machine contract + human report), and when the GitLab output should contain readable documentation that the data science team can review directly.

---

## Critical Feature 4: EDA & Model Building Strategy

How the Website Agent produces analysis and initial models for the GitLab project.

### Approach A: Code Generation Only

The Website Agent generates Python scripts and Jupyter notebooks but does NOT execute them. Notebooks include data loading (using Data Agent's SQL), EDA, feature engineering, model training (scikit-learn), evaluation. Committed to GitLab as executable artifacts.

**Pros:**
- No execution risk -- no LLM-generated code runs against corporate databases in production
- No compute resource concerns (no OOM, no runaway training)
- Simpler pipeline -- Website Agent produces files, not results
- Fastest to implement

**Cons:**
- Delivered GitLab project has no actual results -- data science team must run everything
- Generated code may have bugs that aren't caught until human execution
- The "draft website" has no data-driven content (no plots, no metrics, no model performance)

**Best for:** Security-first environments where executing LLM-generated code is unacceptable. Good starting point that can be upgraded later.

### Approach B: Sandboxed Subprocess Execution

Website Agent generates code, then executes it in a sandboxed subprocess with resource limits (timeout, memory cap, read-only DB user, restricted filesystem). Outputs (plots, metrics, model artifacts) captured and committed to GitLab.

**Pros:**
- Delivered GitLab project contains actual results -- significantly better starting point for data science team
- Generated code is validated by execution (bugs caught immediately)
- Reasonable security boundary for internal tool

**Cons:**
- Subprocess sandboxing is imperfect -- harder to restrict than containers
- LLM-generated code may fail unpredictably, requiring retry logic
- Resource consumption varies per run

**Best for:** Environments where Docker isn't available but actual results in the deliverable are important.

### Approach C: Containerized Execution

Website Agent generates a complete Python project, submits it to a Docker container with pre-built data science image. Container runs with network restricted to DB host, memory/time limits, read-only filesystem except output directory. Results captured and committed to GitLab.

**Pros:**
- Strongest security boundary -- full isolation from host
- Predictable environment (fixed image with pinned library versions)
- Delivered GitLab project contains actual results
- Container image is reusable across runs

**Cons:**
- Requires Docker infrastructure (not available in all corporate environments)
- Container build/maintenance is additional operational work
- Slower execution (container startup overhead)

**Best for:** Environments with Docker available and security teams that require containerized execution for LLM-generated code.

---

## Decision Dependencies

These features are not independent. Key interactions:

| If you choose... | Then consider... |
|---|---|
| Sequential Script orchestration | Pydantic schemas (same simplicity level) + Code Gen Only EDA |
| State Machine orchestration | Pydantic or JSON Schema + any EDA approach |
| Event-Driven orchestration | JSON Schema (language-agnostic for independent services) |
| LangGraph framework | Pydantic (native integration) |
| No framework / Custom Python | Any schema approach works; Markdown fits LLM-native philosophy |
| Code Gen Only EDA | Any orchestration works (simplest path) |
| Containerized EDA | State Machine or Custom Python (needs failure handling for container) |

## Recommended Starting Point (for discussion)

A pragmatic first iteration:
1. **Sequential Script** orchestrator (prove the agents work end-to-end)
2. **Custom Python + Mixed Models** or **LangGraph + Claude** (depends on team's framework preference)
3. **Pydantic schemas** (fast iteration, upgrade path to JSON Schema via export)
4. **Code Generation Only** EDA (start safe, add execution later)

The interface-first constraint means the schemas and handoff protocol can be designed now regardless of orchestration choice. The orchestration and EDA strategy can be upgraded later without changing the agent interfaces -- this is the key architectural property to preserve.
