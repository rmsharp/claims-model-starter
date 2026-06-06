"""Registry-driven URL + token resolution (Overhaul O3, Phase O3-2).

Phase O3-2 folds the host->default-URL and host->token-env mappings into the
single-source ``REPO_PLATFORMS`` registry: ``OrchestratorSettings.from_env``
resolves both from ``REPO_PLATFORMS[host]`` instead of duplicated
``"gitlab" if host == "gitlab" else "github"`` ternaries (the must-agree token
pair formerly at ``config.py:148`` (read) and ``:185`` (error) and the URL
branch at ``:143``).

The decisive pin is a synthetic THIRD host present only in the registry: before
O3-2 the narrowing ternary coerced any non-gitlab host to ``"github"`` and the
URL/token branches handed it GitHub's values, silently mis-resolving it. After
O3-2 the lookups are registry-driven, so a registry-only host resolves its OWN
URL + token with zero edits to ``from_env`` — the config-resolution analogue of
the O3-3 adapter extensibility pin. Candidate #77: the registry is the parseable
producer these behavioural pins consume (parametrized over ``REPO_PLATFORMS``).
"""

from __future__ import annotations

import pytest

from model_project_constructor.agents.website.fake_client import FakeRepoClient
from model_project_constructor.orchestrator import config as cfg
from model_project_constructor.orchestrator.config import (
    DEFAULT_GITHUB_URL,
    DEFAULT_GITLAB_URL,
    REPO_PLATFORMS,
    OrchestratorSettings,
)


def _stub_factory(**_kwargs: object) -> FakeRepoClient:
    """No-op adapter factory for synthetic specs (O3-3 made the field required;
    these tests exercise only URL/token resolution, never build an adapter)."""
    return FakeRepoClient()


class TestUrlAndTokenAreRegistryDriven:
    def test_default_url_constants_alias_the_registry(self) -> None:
        # The back-compat constants (imported by name in test_config.py) are
        # aliases over the registry, so a URL appears once — inside the literal.
        assert REPO_PLATFORMS["gitlab"].default_api_url == DEFAULT_GITLAB_URL
        assert REPO_PLATFORMS["github"].default_api_url == DEFAULT_GITHUB_URL

    @pytest.mark.parametrize("host", sorted(REPO_PLATFORMS))
    def test_each_host_resolves_its_registry_url(self, host: str) -> None:
        s = OrchestratorSettings.from_env({"MPC_HOST": host})
        assert s.host_url == REPO_PLATFORMS[host].default_api_url

    @pytest.mark.parametrize("host", sorted(REPO_PLATFORMS))
    def test_each_host_reads_its_registry_token_var(self, host: str) -> None:
        token_var = REPO_PLATFORMS[host].token_env_var
        s = OrchestratorSettings.from_env({"MPC_HOST": host, token_var: "tok-123"})
        assert s.host_token == "tok-123"

    @pytest.mark.parametrize("host", sorted(REPO_PLATFORMS))
    def test_require_host_token_error_names_the_registry_var(self, host: str) -> None:
        # The "missing token" error names the SAME var ``from_env`` reads: the
        # two ex-ternaries (read at :148, error at :185) now share one source,
        # so they cannot silently diverge.
        token_var = REPO_PLATFORMS[host].token_env_var
        s = OrchestratorSettings.from_env({"MPC_HOST": host})
        with pytest.raises(cfg.ConfigError, match=token_var):
            s.require_host_token()


class TestRegistryOnlyHostResolves:
    """A host present only in ``REPO_PLATFORMS`` resolves its own URL + token
    with no edit to ``from_env`` — RED before O3-2 (the host==gitlab/else-github
    branches mis-mapped any third host to GitHub's URL + token)."""

    def test_third_registry_host_resolves_own_url_and_token(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        spec = cfg.PlatformSpec(
            default_api_url="https://bitbucket.example.com",
            token_env_var="BITBUCKET_TOKEN",
            adapter_factory=_stub_factory,
        )
        monkeypatch.setitem(cfg.REPO_PLATFORMS, "bitbucket", spec)

        s = OrchestratorSettings.from_env(
            {"MPC_HOST": "bitbucket", "BITBUCKET_TOKEN": "bb-tok"}
        )
        assert s.host_url == "https://bitbucket.example.com"
        assert s.host_token == "bb-tok"
