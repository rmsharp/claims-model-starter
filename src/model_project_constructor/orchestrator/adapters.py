"""Intake → Data handoff adapter (architecture-plan §7, §12, §14 Phase 5).

This module is the **only** place where ``IntakeReport`` and ``DataRequest``
are imported together. Per §7 the Data Agent package must not reference the
intake schemas; this adapter lives in the orchestrator so the decoupling
test stays green.

``intake_report_to_data_request`` is deliberately conservative: it copies
what the intake agent explicitly gathered (target definition, candidate
features) and fills the Data Agent's structured-request fields with
best-effort defaults for anything the intake interview does not capture
(``time_range``, ``population_filter``). The Data Agent later surfaces
ambiguous requests as ``status=INCOMPLETE_REQUEST``; the adapter does not
try to be clever about fields the downstream agent can diagnose better.
"""

from __future__ import annotations

from model_project_constructor.schemas.v1.data import (
    DataGranularity,
    DataRequest,
    DataSourceInventory,
)
from model_project_constructor.schemas.v1.intake import IntakeReport

_DEFAULT_TIME_RANGE = "last 5 calendar years of historical records"
_DEFAULT_UNIT = "claim"


def infer_target_granularity(intake: IntakeReport) -> DataGranularity:
    """Pick a sensible ``DataGranularity`` from the intake's ``model_type``.

    Classification / regression / clustering are event-grained (one row per
    observation). ``time_series`` models imply a monthly grain — the P&C
    claims domain has monthly operational cadence, which is what the
    downstream Data Agent will see unless it overrides us.
    """

    model_type = intake.model_solution.model_type
    if model_type == "time_series":
        return DataGranularity(unit=_DEFAULT_UNIT, time_grain="monthly")
    return DataGranularity(unit=_DEFAULT_UNIT, time_grain="event")


def intake_report_to_data_request(
    intake: IntakeReport,
    run_id: str,
    *,
    data_source_inventory: DataSourceInventory | None = None,
) -> DataRequest:
    """Build a ``DataRequest`` from a COMPLETE ``IntakeReport``.

    The adapter assumes ``intake.status == "COMPLETE"`` — callers
    (``run_pipeline``) guarantee this by halting on upstream failure before
    calling the adapter. If an intake with ``status="DRAFT_INCOMPLETE"`` is
    passed in, the adapter still produces a valid ``DataRequest`` object,
    because partial information is still a legitimate starting point for
    the Data Agent's ``INCOMPLETE_REQUEST`` diagnosis path.

    :param intake: The upstream ``IntakeReport``.
    :param run_id: The pipeline run id, copied into ``source_ref`` so the
        Data Agent can trace the request back to its originating run.
    :param data_source_inventory: Optional upstream-produced inventory of
        data sources relevant to the request. When provided, the Data Agent
        consults it while generating primary SQL (Phase 3 of the
        data-source-inventory plan). Default ``None`` preserves pre-Phase-3
        behaviour for every existing caller.
    """

    target_description = intake.model_solution.target_definition
    population_filter = (
        f"Population scoped to the intake target definition: {target_description}"
    )

    return DataRequest(
        target_description=target_description,
        target_granularity=infer_target_granularity(intake),
        required_features=list(intake.model_solution.candidate_features),
        population_filter=population_filter,
        time_range=_DEFAULT_TIME_RANGE,
        database_hint=None,
        data_quality_concerns=[],
        data_source_inventory=data_source_inventory,
        source="pipeline",
        source_ref=run_id,
    )


__all__ = [
    "infer_target_granularity",
    "intake_report_to_data_request",
]
