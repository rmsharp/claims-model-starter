"""Concrete :class:`LLMClient` backed by Anthropic's Claude API.

This is the production LLM integration for the Data Agent. Tests inject a
deterministic fake; real runs use this class.

Design notes:

- Each protocol method builds a prompt, calls Claude, parses JSON, and
  returns the typed intermediate dataclass or schema object. Prompts ask
  Claude to emit a strict JSON shape so downstream code can be schema-bound
  without fuzzy string parsing.

- The Anthropic client is injected via the ``client`` constructor argument
  so tests can pass a mock. Production code calls ``AnthropicLLMClient()``
  which constructs a real :class:`anthropic.Anthropic` using ``ANTHROPIC_API_KEY``.

- The default model is ``claude-sonnet-4-6`` (fast, cost-effective for SQL
  authoring). Callers can override via the ``model`` argument.

- Parsing is defensive: Claude sometimes wraps JSON in ``` ```json ... ``` ```
  code fences, sometimes with surrounding prose. :func:`_extract_json` tries
  a bare parse first (fast path for clean JSON) and falls back to a
  fence-search on failure, so prose before or after the fence does not break
  parsing. Unparseable responses raise :class:`LLMParseError` so the Data
  Agent's outer try/except surfaces them as ``status="EXECUTION_FAILED"``
  instead of crashing.
"""

from __future__ import annotations

import json
import re
from typing import Any

from anthropic.types import TextBlock

from model_project_constructor_data_agent.llm import (
    PrimaryQuerySpec,
    QualityCheckSpec,
    SummaryResult,
    TableRanking,
)
from model_project_constructor_data_agent.schemas import (
    DataRequest,
    Datasheet,
    DataSourceEntry,
    DataSourceInventory,
    QualityCheck,
)

DEFAULT_MODEL = "claude-sonnet-4-6"
DEFAULT_MAX_TOKENS = 4096

MAX_INVENTORY_ENTRIES_IN_PROMPT = 20
MAX_INVENTORY_FIELD_CHARS = 2000

# Curated subset of docs/style/statistical_terms.md injected into the
# summarize() and generate_datasheet() system strings so prose-generating
# data-agent surfaces use precise statistical terminology natively instead
# of relying on review-time correction. NOT injected into
# generate_primary_queries(), generate_quality_checks(), or
# rank_candidate_tables() — those methods produce SQL or 0.0-1.0 relevance
# scores, where statistical-terminology conflations are rare.
_STATISTICAL_TERMS_NOTE = (
    "\n\n"
    "Use precise statistical terminology in prose. See "
    "`docs/style/statistical_terms.md` for the authoritative glossary. "
    "Distinctions relevant to data-agent reports:\n"
    "- class imbalance is a property of the data, not the model; it "
    "reshapes which metrics inform (prefer PR AUC + recall over "
    "accuracy on imbalanced classes).\n"
    "- data leakage = information from outside the training set "
    "influences the model (future features, target leakage, "
    "test-set statistics). Time-series and grouped data are "
    "especially prone; call it out when you see it in the query "
    "design.\n"
    "- calibration (predicted probabilities match observed "
    "frequencies) is distinct from discrimination (ability to rank "
    "positives above negatives). AUC measures discrimination, not "
    "calibration.\n"
    "- bias has two technical meanings: statistical (estimator "
    "error, E[θ̂] − θ) and algorithmic/fairness (disparity across "
    "protected groups). A datasheet 'known_biases' entry usually "
    "means the fairness sense — say so explicitly.\n"
    "- P&C accounting: frequency = claims per exposure-unit-period; "
    "severity = expected cost per claim; pure premium = frequency × "
    "severity."
)


class LLMParseError(ValueError):
    """Raised when Claude's response cannot be parsed into the expected shape."""


