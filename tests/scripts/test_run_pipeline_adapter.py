"""Tests for the DRAFT_INCOMPLETE adapter in scripts/run_pipeline.py.

The adapter lives inline in the script per scope-b-plan §8.4 (a) to avoid
premature abstraction. Loading via importlib keeps the test close to the
production code without promoting the helper to a package module.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

SCRIPT_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "run_pipeline.py"
)


@pytest.fixture(scope="module")
def run_pipeline_module():
    spec = importlib.util.spec_from_file_location(
        "_b2_run_pipeline_under_test", SCRIPT_PATH
    )
    assert spec is not None
    assert spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_draft_incomplete_from_runtime_error_is_valid_report(run_pipeline_module):
    exc = RuntimeError(
        "Fixture ran out of interview answers before the agent was satisfied."
    )
    report = run_pipeline_module._draft_incomplete_from_exception(
        exc=exc,
        stakeholder_id="test_sh",
        session_id="test_session",
    )
    assert report.status == "DRAFT_INCOMPLETE"
    assert report.stakeholder_id == "test_sh"
    assert report.session_id == "test_session"
    assert len(report.missing_fields) == 1
    assert "RuntimeError" in report.missing_fields[0]
    assert "interview_aborted" in report.missing_fields[0]
    assert report.model_solution.target_variable is None
    assert report.estimated_value.confidence == "low"


def test_draft_incomplete_from_arbitrary_exception(run_pipeline_module):
    class _FakeRateLimit(Exception):
        pass

    exc = _FakeRateLimit("429 too many requests")
    report = run_pipeline_module._draft_incomplete_from_exception(
        exc=exc,
        stakeholder_id="sh",
        session_id="s",
    )
    assert report.status == "DRAFT_INCOMPLETE"
    assert "_FakeRateLimit" in report.missing_fields[0]
    assert "429 too many requests" in report.missing_fields[0]


def test_build_intake_runner_catches_runtime_error(run_pipeline_module, monkeypatch):
    """build_intake_runner's closure must convert RuntimeError into a
    DRAFT_INCOMPLETE report, not propagate it. We inject a fake IntakeAgent
    whose run_scripted raises.
    """

    class _RaisingAgent:
        def __init__(self, **_kwargs):
            pass

        def run_scripted(self, **_kwargs):
            raise RuntimeError("Fixture ran out of interview answers.")

    class _StubLLM:
        def __init__(self, **_kwargs):
            pass

    import model_project_constructor.agents.intake.agent as agent_mod
    import model_project_constructor.agents.intake.anthropic_client as ac_mod

    monkeypatch.setattr(agent_mod, "IntakeAgent", _RaisingAgent)
    monkeypatch.setattr(ac_mod, "AnthropicLLMClient", _StubLLM)

    fixture_path = (
        Path(__file__).resolve().parents[1]
        / "fixtures"
        / "_b2_failmode.yaml"
    )
    runner = run_pipeline_module.build_intake_runner(
        llm_mode="both",
        fixture_path=str(fixture_path),
        model="claude-opus-4-7",
    )
    report = runner()
    assert report.status == "DRAFT_INCOMPLETE"
    assert report.stakeholder_id == "b2_failmode_sh"
    assert report.session_id == "b2_failmode_session"
    assert "RuntimeError" in report.missing_fields[0]


def test_build_intake_runner_none_mode_uses_fixture(run_pipeline_module):
    runner = run_pipeline_module.build_intake_runner(
        llm_mode="none",
        fixture_path=None,
        model="claude-opus-4-7",
    )
    report = runner()
    assert report.status == "COMPLETE"
    assert report.stakeholder_id  # non-empty; from subrogation_intake.json


def test_build_intake_runner_both_requires_fixture(run_pipeline_module):
    with pytest.raises(SystemExit):
        run_pipeline_module.build_intake_runner(
            llm_mode="both",
            fixture_path=None,
            model="claude-opus-4-7",
        )


# ---------------------------------------------------------------------------
# build_website_runner — live-mode adapter construction (Session 30)
#
# The GitHub live path at scripts/run_pipeline.py:273-278 had been broken since
# Phase C shipped: (a) it passed ``token=`` but PyGithubAdapter's keyword is
# ``private_token=`` (parallels Session 22's ``url=`` → ``host_url=`` GitLab
# fix), and (b) it never read MPC_HOST_URL so GHE users silently hit public
# api.github.com even with the env var set. These tests pin the kwargs the
# adapter must receive. Live HTTP is never made — the adapter class is
# monkeypatched to a capturing stub.
# ---------------------------------------------------------------------------


def _install_fake_adapters_and_agent(monkeypatch, run_pipeline_module):
    """Replace both adapter classes + WebsiteAgent with capturing stubs.

    Returns the dict that will accumulate kwargs, one key per adapter class.
    """
    captured: dict[str, dict] = {"github": {}, "gitlab": {}}

    class _FakeGithubAdapter:
        def __init__(self, **kwargs):
            captured["github"] = dict(kwargs)

    class _FakeGitlabAdapter:
        def __init__(self, **kwargs):
            captured["gitlab"] = dict(kwargs)

    class _FakeWebsiteAgent:
        def __init__(self, *_args, **_kwargs):
            pass

        def run(self, *_args, **_kwargs):
            return None

    import model_project_constructor.agents.website.github_adapter as gh_mod
    import model_project_constructor.agents.website.gitlab_adapter as gl_mod

    monkeypatch.setattr(gh_mod, "PyGithubAdapter", _FakeGithubAdapter)
    monkeypatch.setattr(gl_mod, "PythonGitLabAdapter", _FakeGitlabAdapter)
    monkeypatch.setattr(run_pipeline_module, "WebsiteAgent", _FakeWebsiteAgent)
    return captured


def test_build_website_runner_github_live_threads_host_url(
    run_pipeline_module, monkeypatch
):
    captured = _install_fake_adapters_and_agent(monkeypatch, run_pipeline_module)

    monkeypatch.setenv("MPC_HOST", "github")
    monkeypatch.setenv("GITHUB_TOKEN", "fake-gh-token")
    monkeypatch.setenv("MPC_HOST_URL", "https://github.mycompany.com/api/v3")

    _runner, fake_client = run_pipeline_module.build_website_runner(
        host="github", live=True
    )
    assert fake_client is None
    assert captured["github"] == {
        "private_token": "fake-gh-token",
        "host_url": "https://github.mycompany.com/api/v3",
    }


def test_build_website_runner_github_live_defaults_host_url(
    run_pipeline_module, monkeypatch
):
    captured = _install_fake_adapters_and_agent(monkeypatch, run_pipeline_module)

    monkeypatch.setenv("MPC_HOST", "github")
    monkeypatch.setenv("GITHUB_TOKEN", "fake-gh-token")
    monkeypatch.delenv("MPC_HOST_URL", raising=False)

    _runner, fake_client = run_pipeline_module.build_website_runner(
        host="github", live=True
    )
    assert fake_client is None
    assert captured["github"] == {
        "private_token": "fake-gh-token",
        "host_url": "https://api.github.com",
    }


def test_build_website_runner_gitlab_live_threads_host_url(
    run_pipeline_module, monkeypatch
):
    """Regression guard for the sibling GitLab branch — kwargs should stay
    stable after the GitHub fix. Mirrors the GitHub test so any future edit
    to the live-adapter block surfaces as a contract change on both paths.
    """
    captured = _install_fake_adapters_and_agent(monkeypatch, run_pipeline_module)

    monkeypatch.setenv("MPC_HOST", "gitlab")
    monkeypatch.setenv("GITLAB_TOKEN", "fake-gl-token")
    monkeypatch.setenv("MPC_HOST_URL", "https://gitlab.internal.company.com")

    _runner, fake_client = run_pipeline_module.build_website_runner(
        host="gitlab", live=True
    )
    assert fake_client is None
    assert captured["gitlab"] == {
        "private_token": "fake-gl-token",
        "host_url": "https://gitlab.internal.company.com",
    }
