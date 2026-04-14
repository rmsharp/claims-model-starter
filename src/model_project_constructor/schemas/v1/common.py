"""Shared literal type aliases, strict base class, and the v1 schema version constant."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict

SCHEMA_VERSION: Literal["1.0.0"] = "1.0.0"


class StrictBase(BaseModel):
    """Base for every v1 schema.

    - ``extra="forbid"`` so typos in producer code fail loudly instead of
      silently dropping fields.
    - ``protected_namespaces=()`` disables Pydantic v2's warning on field names
      that start with ``model_`` (we have ``model_solution``, ``model_type``,
      ``model_registry_entry``; all are domain-meaningful, not Pydantic API
      collisions).
    """

    model_config = ConfigDict(extra="forbid", protected_namespaces=())

CycleTime = Literal["strategic", "tactical", "operational", "continuous"]

RiskTier = Literal[
    "tier_1_critical",
    "tier_2_high",
    "tier_3_moderate",
    "tier_4_low",
]

ModelType = Literal[
    "supervised_classification",
    "supervised_regression",
    "unsupervised_clustering",
    "unsupervised_anomaly",
    "time_series",
    "reinforcement",
    "other",
]
