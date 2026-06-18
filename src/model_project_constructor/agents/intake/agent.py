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

from typing import Any, Protocol

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


class AnswerProvider(Protocol):
    """Supplies a stakeholder answer for each interview question the graph asks.

    Two ways to drive the headless interview:

    * a **fixed list** (``interview_answers``) — the deterministic fixture path,
      where the replay LLM asks exactly the recorded questions, so a one-answer-
      per-question list always matches; and
    * an **answer provider** — a callable handed the *actual* question text the
      graph just asked, so it can answer whatever a live model asks (which may
      differ in count, order, and wording from any recorded script). This is the
      robustness path the live eval uses; see ``tests/eval/stakeholder_sim.py``.

    A provider receives the question text and its 1-based number and returns the
    stakeholder's reply. Because it answers on demand, it can never "run out".
    """

    def __call__(self, *, question: str, question_number: int) -> str: ...


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
        review_responses: list[str],
        interview_answers: list[str] | None = None,
        answer_provider: AnswerProvider | None = None,
        domain: str = "pc_claims",
        initial_problem: str | None = None,
    ) -> IntakeReport:
        """Drive the compiled graph headlessly to a terminal report.

        Interview answers come from exactly one of two sources (supply one):

        * ``interview_answers`` — a fixed list consumed in order, one per
          question. If the graph asks for more answers than supplied we raise
          ``RuntimeError`` — the script is under-specified for this fixture.
          Correct when the replay LLM asks a known, fixed set of questions.
        * ``answer_provider`` — an :class:`AnswerProvider` called with each
          question the graph actually asks. It answers on demand, so it can
          never run out; use it to drive a *live* model that generates its own
          questions (see ``tests/eval/stakeholder_sim.py``).

        ``review_responses`` is always a fixed list (one per review interrupt).
        Stops as soon as ``finalize`` completes.
        """
        if interview_answers is None and answer_provider is None:
            raise ValueError(
                "run_scripted needs interview_answers or answer_provider"
            )

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
        answer_iter = iter(interview_answers or [])
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
                if answer_provider is not None:
                    reply: Any = answer_provider(
                        question=str(payload.get("question", "")),
                        question_number=int(payload.get("question_number", 0)),
                    )
                else:
                    try:
                        reply = next(answer_iter)
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
