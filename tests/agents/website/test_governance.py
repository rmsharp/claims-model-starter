"""Tier 1 / tier 2 / tier 3 governance fan-out (architecture-plan §8.2, §14 Phase 4B).

Each tier has a distinct JSON intake fixture under ``tests/fixtures/``:

- ``tier1_intake.json`` — tier_1_critical, affects_consumers=True,
  uses_protected_attributes=True, cycle_time=continuous, 4 frameworks
- ``tier2_intake.json`` — tier_2_high, affects_consumers=False,
  uses_protected_attributes=False, cycle_time=strategic, 2 frameworks
- ``subrogation_intake.json`` — tier_3_moderate, affects_consumers=True,
  uses_protected_attributes=False, cycle_time=tactical, 2 frameworks

Together they exercise every conditional branch in ``build_governance_files``
and the regulatory-mapping computation in ``build_repo_project_result``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal, cast

import pytest

from model_project_constructor.agents.website.agent import WebsiteAgent
from model_project_constructor.agents.website.fake_client import FakeRepoClient
from model_project_constructor.schemas.v1.data import DataReport
from model_project_constructor.schemas.v1.intake import IntakeReport
from model_project_constructor.schemas.v1.repo import RepoTarget

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures"


@pytest.fixture
def data_report() -> DataReport:
    return DataReport.model_validate_json(
        (FIXTURES / "sample_datareport.json").read_text()
    )


@pytest.fixture
def tier1_intake() -> IntakeReport:
    return IntakeReport.model_validate_json(
        (FIXTURES / "tier1_intake.json").read_text()
    )


@pytest.fixture
def tier2_intake() -> IntakeReport:
    return IntakeReport.model_validate_json(
        (FIXTURES / "tier2_intake.json").read_text()
    )


@pytest.fixture
def tier3_intake() -> IntakeReport:
    return IntakeReport.model_validate_json(
        (FIXTURES / "subrogation_intake.json").read_text()
    )


def _run_agent(
    intake: IntakeReport,
    data: DataReport,
    *,
    ci_platform: str = "gitlab",
    ci_host_config: Any = None,
) -> tuple[Any, FakeRepoClient]:
    client = FakeRepoClient()
    target = RepoTarget(
        host_url="https://gitlab.example.com",
        namespace="data-science/model-drafts",
        project_name_hint=intake.session_id,
        visibility="private",
    )
    platform = cast(Literal["gitlab", "github"], ci_platform)
    result = WebsiteAgent(
        client, ci_platform=platform, ci_host_config=ci_host_config
    ).run(intake, data, target)
    return result, client


# ---------------------------------------------------------------------------
# Tier 1 — the big one: every possible governance artifact
# ---------------------------------------------------------------------------


class TestTier1Critical:
    def test_all_tier1_artifacts_present(
        self, tier1_intake: IntakeReport, data_report: DataReport
    ) -> None:
        result, _ = _run_agent(tier1_intake, data_report)
        files = set(result.files_created)

        assert result.status == "COMPLETE"

        # Always
        assert "governance/model_registry.json" in files
        assert "governance/model_card.md" in files
        assert "governance/change_log.md" in files
        assert ".gitlab-ci.yml" in files
        assert ".pre-commit-config.yaml" in files
        assert "data/datasheet_subrogation_training_set.md" in files

        # Tier 3+
        assert "governance/three_pillar_validation.md" in files
        assert "governance/ongoing_monitoring.md" in files
        assert "governance/deployment_gates.md" in files

        # Tier 2+
        assert "governance/impact_assessment.md" in files
        assert "governance/regulatory_mapping.md" in files

        # Tier 1 only
        assert "governance/lcp_integration.md" in files
        assert "governance/audit_log/README.md" in files

        # affects_consumers=true
        assert "governance/eu_ai_act_compliance.md" in files

        # uses_protected_attributes=true → fairness scaffolds
        assert "analysis/fairness_audit.qmd" in files
        assert any(f.endswith("/fairness/audit.py") for f in files)
        assert any(f.endswith("/fairness/__init__.py") for f in files)
        assert "tests/test_fairness.py" in files

    def test_tier1_manifest_reflects_every_framework(
        self, tier1_intake: IntakeReport, data_report: DataReport
    ) -> None:
        result, _ = _run_agent(tier1_intake, data_report)

        manifest = result.governance_manifest
        assert manifest.risk_tier == "tier_1_critical"
        assert manifest.cycle_time == "continuous"

        # All 4 declared frameworks appear in the mapping
        frameworks = set(manifest.regulatory_mapping.keys())
        assert {"SR_26_2", "NAIC_AIS", "EU_AI_ACT_ART_9", "ASOP_56"} <= frameworks

        # EU_AI_ACT_ART_9 binds to eu_ai_act_compliance.md (committed at tier 1)
        assert (
            "governance/eu_ai_act_compliance.md"
            in manifest.regulatory_mapping["EU_AI_ACT_ART_9"]
        )
        # SR_26_2 binds to three_pillar_validation.md (tier 3+)
        assert (
            "governance/three_pillar_validation.md"
            in manifest.regulatory_mapping["SR_26_2"]
        )
        # NAIC_AIS binds to impact_assessment.md (tier 2+)
        assert (
            "governance/impact_assessment.md"
            in manifest.regulatory_mapping["NAIC_AIS"]
        )

    def test_tier1_ongoing_monitoring_has_continuous_cadence(
        self, tier1_intake: IntakeReport, data_report: DataReport
    ) -> None:
        """§8.3: continuous cycle-time should yield the automated-monitoring cadence."""

        result, client = _run_agent(tier1_intake, data_report)
        stored = client.get_files(result.project_id)
        body = stored["governance/ongoing_monitoring.md"]
        assert "Automated continuous monitoring" in body

    def test_tier1_registry_entry_populated(
        self, tier1_intake: IntakeReport, data_report: DataReport
    ) -> None:
        result, _ = _run_agent(tier1_intake, data_report)
        entry = result.governance_manifest.model_registry_entry

        assert entry["risk_tier"] == "tier_1_critical"
        assert entry["cycle_time"] == "continuous"
        assert entry["affects_consumers"] is True
        assert entry["uses_protected_attributes"] is True
        assert entry["intake_session_id"] == "intake_renewals_001"
        assert "SR_26_2" in entry["regulatory_frameworks"]


# ---------------------------------------------------------------------------
# Tier 2 — medium fan-out: no EU AI Act, no fairness, no tier-1 artifacts
# ---------------------------------------------------------------------------


class TestTier2High:
    def test_tier2_artifacts_present_and_tier1_artifacts_absent(
        self, tier2_intake: IntakeReport, data_report: DataReport
    ) -> None:
        result, _ = _run_agent(tier2_intake, data_report)
        files = set(result.files_created)

        # Always + tier 3+ + tier 2+
        assert "governance/model_registry.json" in files
        assert "governance/three_pillar_validation.md" in files
        assert "governance/impact_assessment.md" in files
        assert "governance/regulatory_mapping.md" in files

        # Tier 1 only → absent
        assert "governance/lcp_integration.md" not in files
        assert "governance/audit_log/README.md" not in files

        # affects_consumers=false → no EU AI Act
        assert "governance/eu_ai_act_compliance.md" not in files

        # uses_protected_attributes=false → no fairness
        assert "analysis/fairness_audit.qmd" not in files
        assert not any("/fairness/" in f for f in files)
        assert "tests/test_fairness.py" not in files

    def test_tier2_manifest_has_only_declared_frameworks(
        self, tier2_intake: IntakeReport, data_report: DataReport
    ) -> None:
        result, _ = _run_agent(tier2_intake, data_report)
        mapping = result.governance_manifest.regulatory_mapping

        # Tier 2 fixture declares exactly SR_26_2 + ASOP_56
        assert set(mapping.keys()) == {"SR_26_2", "ASOP_56"}
        # EU_AI_ACT_ART_9 is NOT declared and NOT in the mapping
        assert "EU_AI_ACT_ART_9" not in mapping

    def test_tier2_strategic_cycle_cadence(
        self, tier2_intake: IntakeReport, data_report: DataReport
    ) -> None:
        result, client = _run_agent(tier2_intake, data_report)
        stored = client.get_files(result.project_id)
        body = stored["governance/ongoing_monitoring.md"]
        assert "Annual review" in body


# ---------------------------------------------------------------------------
# Tier 3 — minimum fan-out: no tier-2 artifacts, no fairness
# ---------------------------------------------------------------------------


class TestTier3Moderate:
    def test_tier3_emits_tier3_and_always_only(
        self, tier3_intake: IntakeReport, data_report: DataReport
    ) -> None:
        result, _ = _run_agent(tier3_intake, data_report)
        files = set(result.files_created)

        # Tier 3+ present
        assert "governance/three_pillar_validation.md" in files
        assert "governance/ongoing_monitoring.md" in files
        assert "governance/deployment_gates.md" in files

        # Tier 2-only absent
        assert "governance/impact_assessment.md" not in files
        assert "governance/regulatory_mapping.md" not in files

        # Tier 1-only absent
        assert "governance/lcp_integration.md" not in files

        # affects_consumers=true → EU AI Act present
        assert "governance/eu_ai_act_compliance.md" in files

    def test_tier3_tactical_cycle_cadence(
        self, tier3_intake: IntakeReport, data_report: DataReport
    ) -> None:
        result, client = _run_agent(tier3_intake, data_report)
        stored = client.get_files(result.project_id)
        body = stored["governance/ongoing_monitoring.md"]
        assert "Quarterly review" in body

    @pytest.mark.parametrize("ci_platform", ["gitlab", "github"])
    def test_tier3_ci_platform_branches(
        self,
        tier3_intake: IntakeReport,
        data_report: DataReport,
        ci_platform: str,
    ) -> None:
        """Phase B: governance scaffold emits exactly one CI file matching
        ``ci_platform``. Pin both presence (positive) and absence (negative)
        of each path so a regression that emits both, neither, or the wrong
        one fails loudly. Tier-3+ artifacts must be unaffected by the switch.
        """
        result, _ = _run_agent(tier3_intake, data_report, ci_platform=ci_platform)
        files = set(result.files_created)

        if ci_platform == "gitlab":
            assert ".gitlab-ci.yml" in files
            assert ".github/workflows/ci.yml" not in files
        else:
            assert ".github/workflows/ci.yml" in files
            assert ".gitlab-ci.yml" not in files

        # CI is always classified as a governance artifact regardless
        # of which file the platform chose.
        assert ".pre-commit-config.yaml" in files

        # Tier-3 fan-out must be unaffected by the CI switch.
        assert "governance/three_pillar_validation.md" in files
        assert "governance/ongoing_monitoring.md" in files
        assert "governance/deployment_gates.md" in files

        # Manifest count of CI artifacts is unchanged across platforms:
        # exactly one CI yaml plus the pre-commit config.
        ci_artifacts = {
            f
            for f in result.governance_manifest.artifacts_created
            if f in {".gitlab-ci.yml", ".github/workflows/ci.yml"}
        }
        assert len(ci_artifacts) == 1

    @pytest.mark.parametrize("ci_platform", ["gitlab", "github"])
    def test_tier3_ci_artifact_in_manifest(
        self,
        tier3_intake: IntakeReport,
        data_report: DataReport,
        ci_platform: str,
    ) -> None:
        """The platform-specific CI file must show up in
        ``GovernanceManifest.artifacts_created`` because it's classified
        as governance regardless of which platform produced it."""
        result, _ = _run_agent(tier3_intake, data_report, ci_platform=ci_platform)
        artifacts = set(result.governance_manifest.artifacts_created)
        if ci_platform == "gitlab":
            assert ".gitlab-ci.yml" in artifacts
            assert ".github/workflows/ci.yml" not in artifacts
        else:
            assert ".github/workflows/ci.yml" in artifacts
            assert ".gitlab-ci.yml" not in artifacts


# ---------------------------------------------------------------------------
# build_governance_files unit tests (no LangGraph)
# ---------------------------------------------------------------------------


class TestBuildGovernanceFilesUnit:
    @pytest.mark.parametrize("ci_platform", ["gitlab", "github"])
    def test_tier4_emits_only_always_artifacts(
        self, data_report: DataReport, ci_platform: str
    ) -> None:
        """A tier 4 low model gets none of the tiered artifacts — only
        'always' + consumer/fairness conditionals (both off here).

        Parametrized over ``ci_platform`` so the always-emitted CI file is
        platform-correct: GitLab → ``.gitlab-ci.yml``,
        GitHub → ``.github/workflows/ci.yml``. Both positive AND negative
        assertions are pinned per platform.
        """

        from model_project_constructor.agents.website.governance_templates import (
            build_governance_files,
        )

        intake = {
            "governance": {
                "cycle_time": "tactical",
                "risk_tier": "tier_4_low",
                "regulatory_frameworks": [],
                "affects_consumers": False,
                "uses_protected_attributes": False,
            },
            "stakeholder_id": "x",
            "session_id": "s",
            "created_at": "2026-01-01T00:00:00Z",
            "model_solution": {"target_variable": "t", "model_type": "other"},
            "proposed_solution": "ps",
        }
        platform = cast(Literal["gitlab", "github"], ci_platform)
        files = build_governance_files(
            intake=intake,
            data=data_report.model_dump(mode="json"),
            project_name="p",
            project_slug="p",
            ci_platform=platform,
        )

        assert "governance/model_registry.json" in files
        assert "governance/model_card.md" in files
        assert "governance/change_log.md" in files
        assert ".pre-commit-config.yaml" in files

        # Platform-gated CI file: pin both presence AND absence.
        if ci_platform == "gitlab":
            assert ".gitlab-ci.yml" in files
            assert ".github/workflows/ci.yml" not in files
        else:
            assert ".github/workflows/ci.yml" in files
            assert ".gitlab-ci.yml" not in files

        # None of the tiered artifacts
        assert "governance/three_pillar_validation.md" not in files
        assert "governance/impact_assessment.md" not in files
        assert "governance/lcp_integration.md" not in files
        assert "governance/eu_ai_act_compliance.md" not in files

    def test_datasheet_emitted_per_query(
        self, data_report: DataReport
    ) -> None:
        from model_project_constructor.agents.website.governance_templates import (
            build_governance_files,
        )

        intake = {
            "governance": {
                "cycle_time": "tactical",
                "risk_tier": "tier_4_low",
                "regulatory_frameworks": [],
                "affects_consumers": False,
                "uses_protected_attributes": False,
            },
            "stakeholder_id": "x",
            "session_id": "s",
            "created_at": "2026-01-01",
            "model_solution": {"target_variable": "t", "model_type": "other"},
            "proposed_solution": "",
        }
        files = build_governance_files(
            intake=intake,
            data=data_report.model_dump(mode="json"),
            project_name="p",
            project_slug="p",
        )
        assert "data/datasheet_subrogation_training_set.md" in files

    def test_regulatory_mapping_filters_unknown_framework(self) -> None:
        from model_project_constructor.agents.website.governance_templates import (
            build_regulatory_mapping,
        )

        mapping = build_regulatory_mapping(
            frameworks=["SR_26_2", "UNKNOWN_FRAMEWORK"],
            emitted_paths={"governance/model_card.md"},
        )
        assert mapping["SR_26_2"] == ["governance/model_card.md"]
        # Unknown framework appears with an empty list so it's visible
        assert mapping["UNKNOWN_FRAMEWORK"] == []

    def test_is_governance_artifact_classification(self) -> None:
        from model_project_constructor.agents.website.governance_templates import (
            is_governance_artifact,
        )

        assert is_governance_artifact("governance/model_card.md")
        assert is_governance_artifact("data/datasheet_foo.md")
        assert is_governance_artifact(".gitlab-ci.yml")
        assert is_governance_artifact(".github/workflows/ci.yml")
        assert is_governance_artifact(".pre-commit-config.yaml")
        assert is_governance_artifact("analysis/fairness_audit.qmd")
        assert is_governance_artifact("src/proj/fairness/audit.py")
        assert is_governance_artifact("tests/test_fairness.py")

        # Non-governance paths
        assert not is_governance_artifact("README.md")
        assert not is_governance_artifact("src/proj/models.py")
        assert not is_governance_artifact("analysis/03_eda.qmd")
        assert not is_governance_artifact("tests/test_features.py")

    def test_impact_assessment_surfaces_cost_bands(self) -> None:
        from model_project_constructor.agents.website.governance_templates import (
            render_impact_assessment,
        )

        intake = {
            "governance": {"regulatory_frameworks": ["SR_26_2"]},
            "estimated_value": {
                "narrative": "A 10% lift yields ~$3M annually.",
                "annual_cost_of_inaction_usd_low": 2000000.0,
                "annual_cost_of_inaction_usd_high": 4000000.0,
                "implementation_cost_band_usd_low": 250000.0,
                "implementation_cost_band_usd_high": 500000.0,
            },
        }
        out = render_impact_assessment(intake=intake)
        assert "## Value Narrative" in out
        assert "Estimated annual cost of inaction" in out
        assert "$2,000,000 – $4,000,000 per year" in out
        assert "Estimated implementation cost" in out
        assert "$250,000 – $500,000" in out

    def test_impact_assessment_missing_cost_bands_render_placeholder(
        self,
    ) -> None:
        from model_project_constructor.agents.website.governance_templates import (
            render_impact_assessment,
        )

        out = render_impact_assessment(
            intake={"governance": {}, "estimated_value": {}}
        )
        assert "Estimated annual cost of inaction:** (not estimated)" in out
        assert "Estimated implementation cost:** (not estimated)" in out

    def test_ongoing_monitoring_threads_baseline_metric(self) -> None:
        from model_project_constructor.agents.website.governance_templates import (
            render_ongoing_monitoring,
        )

        intake = {
            "governance": {"cycle_time": "tactical"},
            "value_measurement_plan": {
                "baseline_metric_name": "subrogation_recovery_rate",
                "review_cadence": "monthly",
            },
        }
        out = render_ongoing_monitoring(intake=intake)
        # The cycle-time cadence rendering is unchanged.
        assert "Quarterly review" in out
        # The intake's value-measurement baseline metric is threaded in.
        assert "Business-value baseline metric:** `subrogation_recovery_rate`" in out
        assert "`monthly` cadence" in out
        # Populated plan → no "none declared" / "not declared" placeholder.
        assert "none declared at intake" not in out
        assert "was not declared at intake" not in out

    def test_ongoing_monitoring_missing_value_plan_renders_placeholder(
        self,
    ) -> None:
        from model_project_constructor.agents.website.governance_templates import (
            render_ongoing_monitoring,
        )

        out = render_ongoing_monitoring(intake={"governance": {}})
        # Section still renders the baseline-metric bullet, as a placeholder.
        assert "Business-value baseline metric:** (none declared at intake" in out
        assert "business-value review cadence was not declared at intake" in out
        # No real metric name leaks through.
        assert "subrogation_recovery_rate" not in out

    def test_deployment_gates_includes_measurement_plan_review(self) -> None:
        from model_project_constructor.agents.website.governance_templates import (
            render_deployment_gates,
        )

        out = render_deployment_gates(intake={})
        # The Phase-5 review gate is present in Stage 1.
        assert "Production Measurement Plan" in out
        assert "06_implementation_plan.qmd" in out
        # The pre-existing Stage 1 gates are untouched.
        assert "Model scores logged without affecting decisions" in out
        assert "## Stage 3 — Full Production" in out


class TestFrameworkPromptMapParity:
    """Audit #39 — the intake prompt's regulatory-framework enumeration
    (producer) and the website agent's ``_FRAMEWORK_ARTIFACTS`` map (consumer)
    must not drift. A framework the prompt nudges the LLM toward but the map
    omits scaffolds zero governance artifacts (a silent compliance gap, e.g.
    the original ``GDPR_ART_22``); a mapped framework the prompt never names is
    dead (e.g. the original bare ``EU_AI_ACT`` alias). These tests pin the two
    enumerations equal so the drift fails the build instead of escaping it."""

    def test_prompt_framework_set_equals_artifact_map_keys(self) -> None:
        from model_project_constructor.agents.intake.anthropic_client import (
            GOVERNANCE_FRAMEWORKS,
        )
        from model_project_constructor.agents.website.governance_templates import (
            _FRAMEWORK_ARTIFACTS,
        )

        prompt_set = set(GOVERNANCE_FRAMEWORKS)
        map_keys = set(_FRAMEWORK_ARTIFACTS)
        prompt_only = prompt_set - map_keys
        map_only = map_keys - prompt_set
        assert prompt_set == map_keys, (
            "Regulatory-framework drift (Audit #39): "
            f"prompted-but-unmapped (scaffold nothing) = {sorted(prompt_only)}; "
            f"mapped-but-unprompted (dead) = {sorted(map_only)}. Reconcile "
            "anthropic_client.GOVERNANCE_FRAMEWORKS with "
            "governance_templates._FRAMEWORK_ARTIFACTS."
        )

    def test_every_prompted_framework_scaffolds_at_least_one_artifact(self) -> None:
        # Stronger than key-presence: each prompted framework must bind to a
        # NON-empty artifact list, so none maps to ``[]`` by accident.
        from model_project_constructor.agents.intake.anthropic_client import (
            GOVERNANCE_FRAMEWORKS,
        )
        from model_project_constructor.agents.website.governance_templates import (
            _FRAMEWORK_ARTIFACTS,
        )

        for framework in GOVERNANCE_FRAMEWORKS:
            assert _FRAMEWORK_ARTIFACTS.get(
                framework
            ), f"{framework} maps to no governance artifacts"


class TestVocabularyDriftGuards:
    """Audit #2 — the governance consumer dicts ``_TIER_SEVERITY`` and
    ``_CYCLE_CADENCE`` (``governance_templates.py``) re-list the ``RiskTier`` /
    ``CycleTime`` schema ``Literal`` members. Their lookups fall back silently:
    ``_TIER_SEVERITY.get(tier, 99)`` ranks an unknown tier LEAST severe, so an
    added critical tier would skip every tier-gated governance artifact — a
    silent compliance gap. An import-time guard ties each dict to
    ``get_args(<Literal>)`` so an added/renamed member fails the build loudly.
    The guard is the shared ``model_project_constructor._vocab_guard``
    ``assert_vocab_parity`` (the original local copy was consolidated there).
    These tests pin the live parity AND prove the guard raises on drift (so the
    parity pins are not vacuous behind the import-time assert)."""

    def test_tier_severity_matches_risk_tier_literal(self) -> None:
        from typing import get_args

        from model_project_constructor.agents.website.governance_templates import (
            _TIER_SEVERITY,
        )
        from model_project_constructor.schemas.v1.common import RiskTier

        assert set(_TIER_SEVERITY) == set(get_args(RiskTier))

    def test_cycle_cadence_matches_cycle_time_literal(self) -> None:
        from typing import get_args

        from model_project_constructor.agents.website.governance_templates import (
            _CYCLE_CADENCE,
        )
        from model_project_constructor.schemas.v1.common import CycleTime

        assert set(_CYCLE_CADENCE) == set(get_args(CycleTime))

    def test_guard_raises_on_missing_member(self) -> None:
        # The real guard function (the shared one the import-time guards
        # call), fed a member set MISSING a Literal value, must raise —
        # proving drift is caught, not silently tolerated.
        from model_project_constructor._vocab_guard import assert_vocab_parity
        from model_project_constructor.schemas.v1.common import RiskTier

        with pytest.raises(AssertionError, match="drifted"):
            assert_vocab_parity(
                {"tier_1_critical"}, RiskTier, name="_TEST", reconcile_hint="test"
            )

    def test_guard_raises_on_extra_member(self) -> None:
        from typing import get_args

        from model_project_constructor._vocab_guard import assert_vocab_parity
        from model_project_constructor.schemas.v1.common import CycleTime

        drifted = set(get_args(CycleTime)) | {"biweekly"}
        with pytest.raises(AssertionError, match="drifted"):
            assert_vocab_parity(drifted, CycleTime, name="_TEST", reconcile_hint="test")

    def test_guard_passes_on_exact_match(self) -> None:
        from typing import get_args

        from model_project_constructor._vocab_guard import assert_vocab_parity
        from model_project_constructor.schemas.v1.common import RiskTier

        # Exact parity returns None (no raise).
        assert (
            assert_vocab_parity(
                set(get_args(RiskTier)), RiskTier, name="_TEST", reconcile_hint="test"
            )
            is None
        )


# ---------------------------------------------------------------------------
# Phase C3b — generated-project CI portability (enterprise-host overrides)
# ---------------------------------------------------------------------------


class TestCIHostConfigDefaults:
    """No overrides -> byte-identical to the pre-C3b public-host output."""

    def test_gitlab_ci_default_is_unchanged(self) -> None:
        from model_project_constructor.agents.website.governance_templates import (
            render_gitlab_ci,
        )

        out = render_gitlab_ci()
        assert "image: python:3.11\n" in out
        assert "- pip install uv\n" in out
        assert "variables:" not in out

    def test_github_actions_ci_default_is_unchanged(self) -> None:
        from model_project_constructor.agents.website.governance_templates import (
            render_github_actions_ci,
        )

        out = render_github_actions_ci()
        assert out.count("- uses: actions/checkout@v4\n") == 3
        assert out.count("- uses: actions/setup-python@v5\n") == 3
        assert out.count("- run: pip install uv\n") == 3
        assert "env:" not in out

    def test_pre_commit_config_default_is_unchanged(self) -> None:
        from model_project_constructor.agents.website.governance_templates import (
            render_pre_commit_config,
        )

        out = render_pre_commit_config()
        assert "- repo: https://github.com/astral-sh/ruff-pre-commit\n" in out


class TestCIHostConfigOverrides:
    def test_gitlab_ci_base_image_override(self) -> None:
        from model_project_constructor.agents.website.governance_templates import (
            CIHostConfig,
            render_gitlab_ci,
        )

        out = render_gitlab_ci(
            ci_host_config=CIHostConfig(base_image="registry.enterprise.example/python:3.11")
        )
        assert "image: registry.enterprise.example/python:3.11\n" in out
        assert "python:3.11\n" not in out.replace(
            "registry.enterprise.example/python:3.11\n", ""
        )
        # Sibling fields (index_url unset here) must keep their defaults —
        # no variables: block, plain "pip install uv".
        assert "variables:" not in out
        assert "- pip install uv\n" in out

    def test_gitlab_ci_index_url_override(self) -> None:
        from model_project_constructor.agents.website.governance_templates import (
            CIHostConfig,
            render_gitlab_ci,
        )

        out = render_gitlab_ci(
            ci_host_config=CIHostConfig(index_url="https://pypi.enterprise.example/simple")
        )
        assert 'UV_INDEX_URL: "https://pypi.enterprise.example/simple"' in out
        assert (
            "pip install --index-url https://pypi.enterprise.example/simple uv"
            in out
        )
        # Sibling field (base_image unset here) must keep its default.
        assert "image: python:3.11\n" in out

    def test_github_actions_action_prefix_override(self) -> None:
        from model_project_constructor.agents.website.governance_templates import (
            CIHostConfig,
            render_github_actions_ci,
        )

        out = render_github_actions_ci(
            ci_host_config=CIHostConfig(action_prefix="enterprise-mirror")
        )
        assert out.count("- uses: enterprise-mirror/checkout@v4\n") == 3
        assert out.count("- uses: enterprise-mirror/setup-python@v5\n") == 3
        assert "actions/checkout@v4" not in out
        assert "actions/setup-python@v5" not in out
        # Sibling field (index_url unset here) must keep its default — no
        # env: block, plain "pip install uv".
        assert "env:" not in out
        assert out.count("- run: pip install uv\n") == 3

    def test_github_actions_index_url_override(self) -> None:
        from model_project_constructor.agents.website.governance_templates import (
            CIHostConfig,
            render_github_actions_ci,
        )

        out = render_github_actions_ci(
            ci_host_config=CIHostConfig(index_url="https://pypi.enterprise.example/simple")
        )
        assert 'UV_INDEX_URL: "https://pypi.enterprise.example/simple"' in out
        assert out.count("pip install --index-url") == 3
        # Sibling field (action_prefix unset here) must keep its default.
        assert out.count("- uses: actions/checkout@v4\n") == 3

    def test_pre_commit_repo_override(self) -> None:
        from model_project_constructor.agents.website.governance_templates import (
            CIHostConfig,
            render_pre_commit_config,
        )

        out = render_pre_commit_config(
            ci_host_config=CIHostConfig(
                pre_commit_repo="https://git.enterprise.example/mirrors/ruff-pre-commit"
            )
        )
        assert (
            "- repo: https://git.enterprise.example/mirrors/ruff-pre-commit\n" in out
        )
        assert "github.com" not in out


class TestCIHostConfigIntegration:
    """End-to-end: WebsiteAgent(ci_host_config=...) -> emitted file content."""

    @pytest.mark.parametrize("ci_platform", ["gitlab", "github"])
    def test_agent_threads_ci_host_config_into_emitted_ci_file(
        self,
        tier3_intake: IntakeReport,
        data_report: DataReport,
        ci_platform: str,
    ) -> None:
        from model_project_constructor.agents.website.governance_templates import (
            CIHostConfig,
        )

        cfg = CIHostConfig(
            base_image="registry.enterprise.example/python:3.11",
            index_url="https://pypi.enterprise.example/simple",
            action_prefix="enterprise-mirror",
            pre_commit_repo="https://git.enterprise.example/mirrors/ruff-pre-commit",
        )
        result, client = _run_agent(
            tier3_intake, data_report, ci_platform=ci_platform, ci_host_config=cfg
        )
        stored = client.get_files(result.project_id)

        ci_path = ".gitlab-ci.yml" if ci_platform == "gitlab" else ".github/workflows/ci.yml"
        ci_body = stored[ci_path]
        assert "enterprise.example" in ci_body
        assert "docker.io" not in ci_body
        assert "python:3.11" not in ci_body.replace(
            "registry.enterprise.example/python:3.11", ""
        )
        if ci_platform == "github":
            assert "enterprise-mirror/checkout@v4" in ci_body
            assert "github.com/" not in ci_body

        pre_commit_body = stored[".pre-commit-config.yaml"]
        assert "git.enterprise.example" in pre_commit_body
        assert "github.com" not in pre_commit_body

    def test_agent_default_ci_host_config_is_unchanged(
        self,
        tier3_intake: IntakeReport,
        data_report: DataReport,
    ) -> None:
        """No ``ci_host_config`` passed to ``WebsiteAgent`` -> public defaults."""
        result, client = _run_agent(tier3_intake, data_report, ci_platform="gitlab")
        stored = client.get_files(result.project_id)
        assert "image: python:3.11" in stored[".gitlab-ci.yml"]
        assert (
            "https://github.com/astral-sh/ruff-pre-commit"
            in stored[".pre-commit-config.yaml"]
        )
