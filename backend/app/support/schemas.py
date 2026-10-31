from typing import Literal

from pydantic import BaseModel, Field

Category = Literal["bug", "misunderstanding", "assisted_action", "feature_request", "other"]


class Triage(BaseModel):
    category: Category = Field(
        description="bug: the product misbehaves (code defect). misunderstanding: the product works as designed "
        "and the customer needs an explanation. assisted_action: the customer wants something done that we can do "
        "through the business API on their behalf. feature_request: asks for new behavior. other: anything else."
    )
    confidence: float = Field(description="0..1")
    subject: str = Field(description="ticket title, max 80 chars")
    summary: str = Field(description="one sentence: what the customer needs")
    customer_goal: str = Field(description="what outcome would make the customer happy")
    also_bug: bool = Field(
        description="true if, besides the main category, the message reveals a product defect"
    )
    bug_hypothesis: str = Field(description="if bug or also_bug: suspected cause in the code, else empty")
    search_queries: list[str] = Field(description="1-3 queries to search the codebase/docs for this ticket")
    needs_clarification: bool
    clarifying_question: str = Field(description="one short question if needs_clarification, else empty")


class ActionProposal(BaseModel):
    operation_id: str
    args_json: str = Field(description='JSON object: {"path": {...}, "query": {...}, "body": {...}}')
    title: str = Field(description="short customer-facing description, e.g. 'Reorder 2 medium Garden Veggie'")
    why: str
