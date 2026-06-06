"""Environment-variable driven settings for the orchestrator.

Phase 6 scope (architecture-plan §14): every secret and every
deployment-variable parameter must come from the environment (or a
``.env`` file loaded into the environment by the caller). There are no
hardcoded credentials or hostnames anywhere in the codebase.

This module intentionally uses ``os.environ`` and a plain dataclass
rather than a third-party settings library. The full matrix of env
vars is small enough that a manual loader is easier to read than a
``pydantic-settings`` BaseSettings subclass, and it keeps the core
package dependency-free.

``.env`` support is the caller's responsibility: load the file (e.g.
via ``python-dotenv`` in the agents extra) before constructing
:class:`OrchestratorSettings`. This module only reads ``os.environ``.

The full env-var matrix is documented in ``OPERATIONS.md``.
"""

from __future__ import annotations

import os
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Literal, cast

from model_project_constructor._vocab_guard import assert_vocab_parity

if TYPE_CHECKING:
    # Type-only import: pulling the protocol at runtime would trigger the
    # SDK-eager ``agents.website`` package __init__ and regress this module's
    # SDK-freeness. Under ``from __future__ import annotations`` the annotations
    # below are strings, so ``RepoClient`` is never looked up at runtime.
    from model_project_constructor.agents.website.protocol import RepoClient

HostLiteral = Literal["gitlab", "github"]


@dataclass(frozen=True)
class PlatformSpec:
    """Per-host configuration carried by the :data:`REPO_PLATFORMS` registry.

    Grown across Overhaul O3: Phase O3-1 introduced the two *data* fields
    (consumed first as host membership, then as the URL/token sources in O3-2);
    Phase O3-3 adds :attr:`adapter_factory`, so the registry now also decides
    which ``RepoClient`` adapter a live run builds. The factory lazy-imports its
    SDK inside the body, so importing this module stays SDK-free — the registry
    pulls ``python-gitlab`` / ``PyGithub`` only when an adapter is actually
    constructed.
    """

    default_api_url: str
    token_env_var: str
    adapter_factory: Callable[..., RepoClient]


def _make_gitlab_adapter(*, host_url: str, private_token: str) -> RepoClient:
    """Build the GitLab :class:`RepoClient` adapter (lazy SDK import).

    Imported inside the body so importing the registry never pulls
    ``python-gitlab``; the SDK loads only when a live run builds the adapter.
    """
    from model_project_constructor.agents.website.gitlab_adapter import (
        PythonGitLabAdapter,
    )

    return PythonGitLabAdapter(host_url=host_url, private_token=private_token)


def _make_github_adapter(*, host_url: str, private_token: str) -> RepoClient:
    """Build the GitHub :class:`RepoClient` adapter (lazy SDK import).

    The uniform ``(*, host_url, private_token)`` signature absorbs the
    constructor asymmetry (GitHub bakes a URL default and omits ``ssl_verify``);
    ``host_url`` is always passed explicitly so an ``MPC_HOST_URL`` override
    (e.g. GitHub Enterprise) wins over that baked default.
    """
    from model_project_constructor.agents.website.github_adapter import (
        PyGithubAdapter,
    )

    return PyGithubAdapter(host_url=host_url, private_token=private_token)


# The single source of truth for the host vocabulary: which repo hosts exist,
# their default API URL, and the env var that carries their token. ``.keys()``
# replaces the four independent membership declarations that previously listed
# ``{"gitlab", "github"}`` by hand (this module's validation tuple,
# ``cli.VALID_HOSTS``, ``run_pipeline``'s argparse ``choices``). ``HostLiteral``
# stays hand-written (mypy cannot read a runtime-derived ``Literal``) and is
# pinned to these keys by the import-time guard below.
REPO_PLATFORMS: dict[str, PlatformSpec] = {
    "gitlab": PlatformSpec(
        default_api_url="https://gitlab.com",
        token_env_var="GITLAB_TOKEN",
        adapter_factory=_make_gitlab_adapter,
    ),
    "github": PlatformSpec(
        default_api_url="https://api.github.com",
        token_env_var="GITHUB_TOKEN",
        adapter_factory=_make_github_adapter,
    ),
}

# Fail the build loudly if a host is added to one of ``REPO_PLATFORMS`` /
# ``HostLiteral`` but not the other (Audit #8 / O3; mirrors Audit #2's guard).
assert_vocab_parity(
    set(REPO_PLATFORMS),
    HostLiteral,
    name="REPO_PLATFORMS",
    reconcile_hint="Reconcile the REPO_PLATFORMS keys with HostLiteral in orchestrator/config.py.",
)

DEFAULT_CHECKPOINT_DIR = Path(".orchestrator/checkpoints")
DEFAULT_HOST: HostLiteral = "gitlab"
# Back-compat aliases over the single-source registry: tests import these by
# name (tests/orchestrator/test_config.py:15-16). Sourcing them from
# REPO_PLATFORMS keeps each URL written exactly once — inside the registry above.
DEFAULT_GITLAB_URL = REPO_PLATFORMS["gitlab"].default_api_url
DEFAULT_GITHUB_URL = REPO_PLATFORMS["github"].default_api_url
DEFAULT_LOG_LEVEL = "INFO"

_TRUTHY = {"1", "true", "yes", "on"}
_FALSY = {"0", "false", "no", "off"}


class ConfigError(ValueError):
    """Raised when environment configuration is invalid or incomplete."""


