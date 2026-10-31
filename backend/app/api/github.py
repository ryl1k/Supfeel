"""GitHub App webhook: re-index on push to the default branch, verify fixes on CI events, close the loop
on merged fix PRs, and remember installations."""

import json
import logging

from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import select, update

from app.db.models import Repo
from app.db.session import session_scope
from app.repos.github import verify_signature
from app.repos.indexer import start_job
from app.support import ci

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/github")


async def _repo_for(full_name: str) -> Repo | None:
    async with session_scope() as s:
        r = await s.scalar(select(Repo).where(Repo.full_name.ilike(full_name), Repo.source == "github"))
        if r:
            s.expunge(r)
        return r


@router.post("/webhook", status_code=202)
async def webhook(request: Request) -> dict:
    body = await request.body()
    if not verify_signature(body, request.headers.get("x-hub-signature-256")):
        raise HTTPException(status_code=401, detail="bad signature")
    event = request.headers.get("x-github-event", "")
    payload = json.loads(body or b"{}")
    full_name = (payload.get("repository") or {}).get("full_name", "")

    if event == "ping":
        return {"ok": True, "event": "ping"}

    if event == "push":
        repo = await _repo_for(full_name)
        if repo and payload.get("ref") == f"refs/heads/{repo.default_branch}":
            job_id = await start_job(repo.id, trigger="push")
            return {"ok": True, "reindex": job_id}
        return {"ok": True, "ignored": "not the default branch of an imported repo"}

    if event in ("check_suite", "workflow_run", "check_run", "status"):
        obj = payload.get(event) or {}
        sha = obj.get("head_sha") or payload.get("sha")
        tickets = await ci.tickets_for(full_name, sha=sha) if sha else []
        for t in tickets:
            await ci.refresh(t)
        return {"ok": True, "refreshed": tickets}

    if event == "pull_request" and payload.get("action") == "closed":
        pr = payload.get("pull_request") or {}
        branch = (pr.get("head") or {}).get("ref", "")
        if branch.startswith("supfeel/"):
            return {"ok": True, "closed": await ci.on_pr_closed(full_name, branch, bool(pr.get("merged")))}
        return {"ok": True}

    if event in ("installation", "installation_repositories"):
        inst_id = (payload.get("installation") or {}).get("id")
        repos = payload.get("repositories") or payload.get("repositories_added") or []
        async with session_scope() as s:
            for r in repos:
                await s.execute(
                    update(Repo).where(Repo.full_name.ilike(r["full_name"])).values(installation_id=inst_id)
                )
        return {"ok": True, "installation": inst_id}

    return {"ok": True, "ignored": event}
