# Security Considerations

This page is for anyone doing a security review of the Model Project Constructor, or for operators responsible for running it in a production environment. It documents:

- where credentials come from and how they flow through the code,
- which components make outbound network calls and to where,
- what the LLM sees,
- what the database contract is,
- what gets written to disk, and
- known sharp edges.

**Claim standard:** every factual statement has a file:line citation. Where the code enforces something, the citation is to the enforcement site. Where something is *only documented* (not enforced), the page says so explicitly.

---

## 1. Credential handling

### 1.1 Every secret comes from the environment

There are **no hardcoded credentials anywhere in the source tree**. The orchestrator reads secrets exclusively via `OrchestratorSettings.from_env()` at `src/model_project_constructor/orchestrator/config.py:72-120`. Module docstring (`config.py:3-6`):

> every secret and every deployment-variable parameter must come from the environment (or a `.env` file loaded into the environment by the caller). There are no hardcoded credentials or hostnames anywhere in the codebase.

Loading a `.env` file is the caller's responsibility — `config.py` only reads `os.environ`. Use `python-dotenv`, `direnv`, or your orchestration layer's secret injection.

### 1.2 The complete env-var matrix

Defined in `.env.example` and documented in `OPERATIONS.md:11-30`:

| Variable | Required | Default | Used for |
|---|---|---|---|
| `MPC_HOST` | no | `gitlab` | `gitlab` or `github` |
| `MPC_HOST_URL` | no | host-specific public URL | API base URL; override for enterprise / self-hosted |
| `GITLAB_TOKEN` | yes (live GitLab) | — | PAT with `api` scope + create_project permission |
| `GITHUB_TOKEN` | yes (live GitHub) | — | PAT with `repo` scope |
| `ANTHROPIC_API_KEY` | yes (any LLM call) | — | Intake, Data Agent QC generation |
| `MPC_CHECKPOINT_DIR` | no | `./.orchestrator/checkpoints` | Where per-run JSON envelopes land |
| `MPC_LOG_LEVEL` | no | `INFO` | `DEBUG` through `CRITICAL` |
| `INTAKE_DB_PATH` | no | `./intake_sessions.db` | SQLite for live intake web UI sessions |

Only two places outside `config.py` read env vars directly:

- `src/model_project_constructor/ui/intake/app.py:75` — `INTAKE_DB_PATH` for the FastAPI web UI.
- `scripts/run_pipeline.py:78-82, 118` — demo script convenience defaults.

The adapters consume tokens via the settings object; their `__init__` signatures take `private_token: str` as a parameter (`gitlab_adapter.py:56-66`, `github_adapter.py:66-72`), so a caller must decide how to get the value to them. The example in the docstring shows `os.environ["GITLAB_TOKEN"]`, but the adapter itself has no opinion on where the token came from — a secret manager, a vault agent, or a keychain all work.

### 1.3 Fail-loud helpers

`OrchestratorSettings` is constructable without credentials so tests and preview runs can build a settings object unconditionally. Runners that actually make HTTP calls must guard against missing tokens by calling the require helpers:

```python
# config.py:122-140
def require_host_token(self) -> str:
    if not self.host_token:
        var = "GITLAB_TOKEN" if self.host == "gitlab" else "GITHUB_TOKEN"
        raise ConfigError(f"{var} is required for host={self.host!r} but was not set")
    return self.host_token

def require_anthropic_api_key(self) -> str:
    if not self.anthropic_api_key:
        raise ConfigError("ANTHROPIC_API_KEY is required but was not set")
    return self.anthropic_api_key
```

Calling these before any network I/O is the operator's responsibility — they are the explicit "I need this now" checkpoint.

### 1.4 What `.env` files look like

The template is at `.env.example`. None of its values are defaults; every credential line is commented out. An operator copies to `.env` (which is gitignored) and fills in the appropriate values for their deployment.

---

## 2. Network boundaries

Outbound network I/O happens from exactly four places.

### 2.1 Anthropic (the LLM)

Both agents that use an LLM call Anthropic's Claude API:

| Caller | File | Model (default) |
|---|---|---|
| Intake Agent | `src/model_project_constructor/agents/intake/anthropic_client.py:30, 63-65` | `claude-sonnet-4-6` |
| Data Agent | `packages/data-agent/src/model_project_constructor_data_agent/anthropic_client.py:43, 60-63` | `claude-sonnet-4-6` |

