"""Website Agent facade.

Thin wrapper around :func:`build_website_graph` that validates Pydantic
inputs, constructs the state dict, drives the graph to completion, and
returns a validated :class:`RepoProjectResult`.
"""

from __future__ import annotations

from typing import Any, Literal

from model_project_constructor.agents.website.graph import build_website_graph
from model_project_constructor.agents.website.nodes import build_repo_project_result
from model_project_constructor.agents.website.protocol import RepoClient
from model_project_constructor.agents.website.state import initial_state
from model_project_constructor.schemas.v1.data import DataReport
from model_project_constructor.schemas.v1.intake import IntakeReport
from model_project_constructor.schemas.v1.repo import (
    RepoProjectResult,
    RepoTarget,
)


class WebsiteAgent:
    """High-level runner for the website graph.

    Usage::

        agent = WebsiteAgent(client)
        result = agent.run(intake_report, data_report, repo_target)
        assert result.status == "COMPLETE"
    """

    def __init__(
        self,
        client: RepoClient,
        *,
        ci_platform: Literal["gitlab", "github"] = "gitlab",
    ):
        self.client = client
        self.ci_platform: Literal["gitlab", "github"] = ci_platform
        self.graph = build_website_graph(client)

    def run(
        self,
        intake_report: IntakeReport,
        data_report: DataReport,
        repo_target: RepoTarget,
    ) -> RepoProjectResult:
        """Drive the graph end-to-end and return a validated result.

        Expects both reports to have ``status == "COMPLETE"``. If either
        predecessor is incomplete, the website agent still runs — it's
        the orchestrator's job per §12 to halt the pipeline on upstream
        failures. We surface the precondition as a ``PARTIAL`` result
        with a clear ``failure_reason`` instead of raising.
        """

        if intake_report.status != "COMPLETE":
            return _precondition_result(
                target=repo_target,
                reason=f"intake_status={intake_report.status}",
            )
        if data_report.status != "COMPLETE":
            return _precondition_result(
                target=repo_target,
                reason=f"data_status={data_report.status}",
            )

        thread_id = f"website::{intake_report.session_id}"
        config: dict[str, Any] = {"configurable": {"thread_id": thread_id}}
        state = initial_state(
            intake_report=intake_report.model_dump(mode="json"),
            data_report=data_report.model_dump(mode="json"),
            repo_target=repo_target.model_dump(mode="json"),
            ci_platform=self.ci_platform,
        )

        self.graph.invoke(state, config=config)
        final = self.graph.get_state(config).values
        return build_repo_project_result(final)


def _precondition_result(
    *,
    target: RepoTarget,
    reason: str,
) -> RepoProjectResult:
    from model_project_constructor.schemas.v1.repo import GovernanceManifest

    manifest = GovernanceManifest(
        model_registry_entry={},
        artifacts_created=[],
        risk_tier="tier_4_low",
        cycle_time="tactical",
        regulatory_mapping={},
    )
    return RepoProjectResult(
        status="FAILED",
        project_url="",
        project_id="",
        initial_commit_sha="",
        files_created=[],
        governance_manifest=manifest,
        failure_reason=f"precondition_failed: {reason}",
    )
