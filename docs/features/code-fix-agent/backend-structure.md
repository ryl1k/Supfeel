# Backend structure

> Status: **done** (Sprint 5). Paths below are real; keep them in sync with the code.

```
backend/app/support/fixer.py
  PROTECTED, FIX_SYSTEM, TOOLS
  FixResult (decision, root_cause, summary, test, confidence, workaround, explanation, edits, files, originals, suspects, turns; diff())
  Workspace  read() / edit() / create() overlay over repo_files
  _tool(), run_agent(), report_only(), investigate()
  pr_body(), _reapply(), publish()
backend/app/support/ci.py
  refresh(), _poll(), track(), tickets_for(full_name, sha|branch), on_pr_closed()
backend/app/api/github.py      webhook(): ping, push (re-index), CI events, pull_request closed, installation(_repositories)
backend/app/repos/github.py    get_file(), commit_files(), create_pr(), ci_status(), FAILED_CONCLUSIONS, verify_signature()
backend/app/llm/client.py      tool_turn(): one turn of a manual tool loop; caches system + tools and the
                               conversation tail; returns {"content": [blocks], "stop_reason"}
```
