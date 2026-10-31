# Supfeel

**More than answers — real solutions.**

Supfeel is an AI customer-support agent that doesn't stop at answering questions. It understands the customer's problem, investigates their account, plans a fix, executes it through business tools (orders, refunds, exchanges, subscriptions) and verifies that the problem is actually resolved.

Hackathon project, built around a customer-support challenge.

## How it works

```
understand → investigate → plan → act → verify → respond
```

1. **Understand** — classify the request and extract the underlying problem.
2. **Investigate** — pull customer, order and shipment data from connected systems.
3. **Plan** — reason against company policy (retrieved from the knowledge base) and pick a resolution.
4. **Act** — execute the resolution via tools (refund, exchange, reship, cancel, update address…).
5. **Verify** — re-read system state to confirm the action took effect.
6. **Respond** — tell the customer what was done, with a visible action trail.

Personalized recommendations (e.g. replacement products) can optionally use Qloo taste intelligence. It is never a hard dependency.

## Repository layout

| Path | Purpose |
|---|---|
| `docs/project/` | Product brief, architecture, design system, budget, roadmap, conventions |
| `docs/agents/` | Living context for coding agents: current state, sprint log, handoff notes |
| `docs/design/` | Visual references (landing page mock) |
| `knowledge-base/` | Support policies and FAQ for the demo store. The agent retrieves from these (RAG) |
| `CLAUDE.md` | Entry point for AI coding agents working in this repo |

Application code (`backend/`, `frontend/`) lands in Sprint 1. See `docs/project/roadmap.md`.

## Getting started

```bash
cp .env.example .env   # add ANTHROPIC_API_KEY and OPENAI_API_KEY
```

Run instructions are added once the app code exists.

## Branches

- `main`: stable, demo-ready
- `dev`: active development; merged into `main` at the end of each sprint
