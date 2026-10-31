# End-to-end flow

> Status: **done** (Sprint 5). Paths below are real; keep them in sync with the code.

`notify(repo_id, kind, title, body="", url=None, ticket_id=None)`:
1. Prefix the title with the kind's icon (`ICONS`, default 🔔); text = title + body (≤ 1500 chars) + url.
2. Span `notify <kind>` (`tool`). One `httpx.AsyncClient(timeout=10)`; targets are built from settings:
   - Telegram: `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` → `sendMessage` (≤ 4000 chars, no link preview).
   - Slack: `SLACK_WEBHOOK_URL` → `{"text": …}`.
   - Discord: `DISCORD_WEBHOOK_URL` → `{"content": …}` (≤ 1900 chars).
3. Each target is awaited in turn; errors are logged and recorded as `<channel>_error` on the span.
4. Insert a `notifications` row with `delivered` = the channels that succeeded. Returns `{id, kind, title, delivered}`.

**Inbox**: `GET /api/notifications?repo_id=&limit=` (newest first, max 500), polled every 5 s by `/app/inbox`.
Ticket detail (`GET /api/tickets/{id}`) includes that ticket's notifications.

**Telegram setup** (`uv run python -m scripts.telegram_setup`): checks the token (`getMe`), lists chats from
`getUpdates` as `TELEGRAM_CHAT_ID=<id>` lines, and sends a test message if `TELEGRAM_CHAT_ID` is set.
