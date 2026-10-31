"""Write tools. Enforce hard business invariants (ToolError); policy decisions live in the agent.

Idempotency per action_id is handled centrally in the registry via action_log.
"""

from datetime import timedelta
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select

from app.db.models import (
    Customer,
    Escalation,
    Exchange,
    Order,
    OrderItem,
    Payment,
    Product,
    Refund,
    ReturnLabel,
    Shipment,
    StoreCredit,
    Subscription,
    Variant,
)
from app.tools.base import ToolContext, ToolError, days_since, iso, money, new_id, now
from app.tools.read import _owned_order

STORE_CREDIT_BONUS = 0.10  # knowledge-base/policies/refunds.md
LABEL_VALID_DAYS = 14


class _Args(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CreateRefundArgs(_Args):
    payment_id: str
    amount_cents: int = Field(gt=0)
    method: Literal["original", "store_credit"] = "original"
    reason: str


class CreateExchangeArgs(_Args):
    order_item_id: int
    new_sku: str
    reason: str
    use_comfort_guarantee: bool = False


class ReturnLabelArgs(_Args):
    order_item_id: int


class ReshipArgs(_Args):
    order_id: str
    reason: str


class CancelOrderArgs(_Args):
    order_id: str
    reason: str


class Address(_Args):
    name: str | None = None
    line1: str
    city: str
    state: str
    zip: str
    country: str = "US"


class UpdateAddressArgs(_Args):
    order_id: str
    address: Address


class StoreCreditArgs(_Args):
    amount_cents: int = Field(gt=0)
    reason: str


class PauseArgs(_Args):
    months: int = Field(ge=1, le=3)


class CancelSubscriptionArgs(_Args):
    refund_renewal: bool = False
    reason: str


class EscalateArgs(_Args):
    reason: Literal[
        "refund_over_limit",
        "repeat_claim",
        "data_deletion",
        "fraud_or_legal",
        "customer_request",
        "verification_failed",
        "policy_gap",
    ]
    summary: str


async def _owned_item(ctx: ToolContext, order_item_id: int) -> tuple[OrderItem, Order]:
    item = await ctx.session.get(OrderItem, order_item_id)
    if item is None:
        raise ToolError("item_not_found", f"No order item {order_item_id}.")
    order = await ctx.session.get(Order, item.order_id)
    if order.customer_id != ctx.customer_id:
        raise ToolError("item_not_found", f"No order item {order_item_id} on this account.")
    return item, order


async def create_refund(ctx: ToolContext, args: CreateRefundArgs) -> dict:
    p = await ctx.session.get(Payment, args.payment_id)
    if p is None or p.customer_id != ctx.customer_id:
        raise ToolError("payment_not_found", f"No payment {args.payment_id} on this account.")
    if p.status == "authorized":
        raise ToolError(
            "not_captured", "This payment is only a pending authorization hold; it will drop off on its own."
        )
    refundable = p.amount_cents - p.refunded_cents
    if args.amount_cents > refundable:
        raise ToolError("amount_exceeds_refundable", f"Only {money(refundable)} is refundable on {p.id}.")
    p.refunded_cents += args.amount_cents
    p.status = "refunded" if p.refunded_cents == p.amount_cents else "partially_refunded"
    refund = Refund(
        id=new_id("RF"),
        customer_id=ctx.customer_id,
        payment_id=p.id,
        order_id=p.order_id,
        amount_cents=args.amount_cents,
        method=args.method,
        reason=args.reason,
        action_id=ctx.action_id,
    )
    ctx.session.add(refund)
    credit_cents = None
    if args.method == "store_credit":
        credit_cents = round(args.amount_cents * (1 + STORE_CREDIT_BONUS))
        ctx.session.add(
            StoreCredit(
                id=new_id("SC"),
                customer_id=ctx.customer_id,
                amount_cents=credit_cents,
                reason=f"Refund {refund.id} as store credit (+10% bonus)",
            )
        )
    await ctx.session.flush()
    return {
        "refund_id": refund.id,
        "payment_id": p.id,
        "amount": money(args.amount_cents),
        "amount_cents": args.amount_cents,
        "method": args.method,
        "store_credit_issued": money(credit_cents) if credit_cents else None,
        "payment_status": p.status,
        "eta": "Store credit available now" if credit_cents else "3–10 business days to appear on statement",
    }


async def create_exchange(ctx: ToolContext, args: CreateExchangeArgs) -> dict:
    item, order = await _owned_item(ctx, args.order_item_id)
    if order.status != "delivered":
        raise ToolError("not_delivered", "Exchanges are only possible for delivered orders.")
    if args.use_comfort_guarantee and item.comfort_guarantee_used:
        raise ToolError("comfort_guarantee_used", "The comfort guarantee was already used for this item.")
    variant = await ctx.session.get(Variant, args.new_sku)
    if variant is None:
        raise ToolError("sku_not_found", f"Unknown SKU {args.new_sku}.")
    if variant.stock <= 0:
        raise ToolError("out_of_stock", f"{args.new_sku} is out of stock.")
    product = await ctx.session.get(Product, variant.product_id)
    price_diff = product.price_cents - item.price_cents

    new_order = Order(
        id=new_id("VX"),
        customer_id=ctx.customer_id,
        status="processing",
        kind="exchange",
        parent_order_id=order.id,
        shipping_method="standard",
        shipping_cents=0,
        total_cents=max(price_diff, 0),
        shipping_address=order.shipping_address,
        placed_at=now(),
    )
    ctx.session.add(new_order)
    await ctx.session.flush()
    ctx.session.add(OrderItem(order_id=new_order.id, sku=variant.sku, qty=1, price_cents=product.price_cents))
    variant.stock -= 1
    if args.use_comfort_guarantee:
        item.comfort_guarantee_used = True
    exchange = Exchange(
        id=new_id("EX"),
        order_item_id=item.id,
        new_order_id=new_order.id,
        new_sku=variant.sku,
        price_diff_cents=price_diff,
        reason=args.reason,
        action_id=ctx.action_id,
    )
    ctx.session.add(exchange)
    await ctx.session.flush()
    return {
        "exchange_id": exchange.id,
        "new_order_id": new_order.id,
        "new_item": f"{product.name} {product.color}, size {float(variant.size):g} {variant.width}",
        "new_sku": variant.sku,
        "price_difference": money(price_diff),
        "price_difference_cents": price_diff,
        "ships": "Replacement ships now (advance exchange); return the original within 14 days.",
    }


async def create_return_label(ctx: ToolContext, args: ReturnLabelArgs) -> dict:
    item, order = await _owned_item(ctx, args.order_item_id)
    if order.status != "delivered":
        raise ToolError("not_delivered", "Return labels are only for delivered items.")
    # Expire any previous active label for this item.
    for old in (
        await ctx.session.scalars(
            select(ReturnLabel).where(ReturnLabel.order_item_id == item.id, ReturnLabel.status == "active")
        )
    ).all():
        old.status = "expired"
    label_id = new_id("RL")
    label = ReturnLabel(
        id=label_id,
        order_item_id=item.id,
        carrier="UPS",
        tracking_no=f"1ZRET{label_id[-6:]}",
        status="active",
        label_url=f"https://returns.velora.example/labels/{label_id}.pdf",
        expires_at=now() + timedelta(days=LABEL_VALID_DAYS),
        action_id=ctx.action_id,
    )
    ctx.session.add(label)
    item.return_status = "label_issued"
    await ctx.session.flush()
    return {
        "label_id": label.id,
        "carrier": label.carrier,
        "tracking_no": label.tracking_no,
        "label_url": label.label_url,
        "qr_code": True,
        "expires_at": iso(label.expires_at),
        "valid_days": LABEL_VALID_DAYS,
    }


async def reship_order(ctx: ToolContext, args: ReshipArgs) -> dict:
    order = await _owned_order(ctx, args.order_id)
    if order.status not in ("shipped",):
        raise ToolError(
            "not_reshippable",
            f"Order {order.id} is '{order.status}', only in-transit orders can be reshipped.",
        )
    shipment = await ctx.session.scalar(select(Shipment).where(Shipment.order_id == order.id))
    if shipment:
        shipment.status = "lost"
    items = (await ctx.session.scalars(select(OrderItem).where(OrderItem.order_id == order.id))).all()
    new_order = Order(
        id=new_id("VR"),
        customer_id=ctx.customer_id,
        status="processing",
        kind="reship",
        parent_order_id=order.id,
        shipping_method="express",
        shipping_cents=0,
        total_cents=0,
        shipping_address=order.shipping_address,
        placed_at=now(),
        action_id=ctx.action_id,
    )
    ctx.session.add(new_order)
    await ctx.session.flush()
    for i in items:
        ctx.session.add(OrderItem(order_id=new_order.id, sku=i.sku, qty=i.qty, price_cents=0))
    await ctx.session.flush()
    return {
        "new_order_id": new_order.id,
        "original_order_id": order.id,
        "shipping_method": "express",
        "eta": "1–2 business days after dispatch",
        "charge": money(0),
    }


async def cancel_order(ctx: ToolContext, args: CancelOrderArgs) -> dict:
    order = await _owned_order(ctx, args.order_id)
    if order.status != "processing":
        raise ToolError(
            "not_cancellable",
            f"Order {order.id} is '{order.status}'; only processing orders can be cancelled.",
        )
    order.status = "cancelled"
    order.cancelled_at = now()
    released, refunded = [], []
    for p in (await ctx.session.scalars(select(Payment).where(Payment.order_id == order.id))).all():
        if p.status == "authorized":
            p.status = "voided"
            released.append(p.id)
        elif p.status == "captured":
            p.refunded_cents = p.amount_cents
            p.status = "refunded"
            ctx.session.add(
                Refund(
                    id=new_id("RF"),
                    customer_id=ctx.customer_id,
                    payment_id=p.id,
                    order_id=order.id,
                    amount_cents=p.amount_cents,
                    method="original",
                    reason=f"Order cancelled: {args.reason}",
                )
            )
            refunded.append(p.id)
    await ctx.session.flush()
    return {
        "order_id": order.id,
        "status": "cancelled",
        "authorizations_released": released,
        "payments_refunded": refunded,
    }


async def update_address(ctx: ToolContext, args: UpdateAddressArgs) -> dict:
    order = await _owned_order(ctx, args.order_id)
    if order.status != "processing":
        raise ToolError(
            "already_shipped", f"Order {order.id} is '{order.status}'; the address can no longer be changed."
        )
    addr = args.address.model_dump()
    addr["name"] = addr["name"] or order.shipping_address.get("name")
    order.shipping_address = addr
    await ctx.session.flush()
    return {"order_id": order.id, "shipping_address": addr}


async def issue_store_credit(ctx: ToolContext, args: StoreCreditArgs) -> dict:
    credit = StoreCredit(
        id=new_id("SC"),
        customer_id=ctx.customer_id,
        amount_cents=args.amount_cents,
        reason=args.reason,
        action_id=ctx.action_id,
    )
    ctx.session.add(credit)
    await ctx.session.flush()
    return {
        "store_credit_id": credit.id,
        "amount": money(args.amount_cents),
        "amount_cents": args.amount_cents,
    }


async def _owned_subscription(ctx: ToolContext) -> Subscription:
    sub = await ctx.session.scalar(select(Subscription).where(Subscription.customer_id == ctx.customer_id))
    if sub is None:
        raise ToolError("no_subscription", "This account has no Velora Club membership.")
    return sub


async def pause_subscription(ctx: ToolContext, args: PauseArgs) -> dict:
    sub = await _owned_subscription(ctx)
    if sub.status != "active":
        raise ToolError("not_active", f"Membership is '{sub.status}'.")
    if sub.pause_used_at is not None and (days_since(sub.pause_used_at) or 0) <= 365:
        raise ToolError("pause_used", "A pause was already used in the last 12 months.")
    sub.status = "paused"
    sub.pause_used_at = now()
    sub.paused_until = now() + timedelta(days=30 * args.months)
    await ctx.session.flush()
    return {
        "subscription_id": sub.id,
        "status": "paused",
        "paused_until": iso(sub.paused_until),
        "months": args.months,
    }


async def cancel_subscription(ctx: ToolContext, args: CancelSubscriptionArgs) -> dict:
    sub = await _owned_subscription(ctx)
    if sub.status == "cancelled":
        raise ToolError("already_cancelled", "Membership is already cancelled.")
    sub.status = "cancelled"
    sub.cancelled_at = now()
    refund_view = None
    if args.refund_renewal:
        payment = await ctx.session.scalar(
            select(Payment)
            .where(Payment.subscription_id == sub.id, Payment.status == "captured")
            .order_by(Payment.created_at.desc())
        )
        if payment is None:
            raise ToolError("no_renewal_payment", "No refundable renewal payment found.")
        payment.refunded_cents = payment.amount_cents
        payment.status = "refunded"
        refund = Refund(
            id=new_id("RF"),
            customer_id=ctx.customer_id,
            payment_id=payment.id,
            amount_cents=payment.amount_cents,
            method="original",
            reason=f"Membership renewal refund: {args.reason}",
            action_id=ctx.action_id,
        )
        ctx.session.add(refund)
        refund_view = {
            "refund_id": refund.id,
            "amount": money(payment.amount_cents),
            "amount_cents": payment.amount_cents,
        }
    await ctx.session.flush()
    return {
        "subscription_id": sub.id,
        "status": "cancelled",
        "access_until": iso(sub.current_period_end) if not args.refund_renewal else iso(now()),
        "renewal_refund": refund_view,
    }


async def escalate_to_human(ctx: ToolContext, args: EscalateArgs) -> dict:
    customer = await ctx.session.get(Customer, ctx.customer_id)
    esc = Escalation(
        id=new_id("ESC"),
        customer_id=customer.id,
        conversation_id=ctx.conversation_id,
        reason=args.reason,
        summary=args.summary,
        action_id=ctx.action_id,
    )
    ctx.session.add(esc)
    await ctx.session.flush()
    return {"escalation_id": esc.id, "status": "open", "response_time": "within 1 business day"}
