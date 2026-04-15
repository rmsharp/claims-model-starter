"""Website Agent graph nodes.

Phase 4A ships three nodes: ``CREATE_PROJECT``, ``SCAFFOLD_BASE``, and
``INITIAL_COMMITS``. Sub-phase 4B will insert ``SCAFFOLD_GOVERNANCE``,
``SCAFFOLD_ANALYSIS``, and ``SCAFFOLD_TESTS`` between ``SCAFFOLD_BASE``
and ``INITIAL_COMMITS``; 4A's accumulator pattern
(``WebsiteState.files_pending``) is designed so those additions only
need to merge more entries into the dict before the flush.

Unlike the intake agent, none of these nodes call ``interrupt()`` — the
website agent is headless and deterministic. The same split of
"LLM/side-effect-heavy" vs "state-update" still applies: each node is a
pure function over state + an injected ``GitLabClient``.
"""

from __future__ import annotations

from typing import Any

from model_project_constructor.agents.website.protocol import (
    GitLabClient,
    GitLabClientError,
    ProjectNameConflictError,
)
from model_project_constructor.agents.website.state import (
    MAX_NAME_CONFLICT_ATTEMPTS,
    WebsiteState,
)
from model_project_constructor.agents.website.templates import (
    build_base_files,
    derive_project_name,
    derive_project_slug,
)
from model_project_constructor.schemas.v1.gitlab import (
    GitLabProjectResult,
    GovernanceManifest,
)


def _candidate_names(base: str) -> list[str]:
    """Return up to ``MAX_NAME_CONFLICT_ATTEMPTS`` candidate project names.

    Starts with the base name, then ``-v2``, ``-v3``, etc. Per
    architecture-plan §4.3 failure modes table (row "GitLab project name
    conflict"): append suffix up to 5 attempts total.
    """

    candidates = [base]
    for i in range(2, MAX_NAME_CONFLICT_ATTEMPTS + 1):
        candidates.append(f"{base}-v{i}")
    return candidates


def make_nodes(client: GitLabClient) -> dict[str, Any]:
    """Build the callable nodes bound to a given GitLab client."""

    def create_project(state: WebsiteState) -> dict[str, Any]:
        target = state["gitlab_target"]
        hint = str(target.get("project_name_hint", "model-project"))
        base_name = derive_project_name(hint)

        last_error: str | None = None
        for candidate in _candidate_names(base_name):
            try:
                info = client.create_project(
                    group_path=str(target["group_path"]),
                    name=candidate,
                    visibility=str(target.get("visibility", "private")),
                )
            except ProjectNameConflictError as exc:
                last_error = str(exc)
                continue
            except GitLabClientError as exc:
                return {
                    "status": "FAILED",
                    "failure_reason": f"gitlab_error: {exc}",
                }

            return {
                "project_name": candidate,
                "project_slug": derive_project_slug(candidate),
                "project_id": info.id,
                "project_url": info.url,
                "default_branch": info.default_branch,
                "status": "PARTIAL",
            }

        return {
            "status": "FAILED",
            "failure_reason": (
                f"project_name_conflict: exhausted "
                f"{MAX_NAME_CONFLICT_ATTEMPTS} suffixes "
                f"(base={base_name!r}, last={last_error})"
            ),
        }

    def scaffold_base(state: WebsiteState) -> dict[str, Any]:
        files = build_base_files(
            intake=state["intake_report"],
            data=state["data_report"],
            project_name=state["project_name"],
            project_slug=state["project_slug"],
        )
        pending = dict(state.get("files_pending", {}))
        pending.update(files)
        return {"files_pending": pending}

    def initial_commits(state: WebsiteState) -> dict[str, Any]:
        pending = dict(state.get("files_pending", {}))
        if not pending:
            return {
                "status": "FAILED",
                "failure_reason": "no_files_scaffolded",
            }

        try:
            commit = client.commit_files(
                project_id=state["project_id"],
                branch=state.get("default_branch", "main"),
                files=pending,
                message="feat: scaffold base project (Phase 4A)",
            )
        except GitLabClientError as exc:
            return {
                "status": "FAILED",
                "failure_reason": f"commit_failed: {exc}",
            }

        return {
            "initial_commit_sha": commit.sha,
            "files_created": sorted(commit.files_committed),
            "status": "COMPLETE",
            "files_pending": {},
        }

    return {
        "create_project": create_project,
        "scaffold_base": scaffold_base,
        "initial_commits": initial_commits,
    }


def route_after_create(state: WebsiteState) -> str:
    if state.get("status") == "FAILED":
        return "end"
    return "scaffold_base"


def build_gitlab_project_result(state: WebsiteState) -> GitLabProjectResult:
    """Assemble a ``GitLabProjectResult`` from the final graph state.

    Phase 4A returns an *empty* governance manifest — the tier-based
    artifacts land in Phase 4B's ``SCAFFOLD_GOVERNANCE`` node. The shape
    is already wired here so downstream consumers don't need to special-
    case the 4A output.
    """

    intake = state.get("intake_report") or {}
    governance_meta = intake.get("governance") or {}
    manifest = GovernanceManifest(
        model_registry_entry={},
        artifacts_created=[],
        risk_tier=governance_meta.get("risk_tier", "tier_4_low"),
        cycle_time=governance_meta.get("cycle_time", "tactical"),
        regulatory_mapping={},
    )
    return GitLabProjectResult(
        status=state.get("status", "FAILED"),  # type: ignore[arg-type]
        project_url=state.get("project_url", ""),
        project_id=state.get("project_id", 0),
        initial_commit_sha=state.get("initial_commit_sha", ""),
        files_created=list(state.get("files_created") or []),
        governance_manifest=manifest,
        failure_reason=state.get("failure_reason"),
    )
