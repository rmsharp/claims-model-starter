"""Governance file content generators for the Website Agent (Phase 4B).

Sibling to :mod:`templates` (which handles the Phase 4A *base* scaffold).
Keeping the two modules separate makes the 4A→4B split visible in review
and leaves ``templates.py`` untouched so the 4A acceptance tests keep
pinning the base scaffold byte-for-byte.

Responsibility (architecture-plan §8.2, §8.3, §11):

- Emit governance artifacts proportional to ``risk_tier`` and
  ``cycle_time`` from the intake report's ``GovernanceMetadata`` block.
- Emit ``data/datasheet_<query>.md`` per primary query in the data
  report (Gebru 2021 datasheet per query — "always" per §8.2).
- Emit ``.gitlab-ci.yml`` and ``.pre-commit-config.yaml`` (classified as
  governance artifacts by §8.2 — Phase 4A explicitly deferred these).
- Emit the monitoring cadence from §8.3 into ``ongoing_monitoring.md``.
- Populate a ``model_registry.json`` registry entry that mirrors the
  ``GovernanceManifest.model_registry_entry`` field.

The module is a pure Python collection of f-string templates — no
template engine, no side effects. ``build_governance_files(...)`` is the
composition entry point; everything else is private.
"""

from __future__ import annotations

import json
from typing import Any, Literal

CIPlatform = Literal["gitlab", "github"]

# ---------------------------------------------------------------------------
# Tier ordering helpers
# ---------------------------------------------------------------------------
#
# RiskTier literal ordering: tier_1_critical is the MOST severe, tier_4_low
# the LEAST. "tier 3+" in §8.2 means tier 3 or worse — i.e. tier 3, 2, 1.

_TIER_SEVERITY = {
    "tier_1_critical": 1,
    "tier_2_high": 2,
    "tier_3_moderate": 3,
    "tier_4_low": 4,
}


def _tier_at_least(risk_tier: str, threshold: str) -> bool:
    """Return True if ``risk_tier`` is at least as severe as ``threshold``.

    "at least tier 3" means tier 3 moderate or worse (so tier 1 and 2 also
    qualify). Lower severity number = more severe.
    """

    return _TIER_SEVERITY.get(risk_tier, 99) <= _TIER_SEVERITY.get(threshold, -1)


# ---------------------------------------------------------------------------
# Monitoring cadence (architecture-plan §8.3)
# ---------------------------------------------------------------------------

_CYCLE_CADENCE = {
    "strategic": "Annual review",
    "tactical": "Quarterly review",
    "operational": "Monthly monitoring",
    "continuous": "Automated continuous monitoring with monthly human review",
}


# ---------------------------------------------------------------------------
# Regulatory framework → artifacts mapping
# ---------------------------------------------------------------------------
#
# Each entry lists the governance artifacts (from §8.2) that directly
# satisfy the framework's documentation requirements. Only artifacts
# actually emitted for this project are retained in the final manifest.

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


def build_regulatory_mapping(
    *,
    frameworks: list[str],
    emitted_paths: set[str],
) -> dict[str, list[str]]:
    """Return ``framework → [artifacts]`` filtered to paths actually emitted.

    Frameworks outside the known set are included with an empty list so
    the manifest makes the gap visible to downstream reviewers.
    """

    mapping: dict[str, list[str]] = {}
    for framework in frameworks:
        candidates = _FRAMEWORK_ARTIFACTS.get(framework, [])
        mapping[framework] = [p for p in candidates if p in emitted_paths]
    return mapping


# ---------------------------------------------------------------------------
# Per-file renderers
# ---------------------------------------------------------------------------


def render_model_registry(
    *,
    intake: dict[str, Any],
    project_name: str,
    project_slug: str,
) -> str:
    """Render ``governance/model_registry.json`` and the matching dict entry.

    Returns the JSON text. The ``build_model_registry_entry`` helper below
    returns the same payload as a Python dict so ``GovernanceManifest``
    can echo it without re-parsing.
    """

    entry = build_model_registry_entry(
        intake=intake,
        project_name=project_name,
        project_slug=project_slug,
    )
    return json.dumps(entry, indent=2, default=str) + "\n"


