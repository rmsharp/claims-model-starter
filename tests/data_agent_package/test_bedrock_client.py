"""Tests for :class:`BedrockLLMClient` (data agent, AWS Bedrock-hosted Claude).

``BedrockLLMClient`` subclasses the wheel's :class:`AnthropicLLMClient` and
overrides only construction (an ``anthropic.AnthropicBedrock`` client) and the
Bedrock-prefixed default model — the five required protocol methods, the
optional ``rank_candidate_tables``, ``_call_claude``, and the JSON parsing are
inherited and already covered by ``test_anthropic_client.py`` and the
cross-provider ``tests/test_llm_json_parity.py`` battery. These tests pin the
Bedrock-specific surface only.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest
from anthropic.types import TextBlock
from model_project_constructor_data_agent.anthropic_client import AnthropicLLMClient
from model_project_constructor_data_agent.bedrock_client import (
    DEFAULT_MODEL,
    BedrockLLMClient,
)
from model_project_constructor_data_agent.llm import LLMClient


@dataclass
class _Response:
    content: list[Any]


class _FakeMessages:
    def __init__(self, responses: list[str]):
        self._responses = list(responses)
        self.calls: list[dict[str, Any]] = []

    def create(self, **kwargs: Any) -> _Response:
        self.calls.append(kwargs)
        text = self._responses.pop(0)
        return _Response(content=[TextBlock(text=text, type="text")])


class _FakeAnthropic:
    def __init__(self, responses: list[str]):
        self.messages = _FakeMessages(responses)


def test_default_model_is_bedrock_prefixed() -> None:
    assert DEFAULT_MODEL == "anthropic.claude-sonnet-4-6"


def test_is_subclass_of_anthropic_client() -> None:
    """The Bedrock client reuses the wheel's Anthropic client by subclassing —
    so the parity guard and Decision C hold without a second parser copy."""
    assert issubclass(BedrockLLMClient, AnthropicLLMClient)


def test_satisfies_llmclient_protocol() -> None:
    """LLMClient is ``@runtime_checkable`` — this asserts structural conformance
    (all five required methods present via inheritance)."""
    assert isinstance(BedrockLLMClient(client=_FakeAnthropic([])), LLMClient)


def test_has_optional_rank_candidate_tables() -> None:
    """``rank_candidate_tables`` is hasattr-dispatched by discovery; the Bedrock
    client inherits it, so discovery's optional-ranking path works on Bedrock."""
    assert hasattr(BedrockLLMClient(client=_FakeAnthropic([])), "rank_candidate_tables")


def test_inherited_call_claude_uses_bedrock_model() -> None:
    """The inherited ``_call_claude`` round-trip sends the Bedrock-prefixed model
    id on the wire and returns the raw text unchanged."""
    fake = _FakeAnthropic(["raw text"])
    client = BedrockLLMClient(client=fake)
    assert client._call_claude("system", "user") == "raw text"
    assert fake.messages.calls[0]["model"] == DEFAULT_MODEL


def test_default_constructor_builds_anthropic_bedrock(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """With no injected client, the default ctor lazily builds
    ``anthropic.AnthropicBedrock`` (NOT ``anthropic.Anthropic``) and forwards
    ``aws_region`` when given."""
    import anthropic

    captured: dict[str, Any] = {}

    class _FakeBedrock:
        def __init__(self, **kwargs: Any) -> None:
            captured["kwargs"] = kwargs
            self.messages = _FakeMessages(["ok"])

    def _boom(*_a: Any, **_k: Any) -> Any:
        raise AssertionError("Bedrock client must not build anthropic.Anthropic")

    monkeypatch.setattr(anthropic, "AnthropicBedrock", _FakeBedrock)
    monkeypatch.setattr(anthropic, "Anthropic", _boom)

    client = BedrockLLMClient(aws_region="us-west-2")
    assert captured["kwargs"] == {"aws_region": "us-west-2"}
    assert client._call_claude("s", "u") == "ok"


def test_default_constructor_omits_region_when_unset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When ``aws_region`` is not passed, no region kwarg is forwarded — the SDK
    self-discovers region from the boto3 chain (e.g. ``AWS_REGION``)."""
    import anthropic

    captured: dict[str, Any] = {}

    class _FakeBedrock:
        def __init__(self, **kwargs: Any) -> None:
            captured["kwargs"] = kwargs
            self.messages = _FakeMessages([])

    monkeypatch.setattr(anthropic, "AnthropicBedrock", _FakeBedrock)
    BedrockLLMClient()
    assert captured["kwargs"] == {}
