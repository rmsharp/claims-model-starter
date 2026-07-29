"""Tests for :class:`BedrockLLMClient` (intake agent, AWS Bedrock-hosted Claude).

``BedrockLLMClient`` subclasses :class:`AnthropicLLMClient` and overrides only
construction (an ``anthropic.AnthropicBedrockMantle`` client) and the
Bedrock-prefixed default model — every interview method and the JSON parsing are
inherited and already covered by ``test_anthropic_client.py`` and the
cross-provider ``tests/test_llm_json_parity.py`` battery. These tests pin the
Bedrock-specific surface: the subclass relationship (so inheritance holds), the
``anthropic.``-prefixed default model, that an inherited method runs over an
injected client and sends the Bedrock model id, and that the default constructor
lazily builds ``AnthropicBedrockMantle`` (not ``Anthropic``) and forwards
``aws_region``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import pytest
from anthropic.types import TextBlock

from model_project_constructor.agents.intake.anthropic_client import AnthropicLLMClient
from model_project_constructor.agents.intake.bedrock_client import (
    DEFAULT_MODEL,
    BedrockLLMClient,
)
from model_project_constructor.agents.intake.protocol import InterviewContext


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


def _ctx(**overrides: Any) -> InterviewContext:
    base = {
        "stakeholder_id": "s",
        "session_id": "sess",
        "domain": "pc_claims",
        "initial_problem": "Problem.",
        "qa_pairs": [{"question": "Q1", "answer": "A1"}],
        "questions_asked": 1,
    }
    base.update(overrides)
    return InterviewContext(**base)  # type: ignore[arg-type]


def test_default_model_is_bedrock_prefixed() -> None:
    """Bedrock model ids carry an ``anthropic.`` provider prefix. Bedrock has no
    Sonnet tier, so the bedrock default is Opus 4.8 (it intentionally differs
    from the first-party client's Sonnet default)."""
    assert DEFAULT_MODEL == "anthropic.claude-opus-4-8"


def test_is_subclass_of_anthropic_client() -> None:
    """The Bedrock client reuses the Anthropic client's methods + JSON parsing
    by subclassing — this is what lets the parity guard and Decision C hold
    without a second parser copy."""
    assert issubclass(BedrockLLMClient, AnthropicLLMClient)


def test_inherited_next_question_uses_bedrock_model() -> None:
    fake = _FakeAnthropic([json.dumps({"question": "Q?", "believe_enough_info": False})])
    client = BedrockLLMClient(client=fake)
    result = client.next_question(_ctx())
    assert result.question == "Q?"
    assert result.believe_enough_info is False
    # The Bedrock-prefixed model id is what gets sent on the wire.
    assert fake.messages.calls[0]["model"] == DEFAULT_MODEL


def test_has_intake_protocol_methods() -> None:
    client = BedrockLLMClient(client=_FakeAnthropic([]))
    for method in (
        "next_question",
        "draft_report",
        "classify_governance",
        "revise_report",
    ):
        assert callable(getattr(client, method)), method


def test_default_constructor_builds_anthropic_bedrock_mantle(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """With no injected client, the default ctor lazily builds
    ``anthropic.AnthropicBedrockMantle`` (NOT ``anthropic.Anthropic``) and
    forwards ``aws_region`` when given. Auth (Bedrock API key / SigV4) is
    self-discovered from the environment by the SDK."""
    import anthropic

    captured: dict[str, Any] = {}

    class _FakeMantle:
        def __init__(self, **kwargs: Any) -> None:
            captured["kwargs"] = kwargs
            self.messages = _FakeMessages(
                [json.dumps({"question": "Q", "believe_enough_info": False})]
            )

    def _boom(*_a: Any, **_k: Any) -> Any:
        raise AssertionError("Bedrock client must not build anthropic.Anthropic")

    monkeypatch.setattr(anthropic, "AnthropicBedrockMantle", _FakeMantle)
    monkeypatch.setattr(anthropic, "Anthropic", _boom)

    client = BedrockLLMClient(aws_region="us-east-1")
    assert captured["kwargs"] == {"aws_region": "us-east-1"}
    assert client.next_question(_ctx()).question == "Q"


def test_default_constructor_omits_region_when_unset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When ``aws_region`` is not passed, no region kwarg is forwarded — the SDK
    self-discovers it from ``AWS_REGION`` / ``AWS_DEFAULT_REGION``."""
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