def build_model_registry_entry(
    *,
    intake: dict[str, Any],
    project_name: str,
    project_slug: str,
) -> dict[str, Any]:
    governance = intake.get("governance") or {}
    model_solution = intake.get("model_solution") or {}
    return {
        "schema_version": "1.0.0",
        "model_id": project_slug,
        "project_name": project_name,
        "owner_stakeholder_id": intake.get("stakeholder_id", "unknown"),
        "intake_session_id": intake.get("session_id", "unknown"),
        "created_at": str(intake.get("created_at", "")),
        "target_variable": model_solution.get("target_variable"),
        "model_type": model_solution.get("model_type", "other"),
        "risk_tier": governance.get("risk_tier", "tier_4_low"),
        "cycle_time": governance.get("cycle_time", "tactical"),
        "regulatory_frameworks": list(governance.get("regulatory_frameworks") or []),
        "affects_consumers": bool(governance.get("affects_consumers", False)),
        "uses_protected_attributes": bool(
            governance.get("uses_protected_attributes", False)
        ),
    }


def render_model_card(*, intake: dict[str, Any], project_name: str) -> str:
    governance = intake.get("governance") or {}
    model_solution = intake.get("model_solution") or {}
    metrics = ", ".join(model_solution.get("evaluation_metrics") or []) or "(none declared)"
    frameworks = ", ".join(governance.get("regulatory_frameworks") or []) or "(none)"
    return (
        f"# Model Card — {project_name}\n"
        "\n"
        "> Per Mitchell et al. 2019, \"Model Cards for Model Reporting.\"\n"
        "> This template is seeded from the intake report; the Data Science\n"
        "> team is expected to expand each section before submitting for review.\n"
        "\n"
        "## Model Details\n"
        "\n"
        f"- **Model type:** `{model_solution.get('model_type', 'other')}`\n"
        f"- **Target variable:** `{model_solution.get('target_variable', 'n/a')}`\n"
        f"- **Is supervised:** `{model_solution.get('is_supervised', 'unknown')}`\n"
        f"- **Owner:** `{intake.get('stakeholder_id', 'unknown')}`\n"
        "\n"
        "## Intended Use\n"
        "\n"
        f"{intake.get('proposed_solution', '').strip()}\n"
        "\n"
        "## Factors\n"
        "\n"
        "List the subpopulations, feature groups, or environmental factors\n"
        "that influence model performance. Fill in during EDA.\n"
        "\n"
        "## Metrics\n"
        "\n"
        f"Requested evaluation metrics: {metrics}\n"
        "\n"
        "## Evaluation Data\n"
        "\n"
        "See `governance/three_pillar_validation.md` for the validation\n"
        "plan and `data/datasheet_<query>.md` for dataset documentation.\n"
        "\n"
        "## Training Data\n"
        "\n"
        "See `data/` datasheets and the Data Agent report under\n"
        "`reports/data_report.json`.\n"
        "\n"
        "## Quantitative Analyses\n"
        "\n"
        "To be populated by the Data Science team during model build.\n"
        "\n"
        "## Ethical Considerations\n"
        "\n"
        f"- Affects consumers: `{governance.get('affects_consumers', False)}`\n"
        f"- Uses protected attributes: `{governance.get('uses_protected_attributes', False)}`\n"
        f"- Regulatory frameworks: {frameworks}\n"
        "\n"
        "## Caveats and Recommendations\n"
        "\n"
        "The scaffolded repo is a starting point — all quantitative sections\n"
        "require human completion before the model can be approved.\n"
    )


def render_change_log(*, intake: dict[str, Any]) -> str:
    created = str(intake.get("created_at", "")) or "unknown"
    return (
        "# Change Log\n"
        "\n"
        "All material changes to this model are recorded here. Each entry\n"
        "should be reviewed by the model's second-line governance contact.\n"
        "\n"
        f"## {created} — Initial scaffold\n"
        "\n"
        "- Repository scaffolded by the Model Project Constructor pipeline.\n"
        f"- Intake session: `{intake.get('session_id', 'unknown')}`\n"
        f"- Requesting stakeholder: `{intake.get('stakeholder_id', 'unknown')}`\n"
        "- No production deployments yet.\n"
    )


