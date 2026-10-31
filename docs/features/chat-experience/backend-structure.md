# Backend structure

> Status: **done** (Sprint 3). Paths below are real; keep them in sync with the code.

- `backend/app/api/chat.py` — SSE endpoints (`/api/chat`, `/api/chat/confirm`).
- `backend/app/agent/events.py` — event models; serialized as `event: <type>\ndata: <json>`.
