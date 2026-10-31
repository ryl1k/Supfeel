import json
import logging
from collections.abc import AsyncIterator
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from app.agent import service

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api")


class ChatRequest(BaseModel):
    conversation_id: str = Field(min_length=6, max_length=60, pattern=r"^[A-Za-z0-9_-]+$")
    customer_id: str = Field(max_length=40)
    message: str = Field(min_length=1, max_length=2000)


class ConfirmRequest(BaseModel):
    conversation_id: str = Field(min_length=6, max_length=60, pattern=r"^[A-Za-z0-9_-]+$")
    approved: bool


async def _sse(events: AsyncIterator[dict[str, Any]]) -> AsyncIterator[dict[str, str]]:
    try:
        async for ev in events:
            yield {"event": ev["event"], "data": json.dumps(ev["data"], default=str)}
    except service.ConversationError as e:
        yield {"event": "error", "data": json.dumps({"code": "bad_request", "message": str(e)})}
    except Exception:
        log.exception("chat turn failed")
        yield {
            "event": "error",
            "data": json.dumps(
                {"code": "internal", "message": "Something went wrong on our side. Please try again."}
            ),
        }


def _stream(events: AsyncIterator[dict[str, Any]]) -> EventSourceResponse:
    return EventSourceResponse(
        _sse(events),
        ping=15,
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/chat")
async def chat(req: ChatRequest) -> EventSourceResponse:
    return _stream(service.handle_message(req.conversation_id, req.customer_id, req.message))


@router.post("/chat/confirm")
async def confirm(req: ConfirmRequest) -> EventSourceResponse:
    return _stream(service.handle_confirm(req.conversation_id, req.approved))


@router.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str) -> dict:
    try:
        return await service.transcript(conversation_id)
    except service.ConversationError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
