"""AWS Bedrock-hosted Claude client for the Data Agent (standalone wheel).

Bedrock-Claude speaks the **same Anthropic Messages API** as the first-party
``anthropic.Anthropic`` client — ``AnthropicBedrockMantle.messages.create`` is
signature-identical — so this client is the wheel's :class:`AnthropicLLMClient`
*pointed at Bedrock via the bedrock-mantle endpoint*. It overrides only:

1. **Construction** — an :class:`anthropic.AnthropicBedrockMantle` client,
   authenticated by **SigV4 from the AWS credential chain (an IAM role)** or, as
   a dev-only fallback, a **Bedrock API key** (``AWS_BEARER_TOKEN_BEDROCK``) —
   rather than ``ANTHROPIC_API_KEY``.
2. **The default model id** — Bedrock model ids carry an ``anthropic.``
   provider prefix (e.g. ``anthropic.claude-opus-4-8``).

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
``docs/architecture-history/multi-provider-llm-plan.md`` Phase C as-built note. Session 178
switched this from ``AnthropicBedrock`` (SigV4-only, ``bedrock-runtime``) to
``AnthropicBedrockMantle`` so a Bedrock API key can be used — see
``docs/architecture-history/bedrock-testing-enablement.md``.)

**Auth (enterprise-first).** ``AnthropicBedrockMantle`` resolves auth from the
AWS credential chain and signs with **SigV4**, so the recommended production path
is an **IAM role** (IRSA / instance profile / ECS task role / SSO) with **no
static keys** and ``AWS_BEARER_TOKEN_BEDROCK`` / ``ANTHROPIC_AWS_API_KEY``
**unset** — the wheel needs **no per-provider key resolver** (the
Phase-A-deferred wheel resolver is a no-op for Bedrock). As a *dev-only*
fallback, a short-term Bedrock API key in either ``AWS_BEARER_TOKEN_BEDROCK`` or
``ANTHROPIC_AWS_API_KEY`` (the SDK honors both — ``_MANTLE_API_KEY_ENV_VARS``)
selects bearer-token mode; it **silently overrides SigV4**, so keep both unset in
production (pass ``require_sigv4=True``, or set ``BEDROCK_REQUIRE_SIGV4=1`` in the
environment, to turn a stray key in *either* variable into a hard error). Region
comes from ``aws_region`` or, when unset, ``AWS_REGION`` / ``AWS_DEFAULT_REGION``;
the endpoint then defaults to
``https://bedrock-mantle.{region}.api.aws/anthropic``. For enterprise networking,
pass ``base_url`` to target a PrivateLink VPCE host (when Private DNS is off) or
a GovCloud host, and ``http_client`` — e.g. ``anthropic.DefaultHttpxClient(proxy=…,
verify=<corp CA bundle>)`` — for a forward proxy / TLS-inspection CA. See
``docs/deployment/bedrock-enterprise.md``.
"""

from __future__ import annotations

import os
from typing import Any

from model_project_constructor_data_agent.anthropic_client import (
    DEFAULT_MAX_TOKENS,
    AnthropicLLMClient,
)

#: Bedrock model ids carry an ``anthropic.`` provider prefix. AWS Bedrock's mantle
#: catalog offers **no Sonnet** tier, so the bedrock default is Opus 4.8 — it
#: intentionally differs from the first-party/anthropic client's Sonnet default
#: (Session 178; see ``docs/architecture-history/bedrock-testing-enablement.md``).
DEFAULT_MODEL = "anthropic.claude-opus-4-8"

#: Bedrock-mantle bearer-token / API-key env vars the SDK's
#: ``AnthropicBedrockMantle`` honors for auth (mirrors
#: ``anthropic.lib.bedrock._mantle._MANTLE_API_KEY_ENV_VARS`` at SDK 0.94.1) —
#: either one silently overrides SigV4 when set, so the ``require_sigv4`` guard
#: below must reject both, not just the first-documented name (D13).
_BEDROCK_API_KEY_ENV_VARS = ("AWS_BEARER_TOKEN_BEDROCK", "ANTHROPIC_AWS_API_KEY")

#: Case-insensitive truthy spellings accepted by ``BEDROCK_REQUIRE_SIGV4``.
_TRUTHY_ENV_VALUES = {"1", "true", "yes", "on"}


class BedrockLLMClient(AnthropicLLMClient):
    """:class:`LLMClient` backed by AWS Bedrock-hosted Claude.

    Subclasses the wheel's :class:`AnthropicLLMClient`, overriding only
    construction (build an ``anthropic.AnthropicBedrockMantle`` client) and the
    Bedrock-prefixed default model. All required + optional protocol methods
    and the JSON parsing are inherited (see the module docstring). The optional
    ``base_url`` / ``http_client`` / ``require_sigv4`` keyword args are
    enterprise-networking / hardening hooks (see the module docstring's Auth
    note and ``docs/deployment/bedrock-enterprise.md``). ``require_sigv4``
    defaults from ``BEDROCK_REQUIRE_SIGV4`` when not passed explicitly (D13) —
    an explicit ``True``/``False`` always wins over the env var.
    """

    def __init__(
        self,
        client: Any | None = None,
        model: str = DEFAULT_MODEL,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        *,
        aws_region: str | None = None,
        base_url: str | None = None,
        http_client: Any | None = None,
        require_sigv4: bool | None = None,
    ) -> None:
        if client is None:
            # Lazy import so the factory / package __init__ stay SDK-free at
            # import time (test_factory_import_does_not_load_anthropic). Auth and
            # region self-discover from the environment: SigV4 from the AWS
            # credential chain (an IAM role) by default, or a Bedrock API key in
            # AWS_BEARER_TOKEN_BEDROCK / ANTHROPIC_AWS_API_KEY (dev only); region
            # falls back to AWS_REGION / AWS_DEFAULT_REGION when not passed.
            if require_sigv4 is None:
                require_sigv4 = (
                    os.environ.get("BEDROCK_REQUIRE_SIGV4", "").strip().lower()
                    in _TRUTHY_ENV_VALUES
                )

            stray_key_env = next(
                (var for var in _BEDROCK_API_KEY_ENV_VARS if os.environ.get(var)),
                None,
            )
            if require_sigv4 and stray_key_env:
                raise ValueError(
                    f"require_sigv4=True but {stray_key_env} is set: a "
                    "bearer token overrides SigV4 and bypasses the IAM role. "
                    "Unset it for role-based (enterprise) auth."
                )

            import anthropic

            kwargs: dict[str, Any] = {}
            if aws_region is not None:
                kwargs["aws_region"] = aws_region
            if base_url is not None:
                kwargs["base_url"] = base_url
            if http_client is not None:
                kwargs["http_client"] = http_client
            client = anthropic.AnthropicBedrockMantle(**kwargs)
        super().__init__(client=client, model=model, max_tokens=max_tokens)
