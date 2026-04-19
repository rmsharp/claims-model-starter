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
)
from model_project_constructor_data_agent.schemas import (
    DataRequest,
    Datasheet,
    QualityCheck,
)

DEFAULT_MODEL = "claude-sonnet-4-6"
DEFAULT_MAX_TOKENS = 4096


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
        self, request: DataRequest, previous_error: str | None = None
    ) -> list[PrimaryQuerySpec]:
        retry_hint = ""
        if previous_error:
            retry_hint = (
                f"\n\nYour previous response produced invalid SQL. Error: "
                f"{previous_error}\nReturn corrected SQL this time."
            )

        system = (
            "You are a senior P&C insurance data analyst. Given a data "
            "collection request, return one or more primary SQL queries that "
            "extract the target population. Always return valid SELECT SQL."
        )
        user = (
            f"DataRequest:\n{_dump_request(request)}\n{retry_hint}\n\n"
            'Return a JSON array. Each element is an object with keys: '
            '"name" (snake_case identifier), "sql" (a SELECT statement), '
            '"purpose" (one sentence on why), "expected_row_count_order" '
            '(one of "tens", "hundreds", "thousands", "millions"). '
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
    return json.dumps(request.model_dump(mode="json"), indent=2)


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
