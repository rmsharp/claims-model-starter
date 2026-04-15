"""Session store + HTTP-driven graph runner for the Intake Web UI.

Phase 3B of architecture-plan. The compiled intake graph from Phase 3A is
reused verbatim (``build_intake_graph``); this module only adds the pieces
that make it drivable one HTTP request at a time:

* a shared ``SqliteSaver`` so interview state survives server restart,
* a per-session compiled graph bound to a per-session LLM client (via a
  factory the app owns),
* ``start_session`` / ``resume_session`` primitives that advance the graph
  until the next interrupt and return a snapshot the HTTP layer can render.

The HTTP layer (``app.py``) should never touch the graph directly — it
should only call these primitives.
"""

from __future__ import annotations

import sqlite3
import threading
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import Command

from model_project_constructor.agents.intake import (
    MAX_QUESTIONS,
    MAX_REVISIONS,
    build_intake_graph,
    build_intake_report,
    initial_state,
)
from model_project_constructor.agents.intake.protocol import IntakeLLMClient
from model_project_constructor.schemas.v1.intake import IntakeReport

LLMFactory = Callable[[str], IntakeLLMClient]


@dataclass
class SessionSnapshot:
    """View of an intake session for the HTTP layer.

    ``phase`` is one of:

    * ``"question"`` — the graph is paused on an ``ask_user`` interrupt;
      ``question`` / ``question_number`` describe what to show.
    * ``"review"`` — the graph is paused on an ``await_review`` interrupt;
      ``draft_fields`` / ``governance_fields`` / ``revision_cycles``
      describe the draft being reviewed.
    * ``"complete"`` — the graph reached ``finalize``; ``report`` is a
      validated ``IntakeReport``.
    """

    session_id: str
    phase: str
    question: str | None = None
    question_number: int | None = None
    draft_fields: dict[str, Any] | None = None
    governance_fields: dict[str, Any] | None = None
    revision_cycles: int = 0
    report: IntakeReport | None = None
    status: str | None = None
    missing_fields: list[str] | None = None


