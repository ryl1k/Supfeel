"""Deterministic investigation: which read tools to call for an intent, plus derived policy flags.

No LLM here on purpose: cheaper, reproducible, and the planner gets pre-computed facts.
"""

from typing import Any

from app.tools import registry

DELIVERED_INTENTS = {"comfort_exchange", "return_refund", "damaged_or_defective"}
SHIPPING_INTENTS = {"lost_or_delayed", "order_status"}
BILLING_INTENTS = {"double_charge", "billing_question"}
PROCESSING_INTENTS = {"cancel_order", "change_address"}
MEMBERSHIP_INTENTS = {"cancel_membership", "pause_membership"}


def _pick_order(intent: str, orders: list[dict], payments: list[dict] | None) -> str | None:
    def first(pred) -> str | None:
        return next((o["order_id"] for o in orders if pred(o)), None)

    if intent in DELIVERED_INTENTS:
        return first(lambda o: o["status"] == "delivered" and o["kind"] == "standard")
    if intent in SHIPPING_INTENTS:
        return first(lambda o: o["status"] == "shipped") or first(lambda o: True)
    if intent in BILLING_INTENTS and payments:
        dup = next((p for p in payments if p.get("possible_duplicate_of")), None)
        if dup:
            return dup["order_id"]
        return payments[0].get("order_id")
    if intent in PROCESSING_INTENTS:
        return first(lambda o: o["status"] == "processing")
    return first(lambda o: True)


def _main_item(order: dict) -> dict | None:
    items = [i for i in order.get("items", []) if i.get("width") != "OS"]
    return items[0] if items else (order.get("items") or [None])[0]


async def investigate(intent: dict[str, Any], customer_id: str) -> dict[str, Any]:
    name = intent["intent"]
    calls: list[str] = ["get_customer", "list_orders"]
    customer = await registry.call_read("get_customer", {}, customer_id=customer_id)
    orders = (await registry.call_read("list_orders", {}, customer_id=customer_id)).get("orders", [])

    payments = None
    if name in BILLING_INTENTS:
        payments = (await registry.call_read("get_payments", {}, customer_id=customer_id)).get("payments", [])
        calls.append("get_payments")

    order_id = intent.get("order_id")
    if order_id and not any(o["order_id"] == order_id.strip().upper().lstrip("#") for o in orders):
        order_id = None  # unknown or someone else's order; fall back to inference
    order_id = order_id or _pick_order(name, orders, payments)

    target = None
    if order_id:
        target = await registry.call_read("get_order", {"order_id": order_id}, customer_id=customer_id)
        calls.append("get_order")
        if "error" in target:
            target = None

    subscription = None
    if name in MEMBERSHIP_INTENTS or name in BILLING_INTENTS:
        subscription = (await registry.call_read("get_subscription", {}, customer_id=customer_id)).get(
            "subscription"
        )
        calls.append("get_subscription")

    recommendations = None
    item = _main_item(target) if target else None
    if name == "comfort_exchange" and item and item.get("size"):
        recommendations = await registry.call_read(
            "get_recommendations",
            {
                "product_id": item["product_id"],
                "size": item["size"],
                "fit_problem": intent.get("fit_problem") or "other",
            },
            customer_id=customer_id,
        )
        calls.append("get_recommendations")

    derived: dict[str, Any] = {"is_member": customer.get("tier") == "member"}
    if target:
        derived.update(
            order_status=target["status"],
            days_since_delivery=target.get("delivered_days_ago"),
            return_window_open=target.get("within_30_day_window", False),
        )
        if item:
            derived.update(
                main_item_id=item["order_item_id"],
                main_item=f"{item['name']} {item['color']}"
                + (f", size {item['size']:g} {item['width']}" if item.get("size") else ""),
                main_item_price_cents=item["price_cents"],
                comfort_guarantee_available=(
                    not item["comfort_guarantee_used"]
                    and derived["return_window_open"]
                    and item.get("width") != "OS"
                ),
                final_sale=item["final_sale"],
            )
        if target.get("shipment"):
            derived["shipment_assessment"] = target["shipment"]["assessment"]
            derived["business_days_since_last_scan"] = target["shipment"]["business_days_since_last_scan"]
    if payments is not None:
        dupes = [p for p in payments if p.get("possible_duplicate_of")]
        derived["duplicate_captured_payments"] = [
            {
                "payment_id": p["payment_id"],
                "duplicate_of": p["possible_duplicate_of"],
                "amount_cents": p["amount_cents"],
            }
            for p in dupes
            if p["status"] == "captured"
        ]
        derived["authorization_holds"] = [
            {"payment_id": p["payment_id"], "order_id": p["order_id"], "amount_cents": p["amount_cents"]}
            for p in payments
            if p["status"] == "authorized"
        ]
    if subscription:
        derived.update(
            membership_status=subscription["status"],
            pause_available=subscription["pause_available"],
            renewal_refund_eligible=(
                subscription["renewed_days_ago"] is not None
                and subscription["renewed_days_ago"] <= 14
                and not subscription["benefits_used_since_renewal"]
                and subscription["renewal_payment"] is not None
            ),
        )

    return {
        "customer": customer,
        "orders": [
            {
                k: o[k]
                for k in ("order_id", "status", "kind", "total", "placed_days_ago", "delivered_days_ago")
            }
            | {"items": [f"{i['name']} {i['color']}" for i in o["items"]]}
            for o in orders
        ],
        "target_order": target,
        "payments": payments,
        "subscription": subscription,
        "recommendations": recommendations,
        "derived": derived,
        "calls": calls,
    }
