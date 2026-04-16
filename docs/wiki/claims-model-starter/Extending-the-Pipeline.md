# Extending the Pipeline

The pipeline has four designed extension surfaces: **adding a new agent**, **adding a new repository-host adapter**, **adding a new governance artifact**, and **adding a new regulatory framework**. Each surface has an explicit boundary — a `Protocol`, a registry, or a tier-gate function — so extensions don't require re-reading the entire codebase.

This page documents the shape of each change, the files to edit, and the tests that enforce the contract.

---

## 1. The envelope contract

Every extension ultimately flows through the same transport: the `HandoffEnvelope`. From `src/model_project_constructor/schemas/envelope.py:20-33`:

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

`src/model_project_constructor/schemas/registry.py:26-32`:

```python
REGISTRY: dict[SchemaKey, type[BaseModel]] = {
    ("IntakeReport", "1.0.0"): v1.IntakeReport,
    ("DataRequest", "1.0.0"): v1.DataRequest,
    ("DataReport", "1.0.0"): v1.DataReport,
    ("RepoTarget", "1.0.0"): v1.RepoTarget,
    ("RepoProjectResult", "1.0.0"): v1.RepoProjectResult,
}
```

`load_payload(envelope)` at `registry.py:39-58` looks up `(payload_type, payload_schema_version)` and validates `envelope.payload` against the matching class. Unknown keys raise `UnknownPayloadError`.

The registry docstring (`registry.py:7-13`) codifies the versioning policy:

- **Minor bump** (1.0.0 → 1.1.0, backwards-compatible additions): register the new class under its new version and keep 1.0.0.
- **Major bump** (1.0.0 → 2.0.0): register v2, keep v1 for at least two major releases, provide a migration function in `schemas/migrations/`.

---

## 2. Extension surface: adding a new agent

Use case: insert an agent between existing stages (e.g., a dedicated *feature-engineering-review* agent between Data and Website), or add an agent outside the three-stage pipeline entirely.

### Files to add or edit

| # | File | Change shape |
|---|---|---|
| 1 | `src/model_project_constructor/schemas/v1/<new>.py` | Define the payload Pydantic class. Include `schema_version: Literal["1.0.0"]`, set `model_config = ConfigDict(extra="forbid", protected_namespaces=())`. |
| 2 | `src/model_project_constructor/schemas/v1/__init__.py` | Export the new class. |
| 3 | `src/model_project_constructor/schemas/registry.py:26-32` | Add a tuple entry `("<PayloadType>", "1.0.0"): v1.<PayloadType>`. |
| 4 | `src/model_project_constructor/schemas/envelope.py:27-28` | If the new agent needs to be named in envelopes, add its string to the `source_agent` and/or `target_agent` `Literal[...]` union. |
| 5 | `src/model_project_constructor/agents/<new>/` | Implement the agent. Follow the existing package structure: `agent.py` (public entry point), `state.py` (LangGraph state), `nodes.py` (graph nodes), plus any auxiliary modules. |
| 6 | `src/model_project_constructor/orchestrator/pipeline.py:41-43` | Declare the runner type alias alongside the existing ones. Existing runners: `IntakeRunner = Callable[[], IntakeReport]`, `DataRunner = Callable[[DataRequest], DataReport]`, `WebsiteRunner = Callable[[IntakeReport, DataReport, RepoTarget], RepoProjectResult]`. |
| 7 | `src/model_project_constructor/orchestrator/pipeline.py` | Thread the new runner through `run_pipeline(...)` with `FAILED_AT_<STAGE>` handling that mirrors the existing data/website halt paths. |
| 8 | `tests/agents/<new>/` | Mirror the test layout of `tests/agents/intake/` or `tests/agents/data/`. Contract tests: (a) agent handles malformed input without raising uncaught exceptions, (b) output validates against the new schema, (c) one end-to-end happy-path test. |

### Key invariants to preserve

- **Every hop writes a checkpoint.** The orchestrator persists each agent's output via `CheckpointStore` before invoking the next stage (`orchestrator/pipeline.py`).
- **No shared state.** The new agent receives only what is in the envelope — no global config, no module-level caches leaking between runs. See `tests/test_data_agent_decoupling.py`, which AST-walks the Data Agent package to enforce zero intake-schema imports.
- **Status vocabulary.** Terminal statuses use `COMPLETE` / `FAILED_AT_<STAGE>` (see `PipelineStatus` at `pipeline.py:45-50`). A new stage adds a new `FAILED_AT_<NEW>` value.

