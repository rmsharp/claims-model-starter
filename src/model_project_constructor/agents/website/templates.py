"""File content templates for the Website Agent's base scaffolding.

Each ``render_*`` function returns a ``(path, contents)`` pair or a list of
them. ``build_base_files(intake, data, project_name, project_slug)`` composes
all of them into the dict that ``SCAFFOLD_BASE`` writes into
``WebsiteState.files_pending``.

Phase 4A scope (architecture-plan §14 Phase 4A + §8.2):

- Everything listed in §11 *except* governance artifacts
- That excludes ``governance/``, ``data/datasheet_*.md``,
  ``.gitlab-ci.yml`` and ``.pre-commit-config.yaml`` (§8.2 classifies
  those as governance artifacts — they land in Phase 4B's
  SCAFFOLD_GOVERNANCE node)

Templates are pure Python f-strings; there is no template engine. The
content is deterministic for a given input so tests can byte-equal the
output.
"""

from __future__ import annotations

import json
import re
from typing import Any

_SLUG_INVALID = re.compile(r"[^a-z0-9_]+")
_NAME_INVALID = re.compile(r"[^a-z0-9\-]+")


def derive_project_name(hint: str) -> str:
    """Turn a free-form ``project_name_hint`` into a GitLab-safe project name.

    Lowercased, hyphen-separated, no trailing/leading hyphens. Collapses
    runs of non-alphanumeric characters to a single hyphen.
    """

    lowered = hint.strip().lower()
    replaced = _NAME_INVALID.sub("-", lowered)
    collapsed = re.sub(r"-+", "-", replaced).strip("-")
    return collapsed or "model-project"


def derive_project_slug(project_name: str) -> str:
    """Turn a project name into a python-package-safe slug.

    Lowercase, underscore-separated, must start with a letter. Collisions
    with Python keywords are not handled — Phase 4A project names are
    derived from business domain strings, not from keywords.
    """

    base = project_name.replace("-", "_").lower()
    cleaned = _SLUG_INVALID.sub("_", base)
    collapsed = re.sub(r"_+", "_", cleaned).strip("_")
    if not collapsed or not collapsed[0].isalpha():
        collapsed = f"m_{collapsed}" if collapsed else "model_project"
    return collapsed


# --- individual file renderers ------------------------------------------------


def render_gitignore() -> str:
    return (
        "# Python\n"
        "__pycache__/\n"
        "*.py[cod]\n"
        "*.egg-info/\n"
        ".venv/\n"
        "venv/\n"
        "build/\n"
        "dist/\n"
        "\n"
        "# Testing / coverage\n"
        ".pytest_cache/\n"
        ".coverage\n"
        "htmlcov/\n"
        "\n"
        "# Editors\n"
        ".vscode/\n"
        ".idea/\n"
        ".DS_Store\n"
        "\n"
        "# Quarto\n"
        "_site/\n"
        "*_files/\n"
        "*.html\n"
        "\n"
        "# Data — never commit raw extracts\n"
        "data/raw/\n"
        "data/processed/\n"
        "*.csv\n"
        "*.parquet\n"
        "*.feather\n"
    )


