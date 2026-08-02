# Extending the Pipeline

The pipeline has five designed extension surfaces: **adding a new agent**, **adding a new repository-host adapter**, **adding a new governance artifact**, **adding a new regulatory framework**, and **adding a new LLM provider**. Each surface has an explicit boundary — a `Protocol`, a registry, a tier-gate function, or a provider factory — so extensions don't require re-reading the entire codebase.

This page documents the shape of each change, the files to edit, and the tests that enforce the contract.

---

## 1. The envelope contract

Every extension ultimately flows through the same transport: the `HandoffEnvelope`. From `HandoffEnvelope` in `src/model_project_constructor/schemas/envelope.py`:

```python
class HandoffEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")

    envelope_version: Literal["1.0.0"] = "1.0.0"
    run_id: str
    source_agent: Literal["intake", "data", "website", "orchestrator"]
    target_agent: Literal["intake", "data", "website"]
    payload_type: str
    payload_schema_version: str
    payload: dict[str, Any]
    created_at: datetime
    correlation_id: str
```

The `envelope_version` evolves independently from payload schemas. Payloads are carried as `dict[str, Any]` and resolved to concrete Pydantic models via the registry.

### The schema registry

`REGISTRY` in `src/model_project_constructor/schemas/registry.py`:

```python
REGISTRY: dict[SchemaKey, type[BaseModel]] = {
    ("IntakeReport", "1.0.0"): v1.IntakeReport,
    ("DataRequest", "1.0.0"): v1.DataRequest,
    ("DataReport", "1.0.0"): v1.DataReport,
    ("RepoTarget", "1.0.0"): v1.RepoTarget,
    ("RepoProjectResult", "1.0.0"): v1.RepoProjectResult,
}
```

`load_payload(envelope)` in `src/model_project_constructor/schemas/registry.py` looks up `(payload_type, payload_schema_version)` and validates `envelope.payload` against the matching class. Unknown keys raise `UnknownPayloadError`.

The registry module docstring (in `src/model_project_constructor/schemas/registry.py`) codifies the versioning policy. Versioning is intentionally minimal today — only `1.0.0` exists and there is no migration machinery — but the registry keys on `(payload_type, schema_version)`, so versions can coexist once a second is added:

- **Minor bump** (1.0.0 → 1.1.0, backwards-compatible additions): register the new class under its new version and keep 1.0.0.
- **Major bump** (1.0.0 → 2.0.0): register v2, keep v1 for at least two major releases, and add whatever migration the change needs at that point. There is no `schemas/migrations/` package today.

---

## 2. Extension surface: adding a new agent

Use case: insert an agent between existing stages (e.g., a dedicated *feature-engineering-review* agent between Data and Website), or add an agent outside the three-stage pipeline entirely.

### Files to add or edit

| # | File | Change shape |
|---|---|---|
| 1 | `src/model_project_constructor/schemas/v1/<new>.py` | Define the payload Pydantic class. Include `schema_version: Literal["1.0.0"]`, set `model_config = ConfigDict(extra="forbid", protected_namespaces=())`. |
| 2 | `src/model_project_constructor/schemas/v1/__init__.py` | Export the new class. |
| 3 | `REGISTRY` in `src/model_project_constructor/schemas/registry.py` | Add a tuple entry `("<PayloadType>", "1.0.0"): v1.<PayloadType>`. |
| 4 | `HandoffEnvelope.source_agent` / `target_agent` in `src/model_project_constructor/schemas/envelope.py` | If the new agent needs to be named in envelopes, add its string to the `source_agent` and/or `target_agent` `Literal[...]` union. |
| 5 | `src/model_project_constructor/agents/<new>/` | Implement the agent. Follow the existing package structure: `agent.py` (public entry point), `state.py` (LangGraph state), `nodes.py` (graph nodes), plus any auxiliary modules. |
| 6 | `IntakeRunner` / `DataRunner` / `WebsiteRunner` in `src/model_project_constructor/orchestrator/pipeline.py` | Declare the runner type alias alongside the existing ones. Existing runners: `IntakeRunner = Callable[[], IntakeReport]`, `DataRunner = Callable[[DataRequest], DataReport]`, `WebsiteRunner = Callable[[IntakeReport, DataReport, RepoTarget], RepoProjectResult]`. |
| 7 | `src/model_project_constructor/orchestrator/pipeline.py` | Thread the new runner through `run_pipeline(...)` with `FAILED_AT_<STAGE>` handling that mirrors the existing data/website halt paths. |
| 8 | `tests/agents/<new>/` | Mirror the test layout of `tests/agents/intake/` or `tests/agents/data/`. Contract tests: (a) agent handles malformed input without raising uncaught exceptions, (b) output validates against the new schema, (c) one end-to-end happy-path test. |

