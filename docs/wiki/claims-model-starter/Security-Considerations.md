# Security Considerations

This page is for anyone doing a security review of the Model Project Constructor, or for operators responsible for running it in a production environment. It documents:

- where credentials come from and how they flow through the code,
- which components make outbound network calls and to where,
- what the LLM sees,
- what the database contract is,
- what gets written to disk, and
- known sharp edges.

**Claim standard:** every factual statement names a grep-locatable code symbol (class, function, method, or module constant) in its full-path defining file. Where the code enforces something, the reference is to the enforcement site. Where something is *only documented* (not enforced), the page says so explicitly.

---

## 1. Credential handling

### 1.1 Every secret comes from the environment

There are **no hardcoded credentials anywhere in the source tree**. The orchestrator reads secrets exclusively via `OrchestratorSettings.from_env` in `src/model_project_constructor/orchestrator/config.py`. Module docstring (in `src/model_project_constructor/orchestrator/config.py`):

> every secret and every deployment-variable parameter must come from the environment (or a `.env` file loaded into the environment by the caller). There are no hardcoded credentials or hostnames anywhere in the codebase.

Loading a `.env` file is the caller's responsibility — `src/model_project_constructor/orchestrator/config.py` only reads `os.environ`. Use `python-dotenv`, `direnv`, or your orchestration layer's secret injection.

### 1.2 The complete env-var matrix

Defined in `.env.example` and documented in `OPERATIONS.md` §1 — except the two AWS rows (`AWS_REGION` / `AWS_DEFAULT_REGION` and `AWS_BEARER_TOKEN_BEDROCK`), which are covered by `docs/deployment/bedrock-enterprise.md` instead of `OPERATIONS.md`:

| Variable | Required | Default | Used for |
|---|---|---|---|
| `MPC_HOST` | no | `gitlab` | `gitlab` or `github` |
| `MPC_HOST_URL` | no | host-specific public URL | API base URL; override for enterprise / self-hosted |
| `MPC_NAMESPACE` | no | host-specific default (GitLab: `data-science/model-drafts`; GitHub: `my-org`) | Target group/org path for generated project (git-host scoped) |
| `GITLAB_TOKEN` | yes (live GitLab) | — | PAT with `api` scope + create_project permission |
| `GITHUB_TOKEN` | yes (live GitHub) | — | PAT with `repo` scope |
| `ANTHROPIC_API_KEY` | yes (LLM calls on the `anthropic` provider) | — | Intake, Data Agent QC generation. Not used by `bedrock`, which authenticates from the AWS credential chain. |
| `MPC_CHECKPOINT_DIR` | no | `./.orchestrator/checkpoints` | Where per-run JSON envelopes land |
| `MPC_LOG_LEVEL` | no | `INFO` | `DEBUG` through `CRITICAL` |
| `INTAKE_DB_PATH` | no | `./intake_sessions.db` | SQLite for live intake web UI sessions |
| `INTAKE_LLM_PROVIDER` | no | `anthropic` | LLM backend for the intake web UI: `anthropic` or `bedrock`. An unknown value raises `ValueError` at app construction (`_resolve_provider` in `src/model_project_constructor/ui/intake/app.py`). Only read by the UI; the CLIs use `--provider`. |
| `INTAKE_LLM_MODEL` | no | provider default | Model-id override for the intake web UI; leave unset to keep the id provider-native. Only read by the UI. |
| `AWS_REGION` / `AWS_DEFAULT_REGION` | yes (bedrock, unless supplied as the `aws_region` argument or by the AWS profile) | — | Region for the Bedrock client — selects the endpoint host and the data-residency geography. An unresolved region raises `AnthropicError` at client construction rather than silently defaulting. |
| `AWS_BEARER_TOKEN_BEDROCK` | no (**dev only**) | — | Short-term Bedrock API key. **Leave unset in production** — the bedrock-mantle client selects bearer mode and skips SigV4 even with a valid IAM role attached, bypassing least-privilege, unless `require_sigv4=True` is passed (default `False`). |

