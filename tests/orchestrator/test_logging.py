"""Tests for :mod:`model_project_constructor.orchestrator.logging`.

Phase 6 scope: verify that :func:`make_logged_runner` emits structured
start / end / error events with ``run_id`` + ``correlation_id`` bound,
records duration, extracts the result's ``status`` on success, and
re-raises exceptions unchanged.

The tests use pytest's ``caplog`` fixture to intercept log records
without installing a handler. Every assertion inspects the record's
``context`` extra, not the message string, because that's the machine-
readable surface downstream tooling consumes.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import pytest

from model_project_constructor.orchestrator.logging import (
    EVENT_AGENT_END,
    EVENT_AGENT_ERROR,
    EVENT_AGENT_START,
    ORCHESTRATOR_LOGGER_NAME,
    get_logger,
    make_logged_runner,
)


@dataclass
class _FakeResult:
    status: str
    value: int = 0


def _events(caplog: pytest.LogCaptureFixture) -> list[tuple[str, dict]]:
    return [
        (record.getMessage(), getattr(record, "context", {}))
        for record in caplog.records
        if record.name == ORCHESTRATOR_LOGGER_NAME
    ]


class TestGetLogger:
    def test_default_name(self) -> None:
        assert get_logger().name == ORCHESTRATOR_LOGGER_NAME

    def test_custom_name(self) -> None:
        assert get_logger("custom.name").name == "custom.name"

    def test_same_logger_instance_returned(self) -> None:
        assert get_logger() is get_logger()


class TestMakeLoggedRunnerSuccess:
    def test_emits_start_and_end_events(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        def runner() -> _FakeResult:
            return _FakeResult(status="COMPLETE")

        wrapped = make_logged_runner(
            runner,
            agent_name="intake",
            run_id="run_abc",
            correlation_id="corr_abc",
        )
        with caplog.at_level(logging.INFO, logger=ORCHESTRATOR_LOGGER_NAME):
            result = wrapped()

        assert result.status == "COMPLETE"
        events = _events(caplog)
        assert len(events) == 2
        assert events[0][0] == EVENT_AGENT_START
        assert events[0][1] == {
            "agent": "intake",
            "run_id": "run_abc",
            "correlation_id": "corr_abc",
        }
        assert events[1][0] == EVENT_AGENT_END
        end_ctx = events[1][1]
        assert end_ctx["agent"] == "intake"
        assert end_ctx["run_id"] == "run_abc"
        assert end_ctx["correlation_id"] == "corr_abc"
        assert end_ctx["status"] == "COMPLETE"
        assert isinstance(end_ctx["duration_ms"], float)
        assert end_ctx["duration_ms"] >= 0.0

    def test_status_is_none_when_result_has_no_status_attr(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        def runner() -> dict[str, int]:
            return {"x": 1}

        wrapped = make_logged_runner(
            runner,
            agent_name="data",
            run_id="run_2",
            correlation_id="c2",
        )
        with caplog.at_level(logging.INFO, logger=ORCHESTRATOR_LOGGER_NAME):
            assert wrapped() == {"x": 1}

        end_event = _events(caplog)[-1]
        assert end_event[0] == EVENT_AGENT_END
        assert end_event[1]["status"] is None

    def test_return_value_and_args_passed_through(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        def runner(a: int, b: int, *, c: int = 0) -> _FakeResult:
            return _FakeResult(status="COMPLETE", value=a + b + c)

        wrapped = make_logged_runner(
            runner,
            agent_name="website",
            run_id="run_args",
            correlation_id="corr_args",
        )
        with caplog.at_level(logging.INFO, logger=ORCHESTRATOR_LOGGER_NAME):
            out = wrapped(1, 2, c=3)

        assert out.value == 6

    def test_custom_logger_is_respected(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        custom = logging.getLogger("test.custom.logger")

        def runner() -> _FakeResult:
            return _FakeResult(status="COMPLETE")

        wrapped = make_logged_runner(
            runner,
            agent_name="intake",
            run_id="r",
            correlation_id="c",
            logger=custom,
        )
        with caplog.at_level(logging.INFO, logger="test.custom.logger"):
            wrapped()

        custom_records = [r for r in caplog.records if r.name == "test.custom.logger"]
        assert len(custom_records) == 2
        orchestrator_records = [
            r for r in caplog.records if r.name == ORCHESTRATOR_LOGGER_NAME
        ]
        assert orchestrator_records == []


class TestMakeLoggedRunnerError:
    def test_emits_error_event_and_reraises(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        def runner() -> _FakeResult:
            raise RuntimeError("boom")

        wrapped = make_logged_runner(
            runner,
            agent_name="data",
            run_id="run_err",
            correlation_id="corr_err",
        )
        with caplog.at_level(logging.INFO, logger=ORCHESTRATOR_LOGGER_NAME), \
                pytest.raises(RuntimeError, match="boom"):
            wrapped()

        events = _events(caplog)
        assert [e[0] for e in events] == [EVENT_AGENT_START, EVENT_AGENT_ERROR]
        err_ctx = events[1][1]
        assert err_ctx["agent"] == "data"
        assert err_ctx["run_id"] == "run_err"
        assert err_ctx["correlation_id"] == "corr_err"
        assert err_ctx["error_type"] == "RuntimeError"
        assert err_ctx["error_message"] == "boom"
        assert isinstance(err_ctx["duration_ms"], float)

    def test_error_event_is_logged_at_error_level(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        def runner() -> None:
            raise ValueError("bad")

        wrapped = make_logged_runner(
            runner,
            agent_name="intake",
            run_id="r",
            correlation_id="c",
        )
        with caplog.at_level(logging.INFO, logger=ORCHESTRATOR_LOGGER_NAME), \
                pytest.raises(ValueError):
            wrapped()

        error_records = [
            r for r in caplog.records if r.getMessage() == EVENT_AGENT_ERROR
        ]
        assert len(error_records) == 1
        assert error_records[0].levelno == logging.ERROR

    def test_no_end_event_on_failure(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        def runner() -> None:
            raise RuntimeError("nope")

        wrapped = make_logged_runner(
            runner,
            agent_name="website",
            run_id="r",
            correlation_id="c",
        )
        with caplog.at_level(logging.INFO, logger=ORCHESTRATOR_LOGGER_NAME), \
                pytest.raises(RuntimeError):
            wrapped()

        events = _events(caplog)
        assert EVENT_AGENT_END not in [e[0] for e in events]
