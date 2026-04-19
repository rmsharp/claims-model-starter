"""Sequential pipeline driver (architecture-plan §12 + §14 Phase 5).

``run_pipeline`` is the single public entry point. It takes a
:class:`PipelineConfig` and three agent runners (callables — not concrete
agent classes — so tests can inject stubs without instantiating LLM
clients or databases), drives the Intake → Data → Website sequence, and
halts on the first ``status != "COMPLETE"``.

Every inter-agent handoff is wrapped in a :class:`HandoffEnvelope` and
persisted via :class:`CheckpointStore`. The orchestrator itself is the
envelope's ``source_agent`` when it is forwarding one agent's output to
the next; only the Website Agent's result envelope has
``source_agent="website"`` because that handoff terminates the run (it
comes back to the orchestrator).

Per §12 the orchestrator does not retry failed agents — a non-COMPLETE
status halts the run and the caller inspects ``PipelineResult`` to
decide whether to re-run with a fresh ``run_id`` or investigate.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal, cast

from model_project_constructor.orchestrator.adapters import (
    intake_report_to_data_request,
)
from model_project_constructor.orchestrator.checkpoints import CheckpointStore
from model_project_constructor.schemas.envelope import HandoffEnvelope
from model_project_constructor.schemas.v1.data import DataReport, DataRequest
from model_project_constructor.schemas.v1.intake import IntakeReport
from model_project_constructor.schemas.v1.repo import (
    RepoProjectResult,
    RepoTarget,
)

IntakeRunner = Callable[[], IntakeReport]
DataRunner = Callable[[DataRequest], DataReport]
WebsiteRunner = Callable[[IntakeReport, DataReport, RepoTarget], RepoProjectResult]

PipelineStatus = Literal[
    "COMPLETE",
    "FAILED_AT_INTAKE",
    "FAILED_AT_DATA",
    "FAILED_AT_WEBSITE",
]

ResumePoint = Literal[
    "intake",
    "intake_to_data_adapter",
    "data",
    "website",
    "already_complete",
]


class ResumeInconsistent(RuntimeError):
    """Raised when a checkpoint dir has a successor envelope without its predecessor.

    Example: a ``DataReport.json`` exists under the run's checkpoint
    directory but ``DataRequest.json`` does not. The resume logic refuses
    to guess the missing predecessor and surfaces this exception so the
    CLI layer can prompt the operator to investigate (the dir was likely
    mutated by hand). See ``docs/planning/resume-from-checkpoint-plan.md``
    §5 for the full truth table.
    """


def determine_resume_point(store: CheckpointStore, run_id: str) -> ResumePoint:
    """Inspect the on-disk envelopes for ``run_id`` and return the first
    stage that must be re-executed.

    Pure function — no side effects beyond reading the checkpoint dir.
    Does NOT consult ``RepoTarget`` (``T`` in the truth table): per the
    plan §6.4, the operator-supplied ``config.repo_target`` always wins
    on resume, so a saved ``RepoTarget`` envelope is not load-bearing for
    the resume-point decision.

    See ``docs/planning/resume-from-checkpoint-plan.md`` §5 for the
    truth table this function implements. Raises
    :class:`ResumeInconsistent` for rows marked INVALID (a successor
    envelope without its predecessor).
    """

    intake_present = store.has(run_id, "IntakeReport")
    request_present = store.has(run_id, "DataRequest")
    report_present = store.has(run_id, "DataReport")
    result_present = store.has_result(run_id, "RepoProjectResult")

    if result_present and not report_present:
        raise ResumeInconsistent(
            f"Run {run_id!r}: RepoProjectResult exists but DataReport is missing."
        )
    if report_present and not request_present:
        raise ResumeInconsistent(
            f"Run {run_id!r}: DataReport exists but DataRequest is missing."
        )
    if (request_present or report_present) and not intake_present:
        raise ResumeInconsistent(
            f"Run {run_id!r}: DataRequest/DataReport exist but IntakeReport is missing."
        )

    if result_present:
        return "already_complete"
    if report_present:
        return "website"
    if request_present:
        return "data"
    if intake_present:
        return "intake_to_data_adapter"
    return "intake"


@dataclass
class PipelineConfig:
    """Static configuration for a single pipeline run.

    ``repo_target`` fully describes the downstream host (GitLab or GitHub)
    via its ``host_url``; the ``ci_platform`` kwarg on ``WebsiteAgent`` is
    orthogonal to this config and is captured by whoever constructs the
    ``website_runner`` closure passed to :func:`run_pipeline`.
    """

    run_id: str
    repo_target: RepoTarget
    checkpoint_dir: Path
    correlation_id: str = field(default="")
    resume_from: ResumePoint | None = None

    def __post_init__(self) -> None:
        if not self.correlation_id:
            self.correlation_id = self.run_id


@dataclass
class PipelineResult:
    """Terminal state of a pipeline run.

    ``status`` follows §12's vocabulary. On the happy path all three
    report fields are populated; on failure, the reports produced before
    the halt are retained so the operator can inspect partial state.
    """

    run_id: str
    status: PipelineStatus
    intake_report: IntakeReport | None = None
    data_request: DataRequest | None = None
    data_report: DataReport | None = None
    project_result: RepoProjectResult | None = None
    failure_reason: str | None = None
    resume_point: ResumePoint | None = None

    @property
    def project_url(self) -> str | None:
        if self.project_result is None:
            return None
        return self.project_result.project_url or None


def run_pipeline(
    config: PipelineConfig,
    *,
    intake_runner: IntakeRunner,
    data_runner: DataRunner,
    website_runner: WebsiteRunner,
    store: CheckpointStore | None = None,
) -> PipelineResult:
    """Drive the Intake → Data → Website sequence per §12.

    Agent runners are callables so that callers retain full control over
    how each agent is constructed (LLM clients, DB handles, ``RepoClient``
    selection, ``ci_platform``). Production code wraps the real agents in
    small closures; tests inject stubs. This keeps the orchestrator free
    of import-time dependencies on heavy agent wiring.
    """

    checkpoint_store = store or CheckpointStore(config.checkpoint_dir)
    resume = config.resume_from

    if resume == "already_complete":
        raise ValueError(
            f"Run {config.run_id!r}: already_complete — nothing to resume."
        )

    # Intake stage — execute unless resume says a later stage is the
    # re-execution point. When loaded, halt logic does not fire (the
    # saved envelope is treated as trusted predecessor output; see
    # resume-from-checkpoint-plan.md §11 risk #5).
    if resume is None or resume == "intake":
        intake_report = intake_runner()
        checkpoint_store.save(
            _envelope(
                run_id=config.run_id,
                correlation_id=config.correlation_id,
                source="orchestrator",
                target="data",
                payload_type="IntakeReport",
                payload=intake_report.model_dump(mode="json"),
            )
        )
        if intake_report.status != "COMPLETE":
            return PipelineResult(
                run_id=config.run_id,
                status="FAILED_AT_INTAKE",
                intake_report=intake_report,
                failure_reason=(
                    f"intake_status={intake_report.status}; "
                    f"missing_fields={intake_report.missing_fields}"
                ),
                resume_point=resume,
            )
    else:
        intake_report = cast(
            IntakeReport,
            checkpoint_store.load_payload(config.run_id, "IntakeReport"),
        )

    # Adapter stage — deterministic pure code. On resume from "data" or
    # later, load the saved DataRequest instead of re-deriving (§6.3:
    # the envelope on disk is ground truth for what the data agent saw).
    if resume in (None, "intake", "intake_to_data_adapter"):
        data_request = intake_report_to_data_request(intake_report, config.run_id)
        checkpoint_store.save(
            _envelope(
                run_id=config.run_id,
                correlation_id=config.correlation_id,
                source="orchestrator",
                target="data",
                payload_type="DataRequest",
                payload=data_request.model_dump(mode="json"),
            )
        )
    else:
        data_request = cast(
            DataRequest,
            checkpoint_store.load_payload(config.run_id, "DataRequest"),
        )

    # Data stage — halt logic only fires when data_runner executed.
    if resume in (None, "intake", "intake_to_data_adapter", "data"):
        data_report = data_runner(data_request)
        checkpoint_store.save(
            _envelope(
                run_id=config.run_id,
                correlation_id=config.correlation_id,
                source="orchestrator",
                target="website",
                payload_type="DataReport",
                payload=data_report.model_dump(mode="json"),
            )
        )
        if data_report.status != "COMPLETE":
            return PipelineResult(
                run_id=config.run_id,
                status="FAILED_AT_DATA",
                intake_report=intake_report,
                data_request=data_request,
                data_report=data_report,
                failure_reason=f"data_status={data_report.status}",
                resume_point=resume,
            )
    else:
        data_report = cast(
            DataReport,
            checkpoint_store.load_payload(config.run_id, "DataReport"),
        )

    # Website stage — always re-executes when reached. RepoTarget from
    # config always wins on resume (§6.4); any prior saved RepoTarget is
    # overwritten.
    checkpoint_store.save(
        _envelope(
            run_id=config.run_id,
            correlation_id=config.correlation_id,
            source="orchestrator",
            target="website",
            payload_type="RepoTarget",
            payload=config.repo_target.model_dump(mode="json"),
        )
    )

    project_result = website_runner(intake_report, data_report, config.repo_target)
    checkpoint_store.save_result(
        run_id=config.run_id,
        name="RepoProjectResult",
        model=project_result,
    )
    if project_result.status != "COMPLETE":
        return PipelineResult(
            run_id=config.run_id,
            status="FAILED_AT_WEBSITE",
            intake_report=intake_report,
            data_request=data_request,
            data_report=data_report,
            project_result=project_result,
            failure_reason=(
                project_result.failure_reason
                or f"website_status={project_result.status}"
            ),
            resume_point=resume,
        )

    return PipelineResult(
        run_id=config.run_id,
        status="COMPLETE",
        intake_report=intake_report,
        data_request=data_request,
        data_report=data_report,
        project_result=project_result,
        resume_point=resume,
    )


def _envelope(
    *,
    run_id: str,
    correlation_id: str,
    source: Literal["intake", "data", "website", "orchestrator"],
    target: Literal["intake", "data", "website"],
    payload_type: str,
    payload: dict[str, Any],
) -> HandoffEnvelope:
    return HandoffEnvelope(
        run_id=run_id,
        source_agent=source,
        target_agent=target,
        payload_type=payload_type,
        payload_schema_version="1.0.0",
        payload=payload,
        created_at=datetime.now(UTC),
        correlation_id=correlation_id,
    )


__all__ = [
    "DataRunner",
    "IntakeRunner",
    "PipelineConfig",
    "PipelineResult",
    "PipelineStatus",
    "ResumeInconsistent",
    "ResumePoint",
    "WebsiteRunner",
    "determine_resume_point",
    "run_pipeline",
]
