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

from datetime import UTC, datetime
from pathlib import Path

from model_project_constructor.schemas.v1.data import (
    DataGranularity,
    DataRequest,
    DataSourceEntry,
    DataSourceInventory,
    ProducerMetadata,
)
from model_project_constructor.schemas.v1.intake import IntakeReport

_DEFAULT_TIME_RANGE = "last 5 calendar years of historical records"
_DEFAULT_UNIT = "claim"

# Canonical P&C claims systems probed by the intake interviewer
# (see ``agents/intake/anthropic_client.py:47-53`` SYSTEM_INTERVIEWER prose).
# Each key is the canonical system name; values are case-insensitive
# substrings that count as a mention. Order: most-specific aliases first
# so a "Guidewire ClaimCenter" mention matches as "Guidewire ClaimCenter"
# rather than the more generic "claims admin" entry.
_CANONICAL_PC_SYSTEMS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Guidewire ClaimCenter", ("guidewire claimcenter", "claimcenter", "guidewire")),
    ("Duck Creek Claims", ("duck creek claims", "duck creek")),
    ("Policy Admin", ("policy admin", "policy administration")),
    ("Billing and Collections", ("billing and collections", "billing", "collections")),
    ("Subrogation Recovery", ("subrogation recovery", "subrogation")),
    ("Fraud / SIU", ("fraud / siu", "fraud and siu", "fraud", "siu")),
    ("Customer CRM", ("customer crm", "agent crm", "crm")),
    ("Enterprise Data Warehouse", ("enterprise data warehouse", "data warehouse", "edw")),
    ("Data Lake", ("data lake",)),
)

_INVENTORY_PRODUCER_ID = "intake-interview"


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

    # Project the upstream value_measurement_plan into the three baseline
    # fields the data agent's baseline_collection_node consumes (architecture
    # plan §3.2 — intake defines, data agent executes; the data agent must
    # not import IntakeReport).
    baseline_metric_name: str | None = None
    baseline_metric_definition: str | None = None
    baseline_measurement_window: str | None = None
    if intake.value_measurement_plan is not None:
        baseline_metric_name = intake.value_measurement_plan.baseline_metric_name
        baseline_metric_definition = (
            intake.value_measurement_plan.baseline_metric_definition
        )
        baseline_measurement_window = (
            intake.value_measurement_plan.baseline_measurement_window
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
        baseline_metric_name=baseline_metric_name,
        baseline_metric_definition=baseline_metric_definition,
        baseline_measurement_window=baseline_measurement_window,
        source="pipeline",
        source_ref=run_id,
    )


def intake_qa_pairs_to_inventory(intake: IntakeReport) -> DataSourceInventory:
    """Convert interview transcript to a ``DataSourceInventory``.

    Scans ``intake.qa_pairs`` (question + answer text, case-insensitive)
    against the canonical P&C claims systems probed by SYSTEM_INTERVIEWER.
    Emits one :class:`DataSourceEntry` per system mentioned, with
    ``producer_type="interview"`` provenance per plan §5.3.

    The conversion is deliberately heuristic: stakeholder answers do not
    name fully-qualified tables, only systems. Each emitted entry carries
    ``entity_kind="other"`` (system-level, coarser than "table") and the
    concatenated answer text of the qa_pairs that triggered the match as
    its description. Downstream consumers can use these entries to remind
    the data agent of likely upstream systems even though the entry does
    not yet name concrete tables.

    Returns an inventory with ``entries=[]`` if no canonical system is
    mentioned anywhere in the transcript; the inventory is still a valid
    :class:`DataSourceInventory` with the interview producer recorded.
    """

    now = datetime.now(UTC)
    producer = ProducerMetadata(
        producer_id=_INVENTORY_PRODUCER_ID,
        producer_type="interview",
        produced_at=now,
        notes="Heuristic substring scan of IntakeReport.qa_pairs",
    )

    mentions: dict[str, list[str]] = {}
    for qa in intake.qa_pairs:
        text = f"{qa.question}\n{qa.answer}".lower()
        for canonical_name, aliases in _CANONICAL_PC_SYSTEMS:
            if canonical_name in mentions:
                # Already matched on this system; just append the next snippet.
                if any(alias in text for alias in aliases):
                    mentions[canonical_name].append(qa.answer)
                continue
            if any(alias in text for alias in aliases):
                mentions[canonical_name] = [qa.answer]

    entries = [
        DataSourceEntry(
            name=canonical_name,
            fully_qualified_name=canonical_name,
            entity_kind="other",
            source_system=canonical_name,
            description=" | ".join(snippets),
            producer_id=_INVENTORY_PRODUCER_ID,
        )
        for canonical_name, snippets in mentions.items()
    ]

    return DataSourceInventory(
        entries=entries,
        producers=[producer],
        created_at=now,
        request_context=(
            "Interview-sourced systems extracted from IntakeReport.qa_pairs "
            f"(stakeholder={intake.stakeholder_id}, session={intake.session_id})"
        ),
    )


