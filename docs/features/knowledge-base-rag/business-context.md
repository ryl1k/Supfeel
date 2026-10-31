# Business context

> Status: **planned**. Paths below are the agreed target layout; no code yet. Update when implemented.

- `knowledge-base/policies/agent-authority.md` is `audience: agent` — retrieve it for the agent,
  but never quote it verbatim to customers.
- When retrieval finds nothing relevant (score below threshold), the agent must say policy doesn't
  cover it and escalate — not guess.
- Policy numbers (days, $) in answers must come from retrieved chunks.