class IntakeSessionStore:
    """Singleton session store for the intake web UI.

    Owns a single ``SqliteSaver`` backed by ``db_path`` and a cache of
    per-session compiled graphs. The LLM client for a session is produced
    by ``llm_factory(session_id)``; in production this returns an
    ``AnthropicLLMClient``, in tests a ``FixtureLLMClient``.
    """

    def __init__(self, *, db_path: str | Path, llm_factory: LLMFactory) -> None:
        self.db_path = str(db_path)
        self.llm_factory = llm_factory
        # ``check_same_thread=False`` because FastAPI runs sync endpoints on
        # a threadpool. ``SqliteSaver`` itself uses a single shared
        # connection, so we guard every call with a reentrant lock.
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._lock = threading.RLock()
        self._saver = SqliteSaver(self._conn)
        self._saver.setup()
        self._graphs: dict[str, Any] = {}
        self._llms: dict[str, IntakeLLMClient] = {}

    # -- lifecycle ---------------------------------------------------------

    def close(self) -> None:
        with self._lock:
            self._conn.close()
            self._graphs.clear()
            self._llms.clear()

    # -- internal helpers --------------------------------------------------

    def _get_graph(self, session_id: str) -> Any:
        graph = self._graphs.get(session_id)
        if graph is None:
            llm = self.llm_factory(session_id)
            graph = build_intake_graph(llm, checkpointer=self._saver)
            self._graphs[session_id] = graph
            self._llms[session_id] = llm
        return graph

    def _config(self, session_id: str) -> dict[str, Any]:
        return {"configurable": {"thread_id": session_id}}

    def _snapshot(self, session_id: str) -> SessionSnapshot:
        graph = self._get_graph(session_id)
        config = self._config(session_id)
        state = graph.get_state(config)

        # If there's an active interrupt, report that phase.
        if state.tasks:
            task = state.tasks[0]
            interrupts = getattr(task, "interrupts", ())
            if interrupts:
                payload = interrupts[0].value or {}
                kind = payload.get("kind") if isinstance(payload, dict) else None
                if kind == "question":
                    return SessionSnapshot(
                        session_id=session_id,
                        phase="question",
                        question=payload.get("question"),
                        question_number=payload.get("question_number"),
                    )
                if kind == "review":
                    return SessionSnapshot(
                        session_id=session_id,
                        phase="review",
                        draft_fields=payload.get("draft_fields"),
                        governance_fields=payload.get("governance_fields"),
                        revision_cycles=int(payload.get("revision_cycles", 0)),
                    )

        # Otherwise the graph is at rest — either finalized or a blank
        # thread that hasn't been started. Distinguish by checking the
        # ``status`` field the ``finalize`` node writes.
        values = state.values or {}
        status = values.get("status")
        if status in {"COMPLETE", "DRAFT_INCOMPLETE"} and values.get("draft_fields"):
            report = build_intake_report(
                values,  # type: ignore[arg-type]
                status=status,
                missing=list(values.get("missing_fields") or []),
            )
            return SessionSnapshot(
                session_id=session_id,
                phase="complete",
                draft_fields=values.get("draft_fields"),
                governance_fields=values.get("governance_fields"),
                revision_cycles=int(values.get("revision_cycles", 0)),
                status=status,
                missing_fields=list(values.get("missing_fields") or []),
                report=report,
            )

        # No state yet for this thread.
        return SessionSnapshot(session_id=session_id, phase="not_started")

    # -- public API --------------------------------------------------------

    def has_session(self, session_id: str) -> bool:
        with self._lock:
            graph = self._get_graph(session_id)
            state = graph.get_state(self._config(session_id))
            return bool(state.values) or bool(state.tasks)

    def start_session(
        self,
        *,
        stakeholder_id: str,
        session_id: str,
        domain: str = "pc_claims",
        initial_problem: str | None = None,
    ) -> SessionSnapshot:
        """Kick off a new interview. Runs until the first interrupt."""

        with self._lock:
            graph = self._get_graph(session_id)
            state = initial_state(
                stakeholder_id=stakeholder_id,
                session_id=session_id,
                domain=domain,
                initial_problem=initial_problem,
            )
            graph.invoke(state, config=self._config(session_id))
            return self._snapshot(session_id)

    def answer(self, session_id: str, answer_text: str) -> SessionSnapshot:
        """Resume an interview from an ``ask_user`` interrupt."""

        with self._lock:
            snap = self._snapshot(session_id)
            if snap.phase != "question":
                raise InvalidPhaseError(
                    f"Session {session_id!r} is in phase {snap.phase!r}, "
                    "cannot accept an interview answer."
                )
            graph = self._get_graph(session_id)
            graph.invoke(
                Command(resume=answer_text),
                config=self._config(session_id),
            )
            return self._snapshot(session_id)

    def review(self, session_id: str, review_text: str) -> SessionSnapshot:
        """Resume an interview from an ``await_review`` interrupt."""

        with self._lock:
            snap = self._snapshot(session_id)
            if snap.phase != "review":
                raise InvalidPhaseError(
                    f"Session {session_id!r} is in phase {snap.phase!r}, "
                    "cannot accept a review response."
                )
            graph = self._get_graph(session_id)
            graph.invoke(
                Command(resume=review_text),
                config=self._config(session_id),
            )
            return self._snapshot(session_id)

    def get_snapshot(self, session_id: str) -> SessionSnapshot:
        with self._lock:
            return self._snapshot(session_id)


class InvalidPhaseError(RuntimeError):
    """Raised when the HTTP layer submits a response for the wrong phase."""


# Exposed mainly for the status endpoint / tests.
CAPS = {
    "max_questions": MAX_QUESTIONS,
    "max_revisions": MAX_REVISIONS,
}
