# Worked Examples

This page traces two end-to-end pipeline runs from a stakeholder idea to a scaffolded repository. The first example is **subrogation recovery** (tier-3 moderate, advisory model) — the scenario from `initial_purpose.txt`. The second is **personal-auto renewal profitability** (tier-1 critical, fairness-constrained) — chosen to contrast how governance scaffolding expands for higher-risk models.

Both examples are reproducible from fixtures shipped in the repository. Every quotation and file path comes from `tests/fixtures/` or the generated-project templates.

---

## Example 1 — Subrogation recovery (tier-3 moderate, advisory)

### Stakeholder idea

A Claims SVP observes that subrogation recovery dropped ~20% after a new claims-system rollout. Adjusters are no longer capturing the evidence (police reports, third-party insurer, fault evidence) needed to pursue recovery. The proposed model would score each claim for subrogation recoverability and prompt adjusters to capture the missing evidence at intake.

### Step 1 — Intake fixture

The pre-captured interview is at `tests/fixtures/subrogation.yaml`. Top-level keys:

| Key | Purpose |
|---|---|
| `schema` | `intake_fixture/v1` version tag |
| `stakeholder_id` | `stakeholder_claims_001` |
| `session_id` | `intake_subrogation_001` |
| `domain` | `pc_claims` |
| `initial_problem` | One-sentence stakeholder statement |
| `qa_pairs` | Seven Q&A pairs — interviewer questions + stakeholder answers |
| `draft_after` | `7` (draft is proposed after question 7) |
| `draft` | The `IntakeReport` draft the agent proposes |
| `governance` | Governance classification (risk tier, cycle time, regulatory frameworks, consumer/protected-attribute flags) |
| `review_sequence` | `[ACCEPT]` — stakeholder accepts the draft on first review |

### Step 2 — IntakeReport output

Running the intake agent against this fixture produces `tests/fixtures/subrogation_intake.json`. Key fields:

**Business problem** (`tests/fixtures/subrogation_intake.json:5`):

> Subrogation recovery dropped ~20% since deployment of a new claims system, primarily because adjusters no longer capture evidence required to pursue recovery (police reports, third-party insurer, fault evidence). There is no adjuster KPI tying performance to subrogation outcomes and the new UI deprioritizes the relevant intake fields.

**Proposed solution** (`:6`):

> Embed structured prompts in the claims workflow so adjusters capture the required evidence during intake, and surface a per-claim subrogation probability score so claims likely to recover are prioritized. Success is measured on subrogation recovery rate over a 12-month rolling window.

**Model solution** (`:7-25`):

- `target_variable: "successful_subrogation"`
- `target_definition: "Binary outcome: 1 if a claim resulted in a non-zero subrogation recovery within 18 months of first notice of loss, 0 otherwise."`
- `model_type: "supervised_classification"`
- `candidate_features:` information_completeness_score, adjuster_tenure_years, claim_type, time_from_incident_to_filing_days, damage_amount_usd, fault_evidence_level
- `evaluation_metrics: ["AUC", "precision_at_top_decile", "recall"]`

**Estimated value** (`:26-36`): a 10% lift on a ~$30M annual subrogation recovery yields roughly $3M/year. Low/high bracket: **$2,000,000 / $4,000,000**. Confidence: medium.

**Governance classification** (`:37-48`):

- `risk_tier: "tier_3_moderate"` — advisory recommendation only; humans decide; moderate financial exposure
- `cycle_time: "tactical"` — scores consumed at intake, workflows change weekly
- `regulatory_frameworks: ["SR_11_7", "NAIC_AIS"]`
- `affects_consumers: true` — downstream claims decisioning can affect the claimant
- `uses_protected_attributes: false`

### Step 3 — DataRequest handoff

The orchestrator converts the `IntakeReport` into a `DataRequest` and hands it to the Data Agent. The shipped sample is `tests/fixtures/sample_request.json`:

```json
{
  "target_description": "subrogation recovery amount on TX auto claims",
  "target_granularity": { "unit": "claim", "time_grain": "event" },
  "required_features": ["paid_amount", "state", "loss_date"],
  "population_filter": "TX auto claims with loss in 2024",
  "time_range": "2024-01-01 to 2024-12-31",
  "database_hint": "claims"
}
```

(The sample fixture uses a narrower TX-2024 scope than the intake; it illustrates the `DataRequest` shape rather than being the literal output of the full subrogation intake.)

#### Optional: attaching a data source inventory

