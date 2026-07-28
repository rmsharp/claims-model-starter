# Software Bill of Materials

This SBOM covers both the **Model Project Constructor** (the tool) and the **generated claims-model-starter projects** (the output).

## System requirements

| Requirement | Version |
|-------------|---------|
| Python | >= 3.11 |
| Package manager | [uv](https://docs.astral.sh/uv/) (workspace-based) |
| Build backend | hatchling |
| License | MIT |

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
| anthropic[bedrock] | >=0.94 | Claude API client (Intake and Data agents only — the Website Agent makes no LLM calls). The `[bedrock]` extra pulls in boto3/botocore for the AWS Bedrock provider |
| sqlparse | >=0.5 | SQL parsing and validation |
| sqlalchemy | >=2.0,<3 | Database abstraction (Data Agent) |
| httpx | >=0.27,<1 | GitLab + GitHub API adapters — direct REST calls (Website Agent) |
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
| pytest-cov | >=5 | Coverage reporting (95% minimum) |
| mypy | >=1.10 | Static type checking (strict mode) |
| ruff | >=0.5 | Linting: E, F, I, UP, B, SIM rule sets |

### Documentation tools (`--extra docs`)

| Package | Constraint | Purpose |
|---------|-----------|----------|
| mkdocs | >=1.5 | Static site generator for wiki |
| mkdocs-material | >=9.0 | Material Design theme for mkdocs |

### Data Agent subpackage (`packages/data-agent/`)

| Package | Constraint | Purpose |
|---------|-----------|---------|
| pydantic | >=2.6,<3 | DataRequest/DataReport schemas |
| langgraph | >=0.2,<0.3 | Agent graph execution |
| sqlparse | >=0.5 | SQL parsing and analysis |
| sqlalchemy | >=2.0,<3 | Database abstraction |
| anthropic[bedrock] | >=0.94 | Claude API client; the `[bedrock]` extra pulls in boto3/botocore for the AWS Bedrock provider |
| typer | >=0.12 | CLI framework |

### Key transitive dependencies

These are pulled in by direct dependencies and pinned in `uv.lock`:

| Package | Pulled in by | Purpose |
|---------|-------------|---------|
| langchain-core | langgraph | Base types and protocols |
| langsmith | langchain-core | Observability and debugging |
| httpx | anthropic, langsmith | Async HTTP client |
| boto3 | anthropic[bedrock] | AWS SDK — present only because of the Bedrock LLM provider |
| botocore | boto3, anthropic[bedrock] | AWS SigV4 request signing and credential-chain resolution |
| jmespath | boto3, botocore | JSON query language used by the AWS SDK |
| s3transfer | boto3 | AWS transfer manager (a boto3 dependency; unused by this project) |
| python-dateutil | botocore, ghp-import | Date parsing for AWS API payloads |
| requests | langsmith | Sync HTTP client |
| starlette | fastapi | ASGI web framework |
| click | typer, uvicorn | CLI argument parsing |
| rich | typer | Terminal formatting |
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
| `ANTHROPIC_API_KEY` | Live agent runs on the `anthropic` provider | Claude API authentication — not used by the `bedrock` provider, which authenticates from the AWS credential chain |
| `AWS_REGION` / `AWS_DEFAULT_REGION` | `bedrock` provider | Selects the regional Bedrock endpoint and the data-residency geography |
| `GITLAB_TOKEN` | GitLab live mode | GitLab API (Website Agent) |
| `GITHUB_TOKEN` | GitHub live mode | GitHub API (Website Agent) |
| `MPC_CHECKPOINT_DIR` | All runs | Orchestrator handoff storage |
| `MPC_HOST` | All runs | `gitlab` or `github` (default: gitlab) |
| `MPC_HOST_URL` | Self-hosted instances | Override API endpoint |
| `MPC_LOG_LEVEL` | All runs | Logging verbosity (default: INFO) |
| `MPC_NAMESPACE` | Live host runs | Target GitLab group / GitHub org **path** (never a URL — a URL is rejected) |
| `INTAKE_DB_PATH` | Web UI only | SQLite session state |
| `INTAKE_LLM_PROVIDER` | Intake web UI | LLM backend: `anthropic` (default) or `bedrock` |
| `INTAKE_LLM_MODEL` | Intake web UI | Model-id override; when unset, each provider uses its own `DEFAULT_MODEL` |

One more variable is honoured by the Bedrock SDK client, documented (in `.env.example`) and guardable via `require_sigv4=True` (default `False`):

| Variable | Scope | Purpose |
|----------|-------|---------|
| `AWS_BEARER_TOKEN_BEDROCK` | `bedrock` provider, **dev only** | Short-term Bedrock API key; when set it overrides SigV4 and bypasses the IAM role — leave unset in production (pass `require_sigv4=True` to make a stray token a hard error) |

### Frontend dependencies

The intake web UI uses **no JavaScript build tools**. It relies on:

- Pure HTML templates (Jinja2-style, minimal inline JS)
- [HTMX](https://htmx.org/) loaded from CDN for form/SSE interactions

There is no `package.json`, `npm`, or `node_modules`.

---

## Dependency summary by component

| Component | Direct deps | Notable transitive |
|-----------|------------|-------------------|
| **Intake Agent** | anthropic[bedrock], langgraph, pydantic, typer | httpx, langchain-core, anyio, boto3, botocore |
| **Intake Web UI** | fastapi, uvicorn, sse-starlette, langgraph-checkpoint-sqlite | starlette, aiosqlite, anyio |
| **Data Agent** | anthropic[bedrock], langgraph, sqlparse, sqlalchemy, typer | httpx, langchain-core, greenlet, boto3, botocore |
| **Website Agent** | langgraph, httpx, typer (no `anthropic` — deterministic, makes no LLM calls) | (none unique — httpx's own transitives are shared with the LLM clients) |
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
| httpx | 0.28.1 |
| pytest | 9.0.3 |
| mypy | 1.20.1 |
| ruff | 0.15.10 |
| boto3 | 1.43.32 |
| botocore | 1.43.32 |

The full locked dependency tree — 91 `[[package]]` entries, including the two workspace members — is in `uv.lock` at the repository root.
