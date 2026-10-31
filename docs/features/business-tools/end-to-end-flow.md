# End-to-end flow

> Status: **planned**. Paths below are the agreed target layout; no code yet. Update when implemented.

1. Agent calls `registry.call("create_exchange", {...})`.
2. Registry validates input (pydantic) → runs tool in a DB transaction → writes `action_log`.
3. Tool returns typed output or `ToolError{code, message}`.
4. Verifier re-reads via read tools (`get_order(exchange_order_id)`) and checks expected fields.
5. Demo reset: `POST /api/admin/reset` truncates business tables and reloads `fixtures/*.json`.