Both construct `anthropic.Anthropic()` with no explicit args — the SDK picks up `ANTHROPIC_API_KEY` from the environment. Both accept an injected `client` argument so tests can pass a mock. Both default to `claude-sonnet-4-6` and expose a `model` argument for override.

The Anthropic SDK's default endpoint is `https://api.anthropic.com`. Self-hosting the LLM is out of scope — the SDK does not support `base_url` override through our constructors.

### 2.2 GitLab (`PythonGitLabAdapter`)

`src/model_project_constructor/agents/website/gitlab_adapter.py:41-155`. Calls:

- `gitlab.Gitlab(url, private_token=..., ssl_verify=True)` (line 63-65) — the SDK client. `ssl_verify=True` is the default and not overridden for live runs.
- `gl.groups.get(namespace)` — group resolution.
- `gl.projects.create(...)` — project creation.
- `project.commits.create(...)` — multi-file commit.

Target host is whatever `host_url` the caller provides (public `https://gitlab.com` by default; enterprise instances via `MPC_HOST_URL`).

### 2.3 GitHub (`PyGithubAdapter`)

`src/model_project_constructor/agents/website/github_adapter.py:48-161`. Calls:

- `Github(auth=Auth.Token(...), base_url=host_url)` (line 72) — SDK client.
- `get_organization(namespace)` → falls back to `get_user(namespace)` — owner resolution.
- `owner.create_repo(...)` — repo creation (maps visibility to `private` boolean).
- `get_git_ref`, `create_git_blob`, `create_git_tree`, `create_git_commit`, `ref.edit` — git data API walk for a single atomic commit.

Target host is `https://api.github.com` by default; GitHub Enterprise via `MPC_HOST_URL` (e.g., `https://github.example.com/api/v3`).

### 2.4 Database (Data Agent, optional)

`ReadOnlyDB.connect()` at `packages/data-agent/src/model_project_constructor_data_agent/db.py:29-37` calls `sqlalchemy.create_engine(url)`. The URL is whatever the operator passes to `--db-url` (CLI) or configures at deployment. This is the only DB connection in the project.

If no DB URL is configured, quality checks are generated but not executed — all marked `NOT_EXECUTED`. The DataReport still carries `status="COMPLETE"` with a data-quality concern noting the unreachable database (`cli.py:10-13`).

### 2.5 What does *not* make network calls

- The intake fixture CLI (`intake/cli.py`) — replays canned answers, calls no LLM.
- The orchestrator's `pipeline.py` — pure dispatcher; no I/O of its own.
- `CheckpointStore` — writes to local disk only.
- `FakeRepoClient` — in-memory test double.
- Observability modules (`orchestrator/logging.py`, `orchestrator/metrics.py`) — stdlib logging + in-memory counters.

---

## 3. What the LLM sees

### 3.1 Intake Agent

Every LLM call sends:

- One of two system prompts (`anthropic_client.py:33-42` for the interviewer, 44-50 for governance classification).
- A user message containing: the domain, the optional `initial_problem`, the full `qa_pairs` history, and the `questions_asked` counter (`anthropic_client.py:72-83`).

**The stakeholder's answers are forwarded verbatim to Anthropic.** Any PII or confidential claim details included in an answer are transmitted as-is. There is **no redaction, scrubbing, or PII filter in this codebase** — grep for `redact|pii|scrub|mask|sanitize` in `src/` returns zero hits.

