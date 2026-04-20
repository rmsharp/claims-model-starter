"""Unit tests for :class:`AnthropicLLMClient`.

These tests mock the anthropic SDK at the client boundary so no network or
API key is required. The goal is to verify the protocol methods correctly
build prompts, parse JSON responses, and propagate malformed responses as
:class:`LLMParseError`. The prompt text itself is not asserted against —
only the structure of the parsed output.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import pytest
from anthropic.types import TextBlock
from model_project_constructor_data_agent.anthropic_client import (
    MAX_INVENTORY_ENTRIES_IN_PROMPT,
    MAX_INVENTORY_FIELD_CHARS,
    AnthropicLLMClient,
    LLMParseError,
    _build_inventory_block,
    _dump_request,
    _extract_json,
    _sanitize_prompt_field,
)
from model_project_constructor_data_agent.llm import (
    LLMClient,
    PrimaryQuerySpec,
)
from model_project_constructor_data_agent.schemas import (
    ColumnMetadata,
    DataGranularity,
    DataRequest,
    DataSourceEntry,
    DataSourceInventory,
    ProducerMetadata,
)

FIXED_TS = datetime(2026, 4, 19, 12, 0, 0, tzinfo=UTC)


@dataclass
class _FakeMessages:
    canned: list[str]
    calls: list[dict[str, Any]]

    def create(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        payload = self.canned.pop(0)
        return type("R", (), {"content": [TextBlock(text=payload, type="text")]})()


@dataclass
class _FakeAnthropic:
    messages: _FakeMessages


def _fake_client(responses: list[str]) -> tuple[_FakeAnthropic, _FakeMessages]:
    msgs = _FakeMessages(canned=list(responses), calls=[])
    return _FakeAnthropic(messages=msgs), msgs


@pytest.fixture
def request_obj() -> DataRequest:
    return DataRequest(
        target_description="subrogation recovery on TX auto claims",
        target_granularity=DataGranularity(unit="claim", time_grain="event"),
        required_features=["paid_amount"],
        population_filter="TX auto",
        time_range="2024",
        source="standalone",
        source_ref="anthropic-test",
    )


def test_protocol_conformance() -> None:
    fake, _ = _fake_client([])
    client = AnthropicLLMClient(client=fake, model="fake-model")
    assert isinstance(client, LLMClient)


def test_call_claude_rejects_non_text_block(request_obj: DataRequest) -> None:
    class _NotATextBlock:
        pass

    fake_msgs = _FakeMessages(canned=[], calls=[])

    def create(**kwargs: Any) -> Any:
        fake_msgs.calls.append(kwargs)
        return type("R", (), {"content": [_NotATextBlock()]})()

    fake_msgs.create = create  # type: ignore[method-assign]
    fake = _FakeAnthropic(messages=fake_msgs)
    client = AnthropicLLMClient(client=fake, model="fake-model")

    with pytest.raises(LLMParseError, match="expected TextBlock"):
        client.generate_primary_queries(request_obj)


def test_generate_primary_queries_parses_json_array(
    request_obj: DataRequest,
) -> None:
    canned = """[
        {
            "name": "tx_claims",
            "sql": "SELECT * FROM claims WHERE state = 'TX'",
            "purpose": "TX training set",
            "expected_row_count_order": "thousands"
        }
    ]"""
    fake, msgs = _fake_client([canned])
    client = AnthropicLLMClient(client=fake, model="fake-model")

    specs = client.generate_primary_queries(request_obj)

    assert len(specs) == 1
    assert specs[0].name == "tx_claims"
    assert specs[0].expected_row_count_order == "thousands"
    assert len(msgs.calls) == 1
    assert msgs.calls[0]["model"] == "fake-model"


def test_generate_primary_queries_strips_code_fence(
    request_obj: DataRequest,
) -> None:
    canned = """```json
[{"name": "q1", "sql": "SELECT 1", "purpose": "x", "expected_row_count_order": "tens"}]
```"""
    fake, _ = _fake_client([canned])
    client = AnthropicLLMClient(client=fake, model="fake-model")
    specs = client.generate_primary_queries(request_obj)
    assert specs[0].name == "q1"


def test_generate_primary_queries_with_retry_hint(
    request_obj: DataRequest,
) -> None:
    canned = (
        '[{"name": "q", "sql": "SELECT 1",'
        ' "purpose": "x", "expected_row_count_order": "tens"}]'
    )
    fake, msgs = _fake_client([canned])
    client = AnthropicLLMClient(client=fake, model="fake-model")

    client.generate_primary_queries(request_obj, previous_error="syntax error at line 3")

    user_msg = msgs.calls[0]["messages"][0]["content"]
    assert "syntax error at line 3" in user_msg
    assert "previous response produced invalid SQL" in user_msg


def test_generate_primary_queries_non_array_raises(
    request_obj: DataRequest,
) -> None:
    fake, _ = _fake_client(['{"not": "an array"}'])
    client = AnthropicLLMClient(client=fake, model="fake-model")
    with pytest.raises(LLMParseError, match="expected JSON array"):
        client.generate_primary_queries(request_obj)


def test_generate_quality_checks_parses_array_of_arrays(
    request_obj: DataRequest,
) -> None:
    canned = """[
        [
            {"check_name": "n1", "check_sql": "SELECT 1", "expectation": "x"},
            {"check_name": "n2", "check_sql": "SELECT 2", "expectation": "y"}
        ]
    ]"""
    fake, _ = _fake_client([canned])
    client = AnthropicLLMClient(client=fake, model="fake-model")

    primary = [
        PrimaryQuerySpec(
            name="q1",
            sql="SELECT 1",
            purpose="x",
            expected_row_count_order="tens",
        )
    ]
    groups = client.generate_quality_checks(request_obj, primary)

    assert len(groups) == 1
    assert len(groups[0]) == 2
    assert groups[0][0].check_name == "n1"


def test_summarize_parses_json_object(request_obj: DataRequest) -> None:
    canned = """{
        "summary": "all good",
        "confirmed_expectations": ["a"],
        "unconfirmed_expectations": [],
        "data_quality_concerns": ["b"]
    }"""
    fake, _ = _fake_client([canned])
    client = AnthropicLLMClient(client=fake, model="fake-model")

    result = client.summarize(request_obj, [], [], db_executed=True)

    assert result.summary == "all good"
    assert result.confirmed_expectations == ["a"]
    assert result.data_quality_concerns == ["b"]


def test_summarize_non_object_raises(request_obj: DataRequest) -> None:
    fake, _ = _fake_client(["[]"])
    client = AnthropicLLMClient(client=fake, model="fake-model")
    with pytest.raises(LLMParseError, match="expected JSON object"):
        client.summarize(request_obj, [], [], db_executed=True)


def test_generate_datasheet_parses_json_object(
    request_obj: DataRequest,
) -> None:
    canned = """{
        "motivation": "m",
        "composition": "c",
        "collection_process": "cp",
        "preprocessing": "pp",
        "uses": "u",
        "known_biases": ["bias1"],
        "maintenance": "mt"
    }"""
    fake, _ = _fake_client([canned])
    client = AnthropicLLMClient(client=fake, model="fake-model")

    spec = PrimaryQuerySpec(
        name="q",
        sql="SELECT 1",
        purpose="x",
        expected_row_count_order="tens",
    )
    sheet = client.generate_datasheet(request_obj, spec)

    assert sheet.motivation == "m"
    assert sheet.known_biases == ["bias1"]


def test_generate_datasheet_non_object_raises(request_obj: DataRequest) -> None:
    fake, _ = _fake_client(["[]"])
    client = AnthropicLLMClient(client=fake, model="fake-model")
    spec = PrimaryQuerySpec(
        name="q",
        sql="SELECT 1",
        purpose="x",
        expected_row_count_order="tens",
    )
    with pytest.raises(LLMParseError, match="expected JSON object"):
        client.generate_datasheet(request_obj, spec)


def test_generate_quality_checks_non_array_raises(
    request_obj: DataRequest,
) -> None:
    fake, _ = _fake_client(['{"not": "array"}'])
    client = AnthropicLLMClient(client=fake, model="fake-model")
    with pytest.raises(LLMParseError, match="expected JSON array"):
        client.generate_quality_checks(request_obj, [])


def test_extract_json_plain_object() -> None:
    assert _extract_json('{"a": 1}') == {"a": 1}


def test_extract_json_with_json_fence() -> None:
    assert _extract_json('```json\n{"a": 1}\n```') == {"a": 1}


def test_extract_json_with_plain_fence() -> None:
    assert _extract_json('```\n{"a": 1}\n```') == {"a": 1}


def test_extract_json_malformed_raises() -> None:
    with pytest.raises(LLMParseError, match="non-JSON"):
        _extract_json("not json at all")


def test_extract_json_prose_before_fence() -> None:
    """Regression for run_id=run_b1_resume_live_1776570556 (Session 51)."""
    raw = 'Here is the JSON:\n```json\n{"a": 1}\n```'
    assert _extract_json(raw) == {"a": 1}


def test_extract_json_prose_after_fence() -> None:
    """Regression for run_id=run_b1_resume_live_1776570556 (Session 51)."""
    raw = '```json\n[{"check_name": "n1"}]\n```\n\nExplanation: n1 checks rows.'
    assert _extract_json(raw) == [{"check_name": "n1"}]


def test_extract_json_prose_before_and_after_fence() -> None:
    raw = 'Response below:\n```json\n{"x": [1, 2]}\n```\nLet me know if...'
    assert _extract_json(raw) == {"x": [1, 2]}


def test_extract_json_fence_without_language_tag_and_prose() -> None:
    raw = 'Sure, here you go:\n```\n{"ok": true}\n```'
    assert _extract_json(raw) == {"ok": True}


def test_extract_json_bare_json_still_parses() -> None:
    """Fast path: bare JSON (no fence) must not regress after fence rework."""
    assert _extract_json('  {"a": 1}  ') == {"a": 1}
    assert _extract_json('[1, 2, 3]') == [1, 2, 3]


def test_default_construction_uses_anthropic_sdk(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Without a ``client`` arg, the constructor imports anthropic.Anthropic()."""
    import anthropic

    sentinel = object()

    def fake_anthropic_ctor(*args: Any, **kwargs: Any) -> Any:
        return sentinel

    monkeypatch.setattr(anthropic, "Anthropic", fake_anthropic_ctor)
    client = AnthropicLLMClient()
    assert client._client is sentinel


