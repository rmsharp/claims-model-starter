"""Tests for :mod:`model_project_constructor.orchestrator.config`.

Phase 6 scope: verify env-var loading, defaults, validation, and the
``require_*`` guards used by agent runners that hit live hosts.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from model_project_constructor.orchestrator.config import (
    DEFAULT_CHECKPOINT_DIR,
    DEFAULT_GITHUB_URL,
    DEFAULT_GITLAB_URL,
    DEFAULT_LLM_PROVIDER,
    LLM_PROVIDERS,
    ConfigError,
    OrchestratorSettings,
    parse_bool,
    validate_namespace,
)


class TestFromEnvDefaults:
    def test_empty_env_uses_gitlab_defaults(self) -> None:
        s = OrchestratorSettings.from_env({})
        assert s.host == "gitlab"
        assert s.host_url == DEFAULT_GITLAB_URL
        assert s.host_token is None
        assert s.checkpoint_dir == DEFAULT_CHECKPOINT_DIR
        assert s.log_level == "INFO"
        assert s.anthropic_api_key is None
        assert s.namespace is None

    def test_namespace_group_path(self) -> None:
        s = OrchestratorSettings.from_env({"MPC_NAMESPACE": "rmsharp-modelpilot"})
        assert s.namespace == "rmsharp-modelpilot"

    def test_namespace_nested_group_path(self) -> None:
        s = OrchestratorSettings.from_env(
            {"MPC_NAMESPACE": "data-science/model-drafts"}
        )
        assert s.namespace == "data-science/model-drafts"

    def test_namespace_empty_string_treated_as_unset(self) -> None:
        s = OrchestratorSettings.from_env({"MPC_NAMESPACE": "   "})
        assert s.namespace is None

    def test_github_default_host_url(self) -> None:
        s = OrchestratorSettings.from_env({"MPC_HOST": "github"})
        assert s.host == "github"
        assert s.host_url == DEFAULT_GITHUB_URL

    def test_host_case_insensitive(self) -> None:
        s = OrchestratorSettings.from_env({"MPC_HOST": "GitHub"})
        assert s.host == "github"

    def test_explicit_host_url_overrides_default(self) -> None:
        s = OrchestratorSettings.from_env(
            {"MPC_HOST": "gitlab", "MPC_HOST_URL": "https://gitlab.example.com"}
        )
        assert s.host_url == "https://gitlab.example.com"

    def test_checkpoint_dir_override(self) -> None:
        s = OrchestratorSettings.from_env({"MPC_CHECKPOINT_DIR": "/tmp/chk"})
        assert s.checkpoint_dir == Path("/tmp/chk")

    def test_log_level_override(self) -> None:
        s = OrchestratorSettings.from_env({"MPC_LOG_LEVEL": "debug"})
        assert s.log_level == "DEBUG"


class TestFromEnvTokens:
    def test_gitlab_token_loaded(self) -> None:
        s = OrchestratorSettings.from_env(
            {"MPC_HOST": "gitlab", "GITLAB_TOKEN": "glpat-xyz"}
        )
        assert s.host_token == "glpat-xyz"

    def test_github_token_loaded(self) -> None:
        s = OrchestratorSettings.from_env(
            {"MPC_HOST": "github", "GITHUB_TOKEN": "ghp_xyz"}
        )
        assert s.host_token == "ghp_xyz"

    def test_gitlab_ignores_github_token(self) -> None:
        s = OrchestratorSettings.from_env(
            {"MPC_HOST": "gitlab", "GITHUB_TOKEN": "ghp_xyz"}
        )
        assert s.host_token is None

    def test_empty_token_treated_as_missing(self) -> None:
        s = OrchestratorSettings.from_env(
            {"MPC_HOST": "gitlab", "GITLAB_TOKEN": ""}
        )
        assert s.host_token is None

    def test_anthropic_api_key(self) -> None:
        s = OrchestratorSettings.from_env({"ANTHROPIC_API_KEY": "sk-ant-xyz"})
        assert s.anthropic_api_key == "sk-ant-xyz"


class TestFromEnvValidation:
    def test_rejects_unknown_host(self) -> None:
        with pytest.raises(ConfigError, match="MPC_HOST"):
            OrchestratorSettings.from_env({"MPC_HOST": "bitbucket"})

    def test_rejects_empty_host_url(self) -> None:
        with pytest.raises(ConfigError, match="MPC_HOST_URL"):
            OrchestratorSettings.from_env({"MPC_HOST_URL": "   "})

    def test_rejects_unknown_log_level(self) -> None:
        with pytest.raises(ConfigError, match="MPC_LOG_LEVEL"):
            OrchestratorSettings.from_env({"MPC_LOG_LEVEL": "LOUD"})

    def test_rejects_namespace_with_https_prefix(self) -> None:
        with pytest.raises(ConfigError, match="MPC_NAMESPACE"):
            OrchestratorSettings.from_env(
                {"MPC_NAMESPACE": "https://gitlab.com/rmsharp-modelpilot"}
            )

    def test_rejects_namespace_with_http_prefix(self) -> None:
        with pytest.raises(ConfigError, match="MPC_NAMESPACE"):
            OrchestratorSettings.from_env(
                {"MPC_NAMESPACE": "http://gitlab.example.com/team"}
            )


class TestRequireHelpers:
    def test_require_host_token_success(self) -> None:
        s = OrchestratorSettings.from_env(
            {"MPC_HOST": "gitlab", "GITLAB_TOKEN": "t"}
        )
        assert s.require_host_token() == "t"

    def test_require_host_token_raises_when_missing(self) -> None:
        s = OrchestratorSettings.from_env({"MPC_HOST": "github"})
        with pytest.raises(ConfigError, match="GITHUB_TOKEN"):
            s.require_host_token()

    def test_require_anthropic_api_key_success(self) -> None:
        s = OrchestratorSettings.from_env({"ANTHROPIC_API_KEY": "sk"})
        assert s.require_anthropic_api_key() == "sk"

    def test_require_anthropic_api_key_raises(self) -> None:
        s = OrchestratorSettings.from_env({})
        with pytest.raises(ConfigError, match="ANTHROPIC_API_KEY"):
            s.require_anthropic_api_key()


class TestRequireLLMApiKey:
    """The provider-keyed credential resolver (multi-provider plan, Phase A)."""

    def test_default_provider_is_anthropic(self) -> None:
        s = OrchestratorSettings.from_env({"ANTHROPIC_API_KEY": "sk"})
        # No-arg call resolves the default provider's key.
        assert s.require_llm_api_key() == "sk"

    def test_explicit_anthropic_provider(self) -> None:
        s = OrchestratorSettings.from_env({"ANTHROPIC_API_KEY": "sk"})
        assert s.require_llm_api_key("anthropic") == "sk"

    def test_unknown_provider_raises_listing_known(self) -> None:
        s = OrchestratorSettings.from_env({"ANTHROPIC_API_KEY": "sk"})
        with pytest.raises(ConfigError, match="Unknown LLM provider 'openai'"):
            s.require_llm_api_key("openai")

    def test_missing_key_raises_naming_env_var(self) -> None:
        s = OrchestratorSettings.from_env({})
        with pytest.raises(ConfigError, match="ANTHROPIC_API_KEY"):
            s.require_llm_api_key("anthropic")

    def test_bedrock_provider_raises_aws_credential_chain_message(self) -> None:
        """Bedrock authenticates via the boto3 credential chain, not an env-var
        key — the resolver rejects it with a clear, self-documenting message
        rather than inventing a missing-env-var error (plan Phase C)."""
        s = OrchestratorSettings.from_env({})
        with pytest.raises(ConfigError, match="AWS credential chain"):
            s.require_llm_api_key("bedrock")

    def test_llm_api_keys_mapping_is_populated_per_provider(self) -> None:
        s = OrchestratorSettings.from_env({"ANTHROPIC_API_KEY": "sk"})
        # Keyed by provider name; unset providers map to None. Providers with no
        # env-var key (``bedrock`` — boto3 chain) are intentionally absent.
        assert s.llm_api_keys == {"anthropic": "sk"}
        assert "bedrock" not in s.llm_api_keys
        empty = OrchestratorSettings.from_env({})
        assert empty.llm_api_keys == {"anthropic": None}


class TestLLMProvidersRegistry:
    def test_anthropic_env_var_single_sourced(self) -> None:
        assert LLM_PROVIDERS["anthropic"].api_key_env_var == "ANTHROPIC_API_KEY"

    def test_bedrock_uses_aws_credential_chain_no_env_var(self) -> None:
        """Bedrock carries no ``api_key_env_var`` — the SDK self-discovers AWS
        credentials from the boto3 chain (plan Phase C)."""
        assert "bedrock" in LLM_PROVIDERS
        assert LLM_PROVIDERS["bedrock"].api_key_env_var is None

    def test_opencode_has_no_env_var_key(self) -> None:
        """``opencode`` carries no ``api_key_env_var`` — but for a different reason
        than Bedrock's. Its credential depends on whichever vendor the *operator's*
        OpenCode config routes to (75+ are possible) and may live in OpenCode's own
        credential store rather than any environment variable, so there is no
        single name to record. ``require_llm_api_key`` must therefore refuse with a
        pointed message rather than invent one (AD-11 / spec D8)."""
        assert "opencode" in LLM_PROVIDERS
        assert LLM_PROVIDERS["opencode"].api_key_env_var is None

    def test_default_provider_is_registered(self) -> None:
        assert DEFAULT_LLM_PROVIDER in LLM_PROVIDERS


class TestFromEnvReadsOsEnviron:
    def test_defaults_to_os_environ(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("MPC_HOST", "github")
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_from_env")
        s = OrchestratorSettings.from_env()
        assert s.host == "github"
        assert s.host_token == "ghp_from_env"


class TestValidateNamespace:
    @pytest.mark.parametrize(
        "raw",
        [
            "rmsharp-modelpilot",
            "data-science/model-drafts",
            "my-org/team/subteam",
            "my-github-org",
        ],
    )
    def test_accepts_group_paths(self, raw: str) -> None:
        assert validate_namespace(raw) == raw

    @pytest.mark.parametrize(
        "raw",
        [
            "https://gitlab.com/rmsharp-modelpilot",
            "http://gitlab.example.com/team",
            "HTTPS://gitlab.com/team",
            "  https://gitlab.com/team  ",
        ],
    )
    def test_rejects_url_prefixes(self, raw: str) -> None:
        with pytest.raises(ConfigError, match="group path, not a URL"):
            validate_namespace(raw)


class TestParseBool:
    @pytest.mark.parametrize("raw", ["1", "true", "TRUE", "yes", "On"])
    def test_truthy(self, raw: str) -> None:
        assert parse_bool(raw) is True

    @pytest.mark.parametrize("raw", ["0", "false", "FALSE", "no", "Off"])
    def test_falsy(self, raw: str) -> None:
        assert parse_bool(raw) is False

    def test_rejects_garbage(self) -> None:
        with pytest.raises(ConfigError):
            parse_bool("maybe")
