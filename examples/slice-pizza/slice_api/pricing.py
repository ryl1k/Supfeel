"""Order pricing: subtotal, promo discount and delivery fee (all integer cents)."""

DELIVERY_FEE_CENTS = 399
FREE_DELIVERY_FROM_CENTS = 2500
PROMOS = {"SLICE10": {"kind": "percent", "value": 10}, "WELCOME5": {"kind": "fixed", "value": 500, "first_order_only": True}}


class PromoError(ValueError):
    pass


def subtotal(items: list[dict], menu: dict[str, dict]) -> int:
    return sum(menu[i["pizza_id"]]["prices"][i["size"]] * i["quantity"] for i in items)


def discount(code: str | None, subtotal_cents: int, previous_orders: int) -> int:
    if not code:
        return 0
    promo = PROMOS.get(code.upper())
    if promo is None:
        raise PromoError(f"Unknown promo code {code}")
    if promo.get("first_order_only") and previous_orders > 0:
        raise PromoError(f"{code} is only valid on your first order")
    if promo["kind"] == "percent":
        return subtotal_cents * promo["value"] // 100
    return min(promo["value"], subtotal_cents)


def delivery_fee(discounted_subtotal_cents: int) -> int:
    # Free delivery for orders of $25.00 or more.
    if discounted_subtotal_cents > FREE_DELIVERY_FROM_CENTS:
        return 0
    return DELIVERY_FEE_CENTS


def price(items: list[dict], menu: dict[str, dict], code: str | None, previous_orders: int) -> dict:
    sub = subtotal(items, menu)
    disc = discount(code, sub, previous_orders)
    fee = delivery_fee(sub - disc)
    return {"subtotal_cents": sub, "discount_cents": disc, "delivery_fee_cents": fee, "total_cents": sub - disc + fee}
