# Data Source Inventory Contract — Architectural Plan

**Status:** DRAFT — authored Session 57 (2026-04-19). Phase 1 implementation is Session 58's deliverable.
**Workstream:** `docs/methodology/workstreams/ARCHITECTURE_WORKSTREAM.md`.
**Supersedes:** BACKLOG line "Data agent: metadata discovery mode" (one-session implementation framing). The operator reframed the work on 2026-04-19 as an architectural plug-in boundary rather than a single feature addition.
**Memory reference:** `feedback_data_source_discovery.md` — durable project memory capturing the operator's architectural principles.

---

## 1. Context

### 1.1 Problem statement

The Data Agent currently takes a `DataRequest` and produces a `DataReport` with generated SQL, executed quality checks, and narrative summary. There is no mechanism for telling the agent *which* tables / datasets / factors are relevant to the request — the agent relies on the LLM's domain knowledge + the single `database_hint: str | None` field (which is a schema hint, not a table inventory).

Three concrete gaps surface from this:

1. **Stakeholder-specific sources are opaque.** The Session 56 intake prompt probes stakeholders for named systems (Guidewire ClaimCenter, Duck Creek Claims, policy admin, billing, subrogation recovery tools, fraud/SIU scoring, CRM, data warehouse, data lake) and captures responses in `qa_pairs`. Those captured answers never flow to the data agent in a structured form.
2. **Curated inputs have no ingestion path.** Some groups already maintain a canonical list of tables and factors. Today they must re-describe sources inside `target_description` and `population_filter` free-text — the data agent cannot distinguish "here are my tables" from "here's what I want."
3. **Automated discovery has no architectural home.** The BACKLOG item ("Data agent: metadata discovery mode") proposed querying `information_schema` to identify relevant tables. As a single feature inside `DataAgent.run()`, this would couple the data agent to one specific discovery mechanism.

### 1.2 Operator's architectural guidance (Session 57 Phase 1, verbatim)

> Potential data source discovery needs to be a separate activity since some groups will have their own curated raw data and factors. We will need a clear method of providing data sources for ingestion by this tool stack. I expect over time separate data discovery tools will be created and evolve. This system will need to be adaptable for that.

### 1.3 Filing-session grounding

- `docs/architecture-history/initial_purpose.txt:88`: "This same basic agent would likely be useful for just writing queries in general. Many analysts teams (esp. DAs) spend a lot of their time just doing this. Helping them by speeding this up as quickly as possible would enable more exploratory analysis that is too difficult to even consider today given the time it takes to work on queries." The data agent is designed as a reusable analyst tool; source-identification workflows fit naturally around it, not inside it.
- `packages/data-agent/USAGE.md:1-17`: the package is explicitly designed to be usable "outside the full `model-project-constructor` pipeline." A plug-in contract preserves that property — both the pipeline and ad-hoc analyst use cases consume the same inventory shape.
- `CLAUDE.md` §"The 6-Step Pipeline": Step 3 is "Data Collection & Validation." The inventory sits at the step-2 → step-3 handoff boundary (output of the intake agent and/or a discovery tool; input to the data agent).

### 1.4 Current-state summary (grep-verified)

| Component | File(s) | Role |
|-----------|---------|------|
| Canonical `DataRequest` / `DataReport` / `Datasheet` / `PrimaryQuery` / `QualityCheck` / `DataGranularity` | `packages/data-agent/src/model_project_constructor_data_agent/schemas.py` | Single source of truth. `packages/data-agent/README` equivalent text lives in `USAGE.md`. |
| Main-package re-export | `src/model_project_constructor/schemas/v1/data.py` | Delegated to the standalone package — "Do not add new schemas or fields here." |
| Pipeline-side adapter | `src/model_project_constructor/orchestrator/adapters.py:63-77` | Builds `DataRequest` from `IntakeReport`; currently passes `database_hint=None`. |
| Data Agent graph | `packages/data-agent/src/model_project_constructor_data_agent/graph.py` | `START → generate_queries → generate_qc → execute_qc → summarize → datasheet → END` with off-ramps. |
| LLM protocol | `packages/data-agent/src/model_project_constructor_data_agent/llm.py` | Four methods: `generate_primary_queries`, `generate_quality_checks`, `summarize`, `generate_datasheet`. |
| DB wrapper | `packages/data-agent/src/model_project_constructor_data_agent/db.py` | `ReadOnlyDB` with `connect`, `execute`, `close`. No metadata method today. |
| CLI | `packages/data-agent/src/model_project_constructor_data_agent/cli.py` | Single `run` subcommand; fake-LLM smoke mode supported. |

### 1.5 What this plan is and is not

**Is:** an architectural plan defining a contract schema and a phased implementation path. The artifact is a multi-session roadmap; each phase is one implementation session.

**Is not:** code. Per Failure Mode #19 (plan-mode bypass) and Failure Mode #18 (planning-to-implementation bleed), no schemas, nodes, LLM methods, CLI changes, or tests are written in this session. Session 58 opens Phase 1.

**Is not:** a commitment to every field name. Implementation sessions may refine details that the plan leaves ambiguous. The plan locks the architectural shape (separation, contract-based, producer-agnostic); it sketches the field set.

---

## 2. Non-goals

