# Backend structure

> Status: **done** (Sprint 5). Paths below are real; keep them in sync with the code.

```
backend/app/support/notify.py    ICONS, _text(), _telegram(), notify()
backend/app/support/service.py   list_notifications(), notification_view(); get_ticket() adds per-ticket notifications
backend/app/api/tickets.py       GET /api/notifications
backend/scripts/telegram_setup.py  main(): getMe, getUpdates → chat ids, test sendMessage
backend/app/config.py            telegram_bot_token, telegram_chat_id, slack_webhook_url, discord_webhook_url, public_app_url
```
