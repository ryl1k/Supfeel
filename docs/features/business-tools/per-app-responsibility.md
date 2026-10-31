# Per-app responsibility

> Status: **planned**. Paths below are the agreed target layout; no code yet. Update when implemented.

| App | Responsibility |
|---|---|
| backend | Schema, tools, invariants, seeding, reset |
| frontend | Demo customer picker only (reads `/api/customers/demo`) |
| Neon DB | Stores all business state |
