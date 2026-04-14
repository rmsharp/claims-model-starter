"""Schema package. Versioned submodules live under ``v1``, ``v2``, etc.

The schema registry in :mod:`model_project_constructor.schemas.registry` is the
single lookup point that maps ``(payload_type, schema_version)`` to a concrete
Pydantic model class. Agents never import each other's schemas directly —
they go through the registry via :func:`load_payload`.
"""
