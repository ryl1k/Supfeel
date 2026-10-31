"""Ticket service: persistence around graph runs, streamed as SSE-ready events.

Each turn runs in its own asyncio task feeding a queue, so a long fix run completes (and is recorded) even if
the customer closes the page. Every turn is one trace run under trace_id = ticket id.
"""

import asyncio
import json
import logging
import re
import uuid
from collections.abc import AsyncIterator
from typing import Any

from sqlalchemy import select

from app.accounts import billing
from app.accounts.context import current_account
from app.config import get_settings
from app.db.models import Notification, Repo, Ticket, TicketAction, TicketMessage
from app.db.session import session_scope
from app.obs import trace
from app.support.graph import GRAPH
from app.support.learn import LEARNABLE, learn
from app.support.notify import notify

log = logging.getLogger(__name__)
# Approving a write must be explicit; "thanks"/"great" only close an answered ticket.
APPROVE = re.compile(
    r"^\s*(yes|yep|yeah|sure|ok|okay|go ahead|please do|do it|approve|confirm|sounds good)\b[\s.!]*(please)?[\s.!]*$",
    re.I,
)
SATISFIED = re.compile(
    r"^\s*(yes|yep|yeah|ok|okay|thanks|thank you|perfect|great|that helps|got it|makes sense)\b", re.I
)
NO = re.compile(r"^\s*(no|nope|don't|do not|stop|decline|not now|that doesn'?t help|still)\b", re.I)
HEDGE = re.compile(r"\b(but|don'?t|do not|wait|instead|actually|not)\b", re.I)
MAX_STEPS = 14
_tasks: set[asyncio.Task] = set()


class TicketError(ValueError):
    pass


def _jsonable(x: Any) -> Any:
    return json.loads(json.dumps(x, default=str))


def new_ticket_id() -> str:
    return "T-" + uuid.uuid4().hex[:6].upper()


async def _messages(ticket_id: str) -> list[dict[str, str]]:
    async with session_scope() as s:
        rows = (
            await s.scalars(
                select(TicketMessage).where(TicketMessage.ticket_id == ticket_id).order_by(TicketMessage.id)
            )
        ).all()
    return [{"role": m.role, "content": m.content, "created_at": m.created_at.isoformat()} for m in rows]


async def _add_message(ticket_id: str, role: str, content: str) -> None:
    async with session_scope() as s:
        s.add(TicketMessage(ticket_id=ticket_id, role=role, content=content))


def _history(messages: list[dict[str, str]]) -> list[dict[str, str]]:
    keep = ("customer", "agent", "frontline")
    return [{"role": m["role"], "content": m["content"]} for m in messages if m["role"] in keep][-12:]


async def learn_ticket(ticket_id: str) -> bool:
    try:
        return await learn(ticket_id, await _messages(ticket_id))
    except Exception:  # learning is best effort
        log.exception("learning failed for %s", ticket_id)
        return False


# ----------------------------------------------------------------------------------------- running


async def _drive(ticket: Ticket, initial: dict[str, Any], queue: asyncio.Queue) -> None:
    final: dict[str, Any] = {}
    current_account.set(initial.get("account_id"))  # bill this turn's AI spend to the workspace
    try:
        async with trace.span(
            f"ticket turn ({initial['mode']})",
            kind="run",
            trace_id=ticket.id,
            message=initial.get("message", "")[:500],
        ):
            async for mode, chunk in GRAPH.astream(
                initial, stream_mode=["custom", "values"], config={"recursion_limit": MAX_STEPS}
            ):
                if mode == "custom":
                    await queue.put(chunk)
                else:
                    final = chunk
        summary = await _finish(ticket, final)
        await queue.put({"event": "done", "data": summary})
    except Exception:
        log.exception("ticket turn failed for %s", ticket.id)
        await queue.put(
            {
                "event": "error",
                "data": {
                    "code": "internal",
                    "message": "Something went wrong on our side. A teammate has been notified.",
                },
            }
        )
        try:
            await notify(
                ticket.repo_id,
                "escalation",
                f"Ticket {ticket.id} crashed",
                "The agent hit an internal error; please handle manually.",
                ticket_id=ticket.id,
            )
        except Exception:
            log.exception("could not notify about crash")
    finally:
        await queue.put(None)


