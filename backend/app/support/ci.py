"""Verification of code fixes: the repository's own CI on the fix PR.

A background poller follows each fix PR's head commit; GitHub webhooks (check_suite / workflow_run /
pull_request) trigger an immediate refresh. Results update the ticket, notify the business and, on merge,
tell the customer the fix is live and feed the ticket into learning.
"""

import asyncio
import logging

from sqlalchemy import select

from app.config import get_settings
from app.db.models import Repo, Ticket, TicketMessage
from app.db.session import session_scope
from app.obs import trace
from app.repos.github import GitHubError, client_for
from app.support.notify import notify

log = logging.getLogger(__name__)
_tasks: set[asyncio.Task] = set()


async def _load(ticket_id: str) -> tuple[Ticket, Repo] | None:
    async with session_scope() as s:
        t = await s.get(Ticket, ticket_id)
        if t is None:
            return None
        r = await s.get(Repo, t.repo_id)
        s.expunge(t)
        s.expunge(r)
        return t, r


async def refresh(ticket_id: str) -> str | None:
    """Fetch CI state for the ticket's fix PR; apply it once it is terminal. Returns the state."""
    loaded = await _load(ticket_id)
    if loaded is None:
        return None
    t, repo = loaded
    fix = dict(t.fix or {})
    if fix.get("mode") != "pr" or not fix.get("head_sha"):
        return None
    async with trace.span("check ci", kind="tool", trace_id=ticket_id, sha=fix["head_sha"]) as sp:
        gh = await client_for(repo.full_name, repo.installation_id)
        try:
            ci = await gh.ci_status(repo.full_name, fix["head_sha"])
        except GitHubError as e:
            sp.set(error=str(e))
            return None
        sp.set(
            state=ci["state"], checks=[f"{c['name']}: {c['conclusion'] or c['status']}" for c in ci["checks"]]
        )
    previous = (fix.get("ci") or {}).get("state")
    fix["ci"] = ci
    status = t.status
    if (
        ci["state"] != previous
        and ci["state"] in ("success", "failure")
        and t.status in ("fix_in_review", "fix_verified", "fix_failed")
    ):
        status = "fix_verified" if ci["state"] == "success" else "fix_failed"
        if ci["state"] == "success":
            await notify(
                repo.id,
                "ci_passed",
                f"CI passed on the fix for {t.id}",
                f"{t.subject}\nReady for review and merge.",
                fix.get("pr_url"),
                t.id,
            )
        else:
            failed = ", ".join(
                c["name"]
                for c in ci["checks"]
                if c["conclusion"] not in (None, "success", "skipped", "neutral")
            )
            await notify(
                repo.id,
                "ci_failed",
                f"CI failed on the fix for {t.id}",
                f"Failing: {failed}. A human should take a look.",
                fix.get("pr_url"),
                t.id,
            )
    async with session_scope() as s:
        row = await s.get(Ticket, ticket_id)
        row.fix, row.status = fix, status
    return ci["state"]


async def _poll(ticket_id: str) -> None:
    settings = get_settings()
    for _ in range(settings.ci_poll_max):
        await asyncio.sleep(settings.ci_poll_seconds)
        try:
            state = await refresh(ticket_id)
        except Exception:  # keep polling through transient errors
            log.exception("ci refresh failed for %s", ticket_id)
            continue
        if state in ("success", "failure", None):
            return


def track(ticket_id: str) -> None:
    task = asyncio.create_task(_poll(ticket_id))
    _tasks.add(task)
    task.add_done_callback(_tasks.discard)


async def tickets_for(full_name: str, *, sha: str | None = None, branch: str | None = None) -> list[str]:
    async with session_scope() as s:
        repo_ids = (await s.scalars(select(Repo.id).where(Repo.full_name.ilike(full_name)))).all()
        if not repo_ids:
            return []
        rows = (await s.scalars(select(Ticket).where(Ticket.repo_id.in_(repo_ids)))).all()
        return [
            t.id for t in rows
            if (sha and (t.fix or {}).get("head_sha") == sha) or (branch and (t.fix or {}).get("branch") == branch)
        ]  # fmt: skip


async def on_pr_closed(full_name: str, branch: str, merged: bool) -> list[str]:
    from app.support import service  # late import: service imports this module

    done = []
    for ticket_id in await tickets_for(full_name, branch=branch):
        loaded = await _load(ticket_id)
        if loaded is None:
            continue
        t, repo = loaded
        async with trace.span("pull request closed", kind="run", trace_id=ticket_id, merged=merged):
            if merged:
                async with session_scope() as s:
                    row = await s.get(Ticket, ticket_id)
                    row.status = "resolved"
                    row.resolution = {
                        **(row.resolution or {}),
                        "summary": f"Fix merged: {(row.fix or {}).get('summary', '')}",
                        "merged": True,
                    }
                    s.add(
                        TicketMessage(
                            ticket_id=ticket_id,
                            role="agent",
                            content="Good news: the fix for the problem you reported is now live. Thanks for letting us know!",
                        )
                    )
                await notify(
                    repo.id,
                    "pr_merged",
                    f"Fix for {ticket_id} merged",
                    t.subject,
                    (t.fix or {}).get("pr_url"),
                    ticket_id,
                )
                await service.learn_ticket(ticket_id)
            else:
                async with session_scope() as s:
                    row = await s.get(Ticket, ticket_id)
                    row.status = "escalated"
                    row.resolution = {
                        **(row.resolution or {}),
                        "summary": "Fix PR closed without merging; handed to a human.",
                    }
        done.append(ticket_id)
    return done
