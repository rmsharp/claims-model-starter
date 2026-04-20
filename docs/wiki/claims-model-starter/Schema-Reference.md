# Schema Reference

This page is the authoritative reference for every Pydantic schema in the Model Project Constructor. Field-by-field: type, default, allowed values, file location. It is complementary to the [Agent Reference](Agent-Reference) (which covers schemas at a pseudocode level) and the [Pipeline Overview](Pipeline-Overview) (which covers how schemas flow between agents).

**Audience:** developers, integrators, anyone constructing or parsing a payload by hand.

All schemas inherit from a strict base that forbids extra fields — typos and stale client code fail loudly.

---

## 1. Schema layout

There are **5 registered payload schemas** plus the **HandoffEnvelope** transport wrapper. All are v1.0.0.

| Schema | Purpose | Writer | Reader(s) | File |
|---|---|---|---|---|
| `IntakeReport` | Interview output | Intake Agent | Orchestrator, Website Agent | `schemas/v1/intake.py:45-62` |
| `DataRequest` | What the Data Agent needs | Orchestrator (adapted from intake) or user (standalone) | Data Agent | `packages/data-agent/.../schemas.py:46-60` |
| `DataReport` | Queries + quality checks + summary | Data Agent | Orchestrator, Website Agent | `packages/data-agent/.../schemas.py:92-102` |
| `RepoTarget` | Destination repo config | Orchestrator (from user config) | Website Agent | `schemas/v1/repo.py:12-17` |
| `RepoProjectResult` | Generated repo metadata | Website Agent | Orchestrator | `schemas/v1/repo.py:28-37` |
| `HandoffEnvelope` | Transport wrapper | All senders | All receivers | `schemas/envelope.py:20-34` |

The Data Agent schemas live in a **separate package** (`packages/data-agent/`) to keep the standalone analyst use-case viable. The main package re-exports them from `schemas/v1/data.py` so pipeline callers import from one place, but `DataRequest` / `DataReport` never import `IntakeReport` — enforced by `tests/test_data_agent_decoupling.py`.

---

## 2. The strict base class

Every schema in this project derives from `StrictBase`:

```python
# src/model_project_constructor/schemas/v1/common.py:12-23
class StrictBase(BaseModel):
    model_config = ConfigDict(extra="forbid", protected_namespaces=())
```

Two non-negotiables:

- **`extra="forbid"`** — any unknown field raises `ValidationError`. This catches silent version drift.
- **`protected_namespaces=()`** — lets us use field names like `model_solution` and `model_type` (Pydantic v2 otherwise warns on the `model_` prefix).

The Data Agent package (`packages/data-agent/.../schemas.py:29-38`) defines its own `StrictBase` with the same configuration — deliberately duplicated to avoid coupling the standalone package to the main orchestrator.

The envelope is the only schema that inherits directly from `BaseModel` rather than `StrictBase`. It still uses `extra="forbid"`.

---

## 3. Shared types (`schemas/v1/common.py`)

The schemas/v1/common module defines three Literal-string enums reused across reports:

### `CycleTime` (line 25)

```python
CycleTime = Literal["strategic", "tactical", "operational", "continuous"]
```

- `strategic` — months to quarters between decisions (e.g., pricing committee).
- `tactical` — weeks (e.g., weekly triage model retuning).
- `operational` — days to hours (e.g., daily batch scoring).
- `continuous` — sub-minute / event-driven (e.g., real-time fraud triage).

### `RiskTier` (lines 27-32)

```python
RiskTier = Literal[
    "tier_1_critical",
    "tier_2_high",
    "tier_3_moderate",
    "tier_4_low",
]
```

- `tier_1_critical` — immediate consumer harm possible (rate-setting, adverse action).
- `tier_2_high` — material financial or fairness impact.
- `tier_3_moderate` — internal operational decisions.
- `tier_4_low` — exploratory, back-office, or decision-support only.

See [Governance Framework](Governance-Framework) for the artifact inventory per tier.

### `ModelType` (lines 34-42)

```python
ModelType = Literal[
    "supervised_classification",
    "supervised_regression",
    "unsupervised_clustering",
    "unsupervised_anomaly",
    "time_series",
    "reinforcement",
    "other",
]
```

The orchestrator's `infer_target_granularity` adapter branches on `model_type`: `time_series` maps to a monthly grain, everything else maps to `event` grain with `unit="claim"` (`orchestrator/adapters.py:82`).

### Version constant

```python
SCHEMA_VERSION: Literal["1.0.0"] = "1.0.0"  # common.py:9
```

