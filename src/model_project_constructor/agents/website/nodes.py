"""Website Agent graph nodes.

Phase 4A shipped three nodes (``CREATE_PROJECT`` → ``SCAFFOLD_BASE`` →
``INITIAL_COMMITS``). Phase 4B layers in:

- ``SCAFFOLD_GOVERNANCE`` — governance artifacts per §8.2 (tier-gated)
- ``SCAFFOLD_ANALYSIS`` — governance-driven analysis scaffolds (fairness)
- ``SCAFFOLD_TESTS`` — governance-driven test scaffolds (fairness)
- A ``RETRY_BACKOFF`` self-loop off ``INITIAL_COMMITS`` for transient
  ``RepoClientError`` (HTTP 401/429/5xx), 3 attempts max with
  exponential delay.

All scaffold nodes merge into ``state["files_pending"]``; none replace it.
``INITIAL_COMMITS`` is the single flush point, so retrying it safely
re-delivers the whole pending dict in one call.

None of these nodes call ``interrupt()`` — the website agent is headless.
Each node is a pure function over state + the injected ``RepoClient``
(plus an injectable ``sleep`` function for test-time determinism on the
retry path).
"""

from __future__ import annotations

import time
from typing import Any, Callable

from model_project_constructor.agents.website.governance_templates import (
    build_analysis_files,
    build_governance_files,
    build_model_registry_entry,
    build_regulatory_mapping,
    build_test_files,
    is_governance_artifact,
)
from model_project_constructor.agents.website.protocol import (
    RepoClient,
    RepoClientError,
    RepoNameConflictError,
)
from model_project_constructor.agents.website.state import (
    MAX_COMMIT_ATTEMPTS,
    MAX_NAME_CONFLICT_ATTEMPTS,
    RETRY_BASE_DELAY_SECONDS,
    WebsiteState,
)
from model_project_constructor.agents.website.templates import (
    build_base_files,
    derive_project_name,
    derive_project_slug,
)
from model_project_constructor.schemas.v1.repo import (
    GovernanceManifest,
    RepoProjectResult,
)


SleepFunc = Callable[[float], None]


def _default_sleep(seconds: float) -> None:
    time.sleep(seconds)


def _candidate_names(base: str) -> list[str]:
    """Return up to ``MAX_NAME_CONFLICT_ATTEMPTS`` candidate project names.

    Starts with the base name, then ``-v2``, ``-v3``, etc. Per
    architecture-plan §4.3 failure modes table (row "repo project name
    conflict"): append suffix up to 5 attempts total.
    """

    candidates = [base]
    for i in range(2, MAX_NAME_CONFLICT_ATTEMPTS + 1):
        candidates.append(f"{base}-v{i}")
    return candidates


