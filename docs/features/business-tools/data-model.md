# Data model

> Status: **done** (Sprint 1). Paths below are real; keep them in sync with the code.

| Table | Key columns |
|---|---|
| `customers` | id (`cus_maya`…), name, email, tier (`member`/`guest`), persona (picker blurb), preferences jsonb (`style_tags`, `shoe_size`, `favorite_colors`) |
| `products` | id (`cloud-runner-slate`), name, line, color, price_cents, tags[], final_sale |
| `variants` | sku (`cloud-runner-slate-10-2E`, accessories `-OS`), product_id, size, width (`D`/`2E`/`OS`), stock |
| `orders` | id (`V1042`; exchange `VX-…`, reship `VR-…`), customer_id, status, kind (`standard`/`exchange`/`reship`), parent_order_id, shipping_method, shipping_cents, total_cents, shipping_address jsonb, placed/shipped/delivered/cancelled_at |
| `order_items` | id, order_id, sku, price_cents, comfort_guarantee_used, return_status (`none`/`label_issued`/`returned`) |
| `shipments` | id, order_id, carrier, tracking_no, status, last_scan_at, estimated_delivery, events jsonb |
| `payments` | id, customer_id, order_id / subscription_id, amount_cents, refunded_cents, method, last4, status (`authorized`/`captured`/`refunded`/`partially_refunded`/`voided`) |
| `refunds`, `exchanges`, `return_labels`, `store_credits`, `escalations` | created by write tools; each has a unique `action_id` |
| `action_log` | id (`ACT-…`), conversation_id, tool, args, result, status, needs_confirmation, verified, verification |

Demo personas (`fixtures/demo.json`, dates relative to seed time): Maya (hero, narrow Cloud Runners, 9 days),
Jordan (lost package, 12 days no scan), Alex (duplicate captured charge + authorization-only holds),
Sam (membership renewed 3 days ago, unused), Lee (day-45 return + processing order), Priya (sole separation at 70 days).
