"""Slice HTTP API."""

import os
from datetime import UTC, datetime

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from slice_api import pricing, store, validation

app = FastAPI(
    title="Slice API",
    version="1.0.0",
    description="Pizza delivery: menu, customers, addresses and orders.",
)
CANCELLABLE = ("received", "confirmed")


def require_service_token(authorization: str = Header(default="")) -> None:
    token = os.environ.get("SLICE_API_TOKEN", "demo-service-token")
    if authorization != f"Bearer {token}":
        raise HTTPException(status_code=401, detail="missing or invalid service token")


class Item(BaseModel):
    pizza_id: str
    size: str = Field(description="small | medium | large")
    quantity: int = 1


class Address(BaseModel):
    line1: str = Field(description="Street number and name, apartment/unit allowed")
    city: str
    postal_code: str


class NewAddress(Address):
    label: str = "Home"


class NewOrder(BaseModel):
    customer_id: str
    items: list[Item]
    address: Address
    promo_code: str | None = None


def _menu() -> dict[str, dict]:
    return {p["id"]: p for p in store.MENU}


def _customer(customer_id: str) -> dict:
    c = store.DB["customers"].get(customer_id)
    if c is None:
        raise HTTPException(status_code=404, detail="customer not found")
    return c


def _order(order_id: str) -> dict:
    o = store.DB["orders"].get(order_id)
    if o is None:
        raise HTTPException(status_code=404, detail="order not found")
    return o


@app.get("/menu", operation_id="list_menu", summary="List pizzas with prices per size")
def list_menu() -> list[dict]:
    return store.MENU


@app.get("/customers/{customer_id}", operation_id="get_customer", summary="Get a customer profile with saved addresses")
def get_customer(customer_id: str) -> dict:
    return _customer(customer_id)


@app.get("/customers/{customer_id}/orders", operation_id="list_customer_orders", summary="List a customer's orders, newest first")
def list_customer_orders(customer_id: str) -> list[dict]:
    _customer(customer_id)
    orders = [o for o in store.DB["orders"].values() if o["customer_id"] == customer_id]
    return sorted(orders, key=lambda o: o["created_at"], reverse=True)


@app.post(
    "/customers/{customer_id}/addresses",
    operation_id="add_address",
    summary="Save a delivery address for a customer",
    dependencies=[Depends(require_service_token)],
    status_code=201,
)
def add_address(customer_id: str, body: NewAddress) -> dict:
    c = _customer(customer_id)
    try:
        clean = validation.validate_address(body.model_dump())
    except validation.ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    addr = {"id": f"a{len(c['addresses']) + 10}", "label": body.label, **clean}
    c["addresses"].append(addr)
    return addr


@app.post(
    "/orders",
    operation_id="create_order",
    summary="Place an order for a customer",
    dependencies=[Depends(require_service_token)],
    status_code=201,
)
def create_order(body: NewOrder) -> dict:
    _customer(body.customer_id)
    items = [i.model_dump() for i in body.items]
    try:
        validation.validate_items(items, _menu())
        address = validation.validate_address(body.address.model_dump())
        previous = sum(1 for o in store.DB["orders"].values() if o["customer_id"] == body.customer_id)
        totals = pricing.price(items, _menu(), body.promo_code, previous)
    except (validation.ValidationError, pricing.PromoError) as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    order_id = f"o_{store.DB['seq']}"
    store.DB["seq"] += 1
    order = {
        "id": order_id, "customer_id": body.customer_id, "status": "received", "items": items, "address": address,
        **totals, "promo_code": body.promo_code, "created_at": datetime.now(UTC).isoformat(),
    }  # fmt: skip
    store.DB["orders"][order_id] = order
    return order


@app.get("/orders/{order_id}", operation_id="get_order", summary="Get one order")
def get_order(order_id: str) -> dict:
    return _order(order_id)


@app.post(
    "/orders/{order_id}/cancel",
    operation_id="cancel_order",
    summary="Cancel an order that is not baking yet (refund to original payment)",
    dependencies=[Depends(require_service_token)],
)
def cancel_order(order_id: str) -> dict:
    o = _order(order_id)
    if o["status"] not in CANCELLABLE:
        raise HTTPException(status_code=409, detail=f"order is {o['status']} and can no longer be cancelled")
    o["status"] = "cancelled"
    o["refund_cents"] = o["total_cents"]
    return o


@app.post("/admin/reset", operation_id="reset_demo_data", include_in_schema=False)
def reset() -> dict:
    store.reset()
    return {"status": "reset"}