---

## 3. Extension surface: adding a new repo-host adapter

Use case: support a third forge (e.g., Bitbucket, Gitea, self-hosted Forgejo). The Website Agent talks to the host exclusively through the `RepoClient` `Protocol`.

### The protocol

`src/model_project_constructor/agents/website/protocol.py:42-66`:

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

`ProjectInfo` (`protocol.py:19-31`) carries `id: str`, `url: str`, `default_branch: str`. The `id` is host-opaque — GitLab uses a stringified integer, GitHub uses `"owner/name"`. Callers treat it as a token and pass it back unchanged.

`CommitInfo` (`protocol.py:34-39`) carries `sha: str` and `files_committed: list[str]`.

### Error contract

`protocol.py:69-78`:

- `RepoClientError` — base class for any host-side failure the agent handles.
- `RepoNameConflictError` — **must** be raised when `create_project` collides with an existing project name. The Website Agent's graph handles this explicitly (retries with a mangled slug up to the retry budget).

Any other failure should be wrapped as `RepoClientError`; raw library exceptions should not leak into the agent's nodes.

### Adapter template

The existing adapters illustrate the template:

| Adapter | Module | Constructor signature |
|---|---|---|
| `PythonGitLabAdapter` | `src/model_project_constructor/agents/website/gitlab_adapter.py` | `__init__(*, host_url: str, private_token: str, ssl_verify: bool = True)` |
| `PyGithubAdapter` | `src/model_project_constructor/agents/website/github_adapter.py` | `__init__(*, private_token: str, host_url: str = "https://api.github.com")` |

Each class is roughly ~120 lines, implements exactly `create_project` and `commit_files`, maps host-library exceptions to `RepoClientError` / `RepoNameConflictError`, and is kwarg-only on construction.

### Files to add or edit

1. **New module** `src/model_project_constructor/agents/website/<host>_adapter.py` — implement `create_project` and `commit_files`, translate host exceptions.
2. **Re-export** in `src/model_project_constructor/agents/website/__init__.py` — mirror the existing `PythonGitLabAdapter` / `PyGithubAdapter` re-export.
3. **Optional dependency** in the top-level `pyproject.toml` under the `agents` extra — add the host's Python SDK (e.g., `atlassian-python-api` for Bitbucket).
4. **Tests** in `tests/agents/website/test_<host>_adapter.py` — follow the pattern of `test_github_adapter.py` and `test_gitlab_adapter.py`:
   - Import-level check (module loads, class has both Protocol methods).
   - Constructor does no network I/O.
   - Exception classification — host-specific failures map to the right `Repo*Error` subclass.
   - `MagicMock`-based happy path for `create_project` and `commit_files`.
5. **Generated-project CI template** in `src/model_project_constructor/agents/website/governance_templates.py` — if the new host has a distinct CI system, add a `render_<host>_ci()` function alongside `render_gitlab_ci()` and `render_github_actions_ci()`, and widen the `ci_platform` dispatch at `governance_templates.py:733-736`.

### Wiring and selection

There is no adapter factory. The Website Agent receives the `RepoClient` instance directly from its caller — see `agents/website/agent.py`. The `scripts/run_pipeline.py` entry point selects the adapter via the `--host` flag. A new host value requires updating that selection code path.

---

## 4. Extension surface: adding a new governance artifact

Use case: your organization needs an artifact type that isn't currently emitted (e.g., "Fair-lending impact statement", "Post-market monitoring plan").

### How tier gating works

`src/model_project_constructor/agents/website/governance_templates.py:708-785` — the `build_governance_files` function reads:

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

The severity comparison uses `_tier_at_least(risk_tier, threshold)` at `governance_templates.py:47-54`, which maps tier strings to ordinal severities.

### Files to add or edit

1. **Write the renderer** in `src/model_project_constructor/agents/website/governance_templates.py`. Convention: `render_<artifact_name>(*, intake: dict[str, Any], ...) -> str` returning the markdown body.
2. **Wire into `build_governance_files`** at the correct tier block (`:725-784`). Choose the narrowest gate that correctly describes when the artifact is required.
3. **Update `is_governance_artifact`** at `governance_templates.py:837-858` so the classifier recognizes the new file path. This is the single source of truth for `GovernanceManifest.artifacts_created` — do not also record the path in state.
4. **Add a positive *and* negative test** in `tests/agents/website/test_governance.py`. Per this project's learning #5: assert the artifact appears at the intended tier *and* does not appear at lower tiers. A positive-only test passes silently if a tier starts emitting the wrong artifact.
5. **If the artifact is a `.qmd` narrative** that needs to be rendered into the project, add it to `build_analysis_files` instead of `build_governance_files` and wire its emission to the appropriate governance flag.

