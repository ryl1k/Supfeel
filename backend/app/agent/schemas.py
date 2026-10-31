"""Structured outputs produced by the brain (LLM or rules)."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

IntentName = Literal[
    "comfort_exchange",
    "return_refund",
    "order_status",
    "lost_or_delayed",
    "damaged_or_defective",
    "double_charge",
    "billing_question",
    "cancel_membership",
    "pause_membership",
    "cancel_order",
    "change_address",
    "product_question",
    "policy_question",
    "human_request",
    "greeting",
    "other",
]

FitProblem = Literal["narrow", "wide", "short", "long", "arch", "stiff", "other"]

WriteTool = Literal[
    "cancel_order",
    "cancel_subscription",
    "create_exchange",
    "create_refund",
    "create_return_label",
    "escalate_to_human",
    "issue_store_credit",
    "pause_subscription",
    "reship_order",
    "update_address",
]


class Intent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    intent: IntentName
    summary: str = Field(description="One sentence: the customer's underlying problem.")
    order_id: str | None = Field(description="Order number if mentioned, e.g. V1042.")
    fit_problem: FitProblem | None = Field(description="For comfort issues: what feels wrong.")
    preferred_resolution: str | None = Field(
        description="What the customer asked for, if stated (refund, exchange, store credit, reship, cancel, pause...)."
    )
    new_address: str | None = Field(description="Full new shipping address if the customer provided one.")
    needs_clarification: bool = Field(
        description="True only if a key fact is missing and cannot be looked up."
    )
    clarifying_question: str | None
    search_query: str = Field(description="Short query to search company policy for this problem.")


class PlannedAction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tool: WriteTool
    args_json: str = Field(description="JSON object with the tool arguments.")
    reason: str


class Plan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision: Literal["act", "ask", "inform", "decline", "escalate"]
    rationale: str = Field(description="Why, grounded in the facts and the cited policy.")
    policy_citations: list[str] = Field(description="Policy section titles relied on.")
    actions: list[PlannedAction]
    question: str | None = Field(description="Question for the customer when decision is 'ask'.")
    offer_recommendations: bool = Field(description="Show personalized product suggestions to the customer.")
