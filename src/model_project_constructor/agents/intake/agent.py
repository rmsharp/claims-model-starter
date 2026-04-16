"""Intake Agent facade.

Provides a thin wrapper around the compiled LangGraph that knows how to
*drive* an interview end-to-end from a fixture: it invokes the graph,
handles interrupts by pulling the next scripted answer, and returns a
validated ``IntakeReport``.

The graph itself is generic: Phase 3B can reuse ``build_intake_graph`` and
drive it from a Web UI instead. The facade below is specifically the
headless / fixture driver.
"""

from __future__ import annotations

from typing import Any

from langgraph.types import Command

from model_project_constructor.agents.intake.fixture import (
    FixtureLLMClient,
    answers_from_fixture,
    load_fixture,
    review_sequence_from_fixture,
)
from model_project_constructor.agents.intake.graph import build_intake_graph
from model_project_constructor.agents.intake.nodes import build_intake_report
from model_project_constructor.agents.intake.protocol import IntakeLLMClient
from model_project_constructor.agents.intake.state import (
    MAX_QUESTIONS,
    MAX_REVISIONS,
    initial_state,
)
from model_project_constructor.schemas.v1.intake import IntakeReport


class IntakeAgent:
    """High-level runner for the intake graph.

    ``run_with_fixture`` is the fixture-driven path used by Phase 3A's CLI
    and tests. A future Web UI will instead instantiate the graph directly
    and drive interrupts from HTTP requests.
    """

    def __init__(self, llm: IntakeLLMClient):
        self.llm = llm
        self.graph = build_intake_graph(llm)

    def run_scripted(
        self,
        *,
        stakeholder_id: str,
        session_id: str,
        interview_answers: list[str],
        review_responses: list[str],
        domain: str = "pc_claims",
        initial_problem: str | None = None,
    ) -> IntakeReport:
        """Drive the compiled graph with a pre-scripted answer sequence.

        Stops as soon as ``finalize`` completes. Caller supplies one string
        per interview answer and one string per review interrupt. If the
        graph asks for more answers than supplied we raise — that means the
        script is under-specified for this fixture.
        """

        config = {"configurable": {"thread_id": session_id}}
        state = initial_state(
            stakeholder_id=stakeholder_id,
            session_id=session_id,
            domain=domain,
            initial_problem=initial_problem,
        )

        # Hard budget: at most MAX_QUESTIONS interview interrupts +
        # MAX_REVISIONS+1 review interrupts, plus a safety margin. This is
        # the only thing standing between a buggy graph and an infinite loop
        # during tests.
        max_turns = MAX_QUESTIONS + MAX_REVISIONS + 5
        answer_iter = iter(interview_answers)
        review_iter = iter(review_responses)

        self.graph.invoke(state, config=config)

        for _ in range(max_turns):
            snapshot = self.graph.get_state(config)
            if not snapshot.tasks:
                break

            task = snapshot.tasks[0]
            interrupts = getattr(task, "interrupts", ())
            if not interrupts:
                break

            payload = interrupts[0].value or {}
            kind = payload.get("kind") if isinstance(payload, dict) else None

            if kind == "question":
                try:
                    reply: Any = next(answer_iter)
                except StopIteration as exc:
                    raise RuntimeError(
                        "Fixture ran out of interview answers before the agent "
                        "was satisfied. Increase qa_pairs or lower draft_after."
                    ) from exc
            elif kind == "review":
                try:
                    reply = next(review_iter)
                except StopIteration as exc:
                    raise RuntimeError(
                        "Fixture ran out of review responses."
                    ) from exc
            else:
                raise RuntimeError(f"Unknown interrupt kind: {kind!r}")

            self.graph.invoke(Command(resume=reply), config=config)
        else:
            raise RuntimeError(
                f"Intake graph exceeded max turns ({max_turns}). "
                "Check interview/review cap enforcement."
            )

        final_state = self.graph.get_state(config).values
        status = final_state.get("status", "DRAFT_INCOMPLETE")
        missing = list(final_state.get("missing_fields") or [])
        return build_intake_report(final_state, status=status, missing=missing)

    def run_with_fixture(self, fixture_path: str) -> IntakeReport:
        fixture = load_fixture(fixture_path)
        # The fixture may override the LLM on this call: a fixture-driven
        # run should use the FixtureLLMClient regardless of what was passed
        # to the constructor, because the fixture IS the LLM for this run.
        self.llm = FixtureLLMClient(fixture)
        self.graph = build_intake_graph(self.llm)
        return self.run_scripted(
            stakeholder_id=fixture["stakeholder_id"],
            session_id=fixture["session_id"],
            domain=fixture.get("domain", "pc_claims"),
            initial_problem=fixture.get("initial_problem"),
            interview_answers=answers_from_fixture(fixture),
            review_responses=review_sequence_from_fixture(fixture),
        )