class AnthropicLLMClient:
    """Production LLM client for the Data Agent."""

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

    def generate_primary_queries(
        self,
        request: DataRequest,
        previous_error: str | None = None,
        *,
        data_source_inventory: DataSourceInventory | None = None,
    ) -> list[PrimaryQuerySpec]:
        retry_hint = ""
        if previous_error:
            retry_hint = (
                f"\n\nYour previous response produced invalid SQL. Error: "
                f"{previous_error}\nReturn corrected SQL this time."
            )

        inventory_block = _build_inventory_block(data_source_inventory)
        inventory_hint = f"\n\n{inventory_block}" if inventory_block else ""

        system = (
            "You are a senior P&C insurance data analyst. Given a data "
            "collection request, return one or more primary SQL queries that "
            "extract the target population. Always return valid SELECT SQL."
        )
        user = (
            f"DataRequest:\n{_dump_request(request)}{retry_hint}{inventory_hint}\n\n"
            'Return a JSON array. Each element is an object with keys: '
            '"name" (snake_case identifier), "sql" (a SELECT statement), '
            '"purpose" (one sentence on why), "expected_row_count_order" '
            '(one of "tens", "hundreds", "thousands", "millions"), and '
            '"inventory_entries_used" (list of fully_qualified_name strings '
            "from the Available data sources block that your SQL references; "
            "empty list if no inventory was provided or none were used). "
            "Return ONLY the JSON array, no prose."
        )
        raw = self._call_claude(system, user)
        parsed = _extract_json(raw)
        if not isinstance(parsed, list):
            raise LLMParseError(
                f"generate_primary_queries: expected JSON array, got {type(parsed).__name__}"
            )
        return [
            PrimaryQuerySpec(
                name=str(item["name"]),
                sql=str(item["sql"]),
                purpose=str(item["purpose"]),
                expected_row_count_order=str(item["expected_row_count_order"]),
                inventory_entries_used=[
                    str(x) for x in item.get("inventory_entries_used", [])
                ],
            )
            for item in parsed
        ]

    def generate_quality_checks(
        self, request: DataRequest, primary_queries: list[PrimaryQuerySpec]
    ) -> list[list[QualityCheckSpec]]:
        system = (
            "You are a senior P&C insurance data analyst. For each primary "
            "query, write quality-check SQL that verifies assumptions about "
            "row counts, non-null keys, and value ranges."
        )
        queries_block = "\n".join(
            f"[{i}] name={q.name} purpose={q.purpose}\nSQL:\n{q.sql}"
            for i, q in enumerate(primary_queries)
        )
        user = (
            f"DataRequest:\n{_dump_request(request)}\n\n"
            f"Primary queries:\n{queries_block}\n\n"
            'Return a JSON array-of-arrays. The outer array has exactly '
            f"{len(primary_queries)} elements, one per primary query (in order). "
            'Each inner array contains objects with keys: "check_name", '
            '"check_sql", "expectation". Return ONLY the JSON, no prose.'
        )
        raw = self._call_claude(system, user)
        parsed = _extract_json(raw)
        if not isinstance(parsed, list):
            raise LLMParseError(
                f"generate_quality_checks: expected JSON array, got {type(parsed).__name__}"
            )
        return [
            [
                QualityCheckSpec(
                    check_name=str(qc["check_name"]),
                    check_sql=str(qc["check_sql"]),
                    expectation=str(qc["expectation"]),
                )
                for qc in group
            ]
            for group in parsed
        ]

    def summarize(
        self,
        request: DataRequest,
        primary_queries: list[PrimaryQuerySpec],
        quality_checks: list[list[QualityCheck]],
        db_executed: bool,
    ) -> SummaryResult:
        system = (
            "You are a senior P&C insurance data scientist writing a concise "
            "summary of a data collection run for the model team."
            + _STATISTICAL_TERMS_NOTE
        )
        qc_block = _dump_qc_status(quality_checks, db_executed)
        user = (
            f"DataRequest:\n{_dump_request(request)}\n\n"
            f"Quality check results:\n{qc_block}\n\n"
            'Return a JSON object with keys: "summary" (2-4 sentences), '
            '"confirmed_expectations" (list of strings), '
            '"unconfirmed_expectations" (list of strings), '
            '"data_quality_concerns" (list of strings). '
            "Return ONLY the JSON object, no prose."
        )
        raw = self._call_claude(system, user)
        parsed = _extract_json(raw)
        if not isinstance(parsed, dict):
            raise LLMParseError(
                f"summarize: expected JSON object, got {type(parsed).__name__}"
            )
        return SummaryResult(
            summary=str(parsed["summary"]),
            confirmed_expectations=[str(x) for x in parsed["confirmed_expectations"]],
            unconfirmed_expectations=[str(x) for x in parsed["unconfirmed_expectations"]],
            data_quality_concerns=[str(x) for x in parsed["data_quality_concerns"]],
        )

    def generate_datasheet(
        self, request: DataRequest, primary_query: PrimaryQuerySpec
    ) -> Datasheet:
        system = (
            "You are writing a datasheet per Gebru et al. 2021 ('Datasheets "
            "for Datasets') for an insurance claims extract."
            + _STATISTICAL_TERMS_NOTE
        )
        user = (
            f"DataRequest:\n{_dump_request(request)}\n\n"
            f"Primary query: {primary_query.name}\n"
            f"Purpose: {primary_query.purpose}\n"
            f"SQL:\n{primary_query.sql}\n\n"
            'Return a JSON object with keys: "motivation", "composition", '
            '"collection_process", "preprocessing", "uses", "known_biases" '
            '(list of strings), "maintenance". Return ONLY the JSON object.'
        )
        raw = self._call_claude(system, user)
        parsed = _extract_json(raw)
        if not isinstance(parsed, dict):
            raise LLMParseError(
                f"generate_datasheet: expected JSON object, got {type(parsed).__name__}"
            )
        return Datasheet(
            motivation=str(parsed["motivation"]),
            composition=str(parsed["composition"]),
            collection_process=str(parsed["collection_process"]),
            preprocessing=str(parsed["preprocessing"]),
            uses=str(parsed["uses"]),
            known_biases=[str(x) for x in parsed["known_biases"]],
            maintenance=str(parsed["maintenance"]),
        )

    def rank_candidate_tables(
        self,
        entries: list[DataSourceEntry],
        request_context: str | None,
    ) -> list[TableRanking]:
        """Rank candidate tables against a request context.

        Called by ``discovery.probe_information_schema`` when
        ``--rank-with-llm`` is set. Returns one :class:`TableRanking` per
        input entry (in any order). Entries not returned by Claude are
        assigned no ranking by the caller — ``relevance_score`` stays
        ``None`` on the corresponding :class:`DataSourceEntry`.
        """
        system = (
            "You are a senior P&C insurance data analyst. Given a candidate "
            "list of database tables and a request context, rank each table "
            "by its relevance to the request on a 0.0-1.0 scale."
        )
        table_summaries = "\n".join(
            f"- {e.fully_qualified_name} "
            f"({e.entity_kind}, {len(e.columns)} cols): "
            f"{', '.join(c.name for c in e.columns[:8])}"
            for e in entries
        )
        context = request_context or "(no explicit request context; rank by generality)"
        user = (
            f"Request context: {context}\n\n"
            f"Candidate tables:\n{table_summaries}\n\n"
            "Return a JSON array. Each element is an object with keys: "
            '"fully_qualified_name" (verbatim from the input), '
            '"relevance_score" (float 0.0-1.0), "relevance_reason" (one '
            "sentence). Return ONLY the JSON array, no prose."
        )
        raw = self._call_claude(system, user)
        parsed = _extract_json(raw)
        if not isinstance(parsed, list):
            raise LLMParseError(
                f"rank_candidate_tables: expected JSON array, got {type(parsed).__name__}"
            )
        return [
            TableRanking(
                fully_qualified_name=str(item["fully_qualified_name"]),
                relevance_score=float(item["relevance_score"]),
                relevance_reason=str(item["relevance_reason"]),
            )
            for item in parsed
        ]

    def _call_claude(self, system: str, user: str) -> str:
        response = self._client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        block = response.content[0]
        if not isinstance(block, TextBlock):
            raise LLMParseError(
                f"expected TextBlock from Claude, got {type(block).__name__}"
            )
        return block.text


