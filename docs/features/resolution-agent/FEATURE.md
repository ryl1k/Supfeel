# Resolution agent

> Status: **planned**. Paths below are the agreed target layout; no code yet. Update when implemented.

The core of Supfeel: a LangGraph state machine that takes a customer message and moves it through
**understand → investigate → retrieve_policy → plan → act → verify → respond**.

## Why
Most support bots stop at answers. The resolution agent owns the outcome: it gathers facts, decides
within policy, executes the fix through tools, and proves it worked with a read-back check.

## Scope
- In: intent detection, clarifying questions, deterministic data gathering, policy-grounded planning,
  tool execution, confirmation pauses, verification, customer-facing summary.
- Out: UI rendering (see `chat-experience`), tool implementations (see `business-tools`),
  retrieval internals (see `knowledge-base-rag`), LLM cost logic (see `llm-budget-guard`).

## Success criteria
- Hero scenario resolves end to end with ≤ 3 LLM calls and a verified exchange.
- Never takes an action outside `knowledge-base/policies/agent-authority.md`.
- Every write action has a matching verification result in the event stream.