def render_three_pillar_validation(*, intake: dict[str, Any]) -> str:
    governance = intake.get("governance") or {}
    return (
        "# Three-Pillar Validation Plan\n"
        "\n"
        "> Required for tier 3 and above per architecture-plan §8.2.\n"
        f"> Risk tier: `{governance.get('risk_tier', 'unknown')}`\n"
        "\n"
        "## Pillar 1 — Conceptual Soundness\n"
        "\n"
        "- Is the model formulation appropriate for the target definition?\n"
        "- Are the candidate features well-motivated and available at scoring time?\n"
        "- Are known alternatives considered and documented?\n"
        "\n"
        "## Pillar 2 — Ongoing Monitoring\n"
        "\n"
        "See `governance/ongoing_monitoring.md` for the cadence and metrics.\n"
        "\n"
        "## Pillar 3 — Outcomes Analysis\n"
        "\n"
        "Cannot be completed at scaffold time — requires production data.\n"
        "Document the outcomes-analysis plan here; execute after launch.\n"
    )


def render_ongoing_monitoring(*, intake: dict[str, Any]) -> str:
    governance = intake.get("governance") or {}
    cycle_time = str(governance.get("cycle_time", "tactical"))
    cadence = _CYCLE_CADENCE.get(cycle_time, "Quarterly review")
    return (
        "# Ongoing Monitoring Plan\n"
        "\n"
        f"- **Declared cycle time:** `{cycle_time}`\n"
        f"- **Default cadence (from architecture-plan §8.3):** {cadence}\n"
        "\n"
        "## Metrics to Track\n"
        "\n"
        "- Performance on the primary evaluation metrics (see model card)\n"
        "- Population stability across key features\n"
        "- Score distribution drift\n"
        "- Coverage / volume (how often is the model scored?)\n"
        "\n"
        "## Trigger Conditions\n"
        "\n"
        "Document the thresholds that trigger a re-review. The default is\n"
        "any 10% absolute drop in a primary metric or any breach of a\n"
        "fairness SLA — the Data Science team should tune these before\n"
        "handing the model off to production.\n"
    )


def render_deployment_gates(*, intake: dict[str, Any]) -> str:
    return (
        "# Deployment Gates\n"
        "\n"
        "> Checklist for staged rollout — required for tier 3 and above.\n"
        "\n"
        "## Stage 1 — Shadow\n"
        "\n"
        "- [ ] Model scores logged without affecting decisions\n"
        "- [ ] Monitoring dashboards live for ≥ 2 weeks\n"
        "- [ ] No SEV-1 alerts in shadow window\n"
        "\n"
        "## Stage 2 — Limited Production\n"
        "\n"
        "- [ ] Scoped to a subset of traffic\n"
        "- [ ] Human-in-the-loop override documented\n"
        "- [ ] Outcomes sampled and reviewed weekly\n"
        "\n"
        "## Stage 3 — Full Production\n"
        "\n"
        "- [ ] Monitoring cadence per `ongoing_monitoring.md`\n"
        "- [ ] Change log updated on every model refresh\n"
    )


def render_impact_assessment(*, intake: dict[str, Any]) -> str:
    governance = intake.get("governance") or {}
    estimated_value = intake.get("estimated_value") or {}
    narrative = str(estimated_value.get("narrative", "")).strip()
    return (
        "# Pre-Deployment Impact Assessment\n"
        "\n"
        "> Required for tier 2 and above per architecture-plan §8.2.\n"
        f"> Regulatory frameworks in scope: "
        f"{', '.join(governance.get('regulatory_frameworks') or []) or '(none)'}\n"
        "\n"
        "## Value Narrative\n"
        "\n"
        f"{narrative or '(fill in from intake report)'}\n"
        "\n"
        "## Risks\n"
        "\n"
        "- **Direct harms:** Who can be harmed if the model is wrong?\n"
        "- **Indirect harms:** What second-order effects does deployment create?\n"
        "- **Reversibility:** How quickly can an incorrect decision be unwound?\n"
        "- **Concentration:** Does the model amplify existing inequities?\n"
        "\n"
        "## Mitigations\n"
        "\n"
        "Document the mitigations that will be in place at launch. Link to\n"
        "`governance/deployment_gates.md` for staged rollout controls.\n"
    )


