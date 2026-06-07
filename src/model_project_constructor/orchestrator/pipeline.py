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
from dataclasses import dataclass, field, fields
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal, TypeVar, cast

from pydantic import BaseModel

from model_project_constructor._vocab_guard import assert_vocab_parity
from model_project_constructor.orchestrator.adapters import (
    intake_qa_pairs_to_inventory,
    intake_report_to_data_request,
    load_curated_inventory,
    merge_inventories,
)
from model_project_constructor.orchestrator.checkpoints import CheckpointStore
from model_project_constructor.schemas.envelope import HandoffEnvelope
from model_project_constructor.schemas.v1.data import (
    DataReport,
    DataRequest,
    DataSourceInventory,
)
from model_project_constructor.schemas.v1.intake import IntakeReport
from model_project_constructor.schemas.v1.repo import (
    RepoProjectResult,
    RepoTarget,
)

IntakeRunner = Callable[[], IntakeReport]
DataRunner = Callable[[DataRequest], DataReport]
WebsiteRunner = Callable[[IntakeReport, DataReport, RepoTarget], RepoProjectResult]

_StageT = TypeVar("_StageT", bound=BaseModel)
"""Per-stage payload type — narrows the registry-resolved ``BaseModel`` back to a
stage's concrete model in :func:`_run_or_load_stage` (inferred from the stage's
``execute`` runner, so no separate ``payload_model`` argument is needed)."""

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

TargetAgent = Literal["intake", "data", "website"]
"""The envelope ``target_agent`` domain (== ``HandoffEnvelope.target_agent``)."""


@dataclass(frozen=True)
class Stage:
    """Per-stage metadata — the single source of stage order (via ``STAGE_ORDER``).

    Pure metadata only: **no callables**. The agent runners stay
    :func:`run_pipeline` keyword arguments (the ``IntakeRunner`` / ``DataRunner``
    / ``WebsiteRunner`` aliases above) because their closures capture per-run
    state (``intake_report``, ``data_request``, ``config.repo_target``) that
    cannot exist at module-import time. Keeping the record import-time
    inspectable is the precondition for the drift guards below to derive
    ``ResumePoint`` / ``PipelineStatus`` parity *without* executing a runner.
    See ``docs/planning/o1-stage-driver-plan.md`` §6.1.

    Introduced **dormant** in Phase O1-1 (no consumer); the resume gates and the
    CLI banner are wired to it in O1-2, the decomposition helpers in O1-3.
    """

    name: ResumePoint
    payload_type: str
    target_agent: TargetAgent
    has_runner: bool
    halt_status: PipelineStatus | None
    result_field: str
    always_runs: bool = False
    terminal_result: bool = False


STAGE_ORDER: tuple[Stage, ...] = (
    Stage(
        "intake",
        "IntakeReport",
        "data",
        has_runner=True,
        halt_status="FAILED_AT_INTAKE",
        result_field="intake_report",
    ),
    Stage(
        "intake_to_data_adapter",
        "DataRequest",
        "data",
        has_runner=False,
        halt_status=None,
        result_field="data_request",
    ),
    Stage(
        "data",
        "DataReport",
        "website",
        has_runner=True,
        halt_status="FAILED_AT_DATA",
        result_field="data_report",
    ),
    Stage(
        "website",
        "RepoTarget",
        "website",
        has_runner=True,
        halt_status="FAILED_AT_WEBSITE",
        result_field="project_result",
        always_runs=True,
        terminal_result=True,
    ),
)
"""The ordered pipeline stages. Its sequence is the single source of stage
order; the resume gates (O1-2), the CLI banner (O1-2), and the save/halt helpers
(O1-3) all derive from it. The website stage is terminal and MUST be last
(pinned by ``tests/orchestrator/test_stage_order.py``)."""

STAGE_NAMES: tuple[ResumePoint, ...] = tuple(s.name for s in STAGE_ORDER)
_STAGE_INDEX: dict[str, int] = {s.name: i for i, s in enumerate(STAGE_ORDER)}

