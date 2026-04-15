"""Intake Agent Web UI package (architecture-plan §9.3, Phase 3B).

Public entry points:

* :func:`create_app` — factory used by tests and for custom LLM injection.
* ``app`` — module-level :class:`FastAPI` instance for
  ``uvicorn model_project_constructor.ui.intake:app``.
* :class:`IntakeSessionStore` — SQLite-backed per-session graph driver.
* :class:`SessionSnapshot` — phase-tagged view of a session.
"""

from __future__ import annotations

from model_project_constructor.ui.intake.app import app, create_app
from model_project_constructor.ui.intake.runner import (
    InvalidPhaseError,
    IntakeSessionStore,
    SessionSnapshot,
)

__all__ = [
    "app",
    "create_app",
    "IntakeSessionStore",
    "SessionSnapshot",
    "InvalidPhaseError",
]