Outside `src/model_project_constructor/orchestrator/config.py`, three modules read env vars directly (one of them duplicated across both packages, so four files in total):

- `_resolve_provider`, `_resolve_model`, and `create_app` in `src/model_project_constructor/ui/intake/app.py` — `INTAKE_LLM_PROVIDER`, `INTAKE_LLM_MODEL`, and `INTAKE_DB_PATH` for the FastAPI web UI.
- `build_repo_target` and `build_website_runner` in `scripts/run_pipeline.py` — demo-script convenience defaults (`MPC_HOST_URL`, `MPC_NAMESPACE`). The host token is *not* read directly here; it comes from `settings.require_host_token()`.
- `BedrockLLMClient.__init__` in `src/model_project_constructor/agents/intake/bedrock_client.py` and in `packages/data-agent/src/model_project_constructor_data_agent/bedrock_client.py` — tests `AWS_BEARER_TOKEN_BEDROCK` for **presence only**, to enforce the optional `require_sigv4=True` guard; the value is never read, and AWS credentials themselves are resolved by the SDK from the credential chain.

The adapters consume tokens via the settings object; their `__init__` signatures take `private_token: str` as a parameter (`PythonGitLabAdapter.__init__` in `src/model_project_constructor/agents/website/gitlab_adapter.py`, `PyGithubAdapter.__init__` in `src/model_project_constructor/agents/website/github_adapter.py`), so a caller must decide how to get the value to them. The example in the docstring shows `os.environ["GITLAB_TOKEN"]`, but the adapter itself has no opinion on where the token came from — a secret manager, a vault agent, or a keychain all work.

### 1.3 Fail-loud helpers

`OrchestratorSettings` is constructable without credentials so tests and preview runs can build a settings object unconditionally. Runners that actually make HTTP calls must guard against missing tokens by calling the require helpers:

```python
# src/model_project_constructor/orchestrator/config.py
def require_host_token(self) -> str:
    """Return the host API token, raising if it is missing.

    Agent runners that actually make HTTP calls to a live host call
    this; test code constructing :class:`OrchestratorSettings`
    without a token does not.
    """

    if not self.host_token:
        var = REPO_PLATFORMS[self.host].token_env_var
        raise ConfigError(
            f"{var} is required for host={self.host!r} but was not set"
        )
    return self.host_token

def require_llm_api_key(self, provider: str = DEFAULT_LLM_PROVIDER) -> str:
    """Return the API key for ``provider``, raising if it is missing."""

    spec = LLM_PROVIDERS.get(provider)
    if spec is None:
        known = ", ".join(sorted(LLM_PROVIDERS))
        raise ConfigError(
            f"Unknown LLM provider {provider!r}. Known providers: {known}."
        )
    if spec.api_key_env_var is None:
        raise ConfigError(
            f"Provider {provider!r} authenticates via the AWS credential "
            f"chain (boto3), not an API-key env var, so require_llm_api_key "
            f"does not apply. Ensure AWS credentials and region are available "
            f"to the boto3 chain (e.g. AWS_REGION, an IAM role, or a profile)."
        )
    key = self.llm_api_keys.get(provider)
    if not key:
        raise ConfigError(f"{spec.api_key_env_var} is required but was not set")
    return key

def require_anthropic_api_key(self) -> str:
    """Back-compat alias for ``require_llm_api_key('anthropic')``."""

    return self.require_llm_api_key("anthropic")
```

Calling these before any network I/O is the operator's responsibility — they are the explicit "I need this now" checkpoint.

Note the consequence for the Bedrock path: **there is deliberately no fail-loud credential checkpoint for `bedrock`.** `require_llm_api_key("bedrock")` raises by design, because `LLM_PROVIDERS["bedrock"].api_key_env_var` is `None` and AWS credentials are self-discovered by the SDK at call time. A missing, expired, or under-scoped IAM role is therefore not detectable at config-load — it surfaces at the first live `messages.create`. Operators wanting an early check must probe the AWS credential chain themselves before starting a run.

### 1.4 What `.env` files look like

