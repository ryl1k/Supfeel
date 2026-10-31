# Known gotchas

> Status: **done** (Sprint 5). Paths below are real; keep them in sync with the code.

- Telegram only delivers to a chat after someone has messaged the bot there; run `scripts.telegram_setup` after
  sending one message to get the chat id.
- Deliveries run one after another with a 10 s timeout each, inside the ticket turn. A slow channel delays the reply.
- `ICONS` has a `fix_failed` entry, but CI failures are emitted as `ci_failed`.
- `GET /api/notifications` is unauthenticated, like the rest of the dashboard API.
- Tests must not hit real channels: `backend/tests/conftest.py` isolates them from real integrations.
- In mock mode the notifications are still real (they don't depend on Claude), so a configured Telegram bot gets test traffic.