def render_regulatory_mapping(
    *,
    intake: dict[str, Any],
    mapping: dict[str, list[str]],
) -> str:
    governance = intake.get("governance") or {}
    lines = [
        "# Regulatory Mapping\n",
        "\n",
        "> Required for tier 2 and above per architecture-plan §8.2. Maps\n",
        "> each declared regulatory framework to the governance artifacts\n",
        "> that satisfy its documentation requirements in this repository.\n",
        "\n",
        f"- **Risk tier:** `{governance.get('risk_tier', 'unknown')}`\n",
        f"- **Affects consumers:** `{governance.get('affects_consumers', False)}`\n",
        "\n",
        "## Framework → Artifacts\n",
        "\n",
    ]
    if not mapping:
        lines.append("_(No regulatory frameworks declared in intake.)_\n")
    for framework, artifacts in sorted(mapping.items()):
        lines.append(f"### {framework}\n\n")
        if not artifacts:
            lines.append("_No scaffolded artifacts directly satisfy this framework._\n\n")
            continue
        for artifact in artifacts:
            lines.append(f"- `{artifact}`\n")
        lines.append("\n")
    return "".join(lines)


def render_lcp_integration(*, intake: dict[str, Any]) -> str:
    return (
        "# Life Cycle Process Integration\n"
        "\n"
        "> Required for tier 1 (critical) models per architecture-plan §8.2.\n"
        "\n"
        "## Pathway\n"
        "\n"
        "Document the LCP review gates for this model:\n"
        "\n"
        "1. **Concept review** — signed off before data pull.\n"
        "2. **Development review** — signed off before validation.\n"
        "3. **Validation review** — signed off before shadow deployment.\n"
        "4. **Deployment review** — signed off before full production.\n"
        "5. **Post-deployment review** — annual or on material change.\n"
        "\n"
        "Each review requires sign-off from the second-line governance\n"
        "function and is recorded in `governance/change_log.md`.\n"
    )


def render_audit_log_readme() -> str:
    return (
        "# Audit Log\n"
        "\n"
        "> Required for tier 1 (critical) models per architecture-plan §8.2.\n"
        "\n"
        "This directory stores dated audit evidence. One subdirectory per\n"
        "review event, containing:\n"
        "\n"
        "- `review.md` — minutes and decisions\n"
        "- `artifacts/` — supporting documents\n"
        "- `signoffs.yaml` — structured sign-off record\n"
        "\n"
        "The directory is scaffolded empty — populate it as reviews occur.\n"
    )


def render_eu_ai_act_compliance(*, intake: dict[str, Any]) -> str:
    governance = intake.get("governance") or {}
    return (
        "# EU AI Act Compliance Mapping\n"
        "\n"
        "> Emitted when `affects_consumers=true` in the intake governance\n"
        "> block. Maps the model to EU AI Act Articles 9–15.\n"
        "\n"
        f"- **Affects consumers:** `{governance.get('affects_consumers', False)}`\n"
        f"- **Uses protected attributes:** `{governance.get('uses_protected_attributes', False)}`\n"
        "\n"
        "## Article 9 — Risk Management System\n"
        "\n"
        "See `governance/three_pillar_validation.md` and\n"
        "`governance/ongoing_monitoring.md`.\n"
        "\n"
        "## Article 10 — Data and Data Governance\n"
        "\n"
        "See the per-query datasheets under `data/datasheet_*.md`.\n"
        "\n"
        "## Article 11 — Technical Documentation\n"
        "\n"
        "See `governance/model_card.md` and this repository's `analysis/`\n"
        "narratives.\n"
        "\n"
        "## Article 12 — Record-Keeping\n"
        "\n"
        "See `governance/change_log.md` and (for tier 1) `governance/audit_log/`.\n"
        "\n"
        "## Article 13 — Transparency to Users\n"
        "\n"
        "Document the user-facing explanation of the model's role in the\n"
        "decision path. Fill in before launch.\n"
        "\n"
        "## Article 14 — Human Oversight\n"
        "\n"
        "Document the human-in-the-loop override. See\n"
        "`governance/deployment_gates.md` for rollout controls.\n"
        "\n"
        "## Article 15 — Accuracy, Robustness, Cybersecurity\n"
        "\n"
        "Reference validation and monitoring plans.\n"
    )


