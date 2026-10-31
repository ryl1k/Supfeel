# API budget and cost controls

Hard limits: **$90 Claude**, **$5 OpenAI**. We will run many tests, so we plan to spend **at most about half** and keep the rest as headroom.

## Models and prices (checked 2026-10-31)

| Purpose | Model | Price |
|---|---|---|
| Reasoning / chat | `claude-sonnet-5-5` | $2.00 / MTok input, $10.00 / MTok output, cache reads $0.20 / MTok |
| Embeddings | `text-embedding-3-small` | about $0.02 / MTok |

Do not switch models without updating this file.

## Spend targets

| Bucket | Allocation |
|---|---|
| Development and manual testing | $25 |
| Automated test runs (live) | $10 |
| Demo rehearsals and the live demo | $10 |
| App hard cap (`LLM_BUDGET_HARD_CAP_USD`) | **$60** (the app refuses calls past this) |
| Untouched reserve | $30 |
| OpenAI embeddings hard cap | $3 (expected real use is under $0.10) |

## Per-conversation estimate

About 3 LLM calls per resolved issue (understand, plan, respond):
- Input ≈ 3 × 4k tokens, mostly a cached prefix of system prompt + tools + policy
- Output ≈ 3 × 400 tokens
- Cost ≈ **$0.02–0.04 per conversation** with caching, about $0.06 without

So $45 of operational spend covers more than 1,000 full conversations.

## Mandatory controls (implement in Sprint 1)

1. **Central LLM client**. All Claude calls go through one module that:
   - logs `usage` (input, output, cache read/write tokens) and the computed USD to the `llm_usage` table (persists across Render redeploys)
   - enforces the global hard cap and a per-session cap (`LLM_SESSION_CAP_USD`)
   - sets a modest `max_tokens` per node (understand 512, plan 1024, respond 768)
   - uses `output_config.effort = "low"` by default; raise it only for `plan` if quality needs it
2. **Prompt caching**: frozen system prompt + tool definitions first, then a `cache_control` breakpoint, then volatile content. Never put timestamps or IDs in the system prompt. Check `cache_read_input_tokens > 0` in the ledger.
3. **LLM modes** (`LLM_MODE`):
   - `mock`: canned responses, used for all UI and frontend work. **Default.**
   - `replay`: serve responses recorded in `.llm-cache/` keyed by request hash; fail on a miss. Used for tests and CI.
   - `live`: real calls, which are also recorded for later replay.
4. **Embeddings**: embed `knowledge-base/` **once** into `kb_chunks` (pgvector), keyed by a content hash per chunk. Re-embed only changed chunks. Cache query embeddings (in memory, plus the `embedding_cache` table).
5. **Agent loop limits**: at most 8 graph steps per turn and at most 2 verify→replan cycles.
6. **Tests**: unit tests use `mock`/`replay`. Live evals run only when asked, on a small scenario set (≤ 10).

## Spend log

Update after each sprint (from `GET /api/admin/usage`, which sums `llm_usage`).

| Sprint | Claude $ | OpenAI $ | Notes |
|---|---|---|---|
| 0 | 0.00 | 0.00 | Docs + KB only |
| 1 | 0.00 | 0.00 | All work in mock mode (hash embeddings, no Claude calls) |
| 2 | 0.07 | 0.0001 | One live smoke run (4 turns) + one OpenAI KB ingest. Measured ≈ $0.017 per turn with caching |
| 3 | 0.00 | 0.00 | UI built against LLM_MODE=mock |
| 4 | 0.067 | 0.00 | Second live smoke run after the prompt change. **Cumulative: $0.135 Claude, $0.0001 OpenAI** |