@dataclass(frozen=True)
class OrchestratorSettings:
    """Resolved orchestrator settings loaded from environment variables.

    Fields:

    - ``host`` — ``"gitlab"`` or ``"github"``. Defaults to ``"gitlab"``.
    - ``host_url`` — API base URL. Defaults to the public host for
      whichever platform was selected.
    - ``host_token`` — API token (``GITLAB_TOKEN`` or ``GITHUB_TOKEN``).
      Required for live runs. ``None`` is allowed so tests can
      construct a settings object without a real token.
    - ``checkpoint_dir`` — root directory for :class:`CheckpointStore`.
      Defaults to ``./.orchestrator/checkpoints``.
    - ``log_level`` — stdlib logging level name. Defaults to ``INFO``.
    - ``anthropic_api_key`` — credential for the Anthropic LLM gateway.
      Optional because the orchestrator is LLM-agnostic; only required
      by agent runners that actually call Anthropic.
    - ``namespace`` — target group/org path for the Website Agent (read
      from ``MPC_NAMESPACE``). Must be a path like ``rmsharp-modelpilot``
      or ``data-science/model-drafts`` — never a URL. ``None`` when
      unset; the pipeline script applies host-specific defaults.
    """

    host: HostLiteral
    host_url: str
    host_token: str | None
    checkpoint_dir: Path
    log_level: str
    anthropic_api_key: str | None
    namespace: str | None

    @classmethod
    def from_env(
        cls,
        env: Mapping[str, str] | None = None,
    ) -> OrchestratorSettings:
        """Construct a settings object from a mapping (defaults to
        ``os.environ``). Raises :class:`ConfigError` on invalid values.

        Accepting an explicit ``env`` mapping keeps the loader fully
        testable without ``monkeypatch`` gymnastics.
        """

        source: Mapping[str, str] = env if env is not None else os.environ

        host_raw = source.get("MPC_HOST", DEFAULT_HOST).strip().lower()
        if host_raw not in REPO_PLATFORMS:
            raise ConfigError(
                f"MPC_HOST must be one of {sorted(REPO_PLATFORMS)}, got {host_raw!r}"
            )
        # ``host_raw`` was validated above to be a REPO_PLATFORMS key, and the
        # import-time guard pins those keys == HostLiteral members, so the cast
        # is sound — and lets a future host resolve without editing this line.
        host: HostLiteral = cast(HostLiteral, host_raw)

        default_url = REPO_PLATFORMS[host].default_api_url
        host_url = source.get("MPC_HOST_URL", default_url).strip()
        if not host_url:
            raise ConfigError("MPC_HOST_URL must not be empty")

        token_var = REPO_PLATFORMS[host].token_env_var
        host_token = source.get(token_var) or None

        checkpoint_dir = Path(
            source.get("MPC_CHECKPOINT_DIR", str(DEFAULT_CHECKPOINT_DIR))
        ).expanduser()

        log_level = source.get("MPC_LOG_LEVEL", DEFAULT_LOG_LEVEL).strip().upper()
        if log_level not in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
            raise ConfigError(
                f"MPC_LOG_LEVEL must be a stdlib logging level, got {log_level!r}"
            )

        anthropic_api_key = source.get("ANTHROPIC_API_KEY") or None

        namespace_raw = source.get("MPC_NAMESPACE", "").strip()
        namespace = validate_namespace(namespace_raw) if namespace_raw else None

        return cls(
            host=host,
            host_url=host_url,
            host_token=host_token,
            checkpoint_dir=checkpoint_dir,
            log_level=log_level,
            anthropic_api_key=anthropic_api_key,
            namespace=namespace,
        )

    def require_host_token(self) -> str:
        """Return the host API token, raising if it is missing.

        Agent runners that actually make HTTP calls to a live host call
        this; test code constructing :class:`OrchestratorSettings`
        without a token does not.
        """

        if not self.host_token:
            var = REPO_PLATFORMS[self.host].token_env_var
            raise ConfigError(
                f"{var} is required for host={self.host!r} but was not set"
            )
        return self.host_token

    def require_anthropic_api_key(self) -> str:
        if not self.anthropic_api_key:
            raise ConfigError("ANTHROPIC_API_KEY is required but was not set")
        return self.anthropic_api_key


def parse_bool(raw: str) -> bool:
    """Parse a common env-var boolean string. Raises on unknown values."""

    lowered = raw.strip().lower()
    if lowered in _TRUTHY:
        return True
    if lowered in _FALSY:
        return False
    raise ConfigError(f"cannot parse {raw!r} as bool")


def validate_namespace(raw: str) -> str:
    """Validate ``MPC_NAMESPACE`` is a group/org path, not a URL.

    The GitLab and GitHub adapters look up a group/org by path
    (``namespace.get("rmsharp-modelpilot")``), not by URL. Pasting the
    full GitLab group URL (``https://gitlab.com/rmsharp-modelpilot``)
    surfaces as a generic ``404`` from the adapter, which is a poor
    error for an operator to debug. Fail fast here with a clearer
    message.
    """

    lowered = raw.strip().lower()
    if lowered.startswith(("http://", "https://")):
        raise ConfigError(
            f"MPC_NAMESPACE must be a group path, not a URL; got {raw!r}. "
            f"Use the path only, e.g. 'rmsharp-modelpilot' "
            f"instead of 'https://gitlab.com/rmsharp-modelpilot'."
        )
    return raw


__all__ = [
    "DEFAULT_CHECKPOINT_DIR",
    "DEFAULT_GITHUB_URL",
    "DEFAULT_GITLAB_URL",
    "DEFAULT_HOST",
    "DEFAULT_LOG_LEVEL",
    "REPO_PLATFORMS",
    "ConfigError",
    "HostLiteral",
    "OrchestratorSettings",
    "PlatformSpec",
    "parse_bool",
    "validate_namespace",
]
