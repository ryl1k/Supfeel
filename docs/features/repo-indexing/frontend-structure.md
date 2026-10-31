# Frontend structure

> Status: **done** (Sprint 5, updated in Sprint 6). Paths below are real; keep them in sync with the code.

- `frontend/app/app/page.tsx` → `components/app/Board.tsx` (see `workspace-board`), which reuses `ImportCard`
  (GitHub URL or local path), `GithubCard` (auth mode + App install link), `RepoCard` + `JobProgress` from
  `components/app/Workspace.tsx`. First import usually happens in the wizard (`components/app/Welcome.tsx`).
- `frontend/app/app/repos/[id]/page.tsx` → `components/app/RepoView.tsx`: tabs Overview, Connect (MCP), Modules, Ask (answer +
  sources + trace), API actions, Tickets, Index runs (job list + `TraceView`), Settings (business API, token,
  spec URL, auto-fix). `?tab=` picks the initial tab. Link to the customer page `/support/{id}`.
- API client and types: `frontend/lib/workspace.ts` (`api.repos`, `api.repo`, `api.importRepo`, `api.reindex`,
  `api.updateSettings`, `api.ask`, `api.jobs`, `api.jobTrace`, `api.deleteRepo` (no UI button yet)). Requests carry
  the session token (`frontend/lib/session.ts`). Polling via `frontend/lib/usePoll.ts`.
