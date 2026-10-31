"""Persistent usage ledger (llm_usage table) and spend caps."""

from decimal import Decimal

from sqlalchemy import func, select

from app.accounts.context import current_account
from app.config import get_settings
from app.db.models import LlmUsage
from app.db.session import session_scope
from app.llm.pricing import cost_usd
from app.obs import trace


class BudgetExceeded(RuntimeError):
    """Raised before a call that would push spend past a configured cap."""


async def record(
    *,
    provider: str,
    model: str,
    node: str,
    mode: str,
    conversation_id: str | None = None,
    input_tokens: int = 0,
    output_tokens: int = 0,
    cache_write_tokens: int = 0,
    cache_read_tokens: int = 0,
    annotate: bool = True,
) -> float:
    cost = cost_usd(model, input_tokens, output_tokens, cache_write_tokens, cache_read_tokens)
    async with session_scope() as s:
        s.add(
            LlmUsage(
                provider=provider,
                model=model,
                node=node,
                mode=mode,
                conversation_id=conversation_id,
                account_id=current_account.get(),
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cache_write_tokens=cache_write_tokens,
                cache_read_tokens=cache_read_tokens,
                cost_usd=Decimal(str(round(cost, 6))),
            )
        )
    if annotate:
        trace.annotate_usage(
            cost,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cache_read_tokens=cache_read_tokens,
            cache_write_tokens=cache_write_tokens,
        )
    return cost


async def total_spend(provider: str, conversation_id: str | None = None) -> float:
    stmt = select(func.coalesce(func.sum(LlmUsage.cost_usd), 0)).where(
        LlmUsage.provider == provider, LlmUsage.mode == "live"
    )
    if conversation_id is not None:
        stmt = stmt.where(LlmUsage.conversation_id == conversation_id)
    async with session_scope() as s:
        return float(await s.scalar(stmt))


async def check_caps(
    provider: str, estimate_usd: float, conversation_id: str | None = None, session_cap: float | None = None
) -> None:
    settings = get_settings()
    if provider == "anthropic":
        total = await total_spend("anthropic")
        if total + estimate_usd > settings.llm_budget_hard_cap_usd:
            raise BudgetExceeded(
                f"Claude hard cap ${settings.llm_budget_hard_cap_usd:.2f} reached (spent ${total:.4f})"
            )
        if conversation_id:
            session_total = await total_spend("anthropic", conversation_id)
            cap = settings.llm_session_cap_usd if session_cap is None else session_cap
            if session_total + estimate_usd > cap:
                raise BudgetExceeded(f"Session cap ${cap:.2f} reached for {conversation_id}")
    elif provider == "openai":
        total = await total_spend("openai")
        if total + estimate_usd > settings.embedding_budget_hard_cap_usd:
            raise BudgetExceeded(f"Embedding cap ${settings.embedding_budget_hard_cap_usd:.2f} reached")


async def summary() -> dict:
    """Totals by provider, node and mode, plus configured caps."""
    settings = get_settings()
    async with session_scope() as s:
        rows = (
            await s.execute(
                select(
                    LlmUsage.provider,
                    LlmUsage.node,
                    LlmUsage.mode,
                    func.count(),
                    func.sum(LlmUsage.input_tokens),
                    func.sum(LlmUsage.output_tokens),
                    func.sum(LlmUsage.cache_read_tokens),
                    func.sum(LlmUsage.cache_write_tokens),
                    func.sum(LlmUsage.cost_usd),
                ).group_by(LlmUsage.provider, LlmUsage.node, LlmUsage.mode)
            )
        ).all()
    breakdown = [
        {
            "provider": r[0],
            "node": r[1],
            "mode": r[2],
            "calls": r[3],
            "input_tokens": int(r[4] or 0),
            "output_tokens": int(r[5] or 0),
            "cache_read_tokens": int(r[6] or 0),
            "cache_write_tokens": int(r[7] or 0),
            "cost_usd": float(r[8] or 0),
        }
        for r in rows
    ]
    live = [b for b in breakdown if b["mode"] == "live"]
    return {
        "anthropic_usd": round(sum(b["cost_usd"] for b in live if b["provider"] == "anthropic"), 4),
        "openai_usd": round(sum(b["cost_usd"] for b in live if b["provider"] == "openai"), 4),
        "caps": {
            "anthropic_hard_cap_usd": settings.llm_budget_hard_cap_usd,
            "session_cap_usd": settings.llm_session_cap_usd,
            "openai_hard_cap_usd": settings.embedding_budget_hard_cap_usd,
        },
        "breakdown": breakdown,
    }