### Key invariants to preserve

- **Every hop writes a checkpoint.** The orchestrator persists each agent's output via `CheckpointStore` in `src/model_project_constructor/orchestrator/checkpoints.py` before invoking the next stage.
- **No shared state.** The new agent receives only what is in the envelope — no global config, no module-level caches leaking between runs. See `tests/test_data_agent_decoupling.py`, which AST-walks the Data Agent package to enforce zero intake-schema imports.
- **Status vocabulary.** Terminal statuses use `COMPLETE` / `FAILED_AT_<STAGE>` (see `PipelineStatus` in `src/model_project_constructor/orchestrator/pipeline.py`). A new stage adds a new `FAILED_AT_<NEW>` value.

---

## 3. Extension surface: adding a new repo-host adapter

Use case: support a third forge (e.g., Bitbucket, Gitea, self-hosted Forgejo). The Website Agent talks to the host exclusively through the `RepoClient` `Protocol`.

### The protocol

`RepoClient` in `src/model_project_constructor/agents/website/protocol.py`:

```python
class RepoClient(Protocol):
    def create_project(
        self,
        *,
        namespace: str,
        name: str,
        visibility: str,
    ) -> ProjectInfo: ...

    def commit_files(
        self,
        *,
        project_id: str,
        branch: str,
        files: dict[str, str],
        message: str,
    ) -> CommitInfo: ...
```

`ProjectInfo` (`src/model_project_constructor/agents/website/protocol.py`) carries `id: str`, `url: str`, `default_branch: str`. The `id` is host-opaque — GitLab uses a stringified integer, GitHub uses `"owner/name"`. Callers treat it as a token and pass it back unchanged.

`CommitInfo` (`src/model_project_constructor/agents/website/protocol.py`) carries `sha: str` and `files_committed: list[str]`.

### Error contract

`RepoClientError` / `RepoNameConflictError` in `src/model_project_constructor/agents/website/protocol.py`:

- `RepoClientError` — base class for any host-side failure the agent handles.
- `RepoNameConflictError` — **must** be raised when `create_project` collides with an existing project name. The Website Agent's graph handles this explicitly (retries with a mangled slug up to the retry budget).

Any other failure should be wrapped as `RepoClientError`; raw library exceptions should not leak into the agent's nodes.

### Adapter template

The existing adapters illustrate the template:

| Adapter | Module | Constructor signature |
|---|---|---|
| `GitLabAdapter` | `src/model_project_constructor/agents/website/gitlab_adapter.py` | `__init__(*, host_url: str, private_token: str, ssl_verify: bool = True)` |
| `GitHubAdapter` | `src/model_project_constructor/agents/website/github_adapter.py` | `__init__(*, private_token: str, host_url: str = "https://api.github.com")` |

Each class is roughly ~120 lines, implements exactly `create_project` and `commit_files`, maps host-library exceptions to `RepoClientError` / `RepoNameConflictError`, and is kwarg-only on construction.

### Files to add or edit

1. **New module** `src/model_project_constructor/agents/website/<host>_adapter.py` — implement `create_project` and `commit_files`, translate host exceptions.
2. **Re-export** in `src/model_project_constructor/agents/website/__init__.py` — mirror the existing `GitLabAdapter` / `GitHubAdapter` re-export.
3. **Optional dependency** in the top-level `pyproject.toml` under the `agents` extra — add the host's Python SDK (e.g., `atlassian-python-api` for Bitbucket).
4. **Tests** in `tests/agents/website/test_<host>_adapter.py` — follow the pattern of `tests/agents/website/test_github_adapter.py` and `tests/agents/website/test_gitlab_adapter.py`:
   - Import-level check (module loads, class has both Protocol methods).
   - Constructor does no network I/O.
   - Exception classification — host-specific failures map to the right `Repo*Error` subclass.
   - `MagicMock`-based happy path for `create_project` and `commit_files`.
