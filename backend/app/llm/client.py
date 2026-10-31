"""The ONLY place that talks to the Anthropic API.

Every call is budget-checked, usage-logged and (in live mode) recorded for replay.
Modes:
  live   - real call, recorded to LLM_CACHE_DIR
  replay - serve recorded response; raise ReplayMiss if absent
  mock   - callers must not reach this module (the agent uses the rule-based brain instead)
"""

import hashlib
import json
import time
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any, TypeVar

import anthropic
from pydantic import BaseModel

from app.config import get_settings
from app.llm import ledger
from app.llm.ledger import BudgetExceeded
from app.llm.pricing import price_for
from app.obs import trace

T = TypeVar("T", bound=BaseModel)

__all__ = [
    "BudgetExceeded",
    "LlmUnavailable",
    "ReplayMiss",
    "complete_json",
    "complete_text",
    "stream_text",
    "strict_schema",
    "tool_turn",
]


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


async def _record_usage(
    node: str, conversation_id: str | None, model: str, usage: Any, annotate: bool = True
) -> float:
    return await ledger.record(
        provider="anthropic",
        model=model,
        node=node,
        mode="live",
        conversation_id=conversation_id,
        input_tokens=getattr(usage, "input_tokens", 0) or 0,
        output_tokens=getattr(usage, "output_tokens", 0) or 0,
        cache_write_tokens=getattr(usage, "cache_creation_input_tokens", 0) or 0,
        cache_read_tokens=getattr(usage, "cache_read_input_tokens", 0) or 0,
        annotate=annotate,
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
    session_cap: float | None = None,
) -> T:
    """Single structured-output call. `effort=None` disables thinking (cheapest)."""
    async with trace.span(f"claude.{node}", kind="llm", node=node) as sp:
        result = await _complete_json(
            sp, node, system, user, schema, max_tokens, conversation_id, effort, session_cap
        )
        sp.set(output=result.model_dump_json()[:2000])
        return result


async def _complete_json(
    sp: Any,
    node: str,
    system: str,
    user: str,
    schema: type[T],
    max_tokens: int,
    conversation_id: str | None,
    effort: str | None,
    session_cap: float | None,
) -> T:
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
    sp.set(model=model, input_preview=user[:1500])

    if path.exists():
        sp.set(cached=True)
        return schema.model_validate_json(json.loads(path.read_text())["text"])
    if mode == "replay":
        raise ReplayMiss(f"no recording for {node} ({key[:12]})")

    await ledger.check_caps(
        "anthropic", _estimate_cost(model, system, user, max_tokens), conversation_id, session_cap
    )
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
    session_cap: float | None = None,
) -> AsyncIterator[str]:
    """Streamed plain-text call (customer-facing reply)."""
    mode = _check_mode()
    started, t0 = datetime.now(UTC), time.perf_counter()
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
        await trace.record_span(
            f"claude.{node}", "llm", started=started, duration_s=time.perf_counter() - t0,
            node=node, model=model, cached=True, output=text[:2000],
        )  # fmt: skip
        return
    if mode == "replay":
        raise ReplayMiss(f"no recording for {node} ({key[:12]})")

    await ledger.check_caps(
        "anthropic", _estimate_cost(model, system, user, max_tokens), conversation_id, session_cap
    )
    chunks: list[str] = []
    try:
        async with _get_client().messages.stream(**params) as stream:
            async for text in stream.text_stream:
                chunks.append(text)
                yield text
            final = await stream.get_final_message()
    except anthropic.APIError as e:
        raise LlmUnavailable(f"Claude API error: {e}") from e
    cost = await _record_usage(node, conversation_id, model, final.usage, annotate=False)
    u = final.usage
    await trace.record_span(
        f"claude.{node}", "llm", started=started, duration_s=time.perf_counter() - t0, cost_usd=cost,
        node=node, model=model, input_preview=user[:1500], output="".join(chunks)[:2000],
        input_tokens=u.input_tokens, output_tokens=u.output_tokens,
        cache_read_tokens=u.cache_read_input_tokens or 0, cache_write_tokens=u.cache_creation_input_tokens or 0,
    )  # fmt: skip
    if final.stop_reason == "refusal":
        raise LlmUnavailable(f"{node}: refusal")
    path.write_text(json.dumps({"node": node, "text": "".join(chunks)}))


async def complete_text(
    *,
    node: str,
    system: str,
    user: str,
    max_tokens: int,
    conversation_id: str | None = None,
    session_cap: float | None = None,
) -> str:
    """Non-streamed plain text (summaries, notifications)."""
    parts = [
        t
        async for t in stream_text(
            node=node,
            system=system,
            user=user,
            max_tokens=max_tokens,
            conversation_id=conversation_id,
            session_cap=session_cap,
        )
    ]
    return "".join(parts)


def _block_dict(block: Any) -> dict[str, Any]:
    return block.model_dump(mode="json", exclude_none=True)


async def tool_turn(
    *,
    node: str,
    system: str,
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]],
    max_tokens: int,
    conversation_id: str | None = None,
    session_cap: float | None = None,
    effort: str = "low",
) -> dict[str, Any]:
    """One turn of a manual tool-use loop. Returns {"content": [block dicts], "stop_reason": str}.

    The caller appends `content` as the assistant turn (thinking blocks included, unmodified) and the
    tool results as the next user turn. The frozen system prompt + tools are cached explicitly; the growing
    conversation tail is cached with top-level automatic caching.
    """
    mode = _check_mode()
    model = get_settings().claude_model
    params: dict[str, Any] = {
        "model": model,
        "max_tokens": max_tokens,
        "system": _system_blocks(system),
        "tools": tools,
        "messages": messages,
        "cache_control": {"type": "ephemeral"},
        "thinking": {"type": "adaptive"},
        "output_config": {"effort": effort},
    }
    key = _request_hash(params)
    path = _cache_path(key)
    async with trace.span(f"claude.{node}", kind="llm", node=node, model=model, turn=len(messages)) as sp:
        if path.exists():
            sp.set(cached=True)
            return json.loads(path.read_text())["response"]
        if mode == "replay":
            raise ReplayMiss(f"no recording for {node} ({key[:12]})")
        transcript = json.dumps(messages, default=str)
        await ledger.check_caps(
            "anthropic", _estimate_cost(model, system, transcript, max_tokens), conversation_id, session_cap
        )
        try:
            response = await _get_client().messages.create(**params)
        except anthropic.APIError as e:
            raise LlmUnavailable(f"Claude API error: {e}") from e
        await _record_usage(node, conversation_id, model, response.usage)
        out = {"content": [_block_dict(b) for b in response.content], "stop_reason": response.stop_reason}
        sp.set(
            stop_reason=response.stop_reason,
            tool_calls=[b["name"] for b in out["content"] if b.get("type") == "tool_use"],
            text=" ".join(b.get("text", "") for b in out["content"] if b.get("type") == "text")[:1500],
        )
        if response.stop_reason == "refusal":
            raise LlmUnavailable(f"{node}: refusal")
        path.write_text(json.dumps({"node": node, "response": out}))
        return out
