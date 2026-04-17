"""Direct tests for ``IntakeSessionStore`` (runner.py).

These exercise the session store without the HTTP layer so failures point
at the driver, not at FastAPI wiring.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from model_project_constructor.agents.intake.fixture import (
    FixtureLLMClient,
    load_fixture,
)
from model_project_constructor.ui.intake.runner import (
    CAPS,
    IntakeSessionStore,
    InvalidPhaseError,
    SessionSnapshot,
)


def _store(tmp_path: Path, fixture_path: str) -> IntakeSessionStore:
    fixture = load_fixture(fixture_path)
    return IntakeSessionStore(
        db_path=tmp_path / "runner.db",
        llm_factory=lambda _sid: FixtureLLMClient(fixture),
    )


def test_caps_constants_exposed() -> None:
    from model_project_constructor.agents.intake import MAX_QUESTIONS, MAX_REVISIONS

    assert CAPS == {
        "max_questions": MAX_QUESTIONS,
        "max_revisions": MAX_REVISIONS,
    }


def test_snapshot_for_missing_session(tmp_path: Path) -> None:
    store = _store(tmp_path, "tests/fixtures/subrogation.yaml")
    try:
        snap = store.get_snapshot("nope")
        assert snap.phase == "not_started"
        assert snap.session_id == "nope"
    finally:
        store.close()


def test_has_session_false_then_true(tmp_path: Path) -> None:
    store = _store(tmp_path, "tests/fixtures/subrogation.yaml")
    try:
        assert store.has_session("hs") is False
        store.start_session(stakeholder_id="alice", session_id="hs")
        assert store.has_session("hs") is True
    finally:
        store.close()


def test_start_session_returns_question_snapshot(tmp_path: Path) -> None:
    store = _store(tmp_path, "tests/fixtures/subrogation.yaml")
    try:
        snap = store.start_session(stakeholder_id="alice", session_id="s1")
        assert isinstance(snap, SessionSnapshot)
        assert snap.phase == "question"
        assert snap.question_number == 1
        assert snap.question
    finally:
        store.close()


def test_answer_wrong_phase_raises(tmp_path: Path) -> None:
    store = _store(tmp_path, "tests/fixtures/subrogation.yaml")
    try:
        with pytest.raises(InvalidPhaseError):
            store.answer("ghost", "hello")
    finally:
        store.close()


def test_review_wrong_phase_raises(tmp_path: Path) -> None:
    store = _store(tmp_path, "tests/fixtures/subrogation.yaml")
    try:
        store.start_session(stakeholder_id="alice", session_id="rw")
        with pytest.raises(InvalidPhaseError):
            store.review("rw", "accept")
    finally:
        store.close()