# Named bindings for the four descriptor rows. The resume gates in
# ``run_pipeline`` and the demotion ladder in ``determine_resume_point`` reference
# these (and ``.name``) instead of literal stage tokens, so ``STAGE_ORDER`` is
# their single source. Positions are pinned by ``test_stage_order.py``'s field
# table; ``_STAGE_WEBSITE`` has no gate (it always re-executes).
_STAGE_INTAKE = STAGE_ORDER[0]
_STAGE_ADAPTER = STAGE_ORDER[1]
_STAGE_DATA = STAGE_ORDER[2]
_STAGE_WEBSITE = STAGE_ORDER[3]


def _should_run(resume: ResumePoint | None, stage: Stage) -> bool:
    """Return True iff ``stage`` must (re-)execute given ``resume``.

    Replaces the three hand-written resume-membership gates in
    :func:`run_pipeline` (the ``resume is None or resume == "intake"``,
    ``resume in (None, "intake", "intake_to_data_adapter")``, and
    ``... "data")`` conditionals): a stage runs when the resume point is at or
    before it in ``STAGE_ORDER``; ``always_runs`` (the terminal website stage)
    is unconditional. ``resume == "already_complete"`` never reaches this gate —
    :func:`run_pipeline` rejects it up front — so ``_STAGE_INDEX`` need not
    contain it. Dormant until O1-2.
    """

    return (
        stage.always_runs
        or resume is None
        or _STAGE_INDEX[resume] <= _STAGE_INDEX[stage.name]
    )


def skipped_stages(resume: ResumePoint | None) -> list[str]:
    """Return the stage names LOADED (not re-executed) for ``resume``.

    Replaces ``_SKIPPED_STAGES_BY_RESUME_POINT``
    (``scripts/run_pipeline.py:317``); the CLI banner consumes it in O1-2.
    ``already_complete`` is not a stage — the CLI intercepts it before the
    banner — so it returns all four names (the dead-but-present CLI row).
    Dormant until O1-2.
    """

    if resume == "already_complete":
        return [stage.name for stage in STAGE_ORDER]
    return [stage.name for stage in STAGE_ORDER if not _should_run(resume, stage)]


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

    Reads the checkpoint dir (pure in the side-effect sense — no mutation)
    and consults the saved ``IntakeReport`` / ``DataReport`` payloads'
    ``status`` field. A non-``"COMPLETE"`` payload is the halt artifact of
    a prior run, not a completed handoff: it demotes the resume point to
    re-execute that stage. See ``docs/planning/resume-from-checkpoint-plan.md``
    §11 risk #8 (the inverse of risk #5).

    Does NOT consult ``RepoTarget`` (``T`` in the truth table): per the
    plan §6.4, the operator-supplied ``config.repo_target`` always wins
    on resume, so a saved ``RepoTarget`` envelope is not load-bearing for
    the resume-point decision.

    Terminal ``RepoProjectResult`` is handled by ``already_complete`` ->
    CLI's ``_handle_already_complete``, which inspects status and offers
    the operator opt-in-to-retry for the FAILED case (website has
    irreversible side effects; auto-retry would be wrong).

    See ``docs/planning/resume-from-checkpoint-plan.md`` §5 for the
    truth table this function implements. Raises
    :class:`ResumeInconsistent` for rows marked INVALID (a successor
    envelope without its predecessor). A FAILED envelope is NOT
    ``ResumeInconsistent`` — it is a legitimate halt artifact.
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

    # RepoProjectResult short-circuits: the CLI's _handle_already_complete
    # (scripts/run_pipeline.py:346) reads the saved result and decides
    # COMPLETE vs FAILED opt-in-to-retry. Status of any predecessor
    # envelope is not load-bearing here.
    if result_present:
        return "already_complete"

    # Status-aware demotion: an IntakeReport or DataReport on disk is
    # the halt artifact of a prior FAILED_AT_{INTAKE,DATA} run when its
    # saved status is not "COMPLETE". Loads happen only when status
    # materially affects the resume point — short-circuit above keeps
    # the hot path free of payload deserialization when a terminal
    # result is present.
    if report_present:
        if _is_saved_payload_complete(store, run_id, "DataReport"):
            return _STAGE_WEBSITE.name
        return _STAGE_DATA.name  # DataReport FAILED → re-run data stage.
    if request_present:
        # DataRequest present with IntakeReport missing is already caught
        # by the INVALID check above, so intake_present is True here.
        # Intake must be COMPLETE for the pipeline to have advanced to
        # DataRequest (pipeline.py:205-215 halts before save_request on
        # non-COMPLETE intake), so demotion from "data" is defensive
        # only — the branch fires for a hand-mutated dir.
        if _is_saved_payload_complete(store, run_id, "IntakeReport"):
            return _STAGE_DATA.name
        return _STAGE_INTAKE.name
    if intake_present:
        if _is_saved_payload_complete(store, run_id, "IntakeReport"):
            return _STAGE_ADAPTER.name
        return _STAGE_INTAKE.name  # DRAFT_INCOMPLETE intake → re-run interview.
    return _STAGE_INTAKE.name