The template is at `.env.example`. None of its values are defaults; every credential line is commented out. An operator copies to `.env` (which is gitignored) and fills in the appropriate values for their deployment.

---

## 2. Network boundaries

Outbound network I/O happens from exactly four places.

### 2.1 The LLM provider (Anthropic API or AWS Bedrock)

Both agents that use an LLM call Claude — via Anthropic's first-party API by default, or via AWS Bedrock when the `bedrock` provider is selected:

| Caller | File | Model (default) |
|---|---|---|
| Intake Agent (`provider="anthropic"`) | `DEFAULT_MODEL` in `src/model_project_constructor/agents/intake/anthropic_client.py` | `claude-sonnet-4-6` |
| Data Agent (`provider="anthropic"`) | `DEFAULT_MODEL` in `packages/data-agent/src/model_project_constructor_data_agent/anthropic_client.py` | `claude-sonnet-4-6` |
| Intake Agent (`provider="bedrock"`) | `DEFAULT_MODEL` in `src/model_project_constructor/agents/intake/bedrock_client.py` | `anthropic.claude-opus-4-8` |
| Data Agent (`provider="bedrock"`) | `DEFAULT_MODEL` in `packages/data-agent/src/model_project_constructor_data_agent/bedrock_client.py` | `anthropic.claude-opus-4-8` |

The Bedrock ids carry the `anthropic.` provider prefix; the two default families deliberately diverge because the mantle catalog has no Sonnet tier. Do not treat the first-party default and the Bedrock default as the same id.

The two first-party clients construct `anthropic.Anthropic()` with no explicit args — the SDK picks up `ANTHROPIC_API_KEY` from the environment. All four accept an injected `client` argument so tests can pass a mock, and all four expose a `model` argument for override.

LLM client construction is routed through factory functions (`make_llm_client` in `src/model_project_constructor/agents/intake/factory.py` for Intake; `make_llm_client` in `packages/data-agent/src/model_project_constructor_data_agent/factory.py` for Data Agent) so the provider is named explicitly by callers, and a second LLM backend becomes one new client module plus one branch in the factory — no changes at the call sites. The known-provider list is single-sourced via `Literal` + `get_args`, so unknown-provider errors cannot drift from reality. Two providers are implemented: `"anthropic"` (the first-party API, keyed by `ANTHROPIC_API_KEY`) and `"bedrock"` (AWS-hosted Claude, authenticated by the AWS credential chain rather than an API-key env var — see `src/model_project_constructor/agents/intake/bedrock_client.py` and §1.2 above). Both factories single-source the list from `LLMProvider = Literal["anthropic", "bedrock"]`. The orchestrator's `LLM_PROVIDERS` registry records `bedrock` with `api_key_env_var=None`, so `require_llm_api_key("bedrock")` deliberately raises rather than inventing an env-var key.

**Which agents call Claude (and which do not):**

| Agent | Calls Claude? | `ANTHROPIC_API_KEY` required? |
|---|---|---|
| Intake Agent | Yes | Yes (on the `anthropic` provider) |
| Data Agent | Yes | Yes (on the `anthropic` provider) |
| Website Agent | **No** | **No** |

On the `bedrock` provider `ANTHROPIC_API_KEY` is not required at all — credentials come from the AWS chain instead (§1.2).

Consequence: `ANTHROPIC_API_KEY` is **not** required for website-only runs. The Website Agent operates on the prior agents' artifacts and needs only the git-host token (`GITLAB_TOKEN` or `GITHUB_TOKEN`). Operations recipes that list `ANTHROPIC_API_KEY` as a universal live-run prerequisite are over-specified — see [Evolution](Evolution) (Learning #24, Session 31).

The endpoint depends on the selected provider. With `provider="anthropic"` (the default) the SDK's default endpoint is `https://api.anthropic.com`. With `provider="bedrock"` the traffic goes to the bedrock-mantle endpoint, `https://bedrock-mantle.{region}.api.aws/anthropic`, via `anthropic.AnthropicBedrockMantle` (SigV4 from the AWS credential chain by default, but the locked SDK also accepts a dev-only `AWS_BEARER_TOKEN_BEDROCK` bearer token in its place, which silently overrides SigV4 unless `require_sigv4=True` is passed). Region comes from the `aws_region` argument or, when unset, `AWS_REGION` / `AWS_DEFAULT_REGION`; an unresolved region with no `base_url` override raises `AnthropicError` at construction rather than silently defaulting.

