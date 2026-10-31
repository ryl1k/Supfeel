# Assisted actions

> Status: **done** (Sprint 5). Paths below are real; keep them in sync with the code.

When the customer asks for something the product can do (reorder, cancel, save an address), Supfeel does it
for them through the business's own API, discovered from its OpenAPI spec. Reads run as lookups; the single
write is proposed, confirmed by the customer, executed, and then **verified by reading the resource back**.

## Why
"The app crashes, can you just reorder for me?" is resolved in the chat instead of becoming a human task, and
the read-back proves it actually happened.

## Scope
- In: planning (Claude tool loop or rules), authority rules in code, proposal persistence, confirmation,
  execution, read-back verification, the Slice demo store mounted at `/demo-store`.
- Out: triage and routing (`ticket-resolution`), OpenAPI discovery (`repo-indexing`).

## Success criteria
- No write runs without explicit approval; no call touches another customer's data.
- Every executed write has a `verification` with named checks.
- Works in mock mode for "cancel my latest order" and "repeat my last order" (`plan_rules`).
