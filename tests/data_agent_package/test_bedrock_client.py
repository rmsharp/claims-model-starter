"""Tests for :class:`BedrockLLMClient` (data agent, AWS Bedrock-hosted Claude).

``BedrockLLMClient`` subclasses the wheel's :class:`AnthropicLLMClient` and
overrides only construction (an ``anthropic.AnthropicBedrockMantle`` client) and
the Bedrock-prefixed default model — the five required protocol methods, the
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
    assert DEFAULT_MODEL == "anthropic.claude-opus-4-8"


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


def test_default_constructor_builds_anthropic_bedrock_mantle(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """With no injected client, the default ctor lazily builds
    ``anthropic.AnthropicBedrockMantle`` (NOT ``anthropic.Anthropic``) and
    forwards ``aws_region`` when given."""
    import anthropic

    captured: dict[str, Any] = {}

    class _FakeMantle:
        def __init__(self, **kwargs: Any) -> None:
            captured["kwargs"] = kwargs
            self.messages = _FakeMessages(["ok"])

    def _boom(*_a: Any, **_k: Any) -> Any:
        raise AssertionError("Bedrock client must not build anthropic.Anthropic")

    monkeypatch.setattr(anthropic, "AnthropicBedrockMantle", _FakeMantle)
    monkeypatch.setattr(anthropic, "Anthropic", _boom)

    client = BedrockLLMClient(aws_region="us-west-2")
    assert captured["kwargs"] == {"aws_region": "us-west-2"}
    assert client._call_claude("s", "u") == "ok"


def test_default_constructor_omits_region_when_unset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When ``aws_region`` is not passed, no region kwarg is forwarded — the SDK
    self-discovers region from ``AWS_REGION`` / ``AWS_DEFAULT_REGION``."""
    import anthropic

    captured: dict[str, Any] = {}

    class _FakeMantle:
        def __init__(self, **kwargs: Any) -> None:
            captured["kwargs"] = kwargs
            self.messages = _FakeMessages([])

    monkeypatch.setattr(anthropic, "AnthropicBedrockMantle", _FakeMantle)
    BedrockLLMClient()
    assert captured["kwargs"] == {}


def test_default_constructor_forwards_base_url_and_http_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``base_url`` (a PrivateLink VPCE / GovCloud host) and ``http_client``
    (a forward proxy / corp CA bundle) are forwarded to ``AnthropicBedrockMantle``
    so an enterprise can wire private connectivity without editing this client."""
    import anthropic

    captured: dict[str, Any] = {}

    class _FakeMantle:
        def __init__(self, **kwargs: Any) -> None:
            captured["kwargs"] = kwargs
            self.messages = _FakeMessages([])

    monkeypatch.setattr(anthropic, "AnthropicBedrockMantle", _FakeMantle)
    sentinel_http = object()
    BedrockLLMClient(
        aws_region="us-east-1",
        base_url="https://vpce-abc.bedrock-mantle.us-east-1.vpce.amazonaws.com/anthropic",
        http_client=sentinel_http,
    )
    assert captured["kwargs"] == {
        "aws_region": "us-east-1",
        "base_url": "https://vpce-abc.bedrock-mantle.us-east-1.vpce.amazonaws.com/anthropic",
        "http_client": sentinel_http,
    }


def test_require_sigv4_rejects_stray_bearer_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``require_sigv4=True`` turns a stray ``AWS_BEARER_TOKEN_BEDROCK`` into a
    hard error, so it cannot silently override role-based SigV4 in production."""
    monkeypatch.setenv("AWS_BEARER_TOKEN_BEDROCK", "bedrock-api-key")
    with pytest.raises(ValueError, match="AWS_BEARER_TOKEN_BEDROCK"):
        BedrockLLMClient(require_sigv4=True)


def test_require_sigv4_allows_construction_when_token_absent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``require_sigv4=True`` does not block the happy path (role SigV4) when no
    bearer token is present."""
    import anthropic

    monkeypatch.delenv("AWS_BEARER_TOKEN_BEDROCK", raising=False)
    monkeypatch.delenv("ANTHROPIC_AWS_API_KEY", raising=False)

    class _FakeMantle:
        def __init__(self, **kwargs: Any) -> None:
            self.messages = _FakeMessages([])

    monkeypatch.setattr(anthropic, "AnthropicBedrockMantle", _FakeMantle)
    BedrockLLMClient(require_sigv4=True)  # must not raise


def test_require_sigv4_rejects_stray_anthropic_aws_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The SDK's ``AnthropicBedrockMantle`` also honors ``ANTHROPIC_AWS_API_KEY``
    as a bearer-token source (``_MANTLE_API_KEY_ENV_VARS``) — the guard must
    reject it too, not just ``AWS_BEARER_TOKEN_BEDROCK`` (D13)."""
    monkeypatch.delenv("AWS_BEARER_TOKEN_BEDROCK", raising=False)
    monkeypatch.setenv("ANTHROPIC_AWS_API_KEY", "bedrock-api-key")
    with pytest.raises(ValueError, match="ANTHROPIC_AWS_API_KEY"):
        BedrockLLMClient(require_sigv4=True)


def test_require_sigv4_defaults_from_env_var(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When ``require_sigv4`` is not passed explicitly, it resolves from
    ``BEDROCK_REQUIRE_SIGV4`` (D13) — so ``INTAKE_LLM_PROVIDER=bedrock`` can
    enforce the guard purely through env config, with no call-site change."""
    monkeypatch.setenv("BEDROCK_REQUIRE_SIGV4", "1")
    monkeypatch.setenv("AWS_BEARER_TOKEN_BEDROCK", "bedrock-api-key")
    monkeypatch.delenv("ANTHROPIC_AWS_API_KEY", raising=False)
    with pytest.raises(ValueError, match="AWS_BEARER_TOKEN_BEDROCK"):
        BedrockLLMClient()


def test_explicit_require_sigv4_false_overrides_env_var(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An explicit ``require_sigv4=False`` always wins over
    ``BEDROCK_REQUIRE_SIGV4`` — the env var only supplies a default."""
    import anthropic

    monkeypatch.setenv("BEDROCK_REQUIRE_SIGV4", "1")
    monkeypatch.setenv("AWS_BEARER_TOKEN_BEDROCK", "bedrock-api-key")

    class _FakeMantle:
        def __init__(self, **kwargs: Any) -> None:
            self.messages = _FakeMessages([])

    monkeypatch.setattr(anthropic, "AnthropicBedrockMantle", _FakeMantle)
    BedrockLLMClient(require_sigv4=False)  # must not raise