Self-hosting the LLM remains out of scope for the first-party client. `BedrockLLMClient.__init__` (both the intake and data-agent copies) exposes optional `base_url` and `http_client` keyword args so an enterprise deployment can target a PrivateLink VPCE host (when Private DNS is off) or a GovCloud host, and can supply `anthropic.DefaultHttpxClient(proxy=…, verify=<corp CA bundle>)` for a forward proxy / TLS-inspection CA. See `docs/deployment/bedrock-enterprise.md` §4.

Bedrock has **never been exercised live** — every governance and eval result in this project was produced against the `anthropic` provider, and the live eval tier auto-skips `bedrock` for want of credentials. Treat the Bedrock path as implemented-but-unvalidated.

### 2.2 GitLab (`PythonGitLabAdapter`)

`PythonGitLabAdapter` in `src/model_project_constructor/agents/website/gitlab_adapter.py`. Migrated off the `python-gitlab` SDK to direct `httpx` calls against the `/api/v4` REST API in Session 191 (`docs/planning/httpx-adapter-migration.md` Phase 1). Calls:

- `httpx.Client(base_url=f"{host_url}/api/v4", headers={"PRIVATE-TOKEN": ...}, verify=ssl_verify)` (constructed in `PythonGitLabAdapter.__init__`) — no network call at construction; `ssl_verify=True` is the default and not overridden for live runs.
- `GET /groups/{namespace}` — group resolution (namespace URL-encoded so nested group paths address a single path segment).
- `POST /projects` — project creation.
- `GET /projects/{id}` then `POST /projects/{id}/repository/commits` — multi-file commit.

Every non-2xx response or `httpx` transport error (`httpx.HTTPError`) is translated to `RepoClientError`/`RepoNameConflictError`; no raw `httpx` exception escapes the adapter. Target host is whatever `host_url` the caller provides (public `https://gitlab.com` by default; enterprise instances via `MPC_HOST_URL`).

### 2.3 GitHub (`PyGithubAdapter`)

`PyGithubAdapter` in `src/model_project_constructor/agents/website/github_adapter.py`. Calls:

- `Github(auth=Auth.Token(...), base_url=host_url)` (constructed in `PyGithubAdapter.__init__`) — SDK client.
- `get_organization(namespace)` → falls back to `get_user(namespace)` — owner resolution.
- `owner.create_repo(...)` — repo creation (maps visibility to `private` boolean).
- `get_git_ref`, `create_git_blob`, `create_git_tree`, `create_git_commit`, `ref.edit` — git data API walk for a single atomic commit.

Target host is `https://api.github.com` by default; GitHub Enterprise via `MPC_HOST_URL` (e.g., `https://github.example.com/api/v3`).

### 2.4 Database (Data Agent, optional)

`ReadOnlyDB.connect` in `packages/data-agent/src/model_project_constructor_data_agent/db.py` calls `sqlalchemy.create_engine(url)`. The URL is whatever the operator passes to `--db-url` (CLI) or configures at deployment. This is the only DB connection in the project.

If no DB URL is configured, quality checks are generated but not executed — all marked `NOT_EXECUTED`. The DataReport still carries `status="COMPLETE"` with a data-quality concern noting the unreachable database (the module docstring in `packages/data-agent/src/model_project_constructor_data_agent/cli.py`).

### 2.5 What does *not* make network calls

- The intake fixture CLI (`src/model_project_constructor/agents/intake/cli.py`) — replays canned answers, calls no LLM.
- The orchestrator's `src/model_project_constructor/orchestrator/pipeline.py` — pure dispatcher; no I/O of its own.
- `CheckpointStore` — writes to local disk only.
- `FakeRepoClient` — in-memory test double.
- Observability modules (`src/model_project_constructor/orchestrator/logging.py`, `src/model_project_constructor/orchestrator/metrics.py`) — stdlib logging + in-memory counters.

