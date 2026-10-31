# Backend structure

> Status: **planned**. Paths below are the agreed target layout; no code yet. Update when implemented.

- `backend/app/api/chat.py` — SSE endpoints (`/api/chat`, `/api/chat/confirm`).
- `backend/app/agent/events.py` — event models; serialized as `event: <type>\ndata: <json>`.
