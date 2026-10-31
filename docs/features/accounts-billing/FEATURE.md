# Accounts and billing

> Status: **done** (Sprint 6). Paths below are real; keep them in sync with the code.

Businesses sign up with email + password and get a **workspace** (account) that owns repositories, MCP keys
and a prepaid credit balance. Billing is **pay as you go** with mocked payments: a $5 welcome grant, priced
units debited when they start, top-ups by (mock) card, a monthly spend limit that resets on the 1st (UTC),
and optional auto-recharge. Every Claude/OpenAI call is attributed to the workspace for margin tracking.

## Why
A multi-tenant product needs tenancy (who owns which repo and ticket) and a way to stop runaway spend.
Pay as you go fits support volume, which is spiky; prepaid credit keeps the demo safe without real payments.

## Scope
- In: signup / login / logout / `me`, scrypt passwords, bearer session tokens, admin-token operator override,
  `repo_for` scoping, API key generation, price list, ledger, charge / refund / top-up / auto-recharge,
  monthly limit, mock cards, AI-cost attribution (`llm_usage.account_id`), Billing page, session guard.
- Out: real payment processing, invoices, team members / roles (one user per workspace), email verification,
  password reset.

## Success criteria
- `backend/tests/test_billing.py` passes: welcome credit, charges and statement, balance and monthly limit,
  declined card, auto-recharge, month boundaries, refunds reduce month spend.
- Out-of-credit is always a clear message (HTTP 402 on REST, `ToolError` over MCP, a "fix skipped" step in the graph).
- A signed-in user only ever sees their own workspace's repos, tickets, keys and notifications.