---

## 3. What the LLM sees

### 3.1 Intake Agent

Every LLM call sends:

- One of two system prompts (`SYSTEM_INTERVIEWER` for the interviewer, `SYSTEM_GOVERNANCE` for governance classification, both in `src/model_project_constructor/agents/intake/anthropic_client.py`).
- A user message containing: the domain, the optional `initial_problem`, the full `qa_pairs` history, and the `questions_asked` counter (assembled in `AnthropicLLMClient.next_question` in `src/model_project_constructor/agents/intake/anthropic_client.py`).

**The stakeholder's answers are forwarded verbatim to the configured LLM provider** — Anthropic's API by default, or AWS Bedrock when `provider="bedrock"` (see §2.1). Any PII or confidential claim details included in an answer are transmitted as-is. There is **no redaction, scrubbing, or PII filter in this codebase** — grep for `redact|pii|scrub|mask|sanitize` in `src/` returns zero hits.

Implication for operators: if the interview may contain policyholder-identifying data, the deployment must satisfy the data handling terms of whichever provider it selects (or the interview must be constrained to not elicit PII). See [Anthropic's product terms](https://www.anthropic.com/legal) for current commitments on the first-party path — this project does not re-state them. On the `bedrock` path the counterparty is AWS instead, and the residency geography is whatever `AWS_REGION` selects.

### 3.2 Data Agent

Prompts sent to Anthropic (six `AnthropicLLMClient` methods in `packages/data-agent/src/model_project_constructor_data_agent/anthropic_client.py` — `generate_primary_queries`, `generate_quality_checks`, `summarize`, `generate_datasheet`, `generate_baseline_query`, `rank_candidate_tables`):

- The full `DataRequest` JSON — which includes the `target_description`, `required_features`, `population_filter`, `time_range`, and `database_hint`.
- The generated SQL and quality-check SQL (for the `summarize` and `generate_datasheet` calls).
- **No actual data rows.** The Data Agent asks Claude to *generate* SQL; it does not feed query results back into the LLM.

Observed rule: **`raw_result` (the executed query output) is never sent to Claude.** The `summarize` call receives only quality-check status summaries (`_dump_qc_status` in `packages/data-agent/src/model_project_constructor_data_agent/anthropic_client.py` formats `check_name: execution_status — result_summary`), not row-level data. This is a significant security property — deployments can safely execute queries against sensitive tables knowing the rows themselves never reach the LLM.

### 3.3 Website Agent

Does not call an LLM. It deterministically templates files from the `IntakeReport` and `DataReport` payloads (`src/model_project_constructor/agents/website/templates.py`, `src/model_project_constructor/agents/website/governance_templates.py`). Payload field content (business problem prose, SQL text, etc.) is interpolated into the generated files and committed to the target repo.

---

## 4. Database contract

### 4.1 Read-only is enforced at the credential layer, not in code

`ReadOnlyDB` (in `packages/data-agent/src/model_project_constructor_data_agent/db.py`) does not parse incoming SQL or attempt to reject mutating statements. Its module docstring is explicit (the `§9.1` and `§10` it cites are sections of `docs/architecture-history/architecture-plan.md`, not of this page):

> Read-only enforcement is a database-credential concern in production (§9.1). This wrapper deliberately does not attempt to parse or reject mutating SQL — the Data Agent's LLM is prompted to emit SELECTs, and the pipeline is configured with a SELECT-only role at deployment time. The wrapper's sole job is to surface a clean `DBConnectionError` on connect failure so the graph can take the SKIP_EXECUTION off-ramp described in §10.

**Operator responsibility:** the DB URL passed to `ReadOnlyDB` must be a role/account with `SELECT`-only privileges (and `USAGE` on the relevant schemas). If the LLM misbehaves and generates a `DROP TABLE`, an unrestricted role will execute it. A correctly restricted role will have the statement rejected by the DB. This is a deliberate design choice — defense-in-depth via DB roles is more trustworthy than in-process SQL parsing.

### 4.2 SQL parse-level validation

`validate_sql` in `packages/data-agent/src/model_project_constructor_data_agent/sql_validation.py` runs `sqlparse.parse(sql)` and rejects:

- Empty / whitespace strings.
- Inputs `sqlparse` classifies as `"UNKNOWN"`.
- Inputs `sqlparse` fails to tokenize.

This is a **coarse well-formedness check**, not a security filter. It will not catch a well-formed `DROP TABLE` or a SQL-injection-style concatenation. The module docstring in `packages/data-agent/src/model_project_constructor_data_agent/sql_validation.py` is explicit about this.

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
- **Query result sample rows** — `QualityCheck.raw_result` inside `DataReport.json`. When a DB URL is configured, `make_execute_qc` in `packages/data-agent/src/model_project_constructor_data_agent/nodes.py` populates it with a row count plus the **first five rows** of the result, so real rows from the source tables are written verbatim. `BaselineSnapshot.value` likewise carries a single aggregate read from the baseline query. Treat `$MPC_CHECKPOINT_DIR` as holding production data, not only prose and SQL — see §10 item 7.

What does **not** land on disk:

- **No API tokens** (`GITLAB_TOKEN`, `GITHUB_TOKEN`, `ANTHROPIC_API_KEY`). Envelopes carry payloads, not the orchestrator's configuration.
- **No full query result sets.** `QualityCheck.raw_result` is capped at the first five rows per executed quality check; a complete result set is never persisted. (It does not reach the LLM either — see §3.2 — but it *is* on disk, per the list above.)

### 5.3 Protection

- `.orchestrator/` is in `.gitignore` — checkpoint files are never committed.
- `intake_sessions.db` and its `-shm` / `-wal` siblings are also gitignored.
- `.env` is gitignored.

Filesystem permissions on `$MPC_CHECKPOINT_DIR` are the operator's responsibility — the code does not chmod the directory or files.

---

## 6. Logging

### 6.1 What gets logged

`src/model_project_constructor/orchestrator/logging.py` emits three event types per agent call (`make_logged_runner` in `src/model_project_constructor/orchestrator/logging.py`):

| Event | Level | Context fields |
|---|---|---|
| `agent.start` | INFO | `agent`, `run_id`, `correlation_id` |
| `agent.end` | INFO | plus `duration_ms`, `status` |
| `agent.error` | ERROR | plus `duration_ms`, `error_type`, `error_message` |

### 6.2 Credential exposure

No field in the context dict carries credentials. `agent`, `run_id`, and `correlation_id` are the only bound context. `error_message` is `str(exc)` for whatever exception propagated — in principle, a poorly-written adapter could include a token in an exception message, but the shipped adapters do not.

`error_type` is the exception class name (e.g., `RepoClientError`), not the message — safe by construction.

### 6.3 Log format

The module uses stdlib `logging`. Structured fields land on the record's `extra={"context": ...}` dict. To produce JSON logs, operators install a JSON formatter on the `model_project_constructor.orchestrator` logger namespace (see `OPERATIONS.md` §3.1 for a `python-json-logger` snippet).

Default level is `INFO` via `MPC_LOG_LEVEL`. `DEBUG` is safe — there is no DEBUG-level log that prints tokens or payloads. (Verified by reading every call site in `src/model_project_constructor/orchestrator/logging.py` and `src/model_project_constructor/orchestrator/metrics.py`.)

---

## 7. CI / shared-infrastructure secrets

The project's GitHub Actions workflow (`.github/workflows/ci.yml`) has **no secrets references** — no `${{ secrets.* }}` expressions anywhere. Jobs:

1. `lint` — `uv sync --extra dev && uv run ruff check src/ tests/ packages/ scripts/`.
2. `typecheck` — `uv sync --extra agents --extra ui --extra dev && uv run mypy` (config-driven; `[tool.mypy]` pins the checked packages).
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
| `anthropic[bedrock]>=0.94` | LLM calls (first-party + Bedrock) | Anthropic's official SDK, on the release that ships `AnthropicBedrockMantle`. The `[bedrock]` extra pulls `boto3` / `botocore` for AWS SigV4 signing (`uv.lock`, the `anthropic` package's `[package.optional-dependencies] bedrock` group) — additional transitive trust surface. |
| `sqlparse>=0.5` | Data Agent SQL validation | Parse-level only — no execution. |
| `sqlalchemy>=2.0,<3` | `ReadOnlyDB` | Standard; DB URL is operator-provided. |
| `httpx>=0.27,<1` | GitLab adapter | Direct REST calls (BSD-3-Clause — see [SBOM](Software-Bill-of-Materials)); replaced `python-gitlab` in Session 191. |
| `PyGithub>=2,<3` | GitHub adapter | Official GitHub SDK. (LGPL-3.0-only — see [SBOM](Software-Bill-of-Materials).) |
| `typer>=0.12` | CLIs | Standard. |
| `fastapi>=0.110`, `uvicorn>=0.29`, `sse-starlette>=2` | intake web UI | Only needed for live interviews. |
| `langgraph-checkpoint-sqlite>=2.0,<3` | intake web UI checkpoints | SQLite-backed state persistence for live interviews. |