def _dump_request(request: DataRequest) -> str:
    """Serialize a request for prompt insertion, hiding the inventory.

    The inventory is rendered by :func:`_build_inventory_block` in a more
    prompt-friendly shape; duplicating it in the raw JSON dump would waste
    tokens and risk the LLM parsing two inconsistent copies on large
    inventories.
    """
    payload = request.model_dump(mode="json")
    payload.pop("data_source_inventory", None)
    return json.dumps(payload, indent=2)


def _sanitize_prompt_field(
    value: str | None, max_chars: int = MAX_INVENTORY_FIELD_CHARS
) -> str:
    """Strip control characters (keeping newline/tab) and bound length.

    Producer-supplied content (``description``, ``relevance_reason``) is fed
    to Claude. Adversarial or malformed content could distort the prompt or
    blow the token budget; this helper removes control characters below
    ASCII 32 (except ``\\n`` and ``\\t``) and truncates at ``max_chars`` with
    an ellipsis. Plan §9 Phase 3 gotcha #2 + §12 Q5 (default 2000).
    """
    if value is None:
        return ""
    cleaned = "".join(
        ch for ch in value if ch in ("\n", "\t") or ord(ch) >= 32
    )
    if len(cleaned) > max_chars:
        cleaned = cleaned[:max_chars] + "..."
    return cleaned


