"""Happy-path tests for the intake web UI — subrogation end-to-end."""

from __future__ import annotations

from fastapi.testclient import TestClient

from model_project_constructor.agents.intake.fixture import (
    answers_from_fixture,
)


def _drive_to_review(
    client: TestClient,
    session_id: str,
    fixture: dict,
) -> None:
    answers = answers_from_fixture(fixture)
    for answer in answers:
        resp = client.post(
            f"/sessions/{session_id}/answer",
            data={"answer": answer},
        )
        assert resp.status_code == 200, resp.text
        if "Review draft" in resp.text:
            return
    raise AssertionError(
        "Interview never reached the review phase within the scripted answers."
    )


def test_healthz_ok(subrogation_client: TestClient) -> None:
    resp = subrogation_client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_index_page_renders_start_form(subrogation_client: TestClient) -> None:
    resp = subrogation_client.get("/")
    assert resp.status_code == 200
    body = resp.text
    assert "Model Project Intake" in body
    assert "stakeholder_id" in body
    assert "/sessions" in body


def test_resume_form_page_renders(subrogation_client: TestClient) -> None:
    resp = subrogation_client.get("/sessions/")
    assert resp.status_code == 200
    assert "Resume Interview" in resp.text
    assert "/sessions/resume" in resp.text


def test_resume_lookup_redirects_to_session(subrogation_client: TestClient) -> None:
    resp = subrogation_client.get(
        "/sessions/resume",
        params={"session_id": "sub-alpha"},
        follow_redirects=False,
    )
    assert resp.status_code == 303
    assert resp.headers["location"] == "/sessions/sub-alpha"


def test_not_started_session_renders_placeholder(
    subrogation_client: TestClient,
) -> None:
    resp = subrogation_client.get("/sessions/no-such-session")
    assert resp.status_code == 200
    assert "Session not started" in resp.text


def test_create_session_redirects_and_starts_interview(
    subrogation_client: TestClient,
    subrogation_fixture: dict,
) -> None:
    resp = subrogation_client.post(
        "/sessions",
        data={
            "stakeholder_id": "alice",
            "session_id": "sub-alpha",
            "initial_problem": "Subrogation outcomes dropped",
        },
        follow_redirects=False,
    )
    assert resp.status_code == 303
    assert resp.headers["location"] == "/sessions/sub-alpha"

    # The redirect target should be rendering the first interview question.
    page = subrogation_client.get("/sessions/sub-alpha")
    assert page.status_code == 200
    assert "Question 1 of up to 10" in page.text
    assert "/sessions/sub-alpha/answer" in page.text


def test_create_session_auto_generates_id_when_blank(
    subrogation_client: TestClient,
) -> None:
    resp = subrogation_client.post(
        "/sessions",
        data={"stakeholder_id": "alice", "session_id": ""},
        follow_redirects=False,
    )
    assert resp.status_code == 303
    loc = resp.headers["location"]
    assert loc.startswith("/sessions/intake-")


def test_end_to_end_subrogation_completes(
    subrogation_client: TestClient,
    subrogation_fixture: dict,
) -> None:
    subrogation_client.post(
        "/sessions",
        data={"stakeholder_id": "alice", "session_id": "sub-e2e"},
    )
    _drive_to_review(subrogation_client, "sub-e2e", subrogation_fixture)

    # Submit an accepting review.
    resp = subrogation_client.post(
        "/sessions/sub-e2e/review",
        data={"review": "accept"},
    )
    assert resp.status_code == 200
    assert "Intake COMPLETE" in resp.text

    # report.json exposes the validated report.
    rep = subrogation_client.get("/sessions/sub-e2e/report.json")
    assert rep.status_code == 200
    data = rep.json()
    assert data["status"] == "COMPLETE"
    assert data["governance"]["cycle_time"] in {
        "continuous",
        "strategic",
        "tactical",
    }

    # state.json reports the complete phase.
    state = subrogation_client.get("/sessions/sub-e2e/state.json")
    assert state.status_code == 200
    assert state.json()["phase"] == "complete"


def test_report_json_rejects_in_question_phase(
    subrogation_client: TestClient,
) -> None:
    subrogation_client.post(
        "/sessions",
        data={"stakeholder_id": "alice", "session_id": "sub-early"},
    )
    resp = subrogation_client.get("/sessions/sub-early/report.json")
    assert resp.status_code == 409


def test_answer_rejected_in_review_phase(
    subrogation_client: TestClient,
    subrogation_fixture: dict,
) -> None:
    subrogation_client.post(
        "/sessions",
        data={"stakeholder_id": "alice", "session_id": "sub-phase"},
    )
    _drive_to_review(subrogation_client, "sub-phase", subrogation_fixture)
    resp = subrogation_client.post(
        "/sessions/sub-phase/answer",
        data={"answer": "I should not be accepted here"},
    )
    assert resp.status_code == 409


def test_review_rejected_in_question_phase(
    subrogation_client: TestClient,
) -> None:
    subrogation_client.post(
        "/sessions",
        data={"stakeholder_id": "alice", "session_id": "sub-phase2"},
    )
    resp = subrogation_client.post(
        "/sessions/sub-phase2/review",
        data={"review": "accept"},
    )
    assert resp.status_code == 409