5. **Generated-project CI template** in `src/model_project_constructor/agents/website/governance_templates.py` — if the new host has a distinct CI system, add a `render_<host>_ci()` function alongside `render_gitlab_ci()` and `render_github_actions_ci()`, and widen the `ci_platform` dispatch in `build_governance_files` (`src/model_project_constructor/agents/website/governance_templates.py`).

### Wiring and selection

Adapter selection is driven by the `REPO_PLATFORMS` registry in `src/model_project_constructor/orchestrator/config.py`. Each `PlatformSpec` carries an `adapter_factory: Callable[..., RepoClient]` (in `src/model_project_constructor/orchestrator/config.py`) that lazy-imports its SDK and constructs the adapter via the uniform `(*, host_url, private_token)` signature. Both live entry points build the client the same way — `client = REPO_PLATFORMS[host].adapter_factory(host_url=..., private_token=...)` (`build_website_runner` in `scripts/run_pipeline.py` and the `run` command in `src/model_project_constructor/agents/website/cli.py`); there is no if/elif `--host` dispatch.

To add a host you do **not** edit a selection code path: add one `PlatformSpec` entry to `REPO_PLATFORMS` (with `default_api_url`, `token_env_var`, and a `_make_<host>_adapter` factory) and add the host string to the `HostLiteral` alias (the import-time `assert_vocab_parity` guard in `src/model_project_constructor/orchestrator/config.py` pins the two together). `VALID_HOSTS` (in `src/model_project_constructor/agents/website/cli.py`) and the pipeline argparse `choices` (the `main` function in `scripts/run_pipeline.py`) are already derived from `REPO_PLATFORMS`, so they update automatically. The Website Agent still receives the constructed `RepoClient` directly from its caller — see `src/model_project_constructor/agents/website/agent.py`.

> Note: `run_pipeline.build_repo_target` retains a `host == "github"` branch (in `scripts/run_pipeline.py`), but that selects the default *namespace* (deployment policy), not the adapter.

---

## 4. Extension surface: adding a new governance artifact

Use case: your organization needs an artifact type that isn't currently emitted (e.g., "Fair-lending impact statement", "Post-market monitoring plan").

### How tier gating works

The `build_governance_files` function in `src/model_project_constructor/agents/website/governance_templates.py` reads:

```python
governance = intake.get("governance") or {}
risk_tier = str(governance.get("risk_tier", "tier_4_low"))
affects_consumers = bool(governance.get("affects_consumers", False))
```

Artifacts are emitted in nested blocks by tier severity (lower number = more severe):

- **Always emitted:** `governance/model_registry.json`, `governance/model_card.md`, `governance/change_log.md`, CI config (`.gitlab-ci.yml` *or* `.github/workflows/ci.yml`), `.pre-commit-config.yaml`, plus one `data/datasheet_<query>.md` per primary query.
- **Tier 3+:** `governance/three_pillar_validation.md`, `governance/ongoing_monitoring.md`, `governance/deployment_gates.md`.
- **Tier 2+:** `governance/impact_assessment.md`, `governance/regulatory_mapping.md`.
- **Tier 1 only:** `governance/lcp_integration.md`, `governance/audit_log/README.md`.
- **Consumer-facing** (`affects_consumers=true`): `governance/eu_ai_act_compliance.md`.
- **Protected attributes** (`uses_protected_attributes=true`): `build_analysis_files` and `build_test_files` add `analysis/fairness_audit.qmd`, `src/<slug>/fairness/__init__.py`, `src/<slug>/fairness/audit.py`, `tests/test_fairness.py`.

The severity comparison uses `_tier_at_least` in `src/model_project_constructor/agents/website/governance_templates.py`, which maps tier strings to ordinal severities.

### Files to add or edit

