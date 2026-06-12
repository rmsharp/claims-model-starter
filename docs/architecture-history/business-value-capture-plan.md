> *This document is a concept-era artifact preserved for design archaeology. It describes the system as designed on 2026-06-12 and may not reflect current implementation. For current state, see `docs/wiki/claims-model-starter/Evolution.md` (design-decision arc) and the code itself (authoritative). See `PROJECT_CONVENTIONS.md` for archive scope.*

# Business Value Capture — Multi-Phase Documentation & Schema Plan

**Status:** DRAFT — authored Session 85 (2026-05-21). Implementation begins Session 86 at Phase 1.
**Workstream:** `docs/methodology/workstreams/ARCHITECTURE_WORKSTREAM.md` (schema + documentation contract); subsequent phases mix into DEVELOPMENT_WORKSTREAM.
**Operator direction (verbatim, Session 85):** "Create a plan that ensures that part of the model intake and design collects the information needed to present the business value of the model prior to model construction and that the necessary information is collected to demonstrate business value downstream once the model is in production." Follow-up: "modify documentation to reflect capturing of business value."
**Phase 1A contract resolution (AskUserQuestion, Session 85):** Multi-phase plan + full grep-based evidence inventory (per Learnings #1, #19).
**Memory reference:** `feedback_data_source_discovery.md` (separation of concerns principle informs Phase 3 plumbing — the data agent collects baselines downstream of the intake-defined contract).

---

## 1. Context

### 1.1 Problem statement

The pipeline today captures **estimated** business value at intake (`EstimatedValue` — narrative + USD low/high band + confidence + assumptions, `src/model_project_constructor/schemas/v1/intake.py:27-32`) and surfaces it in two generated documents (`render_qmd_business_understanding`, `render_qmd_implementation_plan`, `src/model_project_constructor/agents/website/templates.py:303-409`). Two gaps prevent the pipeline from being load-bearing on business-value capture:

1. **Pre-construction presentation is thin.** The current `Estimated Value` section is single-paragraph narrative plus a USD band. There is no business case framing — no cost of inaction, no implementation cost band, no payback horizon, no named value drivers, no decision rights for go/no-go. The stakeholder sees an estimate but not a case.

2. **Downstream demonstration has no plumbing.** `render_qmd_implementation_plan` ends with the literal TODO at `templates.py:406-408`:
   > "Define the pre/post metric and the measurement window before shipping. This section is intentionally sparse — the Data Science team owns the measurement plan."

   There is no captured baseline metric, no counterfactual design, no attribution method, no production logging contract, no review cadence, no success criteria. Post-production demonstration of value cannot be done from pipeline outputs — every artifact the data science team needs lives outside the system.

### 1.2 Operator follow-up clarification (verbatim, Session 85)

> "modify documentation to reflect capturing of business value."

**Interpretation (this plan's scope):** Documentation in three senses, all in scope:

- **Generated documentation** (intake/data/website MDs produced by the pipeline) — Phases 4, 5.
- **Design documentation** (architecture-plan, wiki pages, tutorial) that describes what the pipeline does — Phases 1, 2, 3, 5, 6.
- **Schema-as-documentation** (the EstimatedValue schema IS the contract that downstream code reads as documentation) — Phase 1.

Each phase explicitly enumerates the documentation surfaces it touches.

### 1.3 Filing-session grounding

- `CLAUDE.md` §"The 6-Step Pipeline" — Step 1 captures *estimated value*; Step 5's generated website includes "Implementation Plans & Measuring Value." Both surfaces exist; neither is load-bearing on value capture today.
- `docs/architecture-history/initial_purpose.txt:44-46` — the original framing: "Estimated Value: This section is a rough estimate of the value based on the interviewee's understanding of the problem and solution, but guided and informed by the interviewer's expertise." The worked example at lines 74-76 (subrogation) explicitly says "The exact value will be calculated using historic data once the model has been deployed" — i.e. the **demonstration** path was always implied but never wired.
- `docs/architecture-history/architecture-plan.md:510` + lines 555-562 — the existing monitoring-cadence table (cycle_time → monitoring frequency) is a hook for value-cadence; we extend rather than replace it.
- `feedback_data_source_discovery.md` — the principle that "discovery is upstream, a contract is the plug-in boundary" informs Phase 3: the data agent **executes** the baseline collection but **does not define** the baseline metric. The metric definition is intake's contract; the data agent is a consumer.

### 1.4 Current-state summary (grep-verified, Session 85)

Counts collected via `grep -rn` (raw-string per Learning #38) against `src/`, `packages/`, `tests/`, `docs/` on 2026-05-21:

| Surface | Files | Counts | Notes |
|---------|-------|--------|-------|
| **Canonical schema** (`class EstimatedValue`) | `src/model_project_constructor/schemas/v1/intake.py:27-32` (1 def); `docs/architecture-history/architecture-plan.md:248`, `docs/wiki/claims-model-starter/Schema-Reference.md:131` (2 doc mirrors) | 3 definitions | Plan extends only the canonical; doc mirrors track in Phase 6. |
| **Field plumbing** (`estimated_value`) | 24 hits in `src/`, 28 in `tests/`, 15 in `docs/` | 67 total | Phases 1+2+5 modify code surfaces; Phase 3 + Phase 6 modify docs. |
| **Intake fixtures** (YAML `estimated_value:` block) | `tests/fixtures/subrogation.yaml`, `subrogation_b2.yaml`, `fraud_triage.yaml`, `pricing_optimization.yaml`, `intake_question_cap.yaml`, `intake_revision_cap.yaml`, `_b2_failmode.yaml` | 7 files | All 7 extended in Phase 2. |
| **Wiki pages** (any value/measurement reference) | `Schema-Reference.md`, `Intake-Interview-Design.md`, `Worked-Examples.md`, `Pipeline-Overview.md`, `Monitoring-and-Operations.md`, `Governance-Framework.md`, `Generated-Project-Structure.md`, `Data-Guide.md` | 8 pages | Each touched in the phase that owns its semantic surface (not all in one sweep). |
| **Architecture-plan refs** (`EstimatedValue`, `estimated_value`, `Estimated Value`) | `docs/architecture-history/architecture-plan.md:135, 248, 272, 460` | 4 hits | Phase 1 + Phase 6 update sections §5.1, §5.5 (NEW), §6, §8. |
| **Website template TODO** (the load-bearing gap) | `src/model_project_constructor/agents/website/templates.py:406-408` | 1 site | Phase 5 replaces with structured Production Measurement Plan. |
| **Data agent obligations** (`DataReport` schema) | `packages/data-agent/src/model_project_constructor_data_agent/schemas.py:95-104` | 1 schema | Phase 3 extends with `baseline_snapshot`. |

Per Learning #8 (TYPE / FIELD / STATE KEY / DOCSTRING surfaces separately), the per-grep enumeration is in **Appendix A**.

### 1.5 What this plan is and is not

**Is:** A six-phase implementation plan. Each phase is one session. Each phase modifies code AND its corresponding documentation surfaces — the phases are sliced by semantic surface (schema → intake → data → website-pre → website-post → cross-doc), not by activity type (all-code-then-all-docs).

**Is not:** Code. Per Failure Modes #18, #19 (planning-to-implementation bleed, plan-mode bypass), Session 85 writes only this plan + closes out. Session 86 opens Phase 1.

**Is not:** A wholesale rewrite of `EstimatedValue`. Existing fields stay; new fields are additive and optional at the schema level (required for `COMPLETE` status at the intake-finalize step — see §4.3). Existing fixtures continue to validate; Phase 2 extends them.

**Is not:** Production telemetry infrastructure. Phase 5 emits *TODO scaffolding* into the generated website's measurement plan — actual production logging is a downstream concern of the data-science team that picks up the generated repo.

---

## 2. Non-goals

- **No rename or removal of existing fields.** `EstimatedValue.narrative`, `annual_impact_usd_low`, `annual_impact_usd_high`, `confidence`, `assumptions` all stay. Fixture migrations are additive.
- **No new package.** All schemas extend `src/model_project_constructor/schemas/v1/intake.py` and `packages/data-agent/src/model_project_constructor_data_agent/schemas.py`. No `packages/value-measurement/` extraction.
- **No coupling to a specific BI / observability vendor.** The Production Measurement Plan is vendor-neutral prose + a logging requirements list; it names *what* must be logged, not Datadog / Grafana / Looker / Splunk specifically.
- **No mandatory live-LLM intake re-run for existing fixtures.** Phase 2 extends fixtures by hand; live-LLM validation is a separate optional pilot.
- **No retroactive change to already-generated downstream repos.** Existing claims-model-starter wiki entries describe what *was* generated; new wiki content describes what *will be* generated post-implementation.
- **No A/B-test orchestration logic.** The plan captures *that* a counterfactual exists and *what* type; it does not implement experiment management.

---

## 3. Strategic decisions (cross-phase invariants)

Per Learning #9 — invariants in one document, not duplicated across phase docs.

### 3.1 Schema partition

**Decision:** Extend `EstimatedValue` with pre-construction business-case fields **AND** add a sibling top-level field `IntakeReport.value_measurement_plan: ValueMeasurementPlan` for downstream production demonstration.

**Why:** Pre-construction estimation and post-production measurement are different concerns at different lifecycle stages with different question patterns at intake. Bundling them inside `EstimatedValue` would force `EstimatedValue` to outgrow its current role ("a rough estimate"). The sibling structure keeps the estimate small and the measurement plan visible at the IntakeReport top level.

**Invariant:** `EstimatedValue` and `ValueMeasurementPlan` never reference each other in Python type signatures (no circular dependency). The two schemas are independently composable — a future analyst tool may emit only one of them.

### 3.2 Baseline collection lives in the data agent

**Decision:** Intake captures the *definition* of the baseline metric (name + formula + measurement window). The data agent generates the SQL, executes it, captures the value, and returns it in `DataReport.baseline_snapshot`.

**Why:** Intake has no database access — it cannot measure the baseline. Data agent has database access. Per `feedback_data_source_discovery.md`, the data agent is a consumer of intake-defined contracts.

**Invariant:** No code in `src/model_project_constructor/agents/intake/` queries a database. No code in `packages/data-agent/` defines the metric semantics (only executes them).

### 3.3 `ValueMeasurementPlan` is required for `COMPLETE` status

**Decision:** A `DRAFT_INCOMPLETE` IntakeReport may omit `value_measurement_plan`; a `COMPLETE` IntakeReport must have it (with at least `baseline_metric_name` and `evaluation_horizon_months` non-null).

**Why:** Allowing `COMPLETE` without a measurement plan would defeat the purpose. The intake LLM should drive toward the plan as part of the interview, alongside model_solution and estimated_value.

**Invariant:** The Phase 2 prompt update extends the "drive toward N required sections" framing in `docs/wiki/claims-model-starter/Intake-Interview-Design.md` from four to five. The `finalize` node's status-decision logic (`src/model_project_constructor/agents/intake/nodes.py:142`, per Learning #21) gains a `value_measurement_plan` presence check.

### 3.4 Production logging is TODO scaffolding, not implementation

**Decision:** Phase 5 generates a structured **logging requirements list** in the website's `06_implementation_plan.qmd` and an **ongoing measurement playbook** in `governance/ongoing_monitoring.md`. The generated repo's data-science team is responsible for wiring actual logging.

**Why:** The pipeline is a project scaffolder, not a runtime. Implementing real production logging would couple us to a specific stack.

**Invariant:** No generated file ever contains executable logging code (no `import datadog`, no `wandb.log(...)`). Logging is prose + checklists.

### 3.5 The estimate and the demonstration are different artifacts

**Decision:** `EstimatedValue.annual_impact_usd_low/high` is forever an **estimate**; the data agent's `baseline_snapshot.value` + the post-production demonstration is the **audit path**.

**Why:** The estimate is the intake-time best guess; it does not become "wrong" if production shows a different number. The demonstration is the source of truth post-deployment.

**Invariant:** Phase 5 templates explicitly label the estimate as "estimate at intake" and the production-measurement-plan section as "measurement methodology — outcomes flow here post-deployment." No retroactive overwrite of the estimate.

### 3.6 Decision rights are captured but advisory

**Decision:** `ValueMeasurementPlan.decision_rights` records who reviews and what thresholds trigger retire/retrain. This is **advisory text**, not workflow automation.

**Why:** Decision rights vary by organization; encoding workflow would couple us to a specific governance regime.

**Invariant:** The intake interview asks for decision rights as free-form prose; the website templates surface it in `governance/deployment_gates.md` and `governance/ongoing_monitoring.md` as a checklist. No state-machine enforcement.

---

## 4. Proposed schema extensions (concrete fields)

These shapes are **proposals** for Phase 1 to refine. The Plan locks the architectural separation (§3.1) and the field intent (below); implementation may rename for clarity.

### 4.1 `EstimatedValue` (extended)

Existing five fields preserved. New fields (all `Optional` at schema level, required for `COMPLETE` at finalize-time):

| Field | Type | Purpose |
|-------|------|---------|
| `cost_of_inaction_narrative` | `str` | Prose: what continues to cost the business if the model is NOT built. |
| `annual_cost_of_inaction_usd_low` | `float \| None` | USD lower bound of inaction cost. |
| `annual_cost_of_inaction_usd_high` | `float \| None` | USD upper bound of inaction cost. |
| `implementation_cost_band_usd_low` | `float \| None` | Estimated build cost lower bound (team-quarters × loaded rate, or similar). |
| `implementation_cost_band_usd_high` | `float \| None` | Estimated build cost upper bound. |
| `payback_months` | `int \| None` | Months until cumulative captured value exceeds cumulative build cost. |
| `value_drivers` | `list[str]` | Named drivers, e.g. `["improved subrogation recovery rate", "reduced training overhead"]`. |

### 4.2 NEW `ValueMeasurementPlan` (top-level on `IntakeReport`)

```python
class ValueMeasurementPlan(StrictBase):
    baseline_metric_name: str | None
    baseline_metric_definition: str | None   # formula or SQL-derivable spec
    baseline_measurement_window: str | None  # e.g. "trailing 12 months"

    counterfactual_design: Literal[
        "champion_challenger",
        "ab_test",
        "geographic_split",
        "historical_baseline_with_detrending",
        "synthetic_control",
        "regression_discontinuity",
        "none_declared",
    ] | None
    counterfactual_rationale: str | None
    attribution_method_narrative: str | None

    evaluation_horizon_months: int | None    # 3, 6, 12, ...
    logging_requirements: list[str]          # e.g. ["model_input_features", "model_score", "decision_taken", "outcome_at_30_days"]
    review_cadence: Literal[
        "weekly", "monthly", "quarterly", "ad_hoc"
    ] | None
    success_criteria: list[str]              # e.g. ["recovery rate +5pp at 6mo", "no fairness SLA breach"]
    decision_rights: str | None              # advisory prose
```

### 4.3 NEW `DataReport.baseline_snapshot`

```python
class BaselineSnapshot(StrictBase):
    metric_name: str                         # mirror from ValueMeasurementPlan
    value: float | None
    measurement_unit: str                    # "percent", "USD", "count", ...
    measurement_window_start: datetime | None
    measurement_window_end: datetime | None
    query_sql: str                           # the SQL the agent generated
    query_execution_status: Literal["EXECUTED", "NOT_EXECUTED", "FAILED"]
    caveats: list[str]
```

`DataReport.baseline_snapshot: BaselineSnapshot | None` — optional because intake may have produced `value_measurement_plan=None` for a `DRAFT_INCOMPLETE` report; data agent skips baseline collection in that case.

---

## 5. The six implementation phases

Each phase has: **deliverable**, **files affected**, **completion criteria** (greppable), **verification commands**, **session boundary**. Per Learning #32, completion criteria avoid file-wide greps against append-only files (CHANGELOG.md, SESSION_NOTES.md, wiki Changelog.md).

### Phase 1 — Schema extensions

**Deliverable:** Extended `EstimatedValue` + new `ValueMeasurementPlan` + new `BaselineSnapshot`. Tests + schema-doc mirrors updated. **No** intake/data/website code touched.

**Files affected (with anchors):**

| File | Change | Anchor |
|------|--------|--------|
| `src/model_project_constructor/schemas/v1/intake.py` | Extend `EstimatedValue` (7 new fields); add `ValueMeasurementPlan` class; add `IntakeReport.value_measurement_plan: ValueMeasurementPlan` | Lines 27-32 (extend), insert before line 54 |
| `tests/schemas/fixtures.py` | Extend `make_estimated_value()` defaults; add `make_value_measurement_plan()` factory | Lines 44-49 + new factory |
| `tests/schemas/test_intake.py` | New tests for extension fields + new class + IntakeReport.value_measurement_plan presence | After line 132 |
| `packages/data-agent/src/model_project_constructor_data_agent/schemas.py` | Add `BaselineSnapshot` class; add `DataReport.baseline_snapshot: BaselineSnapshot \| None` | Insert before line 95; extend line 95-104 |
| `tests/data_agent_package/test_inventory_schemas.py` | New tests for `BaselineSnapshot` | Append |
| `docs/architecture-history/architecture-plan.md` | Update §5.1 (EstimatedValue), add §5.5 (ValueMeasurementPlan), add note in §6 (DataReport.baseline_snapshot) | Lines 248-272 region |
| `docs/wiki/claims-model-starter/Schema-Reference.md` | Mirror `EstimatedValue` extensions + new `ValueMeasurementPlan` + `BaselineSnapshot` documentation | Lines 131-140 region |

**Completion criteria (Phase-1 only; greppable):**

```bash
# New EstimatedValue fields
grep -c "cost_of_inaction_narrative" src/model_project_constructor/schemas/v1/intake.py    # expect 1
grep -c "payback_months" src/model_project_constructor/schemas/v1/intake.py                # expect 1
grep -c "value_drivers" src/model_project_constructor/schemas/v1/intake.py                 # expect 1

# New classes
grep -c "^class ValueMeasurementPlan" src/model_project_constructor/schemas/v1/intake.py   # expect 1
grep -c "^class BaselineSnapshot" packages/data-agent/src/model_project_constructor_data_agent/schemas.py  # expect 1

# IntakeReport gained the field
grep -c "value_measurement_plan: ValueMeasurementPlan" src/model_project_constructor/schemas/v1/intake.py  # expect 1

# DataReport gained the field
grep -c "baseline_snapshot:" packages/data-agent/src/model_project_constructor_data_agent/schemas.py       # expect 1

# Tests green
.venv/bin/pytest tests/schemas/ tests/data_agent_package/test_inventory_schemas.py -q

# Type-check clean
.venv/bin/mypy src/model_project_constructor/schemas/ packages/data-agent/src/
```

**Documentation surfaces touched this phase:** `docs/architecture-history/architecture-plan.md`, `docs/wiki/claims-model-starter/Schema-Reference.md`.

**Session boundary:** This phase is one session. Close out when criteria pass. **Do not** continue into Phase 2.

---

### Phase 2 — Intake interview extensions

**Deliverable:** Intake interview drives toward the extended `EstimatedValue` fields AND the new `ValueMeasurementPlan`. All 7 fixtures extended. Wiki design doc updated to reflect "five required sections" (was four).

**Files affected:**

| File | Change | Anchor |
|------|--------|--------|
| `src/model_project_constructor/agents/intake/protocol.py` | Add `value_measurement_plan: dict[str, Any]` to `DraftReportResult` | Lines 42-55 region |
| `src/model_project_constructor/agents/intake/anthropic_client.py` | Extend system-prompt JSON schema for new EstimatedValue fields + new value_measurement_plan; extend draft_report + revise_report | Lines 158-198 (schema instructions) |
| `src/model_project_constructor/agents/intake/nodes.py` | Plumb `value_measurement_plan` through draft, revise, finalize. Extend `finalize` status-decision (Learning #21): require `value_measurement_plan` for `COMPLETE`. | Lines 142, 186-238 |
| `src/model_project_constructor/agents/intake/fixture.py` | Update fixture loader to read new fields | Line 28 docstring + 150 plumbing |
| `tests/agents/intake/test_anthropic_client.py` | Extend mock LLM responses + assertions | Line 81 region |
| `tests/agents/intake/test_nodes.py` | Extend the test fixtures + finalize-status tests | Line 63 region |
| `tests/agents/intake/test_graph.py` | Update end-to-end assertions | Line 37 region |
| `tests/fixtures/subrogation.yaml`, `subrogation_b2.yaml`, `fraud_triage.yaml`, `pricing_optimization.yaml`, `intake_question_cap.yaml`, `intake_revision_cap.yaml`, `_b2_failmode.yaml` | Add 7 EstimatedValue fields + value_measurement_plan block to each | 7 files |
| `docs/wiki/claims-model-starter/Intake-Interview-Design.md` | Section 4: "four required sections" → "five required sections"; add subsection 4.5 documenting `value_measurement_plan`; update Section 7 (terminal status rules) for the COMPLETE requirement | Lines 100-124, 160-174 |
| `docs/tutorial.md` | Walk new fields in the worked example | Line 141 region |

**Completion criteria:**

```bash
# Protocol + prompt
grep -c "value_measurement_plan" src/model_project_constructor/agents/intake/protocol.py        # expect 1
grep -c "value_measurement_plan" src/model_project_constructor/agents/intake/anthropic_client.py # expect ≥2 (schema instruction + parsing)
grep -c "value_measurement_plan" src/model_project_constructor/agents/intake/nodes.py            # expect ≥3 (draft/revise/finalize plumbing)

# All 7 fixtures extended
for f in tests/fixtures/{subrogation,subrogation_b2,fraud_triage,pricing_optimization,intake_question_cap,intake_revision_cap,_b2_failmode}.yaml; do
  grep -lq "value_measurement_plan" "$f" || echo "MISSING: $f"
done

# Wiki doc updated
grep -c "five required sections\|Five required sections" docs/wiki/claims-model-starter/Intake-Interview-Design.md  # expect ≥1
grep -c "value_measurement_plan" docs/wiki/claims-model-starter/Intake-Interview-Design.md                          # expect ≥1

# Tests green
.venv/bin/pytest tests/agents/intake/ tests/schemas/ -q
.venv/bin/mypy src/model_project_constructor/agents/intake/
```

**Documentation surfaces touched this phase:** `docs/wiki/claims-model-starter/Intake-Interview-Design.md`, `docs/tutorial.md`.

**Session boundary:** One session. Close out.

---

### Phase 3 — Data agent baseline collection

**Deliverable:** When intake provides a `value_measurement_plan` with `baseline_metric_definition`, the data agent generates a baseline-collection SQL query, executes it, and returns the result in `DataReport.baseline_snapshot`. When intake provides no plan, the data agent skips baseline collection (`baseline_snapshot=None`).

**Files affected:**

| File | Change | Anchor |
|------|--------|--------|
| `packages/data-agent/src/model_project_constructor_data_agent/llm.py` | Add a new `BaselineQuerySpec` shape + `generate_baseline_query()` method on `LLMClient` Protocol | After existing protocol methods |
| `packages/data-agent/src/model_project_constructor_data_agent/anthropic_client.py` | Implement `generate_baseline_query()` using the existing JSON-driven prompt pattern | Append |
| `packages/data-agent/src/model_project_constructor_data_agent/graph.py` | Insert `baseline_collection` node after `generate_qc` and before `summarize` | START → generate_queries → generate_qc → execute_qc → **baseline_collection** → summarize → datasheet → END |
| `packages/data-agent/src/model_project_constructor_data_agent/nodes.py` | Add `baseline_collection_node()` — reads intake's plan, generates query, executes via `ReadOnlyDB`, populates `state.baseline_snapshot` | New function |
| `packages/data-agent/src/model_project_constructor_data_agent/state.py` | Add `baseline_snapshot: BaselineSnapshot \| None` to `DataAgentState` | Append to state dataclass |
| `packages/data-agent/src/model_project_constructor_data_agent/agent.py` | Pipe `state.baseline_snapshot` into the returned `DataReport` | Line 143 region |
| `src/model_project_constructor/orchestrator/adapters.py` | Pass `value_measurement_plan` through the intake-to-DataRequest adapter | Lines 63-77 region |
| `tests/data_agent_package/test_data_agent.py` (or new file) | Tests: baseline collection executes when plan provided; skipped when None | New tests |
| `docs/wiki/claims-model-starter/Data-Guide.md` | Document the new baseline collection step + `DataReport.baseline_snapshot` | (Section selection per page structure) |
| `docs/architecture-history/architecture-plan.md` §6 (Data Agent) | Add subsection on baseline collection | After existing §6 content |

**Completion criteria:**

```bash
# Code surfaces
grep -c "baseline_collection\|baseline_snapshot" packages/data-agent/src/model_project_constructor_data_agent/graph.py   # expect ≥1
grep -c "baseline_snapshot" packages/data-agent/src/model_project_constructor_data_agent/agent.py                        # expect ≥1
grep -c "BaselineQuerySpec\|generate_baseline_query" packages/data-agent/src/model_project_constructor_data_agent/llm.py  # expect ≥1

# Adapter passes plan through
grep -c "value_measurement_plan" src/model_project_constructor/orchestrator/adapters.py                                   # expect ≥1

# Tests green
.venv/bin/pytest tests/data_agent_package/ tests/orchestrator/ -q
.venv/bin/mypy packages/data-agent/src/ src/model_project_constructor/orchestrator/

# Skip-when-no-plan path tested
grep -c "test_baseline.*skip\|test.*baseline_snapshot.*None\|baseline.*None" tests/data_agent_package/ -r  # expect ≥1
```

**Documentation surfaces touched this phase:** `docs/wiki/claims-model-starter/Data-Guide.md`, `docs/architecture-history/architecture-plan.md` §6.

**Session boundary:** One session. Close out.

---

### Phase 4 — Website pre-construction value-presentation templates

**Deliverable:** Generated `01_business_understanding.qmd` and `reports/intake_report.md` present a coherent **business case** (Problem → Solution → Annual Impact Band → Cost of Inaction → Implementation Cost → Payback → Value Drivers → Assumptions → Decision Rights). Same data flows to both surfaces from a single rendering helper.

**Files affected:**

| File | Change | Anchor |
|------|--------|--------|
| `src/model_project_constructor/agents/website/templates.py` | Extend `render_qmd_business_understanding` (lines 303-317): add sections for cost of inaction, implementation cost, payback, value drivers. Extend `render_reports_intake_md` (lines 500-529) to mirror. Optionally extract a shared `_render_business_case_block(intake)` helper. | Lines 303-317, 500-529 |
| `src/model_project_constructor/agents/website/governance_templates.py` | Update `render_impact_assessment` (lines 329-355) to surface cost of inaction + implementation cost as part of the "## Value Narrative" section | Lines 329-355 |
| `tests/agents/website/test_templates.py` | Tests for new sections + missing-field handling | After line 113 |
| `docs/wiki/claims-model-starter/Generated-Project-Structure.md` | Update generated-files inventory + section list for `01_business_understanding.qmd` | (per page structure) |
| `docs/wiki/claims-model-starter/Worked-Examples.md` | Update Example 1 (subrogation) — show extended estimated_value block at intake AND rendered business_understanding output | Lines 32, 120-188 region |

**Completion criteria:**

```bash
# Generated MD sections present
grep -c "## Cost of Inaction\|## Implementation Cost\|## Payback\|## Value Drivers\|## Decision Rights" src/model_project_constructor/agents/website/templates.py  # expect ≥3 (5 new sections; lenient lower bound)

# Both surfaces share rendering
grep -c "_render_business_case_block\|cost_of_inaction" src/model_project_constructor/agents/website/templates.py  # expect ≥2 (helper + at least one call site, or two inline references)

# Tests green
.venv/bin/pytest tests/agents/website/ -q
.venv/bin/mypy src/model_project_constructor/agents/website/

# Worked-Examples mirrors
grep -c "cost_of_inaction\|value_drivers\|payback_months" docs/wiki/claims-model-starter/Worked-Examples.md  # expect ≥1
```

**Documentation surfaces touched this phase:** `docs/wiki/claims-model-starter/Generated-Project-Structure.md`, `docs/wiki/claims-model-starter/Worked-Examples.md`, **the generated website's `01_business_understanding.qmd` + `reports/intake_report.md` themselves** (these ARE pipeline-produced documentation).

**Session boundary:** One session. Close out.

---

### Phase 5 — Website post-production value-demonstration templates

**Deliverable:** Replace the TODO at `templates.py:406-408` with a structured **Production Measurement Plan** section. `render_qmd_implementation_plan` now emits: Estimated Annual Impact, Confidence, Assumptions, **Baseline (current state from `DataReport.baseline_snapshot`)**, **Counterfactual Design**, **Attribution Method**, **Evaluation Horizon**, **Logging Requirements**, **Review Cadence**, **Success Criteria**, **Decision Rights**. `render_ongoing_monitoring` extended to thread the baseline-metric.

**Files affected:**

| File | Change | Anchor |
|------|--------|--------|
| `src/model_project_constructor/agents/website/templates.py` | Rewrite `render_qmd_implementation_plan` (lines 386-409). Accept `data: dict` in addition to `intake: dict` so baseline_snapshot can be surfaced. Update `build_base_files` (line 604) call signature. | Lines 386-409, 604 |
| `src/model_project_constructor/agents/website/governance_templates.py` | Extend `render_ongoing_monitoring` (lines 278-301) — pull baseline metric from intake's `value_measurement_plan` and surface as a tracked metric alongside the existing performance-metric list | Lines 278-301 |
| `src/model_project_constructor/agents/website/governance_templates.py` | Update `render_deployment_gates` (lines 304-326): add a gate item for "Production Measurement Plan reviewed by Data Science team" | Lines 304-326 |
| `tests/agents/website/test_templates.py` | Update `test_qmd_implementation_plan_*` — assert new sections. Add tests for missing baseline_snapshot (graceful degradation). | Lines 132-141 |
| `docs/wiki/claims-model-starter/Monitoring-and-Operations.md` | Add new top-level section "## Value Demonstration" — describes the post-production cadence + the baseline → attribution → success-criteria thread | Append before "## Troubleshooting" (line 106) |
| `docs/wiki/claims-model-starter/Governance-Framework.md` | Update "## Monitoring cadence" (line 68) to describe how the cycle-time cadence interacts with the value-review cadence | Lines 68-79 |

**Completion criteria:**

```bash
# TODO is gone, structured plan is in
grep -c "intentionally sparse" src/model_project_constructor/agents/website/templates.py                # expect 0 (TODO removed)
grep -c "## Production Measurement Plan\|## Baseline\|## Counterfactual\|## Attribution\|## Evaluation Horizon\|## Logging Requirements\|## Success Criteria" src/model_project_constructor/agents/website/templates.py  # expect ≥4

# data: dict threaded through
grep -c "data=data" src/model_project_constructor/agents/website/templates.py | head -1                  # expect ≥1 (build_base_files call)
grep -c "render_qmd_implementation_plan(" src/model_project_constructor/agents/website/templates.py      # expect ≥1; signature updated

# Wiki sections present
grep -c "^## Value Demonstration" docs/wiki/claims-model-starter/Monitoring-and-Operations.md            # expect 1

# Tests green
.venv/bin/pytest tests/agents/website/ -q
.venv/bin/mypy src/model_project_constructor/agents/website/
```

**Documentation surfaces touched this phase:** `docs/wiki/claims-model-starter/Monitoring-and-Operations.md`, `docs/wiki/claims-model-starter/Governance-Framework.md`, **the generated website's `06_implementation_plan.qmd` + `governance/ongoing_monitoring.md` + `governance/deployment_gates.md`**.

**Session boundary:** One session. Close out.

---

### Phase 6 — Cross-doc consistency + worked examples + glossary

**Deliverable:** Documentation surfaces NOT touched by Phases 1-5 are updated for end-to-end consistency. The Worked-Examples wiki page walks the new schema → intake → data-baseline → website-pre → website-post thread for the subrogation example. Pipeline-Overview reflects the extended capture.

**Files affected (docs only — no code):**

| File | Change | Anchor |
|------|--------|--------|
| `docs/architecture-history/architecture-plan.md` | Update §1 Pipeline overview (line 135 — note value-capture extension); §8 Monitoring (lines 555-562) — thread value cadence with cycle-time cadence | Lines 135, 555-562 |
| `docs/wiki/claims-model-starter/Worked-Examples.md` | Extend Example 1 (subrogation, lines 9-188) with: extended intake fixture excerpt, baseline_snapshot DataReport excerpt, new website `06_implementation_plan.qmd` excerpt | Lines 9-188 |
| `docs/wiki/claims-model-starter/Pipeline-Overview.md` | Update Step 1, 3, 5 descriptions to reflect value-capture extensions | (per page structure) |
| `docs/wiki/claims-model-starter/Glossary.md` | Add entries: "Baseline Snapshot," "Counterfactual Design," "Value Measurement Plan," "Cost of Inaction" | Append |
| `docs/wiki/claims-model-starter/Home.md` | Update the value-proposition framing if it references the four-section model | (per page structure) |
| `docs/wiki/claims-model-starter/Changelog.md` | Add an entry under the current `## Unreleased` (or equivalent) section describing the documentation extension | **Target the current `## Unreleased` section ONLY** (per Learning #32 — do not modify historical phase entries) |

**Completion criteria:**

```bash
# Worked example mirrors new schema
grep -c "baseline_snapshot\|value_measurement_plan\|counterfactual_design" docs/wiki/claims-model-starter/Worked-Examples.md  # expect ≥1

# Glossary additions
grep -c "Baseline Snapshot\|Value Measurement Plan\|Counterfactual Design\|Cost of Inaction" docs/wiki/claims-model-starter/Glossary.md  # expect ≥3 (lenient — one of the four may already exist)

# Architecture-plan §8 monitoring extended
grep -c "value cadence\|Value Demonstration\|baseline_snapshot" docs/architecture-history/architecture-plan.md  # expect ≥1

# Pipeline-Overview reflects extended capture
grep -c "value_measurement_plan\|baseline\|business case" docs/wiki/claims-model-starter/Pipeline-Overview.md  # expect ≥1

# Tests still green (sanity — no code changes expected)
.venv/bin/pytest -q
```

**Documentation surfaces touched this phase:** `docs/architecture-history/architecture-plan.md`, `docs/wiki/claims-model-starter/Worked-Examples.md`, `docs/wiki/claims-model-starter/Pipeline-Overview.md`, `docs/wiki/claims-model-starter/Glossary.md`, `docs/wiki/claims-model-starter/Home.md`, `docs/wiki/claims-model-starter/Changelog.md`.

**Session boundary:** One session. Close out the plan.

---

## 6. Phase ordering rationale

| Phase | Why it goes here |
|-------|------------------|
| **1: Schema** | Foundational — every subsequent phase depends on the schema shape. Tests + doc mirrors land first so downstream code is type-checked against a stable contract. |
| **2: Intake** | Drives the data into the schema. Must precede Phase 3 because the data agent reads the intake-defined plan. Fixtures-extended-here gives Phases 3-5 a stable test surface. |
| **3: Data agent** | Consumes intake's plan; produces baseline. Must precede Phase 5 because the website's post-production template displays the baseline. |
| **4: Website pre-construction** | Independent of Phase 3 (uses only `intake` dict). Could in principle run before Phase 3; placed after because both Phase 4 + Phase 5 belong together conceptually and Phase 5 needs Phase 3. |
| **5: Website post-production** | Depends on Phase 3 (`DataReport.baseline_snapshot`). The load-bearing phase — replaces the templates.py:406-408 TODO. |
| **6: Cross-doc sync** | Final consistency pass. No code; purely documentation. Phases 1-5 each touched their owned docs; Phase 6 handles the cross-cutting surfaces. |

---

## 7. Risk register

| Risk | Mitigation |
|------|-----------|
| **Phase 2 prompt extension causes intake interview to balloon past MAX_QUESTIONS=20.** | Phase 2's prompt should add new questions only after the existing four-section coverage is solid (LLM judgment). Add a fixture (`intake_value_plan_cap.yaml`) that exercises the cap with extended-section questions. |
| **Phase 3 baseline SQL fails silently in production-like DBs.** | `BaselineSnapshot.query_execution_status` is mandatory; `FAILED` is a valid terminal state. Caveats list captures partial-execution context. Data agent's overall status remains `COMPLETE` even when baseline collection fails. |
| **Phase 5 template signature change (`data: dict` added to `render_qmd_implementation_plan`) breaks downstream callers.** | Grep `render_qmd_implementation_plan(` before editing — currently called from `build_base_files` only (templates.py:604). Update that call site in the same diff. Test surface (`test_qmd_implementation_plan_*`) catches signature mismatches. |
| **Fixture migration in Phase 2 misses one of 7 YAMLs.** | The Phase 2 completion-criteria for-loop fails fast if any fixture is missing `value_measurement_plan:`. Phase 2 does not close out until all 7 are extended. |
| **Wiki Changelog drift** (Learning #32). | Phase 6 explicitly targets the current `## Unreleased` section only; historical phase entries are not touched. Completion criteria do not file-wide-grep Changelog.md. |
| **Phase 3 LLM cost regression** (added `generate_baseline_query` call adds an LLM round-trip per data-agent run). | The added call is a single short JSON prompt — comparable cost to existing `generate_quality_checks`. The orchestrator's existing fake-LLM mode + the data agent's fake-client mode both stub this out for CI runs. |

---

## 8. Out of scope (future work, NOT this plan)

- **Real production telemetry SDK integration.** A generated repo could ship with an opinionated logging client (e.g. a stub `value_logger.py` module that wraps OpenTelemetry). This plan emits TODO scaffolding; a future session could implement.
- **A/B-test orchestration.** The plan captures *intent* (counterfactual design); a future session could integrate with an experiment platform (Eppo, Statsig, growthbook).
- **Backfill of value capture into already-shipped projects.** No retroactive update to projects generated before Phase 5 lands. A migration script is a future option, not this plan's scope.
- **`docs/methodology/` updates.** The methodology framework documents (HOW_TO_USE.md, ITERATIVE_METHODOLOGY.md, workstream docs) are session-protocol docs, not project-product docs. They are unaffected by this plan.
- **Standalone "value-measurement service" extraction.** Per §3.1 (schema partition keeps things in `intake.py`). A future extraction into `packages/value-measurement/` is conceivable but not on the path.

---

## Appendix A — Full grep inventory

Per Learnings #1, #19 — counts captured 2026-05-21 during Session 85 planning. Each row is one grep; the executor in Phase N should re-run the grep in their Phase 0 to catch drift since planning.

### A.1 Schema TYPE surfaces (class definitions)

```bash
grep -rn "class EstimatedValue" src/ packages/ docs/                         # 3 hits: intake.py:27 (canonical), architecture-plan.md:248, Schema-Reference.md:131
grep -rn "EstimatedValue\b" src/ packages/ tests/                            # checks for type-annotation surfaces (Pydantic class references)
```

### A.2 Schema FIELD surfaces (snake_case `estimated_value`)

```bash
grep -rn "estimated_value" src/                                              # 24 hits
grep -rn "estimated_value" tests/                                            # 28 hits (test fixtures + factory)
grep -rn "estimated_value" docs/                                             # 15 hits (doc mirrors + tutorial + wiki)
```

Per Learning #8 — TYPE (A.1), FIELD (A.2), STATE KEY (A.3), DOCSTRING (A.4) are separate greps.

### A.3 STATE KEY surfaces (Python dict-literal `"estimated_value"`)

```bash
grep -rn '"estimated_value"' src/                                            # included in A.2; ~12 of those 24 hits are dict-literal form
grep -rn "intake.get.\"estimated_value\"" src/                               # 5 hits in website/templates.py + governance_templates.py + ui/intake/templates.py
```

### A.4 DOCSTRING / human-prose surfaces ("Estimated Value")

```bash
grep -rn "Estimated Value\|ESTIMATED VALUE" src/ docs/                       # 5 hits: templates.py:314, 522 (section headers); architecture-plan.md:135; initial_purpose.txt:44, 74
```

### A.5 Intake interview prompt surfaces

```bash
grep -n "estimated_value\|EstimatedValue\|four required\|drive toward" src/model_project_constructor/agents/intake/anthropic_client.py
# expect 4 hits: lines 158, 198, 243, 254 (per Session 85 reconnaissance)
```

### A.6 Website template surfaces

```bash
grep -n "render_qmd_business_understanding\|render_qmd_implementation_plan\|render_reports_intake_md" src/model_project_constructor/agents/website/templates.py
# expect 3 definitions: 303, 386, 500; plus 1 call site each in build_base_files (lines 597, 604, 615)

grep -n "render_ongoing_monitoring\|render_impact_assessment\|render_deployment_gates" src/model_project_constructor/agents/website/governance_templates.py
# expect 3 definitions: 278, 329, 304; plus call sites in build_governance_files (lines 749 region)
```

### A.7 Fixture surfaces

```bash
ls tests/fixtures/*.yaml
# 7 files (per §1.4); each has an `estimated_value:` block per inventory.
```

### A.8 Wiki documentation surfaces

```bash
grep -l "Estimated Value\|estimated_value\|measuring value\|measurement\|baseline" docs/wiki/claims-model-starter/*.md
# 8 pages (per §1.4): Schema-Reference, Intake-Interview-Design, Worked-Examples, Pipeline-Overview, Monitoring-and-Operations, Governance-Framework, Generated-Project-Structure, Data-Guide
```

### A.9 Architecture-plan surfaces

```bash
grep -n "estimated_value\|EstimatedValue\|Estimated Value" docs/architecture-history/architecture-plan.md
# 4 hits: lines 135, 248, 272, 460
```

### A.10 Data agent surfaces

```bash
grep -n "class DataReport\|DataReport\b" packages/data-agent/src/model_project_constructor_data_agent/schemas.py
# 1 definition: line 95; 1 export: line 185
```

---

## Appendix B — Open contract questions for implementation sessions

These choices are bounded but unresolved. Each implementation phase should resolve its own open questions at Phase 1A (per Learning #40 — pre-named at handoff, resolved at Phase 1A, not mid-execution).

**For Phase 1 (Session 86):**

1. **`payback_months: int | None` — integer or `Literal["<3", "3-6", "6-12", "12-24", ">24"]` enum?** Integer is more flexible; enum is more honest about precision.
2. **`value_drivers: list[str]` — free-form or controlled vocabulary?** Free-form is implementable now; controlled vocabulary is a future hardening.
3. **Place `BaselineSnapshot` in `schemas.py` or as a sibling module?** Schemas.py keeps everything in one place; sibling module follows `governance_templates.py` precedent (Learning #2).

**For Phase 2 (Session 87):**

1. **Does the intake LLM ask about the measurement plan in a separate sub-prompt (analogous to governance classification, `nodes.py:88-92`) or inline within `draft_report`?** Sub-prompt mirrors governance; inline keeps the prompt cost lower.
2. **Question budget allocation: at most how many of the 20-question cap may target value-measurement-plan questions?** Recommend ~3-4; the existing budget already covers four sections + governance.

**For Phase 3 (Session 88):**

1. **Should `baseline_collection_node` fail-the-graph or fail-the-snapshot when the baseline SQL errors?** Recommend fail-the-snapshot (`query_execution_status="FAILED"`) — the report still ships, the snapshot has a `FAILED` status, downstream renderers display the caveat.
2. **Should the baseline collection happen in parallel with primary-query execution or strictly after?** Strictly after (simpler, no concurrency to test) unless a future profiling pass shows it matters.

**For Phase 5 (Session 90):**

1. **Should the generated `06_implementation_plan.qmd` interpolate `baseline_snapshot.value` directly, or render "see `reports/data_report.json` for baseline"?** Interpolating reads better for stakeholders; the indirection is more honest about provenance. Lean toward direct interpolation with a citation footnote.

---

## 9. Definition of done (whole plan)

This plan is "done" when all six phases have closed out. At that point:

- Every intake interview captures a `ValueMeasurementPlan` (or explicitly omits one for `DRAFT_INCOMPLETE`).
- Every `DataReport` for a `COMPLETE` intake contains a `BaselineSnapshot` (executed or `FAILED`).
- Every generated website's `01_business_understanding.qmd` presents a complete business case (problem → solution → impact band → cost of inaction → implementation cost → payback → drivers → assumptions → decision rights).
- Every generated website's `06_implementation_plan.qmd` includes a structured Production Measurement Plan with baseline, counterfactual, attribution, evaluation horizon, logging requirements, cadence, success criteria, decision rights — NOT a TODO.
- The wiki, the architecture-plan, and the tutorial all describe the extended capture end-to-end.

**Verification command for "whole plan done":**

```bash
# (After Phase 6 closes out)
.venv/bin/pytest -q
.venv/bin/mypy src/model_project_constructor/ packages/data-agent/src/
grep -c "intentionally sparse" src/model_project_constructor/agents/website/templates.py  # expect 0
grep -c "value_measurement_plan" src/model_project_constructor/schemas/v1/intake.py       # expect ≥1
grep -c "baseline_snapshot" packages/data-agent/src/model_project_constructor_data_agent/schemas.py  # expect ≥1
grep -c "Value Demonstration" docs/wiki/claims-model-starter/Monitoring-and-Operations.md # expect 1
```

When all of the above hold simultaneously, the plan is complete.
