# Backend structure

> Status: **planned**. Paths below are the agreed target layout; no code yet. Update when implemented.

```
backend/app/agent/
  graph.py            build_graph(): wires nodes + conditional edges, Postgres checkpointer
  state.py            AgentState (TypedDict): messages, customer_id, intent, entities, facts,
                      policy_refs, plan, actions_done, verification, step_count, cost_usd
  events.py           typed SSE events: token, step, action_proposed, action_done, verified, error
  nodes/
    understand.py     LLM → Intent (pydantic, structured output)
    investigate.py    intent → deterministic read-tool calls
    retrieve_policy.py  rag.retrieve(query, k=5)
    plan.py           LLM → Plan[Action] with needs_confirmation
    act.py            executes actions; LangGraph interrupt() for confirmations
    verify.py         per-action read-back checks (registry of verifiers)
    respond.py        LLM streaming summary
  prompts/            system prompts as .md files (frozen → cacheable)
```
Limits: `MAX_STEPS=8`, `MAX_REPLANS=2` (in `graph.py`).