def render_datasheet(*, query: dict[str, Any]) -> str:
    """Render a Gebru-2021 datasheet for a single primary query.

    ``query`` is one element from ``DataReport.primary_queries`` dumped to
    JSON (so the nested ``datasheet`` is a dict).
    """

    name = query.get("name", "unnamed")
    datasheet = query.get("datasheet") or {}
    biases = datasheet.get("known_biases") or []
    biases_md = "\n".join(f"- {b}" for b in biases) or "- (none declared)"
    return (
        f"# Datasheet — `{name}`\n"
        "\n"
        "> Per Gebru et al. 2021, \"Datasheets for Datasets.\"\n"
        f"> Source SQL: `queries/primary/{name}.sql`\n"
        "\n"
        "## Motivation\n\n"
        f"{datasheet.get('motivation', '(not provided)')}\n"
        "\n"
        "## Composition\n\n"
        f"{datasheet.get('composition', '(not provided)')}\n"
        "\n"
        "## Collection Process\n\n"
        f"{datasheet.get('collection_process', '(not provided)')}\n"
        "\n"
        "## Preprocessing\n\n"
        f"{datasheet.get('preprocessing', '(not provided)')}\n"
        "\n"
        "## Uses\n\n"
        f"{datasheet.get('uses', '(not provided)')}\n"
        "\n"
        "## Known Biases\n\n"
        f"{biases_md}\n"
        "\n"
        "## Maintenance\n\n"
        f"{datasheet.get('maintenance', '(not provided)')}\n"
    )


def render_gitlab_ci() -> str:
    return (
        "stages:\n"
        "  - lint\n"
        "  - test\n"
        "  - governance\n"
        "\n"
        "default:\n"
        "  image: python:3.11\n"
        "  before_script:\n"
        "    - pip install uv\n"
        "    - uv sync\n"
        "\n"
        "lint:\n"
        "  stage: lint\n"
        "  script:\n"
        "    - uv run ruff check .\n"
        "\n"
        "unit-tests:\n"
        "  stage: test\n"
        "  script:\n"
        "    - uv run pytest -q\n"
        "\n"
        "model-registry-schema:\n"
        "  stage: governance\n"
        "  script:\n"
        '    - uv run python -c "import json; json.load(open('
        "'governance/model_registry.json'))\"\n"
    )


def render_github_actions_ci() -> str:
    return (
        "name: ci\n"
        "\n"
        "on:\n"
        "  push:\n"
        "    branches: [main]\n"
        "  pull_request:\n"
        "    branches: [main]\n"
        "\n"
        "jobs:\n"
        "  lint:\n"
        "    runs-on: ubuntu-latest\n"
        "    steps:\n"
        "      - uses: actions/checkout@v4\n"
        "      - uses: actions/setup-python@v5\n"
        "        with:\n"
        "          python-version: '3.11'\n"
        "      - run: pip install uv\n"
        "      - run: uv sync\n"
        "      - run: uv run ruff check .\n"
        "\n"
        "  test:\n"
        "    runs-on: ubuntu-latest\n"
        "    steps:\n"
        "      - uses: actions/checkout@v4\n"
        "      - uses: actions/setup-python@v5\n"
        "        with:\n"
        "          python-version: '3.11'\n"
        "      - run: pip install uv\n"
        "      - run: uv sync\n"
        "      - run: uv run pytest -q\n"
        "\n"
        "  governance:\n"
        "    runs-on: ubuntu-latest\n"
        "    steps:\n"
        "      - uses: actions/checkout@v4\n"
        "      - uses: actions/setup-python@v5\n"
        "        with:\n"
        "          python-version: '3.11'\n"
        "      - run: pip install uv\n"
        "      - run: uv sync\n"
        '      - run: uv run python -c "import json; json.load(open('
        "'governance/model_registry.json'))\"\n"
    )


def render_pre_commit_config() -> str:
    return (
        "repos:\n"
        "  - repo: https://github.com/astral-sh/ruff-pre-commit\n"
        "    rev: v0.5.0\n"
        "    hooks:\n"
        "      - id: ruff\n"
        "      - id: ruff-format\n"
        "  - repo: local\n"
        "    hooks:\n"
        "      - id: model-registry-schema\n"
        "        name: Validate governance/model_registry.json\n"
        "        entry: python -c \"import json, sys; "
        "json.load(open('governance/model_registry.json'))\"\n"
        "        language: system\n"
        "        files: ^governance/model_registry\\.json$\n"
    )


