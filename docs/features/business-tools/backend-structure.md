# Backend structure

> Status: **done** (Sprint 1). Paths below are real; keep them in sync with the code.

```
backend/app/tools/
  base.py             ToolContext(session, customer_id, conversation_id, action_id), ToolError, money/date helpers
  read.py             get_customer, list_orders, get_order, get_shipment (delayed/lost assessment),
                      get_payments (duplicate flag), get_subscription, search_products  + their arg models
  write.py            create_refund, create_exchange, create_return_label, reship_order, cancel_order,
                      update_address, issue_store_credit, pause_subscription, cancel_subscription,
                      escalate_to_human  + their arg models (pydantic, extra=forbid)
  recommendations.py  get_recommendations: local taste ranking (style tags, favorite colors, fit problem)
  verify.py           per-tool read-back verifiers (fresh DB session) → {ok, checks[]}
  registry.py         TOOLS specs; call_read(); propose() → action_id; execute(action_id) (idempotent,
                      validates, runs in a transaction, verifies, writes action_log); tool_catalog()
backend/app/db/
  models.py  session.py  seed.py (init_db, reset_demo)  fixtures/catalog.json  fixtures/demo.json
```
Write flow: `propose()` logs `action_log(status=proposed)` → `execute()` runs once, then `verify()`;
re-executing a `done` action returns the stored result (`replayed: true`).
