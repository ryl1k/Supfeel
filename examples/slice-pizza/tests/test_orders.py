import pytest
from fastapi.testclient import TestClient

from slice_api import store
from slice_api.main import app

client = TestClient(app)
AUTH = {"Authorization": "Bearer demo-service-token"}
ADDRESS = {"line1": "48 Elm Street", "city": "Springfield", "postal_code": "10001"}


@pytest.fixture(autouse=True)
def _reset():
    store.reset()


def order(items, promo=None, customer="c_maya", address=ADDRESS):
    return client.post(
        "/orders", json={"customer_id": customer, "items": items, "address": address, "promo_code": promo}, headers=AUTH
    )


def test_menu():
    assert len(client.get("/menu").json()) == 5


def test_create_order_with_delivery_fee():
    r = order([{"pizza_id": "margherita", "size": "small", "quantity": 1}])
    assert r.status_code == 201
    assert r.json()["delivery_fee_cents"] == 399
    assert r.json()["total_cents"] == 899 + 399


def test_large_order_has_free_delivery():
    r = order([{"pizza_id": "quattro", "size": "large", "quantity": 2}])
    assert r.json()["delivery_fee_cents"] == 0


def test_promo_percent():
    r = order([{"pizza_id": "pepperoni", "size": "large", "quantity": 2}], promo="SLICE10")
    assert r.json()["discount_cents"] == 3298 // 10


def test_welcome_promo_only_first_order():
    r = order([{"pizza_id": "veggie", "size": "small", "quantity": 1}], promo="WELCOME5")
    assert r.status_code == 422


def test_requires_token():
    r = client.post("/orders", json={"customer_id": "c_maya", "items": [], "address": ADDRESS})
    assert r.status_code == 401


def test_cancel_and_refund():
    o = order([{"pizza_id": "funghi", "size": "medium", "quantity": 1}]).json()
    r = client.post(f"/orders/{o['id']}/cancel", headers=AUTH)
    assert r.json()["status"] == "cancelled"
    assert r.json()["refund_cents"] == o["total_cents"]


def test_cannot_cancel_delivered():
    assert client.post("/orders/o_1002/cancel", headers=AUTH).status_code == 409


def test_rejects_address_without_number():
    r = order([{"pizza_id": "funghi", "size": "small", "quantity": 1}], address={**ADDRESS, "line1": "Elm Street"})
    assert r.status_code == 422


def test_max_pizzas():
    r = order([{"pizza_id": "funghi", "size": "small", "quantity": 21}])
    assert r.status_code == 422
