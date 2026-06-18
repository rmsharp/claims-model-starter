"""FastAPI application for the Intake Agent Web UI (architecture-plan §9.3).

This module owns the HTTP surface:

* ``GET /`` — landing page with the start-interview form.
* ``POST /sessions`` — start a new interview, redirect to its page.
* ``GET /sessions/{session_id}`` — render current phase (question / review /
  complete).
* ``POST /sessions/{session_id}/answer`` — submit an interview answer.
* ``POST /sessions/{session_id}/review`` — submit a draft review.
* ``GET /sessions/{session_id}/report.json`` — JSON ``IntakeReport`` once
  the session is complete.
* ``GET /sessions/{session_id}/events`` — SSE stream of phase snapshots.
* ``GET /healthz`` — liveness probe.

The graph and session store live in ``runner.py``. This module never
touches the graph directly — it only drives the store.

For production, the app builds its client via
:func:`agents.intake.factory.make_llm_client`. The provider and model are
selectable per deployment — a ``create_app`` argument, then the
``INTAKE_LLM_PROVIDER`` / ``INTAKE_LLM_MODEL`` environment variables, then
the defaults (``DEFAULT_LLM_PROVIDER`` — ``anthropic`` — and the provider's
own default model). Any ``KNOWN_PROVIDERS`` member (e.g. ``bedrock``) is
reachable. For tests, ``create_app`` accepts an ``llm_factory`` so fixtures
can be plugged in, bypassing provider resolution entirely.
"""

from __future__ import annotations

import json
import os
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from sse_starlette.sse import EventSourceResponse

from model_project_constructor.agents.intake.protocol import IntakeLLMClient
from model_project_constructor.ui.intake import templates
from model_project_constructor.ui.intake.runner import (
    IntakeSessionStore,
    InvalidPhaseError,
    LLMFactory,
    SessionSnapshot,
)

DEFAULT_DB_PATH = "intake_sessions.db"


def _resolve_provider(provider: str | None) -> str:
    """Resolve the LLM provider for the production factory.

    Precedence mirrors the ``db_path`` resolution in :func:`create_app`: an
    explicit ``create_app(provider=...)`` argument, then the
    ``INTAKE_LLM_PROVIDER`` environment variable, then the orchestrator
    default (:data:`DEFAULT_LLM_PROVIDER`, currently ``"anthropic"``). The
    resolved value is validated against the intake factory's
    ``KNOWN_PROVIDERS`` so a misconfigured deployment fails here, at app
    construction, with a clear message rather than at the first interview.

    The two imports are intentionally local: both modules are SDK-free, so
    this keeps building the app free of the provider SDK (the lazy-import
    property pinned by ``test_factory_import_does_not_load_anthropic``).
    """

    from model_project_constructor.agents.intake.factory import KNOWN_PROVIDERS
    from model_project_constructor.orchestrator.config import DEFAULT_LLM_PROVIDER

    resolved = provider or os.environ.get("INTAKE_LLM_PROVIDER") or DEFAULT_LLM_PROVIDER
    if resolved not in KNOWN_PROVIDERS:
        raise ValueError(
            f"Unknown LLM provider {resolved!r}. "
            f"Known providers: {', '.join(KNOWN_PROVIDERS)}."
        )
    return resolved


def _resolve_model(model: str | None) -> str | None:
    """Resolve the optional model override for the production factory.

    Precedence: an explicit ``create_app(model=...)`` argument, then the
    ``INTAKE_LLM_MODEL`` environment variable, else ``None``. ``None`` is the
    deliberate default: it lets :func:`make_llm_client` pick each provider's
    own default model, so selecting ``bedrock`` yields the
    ``anthropic.``-prefixed id rather than a first-party id that would 400 on
    Bedrock (the cross-provider model-id gap documented in the plan's Phase C).
    """

    return model or os.environ.get("INTAKE_LLM_MODEL") or None


def _make_default_llm_factory(provider: str, model: str | None) -> LLMFactory:
    """Build the production LLM factory bound to ``provider`` / ``model``.

    Returns an :data:`LLMFactory` closure: the provider/model are captured
    once at app construction, while the concrete client is still built lazily,
    per session, inside :meth:`IntakeSessionStore._get_graph`. Routing through
    :func:`agents.intake.factory.make_llm_client` honors the provider seam
    (E4); the import stays inside the closure so building the app never
    triggers the provider SDK import.
    """

    def factory(_session_id: str) -> IntakeLLMClient:
        from model_project_constructor.agents.intake.factory import make_llm_client

        return make_llm_client(provider, model=model)

    return factory


