"""Live stakeholder simulator — a robust answer source for the interview eval.

The deterministic fixture path replays a *fixed* list of recorded answers, one
per recorded question (``IntakeAgent.run_scripted(interview_answers=...)``). That
only works when the questions are fixed: a **live** interviewer generates its own
questions and asks more/different ones than any recorded script supplies, so the
list runs out and the interview is scored as a non-convergence — the
``interview_convergence`` artifact diagnosed in ``PHASE_E_AGREEMENT_REPORT.md``
(``PROJECT_LEARNINGS`` #21).

This module closes that gap. :class:`StakeholderSimulator` is an
:class:`~model_project_constructor.agents.intake.agent.AnswerProvider`: handed the
*actual* question the live model just asked, it answers from the fixture's full
knowledge (its prior Q/A plus the blessed draft, including the value measurement
plan the interviewer must extract to reach ``COMPLETE``). Because it answers on
demand it can never run out, so a sub-convergence now reflects the *model's* own
interview behaviour rather than a starved script.

It is **not** a pytest test; it is the live eval's stakeholder, used by
``test_eval_live.py`` and ``shadow_run.py``. Construction reuses the intake
factory so the simulated stakeholder talks to the *same* provider, credentials,
and model tier as the interview under test (:func:`stakeholder_simulator_for`);
the LLM client is injectable so the assembly is unit-testable without an API key.
"""

from __future__ import annotations

from typing import Any, cast

import yaml

from model_project_constructor.agents.intake.factory import (
    make_llm_client as make_intake_client,
)

#: A short answer (1-4 sentences) never needs the full interview budget.
_DEFAULT_MAX_TOKENS = 1024

_STAKEHOLDER_SYSTEM = (
    "You are role-playing a BUSINESS STAKEHOLDER being interviewed by a data "
    "scientist about a potential modeling project at a property & casualty "
    "insurer's claims organization. You are the interviewee, NOT the "
    "interviewer.\n\n"
    "Rules:\n"
    "- Answer the SPECIFIC question asked, in 1-4 plain-prose sentences. No "
    "JSON; use a short list only if the question explicitly asks for several "
    "items.\n"
    "- Use the facts in your briefing. If the exact detail the interviewer "
    "wants is not spelled out there, give a brief, plausible answer consistent "
    "with the scenario — never refuse and never say you lack the information.\n"
    "- Do NOT volunteer information the interviewer did not ask about; let them "
    "drive the conversation one question at a time.\n"
    "- Stay in character as a cooperative, knowledgeable business stakeholder."
)


def _brief_from_fixture(fixture: dict[str, Any]) -> str:
    """Assemble the stakeholder's knowledge brief from an intake fixture.

    Everything the stakeholder could plausibly know about the project: the
    initial problem they raised, the facts established in prior discussion
    (``qa_pairs``), and the complete blessed ``draft`` — which carries the value
    measurement plan, the section the interviewer must probe to converge.
    """
    parts: list[str] = [
        "BRIEFING — everything you know about your project (answer questions "
        "using these facts):",
    ]
    initial = fixture.get("initial_problem")
    if initial:
        parts.append(f"\nThe problem you raised:\n{str(initial).strip()}")

    qa_pairs = fixture.get("qa_pairs") or []
    if qa_pairs:
        lines = [
            f"- {pair['question']}\n  {pair['answer']}".strip() for pair in qa_pairs
        ]
        parts.append("\nFacts established in earlier discussion:\n" + "\n".join(lines))

    draft = fixture.get("draft") or {}
    if draft:
        dumped = yaml.safe_dump(draft, sort_keys=False, default_flow_style=False)
        parts.append("\nThe complete picture of your project:\n" + dumped.strip())

    return "\n".join(parts)


class StakeholderSimulator:
    """An :class:`AnswerProvider` that answers any interview question via an LLM.

    The brief (the fixture's known facts) is fixed at construction; each call
    answers one question. Injecting ``client`` + ``model`` keeps the prompt
    assembly testable without an API key — :func:`stakeholder_simulator_for`
    wires the real provider client.
    """

    def __init__(
        self,
        *,
        brief: str,
        client: Any,
        model: str,
        max_tokens: int = _DEFAULT_MAX_TOKENS,
    ) -> None:
        self._brief = brief
        self._client = client
        self._model = model
        self._max_tokens = max_tokens

    def __call__(self, *, question: str, question_number: int) -> str:
        user = (
            f"{self._brief}\n\n"
            f"The interviewer asks (question {question_number}):\n{question}\n\n"
            "Answer as the stakeholder."
        )
        return self._call_text(_STAKEHOLDER_SYSTEM, user)

    def _call_text(self, system: str, user: str) -> str:
        """One plain-text turn. A seam failure raises ``RuntimeError`` so the
        eval records it as a non-convergence (mirrors the intake client's
        empty/non-text guards; the §3.4 driver counts the miss rather than
        crashing)."""
        response = self._client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        if not response.content:
            raise RuntimeError("stakeholder simulator: model returned empty content")
        text = getattr(response.content[0], "text", None)
        if not isinstance(text, str):
            raise RuntimeError(
                "stakeholder simulator: expected a text block, got "
                f"{type(response.content[0]).__name__}"
            )
        return text


def stakeholder_simulator_for(
    fixture: dict[str, Any],
    *,
    provider: str,
    model: str | None = None,
    max_tokens: int = _DEFAULT_MAX_TOKENS,
) -> StakeholderSimulator:
    """Build a :class:`StakeholderSimulator` for ``provider`` from a fixture.

    Reuses the intake factory and borrows the constructed client's own SDK
    handle + resolved model, so the simulated stakeholder uses the *same*
    provider, credential chain, and model tier as the interview under test — no
    duplication of the factory's provider switch and no drift. (``_client`` /
    ``_model`` are the concrete client's attributes; this deliberate reach is
    test-tree-only and would fail loudly here if the client were refactored.)
    """
    intake_client = cast(Any, make_intake_client(provider, model=model))
    return StakeholderSimulator(
        brief=_brief_from_fixture(fixture),
        client=intake_client._client,
        model=intake_client._model,
        max_tokens=max_tokens,
    )