def _is_saved_payload_complete(
    store: CheckpointStore, run_id: str, payload_type: str
) -> bool:
    """Return True iff the saved envelope's payload has ``status == "COMPLETE"``.

    Used by :func:`determine_resume_point` to distinguish a completed
    handoff (skip the stage) from a FAILED halt artifact (re-execute the
    stage). Propagates ``pydantic.ValidationError`` on schema drift —
    that is a different failure class than :class:`ResumeInconsistent`
    (which is reserved for missing-predecessor structural problems).
    """

    payload = store.load_payload(run_id, payload_type)
    return getattr(payload, "status", None) == "COMPLETE"


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
    inventory_from_intake: bool = False
    curated_inventory_path: Path | None = None

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


# --- Import-time drift guards (o1-stage-driver-plan.md §6.3) -----------------
# ``STAGE_ORDER`` is the runtime single source of stage order + per-stage status
# metadata; the hand-written ``ResumePoint`` / ``PipelineStatus`` Literals (which
# mypy can read but cannot derive from a runtime tuple) are pinned to it by these
# checks so the build fails loudly the moment they drift. A real ``raise`` (not a
# bare ``assert``) is used so the guards survive ``python -O`` — see
# ``_vocab_guard`` and ``tests/orchestrator/test_stage_order.py`` (non-vacuous
# RED proofs).

# Guard 1 — ResumePoint == the stage names + the non-stage ``already_complete``
# sentinel. ``assert_vocab_parity`` does an EXACT set match, so the sentinel
# (a CLI-layer signal, not a STAGE_ORDER row) MUST be added explicitly; passing
# ``set(STAGE_NAMES)`` alone would (correctly) fail import.
assert_vocab_parity(
    set(STAGE_NAMES) | {"already_complete"},
    ResumePoint,
    name="STAGE_ORDER",
    reconcile_hint=(
        "Reconcile STAGE_ORDER with ResumePoint in pipeline.py "
        "(ResumePoint = stage names + 'already_complete')."
    ),
)

# Guard 2 — PipelineStatus == COMPLETE + each stage's halt_status. Closes the
# §3.6 metrics gap: a misspelled halt_status would otherwise leak a non-literal
# status into a ``record_run`` metrics key silently.
assert_vocab_parity(
    {"COMPLETE"} | {s.halt_status for s in STAGE_ORDER if s.halt_status is not None},
    PipelineStatus,
    name="STAGE_ORDER.halt_status",
    reconcile_hint="Reconcile STAGE_ORDER.halt_status with PipelineStatus in pipeline.py.",
)