def render_readme(*, intake: dict[str, Any], project_name: str) -> str:
    business_problem = str(intake.get("business_problem", "")).strip()
    proposed_solution = str(intake.get("proposed_solution", "")).strip()
    model_solution = intake.get("model_solution") or {}
    target_variable = model_solution.get("target_variable") or "unsupervised"
    model_type = model_solution.get("model_type") or "other"
    stakeholder_id = intake.get("stakeholder_id", "unknown")

    return (
        f"# {project_name}\n"
        "\n"
        "> **Draft model project.** This repository was scaffolded by the\n"
        "> Model Project Constructor pipeline. The Data Science team should\n"
        "> treat every section below as a starting point, not a deliverable.\n"
        "\n"
        "## Business Problem\n"
        "\n"
        f"{business_problem}\n"
        "\n"
        "## Proposed Solution\n"
        "\n"
        f"{proposed_solution}\n"
        "\n"
        "## Model at a Glance\n"
        "\n"
        f"- **Target:** `{target_variable}`\n"
        f"- **Model type:** `{model_type}`\n"
        f"- **Requesting stakeholder:** `{stakeholder_id}`\n"
        "\n"
        "## Repository Layout\n"
        "\n"
        "- `src/` — unit-testable Python modules (data loading, features,\n"
        "  models, evaluation). All analysis code lives here.\n"
        "- `analysis/` — Quarto narratives that import from `src/`.\n"
        "- `queries/` — SQL pulled directly from the Data Agent report.\n"
        "- `tests/` — scaffolded unit tests for the `src/` modules.\n"
        "- `reports/` — the intake and data reports in both JSON and Markdown.\n"
        "- `data/` — data dictionary and (in Phase 4B) datasheets.\n"
        "- `governance/` — (Phase 4B) governance artifacts proportional to\n"
        "  the model's risk tier and cycle time.\n"
        "\n"
        "## Getting Started\n"
        "\n"
        "```bash\n"
        "uv sync\n"
        "uv run pytest\n"
        "```\n"
    )


def render_pyproject(*, project_name: str, project_slug: str) -> str:
    return (
        "[project]\n"
        f'name = "{project_name}"\n'
        'version = "0.1.0"\n'
        f'description = "Draft model project scaffolded by Model Project Constructor"\n'
        'requires-python = ">=3.11"\n'
        "dependencies = [\n"
        '    "pandas>=2",\n'
        '    "scikit-learn>=1.4",\n'
        '    "sqlalchemy>=2",\n'
        "]\n"
        "\n"
        "[project.optional-dependencies]\n"
        "dev = [\n"
        '    "pytest>=8",\n'
        '    "pytest-cov>=5",\n'
        '    "ruff>=0.5",\n'
        "]\n"
        "\n"
        "[build-system]\n"
        'requires = ["hatchling"]\n'
        'build-backend = "hatchling.build"\n'
        "\n"
        "[tool.hatch.build.targets.wheel]\n"
        f'packages = ["src/{project_slug}"]\n'
        "\n"
        "[tool.pytest.ini_options]\n"
        'testpaths = ["tests"]\n'
        'pythonpath = ["src"]\n'
    )


def render_src_init(*, project_name: str, project_slug: str) -> str:
    return (
        f'"""{project_name} — model package.\n'
        "\n"
        "Scaffolded by Model Project Constructor. Keep all unit-testable\n"
        "code inside this package; the ``analysis/*.qmd`` narratives import\n"
        "from here.\n"
        '"""\n'
        "\n"
        '__all__: list[str] = []\n'
    )


def render_data_loading(*, project_slug: str, primary_query_names: list[str]) -> str:
    names_literal = "[\n" + "".join(f'    "{n}",\n' for n in primary_query_names) + "]"
    return (
        '"""Data loading functions.\n'
        "\n"
        "These are called from ``analysis/02_data.qmd`` and from the unit\n"
        "tests in ``tests/test_data_loading.py``. Each primary query listed\n"
        "in the Data Agent report has a loader stub below; fill in the\n"
        "actual SQLAlchemy connection when the Data Science team is ready.\n"
        '"""\n'
        "\n"
        "from __future__ import annotations\n"
        "\n"
        "from pathlib import Path\n"
        "\n"
        "QUERIES_DIR = Path(__file__).resolve().parents[2] / \"queries\" / \"primary\"\n"
        "\n"
        f"PRIMARY_QUERY_NAMES: list[str] = {names_literal}\n"
        "\n"
        "\n"
        "def read_sql(query_name: str) -> str:\n"
        '    """Return the SQL text for a primary query by name."""\n'
        '    path = QUERIES_DIR / f"{query_name}.sql"\n'
        "    return path.read_text()\n"
        "\n"
        "\n"
        "def load_primary(query_name: str) -> object:\n"
        '    """Load the result of a primary query into a DataFrame.\n'
        "\n"
        "    Stub — wire up your SQLAlchemy engine here.\n"
        '    """\n'
        '    raise NotImplementedError("Wire up SQLAlchemy engine before calling")\n'
    )


