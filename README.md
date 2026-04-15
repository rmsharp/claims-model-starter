# Model Project Constructor

Multi-agent pipeline that turns a business model idea into a governance-scaffolded GitLab project. Given a stakeholder interview, it produces (1) a structured intake report, (2) a data collection plan with validated SQL and a datasheet, and (3) a draft model-build repository with proportional governance artifacts for the claims domain of a property-and-casualty insurer.

The repository is published as `claims-model-starter` on GitHub; the internal package name remains `model-project-constructor`.

## Status

Early implementation. Phases and session boundaries are tracked in `SESSION_NOTES.md`; the authoritative design document is `docs/planning/architecture-plan.md`.

| Phase | Scope | State |
|------:|-------|-------|
| 1 | Repo skeleton + v1 Pydantic schemas + envelope + registry | Complete |
| 2A | Data Agent core + LangGraph flow + AST decoupling test | Complete |
| 2B | Data Agent standalone package + CLI + Python API | Complete |
| 3A | Intake Agent core + LangGraph + CLI | Complete |
| 3B | Intake Agent Web UI (FastAPI + SSE + HTMX + SQLite) | Complete |
| 4A | Website Agent core + GitLab scaffolding (non-governance) | Complete |
| 4B | Website Agent governance scaffolding + retry-backoff + python-gitlab adapter | Complete |
| 5 | Orchestrator + adapters + end-to-end | Not started |
| 6 | Production hardening | Not started |

## Architecture in one screen

```
Stakeholder ──▶ Intake Agent ──▶ IntakeReport ──▶ adapter ──▶ DataRequest
                                                                   │
                                                                   ▼
                                                              Data Agent
                                                                   │
                                                                   ▼
                                                              DataReport
                                                                   │
                                                  IntakeReport + DataReport
                                                                   │
                                                                   ▼
                                                            Website Agent
                                                                   │
                                                                   ▼
                                                       GitLab project (draft)
```

Each agent internally uses LangGraph for state management while the top-level orchestrator is a sequential script. The Data Agent is structurally decoupled from `IntakeReport` (constraint C4) so it can be reused standalone by analysts for ad-hoc query generation; it is distributed as a separate installable package `model-project-constructor-data-agent` under `packages/data-agent/` with its own `pyproject.toml`, CLI (`model-data-agent run`), and `USAGE.md`. An AST-based test in `tests/test_data_agent_decoupling.py` enforces the decoupling at CI time.

## Repository layout

```
src/model_project_constructor/          # main "orchestrator" package
  schemas/v1/                           # IntakeReport, RepoTarget / RepoProjectResult, governance types
  schemas/v1/data.py                    # re-exports data schemas from the standalone
  schemas/envelope.py                   # HandoffEnvelope
  schemas/registry.py                   # payload registry for versioned hand-offs
  agents/data/                          # thin re-export shims onto the standalone package
  agents/intake/                        # Intake Agent: LangGraph flow + CLI (Phase 3A)
    state.py, protocol.py, nodes.py, graph.py
    agent.py                            # IntakeAgent facade (fixture + scripted modes)
    fixture.py                          # FixtureLLMClient + YAML loader
    anthropic_client.py                 # concrete IntakeLLMClient using Claude
    cli.py, __main__.py                 # typer CLI (model-intake-agent / python -m)
  ui/intake/                            # Intake Agent Web UI (Phase 3B)
    app.py                              # FastAPI app + routes + SSE endpoint
    runner.py                           # IntakeSessionStore: SqliteSaver + per-session graph
    templates.py                        # minimal HTMX pages (question/review/complete)
  agents/website/                       # Website Agent (Phase 4A base + 4B governance)
    state.py, protocol.py, nodes.py, graph.py
    agent.py                            # WebsiteAgent facade (run(intake, data, target))
    templates.py                        # pure-python base file content generators
    governance_templates.py             # 4B governance artifact generators (§8.2 tier fan-out)
    fake_client.py                      # in-memory repo-host stand-in for tests + CLI
    gitlab_adapter.py                   # 4B production adapter via python-gitlab
    cli.py, __main__.py                 # typer CLI (--fake or --private-token)
packages/data-agent/                    # standalone: model-project-constructor-data-agent
  pyproject.toml                        # independent distribution
  USAGE.md                              # CLI + Python API documentation
  src/model_project_constructor_data_agent/
    agent.py, graph.py, nodes.py, state.py   # LangGraph flow
    schemas.py                                # DataRequest, DataReport, PrimaryQuery, QC, Datasheet
    db.py, sql_validation.py, llm.py          # Protocol + SQLAlchemy wrapper + sqlparse
    anthropic_client.py                       # concrete LLMClient using Claude
    cli.py, __main__.py                       # typer CLI (model-data-agent run)
tests/
  schemas/                              # 88 schema tests
  agents/data/                          # 12 end-to-end Data Agent tests
  agents/intake/                        # 56 intake tests (graph, nodes, CLI, Anthropic)
  agents/website/                       # 88 website agent tests (templates, fake client, nodes, agent, CLI, governance, retry, adapter)
  ui/intake/                            # 22 web UI tests (FastAPI, runner, SQLite resume, SSE)
  data_agent_package/                   # 21 CLI + AnthropicLLMClient tests
  fixtures/sample_request.json          # canonical DataRequest fixture
  fixtures/subrogation.yaml             # canonical intake fixture (§4.1 worked example)
  fixtures/pricing_optimization.yaml    # strategic/tier-2 governance scenario
  fixtures/fraud_triage.yaml            # continuous/tier-1 governance scenario
  fixtures/intake_question_cap.yaml     # 10-question cap exhaustion scenario
  fixtures/intake_revision_cap.yaml     # 3-revision cap exhaustion scenario
  fixtures/subrogation_intake.json      # serialized IntakeReport (tier 3 moderate, affects_consumers)
  fixtures/tier1_intake.json            # tier 1 critical + protected attrs + EU AI Act (Phase 4B)
  fixtures/tier2_intake.json            # tier 2 high + strategic cycle (Phase 4B)
  fixtures/sample_datareport.json       # serialized DataReport for website agent input
  test_data_agent_decoupling.py         # structural decoupling guarantee (2 tests)
docs/planning/                          # architecture-approaches.md, architecture-plan.md
SESSION_RUNNER.md                       # per-session operating procedure
SAFEGUARDS.md                           # commit discipline and blast-radius rules
SESSION_NOTES.md                        # session-by-session continuity log
```