- **No live-DB integration in early phases.** All discovery testing uses fake `information_schema` responses until a future Scope-C style task adds live-DB coverage.
- **No removal or rename of existing fields.** `database_hint` stays; the inventory is additive. No migration of existing fixtures is required.
- **No new package.** The contract lives inside `packages/data-agent/` initially. Extraction to a separate `packages/data-source-inventory/` is a future option, not a phase.
- **No coupling to a specific data-catalog vendor.** The contract is vendor-neutral; DataHub / Amundsen / Collibra integrations (if ever written) are additional producers, not schema dependencies.
- **No change to the intake agent's Session 56 prompt.** Phase 4 (optional) reads `qa_pairs` post-interview; it does not modify the interview itself.

---

## 3. Architectural decisions

### 3.1 Separation of discovery from consumption

**Decision:** Discovery is a separate activity upstream of the data agent. The data agent *consumes* an inventory; it does not *produce* one. The inventory is the interface between the two concerns.

**Why:** Operator guidance (§1.2). Multiple producer types are first-class — no one producer is "the" discovery mechanism.

**Invariant:** No code under `packages/data-agent/src/model_project_constructor_data_agent/{agent,graph,nodes}.py` shall construct a `DataSourceInventory`. Those modules accept one from `DataRequest` and pass it through. Production of inventories lives in dedicated producer modules (Phase 2 onward).

### 3.2 Contract is pure data

**Decision:** The contract is a set of Pydantic schemas serializable to JSON. Producers are not required to implement a Python Protocol — they need only produce JSON conforming to the schema. A `DataSourceProducer` Protocol MAY be added later for in-process producers, but is not a Phase 1 requirement.

**Why:**
- Curated inputs should be pure files (YAML or JSON), needing no code.
- CI fixtures can be hand-written.
- Non-Python discovery tools (shell scripts, Go services, Slack bots) can produce inventory without importing the Python package.
- Adding a Protocol later is non-breaking if the data shape is stable; inverting that order (Protocol first, then file-based later) risks over-fitting the interface to the first implementation.

### 3.3 Four producer classes, single consumer shape

**Decision:** The contract supports four producer classes, distinguished by `ProducerMetadata.producer_type`:

| producer_type | Examples | When used |
|---------------|----------|-----------|
| `curated` | YAML / JSON file hand-maintained by a team | Teams with canonical table lists |
| `automated` | `information_schema` probe (Phase 2 reference impl) | When connection to a live DB is available |
| `interview` | Converter from intake `qa_pairs` to entries | When Session 56 intake probe captures stakeholder-named systems |
| `external_catalog` | DataHub / Amundsen / Collibra / BigQuery INFORMATION_SCHEMA / Snowflake SHOW TABLES | When a metadata catalog is available (future) |

**The consumer (data agent) does not branch on `producer_type`.** It may *weight* entries by producer (e.g., trust curated entries higher than automated), but the shape and processing path is uniform.

**Why:** Uniform consumer logic is simpler to maintain and test. Differential trust is an optimization, not a correctness requirement.

### 3.4 Backward compatibility with `database_hint`

**Decision:** `DataRequest.database_hint` remains. When `data_source_inventory` is present, the LLM prompt uses the inventory; when both are present, the inventory takes precedence (richer signal subsumes the hint). When neither is present, current behavior is preserved exactly — today's fixtures and call sites continue to work unchanged.

**Why:** Many test fixtures and 27+ production/test/doc files reference `database_hint` (grep-verified §8.1). Removing it is gratuitous churn. A deprecation of `database_hint` could be filed as a separate BACKLOG item post-Phase-3 if the inventory covers every use case, but is out of scope here.

### 3.5 Inventory can be absent

**Decision:** `DataRequest.data_source_inventory: DataSourceInventory | None = None`. All existing test fixtures continue to produce valid `DataRequest` instances without modification.

**Why:** The two-sided coupling (intake produces inventory + data agent consumes it) cannot land atomically across the four phases. A None default lets phases ship independently.

---

## 4. The contract — interface-first design

### 4.1 Schema overview

Four types live in `packages/data-agent/src/model_project_constructor_data_agent/schemas.py` (alongside the existing `DataRequest`, `DataReport`, etc.), all inheriting the local `StrictBase` (which sets `extra="forbid"` and disables `model_` protected namespaces — see `schemas.py:29-38`).

```
DataSourceInventory
├── schema_version: Literal["1.0.0"]
├── entries: list[DataSourceEntry]
├── producers: list[ProducerMetadata]
├── created_at: datetime
└── request_context: str | None

DataSourceEntry
├── schema_version: Literal["1.0.0"]
├── Identity: name, namespace, source_system, fully_qualified_name
├── Kind: entity_kind  (Literal: table / view / materialized_view / file_dataset / feature_view / other)
├── Structure: columns, primary_key_columns, row_count_estimate
├── Semantics: description, business_domain, entity_types
├── Relevance (per-request): relevance_score, relevance_reason
├── Freshness / access: last_updated_at, refresh_cadence, access_notes, owning_team
├── Provenance: producer_id  (FK to ProducerMetadata.producer_id)
└── extra: dict[str, Any]  (producer-specific extension point)

ProducerMetadata
├── producer_id: str  (stable id, e.g. "information_schema_probe_v1")
├── producer_type: Literal["curated", "automated", "interview", "external_catalog"]
├── produced_at: datetime
├── producer_version: str | None
└── notes: str | None

ColumnMetadata
├── name: str
├── data_type: str  (database-native string, e.g. "VARCHAR(255)", "NUMERIC(10,2)")
├── nullable: bool | None
├── description: str | None
├── is_primary_key: bool
├── is_foreign_key: bool
└── foreign_key_target: str | None  (fully qualified, e.g. "public.claims.claim_id")
```

