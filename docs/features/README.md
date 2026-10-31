# Feature context

AI needs business context. Every feature gets `docs/features/<feature>/` with **10 files**:

| Group | File | Contents |
|---|---|---|
| What and why | `FEATURE.md` | Main description: purpose, scope, success criteria |
| | `business-context.md` | Business rules and constraints |
| | `end-to-end-flow.md` | Step-by-step flow, including failure paths |
| Where it lives in code | `entry-points.json` | Entry points: HTTP routes, pages, CLIs, key modules, tests |
| | `per-app-responsibility.md` | What each app (backend, frontend, DB, external APIs) does |
| | `backend-structure.md` | Backend files and modules |
| | `frontend-structure.md` | Frontend routes and components |
| | `data-model.md` | Tables and types |
| Links and risks | `integration-points.md` | Where it touches other features and services |
| | `known-gotchas.md` | Known pitfalls |

New feature: `cp -r docs/features/_template docs/features/<name>`, fill in all 10 files, and add a row below.

## Features

| Feature | Status | Summary |
|---|---|---|
| [repo-indexing](repo-indexing/FEATURE.md) | done | Import a GitHub repo: chunk + embed into pgvector, discover the OpenAPI, explain modules, push re-index, Q&A |
| [ticket-resolution](ticket-resolution/FEATURE.md) | done | Ticket graph: context → triage → explain / assist / fix / feature / escalate → streamed reply; learning |
| [assisted-actions](assisted-actions/FEATURE.md) | done | Act through the business's OpenAPI with customer scoping, confirmation and read-back verification |
| [code-fix-agent](code-fix-agent/FEATURE.md) | done | Claude tool-use agent fixes the bug, opens a PR; CI is the verification; merge resolves the ticket |
| [mcp-server](mcp-server/FEATURE.md) | done (Sprint 6) | MCP endpoint `/mcp` for the business's first-line agent: escalate / reply / confirm, relay-ready results, callbacks |
| [accounts-billing](accounts-billing/FEATURE.md) | done (Sprint 6) | Email + password workspaces, MCP keys, repo scoping; pay-as-you-go credits, monthly limit, auto-recharge (mock payments) |
| [workspace-board](workspace-board/FEATURE.md) | done (Sprint 6) | Board with onboarding checklist and charts, `/app/welcome` setup wizard, motion, landing escalation story + pricing |
| [observability-traces](observability-traces/FEATURE.md) | done | Postgres spans for every step, model call, search, API and GitHub request; flow graph + waterfall |
| [business-notifications](business-notifications/FEATURE.md) | done | Dashboard inbox mirrored to Telegram / Slack / Discord |
| [llm-budget-guard](llm-budget-guard/FEATURE.md) | done | Single LLM gateway: caps, usage ledger, caching, mock/replay/live, `tool_turn` |
| [landing-page](landing-page/FEATURE.md) | done | `/` hero matching the design reference |
| [resolution-agent](resolution-agent/FEATURE.md) | legacy demo (Velora store) | LangGraph loop: understand → investigate → policy → plan → act → verify → respond |
| [business-tools](business-tools/FEATURE.md) | legacy demo (Velora store) | Mock Velora systems (Postgres) + read/write tools + demo reset |
| [knowledge-base-rag](knowledge-base-rag/FEATURE.md) | legacy demo (Velora store) | Chunk + embed `knowledge-base/` into pgvector; top-k retrieval (embedding client still shared) |
| [chat-experience](chat-experience/FEATURE.md) | legacy demo (Velora store) | `/chat` UI: streaming, action trail, confirmations, recommendations |

## Keeping it current

- When implementing: switch `Status` to in progress, and replace "planned" paths with real ones in `entry-points.json`.
- When a sprint ends: every feature touched has accurate structure files, plus new entries in `known-gotchas.md`.