Full dependency tree including transitives and locked versions is in the [SBOM](Software-Bill-of-Materials).

---

## 10. Known gaps and non-goals

These are explicit design decisions, not bugs.

1. **No in-process SQL filtering.** The Data Agent prompts for SELECTs; safety is a DB-role concern. If you need defense-in-depth, add a proxy that rejects non-SELECTs — do not patch `packages/data-agent/src/model_project_constructor_data_agent/sql_validation.py`.
2. **No PII redaction before LLM calls.** The deployment must satisfy its own data-handling contract with whichever LLM provider it selects — Anthropic on the default path, AWS on the `bedrock` path. This is a policy problem, not a code problem.
3. **No auth on the intake web UI.** `src/model_project_constructor/ui/intake/app.py` serves routes without authentication or authorization middleware. The app is designed to be run behind a reverse proxy that handles auth (corporate SSO, OAuth proxy, etc.). Running it as-is on a public interface would expose the interview surface to anyone who can reach it.
4. **No rate limiting** on adapter calls or LLM calls. The SDKs will surface provider-side rate limit errors; this project does not add its own limiter.
5. **No retry budget for network calls.** The Website Agent's LangGraph has a bounded retry loop for commit failures (the `RETRY_BACKOFF` self-loop off `INITIAL_COMMITS`, bounded by `MAX_COMMIT_ATTEMPTS` and `RETRY_BASE_DELAY_SECONDS` in `src/model_project_constructor/agents/website/state.py`), but neither the adapters nor the LLM clients retry on their own. Transient failures bubble up as halt conditions.
6. **No audit log.** Logging is observability, not immutable audit. If you need a compliance-grade audit trail, ship the structured log events to a WORM-capable store; do not rely on in-process logging alone.
7. **Checkpoint files are world-readable by default.** Filesystem permissions are not managed by the code. If `$MPC_CHECKPOINT_DIR` sits on a shared filesystem, apply group/mode restrictions before running production interviews.
8. **LLM model ID is unverified at construction.** The default `claude-sonnet-4-6` is chosen from the session-time model family list (the module docstring in `src/model_project_constructor/agents/intake/anthropic_client.py`). First live invocation will raise from the Anthropic SDK if the ID is wrong — this is a deliberate trade-off to avoid coupling the import path to a network probe.

