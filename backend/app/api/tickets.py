import json
import logging
from collections.abc import AsyncIterator
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

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


@router.post("/repos/{repo_id}/tickets")
async def create_ticket(repo_id: str, body: NewTicket) -> EventSourceResponse:
    return _stream(service.create_ticket(repo_id, body.customer.model_dump(), body.message))


@router.post("/tickets/{ticket_id}/messages")
async def follow_up(ticket_id: str, body: FollowUp) -> EventSourceResponse:
    return _stream(service.post_message(ticket_id, body.message))


@router.post("/tickets/{ticket_id}/confirm")
async def confirm(ticket_id: str, body: Confirm) -> EventSourceResponse:
    return _stream(service.confirm(ticket_id, body.approved))


@router.get("/tickets")
async def list_tickets(repo_id: str | None = None, status: str | None = None, limit: int = 100) -> list[dict]:
    return await service.list_tickets(repo_id, status, min(limit, 500))


@router.get("/tickets/{ticket_id}")
async def get_ticket(ticket_id: str) -> dict:
    try:
        return await service.get_ticket(ticket_id)
    except service.TicketError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.get("/tickets/{ticket_id}/trace")
async def ticket_trace(ticket_id: str) -> dict:
    return await load_trace(ticket_id)


@router.get("/notifications")
async def notifications(repo_id: str | None = None, limit: int = 100) -> list[dict]:
    return await service.list_notifications(repo_id, min(limit, 500))