Every payload carries this as an immutable `schema_version` field.

---

## 4. `IntakeReport` and its nested types

**File:** `src/model_project_constructor/schemas/v1/intake.py`

The Intake Agent writes this; the Orchestrator validates it; the Website Agent reads it to scaffold the project.

### `ModelSolution` (lines 18-25)

```python
class ModelSolution(StrictBase):
    target_variable: str | None         # None is allowed for unsupervised models
    target_definition: str
    candidate_features: list[str]
    model_type: ModelType
    evaluation_metrics: list[str]
    is_supervised: bool
```

`target_variable` is `str | None` with **no default** — the `None` must be explicit. This forces unsupervised modelers to stop and decide rather than silently omit the field.

### `EstimatedValue` (lines 27-33)

```python
class EstimatedValue(StrictBase):
    narrative: str
    annual_impact_usd_low: float | None
    annual_impact_usd_high: float | None
    confidence: Literal["low", "medium", "high"]
    assumptions: list[str]
```

`annual_impact_usd_low` and `_high` are both nullable — when value is genuinely uncertain, both should be `null`, not a zeroed estimate.

### `GovernanceMetadata` (lines 35-43)

```python
class GovernanceMetadata(StrictBase):
    cycle_time: CycleTime
    cycle_time_rationale: str
    risk_tier: RiskTier
    risk_tier_rationale: str
    regulatory_frameworks: list[str]          # e.g., ["SR_11_7", "NAIC_AIS"]
    affects_consumers: bool
    uses_protected_attributes: bool
```

Both `_rationale` strings are required prose — the agent is prompted to produce defensible justifications, not filler. Frameworks are strings (not a Literal) because the acceptable set evolves with regulation.

### `IntakeReport` (lines 45-62)

```python
class IntakeReport(StrictBase):
    schema_version: Literal["1.0.0"] = "1.0.0"
    status: Literal["COMPLETE", "DRAFT_INCOMPLETE"]
    missing_fields: list[str] = Field(default_factory=list)

    business_problem: str
    proposed_solution: str
    model_solution: ModelSolution
    estimated_value: EstimatedValue

    governance: GovernanceMetadata

    stakeholder_id: str
    session_id: str
    created_at: datetime
    questions_asked: int
    revision_cycles: int = 0
```

- `status`: `"COMPLETE"` only if the stakeholder accepted AND no cap tripped. Otherwise `"DRAFT_INCOMPLETE"`.
- `missing_fields`: adds `"questions_cap_reached"` or `"revision_cap_reached"` when applicable — see [Intake Interview Design §7](Intake-Interview-Design).
- `questions_asked`: required (no default) — the report must record how many questions were actually asked.
- `created_at`: tz-aware `datetime` — UTC in practice.

**Example fixture:** `tests/fixtures/subrogation_intake.json`.

---

## 5. `DataRequest` and `DataReport` (Data Agent package)

**File:** `packages/data-agent/src/model_project_constructor_data_agent/schemas.py`

These schemas are deliberately self-contained — the Data Agent package does not import anything from the main project. An analyst can install `model-project-constructor-data-agent` alone and use the schemas for a standalone query-writing session.

### `DataGranularity` (lines 41-43)

```python
class DataGranularity(StrictBase):
    unit: str                                                  # "claim" | "policy" | "customer" | ...
    time_grain: Literal["event", "daily", "weekly",
                        "monthly", "quarterly", "annual"]
```

`unit` is free-form because the set of meaningful grains is domain-dependent.

### `DataRequest`

```python
class DataRequest(StrictBase):
    schema_version: Literal["1.0.0"] = "1.0.0"
    target_description: str
    target_granularity: DataGranularity
    required_features: list[str]
    population_filter: str
    time_range: str                              # free-form, e.g. "last 5 calendar years"
    database_hint: str | None = None
    data_quality_concerns: list[str] = Field(default_factory=list)
    data_source_inventory: DataSourceInventory | None = None
    source: Literal["pipeline", "standalone"]
    source_ref: str                              # run_id if pipeline; user_id if standalone
```

- `source` distinguishes the two usage modes. In pipeline mode the orchestrator constructs it from the `IntakeReport`; in standalone mode the analyst hand-writes it.
- `database_hint` is an optional steer — `None` means "no preference."
- `data_source_inventory` is an optional structured catalog of candidate tables / views / datasets (see `DataSourceInventory` below). When set, the Data Agent renders a summarized block into the query-generation prompt so the LLM prefers inventory-named tables. When both `database_hint` and `data_source_inventory` are set, the inventory wins (richer signal). An inventory with `entries=[]` is treated identically to `None`.

