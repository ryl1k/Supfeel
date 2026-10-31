# Known gotchas

> Status: **done** (Sprint 5, updated in Sprint 6). Paths below are real; keep them in sync with the code.

- **Render free tier sleeps, and GitHub webhooks time out at 10 s**, so CI and PR events can be missed. The
  `ci._poll` loop is the fallback. Keep the service awake during demos (`docs/project/deployment.md`).
- **Fixes are re-applied on the current branch head** (`_reapply`), because the index can be a few commits
  stale. Committing the overlay contents directly could revert newer code. If an `old_str` no longer matches, the
  fix falls back to a patch.
- CI pollers are in-memory tasks. `resume_tracking()` (app lifespan) restarts them on boot for `fix_in_review`
  tickets whose CI state is `pending` or unknown; anything else waits for a webhook.
- A repo without CI reports `none`. After `NO_CI_POLLS` (≈ 2 min) the fix is marked unverified (`ci_missing`),
  but the ticket stays `fix_in_review` until the PR is merged or closed.
- The fix is charged before the agent runs; only the `report` fallback is refunded (`gave_up` / out of turns is not).
- Mock mode / budget cap → `report_only` (no edits, suspects only). `tool_turn` has no rules fallback.
- `PROTECTED` only covers `.github/`, `.env*`, `*.pem`, `*.key`. Other CI configs are protected only by the prompt.
- `create_file` only checks the index: a file that exists on GitHub but was skipped by indexing (lockfile,
  large or vendored file) can be overwritten, and `create` does not count toward the 5-file limit.
- `commit_files` writes every file as mode `100644` (an executable bit is lost if the agent edits a script).
- The diff on the ticket is against the indexed version, not the fresh head the PR was built on.
- The branch name is per ticket, so a second fix for the same ticket force-updates the same branch.
- Cached `tool_turn` recordings key on the full message list; any change in tool output makes the next turn a fresh call.
