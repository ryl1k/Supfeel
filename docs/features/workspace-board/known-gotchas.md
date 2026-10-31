# Known gotchas

> Status: **done** (Sprint 6). Paths below are real; keep them in sync with the code.

- **CSS `text-transform: uppercase` changes `innerText`.** KPI and section labels are uppercase via CSS, so
  browser tests that read `innerText` see "TICKETS", not "Tickets". Use `textContent` or match case-insensitively.
- The dashboard loads every ticket of the last 30 days into memory and counts in Python: fine at demo scale.
- `automated` counts `awaiting_confirmation` and `fix_in_review` as handled although they are not finished.
- `daily` uses UTC days while the tooltip formats dates locally: near midnight a ticket can appear on the "wrong" day.
- The wizard's demo API step prefills `${API_URL}/demo-store`, which only works when the backend mounts the demo
  store (`MOUNT_DEMO_STORE`, default on, and `examples/slice-pizza/slice_api` present).
- The local demo is offered only with both `ALLOW_LOCAL_REPOS` and `OPEN_IMPORT`; in production set `DEMO_GITHUB_REPO`.
- Landing and Connect-tab prices are hard-coded copies of `billing.PRICES`: change both when prices change.
- `ChatPreview` timings are CSS `animationDelay`s; with reduced motion everything shows at once (intended).
- `components/app/Workspace.tsx` still exports the old `Workspace()` page component, now unused (`/app` renders `Board`).
