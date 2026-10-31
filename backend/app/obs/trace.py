"""Lightweight tracing: nested spans stored in Postgres (table `spans`).

    async with trace.span("ticket", kind="run", trace_id=ticket_id):
        async with trace.span("triage", kind="step") as sp:
            sp.set(category="bug")

Spans nest through a ContextVar, so LLM calls, embeddings, tool calls and HTTP requests made anywhere below a
run automatically attach to it. Outside a run (no trace_id anywhere up the stack) spans are no-ops.
LLM/embedding cost is attached by the usage ledger (`annotate_usage`).
"""

import logging
import time
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import select

from app.db.models import Span
from app.db.session import session_scope

log = logging.getLogger(__name__)
MAX_ATTR_CHARS = 4000


@dataclass
class SpanCtx:
    id: str
    trace_id: str
    parent_id: str | None
    name: str
    kind: str
    attributes: dict[str, Any] = field(default_factory=dict)
    cost_usd: float = 0.0
    status: str = "ok"
    started: datetime = field(default_factory=lambda: datetime.now(UTC))
    t0: float = field(default_factory=time.perf_counter)

    def set(self, **attrs: Any) -> None:
        for k, v in attrs.items():
            self.attributes[k] = _clip(v)

    def add_cost(self, usd: float) -> None:
        self.cost_usd += usd


class _NullSpan:
    id = None
    trace_id = None

    def set(self, **attrs: Any) -> None:
        pass

    def add_cost(self, usd: float) -> None:
        pass


NULL_SPAN = _NullSpan()
_current: ContextVar[SpanCtx | None] = ContextVar("supfeel_span", default=None)


def _clip(v: Any) -> Any:
    if isinstance(v, str):
        return v if len(v) <= MAX_ATTR_CHARS else v[:MAX_ATTR_CHARS] + "…"
    if isinstance(v, list):
        return [_clip(x) for x in v[:50]]
    if isinstance(v, dict):
        return {str(k): _clip(x) for k, x in list(v.items())[:50]}
    if isinstance(v, (int, float, bool)) or v is None:
        return v
    return _clip(str(v))  # str() result is handled by the first branch


def current() -> SpanCtx | None:
    return _current.get()


def current_trace_id() -> str | None:
    sp = _current.get()
    return sp.trace_id if sp else None


@asynccontextmanager
async def span(
    name: str, kind: str = "step", *, trace_id: str | None = None, **attrs: Any
) -> AsyncIterator[SpanCtx | _NullSpan]:
    parent = _current.get()
    tid = trace_id or (parent.trace_id if parent else None)
    if tid is None:
        yield NULL_SPAN
        return
    sp = SpanCtx(
        id=uuid.uuid4().hex,
        trace_id=tid,
        parent_id=parent.id if parent and parent.trace_id == tid else None,
        name=name[:120],
        kind=kind,
    )
    sp.set(**attrs)
    token = _current.set(sp)
    try:
        yield sp
    except BaseException as e:
        sp.status = "error"
        sp.set(error=f"{type(e).__name__}: {e}")
        raise
    finally:
        _current.reset(token)
        await _persist(sp)


async def _persist(sp: SpanCtx) -> None:
    elapsed = time.perf_counter() - sp.t0
    try:
        async with session_scope() as s:
            s.add(
                Span(
                    id=sp.id,
                    trace_id=sp.trace_id,
                    parent_id=sp.parent_id,
                    name=sp.name,
                    kind=sp.kind,
                    status=sp.status,
                    attributes=sp.attributes,
                    cost_usd=Decimal(str(round(sp.cost_usd, 6))),
                    started_at=sp.started,
                    ended_at=sp.started + timedelta(seconds=elapsed),
                    duration_ms=int(elapsed * 1000),
                )
            )
    except Exception:  # tracing must never break the request
        log.exception("failed to persist span %s", sp.name)


async def record_span(
    name: str, kind: str, *, started: datetime, duration_s: float, cost_usd: float = 0.0, **attrs: Any
) -> None:
    """Record a finished child span without making it current (for async generators, where a ContextVar
    must not be held across yields)."""
    parent = _current.get()
    if parent is None:
        return
    sp = SpanCtx(
        id=uuid.uuid4().hex, trace_id=parent.trace_id, parent_id=parent.id, name=name[:120], kind=kind
    )
    sp.started, sp.cost_usd = started, cost_usd
    sp.t0 = time.perf_counter() - duration_s
    sp.set(**attrs)
    await _persist(sp)


def annotate_usage(cost: float, **tokens: int) -> None:
    """Called by the usage ledger: attach spend and token counts to the innermost span."""
    sp = _current.get()
    if sp is None:
        return
    sp.add_cost(cost)
    for k, v in tokens.items():
        sp.attributes[k] = int(sp.attributes.get(k, 0)) + int(v)


async def load_trace(trace_id: str) -> dict[str, Any]:
    """Spans of one trace as a tree-friendly list plus roll-ups (total cost, tokens, durations by kind)."""
    async with session_scope() as s:
        rows = (
            await s.scalars(select(Span).where(Span.trace_id == trace_id).order_by(Span.started_at))
        ).all()
    spans = [
        {
            "id": r.id,
            "parent_id": r.parent_id,
            "name": r.name,
            "kind": r.kind,
            "status": r.status,
            "attributes": r.attributes,
            "cost_usd": float(r.cost_usd),
            "started_at": r.started_at.isoformat(),
            "ended_at": r.ended_at.isoformat() if r.ended_at else None,
            "duration_ms": r.duration_ms,
        }
        for r in rows
    ]
    by_kind: dict[str, dict[str, float]] = {}
    for sp in spans:
        k = by_kind.setdefault(sp["kind"], {"count": 0, "duration_ms": 0, "cost_usd": 0.0})
        k["count"] += 1
        k["duration_ms"] += sp["duration_ms"]
        k["cost_usd"] = round(k["cost_usd"] + sp["cost_usd"], 6)
    tokens = {
        key: sum(int(sp["attributes"].get(key, 0) or 0) for sp in spans)
        for key in ("input_tokens", "output_tokens", "cache_read_tokens", "cache_write_tokens")
    }
    return {
        "trace_id": trace_id,
        "spans": spans,
        "summary": {
            "spans": len(spans),
            "cost_usd": round(sum(sp["cost_usd"] for sp in spans), 6),
            "duration_ms": max((sp["duration_ms"] for sp in spans if sp["parent_id"] is None), default=0),
            "errors": sum(sp["status"] == "error" for sp in spans),
            "by_kind": by_kind,
            "tokens": tokens,
        },
    }
