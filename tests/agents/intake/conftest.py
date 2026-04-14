"""Shared fixtures for intake agent tests."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

FIXTURES_DIR = Path(__file__).resolve().parents[2] / "fixtures"


@pytest.fixture
def subrogation_fixture_path() -> Path:
    return FIXTURES_DIR / "subrogation.yaml"


@pytest.fixture
def pricing_fixture_path() -> Path:
    return FIXTURES_DIR / "pricing_optimization.yaml"


@pytest.fixture
def fraud_fixture_path() -> Path:
    return FIXTURES_DIR / "fraud_triage.yaml"


@pytest.fixture
def question_cap_fixture_path() -> Path:
    return FIXTURES_DIR / "intake_question_cap.yaml"


@pytest.fixture
def revision_cap_fixture_path() -> Path:
    return FIXTURES_DIR / "intake_revision_cap.yaml"


@pytest.fixture
def subrogation_fixture(subrogation_fixture_path: Path) -> dict:
    return yaml.safe_load(subrogation_fixture_path.read_text())
