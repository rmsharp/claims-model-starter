"""Website Agent state.

The website agent is a LangGraph ``StateGraph`` over a plain ``TypedDict``.
Nodes return deltas only; ``files_pending`` is accumulated across
``SCAFFOLD_*`` nodes and flushed by ``INITIAL_COMMITS``.

All report fields are stored as ``dict`` (from ``model_dump(mode="json")``)
so the state is JSON-serializable for any checkpointer the orchestrator
cares to plug in.

Architecture plan: §4.3, §5.4, §10, §11.
"""

from __future__ import annotations

from typing import Any, TypedDict


class WebsiteState(TypedDict, total=False):
    """State passed between website graph nodes."""

    # Inputs (dict-shaped copies of the Pydantic reports / target)
    intake_report: dict[str, Any]
    data_report: dict[str, Any]
    gitlab_target: dict[str, Any]

    # Derived project naming
    project_name: str      # final name after conflict resolution
    project_slug: str      # python-package-safe (underscores, lowercase)

    # CREATE_PROJECT outputs
    project_id: int
    project_url: str
    default_branch: str

    # SCAFFOLD_BASE accumulator — INITIAL_COMMITS flushes this to the client.
    files_pending: dict[str, str]

    # INITIAL_COMMITS outputs
    initial_commit_sha: str
    files_created: list[str]

    # Terminal
    status: str            # "COMPLETE" | "PARTIAL" | "FAILED"
    failure_reason: str | None


MAX_NAME_CONFLICT_ATTEMPTS = 5


def initial_state(
    *,
    intake_report: dict[str, Any],
    data_report: dict[str, Any],
    gitlab_target: dict[str, Any],
) -> WebsiteState:
    return WebsiteState(
        intake_report=intake_report,
        data_report=data_report,
        gitlab_target=gitlab_target,
        files_pending={},
        files_created=[],
        status="PARTIAL",
        failure_reason=None,
    )