def _sample_entries() -> list[DataSourceEntry]:
    return [
        DataSourceEntry(
            name="claims",
            namespace="public",
            fully_qualified_name="public.claims",
            entity_kind="table",
            columns=[
                ColumnMetadata(
                    name="claim_id", data_type="INTEGER", is_primary_key=True
                ),
                ColumnMetadata(name="loss_amount", data_type="NUMERIC(12,2)"),
            ],
            producer_id="information_schema_probe_v1",
        ),
        DataSourceEntry(
            name="policies",
            namespace="public",
            fully_qualified_name="public.policies",
            entity_kind="table",
            columns=[
                ColumnMetadata(
                    name="policy_id", data_type="INTEGER", is_primary_key=True
                ),
            ],
            producer_id="information_schema_probe_v1",
        ),
    ]


def test_rank_candidate_tables_parses_json_array() -> None:
    canned = """[
        {
            "fully_qualified_name": "public.claims",
            "relevance_score": 0.92,
            "relevance_reason": "target entity"
        },
        {
            "fully_qualified_name": "public.policies",
            "relevance_score": 0.41,
            "relevance_reason": "join key source"
        }
    ]"""
    fake, msgs = _fake_client([canned])
    client = AnthropicLLMClient(client=fake, model="fake-model")

    rankings = client.rank_candidate_tables(
        entries=_sample_entries(),
        request_context="subrogation recovery model",
    )

    assert len(rankings) == 2
    assert rankings[0].fully_qualified_name == "public.claims"
    assert rankings[0].relevance_score == pytest.approx(0.92)
    assert rankings[1].relevance_reason == "join key source"
    user_msg = msgs.calls[0]["messages"][0]["content"]
    assert "subrogation recovery model" in user_msg
    assert "public.claims" in user_msg


