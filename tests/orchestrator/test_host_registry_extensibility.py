"""Adapter dispatch routed through ``REPO_PLATFORMS[host].adapter_factory`` (O3-3).

Phase O3-3 grows :class:`PlatformSpec` with its third field — ``adapter_factory``
— and collapses the two hardcoded ``if host == "gitlab" / else:  # github``
adapter-construction branches (``agents/website/cli.py`` and
``scripts/run_pipeline.py``) into a single ``REPO_PLATFORMS[host].adapter_factory(
host_url=..., private_token=...)`` call. Two correctness wins fall out:

* **The silent ``else: # github`` fall-through dies.** Any host that is not the
  first branch used to be coerced into the ``else`` arm and built the WRONG
  adapter; the registry now decides, and an unknown host raises ``KeyError``
  instead of silently mis-routing.
* **A new host is a registry row + an adapter module, with zero call-site edits.**
  Proven below by a synthetic third host driving the live dispatch end-to-end.

**RED before O3-3:** ``PlatformSpec`` has no ``adapter_factory`` field and the
dispatch hardcodes the two adapters, so every assertion here fails. The tests are
also a durable behaviour pin — re-hardcoding either dispatch branch makes the
monkeypatched sentinel factory go uncalled even once the field exists
(Candidate #85: a behaviour-difference test, not merely a field-presence check).

**Host/CI non-fusion pin (plan §1.3, the load-bearing scope boundary):**
``PlatformSpec`` carries URL + token + adapter and *nothing* about CI. The
CI-platform vocabulary stays a separate controlled vocabulary
(``cli.VALID_CI_PLATFORMS``, the audit's C4/E2) — folding a CI slot into the host
registry would be a category error. Behavioural separability is pinned by
``test_cli_ci_platform_overrides_host`` (``tests/agents/website/test_cli.py``).
"""

from __future__ import annotations

import importlib.util
from dataclasses import fields
from pathlib import Path
from typing import Any

import pytest

from model_project_constructor.agents.website.fake_client import FakeRepoClient
from model_project_constructor.orchestrator import config as cfg
from model_project_constructor.orchestrator.config import (
    REPO_PLATFORMS,
    PlatformSpec,
)

SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "run_pipeline.py"


@pytest.fixture(scope="module")
def run_pipeline_module():  # type: ignore[no-untyped-def]
    """Load ``scripts/run_pipeline.py`` as a module (mirrors the Session-30 test)."""
    spec = importlib.util.spec_from_file_location(
        "_o3_run_pipeline_under_test", SCRIPT_PATH
    )
    assert spec is not None
    assert spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class _CapturingAgent:
    """Stub WebsiteAgent that records the client it was handed."""

    captured: dict[str, Any] = {}

    def __init__(self, client: Any, **_kwargs: Any) -> None:
        type(self).captured = {"client": client}

    def run(self, *_args: Any, **_kwargs: Any) -> None:
        return None


