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
from model_project_constructor_data_agent.bedrock_client import (
    DEFAULT_MODEL as BEDROCK_DEFAULT_MODEL,
)
from model_project_constructor_data_agent.bedrock_client import (
    BedrockLLMClient,
)
from model_project_constructor_data_agent.factory import (
    KNOWN_PROVIDERS,
    LLMProvider,
    make_llm_client,
)
from model_project_constructor_data_agent.llm import LLMClient
from model_project_constructor_data_agent.opencode_client import (
    DEFAULT_MODEL as OPENCODE_DEFAULT_MODEL,
)
from model_project_constructor_data_agent.opencode_client import (
    OpenCodeLLMClient,
)


@pytest.fixture
def _stub_anthropic(monkeypatch: pytest.MonkeyPatch) -> object:
    """Replace ``anthropic.Anthropic`` with a sentinel-returning ctor."""
    import anthropic

    sentinel = object()
    monkeypatch.setattr(anthropic, "Anthropic", lambda *a, **k: sentinel)
    return sentinel


@pytest.fixture
def _stub_bedrock(monkeypatch: pytest.MonkeyPatch) -> object:
    """Replace ``anthropic.AnthropicBedrockMantle`` with a sentinel-returning ctor.

    Bedrock's no-arg construction would otherwise build a live
    ``anthropic.AnthropicBedrockMantle`` (needs AWS credentials/region).
    """
    import anthropic

    sentinel = object()
    monkeypatch.setattr(anthropic, "AnthropicBedrockMantle", lambda *a, **k: sentinel)
    return sentinel


@pytest.fixture
def _stub_opencode_binary(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make the ``opencode`` binary look installed.

    The OpenCode client checks ``shutil.which`` at construction so a missing
    binary fails fast rather than mid-run. CI deliberately does not install
    ``opencode`` (hermeticity), so the factory branch is exercised against a
    stubbed lookup. No process is spawned either way — nothing here calls the
    client's transport.
    """
    import shutil

    monkeypatch.setattr(shutil, "which", lambda name: f"/usr/local/bin/{name}")


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


def test_bedrock_returns_bedrock_client(_stub_bedrock: object) -> None:
    assert isinstance(make_llm_client("bedrock"), BedrockLLMClient)


def test_bedrock_satisfies_llmclient_protocol(_stub_bedrock: object) -> None:
    assert isinstance(make_llm_client("bedrock"), LLMClient)


def test_bedrock_default_model_is_provider_default(_stub_bedrock: object) -> None:
    client = make_llm_client("bedrock")
    assert client._model == BEDROCK_DEFAULT_MODEL


def test_bedrock_model_is_plumbed_through(_stub_bedrock: object) -> None:
    client = make_llm_client("bedrock", model="anthropic.claude-test")
    assert client._model == "anthropic.claude-test"


def test_opencode_returns_opencode_client(_stub_opencode_binary: None) -> None:
    assert isinstance(make_llm_client("opencode"), OpenCodeLLMClient)


def test_opencode_client_satisfies_protocol(_stub_opencode_binary: None) -> None:
    """The factory's return type is the protocol, not a concrete class — pin that
    the new branch actually satisfies it (``LLMClient`` is ``runtime_checkable``)."""
    assert isinstance(make_llm_client("opencode"), LLMClient)


def test_opencode_default_model_is_unset(_stub_opencode_binary: None) -> None:
    """Spec D6: this provider pins no model — the operator's own OpenCode config
    picks the vendor, which is the entire point of the adapter. ``_model`` is
    typed ``str`` by the parent, so "unset" is stored as ``""``."""
    assert OPENCODE_DEFAULT_MODEL is None
    assert make_llm_client("opencode")._model == ""


def test_opencode_model_is_plumbed_through(_stub_opencode_binary: None) -> None:
    client = make_llm_client("opencode", model="anthropic/claude-haiku-4-5")
    assert client._model == "anthropic/claude-haiku-4-5"


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
    assert "bedrock" in KNOWN_PROVIDERS
    assert "opencode" in KNOWN_PROVIDERS


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


def test_factory_import_does_not_load_anthropic() -> None:
    """Importing the factory module — and the standalone package __init__ that
    re-exports it — must NOT import the anthropic SDK at load time. The wheel
    imports anthropic only when a real client is constructed. Run in a fresh
    interpreter because sys.modules is process-global.
    """
    import subprocess
    import sys
    import textwrap

    code = textwrap.dedent(
        """
        import sys
        import model_project_constructor_data_agent  # noqa: F401  (runs __init__)
        import model_project_constructor_data_agent.factory  # noqa: F401
        # No LLM SDK at factory-import time: neither anthropic nor boto3 /
        # botocore (the Bedrock transport pulled by the anthropic[bedrock]
        # extra, Phase C). The Bedrock client is imported lazily inside the
        # factory branch, so its top-level anthropic import never leaks here.
        leaked = sorted(
            m for m in sys.modules
            if m.split(".")[0] in {"anthropic", "boto3", "botocore"}
        )
        assert not leaked, leaked
        print("sdk-free")
        """
    )
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr
    assert "sdk-free" in result.stdout


def test_sql_dialect_defaults_to_none(_stub_anthropic: object) -> None:
    """Omitting the keyword must not opt any caller into a dialect."""
    assert make_llm_client("anthropic")._sql_dialect is None  # type: ignore[union-attr]


def test_sql_dialect_is_plumbed_through_anthropic(_stub_anthropic: object) -> None:
    client = make_llm_client("anthropic", sql_dialect="sqlite")
    assert client._sql_dialect == "sqlite"  # type: ignore[union-attr]


def test_sql_dialect_is_plumbed_through_bedrock(_stub_bedrock: object) -> None:
    client = make_llm_client("bedrock", sql_dialect="postgresql")
    assert client._sql_dialect == "postgresql"  # type: ignore[union-attr]


def test_sql_dialect_is_plumbed_through_opencode(_stub_opencode_binary: None) -> None:
    client = make_llm_client("opencode", sql_dialect="snowflake")
    assert client._sql_dialect == "snowflake"  # type: ignore[union-attr]


@pytest.mark.parametrize("provider", KNOWN_PROVIDERS)
def test_every_known_provider_accepts_sql_dialect(
    provider: str,
    _stub_anthropic: object,
    _stub_bedrock: object,
    _stub_opencode_binary: None,
) -> None:
    """Parametrized over the Literal so a fourth provider cannot silently skip it.

    Adding a branch to ``make_llm_client`` that forgets ``sql_dialect=`` would
    ship a provider whose SQL is dialect-blind while every other provider's is
    not — exactly the kind of per-provider drift the shared-prompt design exists
    to prevent.
    """
    assert make_llm_client(provider, sql_dialect="sqlite")._sql_dialect == "sqlite"  # type: ignore[union-attr]