def _build_inventory_block(
    inventory: DataSourceInventory | None,
) -> str:
    """Render a :class:`DataSourceInventory` as a prompt-ready summary block.

    ``None`` or empty-entries inventories yield an empty string (pre-Phase-3
    behaviour preserved). Non-empty inventories are sorted by
    ``relevance_score`` descending (None → 0.0) and truncated to
    :data:`MAX_INVENTORY_ENTRIES_IN_PROMPT`; a trailing note reports the
    truncation count when applicable.
    """
    if inventory is None or not inventory.entries:
        return ""
    ranked = sorted(
        inventory.entries,
        key=lambda e: e.relevance_score if e.relevance_score is not None else 0.0,
        reverse=True,
    )
    top = ranked[:MAX_INVENTORY_ENTRIES_IN_PROMPT]
    remainder = len(ranked) - len(top)
    lines: list[str] = [
        "Available data sources (prefer these tables when writing SQL):"
    ]
    for entry in top:
        col_preview = ", ".join(c.name for c in entry.columns[:8])
        if len(entry.columns) > 8:
            col_preview += f", ... (+{len(entry.columns) - 8} more)"
        parts = [f"- {entry.fully_qualified_name} ({entry.entity_kind})"]
        if col_preview:
            parts.append(f"  columns: {col_preview}")
        desc = _sanitize_prompt_field(entry.description)
        if desc:
            parts.append(f"  description: {desc}")
        reason = _sanitize_prompt_field(entry.relevance_reason)
        if reason:
            parts.append(f"  relevance: {reason}")
        lines.append("\n".join(parts))
    if remainder > 0:
        lines.append(f"... and {remainder} more sources truncated.")
    return "\n".join(lines)


def _dump_qc_status(
    quality_checks: list[list[QualityCheck]], db_executed: bool
) -> str:
    header = f"db_executed={db_executed}\n"
    lines: list[str] = []
    for i, group in enumerate(quality_checks):
        for qc in group:
            lines.append(
                f"[{i}] {qc.check_name}: {qc.execution_status} — {qc.result_summary}"
            )
    return header + ("\n".join(lines) if lines else "(no checks)")


_CODE_FENCE = re.compile(r"```(?:json)?\s*\n?(.*?)\n?```", re.DOTALL)


def _extract_json(raw: str) -> Any:
    """Parse JSON from an LLM response, defensively stripping markdown fences.

    Models sometimes return clean JSON and sometimes wrap it in a ``` ```json
    … ``` ``` (or ``` ``` … ``` ```) fence, occasionally with prose before or
    after the fence. We try the bare response first (fast path: already valid
    JSON); on :class:`json.JSONDecodeError` we search for a fenced block
    anywhere in the response and retry with its contents. Only if both attempts
    fail do we raise :class:`LLMParseError`, surfacing the bare-parse error
    since that's what the caller sees on a truly malformed response.

    Tracked bug: Session 51 live-LLM run `run_id=run_b1_resume_live_1776570556`
    crashed here because the previous regex required the entire stripped
    response to be a fenced block (``^…$`` anchors); sonnet-4-6 added prose
    around the fence, and :func:`json.loads` saw the opening backticks.
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
        raise LLMParseError(
            f"Claude returned non-JSON: {first_error}: {stripped[:200]!r}"
        ) from first_error
