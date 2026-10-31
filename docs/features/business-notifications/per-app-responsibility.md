# Per-app responsibility

> Status: **done** (Sprint 5). Paths below are real; keep them in sync with the code.

| App | Responsibility |
|---|---|
| backend | `notify()`, delivery, storage, inbox API |
| Neon DB | `notifications` |
| Telegram / Slack / Discord | Optional mirrors (bot API / incoming webhooks) |
| frontend | `/app/inbox` list and per-ticket "Business notifications" card |