---

## 11. Checklist for a security review

- [ ] Confirm `.env` and `$MPC_CHECKPOINT_DIR` are on appropriately-permissioned storage.
- [ ] Confirm the Data Agent's DB role is `SELECT`-only on the intended schemas.
- [ ] Confirm the intake web UI, if deployed, sits behind an authenticating reverse proxy.
- [ ] Confirm the selected provider's data handling terms are compatible with the content interviewers will elicit — Anthropic's on the default path, AWS's on the `bedrock` path.
- [ ] Confirm the target `GITLAB_TOKEN` / `GITHUB_TOKEN` has the minimum required scope (no broader than `api` / `repo`).
- [ ] Confirm CI does not inject real credentials into the `.github/workflows/ci.yml` jobs.
- [ ] Review the [SBOM](Software-Bill-of-Materials) for unacceptable license profiles — the full per-dependency license table is `THIRD-PARTY-LICENSES` at the repository root; **one** direct dependency is LGPL-3.0 (`PyGithub`; `python-gitlab` was removed in Session 191).
- [ ] Decide whether checkpoint files must be encrypted at rest (this project does not encrypt them).
- [ ] Decide whether LLM call metadata should be forwarded to a SIEM (structured logging makes this straightforward).
- [ ] If the `bedrock` provider is selected (`--provider bedrock` on the CLIs, or `INTAKE_LLM_PROVIDER=bedrock` for the web UI): confirm the execution role's policy is least-privilege **and matches the endpoint in use**. The client is `AnthropicBedrockMantle`, which authorizes on `bedrock-mantle:CreateInference` (plus `aws-marketplace:ViewSubscriptions`) — a *different action namespace* from the classic `bedrock:InvokeModel` path, so a role scoped only to `bedrock:*` will 403 the mantle client. See `docs/deployment/bedrock-enterprise.md` §3.
- [ ] If the `bedrock` provider is selected: confirm `AWS_BEARER_TOKEN_BEDROCK` is **unset** in the production profile. At the locked SDK version `anthropic.AnthropicBedrockMantle` switches to bearer auth when it is set, silently bypassing the IAM role. Construct `BedrockLLMClient(require_sigv4=True)` to turn a stray token into a hard `ValueError` — it defaults to `False`, so the environment is the only control unless the caller opts in.
- [ ] If the `bedrock` provider is selected: confirm `AWS_REGION` satisfies data residency (Regional vs Global endpoint — Global routing is a residency violation for regulated P&C data), and enable Bedrock model-invocation logging if prompts/responses need an audit surface — it is off by default. See `docs/deployment/bedrock-enterprise.md` §5, §6.

