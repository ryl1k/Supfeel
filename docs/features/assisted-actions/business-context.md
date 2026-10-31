# Business context

> Status: **done** (Sprint 5). Paths below are real; keep them in sync with the code.

Authority rules, enforced in `backend/app/support/assist.py` (never only in prompts):
- **Only spec operations**: `_op()` rejects any `operation_id` not in `api_operations`.
- **Customer scoping**: `scope_to_customer()` forces every `CUSTOMER_FIELDS` value (`customer_id`, `customerId`,
  `user_id`, `userId`, `account_id`, `accountId`) in path, query or body to the ticket's `customer.ref`. A different
  value → `ActionBlocked`. An operation that takes a customer field with no known ref → blocked.
- **Ownership read-back**: `check_ownership()` GETs the resource a write targets (`readback_op()`, e.g.
  `/orders/{order_id}/cancel` → `/orders/{order_id}`) and blocks if its owner field is someone else.
- **Confirmation**: lookups (GET) run immediately; every write is `needs_confirmation=True` and waits for the customer.
- **MAX_WRITES = 3** executed writes per ticket; then a human takes over. `MAX_PLAN_TURNS = 6` planning turns.
- **Verification**: after a write, `verify()` reads the resource back and compares scalar fields from the write
  response (≤ 8 checks). No read-back possible → verification fails → escalation.
- Needs `repos.settings.api_base_url` (+ optional `api_token`, sent as `Bearer`). Without it, assist escalates.

Demo store (Slice, `examples/slice-pizza`): writes need `Bearer demo-service-token` (`SLICE_API_TOKEN`);
cancel only while `received`/`confirmed`; data is in memory and resets on restart.