1. **Write the renderer** in `src/model_project_constructor/agents/website/governance_templates.py`. Convention: `render_<artifact_name>(*, intake: dict[str, Any], ...) -> str` returning the markdown body.
2. **Wire into `build_governance_files`** at the correct tier block (in `src/model_project_constructor/agents/website/governance_templates.py`). Choose the narrowest gate that correctly describes when the artifact is required.
3. **Update `is_governance_artifact`** in `src/model_project_constructor/agents/website/governance_templates.py` so the classifier recognizes the new file path. This is the single source of truth for `GovernanceManifest.artifacts_created` — do not also record the path in state.
4. **Add a positive *and* negative test** in `tests/agents/website/test_governance.py`. Per this project's learning #5: assert the artifact appears at the intended tier *and* does not appear at lower tiers. A positive-only test passes silently if a tier starts emitting the wrong artifact.
5. **If the artifact is a `.qmd` narrative** that needs to be rendered into the project, add it to `build_analysis_files` instead of `build_governance_files` and wire its emission to the appropriate governance flag.

### No envelope or registry changes required

Governance artifacts are a content-generation concern internal to the Website Agent. They do not flow across agent boundaries, so they do not require a new schema, registry entry, or envelope update.

---

## 5. Extension surface: adding a new regulatory framework

Use case: your jurisdiction requires a framework not currently supported (e.g., UK FCA CP23/17, Singapore MAS FEAT).

### Current framework registry

`_FRAMEWORK_ARTIFACTS` in `src/model_project_constructor/agents/website/governance_templates.py`:

```python
_FRAMEWORK_ARTIFACTS: dict[str, list[str]] = {
    "SR_26_2": [
        "governance/model_card.md",
        "governance/three_pillar_validation.md",
        "governance/ongoing_monitoring.md",
        "governance/change_log.md",
    ],
    "NAIC_AIS": [
        "governance/model_card.md",
        "governance/impact_assessment.md",
        "governance/regulatory_mapping.md",
        "governance/change_log.md",
    ],
    "EU_AI_ACT_ART_9": [
        "governance/eu_ai_act_compliance.md",
        "governance/impact_assessment.md",
        "governance/regulatory_mapping.md",
    ],
    "GDPR_ART_22": [
        "governance/eu_ai_act_compliance.md",
        "governance/impact_assessment.md",
        "governance/regulatory_mapping.md",
    ],
    "ASOP_56": [
        "governance/model_card.md",
        "governance/three_pillar_validation.md",
    ],
}
```

At render time, `build_regulatory_mapping` in `src/model_project_constructor/agents/website/governance_templates.py` intersects each declared framework's artifact list with the actually-emitted paths for this run — so the `regulatory_mapping.md` content only claims coverage for artifacts that were in fact generated.

### Files to add or edit

1. **Add an entry** to `_FRAMEWORK_ARTIFACTS` mapping the new framework's identifier string to the list of artifact paths it requires. Identifiers follow the convention `<JURISDICTION>_<CODE>` (e.g., `FCA_CP23_17`).
2. **If the framework requires a new artifact type**, add it per §4 above *before* referencing it here.
3. **Update the `IntakeReport` schema documentation** to note the new framework identifier. The schema itself does not validate framework strings (it stores them as `list[str]`), but the intake agent's system prompt in `src/model_project_constructor/agents/intake/anthropic_client.py` enumerates known frameworks — add the new string to that enumeration so the agent will suggest it. This edit and step 1 are **not** independent: a CI parity guard pins the prompt enumeration and `_FRAMEWORK_ARTIFACTS` equal (see *Invariants enforced by tests* below), so doing one without the other fails the build.
4. **Test coverage** in `tests/agents/website/test_governance.py`:
   - Assert `build_regulatory_mapping` includes the new framework when declared in intake.
   - Assert the mapping intersects correctly with emitted artifacts (a framework mapped to an un-emitted artifact must not falsely appear in the manifest).

### No adapter or pipeline changes required

Framework additions are pure content. They flow through `IntakeReport.governance.regulatory_frameworks` → `build_regulatory_mapping` → `governance/regulatory_mapping.md` in the generated project. Nothing in the orchestrator, the envelope, or the adapter layer needs to change.

---

## 6. Extension surface: adding a new LLM provider

