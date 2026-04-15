"""SSE smoke test for the intake web UI.

We use ``TestClient.stream`` to read the first snapshot event emitted by
``/sessions/{id}/events`` and confirm it carries a phase-tagged payload.
"""

from __future__ import annotations

import json

from fastapi.testclient import TestClient


def test_sse_emits_initial_snapshot(subrogation_client: TestClient) -> None:
    subrogation_client.post(
        "/sessions",
        data={"stakeholder_id": "alice", "session_id": "sse-alpha"},
    )

    with subrogation_client.stream(
        "GET",
        "/sessions/sse-alpha/events",
    ) as resp:
        assert resp.status_code == 200
        ctype = resp.headers.get("content-type", "")
        assert "text/event-stream" in ctype
        data_line: str | None = None
        for raw in resp.iter_lines():
            # ``iter_lines`` in httpx yields ``str``.
            line = raw if isinstance(raw, str) else raw.decode()
            if line.startswith("data:"):
                data_line = line[len("data:") :].strip()
                break
        assert data_line is not None
        payload = json.loads(data_line)
        assert payload["session_id"] == "sse-alpha"
        assert payload["phase"] == "question"
        assert payload["question_number"] == 1


def test_sse_returns_event_stream_content_type(
    subrogation_client: TestClient,
) -> None:
    subrogation_client.post(
        "/sessions",
        data={"stakeholder_id": "alice", "session_id": "sse-ct"},
    )
    with subrogation_client.stream(
        "GET",
        "/sessions/sse-ct/events",
    ) as resp:
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers.get("content-type", "")