Implication for operators: if the interview may contain policyholder-identifying data, the deployment must satisfy Anthropic's data handling terms (or the interview must be constrained to not elicit PII). See [Anthropic's product terms](https://www.anthropic.com/legal) for current commitments — this project does not re-state them.

### 3.2 Data Agent

Prompts sent to Anthropic (`packages/data-agent/.../anthropic_client.py:68-209`):

- The full `DataRequest` JSON — which includes the `target_description`, `required_features`, `population_filter`, `time_range`, and `database_hint`.
- The generated SQL and quality-check SQL (for the `summarize` and `generate_datasheet` calls).
- **No actual data rows.** The Data Agent asks Claude to *generate* SQL; it does not feed query results back into the LLM.

Observed rule: **`raw_result` (the executed query output) is never sent to Claude.** The `summarize` call receives only quality-check status summaries (`_dump_qc_status` at `anthropic_client.py:225-235` formats `check_name: execution_status — result_summary`), not row-level data. This is a significant security property — deployments can safely execute queries against sensitive tables knowing the rows themselves never reach the LLM.

### 3.3 Website Agent

Does not call an LLM. It deterministically templates files from the `IntakeReport` and `DataReport` payloads (`src/model_project_constructor/agents/website/templates.py`, `governance_templates.py`). Payload field content (business problem prose, SQL text, etc.) is interpolated into the generated files and committed to the target repo.

---

## 4. Database contract

### 4.1 Read-only is enforced at the credential layer, not in code

`ReadOnlyDB` (`db.py:22-45`) does not parse incoming SQL or attempt to reject mutating statements. Its module docstring is explicit (lines 4-8):

> Read-only enforcement is a database-credential concern in production (§9.1). This wrapper deliberately does not attempt to parse or reject mutating SQL — the Data Agent's LLM is prompted to emit SELECTs, and the pipeline is configured with a SELECT-only role at deployment time. The wrapper's sole job is to surface a clean `DBConnectionError` on connect failure so the graph can take the SKIP_EXECUTION off-ramp.

**Operator responsibility:** the DB URL passed to `ReadOnlyDB` must be a role/account with `SELECT`-only privileges (and `USAGE` on the relevant schemas). If the LLM misbehaves and generates a `DROP TABLE`, an unrestricted role will execute it. A correctly restricted role will have the statement rejected by the DB. This is a deliberate design choice — defense-in-depth via DB roles is more trustworthy than in-process SQL parsing.

### 4.2 SQL parse-level validation

`packages/data-agent/src/model_project_constructor_data_agent/sql_validation.py:16-29` runs `sqlparse.parse(sql)` and rejects:

- Empty / whitespace strings.
- Inputs `sqlparse` classifies as `"UNKNOWN"`.
- Inputs `sqlparse` fails to tokenize.

This is a **coarse well-formedness check**, not a security filter. It will not catch a well-formed `DROP TABLE` or a SQL-injection-style concatenation. Module docstring (lines 1-8) is explicit about this.

### 4.3 What the Data Agent does when DB is unreachable

`DBConnectionError` is raised from `ReadOnlyDB.connect()` on any SQLAlchemy exception. The agent's graph takes the SKIP_EXECUTION off-ramp: quality checks are emitted as `NOT_EXECUTED`, and the DataReport's `data_quality_concerns` records the reason. No partial data is persisted.

---

## 5. Checkpoint storage

### 5.1 What goes to disk

Every inter-agent handoff is written as a JSON file under `$MPC_CHECKPOINT_DIR/<run_id>/`. Per run:

```
IntakeReport.json           # envelope with IntakeReport payload
DataRequest.json            # envelope with DataRequest payload
DataReport.json             # envelope with DataReport payload
RepoTarget.json             # envelope with RepoTarget payload
RepoProjectResult.result.json   # terminal result (plain JSON, not an envelope)
```

See [Schema Reference §9](Schema-Reference) for the layout rationale.

### 5.2 Sensitivity

What lands on disk:

- **Interview Q&A** — in `IntakeReport.json` via the business_problem / proposed_solution fields and governance rationales. Stakeholder prose is preserved.
- **SQL queries** — in `DataRequest.json` (features, filters) and `DataReport.json` (primary queries + quality check SQL).
- **Database hints** — `database_hint` field on `DataRequest`.
- **Repo target URLs and project URLs** — from `RepoTarget` and `RepoProjectResult`.

What does **not** land on disk:

- **No API tokens** (`GITLAB_TOKEN`, `GITHUB_TOKEN`, `ANTHROPIC_API_KEY`). Envelopes carry payloads, not the orchestrator's configuration.
- **No query result rows.** `QualityCheck.raw_result` is the only field that could carry rows, and the production flow populates it only with summary statistics, not row data.

### 5.3 Protection

- `.orchestrator/` is in `.gitignore` — checkpoint files are never committed.
- `intake_sessions.db` and its `-shm` / `-wal` siblings are also gitignored.
- `.env` is gitignored.

Filesystem permissions on `$MPC_CHECKPOINT_DIR` are the operator's responsibility — the code does not chmod the directory or files.

---

## 6. Logging

### 6.1 What gets logged

`orchestrator/logging.py` emits three event types per agent call (`make_logged_runner` at `logging.py:58-117`):

| Event | Level | Context fields |
|---|---|---|
| `agent.start` | INFO | `agent`, `run_id`, `correlation_id` |
| `agent.end` | INFO | plus `duration_ms`, `status` |
| `agent.error` | ERROR | plus `duration_ms`, `error_type`, `error_message` |

### 6.2 Credential exposure

No field in the context dict carries credentials. `agent`, `run_id`, and `correlation_id` are the only bound context. `error_message` is `str(exc)` for whatever exception propagated — in principle, a poorly-written adapter could include a token in an exception message, but the shipped adapters do not.

`error_type` is the exception class name (e.g., `RepoClientError`), not the message — safe by construction.

### 6.3 Log format

The module uses stdlib `logging`. Structured fields land on the record's `extra={"context": ...}` dict. To produce JSON logs, operators install a JSON formatter on the `model_project_constructor.orchestrator` logger namespace (see `OPERATIONS.md:80-106` for a `python-json-logger` snippet).

Default level is `INFO` via `MPC_LOG_LEVEL`. `DEBUG` is safe — there is no DEBUG-level log that prints tokens or payloads. (Verified by reading every call site in `logging.py` and `metrics.py`.)

---

## 7. CI / shared-infrastructure secrets

The project's GitHub Actions workflow (`.github/workflows/ci.yml`) has **no secrets references** — no `${{ secrets.* }}` expressions anywhere. Jobs:

1. `lint` — `uv sync --extra dev && uv run ruff check`.
2. `typecheck` — `uv sync --extra agents --extra ui --extra dev && uv run mypy src/`.
3. `test` — same install plus `uv run pytest -q`.
4. `decoupling` — verifies the Data Agent package does not import from the main package.

None of these jobs perform live network calls to GitLab, GitHub repo APIs, or Anthropic. The full test suite runs against `FakeRepoClient` and stubbed LLM clients. No production credentials are ever present in the CI runner.

---

## 8. Generated project security

The Website Agent scaffolds a new project (see [Generated Project Structure](Generated-Project-Structure)). Templates live in:

- `src/model_project_constructor/agents/website/templates.py`
- `src/model_project_constructor/agents/website/governance_templates.py`

The templates emit:

- `.env.example` with placeholder values (never real credentials).
- CI workflow files (`.gitlab-ci.yml` or `.github/workflows/ci.yml`) that do not reference secrets.
- README, data guide, model registry JSON, governance artifacts.

**Manual verification for any templated credential string:** `grep -R "ghp_\|glpat_\|sk-ant-\|AKIA\|-----BEGIN" src/model_project_constructor/agents/website/` returns zero hits in the shipped codebase. If future templates add a real-looking string, it will stand out.

---

## 9. Third-party dependencies (trust surface)

From `pyproject.toml` (root) and `packages/data-agent/pyproject.toml`:

| Dependency | Used by | Trust profile |
|---|---|---|
| `pydantic>=2.6,<3` | everywhere | Core schema layer — wide usage, active maintenance. |
| `pyyaml>=6` | intake fixtures | Standard YAML. Use `safe_load` only (verified). |
| `langgraph>=0.2,<0.3` | intake/data/website agent graphs | State graph framework. |
| `anthropic>=0.40` | LLM calls | Anthropic's official SDK. |
| `sqlparse>=0.5` | Data Agent SQL validation | Parse-level only — no execution. |
| `sqlalchemy>=2.0,<3` | `ReadOnlyDB` | Standard; DB URL is operator-provided. |
| `python-gitlab>=4` | GitLab adapter | Official GitLab SDK. |
| `PyGithub>=2,<3` | GitHub adapter | Official GitHub SDK. (LGPL-3.0 — see [SBOM](Software-Bill-of-Materials).) |
| `typer>=0.12` | CLIs | Standard. |
| `fastapi>=0.110`, `uvicorn>=0.29`, `sse-starlette>=2` | intake web UI | Only needed for live interviews. |
| `langgraph-checkpoint-sqlite>=2.0,<3` | intake web UI checkpoints | SQLite-backed state persistence for live interviews. |

Full dependency tree including transitives and locked versions is in the [SBOM](Software-Bill-of-Materials).

---

## 10. Known gaps and non-goals

These are explicit design decisions, not bugs.

1. **No in-process SQL filtering.** The Data Agent prompts for SELECTs; safety is a DB-role concern. If you need defense-in-depth, add a proxy that rejects non-SELECTs — do not patch `sql_validation.py`.
2. **No PII redaction before LLM calls.** The deployment must satisfy its own data-handling contract with Anthropic. This is a policy problem, not a code problem.
3. **No auth on the intake web UI.** `src/model_project_constructor/ui/intake/app.py` serves routes without authentication or authorization middleware. The app is designed to be run behind a reverse proxy that handles auth (corporate SSO, OAuth proxy, etc.). Running it as-is on a public interface would expose the interview surface to anyone who can reach it.
4. **No rate limiting** on adapter calls or LLM calls. The SDKs will surface provider-side rate limit errors; this project does not add its own limiter.
5. **No retry budget for network calls.** The Website Agent's LangGraph has a bounded retry loop for commit failures (`RETRY_BACKOFF`), but neither the adapters nor the LLM clients retry on their own. Transient failures bubble up as halt conditions.
6. **No audit log.** Logging is observability, not immutable audit. If you need a compliance-grade audit trail, ship the structured log events to a WORM-capable store; do not rely on in-process logging alone.
7. **Checkpoint files are world-readable by default.** Filesystem permissions are not managed by the code. If `$MPC_CHECKPOINT_DIR` sits on a shared filesystem, apply group/mode restrictions before running production interviews.
8. **LLM model ID is unverified at construction.** The default `claude-sonnet-4-6` is chosen from the session-time model family list (`intake/anthropic_client.py:8-12` module docstring). First live invocation will raise from the Anthropic SDK if the ID is wrong — this is a deliberate trade-off to avoid coupling the import path to a network probe.

---

## 11. Checklist for a security review

- [ ] Confirm `.env` and `$MPC_CHECKPOINT_DIR` are on appropriately-permissioned storage.
- [ ] Confirm the Data Agent's DB role is `SELECT`-only on the intended schemas.
- [ ] Confirm the intake web UI, if deployed, sits behind an authenticating reverse proxy.
- [ ] Confirm Anthropic data handling terms are compatible with the content interviewers will elicit.
- [ ] Confirm the target `GITLAB_TOKEN` / `GITHUB_TOKEN` has the minimum required scope (no broader than `api` / `repo`).
- [ ] Confirm CI does not inject real credentials into the `.github/workflows/ci.yml` jobs.
- [ ] Review the [SBOM](Software-Bill-of-Materials) for unacceptable license profiles.
- [ ] Decide whether checkpoint files must be encrypted at rest (this project does not encrypt them).
- [ ] Decide whether LLM call metadata should be forwarded to a SIEM (structured logging makes this straightforward).

---

## 12. Key files

| File | Security surface |
|---|---|
| `src/model_project_constructor/orchestrator/config.py` | Env-var loader, `require_*` guards |
| `.env.example` | Complete env-var template |
| `OPERATIONS.md` | Env-var reference, deployment recipes |
| `src/model_project_constructor/agents/intake/anthropic_client.py` | Intake LLM prompts + SDK construction |
| `packages/data-agent/.../anthropic_client.py` | Data Agent LLM prompts + SDK construction |
| `src/model_project_constructor/agents/website/gitlab_adapter.py` | GitLab network boundary |
| `src/model_project_constructor/agents/website/github_adapter.py` | GitHub network boundary |
| `packages/data-agent/.../db.py` | Database connection layer + read-only contract |
| `packages/data-agent/.../sql_validation.py` | SQL parse-level check (not a security filter) |
| `src/model_project_constructor/orchestrator/logging.py` | Structured log events |
| `src/model_project_constructor/orchestrator/checkpoints.py` | On-disk envelope storage |
| `.github/workflows/ci.yml` | CI pipeline (no secrets) |
| `.gitignore` | `.env`, `.orchestrator/`, `intake_sessions.db*` excluded |