# Guard 3 — every result_field names a real PipelineResult attribute. A SUBSET
# check, so it cannot use ``assert_vocab_parity`` (exact-match only); a raise
# (not a bare assert) keeps it live under ``python -O``. Closes the §3.6
# wrong-field gap.
_missing_result_fields = {s.result_field for s in STAGE_ORDER} - {
    f.name for f in fields(PipelineResult)
}
if _missing_result_fields:
    raise AssertionError(
        "STAGE_ORDER.result_field names attributes absent from PipelineResult: "
        f"{sorted(_missing_result_fields)}"
    )


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

    if config.resume_from == "already_complete":
        raise ValueError(
            f"Run {config.run_id!r}: already_complete — nothing to resume."
        )

    # Intake stage — execute unless resume points past it; a loaded envelope is
    # trusted predecessor output, so the halt check is gated on ``executed``
    # (resume-from-checkpoint-plan.md §11 risk #5).
    intake_report, executed = _run_or_load_stage(
        checkpoint_store,
        config,
        stage=_STAGE_INTAKE,
        execute=intake_runner,
    )
    if executed and intake_report.status != "COMPLETE":
        return _halt(
            config,
            "FAILED_AT_INTAKE",
            failure_reason=(
                f"intake_status={intake_report.status}; "
                f"missing_fields={intake_report.missing_fields}"
            ),
            intake_report=intake_report,
        )

    # Adapter stage — deterministic pure code (no runner, no halt: DataRequest
    # carries no .status). On resume past it, the saved DataRequest envelope is
    # ground truth (§6.3); otherwise derive it inline (§6.5).
    data_request, _ = _run_or_load_stage(
        checkpoint_store,
        config,
        stage=_STAGE_ADAPTER,
        execute=lambda: _derive_data_request(intake_report, config),
    )

    # Data stage — halt only fires when the data runner actually executed.
    data_report, executed = _run_or_load_stage(
        checkpoint_store,
        config,
        stage=_STAGE_DATA,
        execute=lambda: data_runner(data_request),
    )
    if executed and data_report.status != "COMPLETE":
        return _halt(
            config,
            "FAILED_AT_DATA",
            failure_reason=f"data_status={data_report.status}",
            intake_report=intake_report,
            data_request=data_request,
            data_report=data_report,
        )

    # Website stage — terminal, always re-executes when reached. Explicit block
    # (§6.5): save the RepoTarget envelope (config always wins, overwrites any
    # prior) BEFORE the runner; persist the terminal RepoProjectResult via
    # save_result (NOT _save — un-enveloped, distinct method) AFTER. Ordering
    # pinned by TestWebsiteSaveOrdering.
    _save(checkpoint_store, config, stage=_STAGE_WEBSITE, payload=config.repo_target)
    project_result = website_runner(intake_report, data_report, config.repo_target)
    checkpoint_store.save_result(
        run_id=config.run_id,
        name="RepoProjectResult",
        model=project_result,
    )
    if project_result.status != "COMPLETE":
        return _halt(
            config,
            "FAILED_AT_WEBSITE",
            failure_reason=(
                project_result.failure_reason
                or f"website_status={project_result.status}"
            ),
            intake_report=intake_report,
            data_request=data_request,
            data_report=data_report,
            project_result=project_result,
        )

    return _halt(
        config,
        "COMPLETE",
        failure_reason=None,
        intake_report=intake_report,
        data_request=data_request,
        data_report=data_report,
        project_result=project_result,
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


def _save(
    store: CheckpointStore,
    config: PipelineConfig,
    *,
    stage: Stage,
    payload: BaseModel,
) -> None:
    """Persist ``payload`` as the stage's orchestrator handoff envelope.

    The single place that builds + saves the four non-terminal handoff envelopes
    (formerly four inline envelope-save blocks in :func:`run_pipeline`).
    ``source_agent`` is always ``"orchestrator"``; ``target_agent`` and
    ``payload_type`` come from the :class:`Stage`, so ``STAGE_ORDER`` is their
    single source (pinned by ``TestEnvelopeTargetAgents``). NOT used for the
    terminal ``RepoProjectResult`` — that is un-enveloped and goes through
    :meth:`CheckpointStore.save_result` (§6.5; ``save``/``save_result`` stay
    distinct).
    """

    store.save(
        _envelope(
            run_id=config.run_id,
            correlation_id=config.correlation_id,
            source="orchestrator",
            target=stage.target_agent,
            payload_type=stage.payload_type,
            payload=payload.model_dump(mode="json"),
        )
    )


def _run_or_load_stage(
    store: CheckpointStore,
    config: PipelineConfig,
    *,
    stage: Stage,
    execute: Callable[[], _StageT],
) -> tuple[_StageT, bool]:
    """Execute ``stage`` and persist its output, or load it from a checkpoint.

    Returns ``(payload, executed)``. When :func:`_should_run` says the stage is
    at or before the resume point it runs ``execute``, saves the envelope via
    :func:`_save`, and returns ``executed=True``; otherwise it loads the saved
    payload and returns ``executed=False``. The ``FAILED_AT_*`` halt check stays
    at the CALL SITE, gated on ``executed`` — so a LOADED FAILED/DRAFT envelope
    is treated as trusted predecessor output and never re-halts (resume risk #5,
    §6.5). The concrete payload type ``_StageT`` is inferred from ``execute`` (no
    separate ``payload_model`` arg — the runner's return type already fixes it);
    the registry-resolved ``BaseModel`` on the load path is cast back to it. NOT
    used for the terminal website stage (it owns its explicit ``_save`` +
    ``save_result`` sequence — §6.5).
    """

    if _should_run(config.resume_from, stage):
        payload = execute()
        _save(store, config, stage=stage, payload=payload)
        return payload, True
    return (
        cast(_StageT, store.load_payload(config.run_id, stage.payload_type)),
        False,
    )


def _halt(
    config: PipelineConfig,
    status: PipelineStatus,
    *,
    failure_reason: str | None,
    **reports: Any,
) -> PipelineResult:
    """Build the terminal :class:`PipelineResult` — the single return point.

    Collapses the three ``FAILED_AT_*`` returns and the ``COMPLETE`` return.
    ``reports`` is the ``result_field``-keyed dict of artifacts produced so far
    (``intake_report`` / ``data_request`` / ``data_report`` / ``project_result``);
    unset reports default to ``None``. ``resume_point`` echoes
    ``config.resume_from`` on EVERY path — load-bearing for the resume matrix
    (pinned by ``TestResumePointEchoedOnEveryReturnPath``). A typo'd report key
    raises ``TypeError`` at call time (``PipelineResult`` is a dataclass — it does
    not silently drop); a wrong-but-valid key is caught by guard #3 +
    ``TestHaltPaths``'s retained-report assertions (§6.4).
    """

    return PipelineResult(
        run_id=config.run_id,
        status=status,
        failure_reason=failure_reason,
        resume_point=config.resume_from,
        **reports,
    )


def _derive_data_request(
    intake_report: IntakeReport, config: PipelineConfig
) -> DataRequest:
    """Adapter-stage body — derive the ``DataRequest`` from the intake report.

    Kept inline (not a fake ``DataRunner``) because it closes over
    ``config.curated_inventory_path`` / ``config.inventory_from_intake`` /
    ``config.run_id`` and the live ``intake_report`` — none of which the runner
    aliases carry (§6.5). Optional curated + interview inventories merge with
    curated winning on duplicate FQN (the contract pinned by ``TestPipelineConfig``
    inventory tests). A verbatim extraction of the former inline adapter block —
    no behavior change.
    """

    curated = (
        load_curated_inventory(config.curated_inventory_path)
        if config.curated_inventory_path is not None
        else None
    )
    interview = (
        intake_qa_pairs_to_inventory(intake_report)
        if config.inventory_from_intake
        else None
    )
    inventory: DataSourceInventory | None
    if curated is not None and interview is not None:
        inventory = merge_inventories(curated, interview)
    else:
        inventory = curated or interview
    return intake_report_to_data_request(
        intake_report, config.run_id, data_source_inventory=inventory
    )


__all__ = [
    "STAGE_ORDER",
    "DataRunner",
    "IntakeRunner",
    "PipelineConfig",
    "PipelineResult",
    "PipelineStatus",
    "ResumeInconsistent",
    "ResumePoint",
    "Stage",
    "WebsiteRunner",
    "determine_resume_point",
    "run_pipeline",
    "skipped_stages",
]
