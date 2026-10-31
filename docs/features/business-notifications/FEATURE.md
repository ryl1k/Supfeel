# Business notifications

> Status: **done** (Sprint 5). Paths below are real; keep them in sync with the code.

Everything Supfeel tells the business (bug found, fix PR opened, CI passed/failed, PR merged, action taken,
feature request, escalation) is stored as a notification, shown in the dashboard inbox, and mirrored to
Telegram, Slack and/or Discord when configured.

## Why
The business must hear about real bugs and escalations right away, where the team already is, without
watching the dashboard.

## Scope
- In: `notify()`, the `notifications` table, Telegram/Slack/Discord delivery, the Telegram setup script, the inbox
  page, per-ticket notification lists.
- Out: e-mail, per-repo channel routing, read/unread state.

## Success criteria
- A delivery failure never breaks a ticket; the inbox row is always written.
- `delivered` records which channels actually accepted the message.