### 4.2 Field rationale

| Field | Rationale |
|-------|-----------|
| `schema_version: "1.0.0"` | Matches the pattern on `DataRequest.schema_version`. Enables future non-breaking extensions (`"1.1.0"`) and signals breaking changes (`"2.0.0"`). Consumers assert compatibility on load. |
| `DataSourceEntry.fully_qualified_name` | Stable canonical identifier. Some databases use `catalog.schema.table`, others `schema.table`, others single-level. The producer emits whatever its source system considers canonical; downstream code uses this as the dedup key. |
| `DataSourceEntry.entity_kind` | Distinguishes tables, views, materialized views, and non-DB sources (files, feature-store views). `other` is the escape hatch. |
| `DataSourceEntry.business_domain` and `entity_types` | Enables filtering ("show me only claims-domain sources"). Free-text strings because P&C subdomain taxonomies vary by org. |
| `DataSourceEntry.relevance_score` / `relevance_reason` | Per-request. Different producers assign relevance differently (automated tools may not assign any). None means "producer took no position." |
| `DataSourceEntry.producer_id` | Foreign key into the `producers` list. Enables the consumer to cite provenance in generated artifacts (e.g. "this SQL targets `claims.claim_events`, which was surfaced by producer `information_schema_probe_v1`"). |
| `DataSourceEntry.extra: dict[str, Any]` | Producer-specific extension point. DataHub might include a lineage graph pointer; curated inputs might include a confidential-access flag. Keeping this structured-but-open preserves adaptability (§3 invariant) without fracturing the core schema. |
| `ProducerMetadata.producer_id` (stable) | Enables A/B comparison of producer output over time. `information_schema_probe_v1` → `v2` is a schema-version-of-the-producer, not the inventory contract. |
| `ColumnMetadata.is_foreign_key` / `foreign_key_target` | Enables the downstream query generator to infer join paths. Optional on producers that can't introspect FK constraints. |
| `ProducerMetadata.notes` | Free-text field for producer-specific context (e.g. "probe ran with elevated permissions" or "catalog data 24h stale"). |

### 4.3 Error contract

- Invalid inventory JSON raises a Pydantic `ValidationError` at load time. The consumer (data agent) surfaces this as `DataReport(status="EXECUTION_FAILED", data_quality_concerns=[...])` at the outer boundary — same pattern as existing `LLMParseError` handling (`agent.py:52-60`).
- Missing `producers` entries referenced by `DataSourceEntry.producer_id` are a validation error (cross-field validator in the pydantic model; Phase 1 implements this).
- Empty inventory (`entries: []`) is valid — the consumer treats it identically to `data_source_inventory=None` (falls back to `database_hint` + LLM domain knowledge).

### 4.4 Versioning strategy

- `schema_version` on `DataSourceInventory` and `DataSourceEntry` both start at `"1.0.0"`.
- **Additive changes** (new optional field, new Literal variant) are `"1.1.0"`, etc. Producers that emit the old version still parse; consumers that expect the new version tolerate the old.
- **Breaking changes** (renamed field, required-field addition, removed Literal variant) bump to `"2.0.0"`. Producers and consumers negotiate via `schema_version` check. This is a one-way migration governed by a future plan.
- Consumers SHOULD accept any `"1.x.y"` version. Phase 3 implementation pins this with a test.

---

## 5. Producer ecosystem

### 5.1 Curated inputs

**Shape:** a JSON (or YAML converted to JSON at load time) file conforming to `DataSourceInventory`. Teams maintain these in their own repos; the pipeline / CLI accepts a path.

**Reference path** (Phase 2 or earlier convention): `tests/fixtures/sample_curated_inventory.json`.

**Producer metadata:** `producer_type="curated"`, `producer_id="curated:<team-or-repo-slug>"`, `produced_at` is the file's mtime or an explicit field in the file.

**No code required for Phase 1** — the schema alone supports curated inputs once implemented.

### 5.2 Automated: `information_schema` probe (reference implementation — Phase 2)

**Module:** `packages/data-agent/src/model_project_constructor_data_agent/discovery.py` (new).

**Public API sketch:**
```python
def probe_information_schema(
    db: ReadOnlyDB,
    *,
    include_schemas: list[str] | None = None,    # None = every accessible schema
    llm: LLMClient | None = None,                # None = no relevance ranking
    request_context: str | None = None,          # feeds LLM ranking if llm provided
) -> DataSourceInventory
```

**Behavior:**
- Calls `db.get_information_schema()` (new `ReadOnlyDB` method — Phase 2 addition) to fetch `information_schema.tables` + `columns` + (if supported) `key_column_usage` for primary/foreign key info.
- Builds a `DataSourceEntry` per table/view. If `llm` is provided, optionally asks the LLM to rank entries against `request_context` (assigning `relevance_score` / `relevance_reason`); otherwise leaves those fields `None`.
- Returns a `DataSourceInventory` with one `ProducerMetadata` (`producer_id="information_schema_probe_v1"`, `producer_type="automated"`).

**CLI entry point:** `model-data-agent discover --db-url ... --output inventory.json [--include-schemas ...] [--rank-with-llm]`.

### 5.3 Interview-sourced (Phase 4 — optional)

**Converter location:** `src/model_project_constructor/orchestrator/adapters.py` (or a new sibling `inventory_adapters.py` if the adapter grows).