def render_features() -> str:
    return (
        '"""Feature engineering functions — all unit-testable.\n'
        "\n"
        "Add one function per feature. Each should take a DataFrame and\n"
        "return a DataFrame with the new feature attached. Keep them pure\n"
        "(no I/O, no global state) so the tests in ``tests/test_features.py``\n"
        "can exercise them with small synthetic inputs.\n"
        '"""\n'
        "\n"
        "from __future__ import annotations\n"
        "\n"
        "\n"
        "def build_feature_matrix(df: object) -> object:\n"
        '    """Assemble the full feature matrix from a raw DataFrame."""\n'
        '    raise NotImplementedError("Fill in feature engineering")\n'
    )


def render_models(*, intake: dict[str, Any]) -> str:
    model_solution = intake.get("model_solution") or {}
    model_type = model_solution.get("model_type") or "other"
    return (
        '"""Model training and inference.\n'
        "\n"
        f"The intake report classifies this project as a ``{model_type}``\n"
        "model. The stub below is deliberately minimal — the Data Science\n"
        "team will replace ``train`` / ``predict`` with a real implementation.\n"
        '"""\n'
        "\n"
        "from __future__ import annotations\n"
        "\n"
        "\n"
        "def train(features: object, target: object) -> object:\n"
        '    """Fit a model on the supplied feature matrix and target."""\n'
        '    raise NotImplementedError("Wire up training pipeline")\n'
        "\n"
        "\n"
        "def predict(model: object, features: object) -> object:\n"
        '    """Score a fitted model over a feature matrix."""\n'
        '    raise NotImplementedError("Wire up inference path")\n'
    )


def render_evaluation(*, intake: dict[str, Any]) -> str:
    model_solution = intake.get("model_solution") or {}
    metrics = list(model_solution.get("evaluation_metrics") or [])
    metrics_literal = "[\n" + "".join(f'    "{m}",\n' for m in metrics) + "]"
    return (
        '"""Evaluation functions — thin wrappers around sklearn metrics.\n'
        "\n"
        "The intake report requested the metrics below. Add one function\n"
        "per metric; each should accept ``y_true`` and ``y_pred`` and return\n"
        "a float.\n"
        '"""\n'
        "\n"
        "from __future__ import annotations\n"
        "\n"
        f"REQUESTED_METRICS: list[str] = {metrics_literal}\n"
        "\n"
        "\n"
        "def evaluate(y_true: object, y_pred: object) -> dict[str, float]:\n"
        '    """Return a dict of metric name → score for the requested metrics."""\n'
        '    raise NotImplementedError("Wire up metric computation")\n'
    )


# --- Quarto narratives --------------------------------------------------------


def _qmd_header(title: str) -> str:
    return f"---\ntitle: \"{title}\"\nformat: html\n---\n\n"


def render_qmd_business_understanding(*, intake: dict[str, Any]) -> str:
    estimated_value = intake.get("estimated_value") or {}
    narrative = str(estimated_value.get("narrative", "")).strip()
    return (
        _qmd_header("01 — Business Understanding")
        + "## Business Problem\n\n"
        + str(intake.get("business_problem", "")).strip()
        + "\n\n"
        + "## Proposed Solution\n\n"
        + str(intake.get("proposed_solution", "")).strip()
        + "\n\n"
        + "## Estimated Value\n\n"
        + narrative
        + "\n"
    )


