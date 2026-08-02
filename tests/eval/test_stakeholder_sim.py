"""Deterministic tests for the live stakeholder simulator (no API key).

The simulator only calls a live model at run time; everything else — the
knowledge-brief assembly, the prompt shape, the seam-error handling, and the
fact that it plugs into the real ``run_scripted`` driver as an ``answer_provider``
— is verified here against an injected fake client.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from model_project_constructor.agents.intake import FixtureLLMClient, IntakeAgent
from model_project_constructor.agents.intake.factory import KNOWN_PROVIDERS
from model_project_constructor.agents.intake.fixture import load_fixture
from tests.eval.eval_corpus import load_interview_cases
from tests.eval.stakeholder_sim import (
    _STAKEHOLDER_SYSTEM,
    StakeholderSimulator,
    _brief_from_fixture,
    _text_completer_for,
    stakeholder_simulator_for,
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
    assert call["max_tokens"] == 1024
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


# --- Session 215: the provider-agnostic completion seam --------------------
#
# Before this, the simulator reached straight through to
# ``intake_client._client.messages.create``. That assumes every provider is
# SDK-backed, which stopped being true when ``opencode`` shipped a *subprocess*
# transport whose ``_client`` is a placeholder that raises on attribute access.
# The reach failed mid-run with a bare ``AttributeError`` — not in
# ``interview_sweep._TRANSIENT_ERRORS``, so it aborted the whole shadow run
# after the governance and SQL tiers had already been billed.


class _RaisingSDKHandle:
    """Shaped like ``OpenCodeLLMClient``'s ``_UNUSED_SDK_CLIENT`` placeholder.

    Any attribute access raises, exactly as the real one does — so a test using
    this fails loudly the instant the SDK path is taken by mistake.
    """

    def __getattr__(self, name: str) -> Any:
        raise AttributeError(
            "OpenCodeLLMClient does not use an Anthropic SDK client (attempted "
            f"access: {name!r}); its transport is the opencode CLI."
        )


class _FakeSubprocessClient:
    """Shaped like a subprocess-transport intake client: ``_run`` + a placeholder."""

    def __init__(self, answer: Any = "Recovery dropped about 20%.") -> None:
        self.calls: list[tuple[str, str]] = []
        self._answer = answer
        self._model = "vendor/model-id"
        self._client = _RaisingSDKHandle()

    def _run(self, system: str, user: str) -> Any:
        self.calls.append((system, user))
        return self._answer


def test_subprocess_client_answers_without_touching_the_sdk_handle() -> None:
    """The regression test for the defect that blocked spec Phase 4.

    A subprocess-backed client must answer through its own transport and never
    reach for the SDK handle — whose placeholder would raise ``AttributeError``.
    """
    client = _FakeSubprocessClient("Recovery dropped about 20%.")
    sim = StakeholderSimulator(
        brief="BRIEF BODY", completer=_text_completer_for(client, max_tokens=1024)
    )

    answer = sim(question="How far did recovery drop?", question_number=3)

    assert answer == "Recovery dropped about 20%."
    assert len(client.calls) == 1
    system, user = client.calls[0]
    assert system == _STAKEHOLDER_SYSTEM
    assert "BRIEF BODY" in user
    assert "How far did recovery drop?" in user
    assert "question 3" in user


def test_completer_resolution_prefers_the_subprocess_transport() -> None:
    """``_run`` wins over ``_client`` — the discriminator is the transport the
    client actually has, not its provider name."""
    client = _FakeSubprocessClient()
    assert _text_completer_for(client, max_tokens=1024) == client._run


def test_completer_resolution_falls_back_to_the_sdk_handle() -> None:
    """An SDK-backed client keeps today's behaviour, borrowing its resolved model
    so the stakeholder runs on the same tier as the interviewer."""

    class _SDKShaped:
        def __init__(self) -> None:
            self._client = _FakeClient("An SDK answer.")
            self._model = "borrowed-model-id"

    client = _SDKShaped()
    completer = _text_completer_for(client, max_tokens=77)

    assert completer(_STAKEHOLDER_SYSTEM, "u") == "An SDK answer."
    call = client._client.calls[0]
    assert call["model"] == "borrowed-model-id"
    assert call["max_tokens"] == 77


def test_client_with_neither_transport_fails_loudly_at_construction() -> None:
    """A shape nobody taught this module is a *defect*, so it must abort — not
    raise ``StakeholderSimError``, which ``interview_sweep._TRANSIENT_ERRORS``
    would retry-then-exclude, silently emptying the result set."""

    class _Unteachable:
        pass

    with pytest.raises(TypeError, match="neither a subprocess transport"):
        _text_completer_for(_Unteachable(), max_tokens=1024)


def test_simulator_requires_a_completer_or_a_client() -> None:
    with pytest.raises(TypeError, match="completer="):
        StakeholderSimulator(brief="b")


@pytest.mark.parametrize("blank", ["", "   \n\t "])
def test_blank_subprocess_answer_is_a_typed_seam_error(blank: str) -> None:
    """The shared guard every transport owes the sweep. ``StakeholderSimError``
    *is* right here — a blank answer is the simulator's own seam misbehaving, the
    transient class the sweep retries."""
    client = _FakeSubprocessClient(blank)
    sim = StakeholderSimulator(brief="b", completer=_text_completer_for(client, max_tokens=1))
    with pytest.raises(RuntimeError, match="empty content"):
        sim(question="q", question_number=1)


def test_non_string_subprocess_answer_is_a_typed_seam_error() -> None:
    client = _FakeSubprocessClient(answer=object())
    sim = StakeholderSimulator(brief="b", completer=_text_completer_for(client, max_tokens=1))
    with pytest.raises(RuntimeError, match="expected answer text"):
        sim(question="q", question_number=1)


def test_subprocess_backed_simulator_drives_run_scripted_to_convergence() -> None:
    """The seam works end-to-end through the real driver, on the subprocess path
    — the mirror of ``test_simulator_drives_run_scripted_to_convergence``."""
    client = _FakeSubprocessClient("ok")
    sim = StakeholderSimulator(brief="BRIEF", completer=_text_completer_for(client, max_tokens=1))
    agent = IntakeAgent(llm=FixtureLLMClient(_SUBRO))
    report = agent.run_scripted(
        stakeholder_id="x",
        session_id="sim-drives-subprocess",
        answer_provider=sim,
        review_responses=["ACCEPT"],
    )
    assert report.status == "COMPLETE"
    assert report.questions_asked == 7
    assert client.calls, "the subprocess transport was never exercised"


# --- the pinned model reaches both halves of the interview (spec D6) -------

_OPENCODE_FIXTURE = (
    Path(__file__).resolve().parents[1] / "fixtures" / "opencode" / "success_with_agent.jsonl"
)


class _RecordingRunner:
    """Stands in for ``subprocess.run``; replays a *committed* OpenCode stream."""

    def __init__(self, stdout: str) -> None:
        self.stdout = stdout
        self.calls: list[tuple[list[str], dict[str, Any]]] = []

    def __call__(self, argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        self.calls.append((argv, kwargs))
        if "--version" in argv:
            return subprocess.CompletedProcess(argv, 0, "1.18.11", "")
        return subprocess.CompletedProcess(argv, 0, self.stdout, "")

    @property
    def run_calls(self) -> list[tuple[list[str], dict[str, Any]]]:
        return [call for call in self.calls if "--version" not in call[0]]


def test_stakeholder_simulator_for_pins_the_model_on_a_real_opencode_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """End-to-end through the *real* client, factory branch included, with a
    committed fixture as the process output — no network, no binary, no spend.

    Pins both halves of the Session 215 fix: the simulator drives a subprocess
    provider at all, and the model the caller pinned reaches its argv. Without
    the model threading, ``opencode`` — which pins no default of its own (spec
    D6) — would run the stakeholder on no model while the interviewer ran on the
    pinned one.
    """
    from model_project_constructor.agents.intake import opencode_client as oc

    runner = _RecordingRunner(_OPENCODE_FIXTURE.read_text())
    # ``sys.executable`` always resolves, so this passes on CI too, where
    # ``opencode`` is deliberately not installed (hermeticity, spec §4.5).
    monkeypatch.setattr(oc.shutil, "which", lambda name: sys.executable)
    monkeypatch.setattr(oc, "_default_runner", runner)

    sim = stakeholder_simulator_for(_SUBRO, provider="opencode", model="anthropic/claude-pinned")
    answer = sim(question="How far did recovery drop?", question_number=2)

    # The verbatim assistant text of the committed probe fixture: proof the
    # answer travelled the real event-stream parser, not a hand-written shape.
    assert answer == '```json\n{"ok": true}\n```'

    argv, kwargs = runner.run_calls[0]
    assert argv[argv.index("--model") + 1] == "anthropic/claude-pinned"
    prompt = kwargs["input"]
    assert "BRIEFING" in prompt  # the fixture-derived stakeholder brief
    assert "How far did recovery drop?" in prompt
    assert "question 2" in prompt


def test_new_provider_forces_a_completer_decision() -> None:
    """Sentinel. ``_text_completer_for`` classifies a client by its transport, so
    a fourth provider shaped like either existing one needs no change here — but
    one shaped like *neither* aborts the sweep. When this assertion fails, add
    the new provider to the resolution tests above rather than just widening it.
    """
    assert set(KNOWN_PROVIDERS) == {"anthropic", "bedrock", "opencode"}
