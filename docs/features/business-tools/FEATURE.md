# Business tools (mock Velora systems)

> Status: **done** (Sprint 1). Paths below are real; keep them in sync with the code.

A mock of the systems a real store would expose — customers, orders, shipments, payments, products,
memberships — plus the read/write tools the agent uses to act on them.

## Why
Supfeel's value is *doing* things. Tools must change real (mock) state so verification is meaningful
and the demo is believable.

## Scope
- In: Postgres schema, seed fixtures aligned with KB policies, typed tool functions, demo reset.
- Out: decision-making (agent), policy text (KB).

## Success criteria
- Every tool has a pydantic input/output schema and a unit test.
- `/api/admin/reset` restores the exact demo state in < 2 s.