def test_rank_candidate_tables_accepts_missing_request_context() -> None:
    canned = (
        '[{"fully_qualified_name": "public.claims", '
        '"relevance_score": 0.5, "relevance_reason": "generic"}]'
    )
    fake, msgs = _fake_client([canned])
    client = AnthropicLLMClient(client=fake, model="fake-model")

    rankings = client.rank_candidate_tables(
        entries=_sample_entries()[:1],
        request_context=None,
    )

    assert len(rankings) == 1
    user_msg = msgs.calls[0]["messages"][0]["content"]
    assert "no explicit request context" in user_msg


def test_rank_candidate_tables_non_array_raises() -> None:
    fake, _ = _fake_client(['{"not": "an array"}'])
    client = AnthropicLLMClient(client=fake, model="fake-model")
    with pytest.raises(LLMParseError, match="expected JSON array"):
        client.rank_candidate_tables(
            entries=_sample_entries(), request_context="x"
        )


def _inventory(
    *,
    entries: list[DataSourceEntry] | None = None,
    producer_id: str = "information_schema_probe_v1",
) -> DataSourceInventory:
    """Build an inventory whose producer matches the default ``_sample_entries`` producer_id."""
    return DataSourceInventory(
        entries=entries if entries is not None else _sample_entries(),
        producers=[
            ProducerMetadata(
                producer_id=producer_id,
                producer_type="curated",
                produced_at=FIXED_TS,
            )
        ],
        created_at=FIXED_TS,
        request_context="subrogation recovery model",
    )


