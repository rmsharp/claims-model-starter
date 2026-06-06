"""Tests for the host-vocabulary registry drift guard (Audit #8 / Overhaul O3, Phase O3-1).

The ``REPO_PLATFORMS`` registry in :mod:`model_project_constructor.orchestrator.config`
is the single source of host membership. ``HostLiteral`` (a hand-written
``Literal`` that mypy can read) is pinned to ``REPO_PLATFORMS.keys()`` by an
import-time ``assert_vocab_parity`` ``raise`` guard — the same mechanism Audit #2
applied to the governance vocabulary (``TestVocabularyDriftGuards``). A
runtime-derived ``Literal`` is invisible to the type checker, so the guard — not
derivation — keeps the two in lockstep, failing the build loudly on drift.

These tests pin the live parity AND prove the guard raises on drift (so the
parity pin is not vacuous behind the import-time assert), confirm the host
remediation hint is registry-specific rather than the governance copy's
schema-specific text (§6.2), and pin the §6.4 SDK-free invariant (importing the
registry pulls neither repo SDK).
"""

from __future__ import annotations

import subprocess
import sys
from typing import get_args

import pytest

from model_project_constructor._vocab_guard import assert_vocab_parity
from model_project_constructor.orchestrator.config import (
    REPO_PLATFORMS,
    HostLiteral,
    PlatformSpec,
)

_HOST_HINT = (
    "Reconcile the REPO_PLATFORMS keys with HostLiteral in orchestrator/config.py."
)


class TestHostRegistryDriftGuard:
    def test_repo_platforms_matches_host_literal(self) -> None:
        # Live parity: the registry keys ARE the host Literal members.
        assert set(REPO_PLATFORMS) == set(get_args(HostLiteral))

    def test_registry_entries_are_platform_specs(self) -> None:
        # Phase O3-1 carries the two DATA fields (default API URL + token env
        # var); the adapter_factory field arrives in O3-3.
        for spec in REPO_PLATFORMS.values():
            assert isinstance(spec, PlatformSpec)
            assert spec.default_api_url.startswith("https://")
            assert spec.token_env_var.endswith("_TOKEN")

    def test_guard_raises_on_missing_member(self) -> None:
        # Fed a member set MISSING a Literal value, the guard must raise —
        # proving drift is caught, not silently tolerated (non-vacuous).
        with pytest.raises(AssertionError, match="drifted"):
            assert_vocab_parity(
                {"gitlab"}, HostLiteral, name="_TEST", reconcile_hint=_HOST_HINT
            )

    def test_guard_raises_on_extra_member(self) -> None:
        drifted = set(get_args(HostLiteral)) | {"bitbucket"}
        with pytest.raises(AssertionError, match="drifted"):
            assert_vocab_parity(
                drifted, HostLiteral, name="_TEST", reconcile_hint=_HOST_HINT
            )

    def test_guard_passes_on_exact_match(self) -> None:
        # Exact parity returns None (no raise).
        assert (
            assert_vocab_parity(
                set(get_args(HostLiteral)),
                HostLiteral,
                name="_TEST",
                reconcile_hint=_HOST_HINT,
            )
            is None
        )

    def test_host_failure_hint_is_registry_specific_not_schema(self) -> None:
        # §6.2: the host guard's remediation hint must point at the registry /
        # config module, NOT the governance copy's hardcoded
        # ``schemas/v1/common.py`` (the host vocabulary is not schema-backed).
        with pytest.raises(AssertionError) as exc:
            assert_vocab_parity(
                {"gitlab"},
                HostLiteral,
                name="REPO_PLATFORMS",
                reconcile_hint=_HOST_HINT,
            )
        msg = str(exc.value)
        assert "schemas/v1/common.py" not in msg
        assert "REPO_PLATFORMS" in msg and "config.py" in msg


def test_importing_registry_is_sdk_free() -> None:
    # §6.4 load-bearing invariant: importing the registry/config pulls neither
    # python-gitlab (``gitlab``) nor PyGithub (``github``). Checked in a FRESH
    # subprocess because ``sys.modules`` is process-global — another test in
    # this run may already have imported an SDK, which would mask a regression.
    code = (
        "import sys; "
        "import model_project_constructor.orchestrator.config as c; "
        "leaked = sorted(m for m in ('gitlab', 'github') if m in sys.modules); "
        "assert not leaked, f'registry import pulled an SDK: {leaked}'; "
        "from typing import get_args; "
        "assert set(get_args(c.HostLiteral)) == set(c.REPO_PLATFORMS)"
    )
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr
