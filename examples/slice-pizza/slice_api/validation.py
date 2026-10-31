"""Input validation for addresses and order items."""

import re

MAX_PIZZAS = 20
SIZES = ("small", "medium", "large")

# Street line: house number, then street name words.
_STREET = re.compile(r"^\d+[A-Za-z]?\s+[A-Za-z0-9 .,'-]+$")
_POSTAL = re.compile(r"^[A-Za-z0-9 -]{3,10}$")


class ValidationError(ValueError):
    pass


def validate_address(address: dict) -> dict:
    line1 = (address.get("line1") or "").strip()
    city = (address.get("city") or "").strip()
    postal = (address.get("postal_code") or "").strip()
    if not _STREET.match(line1):
        raise ValidationError("Invalid address: please enter a street number and street name")
    if not city:
        raise ValidationError("Invalid address: city is required")
    if not _POSTAL.match(postal):
        raise ValidationError("Invalid address: postal code looks wrong")
    return {"line1": line1, "city": city, "postal_code": postal}


def validate_items(items: list[dict], menu: dict[str, dict]) -> None:
    if not items:
        raise ValidationError("Your order is empty")
    if sum(i.get("quantity", 0) for i in items) > MAX_PIZZAS:
        raise ValidationError(f"At most {MAX_PIZZAS} pizzas per order")
    for i in items:
        if i.get("pizza_id") not in menu:
            raise ValidationError(f"Unknown pizza {i.get('pizza_id')}")
        if i.get("size") not in SIZES:
            raise ValidationError(f"Unknown size {i.get('size')}")
        if not isinstance(i.get("quantity"), int) or i["quantity"] < 1:
            raise ValidationError("Quantity must be at least 1")