def make_nodes(
    client: RepoClient,
    *,
    sleep: SleepFunc = _default_sleep,
) -> dict[str, Any]:
    """Build the callable nodes bound to a given repo client.

    ``sleep`` is injectable so tests can exercise ``retry_backoff``
    without real wall-clock delay.
    """

    def create_project(state: WebsiteState) -> dict[str, Any]:
        target = state["repo_target"]
        hint = str(target.get("project_name_hint", "model-project"))
        base_name = derive_project_name(hint)

        last_error: str | None = None
        for candidate in _candidate_names(base_name):
            try:
                info = client.create_project(
                    namespace=str(target["namespace"]),
                    name=candidate,
                    visibility=str(target.get("visibility", "private")),
                )
            except RepoNameConflictError as exc:
                last_error = str(exc)
                continue
            except RepoClientError as exc:
                return {
                    "status": "FAILED",
                    "failure_reason": f"repo_error: {exc}",
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

    def scaffold_governance(state: WebsiteState) -> dict[str, Any]:
        files = build_governance_files(
            intake=state["intake_report"],
            data=state["data_report"],
            project_name=state["project_name"],
            project_slug=state["project_slug"],
            ci_platform=state.get("ci_platform", "gitlab"),
        )
        pending = dict(state.get("files_pending", {}))
        pending.update(files)
        governance_paths = sorted(
            set(state.get("governance_paths", []) or []) | set(files.keys())
        )
        return {
            "files_pending": pending,
            "governance_paths": governance_paths,
        }

    def scaffold_analysis(state: WebsiteState) -> dict[str, Any]:
        files = build_analysis_files(
            intake=state["intake_report"],
            project_slug=state["project_slug"],
        )
        if not files:
            return {}
        pending = dict(state.get("files_pending", {}))
        pending.update(files)
        governance_paths = sorted(
            set(state.get("governance_paths", []) or []) | set(files.keys())
        )
        return {
            "files_pending": pending,
            "governance_paths": governance_paths,
        }

    def scaffold_tests(state: WebsiteState) -> dict[str, Any]:
        files = build_test_files(
            intake=state["intake_report"],
            project_slug=state["project_slug"],
        )
        if not files:
            return {}
        pending = dict(state.get("files_pending", {}))
        pending.update(files)
        governance_paths = sorted(
            set(state.get("governance_paths", []) or []) | set(files.keys())
        )
        return {
            "files_pending": pending,
            "governance_paths": governance_paths,
        }

    def initial_commits(state: WebsiteState) -> dict[str, Any]:
        attempts = int(state.get("commit_attempts", 0)) + 1
        pending = dict(state.get("files_pending", {}))
        if not pending:
            return {
                "status": "FAILED",
                "failure_reason": "no_files_scaffolded",
                "commit_attempts": attempts,
            }

        try:
            commit = client.commit_files(
                project_id=state["project_id"],
                branch=state.get("default_branch", "main"),
                files=pending,
                message="feat: scaffold model project (intake + data + governance)",
            )
        except RepoClientError as exc:
            if attempts < MAX_COMMIT_ATTEMPTS:
                # Transient — route through RETRY_BACKOFF. The loop will
                # re-enter this node with the same pending dict.
                return {
                    "status": "RETRYING",
                    "failure_reason": f"commit_failed: {exc}",
                    "commit_attempts": attempts,
                }
            return {
                "status": "FAILED",
                "failure_reason": (
                    f"repo_error_retry_exhausted: {exc} "
                    f"(after {attempts} attempts)"
                ),
                "commit_attempts": attempts,
            }

        return {
            "initial_commit_sha": commit.sha,
            "files_created": sorted(commit.files_committed),
            "status": "COMPLETE",
            "files_pending": {},
            "commit_attempts": attempts,
            "failure_reason": None,
        }

    def retry_backoff(state: WebsiteState) -> dict[str, Any]:
        """Sleep between failed ``initial_commits`` attempts.

        Delay doubles each attempt (1s, 2s, 4s). Uses the injected
        ``sleep`` so tests can patch it out entirely.
        """

        attempts = int(state.get("commit_attempts", 1))
        delay = RETRY_BASE_DELAY_SECONDS * (2 ** max(attempts - 1, 0))
        sleep(delay)
        # Reset status to PARTIAL so re-entering initial_commits is a
        # fresh attempt rather than a retry-on-retry.
        return {"status": "PARTIAL"}

    return {
        "create_project": create_project,
        "scaffold_base": scaffold_base,
        "scaffold_governance": scaffold_governance,
        "scaffold_analysis": scaffold_analysis,
        "scaffold_tests": scaffold_tests,
        "initial_commits": initial_commits,
        "retry_backoff": retry_backoff,
    }


def route_after_create(state: WebsiteState) -> str:
    if state.get("status") == "FAILED":
        return "end"
    return "scaffold_base"


def route_after_commit(state: WebsiteState) -> str:
    """Route off ``initial_commits`` based on transient vs terminal failure.

    - ``RETRYING`` → ``retry_backoff`` (sleeps and re-enters)
    - ``COMPLETE`` or ``FAILED`` → ``end``
    """

    if state.get("status") == "RETRYING":
        return "retry_backoff"
    return "end"


def build_repo_project_result(state: WebsiteState) -> RepoProjectResult:
    """Assemble a ``RepoProjectResult`` from the final graph state.

    Phase 4B populates the governance manifest:

    - ``artifacts_created`` is the intersection of what was committed
      with :func:`is_governance_artifact` (so base files are filtered out).
    - ``regulatory_mapping`` is computed from
      ``intake.governance.regulatory_frameworks`` against the emitted
      governance artifacts.
    - ``model_registry_entry`` mirrors what was written to
      ``governance/model_registry.json``.
    """

    intake = state.get("intake_report") or {}
    governance_meta = intake.get("governance") or {}
    project_name = str(state.get("project_name", ""))
    project_slug = str(state.get("project_slug", ""))

    files_created = list(state.get("files_created") or [])
    governance_artifacts = sorted(
        p for p in files_created if is_governance_artifact(p)
    )

    # Compute regulatory mapping against ONLY the governance artifacts
    # that actually made it into a commit. A failed commit → empty set.
    regulatory_mapping = build_regulatory_mapping(
        frameworks=list(governance_meta.get("regulatory_frameworks") or []),
        emitted_paths=set(governance_artifacts),
    )

    # Only build a registry entry when the project was actually named —
    # otherwise we have no slug to root it on.
    registry_entry: dict[str, Any] = {}
    if project_name and project_slug:
        registry_entry = build_model_registry_entry(
            intake=intake,
            project_name=project_name,
            project_slug=project_slug,
        )

    manifest = GovernanceManifest(
        model_registry_entry=registry_entry,
        artifacts_created=governance_artifacts,
        risk_tier=governance_meta.get("risk_tier", "tier_4_low"),
        cycle_time=governance_meta.get("cycle_time", "tactical"),
        regulatory_mapping=regulatory_mapping,
    )
    return RepoProjectResult(
        status=state.get("status", "FAILED"),  # type: ignore[arg-type]
        project_url=state.get("project_url", ""),
        project_id=state.get("project_id", ""),
        initial_commit_sha=state.get("initial_commit_sha", ""),
        files_created=files_created,
        governance_manifest=manifest,
        failure_reason=state.get("failure_reason"),
    )
