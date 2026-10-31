"""The ONLY place that talks to the Anthropic API.

Every call is budget-checked, usage-logged and (in live mode) recorded for replay.
Modes:
  live   - real call, recorded to LLM_CACHE_DIR
  replay - serve recorded response; raise ReplayMiss if absent
  mock   - callers must not reach this module (the agent uses the rule-based brain instead)
"""

import hashlib
import json
from collections.abc import AsyncIterator
from typing import Any, TypeVar

import anthropic
from pydantic import BaseModel

from app.config import get_settings
from app.llm import ledger
from app.llm.ledger import BudgetExceeded
from app.llm.pricing import price_for

T = TypeVar("T", bound=BaseModel)

__all__ = ["BudgetExceeded", "LlmUnavailable", "ReplayMiss", "complete_json", "stream_text", "strict_schema"]


class LlmUnavailable(RuntimeError):
    """The model could not produce a usable answer (refusal, API error, mock mode)."""


class ReplayMiss(LlmUnavailable):
    """Replay mode and no recorded response exists for this request."""


_client: anthropic.AsyncAnthropic | None = None


def _get_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        settings = get_settings()
        if not settings.anthropic_api_key:
            raise LlmUnavailable("ANTHROPIC_API_KEY is not set")
        _client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key, max_retries=2, timeout=60)
    return _client


def strict_schema(model: type[BaseModel]) -> dict[str, Any]:
    """Pydantic JSON schema adapted for structured outputs: every property required,
    no additional properties, no titles/defaults."""

    def fix(node: Any) -> Any:
        if isinstance(node, dict):
            node = {k: fix(v) for k, v in node.items() if k not in ("title", "default")}
            if node.get("type") == "object" and "properties" in node:
                node["required"] = list(node["properties"].keys())
                node["additionalProperties"] = False
            return node
        if isinstance(node, list):
            return [fix(v) for v in node]
        return node

    return fix(model.model_json_schema())


def _system_blocks(system: str) -> list[dict[str, Any]]:
    # Frozen system prompt first, cached. Volatile content goes in the user turn.
    return [{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}]


def _request_hash(params: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(params, sort_keys=True, default=str).encode()).hexdigest()


def _cache_path(key: str):
    settings = get_settings()
    settings.llm_cache_dir.mkdir(parents=True, exist_ok=True)
    return settings.llm_cache_dir / f"{key}.json"


def _estimate_cost(model: str, system: str, user: str, max_tokens: int) -> float:
    p = price_for(model)
    est_input = (len(system) + len(user)) / 3.5
    return (est_input * p.input + max_tokens * p.output) / 1_000_000


def _thinking_for(effort: str | None) -> dict[str, Any]:
    # Sonnet 5.5 rejects {"type": "disabled"}; "between_tools" turns thinking off for tool-less calls.
    if effort is None:
        return {"thinking": {"type": "between_tools"}, "output_config": {"effort": "low"}}
    return {"thinking": {"type": "adaptive"}, "output_config": {"effort": effort}}


async def _record_usage(node: str, conversation_id: str | None, model: str, usage: Any) -> None:
    await ledger.record(
        provider="anthropic",
        model=model,
        node=node,
        mode="live",
        conversation_id=conversation_id,
        input_tokens=getattr(usage, "input_tokens", 0) or 0,
        output_tokens=getattr(usage, "output_tokens", 0) or 0,
        cache_write_tokens=getattr(usage, "cache_creation_input_tokens", 0) or 0,
        cache_read_tokens=getattr(usage, "cache_read_input_tokens", 0) or 0,
    )


def _check_mode() -> str:
    mode = get_settings().llm_mode
    if mode == "mock":
        raise LlmUnavailable("LLM_MODE=mock")
    return mode


async def complete_json(
    *,
    node: str,
    system: str,
    user: str,
    schema: type[T],
    max_tokens: int,
    conversation_id: str | None = None,
    effort: str | None = None,
) -> T:
    """Single structured-output call. `effort=None` disables thinking (cheapest)."""
    mode = _check_mode()
    settings = get_settings()
    model = settings.claude_model
    params: dict[str, Any] = {
        "model": model,
        "max_tokens": max_tokens,
        "system": _system_blocks(system),
        "messages": [{"role": "user", "content": user}],
        **_thinking_for(effort),
    }
    params["output_config"] = {
        **params["output_config"],
        "format": {"type": "json_schema", "schema": strict_schema(schema)},
    }
    key = _request_hash(params)
    path = _cache_path(key)

    if path.exists():
        return schema.model_validate_json(json.loads(path.read_text())["text"])
    if mode == "replay":
        raise ReplayMiss(f"no recording for {node} ({key[:12]})")

    await ledger.check_caps("anthropic", _estimate_cost(model, system, user, max_tokens), conversation_id)
    try:
        response = await _get_client().messages.create(**params)
    except anthropic.APIError as e:
        raise LlmUnavailable(f"Claude API error: {e}") from e
    await _record_usage(node, conversation_id, model, response.usage)

    if response.stop_reason in ("refusal", "max_tokens"):
        raise LlmUnavailable(f"{node}: stop_reason={response.stop_reason}")
    text = next((b.text for b in response.content if b.type == "text"), "")
    parsed = schema.model_validate_json(text)
    path.write_text(json.dumps({"node": node, "text": text}))
    return parsed


async def stream_text(
    *,
    node: str,
    system: str,
    user: str,
    max_tokens: int,
    conversation_id: str | None = None,
) -> AsyncIterator[str]:
    """Streamed plain-text call (customer-facing reply)."""
    mode = _check_mode()
    settings = get_settings()
    model = settings.claude_model
    params: dict[str, Any] = {
        "model": model,
        "max_tokens": max_tokens,
        "system": _system_blocks(system),
        "messages": [{"role": "user", "content": user}],
        **_thinking_for(None),
    }
    key = _request_hash(params)
    path = _cache_path(key)

    if path.exists():
        text = json.loads(path.read_text())["text"]
        for i in range(0, len(text), 24):
            yield text[i : i + 24]
        return
    if mode == "replay":
        raise ReplayMiss(f"no recording for {node} ({key[:12]})")

    await ledger.check_caps("anthropic", _estimate_cost(model, system, user, max_tokens), conversation_id)
    chunks: list[str] = []
    try:
        async with _get_client().messages.stream(**params) as stream:
            async for text in stream.text_stream:
                chunks.append(text)
                yield text
            final = await stream.get_final_message()
    except anthropic.APIError as e:
        raise LlmUnavailable(f"Claude API error: {e}") from e
    await _record_usage(node, conversation_id, model, final.usage)
    if final.stop_reason == "refusal":
        raise LlmUnavailable(f"{node}: refusal")
    path.write_text(json.dumps({"node": node, "text": "".join(chunks)}))
