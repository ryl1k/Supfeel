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
        String(32), default="open"
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
    account_id: Mapped[str | None] = mapped_column(String(40), nullable=True, index=True)
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
    content_hash: Mapped[str] = mapped_column(String(64), unique=True)  # sha256(embedding_model + text)
    embedding_model: Mapped[str] = mapped_column(String(60), index=True)
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIM))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class EmbeddingCache(Base):
    __tablename__ = "embedding_cache"
    text_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    model: Mapped[str] = mapped_column(String(60))
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIM))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


# --------------------------------------------------------------------------- accounts, keys, plans (mock billing)


class Account(Base):
    """A workspace: owns repositories, MCP keys and a prepaid credit balance (pay as you go, mocked payments)."""

    __tablename__ = "accounts"
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    monthly_limit_cents: Mapped[int] = mapped_column(Integer, default=5000)  # spend cap per calendar month
    payment_method: Mapped[dict[str, Any]] = mapped_column(default=dict)  # mock: {"brand", "last4", "name"}
    auto_recharge: Mapped[dict[str, Any]] = mapped_column(
        default=dict
    )  # {"enabled", "threshold_cents", "amount_cents"}
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    account_id: Mapped[str] = mapped_column(ForeignKey("accounts.id", ondelete="CASCADE"), index=True)
    email: Mapped[str] = mapped_column(String(200), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    password_hash: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class UserSession(Base):
    __tablename__ = "user_sessions"
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ApiKey(Base):
    """MCP / API key, scoped to one repository. Only a hash is stored; the key is shown once."""

    __tablename__ = "api_keys"
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    account_id: Mapped[str] = mapped_column(ForeignKey("accounts.id", ondelete="CASCADE"), index=True)
    repo_id: Mapped[str] = mapped_column(ForeignKey("repos.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(120))  # e.g. "Intercom bot", "Claude Code"
    prefix: Mapped[str] = mapped_column(String(20))  # shown in the UI: "sf_live_ab12…"
    key_hash: Mapped[str] = mapped_column(String(64), unique=True)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class CreditEntry(Base):
    """Credit ledger: balance = sum(amount_cents). Grants and top-ups are positive, usage is negative."""

    __tablename__ = "credit_entries"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_id: Mapped[str] = mapped_column(ForeignKey("accounts.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(20))  # grant | topup | usage | refund
    metric: Mapped[str | None] = mapped_column(String(20), nullable=True)  # ticket | fix | ask | index
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    amount_cents: Mapped[int] = mapped_column(Integer)
    description: Mapped[str] = mapped_column(String(300), default="")
    repo_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    ref: Mapped[str | None] = mapped_column(String(60), nullable=True)  # ticket / job id
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


# --------------------------------------------------------------------------- repositories (code support)


class Repo(Base):
    __tablename__ = "repos"
    id: Mapped[str] = mapped_column(String(120), primary_key=True)  # "owner__name" (or "local__name")
    account_id: Mapped[str | None] = mapped_column(
        ForeignKey("accounts.id", ondelete="CASCADE"), nullable=True, index=True
    )
    full_name: Mapped[str] = mapped_column(String(200))  # owner/name
    source: Mapped[str] = mapped_column(String(20), default="github")  # github | local
    local_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    default_branch: Mapped[str] = mapped_column(String(120), default="main")
    head_sha: Mapped[str | None] = mapped_column(String(64), nullable=True)
    installation_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending | indexing | ready | failed
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    overview: Mapped[str] = mapped_column(Text, default="")  # markdown "explain everything" page
    stats: Mapped[dict[str, Any]] = mapped_column(default=dict)  # languages, file/chunk counts, cost
    settings: Mapped[dict[str, Any]] = mapped_column(default=dict)  # api_base_url, api_token, api_spec_url
    indexed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class RepoFile(Base):
    __tablename__ = "repo_files"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    repo_id: Mapped[str] = mapped_column(ForeignKey("repos.id", ondelete="CASCADE"), index=True)
    path: Mapped[str] = mapped_column(Text)
    language: Mapped[str] = mapped_column(String(30))
    size: Mapped[int] = mapped_column(Integer)
    content_hash: Mapped[str] = mapped_column(String(64))
    content: Mapped[str] = mapped_column(Text)
    outline: Mapped[list[Any]] = mapped_column(default=list)  # [{"symbol", "kind", "line"}]


class RepoDoc(Base):
    """Generated explanations: one repo overview plus one summary per module (directory)."""

    __tablename__ = "repo_docs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    repo_id: Mapped[str] = mapped_column(ForeignKey("repos.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(20))  # overview | module
    key: Mapped[str] = mapped_column(Text)  # module path ("." for overview)
    title: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text)
    input_hash: Mapped[str] = mapped_column(String(64))  # skip regeneration when inputs are unchanged
    generated_by: Mapped[str] = mapped_column(String(20), default="rules")  # llm | rules
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class RepoChunk(Base):
    __tablename__ = "repo_chunks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    repo_id: Mapped[str] = mapped_column(ForeignKey("repos.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(20))  # code | doc | summary | api | ticket
    path: Mapped[str] = mapped_column(Text)
    symbol: Mapped[str] = mapped_column(String(200), default="")
    start_line: Mapped[int] = mapped_column(Integer, default=0)
    end_line: Mapped[int] = mapped_column(Integer, default=0)
    text: Mapped[str] = mapped_column(Text)
    content_hash: Mapped[str] = mapped_column(String(64), index=True)
    embedding_model: Mapped[str] = mapped_column(String(60), index=True)
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIM))