**Example fixture:** `tests/fixtures/sample_request.json`.

### `QualityCheck` (lines 62-68)

```python
class QualityCheck(StrictBase):
    check_name: str                              # e.g., "null_rate_target"
    check_sql: str
    expectation: str                             # prose: what "passing" looks like
    execution_status: Literal["PASSED", "FAILED", "ERROR", "NOT_EXECUTED"]
    result_summary: str
    raw_result: dict[str, Any] | None = None
```

`execution_status="NOT_EXECUTED"` is used when the Data Agent runs without a database connection — quality checks are generated but not run. The report still carries `status="COMPLETE"` in that case.

### `Datasheet` (lines 71-80)

```python
class Datasheet(StrictBase):
    motivation: str
    composition: str
    collection_process: str
    preprocessing: str
    uses: str
    known_biases: list[str]
    maintenance: str
```

The seven fields follow Gebru et al. 2021, *Datasheets for Datasets*. The Data Agent writes one per primary query.

### `PrimaryQuery`

```python
class PrimaryQuery(StrictBase):
    name: str                                                       # snake_case
    sql: str
    purpose: str                                                    # one-sentence rationale
    expected_row_count_order: Literal["tens", "hundreds",
                                      "thousands", "millions"]
    quality_checks: list[QualityCheck]
    datasheet: Datasheet
    inventory_entries_used: list[str] = []                          # fully-qualified names from the inventory that the SQL references
```

`expected_row_count_order` is a sanity check — if a query that should return `"thousands"` returns 3 rows, operators have a cheap signal that something is wrong.

`inventory_entries_used` records the inventory provenance for each query. When a `DataSourceInventory` was passed into the `DataRequest`, the LLM reports which `fully_qualified_name` values its SQL references here. Empty list when no inventory was provided, or when the LLM reported using none of the inventory entries.

### `DataReport` (lines 92-102)

```python
class DataReport(StrictBase):
    schema_version: Literal["1.0.0"] = "1.0.0"
    status: Literal["COMPLETE", "INCOMPLETE_REQUEST", "EXECUTION_FAILED"]
    request: DataRequest                       # echoed back for traceability
    primary_queries: list[PrimaryQuery]
    summary: str                               # 2-4 sentences
    confirmed_expectations: list[str]
    unconfirmed_expectations: list[str]
    data_quality_concerns: list[str]
    created_at: datetime
```

- `status="COMPLETE"` — queries and checks generated; checks may or may not have been executed against a live DB.
- `status="INCOMPLETE_REQUEST"` — the input request was too ambiguous (e.g., empty target) to produce a useful answer.
- `status="EXECUTION_FAILED"` — LLM parse error or other unrecoverable failure.
- `request` is an echo of the input — lets downstream consumers reconstruct the full context without holding a second reference.

**Example fixture:** `tests/fixtures/sample_datareport.json`.

---

## 6. `RepoTarget`, `GovernanceManifest`, `RepoProjectResult`

**File:** `src/model_project_constructor/schemas/v1/repo.py`

### `RepoTarget` (lines 12-17)

```python
class RepoTarget(StrictBase):
    schema_version: Literal["1.0.0"] = "1.0.0"
    host_url: str                                       # "https://gitlab.com" or self-hosted like "https://gitlab.yourcompany.com"
    namespace: str                                      # "data-science/model-drafts" or "my-org"
    project_name_hint: str
    visibility: Literal["private", "internal", "public"] = "private"
```

Default visibility is `"private"`. GitHub does not support nested namespaces — the GitHub adapter raises `RepoClientError` if `namespace` contains a `/` (`github_adapter.py:85-89`).

### `GovernanceManifest` (lines 20-25)

```python
class GovernanceManifest(StrictBase):
    model_registry_entry: dict[str, Any]                # mirrors governance/model_registry.json
    artifacts_created: list[str]                        # paths of governance files emitted
    risk_tier: RiskTier
    cycle_time: CycleTime
    regulatory_mapping: dict[str, list[str]] = Field(default_factory=dict)
```

- `model_registry_entry` is an escape hatch for the full registry row; see [Governance Framework](Governance-Framework) for its shape.
- `regulatory_mapping` maps a framework name (e.g., `"SR_11_7"`) to the list of artifact paths that satisfy it — a reviewer-friendly index into the generated project.

### `RepoProjectResult` (lines 28-37)

