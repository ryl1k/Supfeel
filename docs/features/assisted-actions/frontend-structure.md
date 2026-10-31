# Frontend structure

> Status: **done** (Sprint 5). Paths below are real; keep them in sync with the code.

- `frontend/components/support/SupportChat.tsx`: `ProposalCard` (shows the proposed action title; approve/decline
  calls `useTicketChat().confirm`), `VerifiedCard` (checks list). Demo customers `c_maya` / `c_jordan` for Slice.
- `frontend/components/app/TicketView.tsx`: `ActionsCard` (operation, args, status, response, `Checks`).
- `frontend/components/app/RepoView.tsx`: "API actions" tab (discovered operations) and Settings (base URL, spec URL, service token).
- Events: `action_proposed`, `action_done`, `verified` in `frontend/lib/workspace.ts` `TicketEvent`.
