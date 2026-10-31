# Frontend structure

> Status: **done** (Sprint 6). Paths below are real; keep them in sync with the code.

- `frontend/lib/session.ts`: token in `localStorage` (`supfeel_session`), `setSessionToken`, `getSessionToken`,
  `useSessionToken()` (`useSyncExternalStore`; `null` = unknown on the server, `""` = signed out),
  `authHeaders()`. Cross-tab sync through the `storage` event.
- `frontend/lib/workspace.ts` `call()`: adds `authHeaders()`, clears the token on a 401 (except `/api/auth/*`).
  `api.signup`, `api.login`, `api.logout`, `api.me`, `api.billing`, `api.topup`, `api.saveCard`,
  `api.billingSettings`; types `Me`, `Billing`.
- `frontend/components/auth/AuthForm.tsx` (`mode` login | signup), used by `frontend/app/login/page.tsx` and
  `frontend/app/signup/page.tsx`. Signup → `/app/welcome`, login → `/app`, honours `?next=/…`.
- `frontend/components/app/Shell.tsx`: redirects to `/login?next=` when the token is `""`, renders a skeleton
  until known; `Account` shows the balance pill (warning colour below $1) linking to Billing, workspace name,
  Sign out. `money(cents)` helper. Nav: Workspace, Tickets, Inbox, Billing.
- `frontend/app/app/billing/page.tsx` → `frontend/components/app/BillingView.tsx`: stats (balance, month spend,
  limit, repos), price list, this month by metric + AI cost, statement, payment method (`CardForm`),
  `TopUp` (presets $10 / $25 / $50 / $100), `Limits` (spend bar, limit, auto-recharge). Polls every 15 s.
- `frontend/components/support/SupportChat.tsx` also redirects to `/login` when signed out (the playground is owner-only).
