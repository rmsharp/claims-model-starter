# model-project-constructor-data-agent

A standalone Data Agent that turns a structured data request into executed SQL
queries, quality-check results, and a narrative `DataReport`. Distributed as a
separate Python package so analyst teams can use it outside the full
`model-project-constructor` pipeline.

The Data Agent has exactly one public entry point:

```python
DataAgent(llm, db).run(request) -> DataReport
```

It has three supported usage modes: the `model-data-agent` CLI, Python in a
script, and Python in a notebook. All three construct a `DataRequest`, hand
it to `DataAgent.run`, and receive a `DataReport`. See architecture-plan.md §7
for the design rationale.

## Installation

```bash
# From the monorepo checkout:
uv pip install -e packages/data-agent

# As a standalone distribution (once published):
pip install model-project-constructor-data-agent
```

Set `ANTHROPIC_API_KEY` in your environment before using the default
`AnthropicLLMClient`:

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

## Example 1 — CLI

Write a `request.json` matching the `DataRequest` schema:

```json
{
  "schema_version": "1.0.0",
  "target_description": "subrogation recovery amount on TX auto claims",
  "target_granularity": {"unit": "claim", "time_grain": "event"},
  "required_features": ["paid_amount", "state", "loss_date"],
  "population_filter": "TX auto claims with loss in 2024",
  "time_range": "2024-01-01 to 2024-12-31",
  "database_hint": "claims",
  "source": "standalone",
  "source_ref": "analyst-request-2026-04-14"
}
```

Then run:

```bash
model-data-agent run \
    --request request.json \
    --output report.json \
    --db-url "postgresql+psycopg://readonly_user@db.internal/claims"
```

Options:
- `--db-url` is optional; if omitted, quality checks are generated but not
  executed, and each is marked `NOT_EXECUTED` in the report.
- `--model` overrides the default Claude model (default is a fast/economical
  Sonnet build).
- `--fake-llm` substitutes a deterministic stub and is intended for smoke
  tests only — it does not produce real analysis.

The CLI exits 0 on success and writes the `DataReport` as indented JSON to the
path given by `--output`. The terminal prints a single confirmation line with
the report's `status`.

## Example 2 — Python in a script

```python
from model_project_constructor_data_agent import (
    DataAgent,
    DataGranularity,
    DataRequest,
    ReadOnlyDB,
)
from model_project_constructor_data_agent.anthropic_client import AnthropicLLMClient

request = DataRequest(
    target_description="subrogation recovery amount on TX auto claims",
    target_granularity=DataGranularity(unit="claim", time_grain="event"),
    required_features=["paid_amount", "state", "loss_date"],
    population_filter="TX auto claims with loss in 2024",
    time_range="2024-01-01 to 2024-12-31",
    database_hint="claims",
    source="standalone",
    source_ref="analyst-script-2026-04-14",
)

llm = AnthropicLLMClient()  # reads ANTHROPIC_API_KEY
db = ReadOnlyDB("postgresql+psycopg://readonly_user@db.internal/claims")

agent = DataAgent(llm=llm, db=db)
report = agent.run(request)

print(report.status)
print(report.summary)
for pq in report.primary_queries:
    print(f"  {pq.name}: {pq.expected_row_count_order} rows expected")
    for qc in pq.quality_checks:
        print(f"    [{qc.execution_status}] {qc.check_name}")
```

Handle the three possible statuses explicitly:

```python
if report.status == "COMPLETE":
    save_to_results_table(report)
elif report.status == "INCOMPLETE_REQUEST":
    raise ValueError(f"request was vacuous: {report.data_quality_concerns}")
elif report.status == "EXECUTION_FAILED":
    log.error(f"data agent failed: {report.summary}")
```

The agent **never raises** for expected failure modes — every failure is
returned as a valid `DataReport` with `status` ∈
{`COMPLETE`, `INCOMPLETE_REQUEST`, `EXECUTION_FAILED`}. Callers can treat
`run()` as total for these three outcomes.

## Example 3 — Python in a notebook

Same API, with the typical notebook ergonomics. Persist the report to disk so
you can reload it without re-running the LLM.

```python
from pathlib import Path
import json

from model_project_constructor_data_agent import (
    DataAgent,
    DataGranularity,
    DataReport,
    DataRequest,
    ReadOnlyDB,
)
from model_project_constructor_data_agent.anthropic_client import AnthropicLLMClient

# Cell 1 — build and run
request = DataRequest(
    target_description="subrogation recovery amount on TX auto claims",
    target_granularity=DataGranularity(unit="claim", time_grain="event"),
    required_features=["paid_amount", "state", "loss_date"],
    population_filter="TX auto claims with loss in 2024",
    time_range="2024-01-01 to 2024-12-31",
    database_hint="claims",
    source="standalone",
    source_ref="analyst-notebook-2026-04-14",
)

agent = DataAgent(
    llm=AnthropicLLMClient(),
    db=ReadOnlyDB("sqlite:///claims.db"),
)
report = agent.run(request)

# Cell 2 — persist so you can reload without paying LLM tokens again
Path("report.json").write_text(json.dumps(report.model_dump(mode="json"), indent=2))

# Cell 3 — reload on a subsequent run of the notebook
report = DataReport.model_validate(json.loads(Path("report.json").read_text()))

# Cell 4 — explore
import pandas as pd
rows = [
    {
        "query": pq.name,
        "check": qc.check_name,
        "status": qc.execution_status,
        "summary": qc.result_summary,
    }
    for pq in report.primary_queries
    for qc in pq.quality_checks
]
pd.DataFrame(rows)
```

