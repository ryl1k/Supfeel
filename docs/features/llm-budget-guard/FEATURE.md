# LLM budget guard

> Status: **planned**. Paths below are the agreed target layout; no code yet. Update when implemented.

The single gateway for every Claude and OpenAI call: enforces spend caps, logs usage, applies prompt
caching, and switches between `mock` / `replay` / `live` modes.

## Why
Hard limits: $90 Claude, $5 OpenAI, with heavy testing planned. Running out mid-hackathon would kill
the demo.

## Scope
- In: client wrapper, pricing table, usage ledger, caps, modes, response cache, usage endpoint.
- Out: prompts and graph logic.

## Success criteria
- No code path calls the Anthropic/OpenAI SDK outside `app/llm/` and `app/rag/embeddings.py`.
- Hitting a cap returns a graceful "assistant temporarily unavailable" event, never a crash.
