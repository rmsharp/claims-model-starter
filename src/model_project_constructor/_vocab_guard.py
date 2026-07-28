"""Dependency-free import-time vocabulary drift guard.

A *controlled vocabulary* in this codebase is a hand-written ``Literal`` (which
the type checker can read) paired with a runtime structure that must enumerate
exactly the same members — a ``dict`` registry's keys, a severity table, a
cadence map. mypy cannot derive a ``Literal`` from a runtime value, so the two
are kept in lockstep by an import-time ``raise`` that fails the build the moment
they drift apart.

This module is the shared home for that guard so SDK-free modules (notably
:mod:`model_project_constructor.orchestrator.config`, which must not import
``httpx`` or ``PyGithub``) can pin their vocabularies without importing
the SDK-eager ``agents.website.governance_templates`` where the original
Audit #2 copy lived (that module now imports this shared guard too). The guard
depends only on :mod:`typing`.

A real ``raise`` is used rather than a bare ``assert`` so the check survives
``python -O`` (which strips ``assert`` statements).
"""

from __future__ import annotations

from typing import Any, get_args


def assert_vocab_parity(
    members: set[str],
    literal: Any,
    *,
    name: str,
    reconcile_hint: str,
) -> None:
    """Raise ``AssertionError`` when ``members`` drifts from ``literal``'s members.

    ``members`` is a runtime membership set (e.g. ``set(REPO_PLATFORMS)``);
    ``literal`` is the hand-written ``Literal`` it must match
    (e.g. ``HostLiteral``). ``name`` labels the drifted structure in the error;
    ``reconcile_hint`` is a caller-supplied sentence telling a maintainer where
    to fix the divergence — it is caller-supplied because the two surfaces that
    use this guard live in different modules (the host registry in
    ``orchestrator/config.py``; the governance dicts keyed off
    ``schemas/v1/common.py``), so a single hardcoded hint would be wrong for one
    of them.
    """

    expected = set(get_args(literal))
    if members != expected:
        missing = sorted(expected - members)
        extra = sorted(members - expected)
        raise AssertionError(
            f"{name} has drifted from its Literal: "
            f"missing {missing}, extra {extra}. {reconcile_hint}"
        )


def literal_members(literal: Any) -> tuple[str, ...]:
    """The members of a ``Literal``, in definition order (a thin, typed ``get_args``).

    ``get_args`` returns a ``Literal``'s members in the order they were written,
    which is the same order the prompt prose lists them — so a join of this is
    byte-identical to the hand-written enumeration it replaces.
    """

    return tuple(str(m) for m in get_args(literal))


def join_members(literal: Any, *, sep: str = ", ") -> str:
    """Comma-joined ``Literal`` members for prompt prose, e.g. ``'a, b, c'``.

    Lets an LLM prompt *derive* its enumeration from the canonical ``Literal``
    instead of hand-listing the members, so the producer prose cannot drift from
    the validator (Overhaul O4). ``sep`` overrides the separator for the rare
    prompt that joins differently (e.g. ``low/medium/high``).
    """

    return sep.join(literal_members(literal))


__all__ = ["assert_vocab_parity", "join_members", "literal_members"]
