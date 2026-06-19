"""Phase B eval corpus loaders (multi-provider LLM plan §5 Phase B).

Loads the golden-input corpus that the deterministic and ``live`` tiers share:

* **governance** — ``(DraftReportResult, reference GovernanceClassification)``
  pairs. The first three reuse the project's own human-authored intake fixtures
  (``tests/fixtures/{subrogation,pricing_optimization,fraud_triage}.yaml``), the
  most defensible reference; the fourth is authored for the eval to complete the
  ``RiskTier`` vocabulary. See README §"Governance reference labels".
* **sql** — ``DataRequest`` + a parse-valid, executable reference SQL per case,
  for the SQL parse/executability capability against the seeded P&C schema.
* **interview** — fixture paths + the expected terminal outcome, for the
  interview-convergence capability.

Reusing the existing fixtures keeps the governance labels single-sourced (no
duplication of the project's blessed goldens).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import sqlalchemy as sa
import yaml
from model_project_constructor_data_agent.db import ReadOnlyDB
from model_project_constructor_data_agent.schemas import (
    ColumnMetadata,
    DataGranularity,
    DataRequest,
    DataSourceEntry,
    DataSourceInventory,
    ProducerMetadata,
)

from model_project_constructor.agents.intake.protocol import (
    DraftReportResult,
    GovernanceClassification,
)

# A fixed timestamp so the inventory built from the seeded schema is deterministic
# (the corpus must not depend on wall-clock time).
_FIXED_TS = datetime(2024, 1, 1, tzinfo=UTC)

_CORPUS_DIR = Path(__file__).parent / "corpus"
_PROJECT_FIXTURES = Path(__file__).parents[1] / "fixtures"

#: The seeded P&C schema (DDL + deterministic rows) the SQL capability runs on.
PC_SCHEMA_SQL: Path = _CORPUS_DIR / "pc_schema.sql"


@dataclass(frozen=True)
class GovernanceCase:
    """One governance corpus case: an input draft + its reference label."""

    case_id: str
    draft: DraftReportResult
    reference: GovernanceClassification
    provenance: str  # 'reused project fixture' | 'authored for eval'


@dataclass(frozen=True)
class InterviewCase:
    """One interview golden: a fixture path + its expected terminal outcome."""

    case_id: str
    fixture_path: Path
    expect_complete: bool  # True → converges COMPLETE; False → terminates at a cap


@dataclass(frozen=True)
class SqlCase:
    """One SQL corpus case: a DataRequest + a reference SQL known to execute."""

    name: str
    kind: str  # 'primary' | 'baseline'
    request: DataRequest
    reference_sql: str
    measurement_unit: str | None


# (case_id, fixture path, provenance). Order is stable so corpus metrics and the
# README inventory line up.
_GOVERNANCE_SOURCES: list[tuple[str, Path, str]] = [
    ("subrogation", _PROJECT_FIXTURES / "subrogation.yaml", "reused project fixture"),
    (
        "pricing_optimization",
        _PROJECT_FIXTURES / "pricing_optimization.yaml",
        "reused project fixture",
    ),
    ("fraud_triage", _PROJECT_FIXTURES / "fraud_triage.yaml", "reused project fixture"),
    (
        "reserving_adequacy",
        _CORPUS_DIR / "governance" / "reserving_adequacy.yaml",
        "authored for eval",
    ),
    # Role≠frequency case (Session 177): a fixed nightly BATCH (operational
    # frequency cue) whose output is PER-CASE decision support → tactical. Tests
    # the tactical/operational boundary where run frequency and output purpose
    # diverge; reserving_adequacy is its batch-cadence operational foil. Loaded
    # for governance only (deliberately not added to _INTERVIEW_SOURCES).
    (
        "claim_workqueue_triage",
        _CORPUS_DIR / "governance" / "claim_workqueue_triage.yaml",
        "authored for eval",
    ),
]

# Interview goldens: the four converging scenarios + the question-cap fixture,
# which must terminate DRAFT_INCOMPLETE at the 20-question cap (not converge).
_INTERVIEW_SOURCES: list[tuple[str, Path, bool]] = [
    ("subrogation", _PROJECT_FIXTURES / "subrogation.yaml", True),
    ("pricing_optimization", _PROJECT_FIXTURES / "pricing_optimization.yaml", True),
    ("fraud_triage", _PROJECT_FIXTURES / "fraud_triage.yaml", True),
    ("reserving_adequacy", _CORPUS_DIR / "governance" / "reserving_adequacy.yaml", True),
    ("question_cap", _PROJECT_FIXTURES / "intake_question_cap.yaml", False),
]


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open() as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"expected a mapping in {path}, got {type(data).__name__}")
    return data


def _draft_from_fixture(draft: dict[str, Any]) -> DraftReportResult:
    return DraftReportResult(
        business_problem=draft["business_problem"],
        proposed_solution=draft["proposed_solution"],
        model_solution=draft["model_solution"],
        estimated_value=draft["estimated_value"],
        missing_fields=list(draft.get("missing_fields", [])),
        value_measurement_plan=draft.get("value_measurement_plan", {}),
    )


def _governance_from_fixture(gov: dict[str, Any]) -> GovernanceClassification:
    return GovernanceClassification(
        cycle_time=gov["cycle_time"],
        cycle_time_rationale=gov["cycle_time_rationale"],
        risk_tier=gov["risk_tier"],
        risk_tier_rationale=gov["risk_tier_rationale"],
        regulatory_frameworks=list(gov["regulatory_frameworks"]),
        affects_consumers=bool(gov["affects_consumers"]),
        uses_protected_attributes=bool(gov["uses_protected_attributes"]),
    )


def load_governance_cases() -> list[GovernanceCase]:
    """Load every governance corpus case (reused fixtures + the authored case)."""
    cases: list[GovernanceCase] = []
    for case_id, path, provenance in _GOVERNANCE_SOURCES:
        data = _load_yaml(path)
        cases.append(
            GovernanceCase(
                case_id=case_id,
                draft=_draft_from_fixture(data["draft"]),
                reference=_governance_from_fixture(data["governance"]),
                provenance=provenance,
            )
        )
    return cases


def load_interview_cases() -> list[InterviewCase]:
    """Load the interview goldens (paths + expected terminal outcome)."""
    return [InterviewCase(cid, path, expect) for cid, path, expect in _INTERVIEW_SOURCES]


def load_sql_cases() -> list[SqlCase]:
    """Load the SQL corpus (DataRequest + reference SQL per case)."""
    data = _load_yaml(_CORPUS_DIR / "sql_cases.yaml")
    cases: list[SqlCase] = []
    for raw in data["cases"]:
        req = raw["request"]
        gran = req["target_granularity"]
        request = DataRequest(
            target_description=req["target_description"],
            target_granularity=DataGranularity(
                unit=gran["unit"], time_grain=gran["time_grain"]
            ),
            required_features=list(req["required_features"]),
            population_filter=req["population_filter"],
            time_range=req["time_range"],
            database_hint=req.get("database_hint"),
            baseline_metric_name=req.get("baseline_metric_name"),
            baseline_metric_definition=req.get("baseline_metric_definition"),
            baseline_measurement_window=req.get("baseline_measurement_window"),
            source="standalone",
            source_ref=f"eval:{raw['name']}",
        )
        cases.append(
            SqlCase(
                name=raw["name"],
                kind=raw["kind"],
                request=request,
                # collapse the YAML folded-scalar whitespace into single spaces
                reference_sql=" ".join(raw["reference_sql"].split()),
                measurement_unit=raw.get("measurement_unit"),
            )
        )
    return cases


def _seed_statements() -> list[str]:
    """Split the seed DDL into executable statements (drop full-line comments)."""
    lines = [
        ln for ln in PC_SCHEMA_SQL.read_text().splitlines() if not ln.strip().startswith("--")
    ]
    return [stmt.strip() for stmt in "\n".join(lines).split(";") if stmt.strip()]


def seed_pc_schema(url: str) -> None:
    """Seed the P&C eval schema (DDL + rows) into the SQLite database at ``url``.

    Mirrors ``tests/agents/data/conftest.py``: seed with a writable engine, then
    hand the URL to a read-only ``ReadOnlyDB`` for query execution.
    """
    engine = sa.create_engine(url)
    try:
        with engine.begin() as conn:
            for statement in _seed_statements():
                conn.execute(sa.text(statement))
    finally:
        engine.dispose()


def pc_inventory_from_db(db: ReadOnlyDB) -> DataSourceInventory:
    """Build a ``DataSourceInventory`` by introspecting the seeded P&C schema.

    Single-sourced from the DDL (no hand-maintained copy of the columns): the
    live SQL capability passes this to ``generate_primary_queries`` so the model
    can name the real tables/columns, making the executability measurement fair.
    """
    entries: list[DataSourceEntry] = []
    for row in db.get_information_schema():
        columns = [
            ColumnMetadata(
                name=col["name"],
                data_type=str(col["data_type"]),
                nullable=col.get("nullable"),
                is_primary_key=bool(col.get("is_primary_key", False)),
                is_foreign_key=bool(col.get("is_foreign_key", False)),
                foreign_key_target=col.get("foreign_key_target"),
            )
            for col in row["columns"]
        ]
        entries.append(
            DataSourceEntry(
                name=row["name"],
                fully_qualified_name=row["name"],
                entity_kind=row["entity_kind"],
                columns=columns,
                primary_key_columns=list(row.get("primary_key_columns", [])),
                producer_id="eval_seed",
            )
        )
    producer = ProducerMetadata(
        producer_id="eval_seed", producer_type="curated", produced_at=_FIXED_TS
    )
    return DataSourceInventory(
        entries=entries,
        producers=[producer],
        created_at=_FIXED_TS,
        request_context="Phase B eval seeded P&C schema (tests/eval/corpus/pc_schema.sql)",
    )
