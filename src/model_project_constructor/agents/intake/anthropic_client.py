"""Concrete :class:`IntakeLLMClient` backed by Anthropic's Claude API.

Mirrors the structure of
``packages/data-agent/.../anthropic_client.py`` but with prompts tuned to
the intake interview. We deliberately keep these two clients separate —
they share no methods and live in different packages.

The default model is ``claude-sonnet-4-6`` and was selected from the
session-time system-reminder model family list. It has NOT been verified
against a live API in this session. If the model ID is wrong, first real
invocation will raise from the Anthropic SDK — override via the ``model``
constructor argument or the CLI's future ``--model`` flag.
"""

from __future__ import annotations

import json
import re
from typing import Any

from model_project_constructor.agents.intake.protocol import (
    DraftReportResult,
    GovernanceClassification,
    IntakeLLMClient,
    IntakeLLMError,
    InterviewContext,
    NextQuestionResult,
)

DEFAULT_MODEL = "claude-sonnet-4-6"
DEFAULT_MAX_TOKENS = 4096

SYSTEM_INTERVIEWER = (
    "You are an expert data scientist, business analyst, and consultant "
    "focused on a claims organization within a property & casualty "
    "insurance company that sells auto and property policies. You are "
    "interviewing a business stakeholder to draft an intake document "
    "covering: business problem, proposed solution, model solution "
    "(target and inputs), and estimated value. Ask ONE question at a "
    "time. Drive toward the four required sections and toward a "
    "defensible governance classification (cycle time + risk tier). "
    "When the conversation reaches the model solution's candidate "
    "features, probe for CONCRETE data sources — named systems, "
    "tables, extracts, or feeds — rather than accepting vague answers "
    "like 'we have the data.' If the stakeholder is uncertain about "
    "what data exists, explicitly offer to help identify likely "
    "sources, then ask about the systems typically present in a P&C "
    "claims organization: claims admin (e.g. Guidewire ClaimCenter, "
    "Duck Creek Claims), policy admin, billing and collections, "
    "subrogation recovery tools, fraud / SIU scoring, agent and "
    "customer CRM, and any enterprise data warehouse or data lake "
    "that consolidates these systems. Surface owning team and refresh "
    "cadence when they are material to model feasibility."
)

SYSTEM_GOVERNANCE = (
    "You classify model projects against an internal governance matrix. "
    "cycle_time ∈ {strategic, tactical, operational, continuous}. "
    "risk_tier ∈ {tier_1_critical, tier_2_high, tier_3_moderate, tier_4_low}. "
    "Regulatory frameworks include SR_11_7, NAIC_AIS, EU_AI_ACT_ART_9, "
    "GDPR_ART_22. Be conservative: if in doubt, pick the stricter tier."
)