def create_app(
    *,
    llm_factory: LLMFactory | None = None,
    db_path: str | Path | None = None,
    provider: str | None = None,
    model: str | None = None,
) -> FastAPI:
    """Build a FastAPI app with an isolated session store.

    Tests should call this with a fixture-backed ``llm_factory`` and a
    per-test ``db_path``. Production uses the module-level ``app`` below.

    ``provider`` / ``model`` choose the LLM backend for the *production*
    factory and are ignored when an explicit ``llm_factory`` is injected.
    Each resolves from its argument, then an environment variable
    (``INTAKE_LLM_PROVIDER`` / ``INTAKE_LLM_MODEL``), then a default — the
    orchestrator's ``DEFAULT_LLM_PROVIDER`` (``anthropic``) for the provider
    and the provider's own default model (``None``) for the model. Any
    ``KNOWN_PROVIDERS`` member (e.g. ``bedrock``) is selectable; an unknown
    provider raises ``ValueError`` here, before any session starts.
    """

    if llm_factory is not None:
        resolved_factory: LLMFactory = llm_factory
    else:
        resolved_factory = _make_default_llm_factory(
            _resolve_provider(provider), _resolve_model(model)
        )
    resolved_db = str(db_path or os.environ.get("INTAKE_DB_PATH", DEFAULT_DB_PATH))

    store = IntakeSessionStore(db_path=resolved_db, llm_factory=resolved_factory)

    @asynccontextmanager
    async def lifespan(
        _fastapi_app: FastAPI,
    ) -> AsyncIterator[None]:  # pragma: no cover - exercised by uvicorn
        try:
            yield
        finally:
            store.close()

    fastapi_app = FastAPI(
        title="Model Project Intake",
        version="0.1.0",
        lifespan=lifespan,
    )
    fastapi_app.state.store = store

    # ---- routes ---------------------------------------------------------

    @fastapi_app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @fastapi_app.get("/", response_class=HTMLResponse)
    def index() -> HTMLResponse:
        return HTMLResponse(templates.render_index())

    @fastapi_app.get("/sessions/", response_class=HTMLResponse)
    def resume_form() -> HTMLResponse:
        return HTMLResponse(templates.render_resume_form())

    @fastapi_app.get("/sessions/resume")
    def resume_lookup(session_id: str) -> RedirectResponse:
        return RedirectResponse(
            url=f"/sessions/{session_id}",
            status_code=303,
        )

    @fastapi_app.post("/sessions")
    def create_session(
        stakeholder_id: str = Form(...),
        session_id: str = Form(""),
        domain: str = Form("pc_claims"),
        initial_problem: str = Form(""),
    ) -> RedirectResponse:
        sid = session_id.strip() or f"intake-{uuid.uuid4().hex[:12]}"
        store.start_session(
            stakeholder_id=stakeholder_id,
            session_id=sid,
            domain=domain or "pc_claims",
            initial_problem=initial_problem or None,
        )
        return RedirectResponse(url=f"/sessions/{sid}", status_code=303)

    @fastapi_app.get("/sessions/{session_id}", response_class=HTMLResponse)
    def get_session(session_id: str) -> HTMLResponse:
        snap = store.get_snapshot(session_id)
        return HTMLResponse(templates.render_session(snap))

    @fastapi_app.post("/sessions/{session_id}/answer", response_class=HTMLResponse)
    def post_answer(session_id: str, answer: str = Form(...)) -> HTMLResponse:
        try:
            snap = store.answer(session_id, answer)
        except InvalidPhaseError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return HTMLResponse(templates.render_session(snap))

    @fastapi_app.post("/sessions/{session_id}/review", response_class=HTMLResponse)
    def post_review(session_id: str, review: str = Form(...)) -> HTMLResponse:
        try:
            snap = store.review(session_id, review)
        except InvalidPhaseError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return HTMLResponse(templates.render_session(snap))

    @fastapi_app.get("/sessions/{session_id}/report.json")
    def get_report(session_id: str) -> Response:
        snap = store.get_snapshot(session_id)
        if snap.phase != "complete" or snap.report is None:
            raise HTTPException(
                status_code=409,
                detail=f"Session {session_id!r} is in phase {snap.phase!r}, no report yet.",
            )
        return JSONResponse(content=json.loads(snap.report.model_dump_json()))

    @fastapi_app.get("/sessions/{session_id}/state.json")
    def get_state(session_id: str) -> dict[str, Any]:
        snap = store.get_snapshot(session_id)
        return _snapshot_to_dict(snap)

    @fastapi_app.get("/sessions/{session_id}/events")
    async def session_events(session_id: str) -> EventSourceResponse:
        """Emit the current session snapshot as a single SSE event.

        This is deliberately a one-shot stream: the HTTP layer is the only
        thing that can advance the graph, so clients who care about
        subsequent phases can reconnect after each form submission (HTMX
        handles this naturally via ``hx-sse``) or poll ``/state.json``.
        A one-shot design keeps the endpoint cleanly unit-testable and
        avoids lifecycle hazards under ``TestClient``.
        """

        async def event_stream() -> AsyncIterator[dict[str, str]]:
            snap = store.get_snapshot(session_id)
            payload = json.dumps(_snapshot_to_dict(snap), sort_keys=True)
            yield {"event": "snapshot", "data": payload}

        return EventSourceResponse(event_stream())

    return fastapi_app


def _snapshot_to_dict(snap: SessionSnapshot) -> dict[str, Any]:
    return {
        "session_id": snap.session_id,
        "phase": snap.phase,
        "question": snap.question,
        "question_number": snap.question_number,
        "draft_fields": snap.draft_fields,
        "governance_fields": snap.governance_fields,
        "revision_cycles": snap.revision_cycles,
        "status": snap.status,
        "missing_fields": snap.missing_fields,
    }


# Module-level app for ``uvicorn model_project_constructor.ui.intake:app``.
# Resolves the provider/model from INTAKE_LLM_PROVIDER / INTAKE_LLM_MODEL (or
# the DEFAULT_LLM_PROVIDER — anthropic — and the provider's own default model),
# and the SQLite path from INTAKE_DB_PATH.
app = create_app()
