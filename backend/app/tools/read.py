"""Read tools. All are scoped to ctx.customer_id: a customer can never see another customer's data."""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select

from app.db.models import Customer, Order, OrderItem, Payment, Product, Shipment, Subscription, Variant
from app.tools.base import ToolContext, ToolError, business_days_since, days_since, iso, money

# Thresholds mirror knowledge-base/policies/shipping-and-delivery.md
DELAYED_BUSINESS_DAYS = 5
LOST_BUSINESS_DAYS = 7
RETURN_WINDOW_DAYS = 30


class NoArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")


class OrderArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")
    order_id: str


class PaymentsArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")
    order_id: str | None = None


class SearchProductsArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")
    line: str | None = None
    width: str | None = Field(None, description="D (standard) or 2E (wide)")
    size: float | None = None
    tags: list[str] | None = None
    exclude_product_id: str | None = None
    limit: int = 6


async def _owned_order(ctx: ToolContext, order_id: str) -> Order:
    order = await ctx.session.get(Order, order_id.strip().upper().lstrip("#"))
    if order is None or order.customer_id != ctx.customer_id:
        raise ToolError("order_not_found", f"No order {order_id} on this account.")
    return order


async def _item_view(ctx: ToolContext, item: OrderItem) -> dict:
    variant = await ctx.session.get(Variant, item.sku)
    product = await ctx.session.get(Product, variant.product_id)
    return {
        "order_item_id": item.id,
        "sku": item.sku,
        "product_id": product.id,
        "name": product.name,
        "line": product.line,
        "color": product.color,
        "size": float(variant.size) if variant.width != "OS" else None,
        "width": variant.width,
        "price": money(item.price_cents),
        "price_cents": item.price_cents,
        "final_sale": product.final_sale,
        "comfort_guarantee_used": item.comfort_guarantee_used,
        "return_status": item.return_status,
    }


def _shipment_view(sh: Shipment) -> dict:
    bdays = business_days_since(sh.last_scan_at)
    assessment = "on_track"
    if sh.status == "delivered":
        assessment = "delivered"
    elif sh.status == "lost" or (bdays is not None and bdays >= LOST_BUSINESS_DAYS):
        assessment = "lost"
    elif bdays is not None and bdays >= DELAYED_BUSINESS_DAYS:
        assessment = "delayed"
    return {
        "shipment_id": sh.id,
        "carrier": sh.carrier,
        "tracking_no": sh.tracking_no,
        "status": sh.status,
        "last_scan_at": iso(sh.last_scan_at),
        "business_days_since_last_scan": bdays,
        "estimated_delivery": iso(sh.estimated_delivery),
        "assessment": assessment,
        "events": sh.events,
    }


def _payment_view(p: Payment) -> dict:
    return {
        "payment_id": p.id,
        "order_id": p.order_id,
        "subscription_id": p.subscription_id,
        "amount": money(p.amount_cents),
        "amount_cents": p.amount_cents,
        "refunded_cents": p.refunded_cents,
        "method": p.method,
        "last4": p.last4,
        "status": p.status,
        "description": p.description,
        "created_at": iso(p.created_at),
    }


async def get_customer(ctx: ToolContext, args: NoArgs) -> dict:
    c = await ctx.session.get(Customer, ctx.customer_id)
    if c is None:
        raise ToolError("customer_not_found", "Customer not found.")
    return {
        "customer_id": c.id,
        "name": c.name,
        "email": c.email,
        "tier": c.tier,
        "preferences": c.preferences,
    }


async def list_orders(ctx: ToolContext, args: NoArgs) -> dict:
    orders = (
        await ctx.session.scalars(
            select(Order).where(Order.customer_id == ctx.customer_id).order_by(Order.placed_at.desc())
        )
    ).all()
    out = []
    for o in orders:
        items = (await ctx.session.scalars(select(OrderItem).where(OrderItem.order_id == o.id))).all()
        out.append(
            {
                "order_id": o.id,
                "status": o.status,
                "kind": o.kind,
                "total": money(o.total_cents),
                "placed_days_ago": days_since(o.placed_at),
                "delivered_days_ago": days_since(o.delivered_at),
                "items": [await _item_view(ctx, i) for i in items],
            }
        )
    return {"orders": out}


