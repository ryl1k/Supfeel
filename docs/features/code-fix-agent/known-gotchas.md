# Known gotchas

> Status: **done** (Sprint 5). Paths below are real; keep them in sync with the code.

- **Render free tier sleeps, and GitHub webhooks time out at 10 s**, so CI and PR events can be missed. The
  `ci._poll` loop is the fallback. Keep the service awake during demos (`docs/project/deployment.md`).
- **Fixes are re-applied on the current branch head** (`_reapply`), because the index can be a few commits
  stale. Committing the overlay contents directly could revert newer code. If an `old_str` no longer matches, the
  fix falls back to a patch.
- CI pollers are in-memory tasks: a restart loses them and nothing re-arms them on boot, so a ticket can stay
  `fix_in_review` until a webhook arrives.
- A repo without CI reports `none`. The poller keeps polling the full 45 times and the ticket never leaves `fix_in_review`.
- Mock mode / budget cap → `report_only` (no edits, suspects only). `tool_turn` has no rules fallback.
- `PROTECTED` only covers `.github/`, `.env*`, `*.pem`, `*.key`. Other CI configs are protected only by the prompt.
- `create_file` only checks the index: a file that exists on GitHub but was skipped by indexing (lockfile,
  large or vendored file) can be overwritten, and `create` does not count toward the 5-file limit.
- `commit_files` writes every file as mode `100644` (an executable bit is lost if the agent edits a script).
- The diff on the ticket is against the indexed version, not the fresh head the PR was built on.
- The branch name is per ticket, so a second fix for the same ticket force-updates the same branch.
- Cached `tool_turn` recordings key on the full message list; any change in tool output makes the next turn a fresh call.
