"""Unit tests for :class:`AnthropicLLMClient`.

These tests mock the anthropic SDK at the client boundary so no network or
API key is required. The goal is to verify the protocol methods correctly
build prompts, parse JSON responses, and propagate malformed responses as
:class:`LLMParseError`. The prompt text itself is not asserted against —
only the structure of the parsed output.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest
from anthropic.types import TextBlock
from model_project_constructor_data_agent.anthropic_client import (
    AnthropicLLMClient,
    LLMParseError,
    _extract_json,
)
from model_project_constructor_data_agent.llm import (
    LLMClient,
    PrimaryQuerySpec,
)
from model_project_constructor_data_agent.schemas import (
    DataGranularity,
    DataRequest,
)


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
