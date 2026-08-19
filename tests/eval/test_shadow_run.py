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

from dataclasses import dataclass, field
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


@dataclass
class _StubGovernanceSweep:
    """The shape ``measure_provider`` reads off the governance sweep."""

    cycle_matches: list[bool] = field(default_factory=list)
    risk_acceptable: list[bool] = field(default_factory=list)
    laxer_misses: int = 0
    seam_failures: int = 0
    transient_retries: int = 0
    excluded_transient: int = 0


class _StubIntakeClient:
    """Enough of ``IntakeLLMClient`` for the driver's *wiring* to be walked.

    Only ``classify_governance`` is needed: the driver binds it as a method
    reference for the governance sweep. It is never *called* — the governance
    corpus is emptied by the fixture — so it deliberately raises rather than
    returning canned output, which keeps this double from quietly becoming a
    provider impersonator.
    """

    def classify_governance(self, draft: object) -> object:  # pragma: no cover
        raise AssertionError("the wiring tests must never spend a governance call")


@pytest.fixture
def recorded_data_clients(monkeypatch: pytest.MonkeyPatch) -> list[_RecordedCall]:
    """Neutralize every seam ``measure_provider`` touches; record client builds.

    The corpus loaders are emptied rather than the clients being made to return
    canned output: an empty corpus means the driver's per-case loops never run,
    so no stub has to impersonate a provider's JSON. What remains exercised is
    exactly the wiring under test — how the clients are constructed.

    The intake stub is nonetheless **client-shaped** (Session 225): the driver
    hands ``intake.classify_governance`` to ``sweep_governance_agreement`` as a
    bound method, so the attribute is dereferenced before the (empty) corpus is
    walked. A bare ``object()`` stub raised ``AttributeError`` there — a defect
    in the double, not in the driver, but one only this fixture can see.
    """
    calls: list[_RecordedCall] = []

    def _fake_data_client(provider: str, **kwargs: Any) -> object:
        calls.append(_RecordedCall(provider=provider, kwargs=kwargs))
        return object()

    monkeypatch.setattr(shadow_run, "make_data_client", _fake_data_client)
    monkeypatch.setattr(shadow_run, "make_intake_client", lambda *a, **k: _StubIntakeClient())
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


def test_the_governance_sweep_is_given_an_event_sink(
    seeded_pc_db: ReadOnlyDB,
    recorded_data_clients: list[_RecordedCall],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Without ``on_event`` every retry and exclusion note is silently dropped.

    That is the Session 221 defect this driver's SQL call site had for three
    sessions and its governance call site had from the start: the sweep's
    ``notify`` defaults to a no-op, so the ``str(exc)`` that makes a live failure
    attributable at all goes nowhere. Pinned here because no deterministic test
    can otherwise see it — the sweep is silent by design when the sink is absent.
    """
    seen: dict[str, object] = {}

    monkeypatch.setattr(
        shadow_run,
        "sweep_governance_agreement",
        lambda *a, **k: (seen.update(k), _StubGovernanceSweep())[1],
    )

    shadow_run.measure_provider("anthropic", seeded_pc_db, n_samples=1)

    assert seen["on_event"] is shadow_run._warn
