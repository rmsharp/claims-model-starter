"""Handoff envelope protocol (§6 of architecture-plan.md).

The envelope is the only inter-agent transport type. A concrete payload (e.g.
``IntakeReport``) is carried as ``envelope.payload`` (a plain ``dict``) and is
resolved to the correct Pydantic class by the schema registry using
``(payload_type, payload_schema_version)`` as the key.

``envelope_version`` is versioned independently from payload schemas so the
envelope itself can evolve without forcing every payload to rev.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict


class HandoffEnvelope(BaseModel):
    """Transport wrapper for any inter-agent payload."""

    model_config = ConfigDict(extra="forbid")

    envelope_version: Literal["1.0.0"] = "1.0.0"
    run_id: str
    source_agent: Literal["intake", "data", "website", "orchestrator"]
    target_agent: Literal["intake", "data", "website"]
    payload_type: str
    payload_schema_version: str
    payload: dict[str, Any]
    created_at: datetime
    correlation_id: str
