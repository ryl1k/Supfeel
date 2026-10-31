# Business context

> Status: **done** (Sprint 5). Paths below are real; keep them in sync with the code.

- PRs are opened only for GitHub repos with write access (GitHub App installation or `GITHUB_TOKEN`) and
  `settings.auto_fix` not `false` (default on). Otherwise the fix is kept as a **patch** on the ticket.
- Limits: `FIX_MAX_TURNS` (16) agent turns, `FIX_CAP_USD` (.50) per ticket, 4000 output tokens per turn,
  `effort="medium"`, at most 5 edited files, `PROTECTED` paths (`.github/`, `.env*`, `*.pem`, `*.key`).
- The agent must add or extend a regression test (`FIX_SYSTEM`); `finish` without edits is rejected.
- `not_a_bug` turns the ticket into an explanation (status `answered`) instead of a fix.
- CI polling: every `CI_POLL_SECONDS` (20 s), at most `CI_POLL_MAX` (45) times ≈ 15 minutes per PR.
- Merge → ticket `resolved` + customer message "the fix is now live". Closed unmerged → `escalated`.
- The customer never hears about PRs or code (`RESPOND_SYSTEM`); the business gets `pr_opened`, `ci_passed` /
  `ci_failed`, `pr_merged` notifications.
