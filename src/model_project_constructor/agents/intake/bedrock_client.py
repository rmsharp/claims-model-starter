"""AWS Bedrock-hosted Claude client for the Intake Agent.

Bedrock-Claude speaks the **same Anthropic Messages API** as the first-party
``anthropic.Anthropic`` client — ``AnthropicBedrockMantle.messages.create`` is
signature-identical — so this client is simply the first-party
:class:`AnthropicLLMClient` *pointed at Bedrock via the bedrock-mantle endpoint*.
It overrides only two things:

1. **Construction** — an :class:`anthropic.AnthropicBedrockMantle` client,
   authenticated by a **Bedrock API key** (``AWS_BEARER_TOKEN_BEDROCK``) or, as a
   fallback, SigV4 from the AWS credential chain — rather than ``ANTHROPIC_API_KEY``.
2. **The default model id** — Bedrock model ids carry an ``anthropic.``
   provider prefix (e.g. ``anthropic.claude-sonnet-4-6``).

Every interview method (``next_question`` / ``draft_report`` /
``classify_governance`` / ``revise_report``), the ``_call_json`` round-trip,
and the fenced-text ``_extract_json`` parser are **inherited unchanged**. So:

* **Decision C** (keep the fenced-text ``_extract_json`` convention for the
  first second-provider) holds by construction — there is no second parser.
* **Trap 5** (map the SDK's parse / empty-response failures onto the seam's
  error class) is satisfied by the inherited ``_call_json`` guards, which
  already raise :class:`IntakeLLMError`. ``AnthropicBedrockMantle`` raises the
  same ``anthropic.*`` exception types as the base client (it is the same SDK), so
  the error behaviour is identical to the ``anthropic`` provider.

**Why subclass rather than duplicate.** The cross-package duplication of the
two ``AnthropicLLMClient``s is *forced* by C4 (the standalone data-agent wheel
cannot import the orchestrator). Within this package there is no such force, and
the SDK ships ``AnthropicBedrockMantle`` as a drop-in for ``Anthropic`` — so a thin
subclass expresses the truth ("the same Claude, reached via Bedrock") with zero
parser/method drift surface. (This is a deliberate as-built refinement of the
plan's "one new client module" wording — see
``docs/planning/multi-provider-llm-plan.md`` Phase C as-built note. The original
build targeted ``AnthropicBedrock`` (SigV4-only, ``bedrock-runtime``); Session
178 switched it to ``AnthropicBedrockMantle`` so the operator can authenticate
with a Bedrock API key — see ``docs/planning/bedrock-testing-enablement.md``.)

**Auth.** ``AnthropicBedrockMantle`` resolves auth from the environment: a
Bedrock API key in ``AWS_BEARER_TOKEN_BEDROCK`` selects bearer-token mode,
otherwise it falls back to SigV4 from the AWS credential chain (keys / shared
profile / IAM role). Region comes from ``aws_region`` or, when unset, the
``AWS_REGION`` / ``AWS_DEFAULT_REGION`` env var; the endpoint then defaults to
``https://bedrock-mantle.{region}.api.aws/anthropic``. There is therefore **no
per-provider key resolver to wire** — the Phase-A-deferred resolver is a no-op
for Bedrock. Pass ``aws_region`` explicitly when ``AWS_REGION`` is not set.
"""

from __future__ import annotations

from typing import Any

from model_project_constructor.agents.intake.anthropic_client import (
    DEFAULT_MAX_TOKENS,
    AnthropicLLMClient,
)

#: Bedrock model ids carry an ``anthropic.`` provider prefix. The default tier
#: mirrors the first-party client's Sonnet default (``claude-sonnet-4-6``); the
#: pilot entrypoint still selects Opus first-party — the intentional two-tier
#: default is preserved (Trap 4 / ``PROJECT_LEARNINGS`` #20).
DEFAULT_MODEL = "anthropic.claude-sonnet-4-6"


class BedrockLLMClient(AnthropicLLMClient):
    """:class:`IntakeLLMClient` backed by AWS Bedrock-hosted Claude.

    Subclasses :class:`AnthropicLLMClient`, overriding only construction (build
    an ``anthropic.AnthropicBedrockMantle`` client) and the Bedrock-prefixed
    default model. All four interview methods and the JSON parsing are inherited
    (see the module docstring).
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
