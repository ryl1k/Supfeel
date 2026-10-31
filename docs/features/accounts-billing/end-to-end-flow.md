# End-to-end flow

> Status: **done** (Sprint 6). Paths below are real; keep them in sync with the code.

**Signup** (`/signup` → `POST /api/auth/signup {email, name, password, company}`): `auth.signup` checks the
email is free, creates `accounts` (`acc_<hex>`, name = company or "<name>'s workspace") + `users`
(`usr_<hex>`, scrypt hash), grants $5, creates a `user_sessions` row (sha256 of a random token) and returns
`{token, user, account, admin}`. 409 if the email exists. The browser stores the token (`setSessionToken`)
and goes to `/app/welcome` (or `?next=`).

**Login** → `auth.login` (401 "wrong email or password") → `/app`. **Logout** deletes the session row.

**Every dashboard request**: `call()` in `frontend/lib/workspace.ts` adds `Authorization: Bearer <token>`.
`require_principal` (FastAPI dependency `CurrentPrincipal`): admin token → `Principal(None)`; else the session
must exist and not be expired → `Principal(account_id, user_id, email)`; else 401. A 401 clears the stored token
and `Shell` redirects to `/login?next=…`. Per-repo routes call `repo_for(principal, repo_id)` → 404 unless
the repo belongs to the account (or the caller is admin).

**Charge** (`billing.charge(account_id, metric, ...)`):
1. No account → free (returns 0).
2. `month_spend_cents + cost > monthly_limit_cents` → `PaymentRequired("monthly_limit", …resets on <Mon 1>…)`.
3. `_auto_recharge` may add a `topup`. Then `balance < cost` → `PaymentRequired("balance", "Not enough credit …")`.
4. Insert a `usage` entry (−cost, metric, quantity, repo_id, ref).
Callers map `PaymentRequired`: REST → 402, `open_ticket` → `TicketError` (SSE `error` / MCP `ToolError`),
`fix_node` → the fix is skipped and `report_only()` runs ("Automatic fix skipped (…)").

**Refund**: `fix_node` charges `fix`, runs `fixer.investigate`; if the result is `report` (Claude unavailable /
cap) it adds a `refund` entry (+100, quantity −1).

**Billing page**: `GET /api/billing` (summary + last 100 statement rows); `POST /api/billing/topup
{amount_cents, card?}` (card optional when one is saved; a new card is saved); `PUT /api/billing/card`;
`PATCH /api/billing/settings {monthly_limit_cents?, auto_recharge_*?}`. All return the fresh billing view.

**AI-cost attribution**: entry points set `current_account` (`service._drive`, `indexer` job, `repos.ask.ask`);
`llm/ledger.py` writes it into `llm_usage.account_id`; `billing.summary` sums live `cost_usd` for the month (`ai_cost_usd`).