```python
class RepoProjectResult(StrictBase):
    schema_version: Literal["1.0.0"] = "1.0.0"
    status: Literal["COMPLETE", "PARTIAL", "FAILED"]
    project_url: str                                    # full URL
    project_id: str                                     # opaque: GitLab int-as-str; GitHub "owner/name"
    initial_commit_sha: str
    files_created: list[str]
    governance_manifest: GovernanceManifest
    failure_reason: str | None = None                   # populated when status="FAILED"
```

`project_id` is **host-opaque**. The adapters (`github_adapter.py`, `gitlab_adapter.py`) decide the format; downstream consumers should treat it as a bag of bytes and pass it back to the adapter for subsequent calls.

The orchestrator persists this as a **terminal result**, not an envelope — see §8 below.

---

## 7. `HandoffEnvelope` (transport wrapper)

**File:** `src/model_project_constructor/schemas/envelope.py`

```python
# lines 20-34
class HandoffEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")

    envelope_version: Literal["1.0.0"] = "1.0.0"
    run_id: str
    source_agent: Literal["intake", "data", "website", "orchestrator"]
    target_agent: Literal["intake", "data", "website"]           # NO "orchestrator"
    payload_type: str                                            # e.g., "IntakeReport"
    payload_schema_version: str                                  # e.g., "1.0.0"
    payload: dict[str, Any]                                      # raw; resolved via registry
    created_at: datetime
    correlation_id: str                                          # same across all envelopes in one run
```

Three properties worth internalizing:

- **`envelope_version` is locked at `"1.0.0"` forever.** The envelope protocol evolves by adding a new version field for a future iteration — old envelope versions route through a migration function, not a mutation of the current field.
- **Payload is a raw `dict`, not a Pydantic instance.** The envelope deliberately does not enforce payload schema. Validation happens in `registry.load_payload(envelope)` — this keeps the envelope cheap to serialize/forward without forcing a full Pydantic parse.
- **The orchestrator never *receives* an envelope** — `target_agent` excludes `"orchestrator"`. This is enforced by a dedicated test (`tests/schemas/test_envelope_and_registry.py` — `test_target_agent_cannot_be_orchestrator`). The orchestrator's own terminal outputs use a separate channel (see §8).

### Why the orchestrator can't be a target

The original design tried to widen `target_agent` to include `"orchestrator"` so the website agent's `RepoProjectResult` could ride home in an envelope. It failed the invariant test. The current design uses a sibling `save_result()` method on `CheckpointStore` — cleaner, because the orchestrator's receipt of a terminal result is a fundamentally different operation than an agent-to-agent handoff.

---

## 8. Schema registry (`schemas/registry.py`)

The registry is the single source of truth mapping `(payload_type, schema_version)` → Pydantic class. Agents **never import each other's schemas directly**; they resolve via `load_payload`.

```python
# lines 26-32
SchemaKey = tuple[str, str]

REGISTRY: dict[SchemaKey, type[BaseModel]] = {
    ("IntakeReport", "1.0.0"): v1.IntakeReport,
    ("DataRequest", "1.0.0"): v1.DataRequest,
    ("DataReport", "1.0.0"): v1.DataReport,
    ("RepoTarget", "1.0.0"): v1.RepoTarget,
    ("RepoProjectResult", "1.0.0"): v1.RepoProjectResult,
}
```

### `load_payload(envelope) -> BaseModel`

```python
# lines 39-58 (abbreviated)
def load_payload(envelope: HandoffEnvelope) -> BaseModel:
    key = (envelope.payload_type, envelope.payload_schema_version)
    try:
        cls = REGISTRY[key]
    except KeyError:
        raise UnknownPayloadError(...)
    return cls.model_validate(envelope.payload)
```

- **`UnknownPayloadError`** (subclass of `KeyError`) — payload type/version not registered.
- **`pydantic.ValidationError`** — payload dict doesn't match the resolved schema.

Both are caught and surfaced by the orchestrator as pipeline halt conditions.

### Registry completeness test

`tests/schemas/test_envelope_and_registry.py` asserts the registry contains exactly these five keys. Adding a schema without registering it is a test failure — the registry is guarded, not trusted.

---

## 9. Checkpoint storage layout

The `CheckpointStore` in `orchestrator/checkpoints.py` persists every handoff. A single run produces this layout:

