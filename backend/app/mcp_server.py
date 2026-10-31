"""Supfeel as an MCP server: the main entry point for agents.

A business's first-line support agent (their chatbot, Claude, Cursor, any MCP client) connects with a per-repository
key (`Authorization: Bearer sf_live_…`) and escalates what it can't solve. Supfeel explains, acts through the
business API (after the customer confirms) or fixes the bug with a CI-verified pull request, and returns a
relay-ready result: what to tell the customer and what to do next.

Mounted at /mcp (streamable HTTP, stateless). See docs/features/mcp-server/.
"""

import asyncio
import logging
from typing import Annotated, Any

from mcp.server.mcpserver import Context, MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.accounts import billing
from app.accounts.auth import KeyContext, resolve_key
from app.db.models import ApiOperation, Repo, RepoDoc, Ticket
from app.db.session import session_scope
from app.repos.ask import ask
from app.support import service

log = logging.getLogger(__name__)
_background: set[asyncio.Task] = set()

INSTRUCTIONS = """Supfeel is a tier-2 support agent that has read this product's source code, docs and API.
Use it when you (the first-line agent) can't resolve a customer's problem:
- `ask_product` first for quick factual questions about how the product works (cheap).
- `escalate` when the customer is stuck: a possible bug, something they can't do themselves, or an answer you
  couldn't give. Pass the conversation so far and what you already tried. Supfeel investigates the code, then
  explains, performs the action through the business API (after the customer confirms), or fixes the bug with a
  pull request verified by CI.
- Always send `customer_reply` to the customer as-is, and follow `next_step`.
- If the result has `needs_confirmation`, ask the customer that question and call `confirm` with their answer.
  Never confirm on the customer's behalf.
- Continue a ticket with `reply`; check long-running fixes with `get_ticket`."""

mcp = MCPServer(
    name="Supfeel",
    title="Supfeel: tier-2 support that reads your code",
    instructions=INSTRUCTIONS,
    website_url="https://github.com/ryl1k/Supfeel",
)


# ----------------------------------------------------------------------------------------- auth


async def _key(ctx: Context) -> KeyContext:
    headers = ctx.headers or {}
    auth = headers.get("authorization") or headers.get("Authorization") or ""
    raw = auth[7:].strip() if auth.lower().startswith("bearer ") else headers.get("x-api-key", "")
    key = await resolve_key(raw) if raw else None
    if key is None:
        raise ToolError("Missing or invalid Supfeel key. Create one in the workspace: repository → Connect.")
    return key


async def _owned_ticket(key: KeyContext, ticket_id: str) -> Ticket:
    async with session_scope() as s:
        t = await s.get(Ticket, ticket_id)
    if t is None or t.repo_id != key.repo_id:
        raise ToolError(f"Unknown ticket {ticket_id} for this product.")
    return t


async def _run(ctx: Context, events, wait: bool) -> str | None:
    """Drive a ticket turn, forwarding steps as MCP progress. Returns the ticket id."""
    ticket_id: str | None = None
    n = 0

    async def consume() -> None:
        nonlocal ticket_id, n
        async for ev in events:
            name, data = ev["event"], ev["data"]
            if name == "ticket":
                ticket_id = data["ticket_id"]
            elif name == "error":
                raise ToolError(data.get("message", "Supfeel could not process this ticket."))
            elif name == "step" and wait and data.get("detail"):
                n += 1
                try:
                    await ctx.report_progress(n, None, f"{data['step']}: {data['detail']}"[:200])
                except Exception:  # progress is best effort (the client may not have asked for it)
                    pass

    if wait:
        try:
            await consume()
        except service.TicketError as e:
            raise ToolError(str(e)) from e
        return ticket_id

    # Fire and forget: start the turn, return as soon as the ticket exists.
    try:
        first = await anext(events)
    except service.TicketError as e:
        raise ToolError(str(e)) from e
    if first["event"] == "error":
        raise ToolError(first["data"].get("message", "error"))
    ticket_id = first["data"]["ticket_id"]

    async def drain() -> None:
        async for _ in events:
            pass

    task = asyncio.create_task(drain())
    _background.add(task)
    task.add_done_callback(_background.discard)
    return ticket_id


class Message(BaseModel):
    role: str = Field(description="customer | assistant (the first-line agent)")
    content: str


class Customer(BaseModel):
    name: str = ""
    email: str = ""
    ref: str = Field(
        default="", description="The customer's id in the business system (needed for account actions)."
    )


# ----------------------------------------------------------------------------------------- tools


@mcp.tool(annotations=ToolAnnotations(title="Product overview", read_only_hint=True))
async def get_product_overview(ctx: Context) -> dict[str, Any]:
    """What this product is and how it works (generated from its code), its modules and the actions Supfeel can
    take through its API. Free."""
    key = await _key(ctx)
    async with session_scope() as s:
        repo = await s.get(Repo, key.repo_id)
        modules = (
            await s.scalars(
                select(RepoDoc.key).where(RepoDoc.repo_id == key.repo_id, RepoDoc.kind == "module")
            )
        ).all()
        ops = (await s.scalars(select(ApiOperation).where(ApiOperation.repo_id == key.repo_id))).all()
    return {
        "product": (repo.settings or {}).get("business_name") or repo.full_name,
        "status": repo.status,
        "overview": repo.overview,
        "modules": list(modules),
        "actions_available": [f"{o.operation_id}: {o.summary}" for o in ops if o.method != "GET"],
        "prices_cents": {p.metric: p.cents for p in billing.PRICES.values()},
    }


