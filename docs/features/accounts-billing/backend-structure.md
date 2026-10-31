# Backend structure

> Status: **done** (Sprint 6). Paths below are real; keep them in sync with the code.

```
backend/app/accounts/
  context.py   current_account ContextVar: the account work is billed to (read by app/llm/ledger.py)
  auth.py      hash_password / verify_password (scrypt), signup(), login(), logout(), _new_session(),
               principal_from_token(), Principal (is_admin), require_principal → CurrentPrincipal,
               repo_for(), KEY_PREFIX "sf_live_", create_key / list_keys / revoke_key, KeyContext,
               resolve_key(), me()
  billing.py   FREE_GRANT_CENTS, MIN/MAX_TOPUP_CENTS, DECLINED_TEST_CARD, Price, PRICES, PaymentRequired
               (reason balance | monthly_limit | declined), month_start / next_month_start,
               balance_cents, month_spend_cents, grant, _auto_recharge, charge, refund, topup, summary,
               statement, update_settings, mock_card
backend/app/api/accounts.py   /api/auth/*, /api/me, /api/billing*, key routes
backend/app/db/models.py      Account, User, UserSession, ApiKey, CreditEntry; Repo.account_id, LlmUsage.account_id
backend/app/db/seed.py        init_db(): create_all + idempotent ALTER TABLE ... ADD COLUMN IF NOT EXISTS
                              (repos.account_id, llm_usage.account_id + index, tickets.channel, tickets.meta)
```
Charge call sites: `support/service.py:open_ticket`, `support/graph.py:fix_node`,
`api/repos.py:import_repo` / `reindex` / `ask_repo`, `mcp_server.py:ask_product`.
