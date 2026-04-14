"""Fixture-driven intake agent.

A fixture is a YAML file describing a full interview: the canned
(question, answer) pairs, the canned draft + governance classification the
fake LLM should return, and the canned review response(s) the fake
stakeholder should reply with. This lets us exercise the real LangGraph
interrupt machinery without an API key and without a human in the loop.

Fixture schema (``intake_fixture/v1``)::

    schema: intake_fixture/v1
    stakeholder_id: ...
    session_id: ...
    domain: pc_claims            # optional
    initial_problem: "..."       # optional

    qa_pairs:                    # up to MAX_QUESTIONS entries
      - question: "..."
        answer: "..."
      ...
    draft_after:                 # optional; default = len(qa_pairs)
      5                          # after this many questions, flip enough_info

    draft:                       # canned DraftReportResult
      business_problem: "..."
      proposed_solution: "..."
      model_solution: {...}
      estimated_value: {...}

    governance:                  # canned GovernanceClassification
      cycle_time: tactical
      cycle_time_rationale: "..."
      risk_tier: tier_3_moderate
      risk_tier_rationale: "..."
      regulatory_frameworks: [...]
      affects_consumers: true
      uses_protected_attributes: false

    review_sequence:             # answers to each review interrupt in order.
      - "ACCEPT"                 # use "ACCEPT" for happy path, or free-form
                                 # feedback to exercise revision cycles.

    revised_draft:               # optional; fake revise_report returns this
      ...                        # if absent, revise returns the original draft.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from model_project_constructor.agents.intake.protocol import (
    DraftReportResult,
    GovernanceClassification,
    InterviewContext,
    IntakeLLMError,
    NextQuestionResult,
)

FIXTURE_SCHEMA = "intake_fixture/v1"


def load_fixture(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Fixture not found: {p}")
    data = yaml.safe_load(p.read_text())
    if not isinstance(data, dict):
        raise IntakeLLMError(f"Fixture {p} is not a YAML mapping")
    schema = data.get("schema")
    if schema != FIXTURE_SCHEMA:
        raise IntakeLLMError(
            f"Fixture {p} has schema={schema!r}, expected {FIXTURE_SCHEMA!r}"
        )
    for required in ("stakeholder_id", "session_id", "qa_pairs", "draft", "governance"):
        if required not in data:
            raise IntakeLLMError(f"Fixture {p} missing required field: {required}")
    return data


class FixtureLLMClient:
    """Deterministic ``IntakeLLMClient`` that replays a fixture.

    * ``next_question`` dispenses the pre-recorded questions in order; flips
      ``believe_enough_info`` once ``draft_after`` questions have been asked
      (default: the length of ``qa_pairs``).
    * ``draft_report`` returns the canned draft.
    * ``classify_governance`` returns the canned governance block.
    * ``revise_report`` returns ``revised_draft`` if present, otherwise the
      original draft — enough to exercise revision-cycle counting in tests.
    """

    def __init__(self, fixture: dict[str, Any]):
        self._fixture = fixture
        self._qa_pairs = list(fixture["qa_pairs"])
        self._draft_after = int(fixture.get("draft_after") or len(self._qa_pairs))
        self._draft = fixture["draft"]
        self._governance = fixture["governance"]
        self._revised = fixture.get("revised_draft")
        self._q_index = 0

    def next_question(self, context: InterviewContext) -> NextQuestionResult:
        i = self._q_index
        if i >= len(self._qa_pairs):
            # Fixture exhausted — tell the agent we're done.
            return NextQuestionResult(question="(no more questions)", believe_enough_info=True)
        pair = self._qa_pairs[i]
        self._q_index += 1
        enough = self._q_index >= self._draft_after
        return NextQuestionResult(question=pair["question"], believe_enough_info=enough)

    def draft_report(self, context: InterviewContext) -> DraftReportResult:
        return _build_draft(self._draft)

    def classify_governance(self, draft: DraftReportResult) -> GovernanceClassification:
        return _build_governance(self._governance)

    def revise_report(
        self, draft: DraftReportResult, feedback: str
    ) -> DraftReportResult:
        if self._revised:
            return _build_draft(self._revised)
        return draft


def answers_from_fixture(fixture: dict[str, Any]) -> list[str]:
    return [pair["answer"] for pair in fixture["qa_pairs"]]


def review_sequence_from_fixture(fixture: dict[str, Any]) -> list[str]:
    seq = fixture.get("review_sequence")
    if seq is None:
        return ["ACCEPT"]
    if not isinstance(seq, list) or not seq:
        raise IntakeLLMError("review_sequence must be a non-empty list")
    return [str(s) for s in seq]


def _build_draft(d: dict[str, Any]) -> DraftReportResult:
    try:
        return DraftReportResult(
            business_problem=d["business_problem"],
            proposed_solution=d["proposed_solution"],
            model_solution=dict(d["model_solution"]),
            estimated_value=dict(d["estimated_value"]),
            missing_fields=list(d.get("missing_fields") or []),
        )
    except KeyError as exc:
        raise IntakeLLMError(f"Fixture draft missing field: {exc}") from exc


def _build_governance(d: dict[str, Any]) -> GovernanceClassification:
    try:
        return GovernanceClassification(
            cycle_time=d["cycle_time"],
            cycle_time_rationale=d["cycle_time_rationale"],
            risk_tier=d["risk_tier"],
            risk_tier_rationale=d["risk_tier_rationale"],
            regulatory_frameworks=list(d.get("regulatory_frameworks") or []),
            affects_consumers=bool(d["affects_consumers"]),
            uses_protected_attributes=bool(d["uses_protected_attributes"]),
        )
    except KeyError as exc:
        raise IntakeLLMError(f"Fixture governance missing field: {exc}") from exc