**Behavior:**
- Reads `IntakeReport.qa_pairs`; heuristically extracts named systems (matching the Session 56 list: Guidewire ClaimCenter, Duck Creek Claims, policy admin, billing/collections, subrogation recovery, fraud/SIU, CRM, enterprise data warehouse, data lake).
- Emits one `DataSourceEntry` per named system with `entity_kind="other"` (since the source-system granularity is coarser than "table"), `source_system=<system-name>`, `description=<relevant qa_pair answer>`, `provenance.producer_type="interview"`.
- Owning team / refresh cadence captured from qa_pairs if present (Session 56 prompt requests these).

**Trigger:** opt-in via a pipeline flag (e.g., `--inventory-from-intake`). Default off — intake coupling is still "not wired" per Session 56 gotcha #12.

### 5.4 External catalogs (future, post-Phase-4)

- **DataHub:** REST GraphQL endpoint → `DataSourceInventory`. Producer writes a Python script; output is a JSON file.
- **Amundsen / Collibra / ServiceNow data catalog:** same shape; different API adapters.
- **Query-log miners:** parse historical SQL from a log store; emit frequently-referenced tables as entries.

None of these are in scope for this plan. They are listed to pin the design target: the contract must not embed assumptions that block any of them.

---

## 6. Consumer integration

### 6.1 Entry point

**Decision:** `DataRequest` gains one new optional field.

```python
class DataRequest(StrictBase):
    ...
    database_hint: str | None = None
    data_source_inventory: DataSourceInventory | None = None    # NEW in Phase 3
    ...
```

### 6.2 Effect on generated SQL (Phase 3)

When `data_source_inventory` is present:

- `AnthropicLLMClient.generate_primary_queries` includes a summarized inventory block in the prompt (fully-qualified names, column lists, relevance reasons). The block is bounded — very large inventories get truncated with a token-budget cap; the Phase 3 implementation pins the exact truncation strategy.
- The LLM is instructed to prefer tables from the inventory over inventing table names.
- The `DataReport.summary` cites inventory-surfaced producer ids when the SQL references a specific entry, so auditors can trace provenance.

When `data_source_inventory` is absent, behavior is identical to today.

### 6.3 Precedence rules

| `database_hint` | `data_source_inventory` | Consumer behavior |
|-----------------|-------------------------|-------------------|
| None | None | Current behavior: pure LLM domain knowledge. |
| set | None | Current behavior: LLM uses the hint. |
| None | set (non-empty) | LLM uses inventory; no hint mentioned. |
| set | set (non-empty) | LLM uses inventory (richer); hint passed as context but not authoritative. |
| any | set (empty `entries=[]`) | Treated identically to inventory=None. |

### 6.4 Audit / observability

The `DataReport` is extended in Phase 3 so the summary can cite which inventory entries were used. Specific fields pinned in Phase 3 — probably `PrimaryQuery.inventory_entries_used: list[str]` (list of fully-qualified names) or a map in `DataReport.summary`. Phase 3 decides the final shape.

---

## 7. Alternatives considered

| Alternative | Pros | Cons | Why rejected |
|-------------|------|------|--------------|
| **A. Embed discovery inside `DataAgent.run()` as a pre-step.** | Single public API; simpler call graph. | Couples agent to one discovery mechanism. Curated teams have no clean bypass. Violates operator's §1.2 guidance. | **Rejected** — direct violation of operator guidance. |
| **B. Discovery as a terminal mode only (my original Option A).** | Simple first session. | No path to inventory-informed query generation; every analyst must manually translate discovery output into a DataRequest. | **Rejected** — half a solution; leaves consumer integration unspecified. |
| **C. Separate `packages/data-source-inventory/` from day one.** | Clean package boundary; inventory usable by non-data-agent consumers (website agent, intake agent). | Premature extraction. Two-package refactors inflate Phase 1 from 1 session to 2+. YAGNI: no other consumer is concretely demanding the contract today. | **Rejected for now** — revisit after Phase 3 if demand surfaces. |
| **D. Protocol-based producer interface from day one (in-process adapters only).** | Type-safe producer registration; runtime plug-in. | Excludes non-Python producers. Forces curated-input teams to ship a Python module. | **Rejected** — contract-as-data + optional-Protocol-later covers both in-process and external cases. |
| **E. Extend `database_hint` instead of adding a new field.** | No new schema. | `database_hint: str` can't carry structured data without becoming a JSON-in-a-string footgun. Versioning is impossible. | **Rejected** — the operator wants a "clear method," not a stuffed string. |
| **F. New top-level pipeline step "Step 2.5 — Source Discovery."** | Explicit placement in the 6-step pipeline. | Overbuilds for teams that skip discovery entirely (curated input). Step numbering churn. | **Rejected** — discovery is conditional; making it a mandatory step would force curated-input teams to emit a no-op. |

**F variant considered and deferred:** introduce a "Step 2.5" as an OPTIONAL virtual step, documented but not enforced. Not rejected outright — could be added to `CLAUDE.md` after Phase 3 ships, once the shape is validated. For now, the plan keeps the 6-step framing and treats inventory production as a sub-activity of Step 2 → Step 3 handoff.

---

## 8. Grep-based evidence inventory

All file lists below come from greps run Session 57. Per Learning #19 + #32 + #42 the numbers are fresh, not from memory.

### 8.1 `DataRequest` blast radius (49 files total — grep: `DataRequest`)

