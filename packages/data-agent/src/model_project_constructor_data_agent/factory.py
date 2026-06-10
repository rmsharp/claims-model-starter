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

from model_project_constructor_data_agent.anthropic_client import (
    DEFAULT_MODEL,
    AnthropicLLMClient,
)
from model_project_constructor_data_agent.llm import LLMClient

#: Providers this factory can construct. Add a member here (and a branch in
#: :func:`make_llm_client`) when wiring a new backend; the CLI ``--provider``
#: help and the unknown-provider error both derive their list from this.
LLMProvider = Literal["anthropic"]

KNOWN_PROVIDERS: tuple[str, ...] = get_args(LLMProvider)


def make_llm_client(
    provider: str = "anthropic",
    *,
    model: str = DEFAULT_MODEL,
) -> LLMClient:
    """Construct the concrete :class:`LLMClient` for ``provider``.

    ``provider`` is typed as ``str`` (not :data:`LLMProvider`) because the
    value usually arrives from a CLI flag; unknown values raise
    :class:`ValueError` listing the providers this factory handles, rather
    than failing later inside the concrete client.

    ``model`` is forwarded to the concrete client and defaults to that
    provider's default model.
    """
    if provider == "anthropic":
        return AnthropicLLMClient(model=model)
    raise ValueError(
        f"Unknown LLM provider {provider!r}. "
        f"Known providers: {', '.join(KNOWN_PROVIDERS)}."
    )