---

## 12. Key files

| File | Security surface |
|---|---|
| `src/model_project_constructor/orchestrator/config.py` | Env-var loader, `require_*` guards |
| `.env.example` | Complete env-var template |
| `OPERATIONS.md` | Env-var reference, deployment recipes |
| `src/model_project_constructor/agents/intake/anthropic_client.py` | Intake LLM prompts + SDK construction |
| `packages/data-agent/src/model_project_constructor_data_agent/anthropic_client.py` | Data Agent LLM prompts + SDK construction |
| `src/model_project_constructor/agents/intake/factory.py` | Provider seam — which LLM backend (and therefore which auth mechanism) a run selects |
| `src/model_project_constructor/agents/intake/bedrock_client.py` | Bedrock (AWS) auth surface — SigV4 from the AWS credential chain, with a dev-only `AWS_BEARER_TOKEN_BEDROCK` bearer mode that silently overrides it unless `require_sigv4=True`; also the `base_url` / `http_client` network hooks |
| `packages/data-agent/src/model_project_constructor_data_agent/bedrock_client.py` | Same, for the standalone Data Agent wheel |
| `docs/deployment/bedrock-enterprise.md` | Enterprise Bedrock deployment: least-privilege IAM policy, PrivateLink, data residency, model-invocation logging |
| `src/model_project_constructor/agents/website/gitlab_adapter.py` | GitLab network boundary |
| `src/model_project_constructor/agents/website/github_adapter.py` | GitHub network boundary |
| `packages/data-agent/src/model_project_constructor_data_agent/db.py` | Database connection layer + read-only contract |
| `packages/data-agent/src/model_project_constructor_data_agent/sql_validation.py` | SQL parse-level check (not a security filter) |
| `src/model_project_constructor/orchestrator/logging.py` | Structured log events |
| `src/model_project_constructor/orchestrator/checkpoints.py` | On-disk envelope storage |
| `.github/workflows/ci.yml` | CI pipeline (no secrets) |
| `.gitignore` | `.env`, `.orchestrator/`, `intake_sessions.db*` excluded |