def render_qmd_data(*, data: dict[str, Any]) -> str:
    summary = str(data.get("summary", "")).strip()
    primary_queries = data.get("primary_queries") or []
    lines = [
        _qmd_header("02 — Data"),
        "## Data Agent Summary\n",
        summary,
        "\n\n## Primary Queries\n",
    ]
    for q in primary_queries:
        name = q.get("name", "unknown")
        purpose = q.get("purpose", "")
        lines.append(f"\n### {name}\n\n{purpose}\n")
        lines.append(f"\nSQL: `queries/primary/{name}.sql`\n")
    lines.append(
        "\n```{python}\n"
        "# from <project_slug>.data_loading import load_primary\n"
        "# df = load_primary(\"<query_name>\")\n"
        "```\n"
    )
    return "".join(lines)


def render_qmd_eda() -> str:
    return (
        _qmd_header("03 — Exploratory Data Analysis")
        + "This notebook is a scaffold. The Data Science team should:\n\n"
        + "1. Load each primary query via ``data_loading.load_primary``.\n"
        + "2. Document row counts, missing-value rates, and value distributions.\n"
        + "3. Surface any anomalies that weren't caught by the Data Agent's\n"
        + "   quality checks.\n\n"
        + "```{python}\n"
        + "# EDA code goes here\n"
        + "```\n"
    )


def render_qmd_feature_engineering() -> str:
    return (
        _qmd_header("04 — Feature Engineering")
        + "Features are implemented in ``src/<slug>/features.py`` so they\n"
        + "can be unit-tested. This narrative demonstrates their use.\n\n"
        + "```{python}\n"
        + "# from <project_slug>.features import build_feature_matrix\n"
        + "# X = build_feature_matrix(raw_df)\n"
        + "```\n"
    )


def render_qmd_initial_models(*, intake: dict[str, Any]) -> str:
    ms = intake.get("model_solution") or {}
    metrics = ", ".join(ms.get("evaluation_metrics") or []) or "(none declared)"
    return (
        _qmd_header("05 — Initial Models")
        + f"**Model type:** `{ms.get('model_type', 'other')}`\n\n"
        + f"**Requested evaluation metrics:** {metrics}\n\n"
        + "```{python}\n"
        + "# from <project_slug>.models import train, predict\n"
        + "# from <project_slug>.evaluation import evaluate\n"
        + "# model = train(X_train, y_train)\n"
        + "# preds = predict(model, X_test)\n"
        + "# scores = evaluate(y_test, preds)\n"
        + "```\n"
    )


def render_qmd_implementation_plan(*, intake: dict[str, Any]) -> str:
    estimated_value = intake.get("estimated_value") or {}
    low = estimated_value.get("annual_impact_usd_low")
    high = estimated_value.get("annual_impact_usd_high")
    confidence = estimated_value.get("confidence", "unknown")
    impact = "not estimated"
    if low is not None and high is not None:
        impact = f"${low:,.0f} – ${high:,.0f} per year"
    assumptions = estimated_value.get("assumptions") or []
    assumptions_md = (
        "\n".join(f"- {a}" for a in assumptions) if assumptions else "- (none declared)"
    )
    return (
        _qmd_header("06 — Implementation Plan & Measuring Value")
        + f"**Estimated annual impact:** {impact}\n\n"
        + f"**Confidence:** {confidence}\n\n"
        + "## Assumptions\n\n"
        + assumptions_md
        + "\n\n"
        + "## Measurement\n\n"
        + "Define the pre/post metric and the measurement window before\n"
        + "shipping. This section is intentionally sparse — the Data\n"
        + "Science team owns the measurement plan.\n"
    )


def render_qmd_extensions() -> str:
    return (
        _qmd_header("99 — Extensions & Next Experiments")
        + "Candidate extensions for future iterations:\n\n"
        + "- Additional feature sources surfaced by EDA\n"
        + "- Alternative model families beyond the initial choice\n"
        + "- Fairness / subgroup analyses (see ``src/fairness/`` once\n"
        + "  governance scaffolding lands in Phase 4B)\n"
    )


# --- Queries and tests --------------------------------------------------------


