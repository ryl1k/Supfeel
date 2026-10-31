# Frontend structure

> Status: **done** (Sprint 5). Paths below are real; keep them in sync with the code.

- `frontend/app/app/inbox/page.tsx` → `components/app/Lists.tsx` `Inbox`: polls `api.notifications()` every 5 s.
- `frontend/components/app/TicketView.tsx` `NotificationItem`: title, body, delivered channels, links to the
  ticket and the URL (PR or ticket). Also used in the ticket page's "Business notifications" card.
- Nav entry "Inbox" in `frontend/components/app/Shell.tsx`. Type `Notification` in `frontend/lib/workspace.ts`.
