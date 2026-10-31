import json
import logging
from collections.abc import AsyncIterator
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sse_starlette.sse import EventSourceResponse

from app.accounts.auth import CurrentPrincipal, Principal, repo_for
from app.db.models import Repo, Ticket
from app.db.session import session_scope
from app.obs.trace import load_trace
from app.support import service

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api")


class Customer(BaseModel):
    name: str = Field(default="", max_length=120)
    email: str = Field(default="", max_length=200)
    ref: str = Field(default="", max_length=120, description="the customer's id in the business system")


class NewTicket(BaseModel):
    customer: Customer = Customer()
    message: str = Field(min_length=1, max_length=4000)


class FollowUp(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


class Confirm(BaseModel):
    approved: bool


async def _sse(events: AsyncIterator[dict[str, Any]]) -> AsyncIterator[dict[str, str]]:
    try:
        async for ev in events:
            yield {"event": ev["event"], "data": json.dumps(ev["data"], default=str)}
    except service.TicketError as e:
        yield {"event": "error", "data": json.dumps({"code": "bad_request", "message": str(e)})}
    except Exception:
        log.exception("ticket stream failed")
        yield {
            "event": "error",
            "data": json.dumps({"code": "internal", "message": "Something went wrong on our side."}),
        }


def _stream(events: AsyncIterator[dict[str, Any]]) -> EventSourceResponse:
    return EventSourceResponse(
        _sse(events), ping=15, headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )


async def ticket_for(p: Principal, ticket_id: str) -> Ticket:
    async with session_scope() as s:
        t = await s.get(Ticket, ticket_id)
    if t is None:
        raise HTTPException(status_code=404, detail="unknown ticket")
    await repo_for(p, t.repo_id)
    return t


async def account_repo_ids(p: Principal) -> list[str] | None:
    if p.is_admin:
        return None
    async with session_scope() as s:
        return list((await s.scalars(select(Repo.id).where(Repo.account_id == p.account_id))).all())


# The web endpoints are the workspace playground (signed-in owner). Agents use the MCP server (/mcp).
@router.post("/repos/{repo_id}/tickets")
async def create_ticket(repo_id: str, body: NewTicket, p: CurrentPrincipal) -> EventSourceResponse:
    await repo_for(p, repo_id)
    return _stream(service.create_ticket(repo_id, body.customer.model_dump(), body.message, channel="web"))


@router.post("/tickets/{ticket_id}/messages")
async def follow_up(ticket_id: str, body: FollowUp, p: CurrentPrincipal) -> EventSourceResponse:
    await ticket_for(p, ticket_id)
    return _stream(service.post_message(ticket_id, body.message))


@router.post("/tickets/{ticket_id}/confirm")
async def confirm(ticket_id: str, body: Confirm, p: CurrentPrincipal) -> EventSourceResponse:
    await ticket_for(p, ticket_id)
    return _stream(service.confirm(ticket_id, body.approved))


@router.get("/tickets")
async def list_tickets(
    p: CurrentPrincipal, repo_id: str | None = None, status: str | None = None, limit: int = 100
) -> list[dict]:
    if repo_id:
        await repo_for(p, repo_id)
        return await service.list_tickets([repo_id], status, min(limit, 500))
    return await service.list_tickets(await account_repo_ids(p), status, min(limit, 500))


@router.get("/tickets/{ticket_id}")
async def get_ticket(ticket_id: str, p: CurrentPrincipal) -> dict:
    await ticket_for(p, ticket_id)
    return await service.get_ticket(ticket_id)


@router.get("/tickets/{ticket_id}/trace")
async def ticket_trace(ticket_id: str, p: CurrentPrincipal) -> dict:
    await ticket_for(p, ticket_id)
    return await load_trace(ticket_id)


@router.get("/notifications")
async def notifications(p: CurrentPrincipal, repo_id: str | None = None, limit: int = 100) -> list[dict]:
    if repo_id:
        await repo_for(p, repo_id)
        return await service.list_notifications([repo_id], min(limit, 500))
    return await service.list_notifications(await account_repo_ids(p), min(limit, 500))