Use case: route the agents to a further LLM backend (e.g., an OpenAI-compatible endpoint, a self-hosted model) without editing any call site. Three providers already ship — `anthropic`, `bedrock` (AWS Bedrock-hosted Claude, added Session 162), and `opencode` (the `opencode` CLI driven as a subprocess, added Session 213) — so the recipe below has been executed for real twice, not merely designed. (Neither non-default client has been exercised live: `bedrock` has never reached a live endpoint, and `opencode`'s output quality is unmeasured.) Each agent talks to its LLM only through a `Protocol`, and the provider choice flows through a small **factory** — a `Protocol` + factory boundary, analogous to (but separate from) the `RepoClient` `Protocol` used for repo-host adapters in §3.

### Two parallel factories (not shared)

There are **two** `make_llm_client` factories — one per agent — and they are deliberately kept separate because the intake and data-agent clients share no methods and live in different packages (the data agent ships as a standalone wheel with a decoupling boundary, enforced by `tests/test_data_agent_decoupling.py`):

| Agent | Factory module | Protocol it returns |
|---|---|---|
| Intake | `src/model_project_constructor/agents/intake/factory.py` | `IntakeLLMClient` (`src/model_project_constructor/agents/intake/protocol.py`) |
| Data | `packages/data-agent/src/model_project_constructor_data_agent/factory.py` | `LLMClient` (`packages/data-agent/src/model_project_constructor_data_agent/llm.py`) |

Both factories have the same shape:

```python
# agents/intake/factory.py (the data-agent factory mirrors this)
LLMProvider = Literal["anthropic", "bedrock", "opencode"]
KNOWN_PROVIDERS: tuple[str, ...] = get_args(LLMProvider)

def make_llm_client(
    provider: str = "anthropic",
    *,
    model: str | None = None,
) -> IntakeLLMClient:
    if provider == "anthropic":
        # Lazy import keeps this module — and anything that re-exports it —
        # free of the anthropic SDK at import time.
        from model_project_constructor.agents.intake.anthropic_client import (
            DEFAULT_MODEL,
            AnthropicLLMClient,
        )
        return AnthropicLLMClient(model=DEFAULT_MODEL if model is None else model)
    if provider == "bedrock":
        # Same lazy-import rationale. BedrockLLMClient is a thin subclass of
        # AnthropicLLMClient pointed at AWS Bedrock; AWS credentials are
        # self-discovered by the SDK.
        from model_project_constructor.agents.intake.bedrock_client import (
            DEFAULT_MODEL,
            BedrockLLMClient,
        )
        return BedrockLLMClient(model=DEFAULT_MODEL if model is None else model)
    if provider == "opencode":
        # Same lazy-import convention even though this client imports no SDK
        # at all. Its DEFAULT_MODEL is None (the operator's own OpenCode
        # config picks the vendor), which is str | None where the siblings'
        # are str — hence the import alias: all branches share one function
        # scope, so importing the bare name twice is a type conflict.
        from model_project_constructor.agents.intake.opencode_client import (
            DEFAULT_MODEL as OPENCODE_DEFAULT_MODEL,
        )
        from model_project_constructor.agents.intake.opencode_client import (
            OpenCodeLLMClient,
        )
        return OpenCodeLLMClient(
            model=OPENCODE_DEFAULT_MODEL if model is None else model
        )
    raise ValueError(
        f"Unknown LLM provider {provider!r}. "
        f"Known providers: {', '.join(KNOWN_PROVIDERS)}."
    )
```

Two conventions make this surface safe:

- **The known-provider list is single-sourced.** `KNOWN_PROVIDERS` is derived from the `LLMProvider` `Literal` via `typing.get_args`, so the unknown-provider `ValueError` (and the data-agent CLI's `--provider` help) cannot drift from the set the factory actually handles. `provider` is typed `str`, not `LLMProvider`, because the value usually arrives from a CLI flag.
- **The concrete client is lazy-imported inside the branch.** Importing the factory (or the package `__init__` that re-exports it) never pulls in the `anthropic` SDK — nor `boto3`/`botocore`, which the Bedrock client needs; the SDKs are imported only when a real client is constructed, and each package's factory test asserts none of them is present at factory-import time. A new provider's client module must follow the same lazy-import convention.

### Files to add or edit (in BOTH packages, plus one orchestrator entry)

Steps 1-3 are the same three-step recipe applied independently to each agent; step 4 is done once:

1. **New client module** implementing the agent's protocol — `IntakeLLMClient` for intake (mirror `src/model_project_constructor/agents/intake/anthropic_client.py`) and `LLMClient` for the data agent (mirror `packages/data-agent/src/model_project_constructor_data_agent/anthropic_client.py`). Expose a `DEFAULT_MODEL` constant and accept `model=` as a keyword argument, as the existing Anthropic clients do. **Prefer subclassing `AnthropicLLMClient` and overriding only the transport method** — see "Transport override" below; both shipped non-default providers do this, and it is what keeps the prompts from drifting between providers.
2. **One branch** in that package's `make_llm_client`, lazy-importing the new client.
3. **One member** in that package's `LLMProvider` `Literal` (which automatically updates `KNOWN_PROVIDERS`, the error message, and the data-agent CLI help).
4. **One entry** in the orchestrator's `LLM_PROVIDERS` registry (`src/model_project_constructor/orchestrator/config.py`) — done once, not per package, since the standalone wheel cannot import the orchestrator (C4). Map the provider name to an `LLMProviderSpec`, setting `api_key_env_var` to the env var carrying its credential, or `None` when the provider authenticates by another mechanism (as `bedrock` does, via the AWS credential chain). `OrchestratorSettings.require_llm_api_key` rejects any provider missing from this registry; unlike `REPO_PLATFORMS`/`HostLiteral` there is **no** import-time parity guard tying it to the agents' `LLMProvider` `Literal`s — the module comment explains why — so the lockstep is a documented convention you must keep by hand.

### Transport override: write a transport, not a client

Both non-default providers subclass their package's `AnthropicLLMClient` and replace **one** method rather than implementing the protocol afresh:

| Provider | What it overrides | What it inherits |
|---|---|---|
| `bedrock` | `__init__` and `DEFAULT_MODEL` | everything else — the SDK's Bedrock client is signature-identical to the base one |
| `opencode` | `__init__` plus the single transport method — `_call_json` (intake, returns parsed JSON) or `_call_claude` (data agent, returns raw text) | all four interview methods / all six generation methods, every prompt, every JSON-shape instruction, the dataclass builders, and `_extract_json` |

**Why this is the recommended shape.** The prompts are the expensive, hard-to-review part of each client, and duplicating them per provider is how prompt drift starts. The `_extract_json` twins in this project drifted once and cost three sessions to repair — so the rule is: if your backend can be reached by replacing the transport, replace only the transport. Note the seams are deliberately **asymmetric** — the intake transport returns parsed JSON, the data agent's returns raw text — because each package's methods expect that; match your package's, don't unify them.

The naming consequence is worth stating so nobody "fixes" it: a client class may inherit from `AnthropicLLMClient` while talking to a different vendor entirely. The base class is this project's *prompt-and-parse* layer that happens to carry an Anthropic transport; the subclass replaces the transport.

### Variant: driving an external CLI as the transport (the `opencode` pattern)

If the backend is a command-line agent rather than an HTTP API, the recipe is unchanged but the client carries obligations an SDK client does not. Read `src/model_project_constructor/agents/intake/opencode_client.py` as the worked example; its module docstring records why each of these exists.

- **Fail fast at construction, not mid-run.** Check the executable is on `PATH` in `__init__` and raise the seam's own error type with an install hint. A missing binary discovered halfway through an interview is a much worse failure than one discovered at startup.
- **Never put the prompt in `argv`.** Interview transcripts contain stakeholder text; command lines are world-readable via the process table. Write the prompt to the child's **stdin**, and pass it as an input string so the pipe is opened and closed for you — an inherited stdin will hang until your timeout with no output.
- **Always set a timeout**, and map its expiry onto the seam's error type like any other transport failure.
- **Assume the tool is agentic until proven otherwise.** A coding CLI may read files, run commands, or take multiple steps before answering. Give it an ephemeral working directory it cannot escape *and* an explicit tool-denying configuration — do not rely on a documented "safe default" without verifying it, which is precisely the assumption that proved false here. Never pass a flag that auto-approves tool use, and pin that with a negative test.
- **Extract the answer, don't concatenate the stream.** A multi-step run emits narration before the answer ("I'll list the files…"), so naive concatenation of every text event returns narration plus answer. Take the text of the final step that stopped cleanly.
- **Diagnose "the tool rejected our invocation" separately from "the model failed."** A malformed configuration file that *you* generated typically surfaces as usage help on stderr with empty stdout and a non-zero exit — that is your bug, and the error message should say so rather than blaming the provider.
- **Pin the output schema with committed fixtures captured verbatim from a known binary version**, and record that version in your error text. CLI tools ship far more often than SDKs; when a fixture-backed test fails after an upgrade, treat it as a schema change and re-capture rather than editing the fixture to match.
- **Duplicated helpers need a parity guard in the same commit that creates them.** The standalone wheel cannot import the orchestrator, so a subprocess client's stream-parsing helpers must exist in both packages. Write the behavioural battery immediately — and include at least one test that pins the *rule* rather than only the sameness, because a sameness-only battery is blind to a bug both copies share.

### Provider-selection surfaces

The provider is selectable in three places, all defaulting to `anthropic`:

- **`scripts/run_pipeline.py`** (`--provider`, in `main` of `scripts/run_pipeline.py`) — applies to the intake **and** data agents when `--llm` is `data` or `both` (ignored when `--llm=none`); it routes through each agent's `make_llm_client` factory.
- **The data-agent CLI** (`model-data-agent`, the `run` and `discover` commands in `packages/data-agent/src/model_project_constructor_data_agent/cli.py`) — `--provider` whose help text is `_PROVIDER_HELP`, generated from `KNOWN_PROVIDERS`.
- **The intake web UI** (`create_app` in `src/model_project_constructor/ui/intake/app.py`) — not a CLI flag, but the same seam: the provider resolves from the `create_app(provider=...)` argument, then the `INTAKE_LLM_PROVIDER` env var, then `DEFAULT_LLM_PROVIDER`, and an unknown value raises at app construction listing `KNOWN_PROVIDERS`. The model override (`INTAKE_LLM_MODEL`) defaults to `None` on purpose, so each provider's own `DEFAULT_MODEL` wins.


---

## Invariants enforced by tests

Several extension surfaces have mechanical guards that will fail CI if the contract is broken:

| Invariant | Test | What it checks |
|---|---|---|
| Data Agent has zero intake-schema imports | `tests/test_data_agent_decoupling.py` | AST-walks the standalone data-agent package and the main-package shims; asserts no imports reference the intake schema (architecture-plan §7, constraint C4). |
| Every schema in `REGISTRY` round-trips | `tests/schemas/test_envelope_and_registry.py` | For each `(payload_type, version)` key, constructs an envelope, calls `load_payload`, and asserts equality. |
| Every governance artifact path is classified | `tests/agents/website/test_governance.py` | Asserts `is_governance_artifact` returns `True` for every path emitted by `build_governance_files` / `build_analysis_files` / `build_test_files` across all tier/flag combinations. |
| Tier gating is positive *and* negative | `tests/agents/website/test_governance.py` | Per-tier fan-out asserts both `"governance/<artifact>.md" in files` for the correct tier *and* `... not in files` for lower tiers. |
| Framework vocabulary parity | `tests/agents/website/test_governance.py` | `TestFrameworkPromptMapParity` asserts `set(anthropic_client.GOVERNANCE_FRAMEWORKS) == set(governance_templates._FRAMEWORK_ARTIFACTS)`, and separately that every prompted framework maps to a *non-empty* artifact list — so a framework the intake prompt is told to suggest can never scaffold zero governance artifacts (the Audit #39 hole). |

An extension that breaks any of these invariants is rejected at CI, not in production.

---

## See also

- [Schema Reference](Schema-Reference) — field-by-field Pydantic definitions including the `HandoffEnvelope`
- [Governance Framework](Governance-Framework) — risk tiers and the regulatory mapping table
- [Agent Reference](Agent-Reference) — per-agent inputs, outputs, and failure modes
- [Architecture Decisions](Architecture-Decisions) — AD-1 through AD-10, the design tradeoffs behind these extension points
- [Contributing](Contributing) — code-quality gates, CI, and the commit convention to follow when submitting an extension
