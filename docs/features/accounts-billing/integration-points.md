# Integration points

> Status: **done** (Sprint 6). Paths below are real; keep them in sync with the code.

- **ticket-resolution**: `open_ticket` charges `ticket`; `_drive` sets `current_account`; web ticket routes
  require `CurrentPrincipal` and `repo_for` / `ticket_for`; `list_tickets` / `list_notifications` take the
  account's repo ids (`account_repo_ids`).
- **code-fix-agent**: `fix_node` charges `fix`, refunds on `report`, skips the run on `PaymentRequired`.
- **repo-indexing**: import / reindex / ask charged; `repos.account_id`; `MAX_REPOS` counted per account;
  indexer sets `current_account` from the repo.
- **mcp-server**: keys (`resolve_key`), `ask_product` charge, payment errors as `ToolError`.
- **llm-budget-guard**: `app/llm/ledger.py` stores `current_account.get()` in `llm_usage.account_id`. The global
  $ caps are unchanged; workspace billing is a separate layer on top.
- **workspace-board**: `/api/dashboard` embeds `billing.summary()`; onboarding checks the saved card and keys.