# ---------------------------------------------------------------------------
# Fairness / analysis scaffolds (uses_protected_attributes=true)
# ---------------------------------------------------------------------------


def render_fairness_audit_qmd() -> str:
    return (
        "---\n"
        "title: \"Fairness Audit\"\n"
        "format: html\n"
        "---\n"
        "\n"
        "# Fairness Audit\n"
        "\n"
        "This notebook is scaffolded because the intake report declared\n"
        "`uses_protected_attributes=true`. It should exercise the fairness\n"
        "module in `src/<slug>/fairness/` and document the subgroup\n"
        "performance breakdown.\n"
        "\n"
        "```{python}\n"
        "# from <project_slug>.fairness.audit import subgroup_metrics\n"
        "# subgroup_metrics(df, protected_attribute='...', metric='...')\n"
        "```\n"
    )


def render_fairness_module() -> str:
    return (
        '"""Fairness audit helpers (scaffolded by governance — fill in).\n'
        "\n"
        "Emitted because the intake report flagged\n"
        "``uses_protected_attributes=true``. Implement subgroup performance\n"
        "metrics and bias diagnostics here; exercise them from\n"
        "``analysis/fairness_audit.qmd`` and unit-test them in\n"
        "``tests/test_fairness.py``.\n"
        '"""\n'
        "\n"
        "from __future__ import annotations\n"
        "\n"
        "\n"
        "def subgroup_metrics(\n"
        "    df: object,\n"
        "    *,\n"
        "    protected_attribute: str,\n"
        "    metric: str,\n"
        ") -> dict[str, float]:\n"
        '    """Return metric values broken down by a protected attribute."""\n'
        '    raise NotImplementedError("Wire up fairness metrics")\n'
    )


def render_fairness_package_init() -> str:
    return (
        '"""Fairness audit package.\n'
        "\n"
        "Scaffolded because the intake declared ``uses_protected_attributes=true``.\n"
        '"""\n'
        "\n"
        "from __future__ import annotations\n"
        "\n"
        '__all__: list[str] = ["subgroup_metrics"]\n'
        "\n"
        "from .audit import subgroup_metrics  # noqa: F401\n"
    )


def render_fairness_test_stub() -> str:
    return (
        '"""Unit tests for the fairness audit module (scaffolded)."""\n'
        "\n"
        "from __future__ import annotations\n"
        "\n"
        "import pytest\n"
        "\n"
        "\n"
        "def test_subgroup_metrics_is_scaffolded() -> None:\n"
        "    from importlib import import_module\n"
        "\n"
        "    module = import_module('<project_slug>.fairness.audit')\n"
        "    assert hasattr(module, 'subgroup_metrics')\n"
        "    with pytest.raises(NotImplementedError):\n"
        "        module.subgroup_metrics(\n"
        "            None, protected_attribute='x', metric='accuracy'\n"
        "        )\n"
    )


# ---------------------------------------------------------------------------
# Composition entry points
# ---------------------------------------------------------------------------


