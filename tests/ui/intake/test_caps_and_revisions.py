"""Tests covering 10-question and 3-revision caps via the web UI."""

from __future__ import annotations

from collections.abc import Callable

from fastapi.testclient import TestClient

from model_project_constructor.agents.intake.fixture import (
    answers_from_fixture,
    review_sequence_from_fixture,
)


def _drive_to_review(client: TestClient, session_id: str, fixture: dict) -> None:
    for answer in answers_from_fixture(fixture):
        resp = client.post(
            f"/sessions/{session_id}/answer",
            data={"answer": answer},
        )
        assert resp.status_code == 200, resp.text
        if "Review draft" in resp.text:
            return
    raise AssertionError("Review phase never reached.")


def test_question_cap_triggers_draft_incomplete(
    question_cap_fixture: dict,
    make_client: Callable[[dict], TestClient],
) -> None:
    client = make_client(question_cap_fixture)
    client.post("/sessions", data={"stakeholder_id": "cap", "session_id": "q-cap"})
    _drive_to_review(client, "q-cap", question_cap_fixture)

    resp = client.post("/sessions/q-cap/review", data={"review": "accept"})
    assert resp.status_code == 200

    state = client.get("/sessions/q-cap/state.json").json()
    assert state["phase"] == "complete"
    assert state["status"] == "DRAFT_INCOMPLETE"
    assert "questions_cap_reached" in (state["missing_fields"] or [])


def test_revision_cap_triggers_draft_incomplete(
    revision_cap_fixture: dict,
    make_client: Callable[[dict], TestClient],
) -> None:
    client = make_client(revision_cap_fixture)
    client.post("/sessions", data={"stakeholder_id": "rev", "session_id": "r-cap"})
    _drive_to_review(client, "r-cap", revision_cap_fixture)

    # Submit each scripted review response; the fixture is designed so
    # all of them are rejections, and after MAX_REVISIONS the graph
    # finalizes anyway with DRAFT_INCOMPLETE.
    reviews = review_sequence_from_fixture(revision_cap_fixture)
    for i, review_text in enumerate(reviews):
        resp = client.post(
            f"/sessions/r-cap/review",
            data={"review": review_text},
        )
        assert resp.status_code == 200, resp.text
        if "Intake" in resp.text and "COMPLETE" in resp.text.upper():
            break
        if i >= 10:
            raise AssertionError("Revision loop never terminated.")

    state = client.get("/sessions/r-cap/state.json").json()
    assert state["phase"] == "complete"
    assert state["status"] == "DRAFT_INCOMPLETE"
    assert "revision_cap_reached" in (state["missing_fields"] or [])
