# Backend structure

> Status: **done** (Sprint 5). Paths below are real; keep them in sync with the code.

```
backend/app/obs/trace.py
  SpanCtx (set(), add_cost()), _NullSpan / NULL_SPAN, _current ContextVar, _clip()
  span(name, kind, *, trace_id=None, **attrs)   async context manager
  record_span(name, kind, *, started, duration_s, cost_usd, **attrs)   finished child span, not made current
  annotate_usage(cost, **tokens)                called by app/llm/ledger.py record()
  current(), current_trace_id(), load_trace(trace_id)
Instrumented: app/llm/client.py, app/rag/embeddings.py, app/repos/{github,openapi,search,indexer,ask}.py,
              app/support/{service,graph,context,assist,fixer,ci,learn,notify}.py
```
