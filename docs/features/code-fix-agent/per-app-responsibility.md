# Per-app responsibility

> Status: **done** (Sprint 5). Paths below are real; keep them in sync with the code.

| App | Responsibility |
|---|---|
| backend | Agent loop, overlay, publishing, CI poller, webhook handling, ticket status transitions |
| Claude | The fix agent (`fix_agent` node, adaptive thinking, effort medium) |
| GitHub | Contents API (fresh files), Git Data API (tree/commit/ref), Pulls API, check runs + commit statuses, webhooks |
| CI (the business's) | Runs the repo's tests on the PR: the verification |
| Neon DB | `tickets.fix` (diff, branch, head_sha, pr_url, ci), `spans`, `notifications` |
| frontend | `FixCard` in chat and on the ticket page (PR link, CI checks, diff) |
