# Generated Project Structure

The website agent scaffolds a complete repository project. The exact file set depends on the model's risk tier, cycle time, and governance flags captured during intake.

## Directory layout

```
<project_name>/
├── .gitignore
├── .gitlab-ci.yml              # or .github/workflows/ci.yml
├── .pre-commit-config.yaml
├── README.md
├── pyproject.toml              # uv-managed, Python 3.11+
│
├── src/<project_slug>/
│   ├── __init__.py
│   ├── data_loading.py         # Load Data Agent SQL results
│   ├── features.py             # Feature engineering stubs
│   ├── models.py               # Model training/inference stubs
│   ├── evaluation.py           # Evaluation metrics stubs
│   └── fairness/               # (if uses_protected_attributes)
│       ├── __init__.py
│       └── audit.py
│
├── analysis/                   # Quarto documents
│   ├── 01_business_understanding.qmd
│   ├── 02_data.qmd
│   ├── 03_eda.qmd
│   ├── 04_feature_engineering.qmd
│   ├── 05_initial_models.qmd
│   ├── 06_implementation_plan.qmd
│   ├── 99_extensions.qmd
│   └── fairness_audit.qmd      # (if uses_protected_attributes)
│
├── queries/
│   ├── primary/                # One .sql per primary query
│   │   └── <query_name>.sql
│   └── quality/                # Quality checks per query
│       └── <query_name>/
│           └── <check_name>.sql
│
├── tests/
│   ├── __init__.py
│   ├── test_data_loading.py
│   ├── test_features.py
│   ├── test_models.py
│   ├── test_evaluation.py
│   └── test_fairness.py        # (if uses_protected_attributes)
│
├── governance/                 # Proportional to risk tier
│   ├── model_registry.json     # Always
│   ├── model_card.md           # Always
│   ├── change_log.md           # Always
│   ├── three_pillar_validation.md    # Tier 3+
│   ├── ongoing_monitoring.md         # Tier 3+
│   ├── deployment_gates.md           # Tier 3+
│   ├── impact_assessment.md          # Tier 2+
│   ├── regulatory_mapping.md         # Tier 2+
│   ├── lcp_integration.md            # Tier 1 only
│   ├── eu_ai_act_compliance.md       # (if affects_consumers)
│   └── audit_log/                    # Tier 1 only
│       └── README.md
│
├── data/
│   ├── README.md               # Data dictionary
│   └── datasheet_<query>.md    # Gebru 2021 datasheet per query
│
└── reports/
    ├── intake_report.json      # Machine-readable
    ├── intake_report.md        # Human-readable
    ├── data_report.json
    └── data_report.md
```

## File counts by project type

| Component | Tier 4 (Low) | Tier 3 (Moderate) | Tier 2 (High) | Tier 1 (Critical) |
|-----------|-------------|-------------------|----------------|-------------------|
| Root config | 3 | 3 | 3 | 3 |
| src/ modules | 4 | 4 | 4 | 4 |
| Quarto narratives | 7 | 7 | 7 | 7 |
| Tests | 4 | 4 | 4 | 4 |
| Data/reports | 4 | 4 | 4 | 4 |
| Governance (always) | 5 | 5 | 5 | 5 |
| Governance (tier-gated) | 0 | +3 | +5 | +7 |
| Datasheets | 1/query | 1/query | 1/query | 1/query |
| Query files | varies | varies | varies | varies |
| **Typical total** | ~28 | ~31 | ~33 | ~37 |

Add +3 files if `uses_protected_attributes=true` (fairness audit, fairness module, fairness test).
Add +1 file if `affects_consumers=true` (EU AI Act compliance).

## What each section contains

### Root configuration

- **README.md** -- Generated from the IntakeReport: business problem, proposed solution, model overview, repo layout, getting-started instructions.
- **pyproject.toml** -- Dependencies: `pandas>=2`, `scikit-learn>=1.4`, `sqlalchemy>=2`. Dev deps: `pytest>=8`, `pytest-cov>=5`, `ruff>=0.5`. Build system: hatchling.
- **.gitignore** -- Python, Quarto, and data artifacts (`.venv/`, `_site/`, `*.parquet`, `*.csv`).

### Source modules (`src/`)

Each module contains function stubs that raise `NotImplementedError`. The data science team implements them:

| Module | Purpose | Key function |
|--------|---------|-------------|
| `data_loading.py` | Execute Data Agent SQL queries | `load_primary()` |
| `features.py` | Feature engineering | `build_feature_matrix()` |
| `models.py` | Model training and inference | `train()`, `predict()` |
| `evaluation.py` | Evaluation metrics | `evaluate()` |
| `fairness/audit.py` | Subgroup fairness metrics | `subgroup_metrics()` |

### Quarto narratives (`analysis/`)

Seven `.qmd` files (Quarto markdown, YAML header with `format: html`). Each narrative is pre-seeded with content from the intake and data reports:

| Notebook | Content |
|----------|---------|
| `01_business_understanding` | Business problem, proposed solution, estimated value |
| `02_data` | Data Agent summary, primary query list, loading code |
| `03_eda` | Scaffolded EDA narrative with stub code |
| `04_feature_engineering` | References `features.py`, shows import pattern |
| `05_initial_models` | References `models.py` and `evaluation.py` |
| `06_implementation_plan` | Annual impact estimate, confidence, assumptions |
| `99_extensions` | Candidate extensions (additional features, alternative models) |

### Queries

SQL files generated by the Data Agent, organized by type:

- **`queries/primary/`** -- One `.sql` file per primary query from the DataReport
- **`queries/quality/`** -- Nested by query name, one `.sql` per quality check

### Reports

Both machine-readable (JSON) and human-readable (Markdown) versions of the intake and data reports. These are the pipeline's artifacts, preserved for traceability.

### Governance

See [Governance Framework](Governance-Framework) for full details on each artifact.

### CI pipeline

The generated CI configuration (`.gitlab-ci.yml` or `.github/workflows/ci.yml`) includes:

- **Lint** -- `ruff check`
- **Test** -- `pytest`
- **Governance** -- Schema validation of `model_registry.json`

A `.pre-commit-config.yaml` is included with ruff hooks and a local schema validation hook.

## Design properties

1. **Deterministic** -- For a given IntakeReport + DataReport, the output is byte-for-byte reproducible. No template engine; pure Python f-strings.
2. **Atomic commit** -- All files are committed in a single operation via `RepoClient.commit_files()`.
3. **Draft, not finished** -- Every generated file is a scaffold. Function stubs raise `NotImplementedError`. Narratives have placeholder analysis. The data science team fills them in.
