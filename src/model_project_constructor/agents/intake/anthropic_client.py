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

from anthropic.types import TextBlock

from model_project_constructor._vocab_guard import join_members
from model_project_constructor.agents.intake.protocol import (
    DraftReportResult,
    GovernanceClassification,
    IntakeLLMClient,
    IntakeLLMError,
    InterviewContext,
    NextQuestionResult,
)
from model_project_constructor.schemas.v1.common import CycleTime, ModelType, RiskTier
from model_project_constructor.schemas.v1.intake import (
    Confidence,
    CounterfactualDesign,
    ReviewCadence,
)

DEFAULT_MODEL = "claude-sonnet-4-6"
DEFAULT_MAX_TOKENS = 4096

_INTERVIEWER_BASE = (
    "You are an expert data scientist, business analyst, and consultant "
    "focused on a claims organization within a property & casualty "
    "insurance company that sells auto and property policies. You are "
    "interviewing a business stakeholder to draft an intake document "
    "covering FIVE required sections: business problem, proposed "
    "solution, model solution (target and inputs), estimated value, "
    "and value measurement plan (how downstream success will be "
    "demonstrated). Ask ONE question at a time. Drive toward the "
    "five required sections and toward a defensible governance "
    "classification (cycle time + risk tier). Reserve roughly 3-4 of "
    "your question budget for the value measurement plan: the "
    "baseline metric the business uses today, its definition and "
    "measurement window, the counterfactual design that will "
    "attribute outcomes to the model, the evaluation horizon, the "
    "logging requirements, the review cadence, success criteria, and "
    "decision rights for retire/retrain. "
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

# Curated subset of docs/style/statistical_terms.md injected into
# SYSTEM_INTERVIEWER so drafted intake reports use precise statistical
# terminology natively instead of relying on review-time correction. Covers
# the highest-impact conflations for intake prose (business-problem +
# model-solution + estimated-value sections). NOT injected into
# SYSTEM_GOVERNANCE, which emits regulatory labels rather than statistical
# prose.
_STATISTICAL_TERMS_NOTE = (
    "\n\n"
    "When drafting the intake report, use precise statistical "
    "terminology. See `docs/style/statistical_terms.md` for the "
    "authoritative glossary. Distinctions to honor:\n"
    "- probability = P(event) in [0, 1]; likelihood = L(θ|data), a "
    "function of parameters with data fixed — not a probability over "
    "events.\n"
    "- statistical significance (p below threshold) is not the same "
    "as practical significance (effect large enough to matter).\n"
    "- bias has two technical meanings: statistical (E[θ̂] − θ, "
    "estimator error) and algorithmic/fairness (disparity across "
    "protected groups). Disambiguate when both could apply.\n"
    "- risk is ambiguous in P&C: statistical risk = expected loss; "
    "insurance risk = covered hazard / insured peril. Say 'model "
    "risk' or 'prediction risk' for the statistical sense.\n"
    "- accuracy = (TP+TN)/N; precision = TP/(TP+FP). A stakeholder "
    "asking for 'more accurate' predictions often means higher "
    "precision or recall, not overall accuracy.\n"
    "- overfitting is the gap between training and held-out "
    "performance, not absolute test error.\n"
    "- class imbalance is a property of the data, not the model; it "
    "reshapes which metrics inform (prefer PR AUC + recall over "
    "accuracy on imbalanced classes).\n"
    "If a stakeholder conflates a statistical term with its "
    "colloquial cousin, prefer the precise term in the draft; where "
    "the distinction matters for the model solution, ask a "
    "follow-up to confirm which meaning was intended."
)

SYSTEM_INTERVIEWER = _INTERVIEWER_BASE + _STATISTICAL_TERMS_NOTE

# Regulatory frameworks the intake agent is told to classify against. This
# tuple is the producer-side source for the prompt's framework enumeration; the
# website agent's ``_FRAMEWORK_ARTIFACTS`` map (``governance_templates.py``) is
# the consumer that binds each framework to its governance artifacts. The two
# MUST stay in lockstep — a framework named here but unmapped there scaffolds
# zero artifacts (the Audit #39 governance hole). Parity is pinned by
# ``tests/agents/website/test_governance.py`` (``set(GOVERNANCE_FRAMEWORKS) ==
# set(_FRAMEWORK_ARTIFACTS)``); add a framework here only alongside its mapping.
GOVERNANCE_FRAMEWORKS: tuple[str, ...] = (
    "SR_11_7",
    "NAIC_AIS",
    "EU_AI_ACT_ART_9",
    "GDPR_ART_22",
    "ASOP_56",
)

SYSTEM_GOVERNANCE = (
    "You classify model projects against an internal governance matrix. "
    f"cycle_time ∈ {{{join_members(CycleTime)}}}. "
    f"risk_tier ∈ {{{join_members(RiskTier)}}}. "
    "Regulatory frameworks include "
    + ", ".join(GOVERNANCE_FRAMEWORKS)
    + ". Be conservative: if in doubt, pick the stricter tier."
)

# Static JSON-shape instructions for ``draft_report``. Pulled out of the method
# into a module constant so (a) the controlled-vocabulary enumerations
# (model_type, confidence, counterfactual_design, review_cadence) DERIVE from
# their schema ``Literal``s via ``join_members`` instead of being hand-listed in
# prose (Overhaul O4 producer single-sourcing), and (b) a member-presence test
# can pin the derived prose. Each enumeration keeps its own separator and
# decoration: ``model_type`` uses ", " inside "[one of …]"; ``confidence`` uses
# "/" (low/medium/high); the two Optional fields keep the literal ", or null]"
# framing. ``join_members`` reproduces the members in definition order, so the
# rendered text is byte-identical to the previous hand-written prose.
_DRAFT_REPORT_INSTRUCTIONS = (
    "Draft the intake document. Return a JSON object with keys: "
    '"business_problem" (prose), "proposed_solution" (prose), '
    '"model_solution" (object with keys target_variable [str|null], '
    "target_definition, candidate_features [list of str], "
    f"model_type [one of {join_members(ModelType)}], "
    "evaluation_metrics [list of str], is_supervised [bool]), "
    '"estimated_value" (object with keys narrative, '
    "annual_impact_usd_low [number|null], annual_impact_usd_high "
    f"[number|null], confidence [one of {join_members(Confidence, sep='/')}], "
    "assumptions [list of str], cost_of_inaction_narrative "
    "[str|null], annual_cost_of_inaction_usd_low [number|null], "
    "annual_cost_of_inaction_usd_high [number|null], "
    "implementation_cost_band_usd_low [number|null], "
    "implementation_cost_band_usd_high [number|null], "
    "payback_months [int|null], value_drivers [list of str]), "
    '"value_measurement_plan" (object with keys '
    "baseline_metric_name [str|null], "
    "baseline_metric_definition [str|null — formula or "
    "SQL-derivable spec], baseline_measurement_window "
    '[str|null e.g. "trailing 12 months"], counterfactual_design '
    f"[one of {join_members(CounterfactualDesign)}, or null], "
    "counterfactual_rationale [str|null], "
    "attribution_method_narrative [str|null], "
    "evaluation_horizon_months [int|null], logging_requirements "
    f"[list of str], review_cadence [one of {join_members(ReviewCadence)}, "
    "or null], success_criteria [list of "
    "str], decision_rights [str|null]), "
    '"missing_fields" (list of str — any required section you '
    "could not draft). Return ONLY the JSON object."
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
            "information to draft all five required sections (including "
            "the value measurement plan) AND make a governance "
            "classification). Return ONLY the JSON object."
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
            + _DRAFT_REPORT_INSTRUCTIONS
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
            "model_solution, estimated_value, value_measurement_plan, "
            "missing_fields). Return ONLY the JSON object."
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
        # The Anthropic SDK types ``response.content`` as a union that
        # includes non-text blocks (tool_use, thinking, …). We only request
        # plain text, but a live response could still lead with a non-text
        # block, so guard before reading ``.text`` — an unguarded access
        # raises ``AttributeError`` instead of our typed error. The list can
        # also come back empty, so guard the index access first (``IndexError``
        # otherwise). Mirrors the data agent's ``_call_claude``, preserving
        # intake's ``IntakeLLMError`` (the data agent raises ``LLMParseError``).
        if not response.content:
            raise IntakeLLMError("Claude returned an empty content list")
        block = response.content[0]
        if not isinstance(block, TextBlock):
            raise IntakeLLMError(
                f"expected TextBlock from Claude, got {type(block).__name__}"
            )
        return _extract_json(block.text)


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
        "value_measurement_plan": dict(draft.value_measurement_plan),
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
            value_measurement_plan=dict(parsed.get("value_measurement_plan") or {}),
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


_CODE_FENCE = re.compile(r"```(?:json)?\s*\n?(.*?)\n?```", re.DOTALL)


def _extract_json(raw: str) -> Any:
    """Parse JSON from an LLM response, defensively stripping markdown fences.

    Claude sometimes returns clean JSON and sometimes wraps it in a ``` ```json
    … ``` ``` (or ``` ``` … ``` ```) fence, occasionally with prose before or
    after the fence. We try the bare response first (fast path: already valid
    JSON); on :class:`json.JSONDecodeError` we search for a fenced block
    anywhere in the response and retry with its contents. Only if both attempts
    fail do we raise :class:`IntakeLLMError`, surfacing the bare-parse error
    since that is what the caller sees on a truly malformed response.

    Ported from the data agent's hardened ``_extract_json`` in Session 98
    (audit finding #16). The intake copy was a stale pre-hardening version
    whose regex required the *entire* stripped response to be a fenced block
    (``^…$`` anchors with ``.match``); a real ``claude-sonnet-4-6`` response
    that added prose around the fence crashed here. See the data agent's twin
    and Session 51 ``run_id=run_b1_resume_live_1776570556``.
    """
    stripped = raw.strip()
    try:
        return json.loads(stripped)
    except json.JSONDecodeError as first_error:
        match = _CODE_FENCE.search(stripped)
        if match:
            candidate = match.group(1).strip()
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                pass
        raise IntakeLLMError(
            f"Claude returned non-JSON: {first_error}: {stripped[:200]!r}"
        ) from first_error
