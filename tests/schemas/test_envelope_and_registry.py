"""Unit tests for HandoffEnvelope, schema registry, and load_payload (§6)."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import BaseModel, ValidationError

from model_project_constructor.schemas.envelope import HandoffEnvelope
from model_project_constructor.schemas.registry import (
    REGISTRY,
    UnknownPayloadError,
    load_payload,
)
from model_project_constructor.schemas.v1 import (
    DataReport,
    DataRequest,
    IntakeReport,
    RepoProjectResult,
    RepoTarget,
)
from tests.schemas.fixtures import (
    make_data_report,
    make_data_request,
    make_intake_report,
    make_repo_project_result,
    make_repo_target,
)


# -------------------- HandoffEnvelope --------------------

class TestHandoffEnvelope:
    def _valid_kwargs(self, **overrides: object) -> dict[str, object]:
        defaults: dict[str, object] = dict(
            run_id="run_001",
            source_agent="orchestrator",
            target_agent="data",
            payload_type="IntakeReport",
            payload_schema_version="1.0.0",
            payload={"stub": True},
            created_at=datetime(2026, 4, 14, tzinfo=timezone.utc),
            correlation_id="corr_001",
        )
        defaults.update(overrides)
        return defaults

    def test_happy_path(self) -> None:
        env = HandoffEnvelope(**self._valid_kwargs())  # type: ignore[arg-type]
        assert env.envelope_version == "1.0.0"
        assert env.source_agent == "orchestrator"
        assert env.target_agent == "data"

    def test_envelope_version_locked(self) -> None:
        with pytest.raises(ValidationError):
            HandoffEnvelope(**self._valid_kwargs(envelope_version="2.0.0"))  # type: ignore[arg-type]

    def test_invalid_source_agent_rejected(self) -> None:
        with pytest.raises(ValidationError):
            HandoffEnvelope(**self._valid_kwargs(source_agent="auditor"))  # type: ignore[arg-type]

    def test_target_agent_cannot_be_orchestrator(self) -> None:
        """The orchestrator never *receives* an envelope — it only sends them."""
        with pytest.raises(ValidationError):
            HandoffEnvelope(**self._valid_kwargs(target_agent="orchestrator"))  # type: ignore[arg-type]

    def test_payload_is_stored_as_dict_not_validated(self) -> None:
        """The envelope itself does not enforce payload schema — that is the
        registry's job via ``load_payload``. This is intentional: the envelope
        can transport any registered payload type without recompiling."""
        env = HandoffEnvelope(
            **self._valid_kwargs(payload={"anything": "goes", "nested": {"k": 1}}),  # type: ignore[arg-type]
        )
        assert env.payload == {"anything": "goes", "nested": {"k": 1}}

    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            HandoffEnvelope(**self._valid_kwargs(zombie_field=1))  # type: ignore[arg-type]

    def test_serialization_round_trip(self) -> None:
        env = HandoffEnvelope(**self._valid_kwargs())  # type: ignore[arg-type]
        restored = HandoffEnvelope.model_validate_json(env.model_dump_json())
        assert restored == env


# -------------------- Registry --------------------

class TestRegistry:
    def test_registry_has_all_five_schemas(self) -> None:
        """Adding a new payload type without registering it is a bug. This test
        fails loudly so the registry never silently loses a type."""
        expected = {
            ("IntakeReport", "1.0.0"),
            ("DataRequest", "1.0.0"),
            ("DataReport", "1.0.0"),
            ("RepoTarget", "1.0.0"),
            ("RepoProjectResult", "1.0.0"),
        }
        assert set(REGISTRY.keys()) == expected

    def test_registry_maps_to_correct_classes(self) -> None:
        assert REGISTRY[("IntakeReport", "1.0.0")] is IntakeReport
        assert REGISTRY[("DataRequest", "1.0.0")] is DataRequest
        assert REGISTRY[("DataReport", "1.0.0")] is DataReport
        assert REGISTRY[("RepoTarget", "1.0.0")] is RepoTarget
        assert REGISTRY[("RepoProjectResult", "1.0.0")] is RepoProjectResult

    def test_every_value_is_pydantic_basemodel_subclass(self) -> None:
        for key, cls in REGISTRY.items():
            assert issubclass(cls, BaseModel), f"{key} maps to non-BaseModel {cls}"


# -------------------- load_payload --------------------

def _make_envelope(payload_type: str, payload: dict[str, object]) -> HandoffEnvelope:
    return HandoffEnvelope(
        run_id="run_001",
        source_agent="orchestrator",
        target_agent="data",
        payload_type=payload_type,
        payload_schema_version="1.0.0",
        payload=payload,
        created_at=datetime(2026, 4, 14, tzinfo=timezone.utc),
        correlation_id="corr_001",
    )


class TestLoadPayload:
    def test_loads_intake_report(self) -> None:
        ir = make_intake_report()
        env = _make_envelope("IntakeReport", ir.model_dump(mode="json"))
        loaded = load_payload(env)
        assert isinstance(loaded, IntakeReport)
        assert loaded == ir

    def test_loads_data_request(self) -> None:
        req = make_data_request()
        env = _make_envelope("DataRequest", req.model_dump(mode="json"))
        loaded = load_payload(env)
        assert isinstance(loaded, DataRequest)
        assert loaded == req

    def test_loads_data_report(self) -> None:
        rep = make_data_report()
        env = _make_envelope("DataReport", rep.model_dump(mode="json"))
        loaded = load_payload(env)
        assert isinstance(loaded, DataReport)
        assert loaded == rep

    def test_loads_repo_target(self) -> None:
        tgt = make_repo_target()
        env = _make_envelope("RepoTarget", tgt.model_dump(mode="json"))
        loaded = load_payload(env)
        assert isinstance(loaded, RepoTarget)
        assert loaded == tgt

    def test_loads_repo_project_result(self) -> None:
        res = make_repo_project_result()
        env = _make_envelope("RepoProjectResult", res.model_dump(mode="json"))
        loaded = load_payload(env)
        assert isinstance(loaded, RepoProjectResult)
        assert loaded == res

    def test_unknown_payload_type_raises(self) -> None:
        env = _make_envelope("MysteryReport", {"field": 1})
        with pytest.raises(UnknownPayloadError) as exc_info:
            load_payload(env)
        assert "MysteryReport" in str(exc_info.value)

    def test_unknown_version_raises(self) -> None:
        env = HandoffEnvelope(
            run_id="r",
            source_agent="orchestrator",
            target_agent="data",
            payload_type="IntakeReport",
            payload_schema_version="9.9.9",
            payload={},
            created_at=datetime(2026, 4, 14, tzinfo=timezone.utc),
            correlation_id="c",
        )
        with pytest.raises(UnknownPayloadError) as exc_info:
            load_payload(env)
        assert "9.9.9" in str(exc_info.value)

    def test_invalid_payload_raises_validation_error(self) -> None:
        env = _make_envelope("IntakeReport", {"status": "COMPLETE"})  # missing required fields
        with pytest.raises(ValidationError):
            load_payload(env)
