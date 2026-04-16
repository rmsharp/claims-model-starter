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
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

HostLiteral = Literal["gitlab", "github"]

DEFAULT_CHECKPOINT_DIR = Path(".orchestrator/checkpoints")
DEFAULT_HOST: HostLiteral = "gitlab"
DEFAULT_GITLAB_URL = "https://gitlab.com"
DEFAULT_GITHUB_URL = "https://api.github.com"
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
    """

    host: HostLiteral
    host_url: str
    host_token: str | None
    checkpoint_dir: Path
    log_level: str
    anthropic_api_key: str | None

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
        if host_raw not in ("gitlab", "github"):
            raise ConfigError(
                f"MPC_HOST must be 'gitlab' or 'github', got {host_raw!r}"
            )
        host: HostLiteral = "gitlab" if host_raw == "gitlab" else "github"

        default_url = DEFAULT_GITLAB_URL if host == "gitlab" else DEFAULT_GITHUB_URL
        host_url = source.get("MPC_HOST_URL", default_url).strip()
        if not host_url:
            raise ConfigError("MPC_HOST_URL must not be empty")

        token_var = "GITLAB_TOKEN" if host == "gitlab" else "GITHUB_TOKEN"
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

        return cls(
            host=host,
            host_url=host_url,
            host_token=host_token,
            checkpoint_dir=checkpoint_dir,
            log_level=log_level,
            anthropic_api_key=anthropic_api_key,
        )

    def require_host_token(self) -> str:
        """Return the host API token, raising if it is missing.

        Agent runners that actually make HTTP calls to a live host call
        this; test code constructing :class:`OrchestratorSettings`
        without a token does not.
        """

        if not self.host_token:
            var = "GITLAB_TOKEN" if self.host == "gitlab" else "GITHUB_TOKEN"
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


__all__ = [
    "DEFAULT_CHECKPOINT_DIR",
    "DEFAULT_GITHUB_URL",
    "DEFAULT_GITLAB_URL",
    "DEFAULT_HOST",
    "DEFAULT_LOG_LEVEL",
    "ConfigError",
    "HostLiteral",
    "OrchestratorSettings",
    "parse_bool",
]
