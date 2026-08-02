"""Provider seam for the Data Agent's LLM client.

The Data Agent talks to its LLM only through the :class:`LLMClient` protocol
(``llm.py``). Until now every call site hardwired the one concrete
implementation (:class:`AnthropicLLMClient`) and the provider choice was
implicit in *which symbol you imported*. This factory makes the choice
explicit: callers name a provider and get back an :class:`LLMClient`, so a
second provider becomes one new client module plus one branch here — no
edits at the call sites.

The known-provider list is single-sourced from the :data:`LLMProvider`
``Literal`` via :func:`typing.get_args`, matching the in-wheel derivation
style already used for ``RowCountOrder`` in ``anthropic_client.py`` — so the
error message cannot drift from the set of providers the factory actually
handles.

This module lives **in the standalone wheel** and imports only from the
wheel and the stdlib; it does not touch the main package (decoupling
boundary, ``tests/test_data_agent_decoupling.py``).
"""

from __future__ import annotations

from typing import Literal, get_args

from model_project_constructor_data_agent.llm import LLMClient

#: Providers this factory can construct. Add a member here (and a branch in
#: :func:`make_llm_client`) when wiring a new backend; the CLI ``--provider``
#: help and the unknown-provider error both derive their list from this.
#: ``bedrock`` is AWS Bedrock-hosted Claude (plan Phase C); ``opencode`` shells
#: out to the ``opencode`` CLI, which is itself a multi-vendor multiplexer
#: (AD-11) — kept in lockstep with the intake factory's ``Literal`` and the
#: orchestrator ``LLM_PROVIDERS``.
LLMProvider = Literal["anthropic", "bedrock", "opencode"]

KNOWN_PROVIDERS: tuple[str, ...] = get_args(LLMProvider)


def make_llm_client(
    provider: str = "anthropic",
    *,
    model: str | None = None,
    sql_dialect: str | None = None,
) -> LLMClient:
    """Construct the concrete :class:`LLMClient` for ``provider``.

    ``provider`` is typed as ``str`` (not :data:`LLMProvider`) because the
    value usually arrives from a CLI flag; unknown values raise
    :class:`ValueError` listing the providers this factory handles, rather
    than failing later inside the concrete client.

    ``model`` is forwarded to the concrete client; when ``None`` (the default)
    the provider's own default model is used.

    ``sql_dialect`` names the dialect the generated SQL must execute on (e.g.
    ``"sqlite"``, ``"postgresql"``). Callers that have a database URL should
    derive it with
    :func:`model_project_constructor_data_agent.db.sql_dialect_from_url` rather
    than hardcoding a string, so the prompt cannot drift from the database the
    SQL actually runs against. ``None`` (the default) leaves the dialect
    unstated — the pre-dialect behaviour.
    """
    if provider == "anthropic":
        # Lazy import so this module — and the package __init__ that re-exports
        # it — stays free of the anthropic SDK at import time. The standalone
        # wheel otherwise imports anthropic only when a real client is built.
        from model_project_constructor_data_agent.anthropic_client import (
            DEFAULT_MODEL,
            AnthropicLLMClient,
        )

        return AnthropicLLMClient(
            model=DEFAULT_MODEL if model is None else model, sql_dialect=sql_dialect
        )
    if provider == "bedrock":
        # Lazy import (same rationale as the anthropic branch): keep this module
        # SDK-free at import time. ``BedrockLLMClient`` is the anthropic client
        # pointed at AWS Bedrock; AWS credentials are self-discovered by the SDK.
        from model_project_constructor_data_agent.bedrock_client import (
            DEFAULT_MODEL,
            BedrockLLMClient,
        )

        return BedrockLLMClient(
            model=DEFAULT_MODEL if model is None else model, sql_dialect=sql_dialect
        )
    if provider == "opencode":
        # Lazy import for consistency with the branches above — this client
        # imports no SDK at all (stdlib only), but the convention is what
        # ``test_factory_import_does_not_load_anthropic`` pins, and consistency
        # is cheaper than an exception. ``DEFAULT_MODEL`` is ``None`` here: the
        # operator's own OpenCode config picks the vendor, which is the point
        # (spec D6). Construction fails fast if the binary is absent.
        #
        # Aliased on import because this provider's ``DEFAULT_MODEL`` is
        # ``str | None`` while its siblings' are ``str``; the branches share one
        # function scope, so importing the bare name twice is a type conflict.
        from model_project_constructor_data_agent.opencode_client import (
            DEFAULT_MODEL as OPENCODE_DEFAULT_MODEL,
        )
        from model_project_constructor_data_agent.opencode_client import (
            OpenCodeLLMClient,
        )

        return OpenCodeLLMClient(
            model=OPENCODE_DEFAULT_MODEL if model is None else model,
            sql_dialect=sql_dialect,
        )
    raise ValueError(
        f"Unknown LLM provider {provider!r}. "
        f"Known providers: {', '.join(KNOWN_PROVIDERS)}."
    )