def render_primary_query_files(*, data: dict[str, Any]) -> dict[str, str]:
    out: dict[str, str] = {}
    for q in data.get("primary_queries") or []:
        name = q.get("name", "unnamed")
        out[f"queries/primary/{name}.sql"] = str(q.get("sql", "")).rstrip() + "\n"
    return out


def render_quality_check_files(*, data: dict[str, Any]) -> dict[str, str]:
    out: dict[str, str] = {}
    for q in data.get("primary_queries") or []:
        primary_name = q.get("name", "unnamed")
        for check in q.get("quality_checks") or []:
            check_name = check.get("check_name", "unnamed_check")
            path = f"queries/quality/{primary_name}/{check_name}.sql"
            out[path] = str(check.get("check_sql", "")).rstrip() + "\n"
    return out


def render_tests_init() -> str:
    return ""


def render_test_stub(module: str) -> str:
    return (
        f'"""Unit tests for ``{module}``. Scaffolded — fill in real cases."""\n'
        "\n"
        "from __future__ import annotations\n"
        "\n"
        "import pytest\n"
        "\n"
        "\n"
        f"def test_{module}_importable() -> None:\n"
        f"    import importlib\n"
        f"    module = importlib.import_module('<project_slug>.{module}')\n"
        f"    assert module is not None\n"
        "\n"
        "\n"
        f"def test_{module}_stub_raises() -> None:\n"
        f"    # Replace with real assertions once implementations land.\n"
        f"    with pytest.raises(NotImplementedError):\n"
        f"        pass  # placeholder\n"
    )


# --- Data dictionary and reports ---------------------------------------------


def render_data_readme(*, data: dict[str, Any]) -> str:
    queries = data.get("primary_queries") or []
    lines = [
        "# Data Dictionary\n",
        "\n",
        "This directory holds the data contract for the project. Phase 4B\n",
        "will add a per-query datasheet (``datasheet_<query>.md``) under\n",
        "the governance scaffolding rules.\n",
        "\n",
        "## Primary Queries\n",
        "\n",
    ]
    for q in queries:
        name = q.get("name", "unnamed")
        row_order = q.get("expected_row_count_order", "unknown")
        purpose = q.get("purpose", "")
        lines.append(f"### `{name}`\n\n")
        lines.append(f"- **Expected row order:** {row_order}\n")
        lines.append(f"- **Purpose:** {purpose}\n\n")
    return "".join(lines)


def render_reports_intake_json(*, intake: dict[str, Any]) -> str:
    return json.dumps(intake, indent=2, default=str) + "\n"


def render_reports_intake_md(*, intake: dict[str, Any]) -> str:
    ms = intake.get("model_solution") or {}
    ev = intake.get("estimated_value") or {}
    gov = intake.get("governance") or {}
    return (
        "# Intake Report\n"
        "\n"
        f"- **Stakeholder:** `{intake.get('stakeholder_id', 'unknown')}`\n"
        f"- **Session:** `{intake.get('session_id', 'unknown')}`\n"
        f"- **Status:** `{intake.get('status', 'unknown')}`\n"
        f"- **Questions asked:** {intake.get('questions_asked', 0)}\n"
        f"- **Revision cycles:** {intake.get('revision_cycles', 0)}\n"
        "\n"
        "## Business Problem\n\n"
        f"{intake.get('business_problem', '')}\n\n"
        "## Proposed Solution\n\n"
        f"{intake.get('proposed_solution', '')}\n\n"
        "## Model Solution\n\n"
        f"- Target: `{ms.get('target_variable', 'n/a')}`\n"
        f"- Type: `{ms.get('model_type', 'other')}`\n"
        f"- Metrics: {', '.join(ms.get('evaluation_metrics') or []) or '(none)'}\n"
        "\n"
        "## Estimated Value\n\n"
        f"{ev.get('narrative', '')}\n\n"
        "## Governance\n\n"
        f"- Cycle time: `{gov.get('cycle_time', 'unknown')}`\n"
        f"- Risk tier: `{gov.get('risk_tier', 'unknown')}`\n"
        f"- Regulatory frameworks: {', '.join(gov.get('regulatory_frameworks') or []) or '(none)'}\n"
    )


