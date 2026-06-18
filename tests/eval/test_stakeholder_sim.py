"""Deterministic tests for the live stakeholder simulator (no API key).

The simulator only calls a live model at run time; everything else — the
knowledge-brief assembly, the prompt shape, the seam-error handling, and the
fact that it plugs into the real ``run_scripted`` driver as an ``answer_provider``
— is verified here against an injected fake client.
"""

from __future__ import annotations

from typing import Any

import pytest

from model_project_constructor.agents.intake import FixtureLLMClient, IntakeAgent
from model_project_constructor.agents.intake.fixture import load_fixture
from tests.eval.eval_corpus import load_interview_cases
from tests.eval.stakeholder_sim import (
    _STAKEHOLDER_SYSTEM,
    StakeholderSimulator,
    _brief_from_fixture,
)

_SUBRO = load_fixture(
    next(c for c in load_interview_cases() if c.case_id == "subrogation").fixture_path
)


class _FakeBlock:
    def __init__(self, text: Any) -> None:
        self.text = text


class _FakeResponse:
    def __init__(self, content: list[Any]) -> None:
        self.content = content


class _FakeMessages:
    """Records each ``create`` call and returns a canned text response."""

    def __init__(self, owner: _FakeClient) -> None:
        self._owner = owner

    def create(self, **kwargs: Any) -> _FakeResponse:
        self._owner.calls.append(kwargs)
        return _FakeResponse(self._owner.content)


class _FakeClient:
    def __init__(self, text: str = "A faithful stakeholder answer.") -> None:
        self.calls: list[dict[str, Any]] = []
        self.content: list[Any] = [_FakeBlock(text)]
        self.messages = _FakeMessages(self)


def test_brief_includes_fixture_knowledge() -> None:
    brief = _brief_from_fixture(_SUBRO)
    # The initial problem, an established fact, and — crucially — the value
    # measurement plan the interviewer must extract to reach COMPLETE.
    assert "Subrogation recovery" in brief
    assert "subrogation recovery rate dropped" in brief
    assert "subrogation_recovery_rate" in brief  # value_measurement_plan baseline
    assert "champion_challenger" in brief  # counterfactual_design


def test_call_sends_question_and_returns_text() -> None:
    client = _FakeClient("Recovery dropped about 20%.")
    sim = StakeholderSimulator(brief="BRIEF BODY", client=client, model="m-test")
    answer = sim(question="How far did recovery drop?", question_number=3)

    assert answer == "Recovery dropped about 20%."
    assert len(client.calls) == 1
    call = client.calls[0]
    assert call["model"] == "m-test"
    assert call["system"] == _STAKEHOLDER_SYSTEM
    user = call["messages"][0]["content"]
    assert "BRIEF BODY" in user
    assert "How far did recovery drop?" in user
    assert "question 3" in user


def test_simulator_drives_run_scripted_to_convergence() -> None:
    """The simulator plugs into the real driver: a fake-backed stakeholder feeds
    the FixtureLLMClient interviewer all the way to a COMPLETE report — proving
    the answer_provider seam end-to-end without an API key."""
    sim = StakeholderSimulator(brief="BRIEF", client=_FakeClient("ok"), model="m")
    agent = IntakeAgent(llm=FixtureLLMClient(_SUBRO))
    report = agent.run_scripted(
        stakeholder_id="x",
        session_id="sim-drives",
        answer_provider=sim,
        review_responses=["ACCEPT"],
    )
    assert report.status == "COMPLETE"
    assert report.questions_asked == 7


def test_empty_content_raises_runtime_error() -> None:
    client = _FakeClient()
    client.content = []
    sim = StakeholderSimulator(brief="b", client=client, model="m")
    with pytest.raises(RuntimeError, match="empty content"):
        sim(question="q", question_number=1)


def test_non_text_block_raises_runtime_error() -> None:
    client = _FakeClient()
    client.content = [_FakeBlock(text=None)]  # a non-text block (e.g. tool_use)
    sim = StakeholderSimulator(brief="b", client=client, model="m")
    with pytest.raises(RuntimeError, match="expected a text block"):
        sim(question="q", question_number=1)
