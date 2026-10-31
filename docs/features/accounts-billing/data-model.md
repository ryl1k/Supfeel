# Data model

> Status: **done** (Sprint 6). Paths below are real; keep them in sync with the code.

| Table | Key columns |
|---|---|
| `accounts` | id (`acc_<hex>`), name, monthly_limit_cents (default 5000), payment_method JSONB `{brand, last4, name}`, auto_recharge JSONB `{enabled, threshold_cents, amount_cents}`, created_at |
| `users` | id (`usr_<hex>`), account_id → accounts (cascade), email (unique), name, password_hash (`scrypt$<salt>$<digest>`) |
| `user_sessions` | token_hash (sha256, PK), user_id → users (cascade), expires_at |
| `api_keys` | id (`key_<hex>`), account_id, repo_id → repos (cascade), name, prefix, key_hash (sha256, unique), last_used_at, revoked |
| `credit_entries` | id, account_id, kind (`grant`/`topup`/`usage`/`refund`), metric (`ticket`/`fix`/`ask`/`index`), quantity, amount_cents (+ credit / − usage), description, repo_id, ref (ticket / job id), created_at (indexed) |
| `repos` | + account_id → accounts (nullable; null = legacy / operator) |
| `llm_usage` | + account_id (nullable, indexed) |

Balance = `sum(amount_cents)`. Month spend = −`sum(amount_cents)` of `usage` + `refund` since the 1st (UTC).
Migrations: `init_db()` in `backend/app/db/seed.py` runs `create_all`, then `ALTER TABLE … ADD COLUMN IF NOT EXISTS`
for the columns added to existing tables.