def _entries_with_producer(
    producer_id: str, count: int, *, name_prefix: str = "tbl"
) -> list[DataSourceEntry]:
    return [
        DataSourceEntry(
            name=f"{name_prefix}_{i}",
            namespace="public",
            fully_qualified_name=f"public.{name_prefix}_{i}",
            entity_kind="table",
            producer_id=producer_id,
            relevance_score=float(i) / 100.0,
        )
        for i in range(count)
    ]


class TestSanitizePromptField:
    def test_none_returns_empty(self) -> None:
        assert _sanitize_prompt_field(None) == ""

    def test_strips_control_characters_except_newline_and_tab(self) -> None:
        raw = "line1\n\ttabbed\x00\x01\x07text"
        out = _sanitize_prompt_field(raw)
        assert "\x00" not in out
        assert "\x01" not in out
        assert "\x07" not in out
        assert "\n" in out
        assert "\t" in out
        assert "text" in out

    def test_truncates_beyond_bound(self) -> None:
        raw = "x" * (MAX_INVENTORY_FIELD_CHARS + 500)
        out = _sanitize_prompt_field(raw)
        assert len(out) == MAX_INVENTORY_FIELD_CHARS + 3
        assert out.endswith("...")

    def test_honors_custom_bound(self) -> None:
        out = _sanitize_prompt_field("abcdefghij", max_chars=4)
        assert out == "abcd..."


