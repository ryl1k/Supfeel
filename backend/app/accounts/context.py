"""The account the current work is billed to. Set at entry points (ticket turn, index job, ask, MCP call);
read by the usage ledger so every Claude/OpenAI call is attributed without threading ids through every layer."""

from contextvars import ContextVar

current_account: ContextVar[str | None] = ContextVar("supfeel_account", default=None)