A team that already has a curated catalog of relevant tables can hand the Data Agent a `DataSourceInventory` via the optional `data_source_inventory` field on `DataRequest`. The agent renders a summarized block into the query-generation prompt so the LLM prefers inventory-named tables, and each returned `PrimaryQuery` records its inventory provenance under `inventory_entries_used`.

Using the shipped `tests/fixtures/sample_curated_inventory.json` (two tables: `public.claim_events` and `public.subrogation_outcomes`):

```python
import json
from pathlib import Path
from model_project_constructor_data_agent import DataRequest, DataSourceInventory

inventory = DataSourceInventory.model_validate(
    json.loads(Path("tests/fixtures/sample_curated_inventory.json").read_text())
)
request = DataRequest(..., data_source_inventory=inventory)
```

With the inventory attached, a run against a real Claude model would produce a `PrimaryQuery.inventory_entries_used` pointing back at `public.claim_events` / `public.subrogation_outcomes`. Callers who omit the field get the pre-Phase-3 behaviour unchanged.

### Step 4 — DataReport output

The Data Agent produces `tests/fixtures/sample_datareport.json`:

- **One primary query** named `subrogation_training_set` — joins `claims`, `adjusters`, `intake_scores`, and `subrogation_recovery` over a five-year window, labeling each row with the eventual recovery outcome observed within 18 months of FNOL.
- **Two quality checks:** `row_count_sanity` (PASSED, 1,284,512 rows) and `target_nullability` (PASSED, 9.8% null rate within tolerance).
- **One datasheet** (Gebru 2021 schema) covering motivation, composition, collection process, preprocessing, intended uses, known biases, and maintenance ownership.
- **Summary:** "Built a single training set spanning 5 years of auto BI/PD claims with a binary subrogation-success label observed within 18 months of FNOL. 1.28M rows, ~10% label null rate concentrated in the most recent 18 months."
- **Flagged concern:** label-leakage risk on `information_completeness_score`, which may reflect post-intake adjuster follow-up; recommendation to freeze at t+24h.

### Step 5 — Generated repository

The Website Agent scaffolds a project named `subrogation-model` (slug `subrogation_model`). The Phase 4A baseline file set is enumerated in `tests/agents/website/test_templates.py:176-205`:

**Root and configuration**

- `.gitignore`
- `README.md`
- `pyproject.toml`

**Source module** (`src/subrogation_model/`)

- `__init__.py`
- `data_loading.py`
- `features.py`
- `models.py`
- `evaluation.py`

**Analysis narratives** (`analysis/*.qmd`)

- `01_business_understanding.qmd`
- `02_data.qmd`
- `03_eda.qmd`
- `04_feature_engineering.qmd`
- `05_initial_models.qmd`
- `06_implementation_plan.qmd`
- `99_extensions.qmd`

**Tests** (`tests/`)

- `__init__.py`, `test_data_loading.py`, `test_features.py`, `test_models.py`, `test_evaluation.py`

**Data and reports**

- `data/README.md`
- `reports/intake_report.json`, `reports/intake_report.md`
- `reports/data_report.json`, `reports/data_report.md`

**Queries** (derived from the `DataReport`)

- `queries/primary/subrogation_training_set.sql`
- `queries/quality/subrogation_training_set/row_count_sanity.sql`
- `queries/quality/subrogation_training_set/target_nullability.sql`

**Governance artifacts (Phase 4B, tier-3 moderate with `affects_consumers=true`)** — emitted by `build_governance_files` in `src/model_project_constructor/agents/website/governance_templates.py:708-785`:

Always-emitted:

- `governance/model_registry.json`
- `governance/model_card.md`
- `governance/change_log.md`
- `.gitlab-ci.yml` *or* `.github/workflows/ci.yml` (depending on `ci_platform`)
- `.pre-commit-config.yaml`
- `data/datasheet_subrogation_training_set.md` (one per primary query)

Tier-3+ (`governance_templates.py:744-754`):

- `governance/three_pillar_validation.md`
- `governance/ongoing_monitoring.md`
- `governance/deployment_gates.md`

Consumer-facing (`governance_templates.py:779-783`):

- `governance/eu_ai_act_compliance.md`

Tier-2+ and tier-1 artifacts are **not** emitted at this tier; fairness scaffolds are not emitted because `uses_protected_attributes=false`.

**Total file count:** ~38 files across source, analysis, tests, reports, queries, and governance.

---

## Example 2 — Renewal profitability (tier-1 critical, fairness-constrained)

This example is captured as `tests/fixtures/tier1_intake.json`. It shows how a higher-risk scenario expands the governance scaffolding.

