"""Provider seam for the Intake Agent's LLM client.

The Intake Agent talks to its LLM only through the :class:`IntakeLLMClient`
protocol (``protocol.py``). Until now every call site hardwired the one
concrete implementation (:class:`AnthropicLLMClient`) and the provider choice
was implicit in *which symbol you imported*. This factory makes the choice
explicit: callers name a provider and get back an :class:`IntakeLLMClient`,
so a second provider becomes one new client module plus one branch here — no
edits at the call sites.

This mirrors the Data Agent's ``factory.py`` but is kept **separate on
purpose**: the intake and data-agent clients share no methods and live in
different packages (see ``protocol.py`` and the data-agent decoupling
boundary). The two factories are parallel, not shared.

The known-provider list is single-sourced from the :data:`LLMProvider`
``Literal`` via :func:`typing.get_args`, so the unknown-provider error cannot
drift from the set of providers the factory actually handles.
"""

from __future__ import annotations

from typing import Literal, get_args

from model_project_constructor.agents.intake.protocol import IntakeLLMClient

#: Providers this factory can construct. Add a member here (and a branch in
#: :func:`make_llm_client`) when wiring a new backend; the unknown-provider
#: error derives its list from this. ``bedrock`` is AWS Bedrock-hosted Claude
#: (plan Phase C); ``opencode`` shells out to the ``opencode`` CLI, which is
#: itself a multi-vendor multiplexer (AD-11) — kept in lockstep with the
#: data-agent factory's ``Literal`` and the orchestrator ``LLM_PROVIDERS``
#: registry.
LLMProvider = Literal["anthropic", "bedrock", "opencode"]

KNOWN_PROVIDERS: tuple[str, ...] = get_args(LLMProvider)


def make_llm_client(
    provider: str = "anthropic",
    *,
    model: str | None = None,
) -> IntakeLLMClient:
    """Construct the concrete :class:`IntakeLLMClient` for ``provider``.

    ``provider`` is typed as ``str`` (not :data:`LLMProvider`) because the
    value usually arrives from a CLI flag; unknown values raise
    :class:`ValueError` listing the providers this factory handles, rather
    than failing later inside the concrete client.

    ``model`` is forwarded to the concrete client; when ``None`` (the default)
    the provider's own default model is used.
    """
    if provider == "anthropic":
        # Lazy import so this module — and anything that re-exports it, e.g. the
        # package __init__ — stays free of the anthropic SDK at import time,
        # matching the lazy-construction convention at every call site
        # (ui/intake/app.py, run_pipeline.py, AnthropicLLMClient.__init__).
        from model_project_constructor.agents.intake.anthropic_client import (
            DEFAULT_MODEL,
            AnthropicLLMClient,
        )

        return AnthropicLLMClient(model=DEFAULT_MODEL if model is None else model)
    if provider == "bedrock":
        # Lazy import (same rationale as the anthropic branch): keep this module
        # SDK-free at import time. ``BedrockLLMClient`` is the anthropic client
        # pointed at AWS Bedrock; AWS credentials are self-discovered by the SDK.
        from model_project_constructor.agents.intake.bedrock_client import (
            DEFAULT_MODEL,
            BedrockLLMClient,
        )

        return BedrockLLMClient(model=DEFAULT_MODEL if model is None else model)
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
        from model_project_constructor.agents.intake.opencode_client import (
            DEFAULT_MODEL as OPENCODE_DEFAULT_MODEL,
        )
        from model_project_constructor.agents.intake.opencode_client import (
            OpenCodeLLMClient,
        )

        return OpenCodeLLMClient(model=OPENCODE_DEFAULT_MODEL if model is None else model)
    raise ValueError(
        f"Unknown LLM provider {provider!r}. "
        f"Known providers: {', '.join(KNOWN_PROVIDERS)}."
    )
