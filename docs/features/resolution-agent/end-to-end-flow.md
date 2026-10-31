# End-to-end flow

> Status: **done** (Sprint 2). Paths below are real; keep them in sync with the code.

**Message turn** (`POST /api/chat`) → `service.handle_message`:
1. Load/create the conversation; save the user message. A typed yes/no while a proposal is pending is
   routed as a confirmation. Any other message supersedes (declines) the pending proposal.
2. **understand**: brain → `Intent` (structured output). Missing key fact → `outcome=asked` → respond.
3. **investigate** (no LLM, `facts.py`): picks the relevant order by intent, calls read tools, and computes
   `derived` flags (return window, comfort guarantee, shipment assessment, duplicate charges, renewal-refund eligibility).
4. **policy**: `retrieve(summary + search_query, k=4, audience=customer)`.
5. **plan**: brain → `Plan`. Then `authority.enforce()` validates args, sets confirmation flags, and
   escalates if > $200. Actions are logged as `proposed`. If any action needs confirmation, the whole plan waits
   (`action_proposed` event, `outcome=awaiting_confirmation`). `ask` / `inform` / `decline` go straight to respond.
6. **act**: execute each action once (`registry.execute(verify_after=False)`), emitting `action_done`.
7. **verify**: `registry.verify_action()` read-back (1 retry). Any failure → automatic `escalate_to_human`.
8. **respond**: streamed reply (`token` events). The state is persisted in `conversations.state`
   (`previous` + `pending`), then a `done` event is emitted.

**Confirm turn** (`POST /api/chat/confirm`) → graph starts at **act** with the pending plan restored from
`conversations.state.pending`. Declined → nothing executes and `outcome=declined`.

Hero (live Claude run, 2026-10-31): "uncomfortable" → ask what feels off → "too narrow" → proposes
Cloud Runner Slate 10 **2E** exchange + return label → approve → both verified. That's 4 turns for ≈ $0.07 total.
