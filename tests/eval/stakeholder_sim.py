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
the completion seam is injectable so the assembly is unit-testable without an
API key.

**Two transport shapes, one seam (Session 215).** This module originally reached
straight through to ``intake_client._client.messages.create`` — an assumption
that *every* provider is backed by an Anthropic-SDK handle. That became false
when ``opencode`` shipped: it is a **subprocess** transport, and its
``_UNUSED_SDK_CLIENT`` placeholder raises ``AttributeError`` on any attribute
access, by design (adapter spec D5). The reach therefore failed exactly as its
own docstring promised it would — loudly — but it failed *mid-run*, aborting the
whole shadow run rather than being retried, because a bare ``AttributeError`` is
not in ``interview_sweep._TRANSIENT_ERRORS``. :data:`TextCompleter` is the fix:
a provider-agnostic ``(system, user) -> answer text`` callable that
:func:`_text_completer_for` resolves per transport — the client's own ``_run``
for subprocess providers, the Messages API for SDK providers. Adding a provider
whose client has neither shape is a loud failure at *construction*, before any
billable call.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, cast

import yaml

from model_project_constructor.agents.intake.factory import (
    make_llm_client as make_intake_client,
)

#: A short answer (1-4 sentences) never needs the full interview budget.
_DEFAULT_MAX_TOKENS = 1024

#: One plain-text turn: ``(system, user) -> assistant text``. The seam every
#: provider must satisfy for the interview sweep to be able to drive it, whatever
#: its transport. Deliberately the same shape as ``OpenCodeLLMClient._run``, so a
#: subprocess client *is* a completer with no wrapper.
TextCompleter = Callable[[str, str], str]


class StakeholderSimError(RuntimeError):
    """A seam failure in the stakeholder simulator's own LLM call.

    Raised when the simulator's model returns empty/non-text content for an
    answer. It subclasses ``RuntimeError`` (so any existing ``except
    RuntimeError`` still catches it), but the *type* lets the interview sweep
    classify it as a **transient** API/seam artifact — retried then excluded —
    rather than counting it as the interviewed model failing to converge (gap
    #1c; see ``interview_sweep``).
    """

def _sdk_completer(client: Any, *, model: str, max_tokens: int) -> TextCompleter:
    """A :data:`TextCompleter` over an Anthropic-SDK-shaped ``messages.create``.

    Covers the ``anthropic`` and ``bedrock`` providers (the latter is the former
    pointed at AWS). The empty/non-text guards live here because they inspect an
    SDK **response object**; the shared string guard in
    :meth:`StakeholderSimulator._call_text` applies to every transport.
    """

    def _complete(system: str, user: str) -> str:
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        if not response.content:
            raise StakeholderSimError("stakeholder simulator: model returned empty content")
        text = getattr(response.content[0], "text", None)
        if not isinstance(text, str):
            raise StakeholderSimError(
                "stakeholder simulator: expected a text block, got "
                f"{type(response.content[0]).__name__}"
            )
        return text

    return _complete


