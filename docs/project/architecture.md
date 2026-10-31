# Architecture

Status: **proposed** (Sprint 0). Update this file when decisions change.

## Overview

```
┌──────────────┐   SSE/HTTP   ┌──────────────────────────────────────────────┐
│  Frontend    │ ───────────▶ │  Backend (FastAPI) on Render                 │
│  Next.js     │ ◀─────────── │                                              │
│  (Vercel)    │  stream:     │  LangGraph agent                             │
└──────────────┘  text +      │   understand → investigate → plan → act      │
                  action      │        ▲                          │          │
                  events      │        └──── verify ◀─────────────┘          │
                              │                                              │
                              │  Tools ──▶ Mock business systems (Postgres)  │
                              │  RAG   ──▶ kb_chunks (pgvector)              │
                              │  LLM   ──▶ Claude Sonnet (budget guard)      │
                              │  Emb   ──▶ OpenAI text-embedding-3-small     │
                              └──────────────────────┬───────────────────────┘
                                                     ▼
                                       Neon Postgres + pgvector
```

## Stack

| Layer | Choice | Why |
|---|---|---|
| Frontend | Next.js (App Router) + TypeScript + Tailwind | Fast to build, free on Vercel |
| Backend | Python 3.11 + FastAPI | LangGraph is Python-first |
| Agent orchestration | LangGraph | Explicit state machine, so the steps are visible in the UI |
| LLM | Claude `claude-sonnet-5-5` via the official `anthropic` SDK | Required by the project |
| Embeddings | OpenAI `text-embedding-3-small` (1536-d) | Required by the project |
| Database | Neon Postgres (free plan) via SQLAlchemy 2 + asyncpg | Persistent across backend redeploys, free, scales to zero |
| Vector search | `pgvector` on the same Neon DB (`kb_chunks.embedding vector(1536)`) | One store, no extra infra; HNSW supports 1536-d |
| Business data | Postgres tables seeded from JSON fixtures (`/api/admin/reset`) | Deterministic demo state, one-call reset |
| Local dev DB | Docker `pgvector/pgvector:pg16`, or a Neon dev branch | Same engine as prod |
| Streaming | Server-Sent Events | Simple, works on free hosts |

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
