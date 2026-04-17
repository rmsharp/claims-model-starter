"""Test fixtures for the intake web UI."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from model_project_constructor.agents.intake.fixture import (
    FixtureLLMClient,
    load_fixture,
)
from model_project_constructor.agents.intake.protocol import IntakeLLMClient
from model_project_constructor.ui.intake import create_app

FIXTURE_DIR = Path(__file__).resolve().parents[2] / "fixtures"


@pytest.fixture
def subrogation_fixture() -> dict:
    return load_fixture(str(FIXTURE_DIR / "subrogation.yaml"))


@pytest.fixture
def revision_cap_fixture() -> dict:
    return load_fixture(str(FIXTURE_DIR / "intake_revision_cap.yaml"))


@pytest.fixture
def question_cap_fixture() -> dict:
    return load_fixture(str(FIXTURE_DIR / "intake_question_cap.yaml"))


def _fixture_factory(
    fixture: dict,
) -> Callable[[str], IntakeLLMClient]:
    def factory(_session_id: str) -> IntakeLLMClient:
        return FixtureLLMClient(fixture)

    return factory


@pytest.fixture
def make_app(tmp_path: Path) -> Iterator[Callable[[dict], FastAPI]]:
    """Return a factory that builds an isolated app for a given fixture.

    Each call gets its own SQLite file under the test's ``tmp_path`` so
    test isolation is guaranteed. Every app's ``IntakeSessionStore`` is
    tracked here and closed on teardown: ``TestClient`` doesn't fire
    FastAPI's ``lifespan`` unless it's used as a context manager, so the
    store's SQLite connection would otherwise leak.
    """

    counter = {"n": 0}
    apps: list[FastAPI] = []

    def factory(fixture: dict) -> FastAPI:
        counter["n"] += 1
        db = tmp_path / f"intake_{counter['n']}.db"
        app = create_app(llm_factory=_fixture_factory(fixture), db_path=db)
        apps.append(app)
        return app

    try:
        yield factory
    finally:
        for app in apps:
            app.state.store.close()


@pytest.fixture
def make_client(
    make_app: Callable[[dict], FastAPI],
) -> Callable[[dict], TestClient]:
    def factory(fixture: dict) -> TestClient:
        return TestClient(make_app(fixture))

    return factory


@pytest.fixture
def subrogation_client(
    subrogation_fixture: dict,
    make_client: Callable[[dict], TestClient],
) -> Iterator[TestClient]:
    client = make_client(subrogation_fixture)
    try:
        yield client
    finally:
        client.close()
