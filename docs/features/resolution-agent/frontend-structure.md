# Frontend structure

> Status: **planned**. Paths below are the agreed target layout; no code yet. Update when implemented.

The agent has no UI of its own. The frontend consumes its SSE events in `frontend/lib/sse.ts` and
renders them in `frontend/components/chat/` (see `docs/features/chat-experience/`).
Event contract lives in `backend/app/agent/events.py` and is mirrored in `frontend/lib/types.ts` —
change both together.
