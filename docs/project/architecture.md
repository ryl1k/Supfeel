# Architecture

Status: **current** (updated Sprint 5, 2026-10-31: pivot to code-aware support). The original Velora store agent
still exists as a legacy demo (`/chat`); its design is kept below under "Legacy: Velora agent".

## Overview

```
 GitHub repo ──(App: tarball, PRs, CI, push webhooks)──┐
                                                       ▼
┌──────────────┐   HTTP + SSE   ┌──────────────────────────────────────────────────────────────┐
│ Next.js      │ ─────────────▶ │ FastAPI on Render                                            │
│ (Vercel)     │ ◀───────────── │                                                              │
│  /app        │                │  repos/   index: snapshot → chunks → embeddings → summaries  │
│  /support/:id│                │           OpenAPI → api_operations, Q&A (ask)                │
└──────────────┘                │  support/ ticket graph (LangGraph):                          │
                                │     context → triage → explain | assist | fix | feature |    │
                                │                       escalate → respond  (+ learn)          │
                                │     assist: business API calls, confirm, read-back verify    │
                                │     fix:    Claude tool loop → PR → CI = verification        │
                                │  obs/     spans for every step / LLM / tool / HTTP call      │
                                │  notify   inbox + Telegram / Slack / Discord                 │
                                │  /demo-store  Slice demo business API (examples/slice-pizza) │
                                └───────────────┬──────────────────────────────┬───────────────┘
                                                ▼                              ▼
                                  Neon Postgres + pgvector          Claude Sonnet 5.5 / OpenAI emb
```

## Stack

| Layer | Choice | Why |
|---|---|---|
| Frontend | Next.js 16 (App Router, cacheComponents) + Tailwind v4 | Free on Vercel |
| Backend | Python 3.11 + FastAPI + SSE | LangGraph is Python-first |
| Orchestration | LangGraph (`app/support/graph.py`) | Explicit state machine; every node is a visible step and a trace span |
| LLM | Claude `claude-sonnet-5-5` via `app/llm/client.py` only | Budget guard, caching, recording |
| Embeddings | OpenAI `text-embedding-3-small` (1536-d), batched + cached | Required by the project |
| Vector store | pgvector on Neon (`repo_chunks`, `kb_chunks`, HNSW) | One database |
| GitHub | GitHub App (installation tokens), PAT fallback, anonymous for public repos | PRs as a bot, per-repo access |
| Tracing | Own `spans` table + UI graph (`app/obs/trace.py`, `TraceView.tsx`) | Free, judge-visible transparency |
| Notifications | Dashboard inbox + Telegram / Slack / Discord webhooks | Free |

## Repository indexing (`app/repos/`)

1. **Snapshot**: one tarball request per run (or a local directory in dev). Filters skip vendored dirs, lockfiles,
   binaries, secrets (`.env`, `*.pem`); limits on files / bytes protect the budget and the 512 MB instance.
2. **Diff**: file content hashes vs `repo_files`; only changed files are re-chunked and re-embedded.
3. **Chunk**: code split at top-level definitions (Python, JS/TS, Go, Rust, JVM, Ruby, PHP), markdown at headings,
   otherwise line windows. Symbol outlines stored per file.
4. **API**: OpenAPI/Swagger specs in the repo (or `api_spec_url`) become `api_operations`, the assisted-action toolset.
5. **Explain**: Claude summarizes each module (top 30 by size) and writes a repo overview; inputs are hashed so
   unchanged modules cost nothing. Rules fallback without Claude.
6. **Search**: cosine similarity + keyword boost for identifiers/paths, over kinds code/doc/summary/api/ticket.

Re-index triggers: import, manual button, `push` webhook on the default branch. One job per repo; a push during a
run queues one follow-up.

## Ticket graph (`app/support/`)

