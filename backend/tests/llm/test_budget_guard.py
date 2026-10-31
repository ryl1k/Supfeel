import pytest
from pydantic import BaseModel, ConfigDict
from sqlalchemy import text

from app.config import get_settings
from app.db.session import session_scope
from app.llm import ledger
from app.llm.client import LlmUnavailable, complete_json, strict_schema
from app.llm.pricing import cost_usd


@pytest.fixture
async def clean_ledger():
    async with session_scope() as s:
        await s.execute(text("TRUNCATE llm_usage"))
    yield


def test_sonnet_pricing():
    # 1M in + 1M out = $2 + $10
    assert cost_usd("claude-sonnet-5-5", 1_000_000, 1_000_000) == pytest.approx(12.0)
    assert cost_usd("claude-sonnet-5-5", cache_read_tokens=1_000_000) == pytest.approx(0.20)


def test_unknown_model_priced_pessimistically():
    assert cost_usd("some-other-model", 1_000_000) > cost_usd("claude-sonnet-5-5", 1_000_000)


def test_strict_schema_requires_all_fields():
    class Inner(BaseModel):
        model_config = ConfigDict(extra="forbid")
        a: int

    class Outer(BaseModel):
        name: str
        note: str | None = None
        inner: Inner

    schema = strict_schema(Outer)
    assert schema["required"] == ["name", "note", "inner"]
    assert schema["additionalProperties"] is False
    assert "title" not in schema


async def test_hard_cap_blocks_calls(clean_ledger):
    cap = get_settings().llm_budget_hard_cap_usd
    await ledger.record(
        provider="anthropic",
        model="claude-sonnet-5-5",
        node="t",
        mode="live",
        output_tokens=int(cap * 100_000) + 1000,
    )
    with pytest.raises(ledger.BudgetExceeded):
        await ledger.check_caps("anthropic", 0.01)


async def test_session_cap(clean_ledger):
    await ledger.record(
        provider="anthropic",
        model="claude-sonnet-5-5",
        node="t",
        mode="live",
        conversation_id="c1",
        output_tokens=60_000,
    )  # $0.60
    with pytest.raises(ledger.BudgetExceeded):
        await ledger.check_caps("anthropic", 0.01, conversation_id="c1")
    await ledger.check_caps("anthropic", 0.01, conversation_id="c2")


async def test_replay_and_mock_usage_not_counted(clean_ledger):
    await ledger.record(
        provider="anthropic", model="claude-sonnet-5-5", node="t", mode="replay", output_tokens=10_000_000
    )
    assert await ledger.total_spend("anthropic") == 0


async def test_mock_mode_never_calls_api():
    class Out(BaseModel):
        x: int

    with pytest.raises(LlmUnavailable):
        await complete_json(node="t", system="s", user="u", schema=Out, max_tokens=10)
