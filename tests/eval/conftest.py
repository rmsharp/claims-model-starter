"""Fixtures + collection hook for the Phase B eval tier.

The ``pytest_collection_modifyitems`` hook auto-skips ``live``-marked tests when
no ``ANTHROPIC_API_KEY`` is present, so the live tier is safe to collect locally
and in CI without a key (CI also deselects it via ``-m 'not live'``). The skip is
keyed on the ``live`` marker only, so non-eval tests are never affected.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from model_project_constructor_data_agent.db import ReadOnlyDB

from tests.eval.eval_corpus import (
    GovernanceCase,
    SqlCase,
    load_governance_cases,
    load_sql_cases,
    seed_pc_schema,
)


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if os.environ.get("ANTHROPIC_API_KEY"):
        return
    skip_live = pytest.mark.skip(
        reason="live eval tier requires ANTHROPIC_API_KEY (deselect with -m 'not live')"
    )
    for item in items:
        if "live" in item.keywords:
            item.add_marker(skip_live)


@pytest.fixture
def seeded_pc_db(tmp_path: Path) -> Iterator[ReadOnlyDB]:
    """A connected, read-only ``ReadOnlyDB`` over the seeded P&C eval schema."""
    url = f"sqlite:///{tmp_path / 'pc_eval.db'}"
    seed_pc_schema(url)
    db = ReadOnlyDB(url)
    db.connect()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def governance_cases() -> list[GovernanceCase]:
    return load_governance_cases()


@pytest.fixture
def sql_cases() -> list[SqlCase]:
    return load_sql_cases()
