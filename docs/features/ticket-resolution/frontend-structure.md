# Frontend structure

> Status: **done** (Sprint 5, updated in Sprint 6). Paths below are real; keep them in sync with the code.

- `frontend/app/support/[repoId]/page.tsx` → `components/support/SupportChat.tsx`: the owner's playground (redirects to
  `/login?next=` when signed out; stream calls send `authHeaders()`). For the Slice
  demo (repo name matches `/slice/` or it has a `create_order` operation) it offers demo customers
  (`c_maya`, `c_jordan`) and sample prompts; otherwise a name + account-id form. Renders `StepTrail`,
  `ProposalCard` (approve/decline), `VerifiedCard`, `FixCard`.
- `frontend/lib/useTicketChat.ts`: `useTicketChat(repoId, customer)` → `send`, `confirm`, `reset`; reduces SSE
  events into `AgentTurn`s (steps with running-detail history, proposals, verifications, fix).
- `frontend/app/app/tickets/page.tsx` → `Lists.tsx` `AllTickets` (polls 5 s) using `Workspace.tsx` `TicketList`.
- `frontend/app/app/tickets/[id]/page.tsx` → `components/app/TicketView.tsx`: conversation, resolution, `FixCard`
  (PR, CI checks, diff), `ActionsCard`, notifications, `TraceView`. Polls while status is `open`,
  `awaiting_confirmation` or `fix_in_review`.
- Types and stream helpers: `frontend/lib/workspace.ts` (`TicketEvent`, `ticketStream`), SSE parsing in `frontend/lib/api.ts`.