@mcp.tool(annotations=ToolAnnotations(title="Ask about the product", read_only_hint=True))
async def ask_product(question: str, ctx: Context) -> dict[str, Any]:
    """Answer a factual question about how the product works, grounded in its code and docs (with citations).
    Cheap: use it before escalating."""
    key = await _key(ctx)
    try:
        await billing.charge(
            key.account_id, "ask", repo_id=key.repo_id, note=f"ask_product via {key.key_name}"
        )
    except billing.PaymentRequired as e:
        raise ToolError(str(e)) from e
    result = await ask(key.repo_id, question[:2000], account_id=key.account_id)
    return {k: result[k] for k in ("answer", "citations", "confidence")}


@mcp.tool(
    annotations=ToolAnnotations(title="Escalate to Supfeel", destructive_hint=False, open_world_hint=True)
)
async def escalate(
    message: Annotated[str, Field(description="The customer's latest message, verbatim.")],
    ctx: Context,
    customer: Customer | None = None,
    conversation: Annotated[
        list[Message] | None, Field(description="The conversation so far (oldest first).")
    ] = None,
    attempted: Annotated[str, Field(description="What you already tried or told the customer.")] = "",
    agent: Annotated[str, Field(description="Your name, e.g. 'Acme help bot'.")] = "",
    callback_url: Annotated[
        str,
        Field(
            description="Optional HTTPS URL we POST to when the ticket changes later (fix verified, merged)."
        ),
    ] = "",
    wait: Annotated[
        bool, Field(description="Wait for the result (default). False returns at once; poll get_ticket.")
    ] = True,
) -> dict[str, Any]:
    """Hand a customer's problem to Supfeel. It investigates the product's code and then explains, acts through
    the business API (asking the customer to confirm first) or fixes the bug with a pull request.
    Returns `customer_reply` (send it as-is), `status`, `next_step` and, when needed, `needs_confirmation`."""
    key = await _key(ctx)
    meta = {
        "handoff": {
            "agent": agent or key.key_name,
            "attempted": attempted[:2000],
            "transcript": [m.model_dump() for m in (conversation or [])][-20:],
        },
        "key_id": key.key_id,
    }
    if callback_url.startswith("https://") or callback_url.startswith("http://localhost"):
        meta["callback_url"] = callback_url[:500]
    events = service.create_ticket(
        key.repo_id, (customer or Customer()).model_dump(), message, channel="mcp", meta=meta
    )
    ticket_id = await _run(ctx, events, wait)
    return await service.relay(ticket_id)


@mcp.tool(annotations=ToolAnnotations(title="Reply on a ticket", open_world_hint=True))
async def reply(ticket_id: str, message: str, ctx: Context) -> dict[str, Any]:
    """Send the customer's next message on an existing ticket (answers, clarifications, "that fixed it")."""
    key = await _key(ctx)
    await _owned_ticket(key, ticket_id)
    await _run(ctx, service.post_message(ticket_id, message), wait=True)
    return await service.relay(ticket_id)


@mcp.tool(
    annotations=ToolAnnotations(
        title="Confirm or decline an action", destructive_hint=True, open_world_hint=True
    )
)
async def confirm(ticket_id: str, approved: bool, ctx: Context) -> dict[str, Any]:
    """Pass on the customer's decision about the action in `needs_confirmation`. Only call this with the
    customer's explicit answer; it changes data in the business system when approved."""
    key = await _key(ctx)
    t = await _owned_ticket(key, ticket_id)
    if t.status != "awaiting_confirmation":
        raise ToolError(f"Ticket {ticket_id} has nothing waiting for confirmation (status: {t.status}).")
    await _run(ctx, service.confirm(ticket_id, approved), wait=True)
    return await service.relay(ticket_id)


@mcp.tool(annotations=ToolAnnotations(title="Ticket status", read_only_hint=True))
async def get_ticket(ticket_id: str, ctx: Context) -> dict[str, Any]:
    """Current status of a ticket: latest reply, next step, fix PR and CI state."""
    key = await _key(ctx)
    await _owned_ticket(key, ticket_id)
    return await service.relay(ticket_id)


@mcp.tool(annotations=ToolAnnotations(title="Recent tickets", read_only_hint=True))
async def list_tickets(ctx: Context, status: str = "") -> list[dict[str, Any]]:
    """Recent tickets for this product (optionally filtered by status)."""
    key = await _key(ctx)
    rows = await service.list_tickets([key.repo_id], status or None, 25)
    return [
        {k: r[k] for k in ("id", "subject", "status", "category", "pr_url", "ci", "created_at")} for r in rows
    ]
