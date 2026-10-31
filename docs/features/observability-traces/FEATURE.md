# Observability traces

> Status: **done** (Sprint 5). Paths below are real; keep them in sync with the code.

Every ticket turn, index job and repo question is a trace: nested spans (steps, Claude calls, embeddings,
searches, business-API calls, GitHub requests) stored in Postgres with duration, cost and tokens. The dashboard
shows each trace as a flow graph plus a waterfall.

## Why
"Verify" includes showing the work: the business (and judges) can see exactly what the agent searched, which
model calls it made and what they cost, which API calls it made, and where it failed.

## Scope
- In: `app/obs/trace.py` (span context manager, `record_span`, `annotate_usage`, `load_trace`), span
  instrumentation across llm / rag / repos / support, trace endpoints, `TraceView`.
- Out: OpenTelemetry export, sampling, retention (no cleanup of `spans` yet).

## Success criteria
- Instrumented code needs no trace plumbing: spans nest automatically through a ContextVar.
- Tracing never breaks a request (persist errors are logged and swallowed).
- Per-span cost matches the `llm_usage` ledger.
