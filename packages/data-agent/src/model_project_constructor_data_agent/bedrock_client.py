"""AWS Bedrock-hosted Claude client for the Data Agent (standalone wheel).

Bedrock-Claude speaks the **same Anthropic Messages API** as the first-party
``anthropic.Anthropic`` client — ``AnthropicBedrockMantle.messages.create`` is
signature-identical — so this client is the wheel's :class:`AnthropicLLMClient`
*pointed at Bedrock via the bedrock-mantle endpoint*. It overrides only:

1. **Construction** — an :class:`anthropic.AnthropicBedrockMantle` client,
   authenticated by a **Bedrock API key** (``AWS_BEARER_TOKEN_BEDROCK``) or, as a
   fallback, SigV4 from the AWS credential chain — rather than ``ANTHROPIC_API_KEY``.
2. **The default model id** — Bedrock model ids carry an ``anthropic.``
   provider prefix (e.g. ``anthropic.claude-sonnet-4-6``).

The five required :class:`LLMClient` methods, the optional
``rank_candidate_tables``, ``_call_claude``, the per-caller fenced-text
``_extract_json``, and ``_sanitize_prompt_field`` are **inherited unchanged**.
So **Decision C** (keep the fenced-text parser) holds by construction and
**Trap 5** (map parse / empty-response failures onto the seam error class) is
satisfied by the inherited guards, which already raise :class:`LLMParseError`.

**Decoupling (C4).** This module imports only from the wheel and the ``anthropic``
SDK — never the orchestrator (``tests/test_data_agent_decoupling.py``). It
subclasses the wheel's own ``AnthropicLLMClient`` rather than a shared helper,
so the one-way package dependency is preserved.

**Why subclass rather than duplicate.** The SDK ships ``AnthropicBedrockMantle``
as a drop-in for ``Anthropic``; a thin subclass expresses "the same Claude,
reached via Bedrock" with zero parser/method drift surface (a deliberate
as-built refinement of the plan's "one new client module" wording — see
``docs/planning/multi-provider-llm-plan.md`` Phase C as-built note. Session 178
switched this from ``AnthropicBedrock`` (SigV4-only, ``bedrock-runtime``) to
``AnthropicBedrockMantle`` so a Bedrock API key can be used — see
``docs/planning/bedrock-testing-enablement.md``.)

**Auth.** ``AnthropicBedrockMantle`` resolves auth from the environment: a
Bedrock API key in ``AWS_BEARER_TOKEN_BEDROCK`` selects bearer-token mode,
otherwise it falls back to SigV4 from the AWS credential chain — so the wheel
needs **no per-provider key resolver** (the Phase-A-deferred wheel resolver is a
no-op for Bedrock). Region comes from ``aws_region`` or, when unset, the
``AWS_REGION`` / ``AWS_DEFAULT_REGION`` env var; the endpoint then defaults to
``https://bedrock-mantle.{region}.api.aws/anthropic``. Pass ``aws_region``
explicitly when ``AWS_REGION`` is not set.
"""

from __future__ import annotations

from typing import Any

from model_project_constructor_data_agent.anthropic_client import (
    DEFAULT_MAX_TOKENS,
    AnthropicLLMClient,
)

#: Bedrock model ids carry an ``anthropic.`` provider prefix. The default tier
#: mirrors the first-party client's Sonnet default (``claude-sonnet-4-6``).
DEFAULT_MODEL = "anthropic.claude-sonnet-4-6"


class BedrockLLMClient(AnthropicLLMClient):
    """:class:`LLMClient` backed by AWS Bedrock-hosted Claude.

    Subclasses the wheel's :class:`AnthropicLLMClient`, overriding only
    construction (build an ``anthropic.AnthropicBedrockMantle`` client) and the
    Bedrock-prefixed default model. All required + optional protocol methods
    and the JSON parsing are inherited (see the module docstring).
    """

    def __init__(
        self,
        client: Any | None = None,
        model: str = DEFAULT_MODEL,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        *,
        aws_region: str | None = None,
    ) -> None:
        if client is None:
            # Lazy import so the factory / package __init__ stay SDK-free at
            # import time (test_factory_import_does_not_load_anthropic). Auth and
            # region self-discover from the environment: a Bedrock API key in
            # AWS_BEARER_TOKEN_BEDROCK (else SigV4 from the AWS chain); region
            # falls back to AWS_REGION / AWS_DEFAULT_REGION when not passed.
            import anthropic

            kwargs: dict[str, Any] = {}
            if aws_region is not None:
                kwargs["aws_region"] = aws_region
            client = anthropic.AnthropicBedrockMantle(**kwargs)
        super().__init__(client=client, model=model, max_tokens=max_tokens)
