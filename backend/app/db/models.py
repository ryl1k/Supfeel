"""SQLAlchemy models: mock Velora business systems + Supfeel conversation/agent tables.

Money is always integer cents. Business IDs are readable strings (e.g. order "V1042").
"""

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    ARRAY,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

EMBEDDING_DIM = 1536


def utcnow() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    type_annotation_map = {dict[str, Any]: JSONB, list[Any]: JSONB}


# --------------------------------------------------------------------------- business systems


class Customer(Base):
    __tablename__ = "customers"
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(200))
    tier: Mapped[str] = mapped_column(String(20))  # member | guest
    persona: Mapped[str] = mapped_column(Text, default="")  # demo picker blurb
    preferences: Mapped[dict[str, Any]] = mapped_column(default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Product(Base):
    __tablename__ = "products"
    id: Mapped[str] = mapped_column(String(60), primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    line: Mapped[str] = mapped_column(String(40))
    color: Mapped[str] = mapped_column(String(40))
    price_cents: Mapped[int] = mapped_column(Integer)
    tags: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    description: Mapped[str] = mapped_column(Text, default="")
    final_sale: Mapped[bool] = mapped_column(Boolean, default=False)


class Variant(Base):
    __tablename__ = "variants"
    sku: Mapped[str] = mapped_column(String(80), primary_key=True)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"))
    size: Mapped[Decimal] = mapped_column(Numeric(3, 1))
    width: Mapped[str] = mapped_column(String(10))  # D (standard) | 2E (wide)
    stock: Mapped[int] = mapped_column(Integer, default=0)


class Order(Base):
    __tablename__ = "orders"
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.id"))
    status: Mapped[str] = mapped_column(String(20))  # processing | shipped | delivered | cancelled
    kind: Mapped[str] = mapped_column(String(20), default="standard")  # standard | exchange | reship
    parent_order_id: Mapped[str | None] = mapped_column(String(40), nullable=True)
    shipping_method: Mapped[str] = mapped_column(String(20), default="standard")
    shipping_cents: Mapped[int] = mapped_column(Integer, default=0)
    total_cents: Mapped[int] = mapped_column(Integer)
    shipping_address: Mapped[dict[str, Any]] = mapped_column(default=dict)
    placed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    shipped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    action_id: Mapped[str | None] = mapped_column(String(60), unique=True, nullable=True)


class OrderItem(Base):
    __tablename__ = "order_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.id"))
    sku: Mapped[str] = mapped_column(ForeignKey("variants.sku"))
    qty: Mapped[int] = mapped_column(Integer, default=1)
    price_cents: Mapped[int] = mapped_column(Integer)
    comfort_guarantee_used: Mapped[bool] = mapped_column(Boolean, default=False)
    return_status: Mapped[str] = mapped_column(String(20), default="none")  # none | label_issued | returned


class Shipment(Base):
    __tablename__ = "shipments"
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.id"))
    carrier: Mapped[str] = mapped_column(String(40))
    tracking_no: Mapped[str] = mapped_column(String(60))
    status: Mapped[str] = mapped_column(String(20))  # label_created | in_transit | delivered | lost
    last_scan_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    estimated_delivery: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    events: Mapped[list[Any]] = mapped_column(default=list)