class ApiOperation(Base):
    """Business API operations discovered from an OpenAPI spec; the 'assisted action' toolset."""

    __tablename__ = "api_operations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    repo_id: Mapped[str] = mapped_column(ForeignKey("repos.id", ondelete="CASCADE"), index=True)
    operation_id: Mapped[str] = mapped_column(String(200))
    method: Mapped[str] = mapped_column(String(10))
    path: Mapped[str] = mapped_column(Text)
    summary: Mapped[str] = mapped_column(Text, default="")
    parameters: Mapped[list[Any]] = mapped_column(default=list)  # [{"name", "in", "required", "schema"}]
    body_schema: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    source: Mapped[str] = mapped_column(String(200), default="")  # spec file path or URL


class IndexJob(Base):
    __tablename__ = "index_jobs"
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    repo_id: Mapped[str] = mapped_column(ForeignKey("repos.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(20))  # full | incremental
    trigger: Mapped[str] = mapped_column(String(20), default="manual")  # manual | import | push
    status: Mapped[str] = mapped_column(String(20), default="queued")  # queued | running | done | failed
    commit_sha: Mapped[str | None] = mapped_column(String(64), nullable=True)
    progress: Mapped[dict[str, Any]] = mapped_column(default=dict)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


# --------------------------------------------------------------------------- tickets


class Ticket(Base):
    __tablename__ = "tickets"
    id: Mapped[str] = mapped_column(String(20), primary_key=True)  # T-xxxxxx
    repo_id: Mapped[str] = mapped_column(ForeignKey("repos.id", ondelete="CASCADE"), index=True)
    customer: Mapped[dict[str, Any]] = mapped_column(default=dict)  # name, email, ref (business system id)
    channel: Mapped[str] = mapped_column(String(20), default="web")  # web | mcp | api
    meta: Mapped[dict[str, Any]] = mapped_column(
        default=dict
    )  # handoff from the first-line agent, callback_url
    subject: Mapped[str] = mapped_column(String(200), default="")
    category: Mapped[str | None] = mapped_column(String(30), nullable=True)
    # bug | misunderstanding | assisted_action | feature_request | other
    confidence: Mapped[float | None] = mapped_column(Numeric(4, 3), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="open")
    # open | answered | awaiting_confirmation | fix_in_review | resolved | escalated | failed
    triage: Mapped[dict[str, Any]] = mapped_column(default=dict)
    resolution: Mapped[dict[str, Any]] = mapped_column(
        default=dict
    )  # what happened, for the dashboard + learning
    fix: Mapped[dict[str, Any]] = mapped_column(default=dict)  # branch, pr_number, pr_url, ci, files
    state: Mapped[dict[str, Any]] = mapped_column(default=dict)  # pending confirmation etc.
    learned: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class TicketMessage(Base):
    __tablename__ = "ticket_messages"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticket_id: Mapped[str] = mapped_column(ForeignKey("tickets.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(20))  # customer | agent | system
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class TicketAction(Base):
    """An API call made (or proposed) on the customer's behalf."""

    __tablename__ = "ticket_actions"
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    ticket_id: Mapped[str] = mapped_column(ForeignKey("tickets.id", ondelete="CASCADE"), index=True)
    operation_id: Mapped[str] = mapped_column(String(200))
    method: Mapped[str] = mapped_column(String(10))
    path: Mapped[str] = mapped_column(Text)
    args: Mapped[dict[str, Any]] = mapped_column(default=dict)
    title: Mapped[str] = mapped_column(String(200), default="")
    status: Mapped[str] = mapped_column(String(20))  # proposed | approved | declined | done | failed
    needs_confirmation: Mapped[bool] = mapped_column(Boolean, default=True)
    response: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    verification: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Notification(Base):
    """Business-facing notifications (bug found, PR opened, CI result). Also mirrored to Slack/Discord."""

    __tablename__ = "notifications"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    repo_id: Mapped[str] = mapped_column(ForeignKey("repos.id", ondelete="CASCADE"), index=True)
    ticket_id: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    kind: Mapped[str] = mapped_column(
        String(40)
    )  # bug_reported | pr_opened | ci_passed | ci_failed | escalation …
    title: Mapped[str] = mapped_column(String(300))
    body: Mapped[str] = mapped_column(Text, default="")
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    delivered: Mapped[list[Any]] = mapped_column(default=list)  # ["slack", "discord"]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


# --------------------------------------------------------------------------- observability


class Span(Base):
    """One unit of work in a trace (a ticket run, an index job). Nested through parent_id."""

    __tablename__ = "spans"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    trace_id: Mapped[str] = mapped_column(String(60), index=True)
    parent_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    name: Mapped[str] = mapped_column(String(120))
    kind: Mapped[str] = mapped_column(String(20))  # run | step | llm | embedding | tool | retrieval | http
    status: Mapped[str] = mapped_column(String(10), default="ok")  # ok | error
    attributes: Mapped[dict[str, Any]] = mapped_column(default=dict)
    cost_usd: Mapped[Decimal] = mapped_column(Numeric(12, 6), default=Decimal(0))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)


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
