# Backend structure

> Status: **done** (Sprint 2). Paths below are real; keep them in sync with the code.

```
backend/app/agent/
  graph.py      7 nodes + routers; GRAPH = build_graph() (no checkpointer, see gotchas)
  service.py    handle_message / handle_confirm / transcript: persistence, yes/no routing, SSE events
  brain.py      understand / plan / respond: Claude via app.llm.client, auto-fallback to rules
  rules.py      deterministic rule brain (mock mode + fallback); covers all demo scenarios
  prompts.py    one frozen SYSTEM prompt shared by all nodes (cacheable) + per-job instructions
  authority.py  code-enforced confirmation/escalation rules + action titles/descriptions
  facts.py      deterministic investigation + derived policy flags
  schemas.py    Intent, Plan, PlannedAction (structured output models)
  state.py      AgentState, ActionRecord, Outcome
  events.py     emit()/step() via LangGraph custom stream writer
```
LLM calls per resolved issue: understand (thinking off), plan (adaptive thinking, effort low),
respond (streamed, thinking off).