class TestBuildInventoryBlock:
    def test_none_returns_empty_string(self) -> None:
        assert _build_inventory_block(None) == ""

    def test_empty_entries_returns_empty_string(self) -> None:
        inv = DataSourceInventory(
            entries=[],
            producers=[],
            created_at=FIXED_TS,
        )
        assert _build_inventory_block(inv) == ""

    def test_renders_fully_qualified_names(self) -> None:
        inv = _inventory()
        block = _build_inventory_block(inv)
        assert "Available data sources" in block
        assert "public.claims" in block
        assert "public.policies" in block

    def test_renders_column_previews(self) -> None:
        inv = _inventory()
        block = _build_inventory_block(inv)
        assert "claim_id" in block
        assert "loss_amount" in block

    def test_sorts_by_relevance_score_descending(self) -> None:
        entries = [
            DataSourceEntry(
                name="low",
                fully_qualified_name="public.low",
                entity_kind="table",
                producer_id="information_schema_probe_v1",
                relevance_score=0.1,
            ),
            DataSourceEntry(
                name="high",
                fully_qualified_name="public.high",
                entity_kind="table",
                producer_id="information_schema_probe_v1",
                relevance_score=0.9,
            ),
            DataSourceEntry(
                name="mid",
                fully_qualified_name="public.mid",
                entity_kind="table",
                producer_id="information_schema_probe_v1",
                relevance_score=0.5,
            ),
        ]
        block = _build_inventory_block(_inventory(entries=entries))
        assert block.index("public.high") < block.index("public.mid")
        assert block.index("public.mid") < block.index("public.low")

    def test_none_relevance_score_treated_as_zero(self) -> None:
        entries = [
            DataSourceEntry(
                name="ranked",
                fully_qualified_name="public.ranked",
                entity_kind="table",
                producer_id="information_schema_probe_v1",
                relevance_score=0.5,
            ),
            DataSourceEntry(
                name="unranked",
                fully_qualified_name="public.unranked",
                entity_kind="table",
                producer_id="information_schema_probe_v1",
            ),
        ]
        block = _build_inventory_block(_inventory(entries=entries))
        assert block.index("public.ranked") < block.index("public.unranked")

    def test_truncates_beyond_max_entries(self) -> None:
        over = MAX_INVENTORY_ENTRIES_IN_PROMPT + 5
        entries = _entries_with_producer("information_schema_probe_v1", over)
        block = _build_inventory_block(_inventory(entries=entries))
        assert "and 5 more sources truncated" in block
        # Lowest-ranked (last) entries should be dropped.
        assert "public.tbl_0" not in block
        assert "public.tbl_4" not in block

    def test_exactly_max_entries_no_truncation_note(self) -> None:
        entries = _entries_with_producer(
            "information_schema_probe_v1", MAX_INVENTORY_ENTRIES_IN_PROMPT
        )
        block = _build_inventory_block(_inventory(entries=entries))
        assert "more sources truncated" not in block

    def test_sanitizes_description_and_relevance_reason(self) -> None:
        bad = DataSourceEntry(
            name="evil",
            fully_qualified_name="public.evil",
            entity_kind="table",
            producer_id="information_schema_probe_v1",
            description="clean text\x00with nulls",
            relevance_reason="x" * (MAX_INVENTORY_FIELD_CHARS + 100),
        )
        block = _build_inventory_block(_inventory(entries=[bad]))
        assert "\x00" not in block
        # Truncated relevance_reason ends with ellipsis
        assert block.count("x" * 50) >= 1  # some x's retained
        assert "..." in block

    def test_column_preview_shows_overflow_marker(self) -> None:
        many_cols = [
            ColumnMetadata(name=f"c{i}", data_type="INT") for i in range(12)
        ]
        entry = DataSourceEntry(
            name="wide",
            fully_qualified_name="public.wide",
            entity_kind="table",
            producer_id="information_schema_probe_v1",
            columns=many_cols,
        )
        block = _build_inventory_block(_inventory(entries=[entry]))
        assert "+4 more" in block


