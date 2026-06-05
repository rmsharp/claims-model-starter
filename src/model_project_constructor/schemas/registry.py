"""Schema registry and ``load_payload`` helper (§6 of architecture-plan.md).

The registry is the **single** place where ``(payload_type, schema_version)``
is mapped to a concrete Pydantic model class. Agents resolve payloads via
:func:`load_payload` rather than importing payload classes from each other.

Schema versioning is intentionally minimal today: only ``1.0.0`` exists, and
every payload registers under it. The read path (:func:`load_payload`) already
keys on ``(payload_type, schema_version)``, so multiple versions *can* coexist
once one is introduced — register the new class under its version key here
(keeping ``1.0.0`` so in-flight runs still resolve) and add whatever migration
the change needs at that point. There is no ``schemas/migrations/`` package yet;
this registry does not implement a migration workflow.
"""

from __future__ import annotations

from pydantic import BaseModel

from model_project_constructor.schemas import v1
from model_project_constructor.schemas.envelope import HandoffEnvelope

SchemaKey = tuple[str, str]


REGISTRY: dict[SchemaKey, type[BaseModel]] = {
    ("IntakeReport", "1.0.0"): v1.IntakeReport,
    ("DataRequest", "1.0.0"): v1.DataRequest,
    ("DataReport", "1.0.0"): v1.DataReport,
    ("RepoTarget", "1.0.0"): v1.RepoTarget,
    ("RepoProjectResult", "1.0.0"): v1.RepoProjectResult,
}


class UnknownPayloadError(KeyError):
    """Raised when an envelope references a payload type/version not in REGISTRY."""


def load_payload(envelope: HandoffEnvelope) -> BaseModel:
    """Resolve and validate an envelope's payload against its declared schema.

    Looks up ``(envelope.payload_type, envelope.payload_schema_version)`` in
    :data:`REGISTRY` and validates the payload dict against the matching
    Pydantic class.

    :raises UnknownPayloadError: if the key is not registered.
    :raises pydantic.ValidationError: if the payload fails schema validation.
    """
    key: SchemaKey = (envelope.payload_type, envelope.payload_schema_version)
    try:
        cls = REGISTRY[key]
    except KeyError as exc:
        raise UnknownPayloadError(
            f"No schema registered for payload_type={envelope.payload_type!r} "
            f"schema_version={envelope.payload_schema_version!r}. "
            f"Registered keys: {sorted(REGISTRY)}"
        ) from exc
    return cls.model_validate(envelope.payload)


__all__ = ["REGISTRY", "SchemaKey", "UnknownPayloadError", "load_payload"]