def render_reports_data_json(*, data: dict[str, Any]) -> str:
    return json.dumps(data, indent=2, default=str) + "\n"


def render_reports_data_md(*, data: dict[str, Any]) -> str:
    queries = data.get("primary_queries") or []
    lines = [
        "# Data Report\n",
        "\n",
        f"- **Status:** `{data.get('status', 'unknown')}`\n",
        f"- **Primary queries:** {len(queries)}\n",
        "\n",
        "## Summary\n\n",
        str(data.get("summary", "")).strip() + "\n\n",
        "## Confirmed Expectations\n\n",
    ]
    for item in data.get("confirmed_expectations") or []:
        lines.append(f"- {item}\n")
    lines.append("\n## Unconfirmed Expectations\n\n")
    for item in data.get("unconfirmed_expectations") or []:
        lines.append(f"- {item}\n")
    lines.append("\n## Data Quality Concerns\n\n")
    for item in data.get("data_quality_concerns") or []:
        lines.append(f"- {item}\n")
    return "".join(lines)


# --- composition --------------------------------------------------------------


def build_base_files(
    *,
    intake: dict[str, Any],
    data: dict[str, Any],
    project_name: str,
    project_slug: str,
) -> dict[str, str]:
    """Return every non-governance file the website agent scaffolds in 4A.

    The resulting dict maps repo-relative path → file contents. The
    ``SCAFFOLD_BASE`` node writes this verbatim into
    ``WebsiteState.files_pending`` and ``INITIAL_COMMITS`` flushes it to
    the client in a single commit.
    """

    src_prefix = f"src/{project_slug}"
    primary_query_names = [
        q.get("name", f"query_{i}") for i, q in enumerate(data.get("primary_queries") or [])
    ]

    files: dict[str, str] = {
        ".gitignore": render_gitignore(),
        "README.md": render_readme(intake=intake, project_name=project_name),
        "pyproject.toml": render_pyproject(
            project_name=project_name, project_slug=project_slug
        ),
        f"{src_prefix}/__init__.py": render_src_init(
            project_name=project_name, project_slug=project_slug
        ),
        f"{src_prefix}/data_loading.py": render_data_loading(
            project_slug=project_slug, primary_query_names=primary_query_names
        ),
        f"{src_prefix}/features.py": render_features(),
        f"{src_prefix}/models.py": render_models(intake=intake),
        f"{src_prefix}/evaluation.py": render_evaluation(intake=intake),
        "analysis/01_business_understanding.qmd": render_qmd_business_understanding(
            intake=intake
        ),
        "analysis/02_data.qmd": render_qmd_data(data=data),
        "analysis/03_eda.qmd": render_qmd_eda(),
        "analysis/04_feature_engineering.qmd": render_qmd_feature_engineering(),
        "analysis/05_initial_models.qmd": render_qmd_initial_models(intake=intake),
        "analysis/06_implementation_plan.qmd": render_qmd_implementation_plan(
            intake=intake
        ),
        "analysis/99_extensions.qmd": render_qmd_extensions(),
        "tests/__init__.py": render_tests_init(),
        "tests/test_data_loading.py": render_test_stub("data_loading"),
        "tests/test_features.py": render_test_stub("features"),
        "tests/test_models.py": render_test_stub("models"),
        "tests/test_evaluation.py": render_test_stub("evaluation"),
        "data/README.md": render_data_readme(data=data),
        "reports/intake_report.json": render_reports_intake_json(intake=intake),
        "reports/intake_report.md": render_reports_intake_md(intake=intake),
        "reports/data_report.json": render_reports_data_json(data=data),
        "reports/data_report.md": render_reports_data_md(data=data),
    }
    files.update(render_primary_query_files(data=data))
    files.update(render_quality_check_files(data=data))
    return files
