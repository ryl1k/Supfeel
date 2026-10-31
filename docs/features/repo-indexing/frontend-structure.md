# Frontend structure

> Status: **done** (Sprint 5). Paths below are real; keep them in sync with the code.

- `frontend/app/app/page.tsx` → `components/app/Workspace.tsx`: `ImportCard` (GitHub URL or local path),
  `GithubCard` (auth mode + App install link), `RepoCard` + `JobProgress` (polls every 2.5 s while indexing),
  recent tickets.
- `frontend/app/app/repos/[id]/page.tsx` → `components/app/RepoView.tsx`: tabs Overview, Modules, Ask (answer +
  sources + trace), API actions, Tickets, Index runs (job list + `TraceView`), Settings (business API, token,
  spec URL, auto-fix, admin token). Link to the customer page `/support/{id}`.
- API client and types: `frontend/lib/workspace.ts` (`api.repos`, `api.repo`, `api.importRepo`, `api.reindex`,
  `api.updateSettings`, `api.ask`, `api.jobs`, `api.jobTrace`). The admin token is kept in `localStorage`
  (`supfeel_admin_token`). Polling via `frontend/lib/usePoll.ts`.