def build_governance_files(
    *,
    intake: dict[str, Any],
    data: dict[str, Any],
    project_name: str,
    project_slug: str,
    ci_platform: CIPlatform = "gitlab",
) -> dict[str, str]:
    """Return every governance file this project emits.

    The caller (``scaffold_governance``) merges this dict into
    ``WebsiteState.files_pending`` so ``INITIAL_COMMITS`` can flush it in
    a single commit. Every key in the returned dict is considered a
    governance artifact and is added to ``WebsiteState.governance_paths``
    for manifest assembly.
    """

    governance = intake.get("governance") or {}
    risk_tier = str(governance.get("risk_tier", "tier_4_low"))
    affects_consumers = bool(governance.get("affects_consumers", False))

    files: dict[str, str] = {}

    # --- Always emitted (§8.2 "Always") ---
    files["governance/model_registry.json"] = render_model_registry(
        intake=intake, project_name=project_name, project_slug=project_slug
    )
    files["governance/model_card.md"] = render_model_card(
        intake=intake, project_name=project_name
    )
    files["governance/change_log.md"] = render_change_log(intake=intake)
    if ci_platform == "gitlab":
        files[".gitlab-ci.yml"] = render_gitlab_ci()
    else:
        files[".github/workflows/ci.yml"] = render_github_actions_ci()
    files[".pre-commit-config.yaml"] = render_pre_commit_config()

    # One datasheet per primary query, per Gebru 2021.
    for query in data.get("primary_queries") or []:
        name = query.get("name", "unnamed")
        files[f"data/datasheet_{name}.md"] = render_datasheet(query=query)

    # --- Tier 3+ (tier 3, 2, 1) ---
    if _tier_at_least(risk_tier, "tier_3_moderate"):
        files["governance/three_pillar_validation.md"] = render_three_pillar_validation(
            intake=intake
        )
        files["governance/ongoing_monitoring.md"] = render_ongoing_monitoring(
            intake=intake
        )
        files["governance/deployment_gates.md"] = render_deployment_gates(
            intake=intake
        )

    # --- Tier 2+ (tier 2, 1) ---
    if _tier_at_least(risk_tier, "tier_2_high"):
        files["governance/impact_assessment.md"] = render_impact_assessment(
            intake=intake
        )
        # Regulatory mapping uses the final emitted-paths set — pass the
        # current in-progress set (will include tier 2+ artifacts at this
        # point; that's correct because §8.2 only emits regulatory_mapping
        # for tier 2+ anyway).
        tentative_paths = set(files.keys()) | {"governance/regulatory_mapping.md"}
        mapping = build_regulatory_mapping(
            frameworks=list(governance.get("regulatory_frameworks") or []),
            emitted_paths=tentative_paths,
        )
        files["governance/regulatory_mapping.md"] = render_regulatory_mapping(
            intake=intake, mapping=mapping
        )

    # --- Tier 1 only ---
    if _tier_at_least(risk_tier, "tier_1_critical"):
        files["governance/lcp_integration.md"] = render_lcp_integration(intake=intake)
        files["governance/audit_log/README.md"] = render_audit_log_readme()

    # --- Consumer-facing ---
    if affects_consumers:
        files["governance/eu_ai_act_compliance.md"] = render_eu_ai_act_compliance(
            intake=intake
        )

    return files


def build_analysis_files(
    *,
    intake: dict[str, Any],
    project_slug: str,
) -> dict[str, str]:
    """Governance-driven analysis scaffolds.

    Only emits when ``uses_protected_attributes=true`` — Phase 4A's
    ``build_base_files`` already writes the seven standard ``analysis/*.qmd``
    narratives from §11.
    """

    governance = intake.get("governance") or {}
    if not governance.get("uses_protected_attributes"):
        return {}

    return {
        "analysis/fairness_audit.qmd": render_fairness_audit_qmd(),
        f"src/{project_slug}/fairness/__init__.py": render_fairness_package_init(),
        f"src/{project_slug}/fairness/audit.py": render_fairness_module(),
    }


def build_test_files(
    *,
    intake: dict[str, Any],
    project_slug: str,
) -> dict[str, str]:
    """Governance-driven test scaffolds.

    Only emits when ``uses_protected_attributes=true``. Phase 4A's
    ``build_base_files`` already writes the baseline ``tests/test_*.py``
    stubs from §11.
    """

    governance = intake.get("governance") or {}
    if not governance.get("uses_protected_attributes"):
        return {}

    return {
        "tests/test_fairness.py": render_fairness_test_stub(),
    }


# ---------------------------------------------------------------------------
# Artifact classification (for GovernanceManifest.artifacts_created)
# ---------------------------------------------------------------------------


def is_governance_artifact(path: str) -> bool:
    """Return True if ``path`` is classified as a governance artifact.

    Mirrors §8.2 — anything under ``governance/``, any per-query datasheet,
    the CI and pre-commit config, and the optional fairness scaffolds.
    """

    if path.startswith("governance/"):
        return True
    if path.startswith("data/datasheet_"):
        return True
    if path in {
        ".gitlab-ci.yml",
        ".github/workflows/ci.yml",
        ".pre-commit-config.yaml",
    }:
        return True
    if path == "analysis/fairness_audit.qmd":
        return True
    if "/fairness/" in path:
        return True
    return path == "tests/test_fairness.py"


__all__ = [
    "CIPlatform",
    "build_governance_files",
    "build_analysis_files",
    "build_test_files",
    "build_model_registry_entry",
    "build_regulatory_mapping",
    "is_governance_artifact",
    "render_github_actions_ci",
    "render_gitlab_ci",
]