### No envelope or registry changes required

Governance artifacts are a content-generation concern internal to the Website Agent. They do not flow across agent boundaries, so they do not require a new schema, registry entry, or envelope update.

---

## 5. Extension surface: adding a new regulatory framework

Use case: your jurisdiction requires a framework not currently supported (e.g., UK FCA CP23/17, Singapore MAS FEAT).

### Current framework registry

`src/model_project_constructor/agents/website/governance_templates.py:77-103`:

```python
_FRAMEWORK_ARTIFACTS: dict[str, list[str]] = {
    "SR_11_7": [
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
    "EU_AI_ACT": [
        "governance/eu_ai_act_compliance.md",
        "governance/impact_assessment.md",
    ],
    "ASOP_56": [
        "governance/model_card.md",
        "governance/three_pillar_validation.md",
    ],
}
```

At render time, `build_regulatory_mapping(frameworks, emitted_paths)` (`governance_templates.py:106-121`) intersects each declared framework's artifact list with the actually-emitted paths for this run — so the `regulatory_mapping.md` content only claims coverage for artifacts that were in fact generated.

### Files to add or edit

1. **Add an entry** to `_FRAMEWORK_ARTIFACTS` mapping the new framework's identifier string to the list of artifact paths it requires. Identifiers follow the convention `<JURISDICTION>_<CODE>` (e.g., `FCA_CP23_17`).
2. **If the framework requires a new artifact type**, add it per §4 above *before* referencing it here.
3. **Update the `IntakeReport` schema documentation** to note the new framework identifier. The schema itself does not validate framework strings (it stores them as `list[str]`), but the intake agent's system prompt in `src/model_project_constructor/agents/intake/anthropic_client.py` enumerates known frameworks — add the new string to that enumeration so the agent will suggest it.
4. **Test coverage** in `tests/agents/website/test_governance.py`:
   - Assert `build_regulatory_mapping` includes the new framework when declared in intake.
   - Assert the mapping intersects correctly with emitted artifacts (a framework mapped to an un-emitted artifact must not falsely appear in the manifest).

### No adapter or pipeline changes required

Framework additions are pure content. They flow through `IntakeReport.governance.regulatory_frameworks` → `build_regulatory_mapping` → `governance/regulatory_mapping.md` in the generated project. Nothing in the orchestrator, the envelope, or the adapter layer needs to change.

---

## Invariants enforced by tests

Several extension surfaces have mechanical guards that will fail CI if the contract is broken:

| Invariant | Test | What it checks |
|---|---|---|
| Data Agent has zero intake-schema imports | `tests/test_data_agent_decoupling.py` | AST-walks the standalone data-agent package and the main-package shims; asserts no imports reference the intake schema (architecture-plan §7, constraint C4). |
| Every schema in `REGISTRY` round-trips | `tests/schemas/test_registry.py` | For each `(payload_type, version)` key, constructs an envelope, calls `load_payload`, and asserts equality. |
| Every governance artifact path is classified | `tests/agents/website/test_governance.py` | Asserts `is_governance_artifact` returns `True` for every path emitted by `build_governance_files` / `build_analysis_files` / `build_test_files` across all tier/flag combinations. |
| Tier gating is positive *and* negative | `tests/agents/website/test_governance.py` | Per-tier fan-out asserts both `"governance/<artifact>.md" in files` for the correct tier *and* `... not in files` for lower tiers. |

An extension that breaks any of these invariants is rejected at CI, not in production.

---

## See also

- [Schema Reference](Schema-Reference) — field-by-field Pydantic definitions including the `HandoffEnvelope`
- [Governance Framework](Governance-Framework) — risk tiers and the regulatory mapping table
- [Agent Reference](Agent-Reference) — per-agent inputs, outputs, and failure modes
- [Architecture Decisions](Architecture-Decisions) — AD-1 through AD-10, the design tradeoffs behind these extension points
- [Contributing](Contributing) — code-quality gates, CI, and the commit convention to follow when submitting an extension
