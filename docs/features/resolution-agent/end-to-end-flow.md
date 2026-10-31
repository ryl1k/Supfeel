# End-to-end flow

> Status: **planned**. Paths below are the agreed target layout; no code yet. Update when implemented.

Hero: *"I bought these sneakers, but they're uncomfortable. Can you help?"*

1. **understand** (LLM #1, structured output) → `intent=comfort_issue`, `entities={product:"sneakers"}`,
   `missing=["fit_problem"]`. Missing info → ask *"What feels off — tight, loose, arch?"* and end turn.
2. Customer: *"Too narrow."* → understand again (cheap, cached prefix) → `fit_problem=narrow`.
3. **investigate** (no LLM): `get_customer`, `list_orders` → order #V1042 delivered 9 days ago,
   Cloud Runner size 10 D, comfort guarantee unused.
4. **retrieve_policy** (embeddings): top-k → comfort guarantee, exchanges, sizing-and-fit.
5. **plan** (LLM #2): `[search_products(wide), create_exchange(10 2E), create_return_label]`,
   `needs_confirmation=true` (exchange).
6. **act** → interrupt: confirmation card → customer approves → tools execute.
7. **verify** (no LLM): exchange order exists with status `processing`; label `active`.
8. **respond** (LLM #3): summary + action trail. Turn ends.

Failure path: verify mismatch → retry tool once → still failing → `escalate_to_human` and tell the customer.
