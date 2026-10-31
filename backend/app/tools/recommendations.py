"""Personalized replacement suggestions.

Local tag-similarity ranking over the catalog, weighted by the customer's stated style preferences
and the fit problem. Qloo taste intelligence is an optional future provider (QLOO_API_KEY); it is not
called yet, so results always report provider "velora-taste".
"""

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict
from sqlalchemy import select

from app.db.models import Customer, Product, Variant
from app.tools.base import ToolContext, ToolError, money

FitProblem = Literal["narrow", "wide", "short", "long", "arch", "stiff", "other"]


class RecommendationArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")
    product_id: str
    size: float
    fit_problem: FitProblem = "other"
    limit: int = 3


def _target_size_and_width(size: float, width: str, problem: str) -> tuple[float, str]:
    if problem == "narrow":
        return size, "2E"
    if problem == "wide":
        return size, "D"
    if problem == "short":
        return size + 0.5, width
    if problem == "long":
        return size - 0.5, width
    return size, width


def _fit_bonus(product: Product, problem: str) -> float:
    if problem == "arch" and "arch-support" in product.tags:
        return 2.0
    if problem == "stiff" and "cushioned" in product.tags:
        return 2.0
    if problem == "narrow" and "high-volume" in product.tags:
        return 0.5
    return 0.0


async def get_recommendations(ctx: ToolContext, args: RecommendationArgs) -> dict:
    current = await ctx.session.get(Product, args.product_id)
    if current is None:
        raise ToolError("product_not_found", f"Unknown product {args.product_id}.")
    customer = await ctx.session.get(Customer, ctx.customer_id)
    style = set((customer.preferences or {}).get("style_tags", [])) if customer else set()
    fav_colors = set((customer.preferences or {}).get("favorite_colors", [])) if customer else set()
    current_width = "D"
    size, width = _target_size_and_width(args.size, current_width, args.fit_problem)

    rows = (
        await ctx.session.execute(
            select(Variant, Product)
            .join(Product, Product.id == Variant.product_id)
            .where(Variant.stock > 0, Variant.size == Decimal(str(size)), Variant.width == width)
        )
    ).all()
    scored = []
    for v, p in rows:
        if p.line == "Accessories":
            continue
        tags = set(p.tags)
        score = (
            len(tags & set(current.tags)) * 1.0
            + len(tags & style) * 1.5
            + (1.0 if p.color in fav_colors else 0.0)
            + (3.0 if p.line == current.line else 0.0)
            + (1.0 if p.id == current.id else 0.0)
            + _fit_bonus(p, args.fit_problem)
        )
        why = []
        if p.id == current.id:
            why.append("same shoe you chose, in a better fit")
        elif p.line == current.line:
            why.append(f"same {p.line} feel in {p.color}")
        if tags & style:
            why.append("matches your " + ", ".join(sorted(tags & style)) + " style")
        if width == "2E":
            why.append("wide (2E) fit")
        scored.append(
            (
                score,
                {
                    "sku": v.sku,
                    "product_id": p.id,
                    "name": p.name,
                    "color": p.color,
                    "size": float(v.size),
                    "width": v.width,
                    "price": money(p.price_cents),
                    "price_cents": p.price_cents,
                    "reason": "; ".join(why) or "similar style",
                },
            )
        )
    scored.sort(key=lambda x: -x[0])
    return {
        "provider": "velora-taste",
        "target": {"size": size, "width": width},
        "recommendations": [r for _, r in scored[: args.limit]],
    }
