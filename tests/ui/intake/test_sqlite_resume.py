"""Resume-across-restart test — the core DONE criterion for Phase 3B.

The app is torn down and a brand-new ``create_app`` instance is pointed at
the same SQLite file. The session should resume at the same interrupt.
"""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from model_project_constructor.agents.intake.fixture import (
    FixtureLLMClient,
    answers_from_fixture,
    load_fixture,
)
from model_project_constructor.ui.intake import create_app


def test_resume_after_restart(tmp_path: Path) -> None:
    db = tmp_path / "resume.db"
    fixture = load_fixture("tests/fixtures/subrogation.yaml")

    def factory(_sid: str) -> FixtureLLMClient:
        return FixtureLLMClient(fixture)

    # --- first process ---
    app1 = create_app(llm_factory=factory, db_path=db)
    client1 = TestClient(app1)
    client1.post(
        "/sessions",
        data={"stakeholder_id": "alice", "session_id": "resume-x"},
    )

    # Answer the first 2 questions, then "crash".
    answers = answers_from_fixture(fixture)
    client1.post(
        "/sessions/resume-x/answer",
        data={"answer": answers[0]},
    )
    client1.post(
        "/sessions/resume-x/answer",
        data={"answer": answers[1]},
    )
    state1 = client1.get("/sessions/resume-x/state.json").json()
    assert state1["phase"] == "question"
    q_number_before_restart = state1["question_number"]
    assert q_number_before_restart == 3

    client1.close()
    app1.state.store.close()
    del app1
    del client1

    # --- second process — new app, same DB ---
    app2 = create_app(llm_factory=factory, db_path=db)
    client2 = TestClient(app2)

    state2 = client2.get("/sessions/resume-x/state.json").json()
    assert state2["phase"] == "question"
    assert state2["question_number"] == q_number_before_restart
    assert state2["session_id"] == "resume-x"

    # Finish the interview in the second process.
    for answer in answers[2:]:
        resp = client2.post(
            "/sessions/resume-x/answer",
            data={"answer": answer},
        )
        assert resp.status_code == 200
        if "Review draft" in resp.text:
            break

    resp = client2.post("/sessions/resume-x/review", data={"review": "accept"})
    assert resp.status_code == 200
    assert "Intake COMPLETE" in resp.text

    report = client2.get("/sessions/resume-x/report.json").json()
    assert report["status"] == "COMPLETE"

    client2.close()
    app2.state.store.close()