### Stakeholder idea

Personal auto policy renewals are currently decided by a rules engine that over-indexes on ZIP code and prior-claim count, producing outcomes correlated with demographic attributes. A state UDAP inquiry is open. The proposed model is a profitability classifier with a fairness constraint during training, surfaced to underwriters as an advisory score.

### IntakeReport highlights

- `target_variable: "renewal_profitability_flag"`
- `target_definition`: binary — profitable if 12-month loss ratio < 0.65
- `model_type: "supervised_classification"`
- `evaluation_metrics`: AUC, calibration_slope, **subgroup_AUC_parity**
- `estimated_value`: $8M–$12M annual on a $400M book, *primarily compliance-driven*
- `governance.risk_tier: "tier_1_critical"`
- `governance.cycle_time: "continuous"` — nightly scoring + near-real-time drift/fairness monitoring
- `governance.regulatory_frameworks: ["SR_11_7", "NAIC_AIS", "EU_AI_ACT_ART_9", "ASOP_56"]`
- `governance.affects_consumers: true`
- **`governance.uses_protected_attributes: true`** — triggers fairness scaffolds

### Generated repository — additional artifacts beyond Example 1

Because this intake is **tier-1**, **consumer-facing**, and **uses protected attributes**, `build_governance_files`, `build_analysis_files`, and `build_test_files` in `governance_templates.py` add:

Tier-2+ (`governance_templates.py:756-772`):

- `governance/impact_assessment.md`
- `governance/regulatory_mapping.md` (maps each declared framework to the emitted artifact list via `build_regulatory_mapping`)

Tier-1 only (`governance_templates.py:774-777`):

- `governance/lcp_integration.md`
- `governance/audit_log/README.md`

Fairness scaffolds (`governance_templates.py:788-829`, triggered by `uses_protected_attributes=true`):

- `analysis/fairness_audit.qmd`
- `src/renewal_profitability_model/fairness/__init__.py`
- `src/renewal_profitability_model/fairness/audit.py`
- `tests/test_fairness.py`

**Net effect:** a tier-1 intake emits roughly a dozen governance files on top of the Phase 4A baseline — versus four for the tier-3 subrogation example. Risk-proportional scaffolding is the design goal documented in architecture-plan §8.

---

## Other fixtures in the repository

| Fixture | Scenario | Notes |
|---|---|---|
| `tests/fixtures/subrogation.yaml` / `subrogation_intake.json` | Subrogation recoverability (Example 1) | Tier-3 moderate, advisory |
| `tests/fixtures/tier1_intake.json` | Renewal profitability (Example 2) | Tier-1 critical, fairness-constrained |
| `tests/fixtures/tier2_intake.json` | Commercial property loss reserving | Tier-2 high, regression |
| `tests/fixtures/pricing_optimization.yaml` | Premium elasticity | Drives the rating engine directly |
| `tests/fixtures/fraud_triage.yaml` | Real-time FNOL fraud routing | Continuous cycle time |
| `tests/fixtures/intake_question_cap.yaml` | Test fixture for the `MAX_QUESTIONS` cap | Not a domain scenario |
| `tests/fixtures/intake_revision_cap.yaml` | Test fixture for the 3-revision cap | Not a domain scenario |

---

## Reproducing a worked example

Both examples can be replayed against fake adapters (no credentials, no external services):

```bash
# From the repository root
uv sync --extra agents --extra ui --extra dev

# Run the end-to-end pipeline with fixture-driven runners and FakeRepoClient
uv run python scripts/run_pipeline.py --host gitlab
```

By default `scripts/run_pipeline.py` uses the `subrogation` fixture path through the pipeline, writes checkpoints to `.orchestrator/checkpoints/<run_id>/`, and materializes the generated project via `FakeRepoClient` (a list of commits held in memory, no network I/O). To exercise the real GitLab or GitHub code path, add `--live` and set the corresponding token env var (`GITLAB_TOKEN` or `GITHUB_TOKEN`).

For a richer walkthrough including the intake YAML authoring step and the `model-intake-agent` CLI, see the repository tutorial at `docs/tutorial.md`.

---

## See also

- [Getting Started](Getting-Started) — install and first run
- [Generated Project Structure](Generated-Project-Structure) — per-file purpose in the output repository
- [Governance Framework](Governance-Framework) — risk-tier gates and the regulatory mapping table
- [Schema Reference](Schema-Reference) — full field-by-field schemas for `IntakeReport`, `DataRequest`, `DataReport`
- [Pipeline Overview](Pipeline-Overview) — the agent handoff protocol