async def get_order(ctx: ToolContext, args: OrderArgs) -> dict:
    o = await _owned_order(ctx, args.order_id)
    items = (await ctx.session.scalars(select(OrderItem).where(OrderItem.order_id == o.id))).all()
    shipment = await ctx.session.scalar(select(Shipment).where(Shipment.order_id == o.id))
    payments = (await ctx.session.scalars(select(Payment).where(Payment.order_id == o.id))).all()
    delivered_days = days_since(o.delivered_at)
    return {
        "order_id": o.id,
        "status": o.status,
        "kind": o.kind,
        "parent_order_id": o.parent_order_id,
        "shipping_method": o.shipping_method,
        "shipping": money(o.shipping_cents),
        "total": money(o.total_cents),
        "total_cents": o.total_cents,
        "shipping_address": o.shipping_address,
        "placed_at": iso(o.placed_at),
        "delivered_at": iso(o.delivered_at),
        "delivered_days_ago": delivered_days,
        "within_30_day_window": delivered_days is not None and delivered_days <= RETURN_WINDOW_DAYS,
        "items": [await _item_view(ctx, i) for i in items],
        "shipment": _shipment_view(shipment) if shipment else None,
        "payments": [_payment_view(p) for p in payments],
    }


async def get_shipment(ctx: ToolContext, args: OrderArgs) -> dict:
    o = await _owned_order(ctx, args.order_id)
    sh = await ctx.session.scalar(select(Shipment).where(Shipment.order_id == o.id))
    if sh is None:
        return {"order_id": o.id, "shipment": None, "note": "Order has not shipped yet."}
    return {"order_id": o.id, "shipment": _shipment_view(sh)}


async def get_payments(ctx: ToolContext, args: PaymentsArgs) -> dict:
    stmt = select(Payment).where(Payment.customer_id == ctx.customer_id).order_by(Payment.created_at.desc())
    if args.order_id:
        o = await _owned_order(ctx, args.order_id)
        stmt = stmt.where(Payment.order_id == o.id)
    payments = (await ctx.session.scalars(stmt)).all()
    views = [_payment_view(p) for p in payments]
    # Flag likely duplicates: same order + amount, both captured.
    seen: dict[tuple, str] = {}
    for v in views:
        key = (v["order_id"], v["amount_cents"])
        if v["order_id"] and v["status"] == "captured":
            if key in seen:
                v["possible_duplicate_of"] = seen[key]
            else:
                seen[key] = v["payment_id"]
    return {"payments": views}


async def get_subscription(ctx: ToolContext, args: NoArgs) -> dict:
    sub = await ctx.session.scalar(select(Subscription).where(Subscription.customer_id == ctx.customer_id))
    if sub is None:
        return {"subscription": None}
    renewal_payment = await ctx.session.scalar(
        select(Payment).where(Payment.subscription_id == sub.id).order_by(Payment.created_at.desc())
    )
    pause_available = sub.pause_used_at is None or (days_since(sub.pause_used_at) or 0) > 365
    return {
        "subscription": {
            "subscription_id": sub.id,
            "plan": sub.plan,
            "price": money(sub.price_cents),
            "status": sub.status,
            "renewed_days_ago": days_since(sub.renewed_at),
            "current_period_end": iso(sub.current_period_end),
            "benefits_used_since_renewal": sub.benefits_used_since_renewal,
            "pause_available": pause_available,
            "paused_until": iso(sub.paused_until),
            "renewal_payment": _payment_view(renewal_payment) if renewal_payment else None,
        }
    }


async def search_products(ctx: ToolContext, args: SearchProductsArgs) -> dict:
    stmt = select(Variant, Product).join(Product, Product.id == Variant.product_id).where(Variant.stock > 0)
    if args.line:
        stmt = stmt.where(Product.line.ilike(args.line))
    if args.width:
        stmt = stmt.where(Variant.width == args.width.upper())
    if args.size is not None:
        stmt = stmt.where(Variant.size == Decimal(str(args.size)))
    if args.exclude_product_id:
        stmt = stmt.where(Product.id != args.exclude_product_id)
    if args.tags:
        stmt = stmt.where(Product.tags.overlap(args.tags))
    rows = (await ctx.session.execute(stmt.order_by(Product.id, Variant.size, Variant.width))).all()
    results = [
        {
            "sku": v.sku,
            "product_id": p.id,
            "name": p.name,
            "color": p.color,
            "size": float(v.size) if v.width != "OS" else None,
            "width": v.width,
            "price": money(p.price_cents),
            "price_cents": p.price_cents,
            "tags": p.tags,
            "in_stock": v.stock,
        }
        for v, p in rows
    ]
    return {"results": results[: args.limit], "total_matches": len(results)}
