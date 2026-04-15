"""Unit tests for Website Agent repo schemas (§5.4)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from model_project_constructor.schemas.v1 import (
    GovernanceManifest,
    RepoProjectResult,
    RepoTarget,
)
from tests.schemas.fixtures import (
    make_governance_manifest,
    make_repo_project_result,
    make_repo_target,
)


class TestRepoTarget:
    def test_happy_path(self) -> None:
        t = make_repo_target()
        assert t.visibility == "private"
        assert t.schema_version == "1.0.0"

    @pytest.mark.parametrize("visibility", ["private", "internal", "public"])
    def test_all_visibilities_accepted(self, visibility: str) -> None:
        t = make_repo_target(visibility=visibility)
        assert t.visibility == visibility

    def test_invalid_visibility_rejected(self) -> None:
        with pytest.raises(ValidationError):
            make_repo_target(visibility="top_secret")

    def test_serialization_round_trip(self) -> None:
        original = make_repo_target(visibility="internal")
        restored = RepoTarget.model_validate_json(original.model_dump_json())
        assert restored == original


class TestGovernanceManifest:
    def test_happy_path(self) -> None:
        m = make_governance_manifest()
        assert m.risk_tier == "tier_3_moderate"
        assert "SR_11_7" in m.regulatory_mapping

    def test_regulatory_mapping_defaults_to_empty_dict(self) -> None:
        m = make_governance_manifest(regulatory_mapping={})
        assert m.regulatory_mapping == {}

    def test_each_instance_gets_its_own_mapping_dict(self) -> None:
        """Regression guard against Field(default_factory=dict) misuse — if
        default_factory were not in place, two instances would share a dict."""
        a = GovernanceManifest(
            model_registry_entry={},
            artifacts_created=[],
            risk_tier="tier_4_low",
            cycle_time="strategic",
        )
        b = GovernanceManifest(
            model_registry_entry={},
            artifacts_created=[],
            risk_tier="tier_4_low",
            cycle_time="strategic",
        )
        a.regulatory_mapping["SR_11_7"] = ["governance/model_card.md"]
        assert b.regulatory_mapping == {}


class TestRepoProjectResult:
    def test_happy_path(self) -> None:
        r = make_repo_project_result()
        assert r.status == "COMPLETE"
        assert r.failure_reason is None

    @pytest.mark.parametrize("status", ["COMPLETE", "PARTIAL", "FAILED"])
    def test_all_statuses_accepted(self, status: str) -> None:
        r = make_repo_project_result(status=status)
        assert r.status == status

    def test_failure_reason_for_failed_status(self) -> None:
        r = make_repo_project_result(status="FAILED", failure_reason="host 401")
        assert r.failure_reason == "host 401"

    def test_serialization_round_trip(self) -> None:
        original = make_repo_project_result()
        restored = RepoProjectResult.model_validate_json(original.model_dump_json())
        assert restored == original
