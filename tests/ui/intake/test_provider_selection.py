"""Provider/model selection for the intake web UI (multi-provider plan Phase D).

These tests pin the production factory's provider/model *resolution* — the
arg > env > default precedence, the ``model=None`` provider-native default, the
eager unknown-provider rejection, and the rule that an injected ``llm_factory``
bypasses resolution entirely. They stay hermetic by monkeypatching
``make_llm_client`` to a recorder, so no provider SDK is constructed and no
credentials are needed. The complementary invariant — that *building* the app
imports no SDK — is pinned by ``tests/agents/intake/test_factory.py::
test_factory_import_does_not_load_anthropic`` (which calls ``create_app()``).
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from pathlib import Path

import pytest
from fastapi import FastAPI

from model_project_constructor.ui.intake import create_app

# ``make_llm_client`` is imported *inside* the production factory closure, so
# patching the name on its defining module is what the closure resolves.
_FACTORY_TARGET = "model_project_constructor.agents.intake.factory.make_llm_client"


@pytest.fixture
def record_make_llm_client(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, str | None]]:
    """Replace ``make_llm_client`` with a recorder of ``(provider, model)``.

    Returns the call log. The recorder returns a sentinel instead of a real
    client, so calling the production factory constructs no SDK.
    """

    calls: list[tuple[str, str | None]] = []
    sentinel = object()

    def _recorder(provider: str = "anthropic", *, model: str | None = None) -> object:
        calls.append((provider, model))
        return sentinel

    monkeypatch.setattr(_FACTORY_TARGET, _recorder)
    return calls


@pytest.fixture
def build_app(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Iterator[Callable[..., FastAPI]]:
    """Return a ``create_app`` wrapper with an isolated DB and cleared env.

    Each call gets its own SQLite file under ``tmp_path``; the provider/model
    env vars are cleared first so default-path tests are deterministic
    regardless of the developer's shell. Every store is closed on teardown.
    """

    monkeypatch.delenv("INTAKE_LLM_PROVIDER", raising=False)
    monkeypatch.delenv("INTAKE_LLM_MODEL", raising=False)
    counter = {"n": 0}
    apps: list[FastAPI] = []

    def _build(**kwargs: object) -> FastAPI:
        counter["n"] += 1
        db = tmp_path / f"intake_{counter['n']}.db"
        app = create_app(db_path=db, **kwargs)  # type: ignore[arg-type]
        apps.append(app)
        return app

    try:
        yield _build
    finally:
        for app in apps:
            app.state.store.close()


def test_default_provider_is_anthropic_with_provider_native_model(
    build_app: Callable[..., FastAPI],
    record_make_llm_client: list[tuple[str, str | None]],
) -> None:
    app = build_app()
    # Resolution is lazy: the factory is not called until a session needs it.
    assert record_make_llm_client == []
    app.state.store.llm_factory("sess-1")
    # Default provider, and model=None so make_llm_client picks the provider
    # default (never a hardcoded first-party id that would 400 on Bedrock).
    assert record_make_llm_client == [("anthropic", None)]


def test_provider_argument_overrides_default(
    build_app: Callable[..., FastAPI],
    record_make_llm_client: list[tuple[str, str | None]],
) -> None:
    app = build_app(provider="bedrock")
    app.state.store.llm_factory("sess-1")
    assert record_make_llm_client == [("bedrock", None)]


def test_env_selects_provider_and_model(
    build_app: Callable[..., FastAPI],
    record_make_llm_client: list[tuple[str, str | None]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("INTAKE_LLM_PROVIDER", "bedrock")
    monkeypatch.setenv("INTAKE_LLM_MODEL", "anthropic.claude-sonnet-4-6")
    app = build_app()
    app.state.store.llm_factory("sess-1")
    assert record_make_llm_client == [("bedrock", "anthropic.claude-sonnet-4-6")]


def test_argument_beats_environment(
    build_app: Callable[..., FastAPI],
    record_make_llm_client: list[tuple[str, str | None]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("INTAKE_LLM_PROVIDER", "bedrock")
    monkeypatch.setenv("INTAKE_LLM_MODEL", "anthropic.claude-from-env")
    app = build_app(provider="anthropic", model="claude-from-arg")
    app.state.store.llm_factory("sess-1")
    assert record_make_llm_client == [("anthropic", "claude-from-arg")]


def test_model_argument_threads_through(
    build_app: Callable[..., FastAPI],
    record_make_llm_client: list[tuple[str, str | None]],
) -> None:
    app = build_app(model="anthropic.claude-explicit")
    app.state.store.llm_factory("sess-1")
    assert record_make_llm_client == [("anthropic", "anthropic.claude-explicit")]


def test_unknown_provider_argument_rejected_at_create_app(
    build_app: Callable[..., FastAPI],
    record_make_llm_client: list[tuple[str, str | None]],
) -> None:
    with pytest.raises(ValueError) as exc_info:
        build_app(provider="openai")
    message = str(exc_info.value)
    assert "openai" in message
    assert "anthropic" in message
    assert "bedrock" in message
    # Rejected during resolution, before the factory is ever reached.
    assert record_make_llm_client == []


def test_unknown_provider_from_env_rejected_at_create_app(
    build_app: Callable[..., FastAPI],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("INTAKE_LLM_PROVIDER", "not-a-provider")
    with pytest.raises(ValueError) as exc_info:
        build_app()
    assert "not-a-provider" in str(exc_info.value)


def test_empty_string_env_falls_through_to_defaults(
    build_app: Callable[..., FastAPI],
    record_make_llm_client: list[tuple[str, str | None]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # An empty env var is falsy and must fall through the ``or`` chain rather
    # than being treated as a (then-unknown) provider or a blank model id.
    monkeypatch.setenv("INTAKE_LLM_PROVIDER", "")
    monkeypatch.setenv("INTAKE_LLM_MODEL", "")
    app = build_app()
    app.state.store.llm_factory("sess-1")
    assert record_make_llm_client == [("anthropic", None)]


def test_env_provider_with_argument_model_combine(
    build_app: Callable[..., FastAPI],
    record_make_llm_client: list[tuple[str, str | None]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Provider and model resolve independently: an env provider composes with
    # an explicit model argument.
    monkeypatch.setenv("INTAKE_LLM_PROVIDER", "bedrock")
    app = build_app(model="anthropic.claude-explicit")
    app.state.store.llm_factory("sess-1")
    assert record_make_llm_client == [("bedrock", "anthropic.claude-explicit")]


def test_injected_llm_factory_bypasses_provider_resolution(
    build_app: Callable[..., FastAPI],
    record_make_llm_client: list[tuple[str, str | None]],
) -> None:
    sentinel = object()

    def injected(_session_id: str) -> object:
        return sentinel

    # An explicit llm_factory wins outright: the otherwise-invalid provider is
    # never resolved or validated (the test seam must keep working unchanged).
    app = build_app(llm_factory=injected, provider="openai")
    assert app.state.store.llm_factory("sess-1") is sentinel
    assert record_make_llm_client == []