- **Production (13 files):** `packages/data-agent/src/model_project_constructor_data_agent/{schemas,__init__,cli,agent,anthropic_client,llm,state}.py`; `src/model_project_constructor/schemas/v1/{data,__init__}.py`; `src/model_project_constructor/orchestrator/{pipeline,adapters,__init__}.py`; `src/model_project_constructor/schemas/registry.py`.
- **Tests (10 files):** `tests/data_agent_package/test_anthropic_client.py`; `tests/orchestrator/{test_pipeline,test_adapters,test_checkpoints}.py`; `tests/scripts/test_run_pipeline_resume.py`; `tests/schemas/{test_envelope_and_registry,fixtures,test_data}.py`; `tests/agents/data/{conftest,test_data_agent}.py`.
- **Docs (26 files):** README.md, OPERATIONS.md, ROADMAP.md, TROUBLESHOOTING.md, CHANGELOG.md, BACKLOG.md (by transitive mention), SESSION_NOTES.md, `docs/tutorial.md`; `docs/planning/{resume-from-checkpoint-plan,scope-b-plan}.md`; `docs/architecture-history/{pilot-readiness-audit,github-gitlab-abstraction-plan,architecture-approaches,architecture-plan}.md`; `docs/wiki/claims-model-starter/{Agent-Reference,Pipeline-Overview,Worked-Examples,Schema-Reference,Extending-the-Pipeline,Security-Considerations,Software-Bill-of-Materials,Data-Guide,Changelog,Monitoring-and-Operations,Evolution,Architecture-Decisions}.md`; `packages/data-agent/USAGE.md`.

**Consequence:** Phase 3 (adding the optional field to `DataRequest`) can land as a non-breaking change without touching most of these files — the `| None = None` default preserves every existing call site. Doc updates in Phase 3 are bounded to files that describe the `DataRequest` shape directly (estimated ~6 files: `USAGE.md`, `Schema-Reference.md`, `Data-Guide.md`, `Worked-Examples.md`, `architecture-plan.md`, `Pipeline-Overview.md`).

### 8.2 `database_hint` usage (verify §3.4 backward-compat claim — grep: `database_hint`)

- **Production (2 files, 2 hits):** `packages/data-agent/.../schemas.py:55` (definition); `src/model_project_constructor/orchestrator/adapters.py:73` (currently passes `None`).
- **Tests (4 files, 10 hits):** `tests/orchestrator/test_adapters.py:121-124`; `tests/schemas/test_data.py:39,52,55-57,60`; `tests/agents/data/conftest.py:85`.
- **Fixtures (2 files, 2 hits):** `tests/fixtures/sample_datareport.json:21`; `tests/fixtures/sample_request.json:15`.
- **Docs (6 files, 9 hits):** `packages/data-agent/USAGE.md:48,92,152`; `docs/architecture-history/architecture-plan.md:301`; `docs/wiki/claims-model-starter/Schema-Reference.md:214,221`; `docs/wiki/claims-model-starter/Worked-Examples.md:73`; `docs/wiki/claims-model-starter/Security-Considerations.md:146,206`.

**Consequence:** `database_hint` stays (§3.4). Phase 3 doc updates explain precedence (§6.3) in these ~6 doc files.

### 8.3 `generate_primary_queries` call sites (Phase 3 signature extension — grep: `generate_primary_queries`)

- **7 files:** `packages/data-agent/.../llm.py` (Protocol); `anthropic_client.py` (impl); `nodes.py` (caller); `cli.py` (fake impl); `tests/data_agent_package/test_anthropic_client.py`, `tests/agents/data/test_data_agent.py`, `docs/planning/scope-b-plan.md`.

**Consequence:** Phase 3 signature change is bounded. Adding an optional kwarg `data_source_inventory=None` to the Protocol method preserves all 7 call sites without modification; tests that want to exercise the new path add one assertion.

### 8.4 `ReadOnlyDB` usage (Phase 2 method addition — grep: `ReadOnlyDB`)

- **18 files** — only 1 file (`db.py`) defines the class; the others import it. Adding a new method is purely additive.

### 8.5 Existing discovery / information_schema references (sanity check — grep: `discover|information_schema|catalog.{0,20}tables?|candidate.{0,10}tables?`)

- Matches are in SESSION_NOTES.md, CHANGELOG.md, BACKLOG.md, methodology docs, and the Session 56 intake test file. **Zero matches in any `packages/data-agent/` source or test file.** Confirms greenfield status.

### 8.6 Per-phase file inventory

| Phase | Production files touched | Production files added | Test files touched | Test files added | Doc files touched |
|-------|--------------------------|------------------------|---------------------|------------------|-------------------|
| 1: Contract schema | 2 (`schemas.py`, `__init__.py`) + 1 optional (`src/.../schemas/v1/data.py` re-export) | 0 | 0 | 1 (`tests/data_agent_package/test_inventory_schemas.py` OR extend `tests/schemas/test_data.py`) | 1 (`USAGE.md` adds a §Inventory types stub) |
| 2: `information_schema` producer | 3-4 (`db.py` +method, `cli.py` +subcommand, optionally `anthropic_client.py` +rank method) | 1 (`discovery.py`) | 0 | 2 (`tests/data_agent_package/test_discovery.py`, `tests/data_agent_package/test_cli_discover.py`) | 1 (`USAGE.md` §Example 4 — discovery mode) |
| 3: Consumer integration | 4 (`schemas.py` +field, `llm.py` Protocol, `anthropic_client.py` prompt, `nodes.py` plumb-through) + adapter decision | 0 | 3-4 (existing data-agent tests + `tests/orchestrator/test_adapters.py`) | 1 (new integration test) | ~6 (`USAGE.md`, `Schema-Reference.md`, `Data-Guide.md`, `Worked-Examples.md`, `Pipeline-Overview.md`, `architecture-plan.md` note) |
| 4 (optional): Intake coupling | 1-2 (`adapters.py` or new `inventory_adapters.py`) | 0-1 | 1 (`tests/orchestrator/test_adapters.py`) | 0-1 | 1 (`Pipeline-Overview.md` update) |

