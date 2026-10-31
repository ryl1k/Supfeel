"""Verification of code fixes: the repository's own CI on the fix PR.

A background poller follows each fix PR's head commit; GitHub webhooks (check_suite / workflow_run /
pull_request) trigger an immediate refresh. Results update the ticket, notify the business and, on merge,
tell the customer the fix is live and feed the ticket into learning.
"""

import asyncio
import contextvars
import logging

from sqlalchemy import select

from app.config import get_settings
from app.db.models import Repo, Ticket, TicketMessage
from app.db.session import session_scope
from app.obs import trace
from app.repos.github import GitHubError, client_for
from app.support import callbacks
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
    if status != t.status:
        await callbacks.fire(ticket_id, status)
    return ci["state"]


NO_CI_POLLS = 6  # ≈ 2 minutes without any check run → the repo has no CI for this branch


async def _poll(ticket_id: str) -> None:
    settings = get_settings()
    state, none_seen = None, 0
    for _ in range(settings.ci_poll_max):
        await asyncio.sleep(settings.ci_poll_seconds)
        try:
            state = await refresh(ticket_id)
        except Exception:  # keep polling through transient errors
            log.exception("ci refresh failed for %s", ticket_id)
            continue
        if state in ("success", "failure", None):
            return
        none_seen = none_seen + 1 if state == "none" else 0
        if none_seen >= NO_CI_POLLS:
            break
    await _unverified(
        ticket_id, "no CI checks ran on the fix branch" if state == "none" else "CI did not finish in time"
    )


async def _unverified(ticket_id: str, reason: str) -> None:
    """CI never produced a verdict: say so plainly; the PR still waits for human review."""
    loaded = await _load(ticket_id)
    if loaded is None:
        return
    t, repo = loaded
    fix = dict(t.fix or {})
    fix["ci"] = {**(fix.get("ci") or {}), "state": "none", "note": reason}
    async with session_scope() as s:
        (await s.get(Ticket, ticket_id)).fix = fix
    await notify(
        repo.id,
        "ci_missing",
        f"Fix for {t.id} is unverified: {reason}",
        "Please review and test the PR manually.",
        fix.get("pr_url"),
        t.id,
    )


def track(ticket_id: str) -> None:
    # A fresh context: the poller outlives the ticket turn, so its spans must not nest under a finished step.
    task = asyncio.create_task(_poll(ticket_id), context=contextvars.Context())
    _tasks.add(task)
    task.add_done_callback(_tasks.discard)


async def resume_tracking() -> int:
    """On startup: pollers live in memory, so restart them for fixes still waiting on CI."""
    async with session_scope() as s:
        rows = (await s.scalars(select(Ticket).where(Ticket.status == "fix_in_review"))).all()
        ids = [t.id for t in rows if ((t.fix or {}).get("ci") or {}).get("state") in (None, "pending")]
    for ticket_id in ids:
        track(ticket_id)
    return len(ids)


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
                await callbacks.fire(ticket_id, "resolved")
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
