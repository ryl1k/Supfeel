# Known gotchas

> Status: **done** (Sprint 6). Paths below are real; keep them in sync with the code.

- **Balance and limit checks are not transactional.** `charge` reads spend and balance, then inserts in a
  separate session, so concurrent charges can overdraw slightly. Acceptable for a demo.
- **Monthly spend nets refunds** (`kind in (usage, refund)`), so a refunded fix frees its $1.00 of the limit again.
- Charges happen up front: a ticket whose turn later crashes, or an import whose job fails, is not refunded.
  Only `fix` is refunded, and only for the `report` fallback.
- Auto-recharge runs only inside `charge` (never on a schedule), and top-ups don't count toward the monthly
  limit: only `usage` and `refund` entries do.
- Expired `user_sessions` rows are rejected but never deleted.
- Session tokens live in `localStorage` (not httpOnly cookies): fine for the demo, XSS-sensitive in production.
- No migrations framework: new columns rely on `init_db`'s `ADD COLUMN IF NOT EXISTS` list. Indexes declared on
  models (e.g. `repos.account_id`) are only created for new tables, not by the `ALTER`.
- **Stale Turbopack modules**: after adding `api.signup` to `lib/workspace.ts`, the dev server kept serving the
  old module (`api.signup is not a function`) until it was restarted.
- The admin token principal has `account_id=None`: billing endpoints return 400 for it, and `charge(None, …)` is free.