## Example 4 — Data-source discovery (`discover` CLI)

The package ships a reference producer for the data-source-inventory contract
that probes a live database's `information_schema` and emits a valid
`DataSourceInventory` JSON file. Useful as a standalone analyst tool (Phase 2
of the inventory plan) and as a building block for automated pipeline flows.

```bash
# Discover every accessible schema except information_schema / pg_catalog:
model-data-agent discover \
    --db-url "postgresql+psycopg://readonly_user@db.internal/claims" \
    --output inventory.json

# Limit to specific schemas (repeatable flag):
model-data-agent discover \
    --db-url "postgresql+psycopg://readonly_user@db.internal/claims" \
    --output inventory.json \
    --include-schemas public \
    --include-schemas claims_domain

# Ask the LLM to rank each discovered table's relevance to a request context:
model-data-agent discover \
    --db-url "postgresql+psycopg://readonly_user@db.internal/claims" \
    --output inventory.json \
    --rank-with-llm \
    --request-context "subrogation recovery classifier"
```

The command writes a JSON file conforming to `DataSourceInventory` and
exits 0 with a one-line confirmation (`wrote inventory.json (N entries)`).
When reflection fails (permission denied, unsupported dialect), the output
still conforms to the contract — `entries` is empty and the single
`ProducerMetadata` carries a `notes` field naming the cause.

The same behavior is available in Python via `probe_information_schema`:

```python
from model_project_constructor_data_agent import (
    ReadOnlyDB,
    probe_information_schema,
)

db = ReadOnlyDB("postgresql+psycopg://readonly_user@db.internal/claims")
db.connect()
try:
    inventory = probe_information_schema(
        db,
        include_schemas=["public"],
        request_context="subrogation recovery model",
    )
finally:
    db.close()

print(f"{len(inventory.entries)} tables/views discovered")
```

## Public API

All names below are importable from the top-level package:

```python
from model_project_constructor_data_agent import (
    DataAgent,           # the agent class
    DataGranularity,     # schema: unit + time_grain
    DataReport,          # schema: complete output
    DataRequest,         # schema: input
    Datasheet,           # schema: Gebru 2021 datasheet
    PrimaryQuery,        # schema: generated SQL + QC + datasheet
    QualityCheck,        # schema: single QC result
    # Data-source-inventory contract (see "Data source inventory" below)
    ColumnMetadata,      # schema: per-column metadata
    DataSourceEntry,     # schema: one table/view/dataset entry
    DataSourceInventory, # schema: collection of entries + producer metadata
    ProducerMetadata,    # schema: which tool produced which entries
    probe_information_schema,  # automated producer (information_schema probe)
    ReadOnlyDB,          # SQLAlchemy wrapper (.get_information_schema() for discovery)
    LLMClient,           # Protocol — implement this for alternate LLM vendors
    PrimaryQuerySpec,    # intermediate dataclass returned by LLMClient
    QualityCheckSpec,    # intermediate dataclass returned by LLMClient
    SummaryResult,       # intermediate dataclass returned by LLMClient
    TableRanking,        # intermediate dataclass for LLM-ranked discovery results
    DBConnectionError,   # exception
)
from model_project_constructor_data_agent.anthropic_client import (
    AnthropicLLMClient,
    LLMParseError,
)
```

## Data source inventory

The data agent accepts an optional `DataSourceInventory` describing which
tables / views / datasets are relevant to a `DataRequest`. The inventory is a
plug-in contract: discovery (identifying sources) is a separate activity,
and multiple producer classes populate the same consumer shape:

- **Curated** — hand-maintained JSON/YAML files from teams that already know
  their canonical tables and factors. No code required.
- **Automated** — probes like `information_schema` against a live DB
  (reference implementation is planned for a future release).
- **Interview** — converter from stakeholder-named systems captured by the
  intake agent (Guidewire, Duck Creek, etc.) into inventory entries.
- **External catalog** — DataHub, Amundsen, Collibra, and similar metadata
  catalogs (future).

Phase 1 shipped the schema. Phase 2 ships the `information_schema` reference
producer (Example 4 above): `probe_information_schema` + `model-data-agent
discover` + `ReadOnlyDB.get_information_schema`. The downstream consumer
integration (plumbing `DataRequest.data_source_inventory` through to the
query-generation prompt) lands in a later phase; today's callers continue to
work unchanged. See
`docs/planning/data-source-inventory-contract-plan.md` for the full plan and
`tests/fixtures/sample_curated_inventory.json` for a valid curated-producer
example.

## Error contract

- `DataAgent.run()` never raises for expected failure modes.
- Unexpected exceptions inside the graph are caught at the outer boundary and
  surfaced as `DataReport(status="EXECUTION_FAILED")`.
- `AnthropicLLMClient` raises `LLMParseError` on unparseable Claude output;
  this propagates through the outer boundary and becomes `EXECUTION_FAILED`.
- `ReadOnlyDB.connect()` raises `DBConnectionError` on connect failure;
  `DataAgent` catches it and routes the QC stage to `NOT_EXECUTED`.

## Decoupling guarantee

This package has zero runtime dependency on the main
`model_project_constructor` package. It cannot import `IntakeReport` or any
intake-side code. A CI test (`tests/test_data_agent_decoupling.py`) AST-walks
every module here and fails the build on any `import` that references the
intake schema. See architecture-plan.md §7 for details.
