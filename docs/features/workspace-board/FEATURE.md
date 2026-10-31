# Workspace board and onboarding

> Status: **done** (Sprint 6). Paths below are real; keep them in sync with the code.

The signed-in home (`/app`) is a **Board**: an onboarding checklist until setup is complete, KPI tiles,
"tickets per day" and "what customers needed" charts, recent tickets, activity and repositories. Signup leads
to a guided **onboarding wizard** (`/app/welcome`): import a repo (or the one-click Slice demo), watch Supfeel
learn it, connect the business API, create an MCP key, send a first escalation. The landing page tells the
MCP escalation story and shows pay-as-you-go pricing.

## Why
The product only works after several setup steps (repo, index, API, key, first ticket). The wizard and the
checklist make that path obvious; the board shows the value (automation rate, fixes, verified actions).

## Scope
- In: `GET /api/dashboard`, the `demo` field of `GET /api/github/status`, `Board`, `Charts`, `Welcome`,
  motion components and CSS utilities, landing `ChatPreview`, `EscalationFlow` and the Pricing section.
- Out: the data sources themselves (tickets, repos, billing, keys: see their features).

## Success criteria
- The dashboard test in `backend/tests/support/test_mcp.py` (`test_dashboard_reflects_onboarding_and_tickets`)
  passes: onboarding flags, 14 daily points, billing, 401 when signed out.
- Charts use the validated categorical palette; color follows the category, never rank.
- Every animation is disabled under `prefers-reduced-motion: reduce`.
