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
from tests.eval.eval_cutover import CHECK_KEYS


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

    The sweep's ``notify`` defaults to a no-op, so a call site that omits the
    sink discards every retry and exclusion note — including the ``str(exc)``
    that makes a live failure attributable at all. That defect was real and cost
    three sessions to find, but it was ``test_eval_live``'s SQL call site, not
    this driver's: ``shadow_run`` has passed ``_warn`` to the SQL sweep since
    Session 218 (``4e2c8ec``), as ``test_eval_live.py`` itself records. This
    driver's *governance* call site had no sweep at all before Session 225 — its
    hand-written loop did call ``_warn``, just without ``str(exc)``.

    Pinned here because no deterministic test can otherwise see the omission:
    the sweep is silent by design when the sink is absent.
    """
    seen: dict[str, object] = {}

    monkeypatch.setattr(
        shadow_run,
        "sweep_governance_agreement",
        lambda *a, **k: (seen.update(k), _StubGovernanceSweep())[1],
    )

    shadow_run.measure_provider("anthropic", seeded_pc_db, n_samples=1)

    assert seen["on_event"] is shadow_run._warn


def test_governance_results_reach_their_gate_keys_unswapped(
    seeded_pc_db: ReadOnlyDB,
    recorded_data_clients: list[_RecordedCall],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The six-field mapping from sweep result to measured keys, pinned.

    ``measure_provider`` is reachable by no other test in the tree, so without
    this the rewritten mapping is invisible: a stub returning all-default values
    cannot tell ``governance_laxer_miss`` wired to ``laxer_misses`` apart from it
    wired to ``seam_failures``. That key is the zero-tolerance gate row
    (``GOVERNANCE_LAXER_MISSES_MAX = 0``) and "a seam failure must never feed it"
    is this change's whole thesis — tested at the sweep level, and here at the
    level where the number actually reaches ``evaluate_cutover``. Every value
    below is distinct so no two fields can be swapped without failing.
    """
    monkeypatch.setattr(
        shadow_run,
        "sweep_governance_agreement",
        lambda *a, **k: _StubGovernanceSweep(
            cycle_matches=[True, True, True, False],  # 3/4 = 0.75
            risk_acceptable=[True, False],  # 1/2 = 0.5
            laxer_misses=7,
            seam_failures=3,
            transient_retries=11,
            excluded_transient=2,
        ),
    )

    measured = shadow_run.measure_provider("anthropic", seeded_pc_db, n_samples=1)

    assert measured["governance_cycle_time_agreement"] == 0.75
    assert measured["governance_risk_tier_acceptable"] == 0.5
    assert measured["governance_laxer_miss"] == 7.0
    assert measured["governance_seam_failures"] == 3.0
    assert measured["governance_transient_retries"] == 11.0
    assert measured["governance_excluded_transient"] == 2.0


def test_the_governance_diagnostics_are_not_mistaken_for_gate_keys() -> None:
    """Extra keys in the measured mapping must not enter the §3.4 gate.

    ``eval_cutover`` reads a fixed key set and ignores the rest; this pins that
    the three diagnostics Session 225 added stayed out of it, so a future reader
    cannot mistake them for thresholds nobody set.
    """
    added = {
        "governance_seam_failures",
        "governance_excluded_transient",
        "governance_transient_retries",
    }

    assert added.isdisjoint(set(CHECK_KEYS))