def load_curated_inventory(path: Path) -> DataSourceInventory:
    """Load a curated ``DataSourceInventory`` from a JSON file.

    Producer-side counterpart to :func:`intake_qa_pairs_to_inventory`. The
    file format is the canonical Pydantic JSON shape emitted by the
    data-agent ``discover`` subcommand (see
    ``packages/data-agent/src/model_project_constructor_data_agent/cli.py``)
    and pinned by ``tests/fixtures/sample_curated_inventory.json``.

    Validation errors (malformed JSON, missing required fields, dangling
    ``producer_id``) propagate as ``pydantic.ValidationError`` /
    ``json.JSONDecodeError``; ``FileNotFoundError`` propagates from
    :meth:`pathlib.Path.read_text` when the path does not exist. Callers
    decide whether to surface these to the operator or halt the pipeline.
    """

    return DataSourceInventory.model_validate_json(path.read_text())


def merge_inventories(
    curated: DataSourceInventory,
    interview: DataSourceInventory,
) -> DataSourceInventory:
    """Merge a curated inventory with an interview-derived inventory.

    Per ``docs/planning/data-source-inventory-contract-plan.md`` §9 Phase 4
    bullet 3: **curated entries win on duplicate ``fully_qualified_name``;
    interview entries enrich (not override)**. Interview entries whose FQN
    already appears in ``curated`` are dropped; remaining interview entries
    are appended to the curated entry list.

    The result's ``producers`` list is the union of both inventories'
    producers (deduplicated by ``producer_id``, curated-first ordering).
    The interview producer is always carried even if all its entries were
    deduped out — provenance is preserved for traceability.

    ``created_at`` is set to the merge timestamp; ``request_context`` is
    descriptive of the merge composition so downstream audit
    (``DataReport`` provenance) can see what was combined.
    """

    curated_fqns = {e.fully_qualified_name for e in curated.entries}
    enriching = [
        e for e in interview.entries if e.fully_qualified_name not in curated_fqns
    ]

    seen_producer_ids: set[str] = set()
    merged_producers: list[ProducerMetadata] = []
    for producer in [*curated.producers, *interview.producers]:
        if producer.producer_id in seen_producer_ids:
            continue
        merged_producers.append(producer)
        seen_producer_ids.add(producer.producer_id)

    return DataSourceInventory(
        entries=[*curated.entries, *enriching],
        producers=merged_producers,
        created_at=datetime.now(UTC),
        request_context=(
            f"Merged inventory: curated ({len(curated.entries)} entries) + "
            f"interview ({len(enriching)} of {len(interview.entries)} "
            f"entries enriching after fully_qualified_name dedup)"
        ),
    )


__all__ = [
    "infer_target_granularity",
    "intake_qa_pairs_to_inventory",
    "intake_report_to_data_request",
    "load_curated_inventory",
    "merge_inventories",
]
