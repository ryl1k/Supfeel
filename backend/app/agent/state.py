from typing import Any, Literal, TypedDict

Outcome = Literal[
    "asked",  # clarifying question
    "awaiting_confirmation",
    "resolved",
    "partially_resolved",
    "declined",  # customer declined our proposal
    "not_allowed",  # request outside policy
    "escalated",
    "answered",  # informational
]


class ActionRecord(TypedDict, total=False):
    action_id: str
    tool: str
    args: dict[str, Any]
    reason: str
    title: str
    description: str
    amount_cents: int
    needs_confirmation: bool
    status: str  # proposed | approved | declined | done | failed
    result: dict[str, Any] | None
    error: dict[str, Any] | None
    verification: dict[str, Any] | None


class AgentState(TypedDict, total=False):
    conversation_id: str
    customer_id: str
    mode: Literal["message", "confirm"]
    user_message: str
    approved: bool
    history: list[dict[str, str]]
    previous: dict[str, Any]  # persisted context from earlier turns (last intent, outcome)

    brain: Literal["llm", "rules"]
    intent: dict[str, Any]
    facts: dict[str, Any]
    policies: list[dict[str, Any]]
    plan: dict[str, Any]
    actions: list[ActionRecord]
    outcome: Outcome
    reply: str
    notices: list[str]
