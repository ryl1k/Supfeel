# Business context

> Status: **done** (Sprint 2). Paths below are real; keep them in sync with the code.

- Source of truth for rules: `knowledge-base/policies/*.md`, especially `agent-authority.md`.
- **Autonomous**: reads, return labels, duplicate-charge refunds, goodwill credit ≤ $25,
  address change on `processing` orders, membership pause.
- **Needs customer confirmation**: refunds to original payment, exchanges, cancellations, reships,
  store credit > $25.
- **Escalate to human**: > $200 refunded/credited in one conversation, 2nd "delivered not received"
  claim in 12 months, data deletion, fraud/legal, explicit request, verification failing twice.
- Retention rule: on membership cancel, offer pause **once**, then comply.
- Tone: own the problem ("I've done X"), concise, at most one apology.
- Identity: the chat session is tied to a demo customer; never expose other customers' data.
