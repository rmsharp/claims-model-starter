"""Fixtures for Data Agent tests.

Seeds a small SQLite claims table on a tmp path so the EXECUTE_QC node
can be exercised against real SQL over a real database without hitting
a network or requiring credentials.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
import sqlalchemy as sa

from model_project_constructor.agents.data.db import ReadOnlyDB
from model_project_constructor.agents.data.llm import (
    PrimaryQuerySpec,
    QualityCheckSpec,
    SummaryResult,
)
from model_project_constructor.schemas.v1.data import (
    DataGranularity,
    DataRequest,
    Datasheet,
)


@pytest.fixture
def seeded_sqlite_url(tmp_path: Path) -> Iterator[str]:
    db_path = tmp_path / "claims.db"
    engine = sa.create_engine(f"sqlite:///{db_path}")
    try:
        with engine.begin() as conn:
            conn.execute(
                sa.text(
                    """
                    CREATE TABLE claims (
                        claim_id INTEGER PRIMARY KEY,
                        policy_id INTEGER NOT NULL,
                        loss_date TEXT NOT NULL,
                        paid_amount REAL NOT NULL,
                        subro_recovered REAL DEFAULT 0,
                        state TEXT NOT NULL
                    )
                    """
                )
            )
            conn.execute(
                sa.text(
                    """
                    INSERT INTO claims
                        (claim_id, policy_id, loss_date, paid_amount, subro_recovered, state)
                    VALUES
                        (1, 100, '2024-01-15',  5000.0, 1200.0, 'TX'),
                        (2, 101, '2024-02-20',  8000.0,    0.0, 'TX'),
                        (3, 102, '2024-03-05',  2500.0,  500.0, 'NY'),
                        (4, 103, '2024-04-11', 15000.0,    0.0, 'CA'),
                        (5, 104, '2024-05-22',  6200.0, 3100.0, 'TX')
                    """
                )
            )
        yield f"sqlite:///{db_path}"
    finally:
        engine.dispose()


@pytest.fixture
def seeded_db(seeded_sqlite_url: str) -> Iterator[ReadOnlyDB]:
    db = ReadOnlyDB(seeded_sqlite_url)
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def sample_request() -> DataRequest:
    return DataRequest(
        target_description="subrogation recovery amount on TX auto claims",
        target_granularity=DataGranularity(unit="claim", time_grain="event"),
        required_features=["paid_amount", "state", "loss_date"],
        population_filter="TX auto claims with loss in 2024",
        time_range="2024-01-01 to 2024-12-31",
        database_hint="claims",
        source="standalone",
        source_ref="unit-test",
    )


@pytest.fixture
def primary_query_spec_valid() -> PrimaryQuerySpec:
    return PrimaryQuerySpec(
        name="tx_claims_2024",
        sql="SELECT claim_id, paid_amount, subro_recovered FROM claims WHERE state = 'TX'",
        purpose="Training set for TX subrogation recovery classifier",
        expected_row_count_order="thousands",
    )


@pytest.fixture
def qc_specs_valid() -> list[QualityCheckSpec]:
    return [
        QualityCheckSpec(
            check_name="row_count_nonempty",
            check_sql="SELECT COUNT(*) AS n FROM claims WHERE state = 'TX'",
            expectation="TX claim set should contain at least one row",
        ),
        QualityCheckSpec(
            check_name="no_negative_paid_amount",
            check_sql=(
                "SELECT claim_id FROM claims "
                "WHERE state = 'TX' AND paid_amount < 0"
            ),
            expectation="No TX claim should have a negative paid amount",
        ),
    ]


@pytest.fixture
def summary_response() -> SummaryResult:
    return SummaryResult(
        summary=(
            "The TX claims training set contains 3 rows. Paid amounts are all "
            "non-negative. Subrogation recovery is present on 2 of 3 rows, "
            "consistent with a classifier-sized positive rate."
        ),
        confirmed_expectations=[
            "row_count_nonempty is satisfied",
            "no_negative_paid_amount is satisfied",
        ],
        unconfirmed_expectations=[
            "population filter precision cannot be confirmed without join keys"
        ],
        data_quality_concerns=[
            "subro_recovered==0 rows may be censored rather than true negatives"
        ],
    )


@pytest.fixture
def datasheet_response() -> Datasheet:
    return Datasheet(
        motivation="Train a classifier to predict successful subrogation recovery.",
        composition="Claim-level rows keyed by claim_id with paid amount and outcome.",
        collection_process="Query over claims table filtered to TX, 2024.",
        preprocessing="None at extraction time.",
        uses="Supervised training set.",
        known_biases=["TX-only; cannot generalise to other states"],
        maintenance="Regenerated whenever the source claims table is refreshed.",
    )
