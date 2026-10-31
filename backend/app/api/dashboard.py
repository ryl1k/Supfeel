"""Workspace board: ticket stats (last 30 days), daily series, outcomes and onboarding progress."""

from collections import Counter
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter
from sqlalchemy import select

from app.accounts import billing
from app.accounts.auth import CurrentPrincipal
from app.db.models import ApiKey, Repo, Ticket, TicketAction
from app.db.session import session_scope

router = APIRouter(prefix="/api")
DAYS = 14
AUTOMATED = {"answered", "resolved", "fix_in_review", "fix_verified", "reported", "awaiting_confirmation"}


@router.get("/dashboard")
async def dashboard(p: CurrentPrincipal) -> dict:
    since = datetime.now(UTC) - timedelta(days=30)
    async with session_scope() as s:
        repo_stmt = select(Repo)
        if not p.is_admin:
            repo_stmt = repo_stmt.where(Repo.account_id == p.account_id)
        repos = (await s.scalars(repo_stmt)).all()
        repo_ids = [r.id for r in repos]
        tickets = (
            (
                await s.scalars(
                    select(Ticket).where(Ticket.repo_id.in_(repo_ids), Ticket.created_at >= since)
                )
            ).all()
            if repo_ids
            else []
        )
        any_ticket = (
            bool(repo_ids)
            and (await s.scalar(select(Ticket.id).where(Ticket.repo_id.in_(repo_ids)).limit(1))) is not None
        )
        mcp_ticket = (
            bool(repo_ids)
            and (
                await s.scalar(
                    select(Ticket.id).where(Ticket.repo_id.in_(repo_ids), Ticket.channel == "mcp").limit(1)
                )
            )
            is not None
        )
        actions = (
            (
                await s.scalars(
                    select(TicketAction).where(TicketAction.ticket_id.in_([t.id for t in tickets]))
                )
            ).all()
            if tickets
            else []
        )
        keys = 0
        if not p.is_admin:
            keys = len(
                (
                    await s.scalars(
                        select(ApiKey.id).where(ApiKey.account_id == p.account_id, ApiKey.revoked.is_(False))
                    )
                ).all()
            )

    today = datetime.now(UTC).date()
    per_day = Counter(t.created_at.astimezone(UTC).date() for t in tickets)
    daily = [
        {"date": (today - timedelta(days=i)).isoformat(), "count": per_day.get(today - timedelta(days=i), 0)}
        for i in range(DAYS - 1, -1, -1)
    ]
    fixes = [t.fix or {} for t in tickets if (t.fix or {}).get("decision")]
    billing_summary = await billing.summary(p.account_id) if not p.is_admin else None
    ready = [r for r in repos if r.status == "ready"]
    return {
        "window_days": 30,
        "tickets": len(tickets),
        "automated": sum(t.status in AUTOMATED for t in tickets),
        "escalated_to_human": sum(t.status == "escalated" for t in tickets),
        "by_category": dict(Counter(t.category or "other" for t in tickets)),
        "by_status": dict(Counter(t.status for t in tickets)),
        "by_channel": dict(Counter(t.channel for t in tickets)),
        "daily": daily,
        "fixes": {
            "prs": sum(1 for f in fixes if f.get("pr_url")),
            "ci_passed": sum(1 for f in fixes if (f.get("ci") or {}).get("state") == "success"),
            "patches": sum(1 for f in fixes if f.get("decision") == "fixed"),
            "not_a_bug": sum(1 for f in fixes if f.get("decision") == "not_a_bug"),
        },
        "actions": {
            "done": sum(a.status == "done" for a in actions),
            "verified": sum(bool((a.verification or {}).get("ok")) for a in actions),
        },
        "learned": sum(t.learned for t in tickets),
        "onboarding": {
            "repo_imported": bool(repos),
            "repo_ready": bool(ready),
            "api_connected": any((r.settings or {}).get("api_base_url") for r in repos),
            "key_created": keys > 0,
            "first_ticket": any_ticket,
            "first_mcp_escalation": mcp_ticket,
            "payment_method": bool(billing_summary and billing_summary["payment_method"]),
            "first_repo_id": (ready or repos)[0].id if repos else None,
        },
        "billing": billing_summary,
    }
