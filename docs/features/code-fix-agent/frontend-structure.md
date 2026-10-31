# Frontend structure

> Status: **done** (Sprint 5). Paths below are real; keep them in sync with the code.

- `frontend/components/support/SupportChat.tsx` `FixCard`: shown when a `fix` event arrives; the `StepTrail` lists
  the agent's successive tool steps ("Reading …", "Editing …").
- `frontend/components/app/TicketView.tsx` `FixCard`: decision badge, PR link, CI state and `Checks`, root
  cause / change / test, suspects, note, and `DiffView` for the unified diff.
- `Fix` type in `frontend/lib/workspace.ts`.
