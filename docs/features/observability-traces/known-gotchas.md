# Known gotchas

> Status: **done** (Sprint 5). Paths below are real; keep them in sync with the code.

- **A ContextVar must not be held across async-generator yields.** Setting it inside a generator and resetting
  after a `yield` fails (the consumer may resume it in another context) and mis-parents spans. Generators like
  `stream_text` therefore use `record_span()` after the stream ends. A stream abandoned mid-way records no span.
- `asyncio.create_task` copies the context: a background task started inside a span keeps that span as parent.
  The CI poller is started from the `fix` step, so polled `check ci` spans nest under that (long finished) step,
  while webhook-triggered refreshes become new root spans in the ticket trace.
- Spans are written when they **end**, so while a run is in progress its children exist before their parent.
  `TraceView` shows them as roots until the parent lands.
- Spans outside any trace are no-ops. Learning after a normal ticket turn runs outside the run span and is not traced.
- Each CI poll writes its own `check ci` span (up to `CI_POLL_MAX` = 45 per PR), which clutters long traces.
- Token totals in `load_trace` add up embedding `input_tokens` and Claude `input_tokens` together.
- Cached Claude responses have `cached=True` and zero cost; the replay cache (`.llm-cache/`) makes re-runs free but still traced.
- `notify` stores its kind as attribute `kind_`, because `kind` is the span kind parameter.
- No retention: `spans` grows forever (watch the Neon free-tier storage).
