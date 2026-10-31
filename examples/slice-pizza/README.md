# Slice: pizza delivery API

Slice is a small pizza-delivery service: customers browse the menu, save delivery addresses, place orders,
apply promo codes and cancel orders before they go into the oven.

This repository is the **demo target for Supfeel**: import it, then send support tickets such as
"the app says my address is invalid" (a real bug Supfeel can fix with a pull request),
"why did I pay for delivery?" (a misunderstanding Supfeel explains), or
"the app crashes, can you reorder my last order?" (an assisted action through this API).

## Business rules

- **Delivery fee**: $3.99, **free for orders of $25.00 or more** (subtotal after discounts).
- **Promo codes**: `SLICE10` = 10% off the subtotal; `WELCOME5` = $5 off a customer's first order. One code per order.
- **Opening hours**: orders are accepted 10:00–23:00 store time.
- **Limits**: at most 20 pizzas per order.
- **Cancellation**: allowed while the order is `received` or `confirmed`. Once it is `baking` it can no longer be cancelled.
  Cancelled orders are refunded to the original payment method within 3–5 business days.
- **Addresses**: a street line (number + street, apartment/unit allowed, e.g. `12 Oak St Apt #4B` or `5/2 King Rd`),
  a city and a postal code.

## API

OpenAPI spec: [`openapi.json`](openapi.json) (also served at `/openapi.json`).
Write operations need `Authorization: Bearer $SLICE_API_TOKEN` (default `demo-service-token`).

## Run

```bash
pip install -r requirements.txt
uvicorn slice_api.main:app --reload     # http://localhost:8000/docs
pytest
```

`python -m slice_api.export_openapi` regenerates `openapi.json`.