class TestGeneratePrimaryQueriesInventoryPrompt:
    def test_inventory_block_present_when_inventory_provided(
        self, request_obj: DataRequest
    ) -> None:
        canned = (
            '[{"name": "q", "sql": "SELECT 1 FROM public.claims", '
            '"purpose": "x", "expected_row_count_order": "tens", '
            '"inventory_entries_used": ["public.claims"]}]'
        )
        fake, msgs = _fake_client([canned])
        client = AnthropicLLMClient(client=fake, model="fake-model")

        client.generate_primary_queries(
            request_obj,
            data_source_inventory=_inventory(),
        )

        user_msg = msgs.calls[0]["messages"][0]["content"]
        assert "Available data sources" in user_msg
        assert "public.claims" in user_msg

    def test_inventory_block_absent_when_inventory_none(
        self, request_obj: DataRequest
    ) -> None:
        canned = (
            '[{"name": "q", "sql": "SELECT 1", "purpose": "x", '
            '"expected_row_count_order": "tens"}]'
        )
        fake, msgs = _fake_client([canned])
        client = AnthropicLLMClient(client=fake, model="fake-model")

        client.generate_primary_queries(request_obj)

        user_msg = msgs.calls[0]["messages"][0]["content"]
        # Block title (not the phrase inside JSON instructions) must be absent.
        assert "Available data sources (prefer" not in user_msg

    def test_inventory_block_absent_when_entries_empty(
        self, request_obj: DataRequest
    ) -> None:
        empty_inv = DataSourceInventory(
            entries=[], producers=[], created_at=FIXED_TS
        )
        canned = (
            '[{"name": "q", "sql": "SELECT 1", "purpose": "x", '
            '"expected_row_count_order": "tens"}]'
        )
        fake, msgs = _fake_client([canned])
        client = AnthropicLLMClient(client=fake, model="fake-model")

        client.generate_primary_queries(
            request_obj, data_source_inventory=empty_inv
        )

        user_msg = msgs.calls[0]["messages"][0]["content"]
        assert "Available data sources (prefer" not in user_msg

    def test_dump_request_strips_inventory(
        self, request_obj: DataRequest
    ) -> None:
        """The raw JSON dump in the prompt must not duplicate the inventory.

        The inventory is rendered by ``_build_inventory_block`` in a
        prompt-friendly shape; duplicating it in ``_dump_request`` would
        waste tokens and risk prompt inconsistency. The ``data_source_inventory``
        key must be absent from the dumped payload even when set on the request.
        """
        request_with_inv = request_obj.model_copy(
            update={"data_source_inventory": _inventory()}
        )
        dumped = _dump_request(request_with_inv)
        assert "data_source_inventory" not in dumped

    def test_parses_inventory_entries_used(
        self, request_obj: DataRequest
    ) -> None:
        canned = (
            '[{"name": "q", "sql": "SELECT * FROM public.claims", '
            '"purpose": "x", "expected_row_count_order": "tens", '
            '"inventory_entries_used": ["public.claims", "public.policies"]}]'
        )
        fake, _ = _fake_client([canned])
        client = AnthropicLLMClient(client=fake, model="fake-model")

        specs = client.generate_primary_queries(
            request_obj, data_source_inventory=_inventory()
        )

        assert specs[0].inventory_entries_used == [
            "public.claims",
            "public.policies",
        ]

    def test_inventory_entries_used_defaults_to_empty_when_absent(
        self, request_obj: DataRequest
    ) -> None:
        """Responses from pre-Phase-3 prompts or clients that omit the new
        ``inventory_entries_used`` key must still parse — defaulting the
        field to ``[]`` preserves backward compatibility.
        """
        canned = (
            '[{"name": "q", "sql": "SELECT 1", "purpose": "x", '
            '"expected_row_count_order": "tens"}]'
        )
        fake, _ = _fake_client([canned])
        client = AnthropicLLMClient(client=fake, model="fake-model")

        specs = client.generate_primary_queries(request_obj)

        assert specs[0].inventory_entries_used == []

    def test_truncation_note_in_prompt_for_large_inventory(
        self, request_obj: DataRequest
    ) -> None:
        canned = (
            '[{"name": "q", "sql": "SELECT 1", "purpose": "x", '
            '"expected_row_count_order": "tens"}]'
        )
        fake, msgs = _fake_client([canned])
        client = AnthropicLLMClient(client=fake, model="fake-model")

        over = MAX_INVENTORY_ENTRIES_IN_PROMPT + 7
        big_inventory = _inventory(
            entries=_entries_with_producer("information_schema_probe_v1", over)
        )
        client.generate_primary_queries(
            request_obj, data_source_inventory=big_inventory
        )

        user_msg = msgs.calls[0]["messages"][0]["content"]
        assert "and 7 more sources truncated" in user_msg
