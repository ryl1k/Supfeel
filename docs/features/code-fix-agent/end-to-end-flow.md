# End-to-end flow

> Status: **done** (Sprint 5). Paths below are real; keep them in sync with the code.

1. `graph.fix_node` builds a report (subject, message, recent history, triage `bug_hypothesis`) →
   `fixer.investigate()` (span "fix agent").
2. `run_agent()`: up to `FIX_MAX_TURNS` calls of `tool_turn(node="fix_agent")`. Tools: `search_code`, `read_file`
   (numbered, ≤ 400 lines), `list_files`, `edit_file` (unique `old_str`), `create_file`, and terminal `finish`,
   `not_a_bug`, `give_up`. Each tool call is a `fix tool <name>` span and a `step fix running` event.
   Edits land in `Workspace` (overlay over `repo_files`), not on disk or GitHub.
3. Outcomes: `fixed` (edits + root cause, summary, test, confidence, workaround), `not_a_bug` → route `explain`,
   `gave_up` / out of turns, or `report` (`LlmUnavailable`/`BudgetExceeded` → `report_only()`: top 5 code hits as suspects).
4. `fixer.publish()` (span "open pull request"): `client_for()`; no write access / local repo / `auto_fix=false` →
   `mode="patch"` with diff. Otherwise `_reapply()` fetches each touched file from the **current default-branch
   head** and re-applies the `old_str → new_str` edits (409 if a file vanished or the edit no longer matches →
   patch), `commit_files()` on `supfeel/fix-<ticket id>` (force-updated if it exists), `create_pr()` (reuses an open PR).
5. PR opened → status `fix_in_review`, `fix` event, `pr_opened` notification, `ci.track(ticket_id)` starts the poller.
   Patch / report → status `reported`, `bug_reported` notification.
6. **CI** (`ci.refresh`, span "check ci" with `trace_id` = ticket): `ci_status(head_sha)` merges check runs and
   commit statuses into `none`/`pending`/`success`/`failure`. On a new terminal state: `fix_verified` +
   `ci_passed`, or `fix_failed` + `ci_failed`. Webhooks `check_suite` / `check_run` / `workflow_run` / `status`
   trigger an immediate refresh via `ci.tickets_for(sha=…)`.
7. **PR closed** webhook on a `supfeel/` branch → `ci.on_pr_closed()`: merged → `resolved`, agent message,
   `pr_merged` notification, `service.learn_ticket()`; not merged → `escalated`.