Counts are upper bounds. Implementation sessions may cover less if scope tightens during the phase.

---

## 9. Phased implementation

Each phase is one session. Session boundaries are hard — implementations that grow beyond one session's scope split, they do not bundle (FM #18).

### Phase 1 — Contract schema (Session 58)

**Deliverable:** the four Pydantic types (§4) exist, are importable, serialize-round-trip cleanly, and pass validation tests. No consumer or producer code. No CLI change.

**Scope:**
1. Add `DataSourceInventory`, `DataSourceEntry`, `ProducerMetadata`, `ColumnMetadata` to `packages/data-agent/src/model_project_constructor_data_agent/schemas.py`. Include the cross-field validator (§4.3) for producer-id integrity.
2. Re-export from `packages/data-agent/src/model_project_constructor_data_agent/__init__.py`.
3. Mirror the re-export in `src/model_project_constructor/schemas/v1/data.py` (consistency with `DataRequest` / `DataReport`).
4. Write `tests/data_agent_package/test_inventory_schemas.py` (or extend `tests/schemas/test_data.py`) covering: valid round-trip; empty entries; dangling `producer_id`; `schema_version` pinned; extra=forbid on a typo.
5. Add a sample curated fixture to `tests/fixtures/sample_curated_inventory.json` for use by future phases.

**Completion criteria:**
- `uv run python -c "from model_project_constructor_data_agent import DataSourceInventory"` succeeds.
- `uv run python -c "from model_project_constructor.schemas.v1.data import DataSourceInventory"` succeeds.
- `uv run pytest tests/data_agent_package/test_inventory_schemas.py -q` green (or new tests green within `test_data.py`).
- `uv run pytest -q` green overall with increased count (baseline 476 → ~485, give or take).
- `uv run ruff check src/ tests/ packages/` clean.
- `uv run mypy src/` and `uv run mypy packages/data-agent/src/` both clean.

**Session boundary:** Phase 1 closes when these criteria hold. Do NOT start Phase 2.

**Gotchas to forecast for Session 58:**
- The existing `DataRequest` docstring (`schemas.py:15-19`) forbids referencing `IntakeReport` or `schemas.v1.intake` — Phase 1 types must stay within that guarantee.
- `StrictBase` has `extra="forbid"` — `DataSourceEntry.extra: dict[str, Any]` is a DELIBERATE opening for producer-specific keys at runtime but at the SCHEMA level it is a typed field, not a forbidden-extra bypass.
- `ConfigDict(extra="forbid", protected_namespaces=())` must be applied consistently.

### Phase 2 — `information_schema` reference producer (Session 59)

**Deliverable:** a working standalone `discover` CLI subcommand that produces a valid `DataSourceInventory` JSON file from a database URL (fake-DB coverage only; live-DB deferred).

**Scope:**
1. Add `ReadOnlyDB.get_information_schema(schemas: list[str] | None = None) -> list[dict]` method in `db.py`. Queries `information_schema.tables`, `columns`, and (best-effort) `key_column_usage`. Returns a list of dicts suitable for building entries.
2. Add `probe_information_schema(db, ...) -> DataSourceInventory` function in a new `discovery.py` module.
3. Add `discover` CLI subcommand in `cli.py` with flags: `--db-url`, `--output`, `--include-schemas`, `--rank-with-llm`, `--fake-llm`.
4. Add fake `information_schema` fixture for tests (a list of table/column dicts).
5. Tests: unit tests for `probe_information_schema` using the fake fixture; CLI smoke test with `--fake-llm` and a fake DB.

**Completion criteria:**
- `uv run model-data-agent discover --help` shows the subcommand.
- `uv run model-data-agent discover --db-url <test-sqlite-url> --output /tmp/inv.json --fake-llm` exits 0 and writes a file that parses as `DataSourceInventory`.
- Unit tests cover: success path, empty DB, permission-denied on `information_schema` (producer emits entries=[] with a note).
- All four gate commands (pytest / ruff / mypy-src / mypy-packages) green.

**Session boundary:** Phase 2 closes here. Do NOT wire this into `DataAgent.run()` yet.

**Gotchas to forecast for Session 59:**
- `information_schema` dialects differ. Phase 2 targets PostgreSQL + SQLite; other dialects are best-effort via a `NotImplementedError` fallback.
- `anthropic_client.py` may need a new `rank_candidate_tables` LLM method if the `--rank-with-llm` flag is scoped in. If the ranking adds scope pressure, DEFER it — ranking without LLM is still a valid mode (producer just emits `relevance_score=None`).
- The existing `--fake-llm` flag re-use: ensure the fake client grows a `rank_candidate_tables` stub if the method is added.

### Phase 3 — Consumer integration (Session 60)

**Deliverable:** `DataRequest.data_source_inventory` field accepted end-to-end; `generate_primary_queries` uses the inventory when present; current behavior preserved when absent.

