# Known gotchas

> Status: **done** (Sprint 5). Paths below are real; keep them in sync with the code.

- The customer `ref` is whatever the support page sends. Scoping and ownership are only as strong as that
  identity; a real deployment needs an authenticated/signed customer id.
- Ownership is only checked for **writes**. GET lookups with a resource id (e.g. `/orders/{order_id}`) are not
  ownership-checked unless they take a customer field.
- `check_ownership` allows the write when the read-back fails or the resource has no recognised owner field.
- A write with no matching GET (`readback_op` is None) can never verify (`len(checks) > 1` is required), so it is
  escalated even if the API accepted it.
- Mock mode uses `plan_rules`: it only handles cancel-latest and repeat-last, and assumes the list operation
  returns newest first.
- The demo store is in memory: a Render restart or sleep resets orders. `/demo-store/admin/reset` is unauthenticated.
- The backend calls its own `/demo-store` over the public URL in production, so a cold instance can time out the first call (20 s).
- `assist.transport` is a module-level test hook; tests set it to an `ASGITransport` over the Slice app.
- `repos.settings.api_token` is stored in plain text (only masked in API responses).