async def _stream(ticket: Ticket, initial: dict[str, Any]) -> AsyncIterator[dict[str, Any]]:
    queue: asyncio.Queue = asyncio.Queue()
    task = asyncio.create_task(_drive(ticket, initial, queue))
    _tasks.add(task)
    task.add_done_callback(_tasks.discard)
    while (ev := await queue.get()) is not None:
        yield ev


async def _finish(ticket: Ticket, final: dict[str, Any]) -> dict[str, Any]:
    status = final.get("status") or "open"
    t = final.get("triage") or {}
    async with session_scope() as s:
        row = await s.get(Ticket, ticket.id)
        if t:
            row.category = t.get("category")
            row.confidence = t.get("confidence")
            row.triage = _jsonable({**t, "route": final.get("route"), "brain": final.get("brain")})
            if not row.subject:
                row.subject = (final.get("subject") or t.get("subject") or "")[:200]
        if final.get("fix"):
            row.fix = _jsonable(final["fix"])
        if final.get("resolution"):
            row.resolution = _jsonable(final["resolution"])
        action = final.get("action")
        row.state = _jsonable(
            {"pending_action": action} if status == "awaiting_confirmation" and action else {}
        )
        row.status = status
    if final.get("reply"):
        await _add_message(ticket.id, "agent", final["reply"])
    if status in LEARNABLE and status not in ("fix_in_review",):
        await learn_ticket(ticket.id)
    return {
        "ticket_id": ticket.id,
        "status": status,
        "category": t.get("category"),
        "route": final.get("route"),
        "brain": final.get("brain"),
    }


async def _load(ticket_id: str) -> Ticket:
    async with session_scope() as s:
        t = await s.get(Ticket, ticket_id)
        if t is None:
            raise TicketError("unknown ticket")
        s.expunge(t)
        return t


async def _business(repo_id: str) -> tuple[str, str | None]:
    """(business display name, owning account id)."""
    async with session_scope() as s:
        r = await s.get(Repo, repo_id)
        if r is None:
            raise TicketError("unknown product")
        if r.status not in ("ready", "indexing") or not r.indexed_at:
            raise TicketError("this product is still being set up; try again in a minute")
        return (r.settings or {}).get("business_name") or r.full_name.split("/")[-1], r.account_id


def _initial(
    t: Ticket, business: tuple[str, str | None], message: str, history: list[dict[str, str]]
) -> dict[str, Any]:
    return {
        "ticket_id": t.id, "repo_id": t.repo_id, "business": business[0], "account_id": business[1],
        "customer": t.customer or {}, "mode": "message", "message": message, "history": history, "brain": {},
        "notes": [], "handoff": (t.meta or {}).get("handoff"),
    }  # fmt: skip


async def open_ticket(
    repo_id: str,
    customer: dict[str, Any],
    message: str,
    *,
    channel: str = "web",
    meta: dict[str, Any] | None = None,
) -> tuple[Ticket, tuple[str, str | None]]:
    """Create and bill a ticket; the turn itself is started by the caller."""
    message = message.strip()[:4000]
    business = await _business(repo_id)
    t = Ticket(id=new_ticket_id(), repo_id=repo_id, customer=_jsonable(customer), status="open", channel=channel,
               meta=_jsonable(meta or {}))  # fmt: skip
    try:
        await billing.charge(
            business[1], "ticket", repo_id=repo_id, ref=t.id, note=f"Ticket {t.id} ({channel})"
        )
    except billing.PaymentRequired as e:
        raise TicketError(str(e)) from e
    async with session_scope() as s:
        s.add(t)
    for m in ((meta or {}).get("handoff") or {}).get("transcript") or []:
        role = "customer" if m.get("role") in ("customer", "user") else "frontline"
        await _add_message(t.id, role, str(m.get("content", ""))[:4000])
    await _add_message(t.id, "customer", message)
    return t, business


async def create_ticket(
    repo_id: str,
    customer: dict[str, Any],
    message: str,
    *,
    channel: str = "web",
    meta: dict[str, Any] | None = None,
) -> AsyncIterator[dict[str, Any]]:
    t, business = await open_ticket(repo_id, customer, message, channel=channel, meta=meta)
    message = message.strip()[:4000]
    yield {"event": "ticket", "data": {"ticket_id": t.id}}
    history = _history(await _messages(t.id))[:-1]  # the first-line agent's transcript, if any
    async for ev in _stream(t, _initial(t, business, message, history)):
        yield ev


