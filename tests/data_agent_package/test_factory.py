"""Unit tests for the Data Agent's LLM-provider factory.

The factory constructs the real :class:`AnthropicLLMClient`, whose no-arg
construction would otherwise import ``anthropic`` and build a live
``anthropic.Anthropic()`` (needs an API key). Each test that exercises the
``"anthropic"`` branch monkeypatches the SDK constructor to a sentinel, the
same pattern used in ``test_anthropic_client.py``.
"""

from __future__ import annotations

from typing import Any, get_args

import pytest
from model_project_constructor_data_agent.anthropic_client import (
    DEFAULT_MODEL,
    AnthropicLLMClient,
)
from model_project_constructor_data_agent.factory import (
    KNOWN_PROVIDERS,
    LLMProvider,
    make_llm_client,
)
from model_project_constructor_data_agent.llm import LLMClient


@pytest.fixture
def _stub_anthropic(monkeypatch: pytest.MonkeyPatch) -> object:
    """Replace ``anthropic.Anthropic`` with a sentinel-returning ctor."""
    import anthropic

    sentinel = object()
    monkeypatch.setattr(anthropic, "Anthropic", lambda *a, **k: sentinel)
    return sentinel


def test_default_provider_returns_anthropic_client(_stub_anthropic: object) -> None:
    client = make_llm_client()
    assert isinstance(client, AnthropicLLMClient)


def test_explicit_anthropic_returns_anthropic_client(_stub_anthropic: object) -> None:
    client = make_llm_client("anthropic")
    assert isinstance(client, AnthropicLLMClient)


def test_returned_client_satisfies_llmclient_protocol(
    _stub_anthropic: object,
) -> None:
    # LLMClient is @runtime_checkable, so this asserts structural conformance.
    assert isinstance(make_llm_client("anthropic"), LLMClient)


def test_default_model_is_provider_default(_stub_anthropic: object) -> None:
    client = make_llm_client("anthropic")
    assert client._model == DEFAULT_MODEL


def test_model_is_plumbed_through(_stub_anthropic: object) -> None:
    client = make_llm_client("anthropic", model="claude-test-model")
    assert client._model == "claude-test-model"


def test_unknown_provider_raises_value_error() -> None:
    with pytest.raises(ValueError) as exc_info:
        make_llm_client("openai")
    message = str(exc_info.value)
    assert "openai" in message
    # The error lists every known provider, single-sourced from the Literal.
    for provider in KNOWN_PROVIDERS:
        assert provider in message


def test_known_providers_derived_from_literal() -> None:
    assert get_args(LLMProvider) == KNOWN_PROVIDERS
    assert "anthropic" in KNOWN_PROVIDERS


def test_unknown_provider_does_not_construct_sdk(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An unknown provider must fail before importing/constructing the SDK."""
    import anthropic

    def _boom(*_a: Any, **_k: Any) -> Any:
        raise AssertionError("anthropic.Anthropic must not be constructed")

    monkeypatch.setattr(anthropic, "Anthropic", _boom)
    with pytest.raises(ValueError):
        make_llm_client("not-a-provider")
