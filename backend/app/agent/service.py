"""Conversation service: persistence around one graph run, yielding SSE-ready events."""

import json
import re
from collections.abc import AsyncIterator
from typing import Any

from sqlalchemy import select

from app.agent.graph import GRAPH
from app.db.models import Conversation, Customer, Message
from app.db.session import session_scope
from app.tools import registry

YES = re.compile(
    r"^\s*(yes|yep|yeah|sure|ok|okay|go ahead|please do|do it|approve|confirm|sounds good)\b", re.I
)
NO = re.compile(r"^\s*(no|nope|don't|do not|cancel that|stop|decline|not now)\b", re.I)
MAX_STEPS = 12  # graph recursion limit; a full turn uses at most 7 nodes


class ConversationError(ValueError):
    pass


def _jsonable(x: Any) -> Any:
    return json.loads(json.dumps(x, default=str))


async def _load_or_create(conversation_id: str, customer_id: str | None) -> Conversation:
    async with session_scope() as s:
        conv = await s.get(Conversation, conversation_id)
        if conv is None:
            if not customer_id or await s.get(Customer, customer_id) is None:
                raise ConversationError("unknown customer")
            conv = Conversation(id=conversation_id, customer_id=customer_id, status="open", state={})
            s.add(conv)
        elif customer_id and conv.customer_id != customer_id:
            raise ConversationError("conversation belongs to another customer")
        await s.flush()
        s.expunge(conv)
        return conv


async def _history(conversation_id: str) -> list[dict[str, str]]:
    async with session_scope() as s:
        msgs = (
            await s.scalars(
                select(Message).where(Message.conversation_id == conversation_id).order_by(Message.id)
            )
        ).all()
    return [{"role": m.role, "content": m.content} for m in msgs][-10:]


async def _save_message(conversation_id: str, role: str, content: str) -> None:
    async with session_scope() as s:
        s.add(Message(conversation_id=conversation_id, role=role, content=content))


async def _run(initial: dict[str, Any]) -> AsyncIterator[dict[str, Any]]:
    final: dict[str, Any] = {}
    async for mode, chunk in GRAPH.astream(
        initial, stream_mode=["custom", "values"], config={"recursion_limit": MAX_STEPS}
    ):
        if mode == "custom":
            yield chunk
        else:
            final = chunk
    yield {"event": "_final", "data": final}


async def _finish_turn(conv: Conversation, final: dict[str, Any]) -> dict[str, Any]:
    outcome = final.get("outcome") or "answered"
    intent = final.get("intent") or {}
    plan = final.get("plan") or {}
    previous = dict((conv.state or {}).get("previous") or {})
    pause_offered = previous.get("pause_offered", False) or (
        intent.get("intent") == "cancel_membership" and plan.get("decision") == "ask"
    )
    state: dict[str, Any] = {
        "previous": {
            "intent": intent,
            "outcome": outcome,
            "pause_offered": pause_offered,
            "last_message": final.get("user_message", ""),
        }
    }
    if outcome == "awaiting_confirmation":
        state["pending"] = {
            k: final.get(k)
            for k in ("intent", "facts", "policies", "plan", "actions", "user_message", "brain")
        }
    status = {
        "awaiting_confirmation": "awaiting_confirmation",
        "resolved": "resolved",
        "escalated": "escalated",
        "partially_resolved": "escalated",
    }.get(outcome, "open")
    async with session_scope() as s:
        c = await s.get(Conversation, conv.id)
        c.state = _jsonable(state)
        c.status = status
    if final.get("reply"):
        await _save_message(conv.id, "assistant", final["reply"])
    return {"outcome": outcome, "status": status, "brain": final.get("brain")}


async def handle_message(
    conversation_id: str, customer_id: str, message: str
) -> AsyncIterator[dict[str, Any]]:
    message = message.strip()[:2000]
    conv = await _load_or_create(conversation_id, customer_id)

    # A typed yes/no while a confirmation card is open counts as the decision.
    if conv.status == "awaiting_confirmation" and (YES.match(message) or NO.match(message)):
        await _save_message(conv.id, "user", message)
        async for ev in _confirm(conv, approved=bool(YES.match(message))):
            yield ev
        return

    # Any other message supersedes a pending proposal.
    pending = (conv.state or {}).get("pending")
    if pending:
        for a in pending.get("actions") or []:
            if a.get("status") == "proposed" and a.get("action_id"):
                await registry.set_status(a["action_id"], "declined")

    history = await _history(conv.id)
    await _save_message(conv.id, "user", message)
    initial = {
        "conversation_id": conv.id,
        "customer_id": conv.customer_id,
        "mode": "message",
        "user_message": message,
        "history": history,
        "previous": (conv.state or {}).get("previous") or {},
    }
    final: dict[str, Any] = {}
    async for ev in _run(initial):
        if ev["event"] == "_final":
            final = ev["data"]
        else:
            yield ev
    yield {"event": "done", "data": await _finish_turn(conv, final)}


async def handle_confirm(conversation_id: str, approved: bool) -> AsyncIterator[dict[str, Any]]:
    conv = await _load_or_create(conversation_id, None)
    if conv.status != "awaiting_confirmation":
        yield {
            "event": "error",
            "data": {"code": "nothing_pending", "message": "There is nothing waiting for confirmation."},
        }
        return
    await _save_message(conv.id, "user", "Yes, go ahead." if approved else "No, don't do that.")
    async for ev in _confirm(conv, approved):
        yield ev


async def _confirm(conv: Conversation, approved: bool) -> AsyncIterator[dict[str, Any]]:
    pending = (conv.state or {}).get("pending") or {}
    initial = {
        "conversation_id": conv.id,
        "customer_id": conv.customer_id,
        "mode": "confirm",
        "approved": approved,
        "history": await _history(conv.id),
        "previous": (conv.state or {}).get("previous") or {},
        **{k: v for k, v in pending.items() if v is not None},
    }
    initial["user_message"] = "Yes, go ahead." if approved else "No, don't do that."
    final: dict[str, Any] = {}
    async for ev in _run(initial):
        if ev["event"] == "_final":
            final = ev["data"]
        else:
            yield ev
    yield {"event": "done", "data": await _finish_turn(conv, final)}


async def transcript(conversation_id: str) -> dict[str, Any]:
    async with session_scope() as s:
        conv = await s.get(Conversation, conversation_id)
        if conv is None:
            raise ConversationError("unknown conversation")
        status, customer_id = conv.status, conv.customer_id
    return {
        "conversation_id": conversation_id,
        "customer_id": customer_id,
        "status": status,
        "messages": await _history(conversation_id),
    }