**Scope:**
1. Add `data_source_inventory: DataSourceInventory | None = None` to `DataRequest` in `schemas.py`.
2. Extend the `LLMClient.generate_primary_queries` protocol signature to accept `data_source_inventory=None`. Update `AnthropicLLMClient.generate_primary_queries` to include an inventory block in its prompt when present. Update `nodes.py` to pass inventory through from state.
3. Decide DataReport shape for provenance citation (§6.4) — likely `PrimaryQuery.inventory_entries_used: list[str]` or a field on `SummaryResult`.
4. Update `src/model_project_constructor/orchestrator/adapters.py:63-77` to optionally accept / pass an inventory (default None).
5. Update `USAGE.md` with a §Example 5 — running with an inventory.
6. Update `docs/wiki/claims-model-starter/Schema-Reference.md`, `Data-Guide.md`, and the relevant `Worked-Examples.md` section.
7. Tests: inventory-populated request produces SQL that cites an inventory-named table (assertion on generated SQL string); inventory-absent request matches current-baseline behavior; round-trip of a request with and without inventory.

**Completion criteria:**
- `uv run pytest -q` green (existing tests unchanged; new tests added for inventory path).
- Fake-LLM run with inventory produces a `DataReport` whose primary_queries reference inventory-named tables (the fake-LLM must respect the new prompt hint — Phase 3 updates `_FakeCLIClient` if necessary).
- Absence of inventory continues to use `database_hint`.
- Schema-version of `DataSourceInventory` is asserted against a "1.x.y" tolerance in consumer code.
- All four gate commands clean.

**Session boundary:** Phase 3 closes here. Phase 4 is OPTIONAL.

**Gotchas to forecast for Session 60:**
- **MAX_TOKENS headroom.** Large inventories may balloon prompt tokens past `DEFAULT_MAX_TOKENS = 4096` (`anthropic_client.py:49`). Phase 3 implements truncation: rank by `relevance_score` (if present), then emit top N entries, append a "... and M more sources truncated" note. Exact N pinned during implementation.
- **Prompt injection.** `DataSourceEntry.description` is LLM-consumed. If a producer emits adversarial content, the downstream LLM may be misdirected. Phase 3 sanitizes (strip control chars, bound per-field length) — mirrors how `qa_pairs` content is handled today in `anthropic_client.py`.
- **Backward-compat:** every test in `tests/data_agent_package/` and `tests/agents/data/` must continue to pass without modification. Fresh test coverage goes in new tests, not by mutating existing ones.

### Phase 4 (optional) — Intake coupling (Session 61+)

**Deliverable:** a pipeline flag that converts Session 56 intake-captured stakeholder-named systems into inventory entries with `producer_type="interview"`.

**Scope:**
1. Add a converter in `src/model_project_constructor/orchestrator/adapters.py` (or `inventory_adapters.py`) that reads `IntakeReport.qa_pairs` and emits a `DataSourceInventory`.
2. Opt-in via flag (probably `--inventory-from-intake`).
3. When both `--inventory-from-intake` and a `--curated-inventory` path are given, merge: curated entries win on duplicate `fully_qualified_name`; interview entries enrich (not override).
4. Tests in `tests/orchestrator/` covering the conversion.

**Completion criteria:**
- `uv run pytest -q` green.
- Integration test: pipeline run with `--inventory-from-intake` produces a DataReport whose summary cites interview-sourced entries.
- All four gate commands clean.

**Deferred to / blocked on:** pilot demand. If no pilot run surfaces the need, Phase 4 may stay unimplemented indefinitely. This is deliberate — the contract supports it; shipping it without use-case grounding is YAGNI.

---

## 10. Impact analysis

| System / file | Phase touched | Impact | Risk level |
|---------------|---------------|--------|------------|
| `packages/data-agent/.../schemas.py` | 1, 3 | New types added (1); existing `DataRequest` gains optional field (3) | Low — additive |
| `packages/data-agent/.../db.py` | 2 | New method added; existing methods unchanged | Low — additive |
| `packages/data-agent/.../cli.py` | 2 | New subcommand added; `run` subcommand unchanged | Low — additive |
| `packages/data-agent/.../anthropic_client.py` | 2 (optional), 3 | New LLM method (2, optional); existing `generate_primary_queries` prompt extended (3) | Medium — prompt changes can affect LLM output shape. Phase 3 pins test assertions against fake-LLM response structure, not Claude-verbatim output |
| `packages/data-agent/.../llm.py` (Protocol) | 3 | Protocol signature extended with optional kwarg | Low — existing impls unaffected |
| `packages/data-agent/.../nodes.py` | 3 | `generate_queries` node plumbs inventory through state | Low |
| `packages/data-agent/.../state.py` | 3 | `DataAgentState` gains optional `data_source_inventory` key (already `total=False`) | Low |
| `src/model_project_constructor/schemas/v1/data.py` | 1, 3 | New re-exports | Low |
| `src/model_project_constructor/orchestrator/adapters.py` | 3, 4 | Optional inventory pass-through | Low |
| All existing tests | 1, 2, 3 | Must continue passing unchanged | High — any break indicates regression |
| Docs (~6 files) | 3, 4 | Describe new field and precedence | Low |
| `CHANGELOG.md`, `BACKLOG.md` | every phase | Entry + phase-line removal | Low — mechanical |

**Blast-radius summary:** The total blast radius across all four phases is ~12 production files, ~8 test files, ~6 doc files. Each phase keeps its blast radius under the 5-file SAFEGUARDS rule when measured per session.

**Backward compatibility:** every change is additive. The plan explicitly preserves `database_hint` (§3.4), accepts absent inventory everywhere (§3.5), and does not rename or remove any existing field or method.