## Getting started

Prerequisites: `uv` and Python ≥ 3.11.

```bash
uv sync --extra agents --extra dev
uv run pytest
```

All 289 tests should pass with coverage above 90% (currently ≈96.5%). `uv sync` uses a workspace to build and install both `model-project-constructor` and `model-project-constructor-data-agent` editable in one step.

To run the web UI tests as well, add the `ui` extra:

```bash
uv sync --extra agents --extra ui --extra dev
```

To use the standalone Data Agent CLI (requires `ANTHROPIC_API_KEY` in the environment):

```bash
uv run model-data-agent run --request request.json --output report.json \
    --db-url "sqlite:///claims.db"
```

Add `--fake-llm` for smoke tests that don't hit the real API. Full usage is in `packages/data-agent/USAGE.md`.

To run the Intake Agent against a fixture (headless / CLI mode):

```bash
uv run python -m model_project_constructor.agents.intake \
    --fixture tests/fixtures/subrogation.yaml --output intake.json
```

This drives a synthetic interview via the real LangGraph interrupt/resume loop and writes a validated `IntakeReport` JSON document.

To start the Intake Agent **web UI** (Phase 3B, requires `ANTHROPIC_API_KEY` to drive a real interview):

```bash
uv sync --extra agents --extra ui --extra dev
uv run uvicorn model_project_constructor.ui.intake:app --reload
```

Then open `http://localhost:8000/`. The UI is a minimal HTMX frontend over the same LangGraph flow used by the CLI; session state is checkpointed to a SQLite file (`intake_sessions.db` by default, override via `INTAKE_DB_PATH`) so interviews survive server restart. Resume via `GET /sessions/{session_id}`. A server-sent-events endpoint at `/sessions/{session_id}/events` emits the current phase snapshot for scripting/monitoring.

To run the Website Agent against seeded intake + data reports:

```bash
# Fake repo host — no credentials required, writes nothing external.
uv run python -m model_project_constructor.agents.website \
    --intake tests/fixtures/subrogation_intake.json \
    --data tests/fixtures/sample_datareport.json \
    --fake

# Real GitLab (Phase 4B) — creates an actual project.
uv run python -m model_project_constructor.agents.website \
    --intake tests/fixtures/subrogation_intake.json \
    --data tests/fixtures/sample_datareport.json \
    --host-url https://gitlab.example.com \
    --namespace data-science/model-drafts \
    --private-token "$GITLAB_TOKEN"
```

The `--fake` mode prints the full file tree that would be committed and dumps a `RepoProjectResult` JSON payload. (`--fake-gitlab`, `--gitlab-url`, and `--group-path` are kept as hidden deprecated aliases for one Phase window and will be removed in Phase D.) Phase 4B scaffolds everything in §11 of `docs/planning/architecture-plan.md`, including governance artifacts proportional to `risk_tier` / `cycle_time` per §8.2. Try the tier-1 fixture (`tests/fixtures/tier1_intake.json`) to see the full fan-out including `governance/audit_log/`, `governance/eu_ai_act_compliance.md`, `governance/lcp_integration.md`, and the fairness-audit scaffolds.

## Documents worth reading

- `docs/planning/architecture-plan.md` — the authoritative design document. Sections §4 (agent boundaries), §7 (Data Agent decoupling), §10 (per-agent LangGraph flows), and §14 (implementation phases) are load-bearing.
- `docs/planning/architecture-approaches.md` — alternatives considered for each architectural decision, with pros/cons.
- `SESSION_RUNNER.md` — the session protocol. Read before starting any session.
- `SAFEGUARDS.md` — commit discipline and the two-mode engineer/architect rules.

## License

Proprietary.
