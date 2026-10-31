# Business context

> Status: **done** (Sprint 1). Paths below are real; keep them in sync with the code.

- Tools enforce **hard invariants** (e.g. cannot cancel a shipped order, cannot refund more than paid),
  returning a typed error; the agent enforces **policy** (windows, thresholds) from the KB.
- Money is stored in integer cents.
- Seed scenarios must match the KB:
  - Hero: order delivered 9 days ago, Cloud Runner 10 D, comfort guarantee unused; Cloud Runner 10 2E in stock.
  - Lost package: shipment with no scan for 8 business days.
  - Double charge: two `captured` payments, same order/amount; plus one case of `authorized` hold only.
  - Membership: monthly member, renewal charged 3 days ago, no benefits used.
  - Out of policy: return request at day 45.