class AnthropicLLMClient(IntakeLLMClient):
    """Production LLM client for the Intake Agent."""

    def __init__(
        self,
        client: Any | None = None,
        model: str = DEFAULT_MODEL,
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ) -> None:
        if client is None:
            import anthropic

            client = anthropic.Anthropic()
        self._client = client
        self._model = model
        self._max_tokens = max_tokens

    # --- IntakeLLMClient methods ---------------------------------------

    def next_question(self, context: InterviewContext) -> NextQuestionResult:
        user = (
            f"Domain: {context.domain}\n"
            f"Initial problem statement (optional): {context.initial_problem}\n"
            f"Questions asked so far: {context.questions_asked}\n\n"
            f"Conversation so far:\n{_format_qa(context.qa_pairs)}\n\n"
            'Return a JSON object with keys: "question" (the next single '
            'question to ask the stakeholder, empty string if none), '
            '"believe_enough_info" (boolean — true if you now have enough '
            "information to draft all four required sections AND make a "
            "governance classification). Return ONLY the JSON object."
        )
        parsed = self._call_json(SYSTEM_INTERVIEWER, user)
        if not isinstance(parsed, dict):
            raise IntakeLLMError(
                f"next_question: expected JSON object, got {type(parsed).__name__}"
            )
        return NextQuestionResult(
            question=str(parsed.get("question", "")),
            believe_enough_info=bool(parsed.get("believe_enough_info", False)),
        )

    def draft_report(self, context: InterviewContext) -> DraftReportResult:
        user = (
            f"Domain: {context.domain}\n"
            f"Initial problem statement (optional): {context.initial_problem}\n\n"
            f"Conversation:\n{_format_qa(context.qa_pairs)}\n\n"
            "Draft the intake document. Return a JSON object with keys: "
            '"business_problem" (prose), "proposed_solution" (prose), '
            '"model_solution" (object with keys target_variable [str|null], '
            "target_definition, candidate_features [list of str], "
            "model_type [one of supervised_classification, "
            "supervised_regression, unsupervised_clustering, "
            "unsupervised_anomaly, time_series, reinforcement, other], "
            "evaluation_metrics [list of str], is_supervised [bool]), "
            '"estimated_value" (object with keys narrative, '
            "annual_impact_usd_low [number|null], annual_impact_usd_high "
            "[number|null], confidence [one of low/medium/high], "
            "assumptions [list of str]), "
            '"missing_fields" (list of str — any required section you '
            "could not draft). Return ONLY the JSON object."
        )
        parsed = self._call_json(SYSTEM_INTERVIEWER, user)
        if not isinstance(parsed, dict):
            raise IntakeLLMError(
                f"draft_report: expected JSON object, got {type(parsed).__name__}"
            )
        return _build_draft(parsed)

    def classify_governance(
        self, draft: DraftReportResult
    ) -> GovernanceClassification:
        user = (
            f"Draft:\n{json.dumps(_draft_as_dict(draft), indent=2)}\n\n"
            "Classify this project. Return a JSON object with keys: "
            '"cycle_time", "cycle_time_rationale", "risk_tier", '
            '"risk_tier_rationale", "regulatory_frameworks" (list of str), '
            '"affects_consumers" (bool), "uses_protected_attributes" '
            "(bool). Return ONLY the JSON object."
        )
        parsed = self._call_json(SYSTEM_GOVERNANCE, user)
        if not isinstance(parsed, dict):
            raise IntakeLLMError(
                f"classify_governance: expected JSON object, got {type(parsed).__name__}"
            )
        return _build_governance(parsed)

    def revise_report(
        self, draft: DraftReportResult, feedback: str
    ) -> DraftReportResult:
        user = (
            f"Current draft:\n{json.dumps(_draft_as_dict(draft), indent=2)}\n\n"
            f"Stakeholder feedback:\n{feedback}\n\n"
            "Return a revised draft as a JSON object with the same keys "
            "as the original draft (business_problem, proposed_solution, "
            "model_solution, estimated_value, missing_fields). Return "
            "ONLY the JSON object."
        )
        parsed = self._call_json(SYSTEM_INTERVIEWER, user)
        if not isinstance(parsed, dict):
            raise IntakeLLMError(
                f"revise_report: expected JSON object, got {type(parsed).__name__}"
            )
        return _build_draft(parsed)

    # --- internals -----------------------------------------------------

    def _call_json(self, system: str, user: str) -> Any:
        response = self._client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        # Mirrors the pattern used by the data agent's AnthropicLLMClient:
        # the SDK union includes non-text block types we never produce, so a
        # runtime str() wrapping the .text attribute is safe but mypy-visible.
        raw = str(response.content[0].text)  # type: ignore[union-attr]
        return _extract_json(raw)


# --- helpers -----------------------------------------------------------


def _format_qa(qa_pairs: list[dict[str, str]] | list[Any]) -> str:
    if not qa_pairs:
        return "(no questions asked yet)"
    lines: list[str] = []
    for i, pair in enumerate(qa_pairs, start=1):
        q = pair["question"] if isinstance(pair, dict) else getattr(pair, "question", "")
        a = pair["answer"] if isinstance(pair, dict) else getattr(pair, "answer", "")
        lines.append(f"Q{i}: {q}\nA{i}: {a}")
    return "\n\n".join(lines)


def _draft_as_dict(draft: DraftReportResult) -> dict[str, Any]:
    return {
        "business_problem": draft.business_problem,
        "proposed_solution": draft.proposed_solution,
        "model_solution": dict(draft.model_solution),
        "estimated_value": dict(draft.estimated_value),
        "missing_fields": list(draft.missing_fields),
    }


def _build_draft(parsed: dict[str, Any]) -> DraftReportResult:
    try:
        return DraftReportResult(
            business_problem=str(parsed["business_problem"]),
            proposed_solution=str(parsed["proposed_solution"]),
            model_solution=dict(parsed["model_solution"]),
            estimated_value=dict(parsed["estimated_value"]),
            missing_fields=[str(x) for x in parsed.get("missing_fields") or []],
        )
    except KeyError as exc:
        raise IntakeLLMError(f"draft_report: missing key {exc}") from exc


def _build_governance(parsed: dict[str, Any]) -> GovernanceClassification:
    try:
        return GovernanceClassification(
            cycle_time=str(parsed["cycle_time"]),
            cycle_time_rationale=str(parsed["cycle_time_rationale"]),
            risk_tier=str(parsed["risk_tier"]),
            risk_tier_rationale=str(parsed["risk_tier_rationale"]),
            regulatory_frameworks=[str(x) for x in parsed.get("regulatory_frameworks") or []],
            affects_consumers=bool(parsed["affects_consumers"]),
            uses_protected_attributes=bool(parsed["uses_protected_attributes"]),
        )
    except KeyError as exc:
        raise IntakeLLMError(f"classify_governance: missing key {exc}") from exc


_CODE_FENCE = re.compile(r"^```(?:json)?\s*\n(.*?)\n```\s*$", re.DOTALL)


def _extract_json(raw: str) -> Any:
    stripped = raw.strip()
    match = _CODE_FENCE.match(stripped)
    if match:
        stripped = match.group(1).strip()
    try:
        return json.loads(stripped)
    except json.JSONDecodeError as exc:
        raise IntakeLLMError(
            f"Claude returned non-JSON: {exc}: {stripped[:200]!r}"
        ) from exc
