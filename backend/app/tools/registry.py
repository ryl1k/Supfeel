"""Tool registry: validation, transactions, action_log, idempotency, verification."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, Literal

from pydantic import BaseModel, ValidationError

from app.db.models import ActionLog
from app.db.session import session_scope
from app.tools import read, recommendations, write
from app.tools.base import ToolContext, ToolError, new_id
from app.tools.verify import verify


@dataclass(frozen=True)
class ToolSpec:
    name: str
    fn: Callable[[ToolContext, Any], Awaitable[dict]]
    args: type[BaseModel]
    kind: Literal["read", "write"]
    description: str


TOOLS: dict[str, ToolSpec] = {
    s.name: s
    for s in [
        ToolSpec(
            "get_customer", read.get_customer, read.NoArgs, "read", "Customer profile, tier, preferences."
        ),
        ToolSpec("list_orders", read.list_orders, read.NoArgs, "read", "All orders with items and dates."),
        ToolSpec(
            "get_order",
            read.get_order,
            read.OrderArgs,
            "read",
            "Order details: items, shipment, payments, return window.",
        ),
        ToolSpec(
            "get_shipment",
            read.get_shipment,
            read.OrderArgs,
            "read",
            "Tracking with delayed/lost assessment.",
        ),
        ToolSpec(
            "get_payments",
            read.get_payments,
            read.PaymentsArgs,
            "read",
            "Payments with authorized/captured status and duplicate flags.",
        ),
        ToolSpec(
            "get_subscription",
            read.get_subscription,
            read.NoArgs,
            "read",
            "Velora Club membership status and renewal.",
        ),
        ToolSpec(
            "search_products",
            read.search_products,
            read.SearchProductsArgs,
            "read",
            "In-stock variants by line, size, width, tags.",
        ),
        ToolSpec(
            "get_recommendations",
            recommendations.get_recommendations,
            recommendations.RecommendationArgs,
            "read",
            "Personalized replacement suggestions for a fit problem.",
        ),
        ToolSpec(
            "create_refund",
            write.create_refund,
            write.CreateRefundArgs,
            "write",
            "Refund a captured payment (original method or store credit +10%).",
        ),
        ToolSpec(
            "create_exchange",
            write.create_exchange,
            write.CreateExchangeArgs,
            "write",
            "Advance exchange of a delivered item for another SKU.",
        ),
        ToolSpec(
            "create_return_label",
            write.create_return_label,
            write.ReturnLabelArgs,
            "write",
            "Prepaid return label (PDF + QR), valid 14 days.",
        ),
        ToolSpec(
            "reship_order",
            write.reship_order,
            write.ReshipArgs,
            "write",
            "Free express reship of a lost order.",
        ),
        ToolSpec(
            "cancel_order",
            write.cancel_order,
            write.CancelOrderArgs,
            "write",
            "Cancel a processing order; releases holds/refunds.",
        ),
        ToolSpec(
            "update_address",
            write.update_address,
            write.UpdateAddressArgs,
            "write",
            "Change shipping address of a processing order.",
        ),
        ToolSpec(
            "issue_store_credit",
            write.issue_store_credit,
            write.StoreCreditArgs,
            "write",
            "Goodwill store credit.",
        ),
        ToolSpec(
            "pause_subscription",
            write.pause_subscription,
            write.PauseArgs,
            "write",
            "Pause membership 1-3 months.",
        ),
        ToolSpec(
            "cancel_subscription",
            write.cancel_subscription,
            write.CancelSubscriptionArgs,
            "write",
            "Cancel membership, optionally refunding the renewal.",
        ),
        ToolSpec(
            "escalate_to_human",
            write.escalate_to_human,
            write.EscalateArgs,
            "write",
            "Hand the case to a human specialist.",
        ),
    ]
}

WRITE_TOOLS = sorted(n for n, s in TOOLS.items() if s.kind == "write")


def tool_catalog() -> str:
    """Stable, sorted text description of write tools and their args (for the planner prompt)."""
    lines = []
    for name in WRITE_TOOLS:
        spec = TOOLS[name]
        props = spec.args.model_json_schema().get("properties", {})
        arg_desc = ", ".join(
            f"{k}: {v.get('type', v.get('$ref', 'object')).split('/')[-1]}" for k, v in props.items()
        )
        lines.append(f"- {name}({arg_desc}): {spec.description}")
    return "\n".join(lines)


async def call_read(name: str, args: dict, *, customer_id: str) -> dict:
    spec = TOOLS[name]
    if spec.kind != "read":
        raise ValueError(f"{name} is not a read tool")
    try:
        parsed = spec.args.model_validate(args)
    except ValidationError as e:
        return {"error": "invalid_args", "message": str(e)}
    async with session_scope() as session:
        try:
            return await spec.fn(ToolContext(session=session, customer_id=customer_id), parsed)
        except ToolError as e:
            return e.to_dict()


async def propose(name: str, args: dict, *, conversation_id: str | None, needs_confirmation: bool) -> str:
    """Log a planned write action and return its action_id."""
    action_id = new_id("ACT")
    async with session_scope() as session:
        session.add(
            ActionLog(
                id=action_id,
                conversation_id=conversation_id,
                tool=name,
                args=args,
                status="proposed",
                needs_confirmation=needs_confirmation,
            )
        )
    return action_id


async def set_status(action_id: str, status: str) -> None:
    async with session_scope() as session:
        log = await session.get(ActionLog, action_id)
        if log:
            log.status = status


async def execute(action_id: str, *, customer_id: str, conversation_id: str | None) -> dict:
    """Run a proposed write action exactly once. Returns {ok, result|error, verification}."""
    async with session_scope() as session:
        log = await session.get(ActionLog, action_id)
        if log is None:
            raise ValueError(f"Unknown action {action_id}")
        if log.status == "done":
            return {"ok": True, "result": log.result, "verification": log.verification, "replayed": True}
        tool, raw_args = log.tool, dict(log.args)

    spec = TOOLS[tool]
    try:
        parsed = spec.args.model_validate(raw_args)
    except ValidationError as e:
        outcome = {"ok": False, "error": {"error": "invalid_args", "message": str(e)}}
        await _finish(action_id, "failed", outcome["error"], None)
        return outcome

    try:
        async with session_scope() as session:
            ctx = ToolContext(
                session=session, customer_id=customer_id, conversation_id=conversation_id, action_id=action_id
            )
            result = await spec.fn(ctx, parsed)
    except ToolError as e:
        await _finish(action_id, "failed", e.to_dict(), None)
        return {"ok": False, "error": e.to_dict()}

    verification = await verify(tool, parsed.model_dump(), result)
    await _finish(action_id, "done", result, verification)
    return {"ok": True, "result": result, "verification": verification}


async def _finish(action_id: str, status: str, result: dict | None, verification: dict | None) -> None:
    async with session_scope() as session:
        log = await session.get(ActionLog, action_id)
        log.status = status
        log.result = result
        log.verification = verification
        log.verified = verification["ok"] if verification else None