async def post_message(ticket_id: str, message: str) -> AsyncIterator[dict[str, Any]]:
    message = message.strip()[:4000]
    t = await _load(ticket_id)
    business = await _business(t.repo_id)
    history = _history(await _messages(ticket_id))
    await _add_message(ticket_id, "customer", message)
    yield {"event": "ticket", "data": {"ticket_id": t.id}}

    if t.status == "awaiting_confirmation" and (
        APPROVE.match(message) or (NO.match(message) and len(message) < 40)
    ):
        async for ev in _confirm(t, business, bool(APPROVE.match(message)), history):
            yield ev
        return
    if t.status == "answered" and SATISFIED.match(message) and not HEDGE.search(message):
        async for ev in _close_answered(t, resolved=True):
            yield ev
        return
    if t.status == "answered" and NO.match(message) and len(message) < 40:
        async for ev in _close_answered(t, resolved=False):
            yield ev
        return
    pending = (t.state or {}).get("pending_action")
    if pending:  # a new message supersedes the proposal
        async with session_scope() as s:
            row = await s.get(TicketAction, pending["id"])
            if row and row.status == "proposed":
                row.status = "declined"
    async for ev in _stream(t, _initial(t, business, message, history)):
        yield ev


async def confirm(ticket_id: str, approved: bool) -> AsyncIterator[dict[str, Any]]:
    t = await _load(ticket_id)
    if t.status != "awaiting_confirmation":
        yield {
            "event": "error",
            "data": {"code": "nothing_pending", "message": "There is nothing waiting for confirmation."},
        }
        return
    business = await _business(t.repo_id)
    history = _history(await _messages(ticket_id))
    await _add_message(ticket_id, "customer", "Yes, go ahead." if approved else "No, don't do that.")
    async for ev in _confirm(t, business, approved, history):
        yield ev


async def _confirm(
    t: Ticket, business: str, approved: bool, history: list[dict[str, str]]
) -> AsyncIterator[dict[str, Any]]:
    initial = {**_initial(t, business, "Yes, go ahead." if approved else "No, don't do that.", history),
               "mode": "confirm", "approved": approved, "action": (t.state or {}).get("pending_action"), "route": "act",
               "triage": t.triage or {}}  # fmt: skip
    async for ev in _stream(t, initial):
        yield ev


async def _close_answered(t: Ticket, resolved: bool) -> AsyncIterator[dict[str, Any]]:
    async with trace.span("customer feedback", kind="run", trace_id=t.id, resolved=resolved):
        if resolved:
            reply, status = "Glad that helped! I'll close this ticket. Reach out anytime.", "resolved"
        else:
            reply, status = (
                "Sorry that didn't solve it. I've passed your ticket to a teammate, who will follow up shortly.",
                "escalated",
            )
            await notify(
                t.repo_id, "escalation", f"Explanation didn't help on {t.id}", t.subject, ticket_id=t.id
            )
        async with session_scope() as s:
            row = await s.get(Ticket, t.id)
            row.status = status
            row.resolution = {**(row.resolution or {}), "customer_confirmed": resolved}
    await _add_message(t.id, "agent", reply)
    yield {"event": "token", "data": {"text": reply}}
    await learn_ticket(t.id)
    yield {"event": "done", "data": {"ticket_id": t.id, "status": status}}


# ----------------------------------------------------------------------------------------- relay view (for agents)

NEXT_STEP = {
    "open": "Send the customer's answer with `reply`.",
    "answered": "Send the reply. If the customer confirms it helped, call `reply` with their message to close the ticket.",
    "awaiting_confirmation": "Ask the customer the confirmation question, then call `confirm` with their decision.",
    "fix_in_review": "A code fix is in review and CI is verifying it. Check back with `get_ticket` (or wait for the callback).",
    "fix_verified": "The fix passed CI and awaits merge by the engineering team. Nothing to do for the customer now.",
    "fix_failed": "The automatic fix failed CI; engineers were notified. Tell the customer the team is on it.",
    "reported": "The bug was reported to engineering. Share the reply; nothing else to do.",
    "resolved": "Resolved. Nothing else to do.",
    "escalated": "A human teammate was notified and will follow up.",
}


