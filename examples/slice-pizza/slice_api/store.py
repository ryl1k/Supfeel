"""In-memory data store with seed data (resettable via POST /admin/reset)."""

import copy
from datetime import UTC, datetime, timedelta

MENU = [
    {"id": "margherita", "name": "Margherita", "prices": {"small": 899, "medium": 1199, "large": 1499}},
    {"id": "pepperoni", "name": "Pepperoni", "prices": {"small": 999, "medium": 1349, "large": 1649}},
    {"id": "funghi", "name": "Funghi", "prices": {"small": 949, "medium": 1249, "large": 1549}},
    {"id": "quattro", "name": "Quattro Formaggi", "prices": {"small": 1099, "medium": 1449, "large": 1799}},
    {"id": "veggie", "name": "Garden Veggie", "prices": {"small": 949, "medium": 1249, "large": 1549}},
]

_now = datetime.now(UTC)

SEED = {
    "customers": {
        "c_maya": {
            "id": "c_maya", "name": "Maya Chen", "email": "maya@example.com",
            "addresses": [{"id": "a1", "label": "Home", "line1": "48 Elm Street", "city": "Springfield", "postal_code": "10001"}],
        },
        "c_jordan": {
            "id": "c_jordan", "name": "Jordan Blake", "email": "jordan@example.com",
            "addresses": [{"id": "a2", "label": "Work", "line1": "200 Market Ave", "city": "Springfield", "postal_code": "10002"}],
        },
    },
    "orders": {
        "o_1001": {
            "id": "o_1001", "customer_id": "c_jordan", "status": "delivered",
            "items": [{"pizza_id": "pepperoni", "size": "large", "quantity": 1}, {"pizza_id": "margherita", "size": "medium", "quantity": 1}],
            "address": {"line1": "200 Market Ave", "city": "Springfield", "postal_code": "10002"},
            "subtotal_cents": 2848, "discount_cents": 0, "delivery_fee_cents": 0, "total_cents": 2848, "promo_code": None,
            "created_at": (_now - timedelta(days=3)).isoformat(),
        },
        "o_1002": {
            "id": "o_1002", "customer_id": "c_maya", "status": "delivered",
            "items": [{"pizza_id": "veggie", "size": "medium", "quantity": 2}],
            "address": {"line1": "48 Elm Street", "city": "Springfield", "postal_code": "10001"},
            "subtotal_cents": 2498, "discount_cents": 0, "delivery_fee_cents": 399, "total_cents": 2897, "promo_code": None,
            "created_at": (_now - timedelta(days=1)).isoformat(),
        },
    },
}  # fmt: skip

DB: dict = {}


def reset() -> None:
    DB.clear()
    DB.update(copy.deepcopy(SEED))
    DB["seq"] = 1003


reset()