def _text_completer_for(intake_client: Any, *, max_tokens: int) -> TextCompleter:
    """Resolve the plain-text completion seam for a constructed intake client.

    Two transport shapes exist today and the discriminator is the client's own
    transport method, not its provider name — so a future provider is classified
    by what it *is* rather than by a name this module would have to be taught:

    * **Subprocess** (``opencode``): ``_run(system, user) -> str`` already *is* a
      :data:`TextCompleter`. Returned directly — no SDK handle is touched, which
      is the whole point (its ``_client`` is a placeholder that raises).
    * **SDK** (``anthropic``, ``bedrock``): wrap ``_client.messages.create``,
      borrowing the client's own resolved ``_model`` so the simulated stakeholder
      runs on the same model tier as the interview under test.

    Reaching for ``_run``/``_client``/``_model`` is the same deliberate,
    test-tree-only reach this module has always made. A client with neither shape
    raises **here, at construction** — before the sweep spends a cent — rather
    than mid-run on the first stakeholder turn.

    That failure is deliberately a :class:`TypeError`, **not** a
    :class:`StakeholderSimError`: an unsupported client shape is a defect in this
    module, not a transient API blip. ``StakeholderSimError`` is in
    ``interview_sweep._TRANSIENT_ERRORS``, so raising it here would get every
    interview retried three times and then *excluded* — turning a
    "nobody taught the harness this provider" bug into a silently empty result
    set. ``TypeError`` propagates and aborts, which is the honest outcome.
    """
    run = getattr(intake_client, "_run", None)
    if callable(run):
        return cast(TextCompleter, run)
    sdk_client = getattr(intake_client, "_client", None)
    if sdk_client is None:
        raise TypeError(
            "stakeholder simulator: cannot drive "
            f"{type(intake_client).__name__} — it exposes neither a subprocess "
            "transport (_run) nor an SDK handle (_client). Teach "
            "_text_completer_for its transport shape."
        )
    return _sdk_completer(
        sdk_client, model=getattr(intake_client, "_model", ""), max_tokens=max_tokens
    )


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
    answers one question. Injecting the completion seam keeps the prompt assembly
    testable without an API key — :func:`stakeholder_simulator_for` wires the real
    provider's.

    Supply **either** ``completer`` (any transport) **or** ``client`` + ``model``
    (an Anthropic-SDK-shaped handle, wrapped for you). The latter is the original
    signature, kept because it is the convenient shape for a fake in a test.
    """

    def __init__(
        self,
        *,
        brief: str,
        client: Any = None,
        model: str = "",
        max_tokens: int = _DEFAULT_MAX_TOKENS,
        completer: TextCompleter | None = None,
    ) -> None:
        if completer is None:
            if client is None:
                raise TypeError(
                    "stakeholder simulator: pass either completer= or client= + model="
                )
            completer = _sdk_completer(client, model=model, max_tokens=max_tokens)
        self._brief = brief
        self._completer = completer
        self._max_tokens = max_tokens

    def __call__(self, *, question: str, question_number: int) -> str:
        user = (
            f"{self._brief}\n\n"
            f"The interviewer asks (question {question_number}):\n{question}\n\n"
            "Answer as the stakeholder."
        )
        return self._call_text(_STAKEHOLDER_SYSTEM, user)

    def _call_text(self, system: str, user: str) -> str:
        """One plain-text turn. A seam failure raises :class:`StakeholderSimError`
        (mirrors the intake client's empty/non-text guards). The §3.4 interview
        sweep treats that typed error as a *transient* artifact of the
        simulator's own call — retried then excluded — not as the interviewed
        model failing to converge (gap #1c; see ``interview_sweep``).

        The transport-specific guards live in the completer; the guard here is
        the one every transport owes the sweep — a usable answer string. A
        subprocess client signals its own failures as ``IntakeLLMError``, which
        the sweep already classifies as transient, so both paths degrade the
        same way."""
        text = self._completer(system, user)
        if not isinstance(text, str):
            raise StakeholderSimError(
                f"stakeholder simulator: expected answer text, got {type(text).__name__}"
            )
        if not text.strip():
            raise StakeholderSimError("stakeholder simulator: model returned empty content")
        return text


def stakeholder_simulator_for(
    fixture: dict[str, Any],
    *,
    provider: str,
    model: str | None = None,
    max_tokens: int = _DEFAULT_MAX_TOKENS,
) -> StakeholderSimulator:
    """Build a :class:`StakeholderSimulator` for ``provider`` from a fixture.

    Reuses the intake factory and borrows the constructed client's own transport,
    so the simulated stakeholder uses the *same* provider, credential chain, and
    model tier as the interview under test — no duplication of the factory's
    provider switch and no drift. :func:`_text_completer_for` picks the seam that
    matches the client's transport shape.

    ``model`` is forwarded to the factory and **must** be passed for a provider
    that pins no default of its own (``opencode``: adapter spec D6). Callers get
    it from ``eval_cutover.provider_eval_model``; omitting it there would run the
    stakeholder half of the interview on an unpinned model while the interviewer
    half ran on the pinned one.
    """
    intake_client = cast(Any, make_intake_client(provider, model=model))
    return StakeholderSimulator(
        brief=_brief_from_fixture(fixture),
        completer=_text_completer_for(intake_client, max_tokens=max_tokens),
        max_tokens=max_tokens,
    )
