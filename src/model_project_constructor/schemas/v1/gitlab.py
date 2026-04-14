"""Website Agent GitLab target and result schemas (§5.4 of architecture-plan.md)."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from model_project_constructor.schemas.v1.common import CycleTime, RiskTier, StrictBase


class GitLabTarget(StrictBase):
    schema_version: Literal["1.0.0"] = "1.0.0"
    gitlab_url: str
    group_path: str
    project_name_hint: str
    visibility: Literal["private", "internal", "public"] = "private"


class GovernanceManifest(StrictBase):
    model_registry_entry: dict[str, Any]
    artifacts_created: list[str]
    risk_tier: RiskTier
    cycle_time: CycleTime
    regulatory_mapping: dict[str, list[str]] = Field(default_factory=dict)


class GitLabProjectResult(StrictBase):
    schema_version: Literal["1.0.0"] = "1.0.0"
    status: Literal["COMPLETE", "PARTIAL", "FAILED"]
    project_url: str
    project_id: int
    initial_commit_sha: str
    files_created: list[str]
    governance_manifest: GovernanceManifest
    failure_reason: str | None = None