class Payment(Base):
    __tablename__ = "payments"
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.id"))
    order_id: Mapped[str | None] = mapped_column(String(40), nullable=True)
    subscription_id: Mapped[str | None] = mapped_column(String(40), nullable=True)
    amount_cents: Mapped[int] = mapped_column(Integer)
    refunded_cents: Mapped[int] = mapped_column(Integer, default=0)
    method: Mapped[str] = mapped_column(String(20))  # card | paypal | apple_pay
    last4: Mapped[str | None] = mapped_column(String(4), nullable=True)
    status: Mapped[str] = mapped_column(String(24))  # authorized | captured | refunded | partially_refunded
    description: Mapped[str] = mapped_column(String(200), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Refund(Base):
    __tablename__ = "refunds"
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.id"))
    payment_id: Mapped[str | None] = mapped_column(String(40), nullable=True)
    order_id: Mapped[str | None] = mapped_column(String(40), nullable=True)
    amount_cents: Mapped[int] = mapped_column(Integer)
    method: Mapped[str] = mapped_column(String(20))  # original | store_credit
    reason: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="issued")
    action_id: Mapped[str | None] = mapped_column(String(60), unique=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Exchange(Base):
    __tablename__ = "exchanges"
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    order_item_id: Mapped[int] = mapped_column(ForeignKey("order_items.id"))
    new_order_id: Mapped[str] = mapped_column(String(40))
    new_sku: Mapped[str] = mapped_column(String(80))
    price_diff_cents: Mapped[int] = mapped_column(Integer, default=0)
    reason: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="created")
    action_id: Mapped[str | None] = mapped_column(String(60), unique=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ReturnLabel(Base):
    __tablename__ = "return_labels"
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    order_item_id: Mapped[int] = mapped_column(ForeignKey("order_items.id"))
    carrier: Mapped[str] = mapped_column(String(40))
    tracking_no: Mapped[str] = mapped_column(String(60))
    status: Mapped[str] = mapped_column(String(20), default="active")  # active | expired | used
    label_url: Mapped[str] = mapped_column(String(300))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    action_id: Mapped[str | None] = mapped_column(String(60), unique=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class StoreCredit(Base):
    __tablename__ = "store_credits"
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.id"))
    amount_cents: Mapped[int] = mapped_column(Integer)
    reason: Mapped[str] = mapped_column(Text)
    action_id: Mapped[str | None] = mapped_column(String(60), unique=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Subscription(Base):
    __tablename__ = "subscriptions"
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.id"))
    plan: Mapped[str] = mapped_column(String(20))  # monthly | annual
    price_cents: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20))  # active | paused | cancelled
    renewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    current_period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    benefits_used_since_renewal: Mapped[bool] = mapped_column(Boolean, default=False)
    paused_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    pause_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Escalation(Base):
    __tablename__ = "escalations"
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.id"))
    conversation_id: Mapped[str | None] = mapped_column(String(60), nullable=True)
    reason: Mapped[str] = mapped_column(String(60))
    summary: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="open")
    action_id: Mapped[str | None] = mapped_column(String(60), unique=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


# --------------------------------------------------------------------------- supfeel runtime


class Conversation(Base):
    __tablename__ = "conversations"
    id: Mapped[str] = mapped_column(String(60), primary_key=True)
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.id"))
    status: Mapped[str] = mapped_column(
        String(20), default="open"
    )  # open | awaiting_confirmation | resolved | escalated
    state: Mapped[dict[str, Any]] = mapped_column(default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class Message(Base):
    __tablename__ = "messages"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversations.id"))
    role: Mapped[str] = mapped_column(String(20))  # user | assistant
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ActionLog(Base):
    __tablename__ = "action_log"
    id: Mapped[str] = mapped_column(String(60), primary_key=True)
    conversation_id: Mapped[str | None] = mapped_column(String(60), nullable=True)
    tool: Mapped[str] = mapped_column(String(60))
    args: Mapped[dict[str, Any]] = mapped_column(default=dict)
    result: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(String(20))  # proposed | approved | declined | done | failed
    needs_confirmation: Mapped[bool] = mapped_column(Boolean, default=False)
    verified: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    verification: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class LlmUsage(Base):
    __tablename__ = "llm_usage"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    provider: Mapped[str] = mapped_column(String(20))  # anthropic | openai
    model: Mapped[str] = mapped_column(String(60))
    node: Mapped[str] = mapped_column(String(40))
    conversation_id: Mapped[str | None] = mapped_column(String(60), nullable=True)
    mode: Mapped[str] = mapped_column(String(10))
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cache_read_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cache_write_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cost_usd: Mapped[Decimal] = mapped_column(Numeric(12, 6), default=Decimal(0))


class KbChunk(Base):
    __tablename__ = "kb_chunks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    doc_id: Mapped[str] = mapped_column(String(80), index=True)
    doc_title: Mapped[str] = mapped_column(String(200))
    heading: Mapped[str] = mapped_column(String(200))
    text: Mapped[str] = mapped_column(Text)
    audience: Mapped[str] = mapped_column(String(20))
    tags: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    content_hash: Mapped[str] = mapped_column(String(64), unique=True)
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIM))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class EmbeddingCache(Base):
    __tablename__ = "embedding_cache"
    text_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    model: Mapped[str] = mapped_column(String(60))
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIM))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


BUSINESS_TABLES = [
    "escalations",
    "store_credits",
    "return_labels",
    "exchanges",
    "refunds",
    "payments",
    "shipments",
    "order_items",
    "orders",
    "subscriptions",
    "variants",
    "products",
]
RUNTIME_TABLES = ["action_log", "messages", "conversations"]