```
<MPC_CHECKPOINT_DIR>/<run_id>/
    IntakeReport.json           # envelope (source_agent=orchestrator, target=data)
    DataRequest.json            # envelope (source=orchestrator, target=data)
    DataReport.json             # envelope (source=data, target=website)
    RepoTarget.json             # envelope (source=orchestrator, target=website)
    RepoProjectResult.result.json   # terminal result, not an envelope
```

The `.result.json` suffix is load-bearing: it prevents a terminal result from ever colliding with an envelope filename, even if the registered payload type happens to be named the same thing.

Reconstructing a halted run:

```python
from model_project_constructor.orchestrator import CheckpointStore

store = CheckpointStore(Path("/var/lib/mpc/checkpoints"))
intake = store.load_payload("run_abc", "IntakeReport")   # returns IntakeReport
data   = store.load_payload("run_abc", "DataReport")     # if present
```

See [Monitoring and Operations §5](Monitoring-and-Operations) for resume recipes.

---

## 10. Versioning strategy

All payloads are currently v1.0.0. The registry keys on `(payload_type, schema_version)` so multiple versions can coexist during a migration.

**Minor bump** (1.0.0 → 1.1.0, backward-compatible additions):

- Add the new class under key `("Foo", "1.1.0")`.
- Keep `("Foo", "1.0.0")` in the registry — old envelopes continue to validate.
- Callers choose which version to emit; readers handle both.

**Major bump** (1.0.0 → 2.0.0, breaking change):

- Register 2.0.0 and keep 1.0.0 for at least two major releases — in-flight runs must not break mid-upgrade.
- Provide a migration function in `schemas/migrations/` that converts a v1 payload dict to v2.

**Envelope version** is separate and is locked at `1.0.0` permanently. Envelope protocol evolution happens via additive fields, not version bumps.

---

## 11. Constructing a valid payload by hand

Checklist:

1. **Pick a schema from the registry** (5 options).
2. **Provide every required field.** Defaults are documented above; everything else is required.
3. **Use Literal values exactly as spelled** — `"tier_3_moderate"`, never `"TIER_3_MODERATE"` or `"tier-3-moderate"`.
4. **For nested models**, instantiate them as nested objects — Pydantic will not promote dicts silently.
5. **For timestamps**, pass a timezone-aware `datetime`. JSON serialization emits ISO 8601; deserialization restores the `datetime`.
6. **For collection defaults** (e.g., `missing_fields`, `data_quality_concerns`, `regulatory_mapping`), omit the field to get the empty default — do not pass `None`.
7. **Wrap for transport** in a `HandoffEnvelope`:
    - `payload_type`: class name string (e.g., `"IntakeReport"`).
    - `payload_schema_version`: `"1.0.0"`.
    - `payload`: `my_model.model_dump(mode="json")`.

Test helpers are available at `tests/schemas/fixtures.py` (e.g., `make_intake_report(**overrides)`, `make_data_report(**overrides)`) — the fastest way to get a valid instance with just the overrides that matter for a test.

---

## 12. Round-trip guarantees

Every schema round-trips losslessly through JSON via Pydantic v2:

```python
blob = report.model_dump_json()
restored = IntakeReport.model_validate_json(blob)
assert restored == report
```

Datetime fields serialize as ISO 8601 with timezone. Nested models survive intact. `dict[str, Any]` fields carry arbitrary structure — useful for `GovernanceManifest.model_registry_entry` and `QualityCheck.raw_result`.

---

## 13. Key files

| File | Contents |
|---|---|
| `src/model_project_constructor/schemas/v1/common.py` | `StrictBase`, `CycleTime`, `RiskTier`, `ModelType`, `SCHEMA_VERSION` |
| `src/model_project_constructor/schemas/v1/intake.py` | `IntakeReport`, `ModelSolution`, `EstimatedValue`, `GovernanceMetadata` |
| `src/model_project_constructor/schemas/v1/data.py` | Re-export surface for Data Agent schemas |
| `src/model_project_constructor/schemas/v1/repo.py` | `RepoTarget`, `GovernanceManifest`, `RepoProjectResult` |
| `src/model_project_constructor/schemas/envelope.py` | `HandoffEnvelope` |
| `src/model_project_constructor/schemas/registry.py` | `REGISTRY`, `load_payload`, `UnknownPayloadError` |
| `packages/data-agent/src/model_project_constructor_data_agent/schemas.py` | `DataRequest`, `DataReport`, `DataGranularity`, `PrimaryQuery`, `QualityCheck`, `Datasheet` |
| `tests/schemas/fixtures.py` | `make_*()` factories for every schema |
| `tests/fixtures/*.json` | Realistic JSON examples for each payload type |
