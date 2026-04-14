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
| 3 | Intake Agent + Web UI | Not started |
| 4 | Website Agent (GitLab scaffolding) | Not started |
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
  schemas/v1/                           # IntakeReport, GitLab*, governance types
  schemas/v1/data.py                    # re-exports data schemas from the standalone
  schemas/envelope.py                   # HandoffEnvelope
  schemas/registry.py                   # payload registry for versioned hand-offs
  agents/data/                          # thin re-export shims onto the standalone package
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
  data_agent_package/                   # 21 CLI + AnthropicLLMClient tests
  fixtures/sample_request.json          # canonical DataRequest fixture
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

All 123 tests should pass with coverage above 80% (currently ≈96%). `uv sync` uses a workspace to build and install both `model-project-constructor` and `model-project-constructor-data-agent` editable in one step.

To use the standalone Data Agent CLI (requires `ANTHROPIC_API_KEY` in the environment):

```bash
uv run model-data-agent run --request request.json --output report.json \
    --db-url "sqlite:///claims.db"
```

Add `--fake-llm` for smoke tests that don't hit the real API. Full usage is in `packages/data-agent/USAGE.md`.

## Documents worth reading

- `docs/planning/architecture-plan.md` — the authoritative design document. Sections §4 (agent boundaries), §7 (Data Agent decoupling), §10 (per-agent LangGraph flows), and §14 (implementation phases) are load-bearing.
- `docs/planning/architecture-approaches.md` — alternatives considered for each architectural decision, with pros/cons.
- `SESSION_RUNNER.md` — the session protocol. Read before starting any session.
- `SAFEGUARDS.md` — commit discipline and the two-mode engineer/architect rules.

## License

Proprietary.
