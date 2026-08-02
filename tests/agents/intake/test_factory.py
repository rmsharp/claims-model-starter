"""Unit tests for the Intake Agent's LLM-provider factory.

The factory constructs the real :class:`AnthropicLLMClient`, whose no-arg
construction would otherwise import ``anthropic`` and build a live
``anthropic.Anthropic()`` (needs an API key). Each test that exercises the
``"anthropic"`` branch monkeypatches the SDK constructor to a sentinel.
"""

from __future__ import annotations

from typing import Any, get_args

import pytest

from model_project_constructor.agents.intake.anthropic_client import (
    DEFAULT_MODEL,
    AnthropicLLMClient,
)
from model_project_constructor.agents.intake.bedrock_client import (
    DEFAULT_MODEL as BEDROCK_DEFAULT_MODEL,
)
from model_project_constructor.agents.intake.bedrock_client import (
    BedrockLLMClient,
)
from model_project_constructor.agents.intake.factory import (
    KNOWN_PROVIDERS,
    LLMProvider,
    make_llm_client,
)
from model_project_constructor.agents.intake.opencode_client import (
    DEFAULT_MODEL as OPENCODE_DEFAULT_MODEL,
)
from model_project_constructor.agents.intake.opencode_client import (
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
    binary fails fast rather than mid-interview. CI deliberately does not install
    ``opencode`` (hermeticity), so the factory branch is exercised against a
    stubbed lookup. No process is spawned either way — nothing here calls the
    client's transport.
    """
    import shutil

    monkeypatch.setattr(shutil, "which", lambda name: f"/usr/local/bin/{name}")


def test_default_provider_returns_anthropic_client(_stub_anthropic: object) -> None:
    assert isinstance(make_llm_client(), AnthropicLLMClient)


def test_explicit_anthropic_returns_anthropic_client(_stub_anthropic: object) -> None:
    assert isinstance(make_llm_client("anthropic"), AnthropicLLMClient)


def test_returned_client_has_intake_protocol_methods(_stub_anthropic: object) -> None:
    # IntakeLLMClient is a plain (non-runtime_checkable) Protocol, so isinstance
    # against it raises; assert the four protocol methods are present instead.
    client = make_llm_client("anthropic")
    for method in (
        "next_question",
        "draft_report",
        "classify_governance",
        "revise_report",
    ):
        assert callable(getattr(client, method)), method


def test_default_model_is_provider_default(_stub_anthropic: object) -> None:
    client = make_llm_client("anthropic")
    assert client._model == DEFAULT_MODEL


def test_model_is_plumbed_through(_stub_anthropic: object) -> None:
    client = make_llm_client("anthropic", model="claude-test-model")
    assert client._model == "claude-test-model"


def test_bedrock_returns_bedrock_client(_stub_bedrock: object) -> None:
    assert isinstance(make_llm_client("bedrock"), BedrockLLMClient)


def test_bedrock_default_model_is_provider_default(_stub_bedrock: object) -> None:
    client = make_llm_client("bedrock")
    assert client._model == BEDROCK_DEFAULT_MODEL


def test_bedrock_model_is_plumbed_through(_stub_bedrock: object) -> None:
    client = make_llm_client("bedrock", model="anthropic.claude-test")
    assert client._model == "anthropic.claude-test"


def test_opencode_returns_opencode_client(_stub_opencode_binary: None) -> None:
    assert isinstance(make_llm_client("opencode"), OpenCodeLLMClient)


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
    """Importing the factory module — and the package __init__ that re-exports
    it — must NOT import the anthropic SDK. This is the lazy-construction
    property that lets the intake web app be built without anthropic
    (ui/intake/app.py). Run in a fresh interpreter because sys.modules is
    process-global and other tests have already imported anthropic.
    """
    import subprocess
    import sys
    import textwrap

    code = textwrap.dedent(
        """
        import sys
        # Triggers agents/intake/__init__.py, which re-exports the factory.
        import model_project_constructor.agents.intake  # noqa: F401
        import model_project_constructor.agents.intake.factory  # noqa: F401
        from model_project_constructor.ui.intake.app import create_app
        create_app()
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
