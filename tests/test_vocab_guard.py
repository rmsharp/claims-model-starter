"""Unit tests for the vocabulary-derivation helpers in :mod:`_vocab_guard`.

``literal_members`` / ``join_members`` let a prompt DERIVE its enumeration from
the canonical ``Literal`` (Overhaul O4 producer single-sourcing) instead of
hand-listing the members. These tests pin the contract the intake prompts rely
on: definition-order members and a byte-stable join.
"""

from __future__ import annotations

from typing import Literal

from model_project_constructor._vocab_guard import join_members, literal_members
from model_project_constructor.schemas.v1.common import ModelType

_SAMPLE = Literal["alpha", "beta", "gamma"]


def test_literal_members_returns_definition_order_tuple() -> None:
    assert literal_members(_SAMPLE) == ("alpha", "beta", "gamma")


def test_literal_members_single_member() -> None:
    assert literal_members(Literal["solo"]) == ("solo",)


def test_literal_members_preserves_real_literal_order() -> None:
    # The derived prose is byte-identical to the old hand-written list only
    # because get_args yields members in definition order. Pin that for a real
    # vocabulary so a reorder of ModelType cannot silently shuffle the prompt.
    assert literal_members(ModelType) == (
        "supervised_classification",
        "supervised_regression",
        "unsupervised_clustering",
        "unsupervised_anomaly",
        "time_series",
        "reinforcement",
        "other",
    )


def test_join_members_default_separator() -> None:
    assert join_members(_SAMPLE) == "alpha, beta, gamma"


def test_join_members_custom_separator() -> None:
    # The intake `confidence` enumeration renders as low/medium/high.
    assert join_members(_SAMPLE, sep="/") == "alpha/beta/gamma"


def test_join_members_single_member_has_no_separator() -> None:
    assert join_members(Literal["solo"], sep="/") == "solo"
