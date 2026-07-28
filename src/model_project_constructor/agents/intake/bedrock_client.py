"""AWS Bedrock-hosted Claude client for the Intake Agent.

Bedrock-Claude speaks the **same Anthropic Messages API** as the first-party
``anthropic.Anthropic`` client — ``AnthropicBedrockMantle.messages.create`` is
signature-identical — so this client is simply the first-party
:class:`AnthropicLLMClient` *pointed at Bedrock via the bedrock-mantle endpoint*.
It overrides only two things:

1. **Construction** — an :class:`anthropic.AnthropicBedrockMantle` client,
   authenticated by **SigV4 from the AWS credential chain (an IAM role)** or, as
   a dev-only fallback, a **Bedrock API key** (``AWS_BEARER_TOKEN_BEDROCK``) —
   rather than ``ANTHROPIC_API_KEY``.
2. **The default model id** — Bedrock model ids carry an ``anthropic.``
   provider prefix (e.g. ``anthropic.claude-opus-4-8``).

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
``docs/architecture-history/multi-provider-llm-plan.md`` Phase C as-built note. The original
build targeted ``AnthropicBedrock`` (SigV4-only, ``bedrock-runtime``); Session
178 switched it to ``AnthropicBedrockMantle`` so the operator can authenticate
with a Bedrock API key — see ``docs/architecture-history/bedrock-testing-enablement.md``.)

**Auth (enterprise-first).** ``AnthropicBedrockMantle`` resolves auth from the
AWS credential chain and signs with **SigV4**, so the recommended production path
is an **IAM role** (IRSA / instance profile / ECS task role / SSO) with **no
static keys** and ``AWS_BEARER_TOKEN_BEDROCK`` **unset** — the constructor
supports this with no extra wiring. As a *dev-only* fallback, a short-term
Bedrock API key in ``AWS_BEARER_TOKEN_BEDROCK`` selects bearer-token mode; it
**silently overrides SigV4**, so keep it unset in production (pass
``require_sigv4=True`` to turn a stray token into a hard error). Region comes
from ``aws_region`` or, when unset, ``AWS_REGION`` / ``AWS_DEFAULT_REGION``; the
endpoint then defaults to ``https://bedrock-mantle.{region}.api.aws/anthropic``.
For enterprise networking, pass ``base_url`` to target a PrivateLink VPCE host
(when Private DNS is off) or a GovCloud host, and ``http_client`` — e.g.
``anthropic.DefaultHttpxClient(proxy=…, verify=<corp CA bundle>)`` — for a
forward proxy / TLS-inspection CA. See ``docs/deployment/bedrock-enterprise.md``.
"""

from __future__ import annotations

import os
from typing import Any

from model_project_constructor.agents.intake.anthropic_client import (
    DEFAULT_MAX_TOKENS,
    AnthropicLLMClient,
)

#: Bedrock model ids carry an ``anthropic.`` provider prefix. AWS Bedrock's mantle
#: catalog offers **no Sonnet** tier, so the bedrock default is Opus 4.8 — it
#: intentionally differs from the first-party/anthropic client's Sonnet default
#: (Session 178; see ``docs/architecture-history/bedrock-testing-enablement.md``).
DEFAULT_MODEL = "anthropic.claude-opus-4-8"


class BedrockLLMClient(AnthropicLLMClient):
    """:class:`IntakeLLMClient` backed by AWS Bedrock-hosted Claude.

    Subclasses :class:`AnthropicLLMClient`, overriding only construction (build
    an ``anthropic.AnthropicBedrockMantle`` client) and the Bedrock-prefixed
    default model. All four interview methods and the JSON parsing are inherited
    (see the module docstring). The optional ``base_url`` / ``http_client`` /
    ``require_sigv4`` keyword args are enterprise-networking / hardening hooks
    (see the module docstring's Auth note and
    ``docs/deployment/bedrock-enterprise.md``).
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
        require_sigv4: bool = False,
    ) -> None:
        if client is None:
            # Lazy import so the factory / package __init__ stay SDK-free at
            # import time (test_factory_import_does_not_load_anthropic). Auth and
            # region self-discover from the environment: SigV4 from the AWS
            # credential chain (an IAM role) by default, or a Bedrock API key in
            # AWS_BEARER_TOKEN_BEDROCK (dev only); region falls back to
            # AWS_REGION / AWS_DEFAULT_REGION when not passed.
            if require_sigv4 and os.environ.get("AWS_BEARER_TOKEN_BEDROCK"):
                raise ValueError(
                    "require_sigv4=True but AWS_BEARER_TOKEN_BEDROCK is set: a "
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