---

## 11. Verification plan (overall)

**Per-phase:** see "Completion criteria" in §9.

**Cross-phase / plan-completion:**

- After Phase 3, the following end-to-end invariant holds: a `DataRequest` with a non-empty `data_source_inventory` produces a `DataReport` whose `primary_queries[0].sql` references at least one table name that appears in `data_source_inventory.entries[*].fully_qualified_name`. Assertion covered by a fake-LLM integration test.
- After Phase 3, a `DataRequest` without a `data_source_inventory` produces identical output to today for every existing fixture — pinned by re-running the baseline test suite.
- Per Learning #21 / Session 26: confirm that adding inventory does NOT change any DataAgent status-decision logic. `DataAgent.run()` routes to `COMPLETE` / `INCOMPLETE_REQUEST` / `EXECUTION_FAILED` on the same criteria as today; inventory presence/absence does not add a new status. (Phase 3 implementation must verify this explicitly — the status-decision surface is at `agent.py:55-61`.)

**Decoupling guarantee preservation:** `tests/test_data_agent_decoupling.py` AST-walks every module in `packages/data-agent/` and rejects any import of `IntakeReport` or `schemas.v1.intake`. This plan's Phase 1-3 add no such imports; the interview-sourced producer (Phase 4) lives in the orchestrator package, outside the walled garden. The decoupling test continues to pass unchanged.

---

## 12. Open questions / deferred decisions

Each of these is flagged for the phase where it becomes decidable. Implementation sessions resolve these; this plan names them so they are not forgotten.

| Q# | Question | Phase that decides |
|----|----------|--------------------|
| Q1 | Should `DataSourceEntry.relevance_score` be `float` (0.0-1.0) or a `Literal["low", "medium", "high"]`? Producers may not have calibrated scores. | Phase 1. Default: `float \| None`. |
| Q2 | Is there a Protocol `DataSourceProducer` for in-process producers, or is the contract purely data? | Phase 2. Default per §3.2: pure data; Protocol optional, defer unless Phase 2 shows concrete need. |
| Q3 | Should the `discover` CLI subcommand live in the standalone package or in a separate future `packages/data-source-inventory/`? | Phase 2. Default per §2 non-goals: standalone data-agent package. |
| Q4 | Truncation strategy when inventory exceeds prompt token budget — top-N by relevance, bucket-balanced by entity_kind, or something else? | Phase 3. |
| Q5 | Sanitization: strip only control chars, or bound per-field length too? What's the limit? | Phase 3. Default: strip control chars; bound `description` and `relevance_reason` at 2000 chars each. |
| Q6 | Should `DataReport` expose inventory-provenance to downstream consumers (pipeline → website agent)? | Phase 3. Default: yes, via `PrimaryQuery.inventory_entries_used: list[str]`. |
| Q7 | How does `--curated-inventory` CLI flag interact with multi-file curated inputs? One file only, or glob? | Phase 2 or Phase 3. Default: one file; revisit if multi-source merging becomes a common need. |
| Q8 | Is a YAML loader (in addition to JSON) part of scope for curated inputs? | Phase 1. Default: JSON only for Phase 1; YAML is a thin wrapper that can be added later without contract changes. |
| Q9 | Do we emit a dedicated `schema_version` check for the contract, or rely on Pydantic's default rejection of unknown `schema_version` Literals? | Phase 1. Default: Literal-based pinning; a runtime compat shim is out of scope. |
| Q10 | Should `DataSourceEntry.business_domain` be an enum or free text? | Phase 1. Default: free text (P&C subdomain taxonomies vary). |
| Q11 | What's the deprecation path (if any) for `database_hint` once inventory covers 100% of use cases? | Post-Phase-3, separate BACKLOG item. |

---

## 13. References

- **Operator guidance (Session 57):** captured verbatim in `memory/feedback_data_source_discovery.md` (auto-memory, project-scoped).
- **Filing-session grounding:** `docs/architecture-history/initial_purpose.txt:88`.
- **Data Agent implementation:** `packages/data-agent/src/model_project_constructor_data_agent/` (12 files).
- **Standalone package USAGE:** `packages/data-agent/USAGE.md`.
- **Pipeline orchestrator adapter:** `src/model_project_constructor/orchestrator/adapters.py:63-77`.
- **Session 56 intake probe (human-side discovery):** `src/model_project_constructor/agents/intake/anthropic_client.py:33-42` (SYSTEM_INTERVIEWER with 9 P&C-claims-domain systems).
- **Decoupling guarantee test:** `tests/test_data_agent_decoupling.py`.
- **Workstream doc:** `docs/methodology/workstreams/ARCHITECTURE_WORKSTREAM.md`.
- **Failure modes referenced:** FM #18 (planning-to-implementation bleed), FM #19 (plan-mode bypass), Learning #18 (scope discipline), Learning #21 (status-decision invariant), Learning #19 / #32 / #42 (grep evidence discipline).

---

## 14. Planning Session Checklist (per SESSION_RUNNER.md)

- [x] Plan document written with file paths and line numbers (§1.4, §8, §9, §10, §13).
- [x] Grep-based inventory completed for affected symbols (§8 — four separate greps, file lists, counts).
- [x] Each phase has explicit completion criteria and verification commands (§9).
- [x] Each phase marked as "separate session" with a STOP point (§9 "Session boundary" in each phase).
- [ ] Close-out: evaluate predecessor, self-assess, commit, STOP. ← pending this session's Phase 3 close-out.
