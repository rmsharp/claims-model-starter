# Software Bill of Materials

This SBOM covers both the **Model Project Constructor** (the tool) and the **generated claims-model-starter projects** (the output).

## System requirements

| Requirement | Version |
|-------------|---------|
| Python | >= 3.11 |
| Package manager | [uv](https://docs.astral.sh/uv/) (workspace-based) |
| Build backend | hatchling |
| License | Proprietary |

---

## Part 1: Model Project Constructor dependencies

### Core dependencies

| Package | Constraint | Purpose |
|---------|-----------|---------|
| pydantic | >=2.6,<3 | Data validation and serialization for all schemas |
| pyyaml | >=6 | YAML fixture loading for intake interviews |
| model-project-constructor-data-agent | workspace | Standalone data agent subpackage |

### Agent stack (`--extra agents`)

| Package | Constraint | Purpose |
|---------|-----------|---------|
| langgraph | >=0.2,<0.3 | Agent state machine and graph execution |
| anthropic | >=0.40 | Claude API client (all agents) |
| sqlparse | >=0.5 | SQL parsing and validation |
| sqlalchemy | >=2.0,<3 | Database abstraction (Data Agent) |
| python-gitlab | >=4 | GitLab API adapter (Website Agent) |
| PyGithub | >=2,<3 | GitHub API adapter (Website Agent) |
| typer | >=0.12 | CLI framework |

### Web UI stack (`--extra ui`)

| Package | Constraint | Purpose |
|---------|-----------|---------|
| fastapi | >=0.110 | Intake web server and routing |
| uvicorn | >=0.29 | ASGI application server |
| sse-starlette | >=2 | Server-Sent Events for interview streaming |
| langgraph-checkpoint-sqlite | >=2.0,<3 | SQLite-backed session checkpointing |
| python-multipart | >=0.0.9 | Form data parsing |

### Development tools (`--extra dev`)

| Package | Constraint | Purpose |
|---------|-----------|---------|
| pytest | >=8 | Testing framework |
| pytest-asyncio | >=0.23 | Async test support for LangGraph nodes |
| pytest-cov | >=5 | Coverage reporting (94% minimum) |
| mypy | >=1.10 | Static type checking (strict mode) |
| ruff | >=0.5 | Linting: E, F, I, UP, B, SIM rule sets |

### Data Agent subpackage (`packages/data-agent/`)

| Package | Constraint | Purpose |
|---------|-----------|---------|
| pydantic | >=2.6,<3 | DataRequest/DataReport schemas |
| langgraph | >=0.2,<0.3 | Agent graph execution |
| sqlparse | >=0.5 | SQL parsing and analysis |
| sqlalchemy | >=2.0,<3 | Database abstraction |
| anthropic | >=0.40 | Claude API client |
| typer | >=0.12 | CLI framework |

### Key transitive dependencies

These are pulled in by direct dependencies and pinned in `uv.lock`:

| Package | Pulled in by | Purpose |
|---------|-------------|---------|
| langchain-core | langgraph | Base types and protocols |
| langsmith | langchain-core | Observability and debugging |
| httpx | anthropic, langsmith | Async HTTP client |
| requests | python-gitlab, PyGithub | Sync HTTP client |
| starlette | fastapi | ASGI web framework |
| click | typer, uvicorn | CLI argument parsing |
| rich | typer | Terminal formatting |
| cryptography | PyGithub, python-gitlab | Encryption, SSH key handling |
| pynacl | PyGithub | Public key encryption |
| pyjwt | PyGithub | JWT token handling |
| anyio | httpx, sse-starlette | Async/sync bridge |
| aiosqlite | langgraph-checkpoint-sqlite | Async SQLite wrapper |
| orjson | langgraph-sdk, langsmith | Fast JSON encoding |
| ormsgpack | langgraph-checkpoint | MessagePack serialization |
| greenlet | sqlalchemy | Coroutine context switching |
| tenacity | langchain-core | Retry logic |
| typing-extensions | multiple | Backported typing features |

### CI/CD tooling

| Tool | Source | Purpose |
|------|--------|---------|
| actions/checkout | GitHub Actions v4 | Git checkout |
| astral-sh/setup-uv | GitHub Actions | Install uv package manager |
| actions/upload-artifact | GitHub Actions v4 | Store coverage HTML reports |

---

## Part 2: Generated project dependencies

The generated claims-model-starter repository has its own, much smaller dependency set:

### Core dependencies

| Package | Constraint | Purpose |
|---------|-----------|---------|
| pandas | >=2 | Data manipulation and analysis |
| scikit-learn | >=1.4 | Machine learning models and evaluation |
| sqlalchemy | >=2 | Database query execution |

### Development dependencies

| Package | Constraint | Purpose |
|---------|-----------|---------|
| pytest | >=8 | Testing framework |
| pytest-cov | >=5 | Coverage reporting |
| ruff | >=0.5 | Linting and formatting |

### Build system

| Component | Value |
|-----------|-------|
| Build backend | hatchling |
| Python requirement | >=3.11 |
| Package layout | `src/<project_slug>/` |

### Pre-commit hooks

| Hook | Source | Purpose |
|------|--------|---------|
| ruff (lint) | ruff-pre-commit | Code linting |
| ruff (format) | ruff-pre-commit | Code formatting |
| model_registry validation | local | Schema validation of `governance/model_registry.json` |

### Rendering (optional, not installed by default)

| Tool | Purpose |
|------|---------|
| [Quarto](https://quarto.org/) >= 1.5 | Render `.qmd` analysis notebooks to HTML |

---

## Part 3: Runtime environment

### Environment variables

| Variable | Scope | Purpose |
|----------|-------|---------|
| `ANTHROPIC_API_KEY` | Any live agent run | Claude API authentication |
| `GITLAB_TOKEN` | GitLab live mode | GitLab API (Website Agent) |
| `GITHUB_TOKEN` | GitHub live mode | GitHub API (Website Agent) |
| `MPC_CHECKPOINT_DIR` | All runs | Orchestrator handoff storage |
| `MPC_HOST` | All runs | `gitlab` or `github` (default: gitlab) |
| `MPC_HOST_URL` | Self-hosted instances | Override API endpoint |
| `MPC_LOG_LEVEL` | All runs | Logging verbosity (default: INFO) |
| `INTAKE_DB_PATH` | Web UI only | SQLite session state |

### Frontend dependencies

The intake web UI uses **no JavaScript build tools**. It relies on:

- Pure HTML templates (Jinja2-style, minimal inline JS)
- [HTMX](https://htmx.org/) loaded from CDN for form/SSE interactions

There is no `package.json`, `npm`, or `node_modules`.

---

## Dependency summary by component

| Component | Direct deps | Notable transitive |
|-----------|------------|-------------------|
| **Intake Agent** | anthropic, langgraph, pydantic, typer | httpx, langchain-core, anyio |
| **Intake Web UI** | fastapi, uvicorn, sse-starlette, langgraph-checkpoint-sqlite | starlette, aiosqlite, anyio |
| **Data Agent** | anthropic, langgraph, sqlparse, sqlalchemy, typer | httpx, langchain-core, greenlet |
| **Website Agent** | anthropic, langgraph, python-gitlab, PyGithub, typer | requests, cryptography, pynacl, pyjwt |
| **Orchestrator** | pydantic, pyyaml | (uses agent deps transitively) |
| **Testing** | pytest, pytest-asyncio, pytest-cov, mypy, ruff | coverage, pluggy, pathspec |

## Locked version snapshot

The `uv.lock` file pins all packages to exact versions. As of the current lockfile:

| Package | Locked version |
|---------|---------------|
| anthropic | 0.94.1 |
| langgraph | 0.2.76 |
| fastapi | 0.135.3 |
| pydantic | 2.13.0 |
| sqlalchemy | 2.0.49 |
| python-gitlab | 8.2.0 |
| PyGithub | 2.9.1 |
| pytest | 9.0.3 |
| mypy | 1.20.1 |
| ruff | 0.15.10 |

The full locked dependency tree (87 packages) is in `uv.lock` at the repository root.
