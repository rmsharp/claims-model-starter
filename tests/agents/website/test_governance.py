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
from typing import Any

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
    intake: IntakeReport, data: DataReport
) -> tuple[Any, FakeRepoClient]:
    client = FakeRepoClient()
    target = RepoTarget(
        host_url="https://gitlab.example.com",
        namespace="data-science/model-drafts",
        project_name_hint=intake.session_id,
        visibility="private",
    )
    result = WebsiteAgent(client).run(intake, data, target)
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
        assert {"SR_11_7", "NAIC_AIS", "EU_AI_ACT_ART_9", "ASOP_56"} <= frameworks

        # EU_AI_ACT_ART_9 binds to eu_ai_act_compliance.md (committed at tier 1)
        assert (
            "governance/eu_ai_act_compliance.md"
            in manifest.regulatory_mapping["EU_AI_ACT_ART_9"]
        )
        # SR_11_7 binds to three_pillar_validation.md (tier 3+)
        assert (
            "governance/three_pillar_validation.md"
            in manifest.regulatory_mapping["SR_11_7"]
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
        assert "SR_11_7" in entry["regulatory_frameworks"]


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

        # Tier 2 fixture declares exactly SR_11_7 + ASOP_56
        assert set(mapping.keys()) == {"SR_11_7", "ASOP_56"}
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


# ---------------------------------------------------------------------------
# build_governance_files unit tests (no LangGraph)
# ---------------------------------------------------------------------------


class TestBuildGovernanceFilesUnit:
    def test_tier4_emits_only_always_artifacts(
        self, data_report: DataReport
    ) -> None:
        """A tier 4 low model gets none of the tiered artifacts — only
        'always' + consumer/fairness conditionals (both off here)."""

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
        files = build_governance_files(
            intake=intake,
            data=data_report.model_dump(mode="json"),
            project_name="p",
            project_slug="p",
        )

        assert "governance/model_registry.json" in files
        assert "governance/model_card.md" in files
        assert "governance/change_log.md" in files
        assert ".gitlab-ci.yml" in files
        assert ".pre-commit-config.yaml" in files
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
            frameworks=["SR_11_7", "UNKNOWN_FRAMEWORK"],
            emitted_paths={"governance/model_card.md"},
        )
        assert mapping["SR_11_7"] == ["governance/model_card.md"]
        # Unknown framework appears with an empty list so it's visible
        assert mapping["UNKNOWN_FRAMEWORK"] == []

    def test_is_governance_artifact_classification(self) -> None:
        from model_project_constructor.agents.website.governance_templates import (
            is_governance_artifact,
        )

        assert is_governance_artifact("governance/model_card.md")
        assert is_governance_artifact("data/datasheet_foo.md")
        assert is_governance_artifact(".gitlab-ci.yml")
        assert is_governance_artifact(".pre-commit-config.yaml")
        assert is_governance_artifact("analysis/fairness_audit.qmd")
        assert is_governance_artifact("src/proj/fairness/audit.py")
        assert is_governance_artifact("tests/test_fairness.py")

        # Non-governance paths
        assert not is_governance_artifact("README.md")
        assert not is_governance_artifact("src/proj/models.py")
        assert not is_governance_artifact("analysis/03_eda.qmd")
        assert not is_governance_artifact("tests/test_features.py")
