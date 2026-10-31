# End-to-end flow

> Status: **done** (Sprint 5). Paths below are real; keep them in sync with the code.

1. A root span opens with an explicit `trace_id`: `trace.span("ticket turn (message)", kind="run", trace_id=ticket.id)`
   (`support/service.py`), `"index repository"` (`repos/indexer.py`), `"ask repository"` (`repos/ask.py`),
   `"customer feedback"`, `"pull request closed"`, and `"check ci"` (`support/ci.py`).
2. Nested `trace.span(...)` calls read the parent from the `_current` ContextVar. With no trace id anywhere up
   the stack they return `NULL_SPAN` (no-op), so the same code runs untraced in scripts and tests.
3. Instrumentation: graph nodes (`traced()` → `step`), `complete_json` / `tool_turn` (`claude.<node>`, `llm`),
   `embed` (`embed.<node>`, `embedding`), `search` (`search code`, `retrieval`), `GitHub.request` / `tarball`
   (`http`), `openapi.fetch_spec` (`http`), `assist.call_api` / `verify` and fix tools (`tool`), `notify <kind>` (`tool`).
4. `ledger.record()` calls `annotate_usage(cost, tokens…)`, which adds cost and token counts to the innermost span.
5. Streaming: `stream_text` is an async generator, so it does not open a span. After the stream ends it calls
   `record_span()` with the measured start, duration, cost and tokens (`annotate=False` on the ledger record).
6. On exit, `_persist()` writes the span (status `error` + `error` attribute if an exception escaped).
7. `load_trace(trace_id)` returns spans ordered by start plus a summary: span count, total cost, root duration,
   errors, `by_kind` roll-ups and token totals. `TraceView` builds the tree client-side.