class TestLiveDispatchIsRegistryDriven:
    """``build_website_runner`` obtains its client from the registry factory."""

    def test_existing_host_dispatch_calls_registry_factory(
        self, run_pipeline_module: Any, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Swap the GitHub spec's factory for a sentinel-returning stub. Seeing
        # the sentinel flow all the way to the agent proves the dispatch reads
        # ``REPO_PLATFORMS[host].adapter_factory`` rather than a hardcoded
        # ``PyGithubAdapter(...)``.
        sentinel = FakeRepoClient()
        calls: dict[str, Any] = {}

        def _factory(*, host_url: str, private_token: str) -> FakeRepoClient:
            calls.update(host_url=host_url, private_token=private_token)
            return sentinel

        monkeypatch.setitem(
            cfg.REPO_PLATFORMS,
            "github",
            PlatformSpec(
                default_api_url="https://api.github.com",
                token_env_var="GITHUB_TOKEN",
                adapter_factory=_factory,
            ),
        )
        _CapturingAgent.captured = {}
        monkeypatch.setattr(run_pipeline_module, "WebsiteAgent", _CapturingAgent)
        monkeypatch.setenv("MPC_HOST", "github")
        monkeypatch.setenv("GITHUB_TOKEN", "tok-gh")
        monkeypatch.setenv("MPC_HOST_URL", "https://github.example.com/api/v3")

        _runner, fake_client = run_pipeline_module.build_website_runner(
            host="github", live=True
        )
        assert fake_client is None
        assert _CapturingAgent.captured["client"] is sentinel
        assert calls == {
            "host_url": "https://github.example.com/api/v3",
            "private_token": "tok-gh",
        }

    def test_third_host_drives_adapter_path_with_zero_call_site_edits(
        self, run_pipeline_module: Any, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # A host present ONLY in the registry (bitbucket) routes through its own
        # factory with no edit to build_website_runner. Pre-O3-3 the ``else``
        # branch silently built a GitLab adapter for any non-github host.
        sentinel = FakeRepoClient()
        calls: dict[str, Any] = {}

        def _bitbucket_factory(*, host_url: str, private_token: str) -> FakeRepoClient:
            calls.update(host_url=host_url, private_token=private_token)
            return sentinel

        monkeypatch.setitem(
            cfg.REPO_PLATFORMS,
            "bitbucket",
            PlatformSpec(
                default_api_url="https://bitbucket.example.com",
                token_env_var="BITBUCKET_TOKEN",
                adapter_factory=_bitbucket_factory,
            ),
        )
        _CapturingAgent.captured = {}
        monkeypatch.setattr(run_pipeline_module, "WebsiteAgent", _CapturingAgent)
        monkeypatch.setenv("MPC_HOST", "bitbucket")
        monkeypatch.setenv("BITBUCKET_TOKEN", "bb-tok")
        monkeypatch.delenv("MPC_HOST_URL", raising=False)

        _runner, fake_client = run_pipeline_module.build_website_runner(
            host="bitbucket", live=True
        )
        assert fake_client is None
        assert _CapturingAgent.captured["client"] is sentinel
        assert calls == {
            "host_url": "https://bitbucket.example.com",
            "private_token": "bb-tok",
        }


class TestRegistryFactories:
    """The two ``_make_*`` factories build the right adapter with the right kwargs."""

    def test_registry_factories_are_the_module_make_functions(self) -> None:
        assert REPO_PLATFORMS["gitlab"].adapter_factory is cfg._make_gitlab_adapter
        assert REPO_PLATFORMS["github"].adapter_factory is cfg._make_github_adapter

    def test_gitlab_factory_builds_gitlab_adapter_with_kwargs(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        captured: dict[str, Any] = {}

        class _Fake(FakeRepoClient):
            def __init__(self, **kwargs: Any) -> None:
                captured.update(kwargs)
                super().__init__()

        import model_project_constructor.agents.website.gitlab_adapter as gl

        monkeypatch.setattr(gl, "PythonGitLabAdapter", _Fake)
        client = cfg._make_gitlab_adapter(host_url="https://gl", private_token="t")
        assert isinstance(client, _Fake)
        assert captured == {"host_url": "https://gl", "private_token": "t"}

    def test_github_factory_builds_github_adapter_with_kwargs(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        captured: dict[str, Any] = {}

        class _Fake(FakeRepoClient):
            def __init__(self, **kwargs: Any) -> None:
                captured.update(kwargs)
                super().__init__()

        import model_project_constructor.agents.website.github_adapter as gh

        monkeypatch.setattr(gh, "PyGithubAdapter", _Fake)
        client = cfg._make_github_adapter(host_url="https://gh", private_token="t")
        assert isinstance(client, _Fake)
        assert captured == {"host_url": "https://gh", "private_token": "t"}


class TestRegistryImportStaysSdkFree:
    """Defining the factories must not pull an SDK at registry-import time."""

    def test_importing_config_pulls_no_sdk(self) -> None:
        import subprocess
        import sys

        code = (
            "import sys; "
            "import model_project_constructor.orchestrator.config as c; "
            "bad = [m for m in ('gitlab', 'github') if m in sys.modules]; "
            "assert not bad, bad; "
            "from dataclasses import fields; "
            "assert any(f.name == 'adapter_factory' for f in fields(c.PlatformSpec)); "
            "print('sdk-free-ok')"
        )
        result = subprocess.run(
            [sys.executable, "-c", code], capture_output=True, text=True
        )
        assert result.returncode == 0, result.stderr
        assert "sdk-free-ok" in result.stdout


class TestHostCiNonFusion:
    """The host registry carries no CI concept; CI vocabulary stays separate."""

    def test_platformspec_carries_no_ci_field(self) -> None:
        names = {f.name for f in fields(PlatformSpec)}
        assert names == {"default_api_url", "token_env_var", "adapter_factory"}
        assert not any("ci" in name.lower() for name in names)

    def test_ci_vocabulary_is_a_separate_hand_listed_source(self) -> None:
        # ``ci_platform`` plumbing derives from ``cli.VALID_CI_PLATFORMS`` — a
        # frozenset literal independent of ``REPO_PLATFORMS`` — so the two
        # vocabularies can diverge (--host gitlab --ci-platform github). They
        # share membership today but are NOT one source.
        from model_project_constructor.agents.website import cli

        assert sorted(cli.VALID_CI_PLATFORMS) == ["github", "gitlab"]
        assert sorted(cli.VALID_HOSTS) == sorted(REPO_PLATFORMS)
        assert cli.VALID_CI_PLATFORMS is not cli.VALID_HOSTS
