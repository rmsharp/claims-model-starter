"""Fixtures + collection hook for the eval tier (Phase B corpus / Phase E shadow run).

The ``pytest_collection_modifyitems`` hook auto-skips a ``live``-marked test when
the **provider it targets** has no credentials. The live tier is parametrized
over :data:`SHADOW_PROVIDERS` (``test_eval_live.py``); each item's provider comes
from its ``provider`` parameter (defaulting to :data:`BASELINE_PROVIDER` for an
unparametrized live test), and ``eval_cutover.provider_creds_available`` decides
whether that provider is runnable (``anthropic`` → ``ANTHROPIC_API_KEY``;
``bedrock`` → the AWS credential chain; ``opencode`` → the binary on ``PATH``
**and** ``OPENCODE_EVAL_MODEL`` naming the model to pin).

CI runs ``uv run pytest -q`` with **no** credentials
(``.github/workflows/ci.yml``), so every provider's cases skip and the tier stays
out of CI via this hook — not a ``-m 'not live'`` flag. A Bedrock-only
environment runs only the Bedrock half; ``-m 'not live'`` is the explicit way to
deselect the whole tier anywhere. The skip is keyed on the ``live`` marker only,
so non-eval tests are never affected.

The ``opencode`` probe deliberately takes **two** signals. A developer machine
that ran the adapter's Phase 1 spike has the binary installed globally, so a
binary-only probe would make a bare ``uv run pytest -q`` *there* start billing
for the live tier while CI — which has no binary — still looked hermetic. The
model variable is the deliberate opt-in, and it is also what an ``opencode`` run
needs to be reproducible at all (that provider pins no default model). See
``eval_cutover.provider_creds_available``.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from model_project_constructor_data_agent.db import ReadOnlyDB

from tests.eval.eval_corpus import (
    GovernanceCase,
    SqlCase,
    load_governance_cases,
    load_sql_cases,
    seed_pc_schema,
)
from tests.eval.eval_cutover import BASELINE_PROVIDER, provider_creds_available


def _live_item_provider(item: pytest.Item) -> str:
    """The provider a live item targets: its ``provider`` param, else baseline."""
    callspec = getattr(item, "callspec", None)
    if callspec is not None:
        provider = callspec.params.get("provider")
        if isinstance(provider, str):
            return provider
    return BASELINE_PROVIDER


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    for item in items:
        if "live" not in item.keywords:
            continue
        provider = _live_item_provider(item)
        if not provider_creds_available(provider):
            item.add_marker(
                pytest.mark.skip(
                    reason=(
                        f"live eval tier: no credentials for provider '{provider}' "
                        "(deselect the whole tier with -m 'not live')"
                    )
                )
            )


@pytest.fixture
def seeded_pc_db(tmp_path: Path) -> Iterator[ReadOnlyDB]:
    """A connected, read-only ``ReadOnlyDB`` over the seeded P&C eval schema."""
    url = f"sqlite:///{tmp_path / 'pc_eval.db'}"
    seed_pc_schema(url)
    db = ReadOnlyDB(url)
    db.connect()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def governance_cases() -> list[GovernanceCase]:
    return load_governance_cases()


@pytest.fixture
def sql_cases() -> list[SqlCase]:
    return load_sql_cases()
