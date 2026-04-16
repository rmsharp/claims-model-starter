"""Structured logging helpers for the orchestrator pipeline.

Phase 6 scope (architecture-plan §14): structured logging with
``run_id`` / ``correlation_id`` threaded through each agent call.

The implementation uses the stdlib ``logging`` module and emits
structured events by attaching a ``context`` dict to every record via
``extra=``. Downstream handlers (JSON formatters, log aggregators) can
parse the structured fields without scraping the message string. This
keeps the orchestrator free of any third-party logging dependency while
still producing machine-readable output.

The public surface:

- :func:`get_logger` — returns the orchestrator's named stdlib logger.
- :func:`make_logged_runner` — wraps a pipeline runner callable so every
  invocation emits ``agent.start`` / ``agent.end`` / ``agent.error``
  events with ``run_id`` + ``correlation_id`` + ``agent`` bound, plus the
  call's ``duration_ms``. The wrapper preserves the runner's signature.

The orchestrator's ``pipeline.py`` does **not** import this module. The
caller wraps runners before passing them to :func:`run_pipeline`, so the
pipeline driver stays dependency-free and the observability layer is
opt-in per deployment.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import Any, TypeVar

T = TypeVar("T")

ORCHESTRATOR_LOGGER_NAME = "model_project_constructor.orchestrator"

EVENT_AGENT_START = "agent.start"
EVENT_AGENT_END = "agent.end"
EVENT_AGENT_ERROR = "agent.error"


def get_logger(name: str = ORCHESTRATOR_LOGGER_NAME) -> logging.Logger:
    """Return the orchestrator's named stdlib logger."""

    return logging.getLogger(name)


def _emit(
    logger: logging.Logger,
    level: int,
    event: str,
    context: dict[str, Any],
) -> None:
    logger.log(level, event, extra={"context": context})


def make_logged_runner(
    runner: Callable[..., T],
    *,
    agent_name: str,
    run_id: str,
    correlation_id: str,
    logger: logging.Logger | None = None,
) -> Callable[..., T]:
    """Wrap ``runner`` so each call emits start / end / error events.

    The wrapper:

    - Emits ``agent.start`` at level ``INFO`` immediately before the call.
    - Emits ``agent.end`` at level ``INFO`` on success, with ``duration_ms``
      and (if the result carries a ``status`` attribute) the result's
      status.
    - Emits ``agent.error`` at level ``ERROR`` if the runner raises,
      capturing ``error_type``, ``error_message``, and ``duration_ms``,
      then re-raises the original exception.

    All records include the bound context ``{"agent", "run_id",
    "correlation_id"}`` on the ``context`` extra.
    """

    log = logger or get_logger()

    def wrapped(*args: Any, **kwargs: Any) -> T:
        base_ctx: dict[str, Any] = {
            "agent": agent_name,
            "run_id": run_id,
            "correlation_id": correlation_id,
        }
        _emit(log, logging.INFO, EVENT_AGENT_START, base_ctx)
        start = time.perf_counter()
        try:
            result = runner(*args, **kwargs)
        except Exception as exc:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            _emit(
                log,
                logging.ERROR,
                EVENT_AGENT_ERROR,
                {
                    **base_ctx,
                    "duration_ms": duration_ms,
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                },
            )
            raise
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        end_ctx: dict[str, Any] = {
            **base_ctx,
            "duration_ms": duration_ms,
            "status": getattr(result, "status", None),
        }
        _emit(log, logging.INFO, EVENT_AGENT_END, end_ctx)
        return result

    return wrapped


__all__ = [
    "EVENT_AGENT_END",
    "EVENT_AGENT_ERROR",
    "EVENT_AGENT_START",
    "ORCHESTRATOR_LOGGER_NAME",
    "get_logger",
    "make_logged_runner",
]
