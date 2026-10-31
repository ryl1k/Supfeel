from typing import Any, Literal, TypedDict


class TicketState(TypedDict, total=False):
    ticket_id: str
    repo_id: str
    business: str
    customer: dict[str, Any]
    subject: str
    mode: Literal["message", "confirm"]
    approved: bool
    message: str
    history: list[dict[str, str]]

    ctx: dict[str, Any]
    triage: dict[str, Any]
    brain: dict[str, str]  # node -> llm | rules
    route: str  # explain | assist | fix | feature | escalate | ask
    action: dict[str, Any] | None  # proposed / executed business API action
    fix: dict[str, Any]
    status: str
    resolution: dict[str, Any]
    notes: list[str]
    reply: str
