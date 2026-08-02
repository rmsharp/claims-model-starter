"""Deterministic tests for the Phase E shadow-run driver's *wiring*.

``shadow_run.measure_provider`` is normally exercised only by spending money, and
``test_eval_live.py`` auto-skips without credentials — so every line in the driver
is green-badged and unexercised in CI. That is precisely how Session 215's
harness defect survived (learning #71): the driver could not drive the
``opencode`` provider at all, and no test could see it.

These tests run the driver with **every** LLM seam and corpus loader stubbed, so
they make zero API calls and assert only what the driver hands to its
collaborators. The load-bearing assertion is that the data client is told the
dialect of the database its SQL will be executed against — the Session 216
finding. Without it ``sql_exec`` measures dialect mismatch, and it does so
silently: the SQL still parses, still returns, and only the rate moves.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest
from model_project_constructor_data_agent.db import ReadOnlyDB

from tests.eval import shadow_run


@dataclass
class _RecordedCall:
    provider: str
    kwargs: dict[str, Any]


@dataclass
class _StubSweep:
    convergence_results: list[bool]
    premature_count: int


@pytest.fixture
def recorded_data_clients(monkeypatch: pytest.MonkeyPatch) -> list[_RecordedCall]:
    """Neutralize every seam ``measure_provider`` touches; record client builds.

    The corpus loaders are emptied rather than the clients being made to return
    canned output: an empty corpus means the driver's per-case loops never run,
    so no stub has to impersonate a provider's JSON. What remains exercised is
    exactly the wiring under test — how the clients are constructed.
    """
    calls: list[_RecordedCall] = []

    def _fake_data_client(provider: str, **kwargs: Any) -> object:
        calls.append(_RecordedCall(provider=provider, kwargs=kwargs))
        return object()

    monkeypatch.setattr(shadow_run, "make_data_client", _fake_data_client)
    monkeypatch.setattr(shadow_run, "make_intake_client", lambda *a, **k: object())
    monkeypatch.setattr(shadow_run, "provider_eval_model", lambda _p: "pinned-model")
    # Inventory building reflects a *connected* DB; the dialect deliberately does
    # not, which is what lets the unreachable-warehouse case below exist at all.
    monkeypatch.setattr(shadow_run, "pc_inventory_from_db", lambda _db: None)
    monkeypatch.setattr(shadow_run, "load_governance_cases", list)
    monkeypatch.setattr(shadow_run, "load_sql_cases", list)
    monkeypatch.setattr(shadow_run, "load_interview_cases", list)
    monkeypatch.setattr(
        shadow_run,
        "sweep_interview_convergence",
        lambda *a, **k: _StubSweep(convergence_results=[], premature_count=0),
    )
    return calls


def test_data_client_is_told_the_dialect_of_the_execution_target(
    seeded_pc_db: ReadOnlyDB, recorded_data_clients: list[_RecordedCall]
) -> None:
    shadow_run.measure_provider("anthropic", seeded_pc_db, n_samples=1)

    assert len(recorded_data_clients) == 1
    assert recorded_data_clients[0].kwargs["sql_dialect"] == "sqlite"


def test_dialect_is_derived_from_the_db_not_hardcoded(
    tmp_path: Any, recorded_data_clients: list[_RecordedCall]
) -> None:
    """A different execution target must produce a different prompt.

    Hardcoding ``"sqlite"`` in the driver would pass the test above and still be
    wrong — it would silently mislabel the dialect the moment the eval ran
    against anything else. Pointing the driver at a non-SQLite URL proves the
    value tracks the database.
    """
    warehouse = ReadOnlyDB("postgresql://user:pw@warehouse.internal/claims")

    shadow_run.measure_provider("anthropic", warehouse, n_samples=1)

    assert recorded_data_clients[0].kwargs["sql_dialect"] == "postgresql"


def test_seeded_eval_db_reports_sqlite(seeded_pc_db: ReadOnlyDB) -> None:
    """Pins the actual value the harness now sends for the real eval corpus.

    ``pc_schema.sql`` and every ``reference_sql`` in ``sql_cases.yaml`` are
    authored SQLite-only; this asserts the dialect the prompt advertises matches
    that authoring constraint.
    """
    assert seeded_pc_db.dialect == "sqlite"
