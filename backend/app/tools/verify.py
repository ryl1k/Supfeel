"""Read-back verification for write tools.

Each verifier opens a FRESH session and checks persisted state, never the tool's own return value.
"""

from collections.abc import Awaitable, Callable

from sqlalchemy import select

from app.db.models import (
    Escalation,
    Exchange,
    Order,
    OrderItem,
    Payment,
    Refund,
    ReturnLabel,
    StoreCredit,
    Subscription,
)
from app.db.session import session_scope

Check = dict  # {"label": str, "ok": bool, "detail": str}


def _check(label: str, ok: bool, detail: str = "") -> Check:
    return {"label": label, "ok": bool(ok), "detail": detail}


async def _verify_refund(args: dict, result: dict) -> list[Check]:
    async with session_scope() as s:
        refund = await s.get(Refund, result["refund_id"])
        payment = await s.get(Payment, args["payment_id"])
    return [
        _check("Refund recorded", refund is not None and refund.status == "issued", result["refund_id"]),
        _check(
            "Amount matches",
            refund is not None and refund.amount_cents == args["amount_cents"],
            result["amount"],
        ),
        _check(
            "Payment updated",
            payment is not None and payment.status in ("refunded", "partially_refunded"),
            payment.status if payment else "missing",
        ),
    ]


async def _verify_exchange(args: dict, result: dict) -> list[Check]:
    async with session_scope() as s:
        exchange = await s.get(Exchange, result["exchange_id"])
        new_order = await s.get(Order, result["new_order_id"])
        item = await s.scalar(select(OrderItem).where(OrderItem.order_id == result["new_order_id"]))
    return [
        _check("Exchange recorded", exchange is not None, result["exchange_id"]),
        _check(
            "Replacement order created",
            new_order is not None and new_order.status == "processing",
            f"{result['new_order_id']} ({new_order.status if new_order else 'missing'})",
        ),
        _check("Correct item reserved", item is not None and item.sku == args["new_sku"], args["new_sku"]),
    ]


async def _verify_label(args: dict, result: dict) -> list[Check]:
    async with session_scope() as s:
        label = await s.get(ReturnLabel, result["label_id"])
    return [
        _check("Label active", label is not None and label.status == "active", result["label_id"]),
        _check("Label not expired", label is not None and label.expires_at > _now(), result["expires_at"]),
    ]


async def _verify_reship(args: dict, result: dict) -> list[Check]:
    async with session_scope() as s:
        new_order = await s.get(Order, result["new_order_id"])
    return [
        _check(
            "Replacement order created",
            new_order is not None
            and new_order.status == "processing"
            and new_order.shipping_method == "express",
            result["new_order_id"],
        )
    ]


async def _verify_cancel_order(args: dict, result: dict) -> list[Check]:
    async with session_scope() as s:
        order = await s.get(Order, result["order_id"])
        payments = (await s.scalars(select(Payment).where(Payment.order_id == result["order_id"]))).all()
    return [
        _check("Order cancelled", order is not None and order.status == "cancelled", result["order_id"]),
        _check(
            "No active charges left",
            all(p.status in ("voided", "refunded") for p in payments),
            ", ".join(f"{p.id}:{p.status}" for p in payments),
        ),
    ]


async def _verify_address(args: dict, result: dict) -> list[Check]:
    async with session_scope() as s:
        order = await s.get(Order, result["order_id"])
    want = args["address"]
    ok = order is not None and all(order.shipping_address.get(k) == v for k, v in want.items() if v)
    return [_check("Address updated", ok, f"{want.get('line1')}, {want.get('city')}")]


async def _verify_store_credit(args: dict, result: dict) -> list[Check]:
    async with session_scope() as s:
        credit = await s.get(StoreCredit, result["store_credit_id"])
    return [
        _check(
            "Store credit issued",
            credit is not None and credit.amount_cents == args["amount_cents"],
            result["amount"],
        )
    ]


async def _verify_pause(args: dict, result: dict) -> list[Check]:
    async with session_scope() as s:
        sub = await s.get(Subscription, result["subscription_id"])
    return [
        _check(
            "Membership paused", sub is not None and sub.status == "paused", result.get("paused_until") or ""
        )
    ]


async def _verify_cancel_sub(args: dict, result: dict) -> list[Check]:
    async with session_scope() as s:
        sub = await s.get(Subscription, result["subscription_id"])
        checks = [
            _check(
                "Membership cancelled",
                sub is not None and sub.status == "cancelled",
                result["subscription_id"],
            )
        ]
        if result.get("renewal_refund"):
            refund = await s.get(Refund, result["renewal_refund"]["refund_id"])
            checks.append(_check("Renewal refunded", refund is not None, result["renewal_refund"]["amount"]))
    return checks


async def _verify_escalation(args: dict, result: dict) -> list[Check]:
    async with session_scope() as s:
        esc = await s.get(Escalation, result["escalation_id"])
    return [
        _check(
            "Case handed to a specialist", esc is not None and esc.status == "open", result["escalation_id"]
        )
    ]


def _now():
    from app.tools.base import now

    return now()


VERIFIERS: dict[str, Callable[[dict, dict], Awaitable[list[Check]]]] = {
    "create_refund": _verify_refund,
    "create_exchange": _verify_exchange,
    "create_return_label": _verify_label,
    "reship_order": _verify_reship,
    "cancel_order": _verify_cancel_order,
    "update_address": _verify_address,
    "issue_store_credit": _verify_store_credit,
    "pause_subscription": _verify_pause,
    "cancel_subscription": _verify_cancel_sub,
    "escalate_to_human": _verify_escalation,
}


async def verify(tool: str, args: dict, result: dict) -> dict:
    verifier = VERIFIERS.get(tool)
    if verifier is None:
        return {"ok": True, "checks": []}
    checks = await verifier(args, result)
    return {"ok": all(c["ok"] for c in checks), "checks": checks}
