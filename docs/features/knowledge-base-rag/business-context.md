# Business context

> Status: **done** (Sprint 1). Paths below are real; keep them in sync with the code.

- `knowledge-base/policies/agent-authority.md` is `audience: agent` — retrieve it for the agent,
  but never quote it verbatim to customers.
- When retrieval finds nothing relevant (score below threshold), the agent must say policy doesn't
  cover it and escalate — not guess.
- Policy numbers (days, $) in answers must come from retrieved chunks.