| Node | What | LLM |
|---|---|---|
| context | search code/docs/summaries, similar past tickets, API operations | – |
| triage | category (bug / misunderstanding / assisted_action / feature_request / other), also_bug, search queries | 1 structured call |
| explain | answer from context (customer then confirms → resolved, or not → escalated) | – |
| assist | plan with read-only API lookups (tool loop), propose one write; authority rules in code | tool loop (≤ 6 turns) |
| act (confirm turn) | execute the write, read the resource back, compare fields | – |
| fix | code agent: search/read/edit/create tools on an in-memory overlay, regression test; `not_a_bug` reroutes to explain | tool loop (≤ 16 turns) |
| publish | re-apply edits on the branch head, commit, open PR; CI via poller + webhooks; merge → resolved | – |
| feature / escalate | notify the business | – |
| respond | streamed customer reply (no internals) | 1 streamed call |

Each turn runs in a background task (it survives client disconnects) under one trace (`trace_id` = ticket id).
Closed tickets are embedded as `ticket` chunks: learning from previous tickets.

## Safety

- Customer text is data, not instructions (stated in every prompt; no tool can reach outside the repo/API).
- Assisted actions: only spec'd operations; customer-id fields forced to the ticket's customer; ownership read-back
  before writes on other resources; customer confirmation for every write; ≤ 3 writes per ticket; read-back
  verification; failures escalate.
- Fixes: protected paths (CI config, secrets), ≤ 5 files, PRs are never merged automatically; CI is the check.
- Spend caps: global $60, per ticket (`TICKET_CAP_USD`), per fix (`FIX_CAP_USD`), per index job (`INDEX_CAP_USD`).

---

# Legacy: Velora agent (Sprints 0–4)

## Agent graph (LangGraph)

State: `messages`, `customer_id`, `intent`, `facts` (gathered data), `policy_refs` (retrieved KB chunks), `plan` (list of actions), `actions_done`, `verification`, `cost`.

Nodes:
1. **understand**: one LLM call: intent, entities (order id, product), missing info → may ask a clarifying question and stop.
2. **investigate**: deterministic tool calls (no LLM) based on intent: `get_customer`, `list_orders`, `get_order`, `get_shipment`, `get_payments`.
3. **retrieve_policy**: embed the query and take the top-k KB chunks.
4. **plan**: one LLM call with facts + policy: ordered actions + justification + `needs_confirmation` flag.
5. **act**: execute tools. Sensitive actions pause for user confirmation (LangGraph interrupt).
6. **verify**: deterministic read-back of system state for each action. The LLM only runs if a mismatch needs a decision.
7. **respond**: one LLM call that writes the customer-facing summary.

Typical cost: **3 LLM calls per resolved issue**. Investigate and verify stay deterministic on purpose, to save budget and make results reproducible.

## Tools (mock business API)

Read: `get_customer`, `list_orders`, `get_order`, `get_shipment`, `get_payments`, `get_subscription`, `search_products`.
Write: `create_refund`, `create_exchange`, `create_return_label`, `reship_order`, `cancel_order`, `update_address`, `issue_store_credit`, `pause_subscription`, `cancel_subscription`, `escalate_to_human`.

Optional: `get_recommendations` (Qloo when a key is available, otherwise a local tag-similarity fallback).

## Deployment (decided 2026-10-31)

| Part | Host | Plan / limits that matter |
|---|---|---|
| Frontend | **Vercel** Hobby | Free. Static/edge only; no long-running backend work here |
| Backend | **Render** free web service (Docker) | 512 MB RAM (we use ~145 MB), 750 h/month, spins down after ~15 min idle (30–60 s cold start) |
| Database | **Neon** Free | 0.5 GB storage, 100 CU-hours/month per project, scales to zero after 5 min idle (cold start ~1 s) |

- Cold starts are the main risk: keep the service warm with a free uptime ping during judging. Fallbacks with the same Dockerfile: Koyeb, HF Spaces.
- Frontend → backend over HTTPS + SSE; CORS allows the Vercel domain only.
- Secrets live in Render/Vercel env vars, never in the repo.

See `budget.md` for API spend.
