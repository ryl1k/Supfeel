"""Schema creation and deterministic demo seeding.

Run: `uv run python -m app.db.seed` (creates tables, resets demo data).
"""

import asyncio
import json
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    BUSINESS_TABLES,
    RUNTIME_TABLES,
    Base,
    Customer,
    Order,
    OrderItem,
    Payment,
    Product,
    Shipment,
    Subscription,
    Variant,
    utcnow,
)
from app.db.session import get_engine, session_scope

FIXTURES = Path(__file__).parent / "fixtures"


def sku_for(product_id: str, size: float | None, width: str) -> str:
    if size is None:
        return f"{product_id}-OS"
    return f"{product_id}-{size:g}-{width}"


async def init_db() -> None:
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS kb_chunks_embedding_hnsw "
                "ON kb_chunks USING hnsw (embedding vector_cosine_ops)"
            )
        )


def _ago(now: datetime, days: float | None) -> datetime | None:
    return None if days is None else now - timedelta(days=days)


async def _seed_catalog(session: AsyncSession) -> None:
    catalog = json.loads((FIXTURES / "catalog.json").read_text())
    out_of_stock = set(catalog["out_of_stock"])
    for p in catalog["products"]:
        session.add(
            Product(
                id=p["id"],
                name=p["name"],
                line=p["line"],
                color=p["color"],
                price_cents=p["price_cents"],
                tags=p["tags"],
                description=p["description"],
                final_sale=p.get("final_sale", False),
            )
        )
    await session.flush()
    for p in catalog["products"]:
        if p.get("one_size"):
            session.add(
                Variant(
                    sku=sku_for(p["id"], None, "D"), product_id=p["id"], size=Decimal(0), width="OS", stock=50
                )
            )
            continue
        for size in catalog["sizes"]:
            for width in p["widths"]:
                sku = sku_for(p["id"], size, width)
                session.add(
                    Variant(
                        sku=sku,
                        product_id=p["id"],
                        size=Decimal(str(size)),
                        width=width,
                        stock=0 if sku in out_of_stock else 12,
                    )
                )


async def _seed_demo(session: AsyncSession, now: datetime) -> None:
    demo = json.loads((FIXTURES / "demo.json").read_text())
    for c in demo["customers"]:
        session.add(Customer(**c))
    await session.flush()

    for o in demo["orders"]:
        items_total = sum(i["price_cents"] for i in o["items"])
        session.add(
            Order(
                id=o["id"],
                customer_id=o["customer_id"],
                status=o["status"],
                shipping_method=o["shipping_method"],
                shipping_cents=o["shipping_cents"],
                total_cents=items_total + o["shipping_cents"],
                shipping_address=o["address"],
                placed_at=_ago(now, o["placed_days_ago"]),
                shipped_at=_ago(now, o.get("shipped_days_ago")),
                delivered_at=_ago(now, o.get("delivered_days_ago")),
            )
        )
        await session.flush()
        for i in o["items"]:
            session.add(OrderItem(order_id=o["id"], sku=i["sku"], qty=1, price_cents=i["price_cents"]))
        if sh := o.get("shipment"):
            session.add(
                Shipment(
                    id=sh["id"],
                    order_id=o["id"],
                    carrier=sh["carrier"],
                    tracking_no=sh["tracking_no"],
                    status=sh["status"],
                    last_scan_at=_ago(now, sh.get("last_scan_days_ago")),
                    estimated_delivery=_ago(now, sh.get("estimated_delivery_days_ago")),
                    events=[
                        {"at": _ago(now, e["days_ago"]).isoformat(), "description": e["desc"]}
                        for e in sh.get("events", [])
                    ],
                )
            )
        for p in o["payments"]:
            session.add(
                Payment(
                    id=p["id"],
                    customer_id=o["customer_id"],
                    order_id=o["id"],
                    amount_cents=p["amount_cents"],
                    method=p["method"],
                    last4=p["last4"],
                    status=p["status"],
                    description=f"Order {o['id']}",
                    created_at=_ago(now, p["days_ago"]),
                )
            )

    for s in demo["subscriptions"]:
        renewed = _ago(now, s["renewed_days_ago"])
        period = timedelta(days=30 if s["plan"] == "monthly" else 365)
        session.add(
            Subscription(
                id=s["id"],
                customer_id=s["customer_id"],
                plan=s["plan"],
                price_cents=s["price_cents"],
                status=s["status"],
                renewed_at=renewed,
                current_period_end=renewed + period,
                benefits_used_since_renewal=s["benefits_used_since_renewal"],
            )
        )
        if rp := s.get("renewal_payment"):
            session.add(
                Payment(
                    id=rp["id"],
                    customer_id=s["customer_id"],
                    subscription_id=s["id"],
                    amount_cents=s["price_cents"],
                    method=rp["method"],
                    last4=rp["last4"],
                    status="captured",
                    description=f"Velora Club {s['plan']} renewal",
                    created_at=renewed,
                )
            )


async def reset_demo() -> None:
    """Wipe business + conversation state and reload fixtures. Keeps llm_usage and kb tables."""
    now = utcnow()
    async with session_scope() as session:
        tables = ", ".join(RUNTIME_TABLES + BUSINESS_TABLES + ["customers"])
        await session.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))
        await _seed_catalog(session)
        await session.flush()
        await _seed_demo(session, now)


async def _main() -> None:
    await init_db()
    await reset_demo()
    print("Database initialized and demo data seeded.")


if __name__ == "__main__":
    asyncio.run(_main())
