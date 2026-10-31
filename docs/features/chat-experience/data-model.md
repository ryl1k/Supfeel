# Data model

> Status: **planned**. Paths below are the agreed target layout; no code yet. Update when implemented.

Client state only (no DB): `messages[]`, `pendingAction?`, `trail[]`, `status` (`idle`/`streaming`/`awaiting_confirmation`/`error`).
Event types mirror `backend/app/agent/events.py`: `step`, `token`, `action_proposed`, `action_done`,
`verified`, `recommendations`, `error`, `done`.
