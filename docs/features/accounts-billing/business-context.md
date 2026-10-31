# Business context

> Status: **done** (Sprint 6). Paths below are real; keep them in sync with the code.

- Prices (`billing.PRICES`, cents): `ticket` 15 (escalated ticket), `fix` 100 (fix agent run), `ask` 2
  (knowledge question), `index` 10 (import or re-index). Debited **when the unit starts**.
- Where charges happen: `service.open_ticket` (`ticket`, web and MCP), `graph.fix_node` (`fix`, refunded with
  `billing.refund` when the fix agent falls back to `report` because Claude is unavailable),
  `api/repos.py` `import_repo` / `reindex` (`index`) and `ask_repo` (`ask`), `mcp_server.ask_product` (`ask`).
  Push-triggered re-index (`api/github.py`) is not charged.
- `charge(account_id=None)` is free: operator (admin token) and legacy repos without an account.
- New workspaces get `FREE_GRANT_CENTS` (500 = $5) as a `grant` entry ("Welcome credit").
- Monthly spend limit: `accounts.monthly_limit_cents` (default 5000 = $50), checked before the balance.
  Spend = −sum of `usage` + `refund` entries since `month_start()` (UTC), so refunds net out. Resets on the 1st.
- Top-ups: `MIN_TOPUP_CENTS` 500 to `MAX_TOPUP_CENTS` 50 000. Payments are mocked (`mock_card`): any 12+
  digits; brand from the first digit (4 Visa, 5 Mastercard); `4000 0000 0000 0002` is declined (HTTP 402).
- Auto-recharge (`accounts.auto_recharge {enabled, threshold_cents, amount_cents}`, needs a saved card): when
  `balance − cost < threshold`, a `topup` of `max(amount, cost)` is added before the charge.
- Passwords ≥ 8 chars, scrypt (n=2^14, r=8, p=1). Sessions last `SESSION_DAYS` (30). Emails are lower-cased and unique.
- `ADMIN_TOKEN` (`x-admin-token`) is an operator override: sees every account, cannot use billing endpoints.
