# Data model

> Status: **planned**. Paths below are the agreed target layout; no code yet. Update when implemented.

| Table | Key columns |
|---|---|
| `customers` | id, name, email, tier (`member`/`guest`), preferences jsonb (style tags, sizes) |
| `products` | id, sku, name, line, color, size, width, price_cents, stock, tags text[] |
| `orders` | id, customer_id, status (`processing`/`shipped`/`delivered`/`cancelled`), total_cents, placed_at, delivered_at, shipping_address jsonb |
| `order_items` | id, order_id, product_id, qty, price_cents, comfort_guarantee_used bool |
| `shipments` | id, order_id, carrier, tracking_no, status, last_scan_at, events jsonb |
| `payments` | id, order_id, amount_cents, method, last4, status (`authorized`/`captured`/`refunded`), created_at |
| `refunds` | id, payment_id, amount_cents, method (`original`/`store_credit`), status (`issued`) |
| `exchanges` | id, original_item_id, new_order_id, price_diff_cents, status |
| `return_labels` | id, order_item_id, carrier, status (`active`/`expired`/`used`), expires_at |
| `store_credits` | id, customer_id, amount_cents, reason |
| `subscriptions` | id, customer_id, plan (`monthly`/`annual`), status (`active`/`paused`/`cancelled`), renewed_at, paused_until, pause_used_at |
| `escalations` | id, conversation_id, reason, summary, status |