async def relay(ticket_id: str) -> dict[str, Any]:
    """Compact, agent-friendly view: what to tell the customer and what to do next."""
    t = await _load(ticket_id)
    msgs = await _messages(ticket_id)
    reply = next((m["content"] for m in reversed(msgs) if m["role"] == "agent"), "")
    pending = (t.state or {}).get("pending_action")
    fix = t.fix or {}
    out: dict[str, Any] = {
        "ticket_id": t.id,
        "status": t.status,
        "category": t.category,
        "customer_reply": reply,
        "next_step": NEXT_STEP.get(t.status, ""),
        "trace_url": f"{get_settings().public_app_url.rstrip('/')}/app/tickets/{t.id}",
    }
    if pending:
        out["needs_confirmation"] = {
            "question": f"Shall we {pending.get('title', 'do this').rstrip('.')}? (yes/no)",
            "action": pending.get("title"),
            "details": pending.get("args"),
        }
    if fix.get("decision"):
        out["engineering"] = {
            k: fix.get(k) for k in ("decision", "root_cause", "pr_url", "workaround") if fix.get(k)
        }
        if fix.get("ci"):
            out["engineering"]["ci"] = (fix.get("ci") or {}).get("state")
    return out


# ----------------------------------------------------------------------------------------- views


def ticket_summary(t: Ticket) -> dict[str, Any]:
    fix = t.fix or {}
    return {
        "id": t.id, "repo_id": t.repo_id, "subject": t.subject, "category": t.category,
        "confidence": float(t.confidence) if t.confidence is not None else None, "status": t.status,
        "customer": t.customer, "channel": t.channel, "pr_url": fix.get("pr_url"), "ci": (fix.get("ci") or {}).get("state"),
        "learned": t.learned, "created_at": t.created_at.isoformat(), "updated_at": t.updated_at.isoformat(),
    }  # fmt: skip


async def get_ticket(ticket_id: str) -> dict[str, Any]:
    t = await _load(ticket_id)
    async with session_scope() as s:
        actions = (
            await s.scalars(
                select(TicketAction)
                .where(TicketAction.ticket_id == ticket_id)
                .order_by(TicketAction.created_at)
            )
        ).all()
        notes = (
            await s.scalars(
                select(Notification).where(Notification.ticket_id == ticket_id).order_by(Notification.id)
            )
        ).all()
    return {
        **ticket_summary(t),
        "triage": t.triage, "resolution": t.resolution, "fix": t.fix,
        "pending_action": (t.state or {}).get("pending_action"),
        "messages": await _messages(ticket_id),
        "actions": [
            {"id": a.id, "operation_id": a.operation_id, "method": a.method, "path": a.path, "args": a.args, "title": a.title,
             "status": a.status, "response": a.response, "verification": a.verification, "created_at": a.created_at.isoformat()}
            for a in actions
        ],
        "notifications": [notification_view(n) for n in notes],
    }  # fmt: skip


def notification_view(n: Notification) -> dict[str, Any]:
    return {"id": n.id, "repo_id": n.repo_id, "ticket_id": n.ticket_id, "kind": n.kind, "title": n.title, "body": n.body,
            "url": n.url, "delivered": n.delivered, "created_at": n.created_at.isoformat()}  # fmt: skip


async def list_tickets(
    repo_ids: list[str] | None = None, status: str | None = None, limit: int = 100
) -> list[dict[str, Any]]:
    """`repo_ids=None` lists every repository (operator)."""
    stmt = select(Ticket).order_by(Ticket.created_at.desc()).limit(limit)
    if repo_ids is not None:
        stmt = stmt.where(Ticket.repo_id.in_(repo_ids))
    if status:
        stmt = stmt.where(Ticket.status == status)
    async with session_scope() as s:
        return [ticket_summary(t) for t in (await s.scalars(stmt)).all()]


async def list_notifications(repo_ids: list[str] | None = None, limit: int = 100) -> list[dict[str, Any]]:
    stmt = select(Notification).order_by(Notification.id.desc()).limit(limit)
    if repo_ids is not None:
        stmt = stmt.where(Notification.repo_id.in_(repo_ids))
    async with session_scope() as s:
        return [notification_view(n) for n in (await s.scalars(stmt)).all()]
