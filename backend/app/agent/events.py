"""Server-sent event contract. Mirrored in frontend/lib/types.ts. Change both together."""

from typing import Any

from langgraph.config import get_stream_writer

STEPS = ("understand", "investigate", "policy", "plan", "act", "verify", "respond")


def emit(event: str, **data: Any) -> None:
    """Send an event to the client. Safe to call outside a streaming graph run (no-op)."""
    try:
        writer = get_stream_writer()
    except Exception:  # not inside a LangGraph run (e.g. unit tests calling nodes directly)
        return
    writer({"event": event, "data": data})


def step(name: str, status: str, detail: str = "", **data: Any) -> None:
    emit("step", step=name, status=status, detail=detail, **data)
