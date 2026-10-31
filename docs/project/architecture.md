# Architecture

Status: **proposed** (Sprint 0). Update this file when decisions change.

## Overview

```
┌──────────────┐   SSE/HTTP   ┌──────────────────────────────────────────────┐
│  Frontend    │ ───────────▶ │  Backend (FastAPI)                           │
│  Next.js     │ ◀─────────── │                                              │
│  (Vercel)    │  stream:     │  LangGraph agent                             │
└──────────────┘  text +      │   understand → investigate → plan → act      │
                  action      │        ▲                          │          │
                  events      │        └──── verify ◀─────────────┘          │
                              │                                              │
                              │  Tools ──▶ Mock business systems (SQLite)    │
                              │  RAG   ──▶ knowledge-base/ embeddings (npz)  │
                              │  LLM   ──▶ Claude Sonnet (budget guard)      │
                              │  Emb   ──▶ OpenAI text-embedding-3-small     │
                              └──────────────────────────────────────────────┘
```

## Stack

| Layer | Choice | Why |
|---|---|---|
| Frontend | Next.js (App Router) + TypeScript + Tailwind | Fast to build, free on Vercel |
| Backend | Python 3.11 + FastAPI | LangGraph is Python-first |
| Agent orchestration | LangGraph | Explicit state machine, so the steps are visible in the UI |
| LLM | Claude `claude-sonnet-5-5` via the official `anthropic` SDK | Required by the project |
| Embeddings | OpenAI `text-embedding-3-small` (1536-d) | Required by the project |
| Vector search | In-process cosine over a precomputed `.npz` file | Zero infra, zero cost, fine for under 1k chunks |
| Business data | SQLite seeded from JSON fixtures | Deterministic demo state, easy reset |
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

## Free deployment

| Part | Host |
|---|---|
| Frontend | Vercel Hobby |
| Backend | Render free web service (Docker), or Hugging Face Spaces (Docker) as fallback |
| Data | SQLite + npz shipped in the image; resets on restart (fine for the demo) |

No paid services anywhere. See `budget.md` for API spend.
