"""Orchestrator package (architecture-plan §12 + §14 Phase 5).

Binds the three pipeline agents (Intake, Data, Website) into a single
``run_pipeline`` sequential driver per §12. The orchestrator owns:

- The halt logic for each ``FAILED_AT_*`` path.
- The adapter that turns an ``IntakeReport`` into a ``DataRequest``
  (the only place in the codebase where those two schemas meet — per §7
  the Data Agent must not import intake types).
- Checkpoint persistence of every ``HandoffEnvelope`` between agents so a
  crashed run can be inspected / resumed.

The ``--host gitlab|github`` selection is delegated to the Website Agent
via its ``ci_platform`` constructor kwarg + the concrete ``RepoClient``
the caller passes in (see ``agents/website/cli.py`` for the reference
plumbing).
"""

from __future__ import annotations

from model_project_constructor.orchestrator.adapters import (
    infer_target_granularity,
    intake_report_to_data_request,
)
from model_project_constructor.orchestrator.checkpoints import CheckpointStore
from model_project_constructor.orchestrator.config import OrchestratorSettings
from model_project_constructor.orchestrator.logging import (
    EVENT_AGENT_END,
    EVENT_AGENT_ERROR,
    EVENT_AGENT_START,
    ORCHESTRATOR_LOGGER_NAME,
    get_logger,
    make_logged_runner,
)
from model_project_constructor.orchestrator.metrics import (
    LatencySamples,
    MetricsRegistry,
    MetricsSnapshot,
    make_measured_runner,
)
from model_project_constructor.orchestrator.pipeline import (
    DataRunner,
    IntakeRunner,
    PipelineConfig,
    PipelineResult,
    WebsiteRunner,
    run_pipeline,
)

__all__ = [
    "EVENT_AGENT_END",
    "EVENT_AGENT_ERROR",
    "EVENT_AGENT_START",
    "ORCHESTRATOR_LOGGER_NAME",
    "CheckpointStore",
    "DataRunner",
    "IntakeRunner",
    "LatencySamples",
    "MetricsRegistry",
    "MetricsSnapshot",
    "OrchestratorSettings",
    "PipelineConfig",
    "PipelineResult",
    "WebsiteRunner",
    "get_logger",
    "infer_target_granularity",
    "intake_report_to_data_request",
    "make_logged_runner",
    "make_measured_runner",
    "run_pipeline",
]
