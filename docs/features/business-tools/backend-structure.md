# Backend structure

> Status: **planned**. Paths below are the agreed target layout; no code yet. Update when implemented.

```
backend/app/tools/
  schemas.py    pydantic In/Out models per tool, ToolError
  read.py       get_customer, list_orders, get_order, get_shipment, get_payments,
                get_subscription, search_products
  write.py      create_refund, create_exchange, create_return_label, reship_order, cancel_order,
                update_address, issue_store_credit, pause_subscription, cancel_subscription,
                escalate_to_human
  registry.py   name → (fn, In, Out, kind=read|write); call(); to_claude_tool_defs() (sorted, stable)
  recommendations.py  get_recommendations: Qloo if QLOO_API_KEY else tag-similarity fallback
backend/app/db/
  models.py  session.py  seed.py  fixtures/*.json
```
