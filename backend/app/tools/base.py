"""Shared tool plumbing: context, errors, formatting helpers."""

import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession


class ToolError(Exception):
    """A business invariant was violated. `code` is machine-readable, `message` is for the agent."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message

    def to_dict(self) -> dict:
        return {"error": self.code, "message": self.message}


@dataclass
class ToolContext:
    session: AsyncSession
    customer_id: str
    conversation_id: str | None = None
    action_id: str | None = None


def new_id(prefix: str) -> str:
    return f"{prefix}-{secrets.token_hex(3).upper()}"


def money(cents: int) -> str:
    sign = "-" if cents < 0 else ""
    return f"{sign}${abs(cents) / 100:,.2f}"


def now() -> datetime:
    return datetime.now(UTC)


def days_since(dt: datetime | None) -> int | None:
    if dt is None:
        return None
    return (now() - dt).days


def business_days_since(dt: datetime | None) -> int | None:
    if dt is None:
        return None
    count, day = 0, dt.date()
    end = now().date()
    while day < end:
        day += timedelta(days=1)
        if day.weekday() < 5:
            count += 1
    return count


def iso(dt: datetime | None) -> str | None:
    return dt.isoformat() if dt else None
