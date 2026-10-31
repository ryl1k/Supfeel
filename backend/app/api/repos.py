import re
from pathlib import Path

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select

from app.config import get_settings
from app.db.models import ApiOperation, IndexJob, Repo, RepoDoc, RepoFile
from app.db.session import session_scope
from app.obs.trace import load_trace
from app.repos.ask import ask
from app.repos.github import GitHubError, auth_mode, client_for
from app.repos.indexer import repo_id_for, start_job
from app.repos.search import search

router = APIRouter(prefix="/api")
_GITHUB_URL = re.compile(r"^(?:https?://github\.com/|git@github\.com:)?([\w.-]+)/([\w.-]+?)(?:\.git)?/?$")
SECRET_SETTINGS = ("api_token",)


def require_import_rights(x_admin_token: str = Header(default="")) -> None:
    settings = get_settings()
    if not settings.open_import and x_admin_token != settings.admin_token:
        raise HTTPException(status_code=401, detail="admin token required")


def require_admin(x_admin_token: str = Header(default="")) -> None:
    if x_admin_token != get_settings().admin_token:
        raise HTTPException(status_code=401, detail="admin token required")


def parse_full_name(value: str) -> str:
    m = _GITHUB_URL.match(value.strip())
    if not m:
        raise HTTPException(status_code=422, detail="expected owner/name or a github.com URL")
    return f"{m.group(1)}/{m.group(2)}"


def public_settings(settings: dict) -> dict:
    return {
        k: ("••••" + str(v)[-4:] if k in SECRET_SETTINGS and v else v) for k, v in (settings or {}).items()
    }


def repo_view(r: Repo, job: IndexJob | None = None) -> dict:
    return {
        "id": r.id,
        "full_name": r.full_name,
        "source": r.source,
        "default_branch": r.default_branch,
        "head_sha": r.head_sha,
        "status": r.status,
        "error": r.error,
        "stats": r.stats or {},
        "settings": public_settings(r.settings),
        "indexed_at": r.indexed_at.isoformat() if r.indexed_at else None,
        "created_at": r.created_at.isoformat(),
        "html_url": f"https://github.com/{r.full_name}" if r.source == "github" else None,
        "job": job_view(job) if job else None,
    }


def job_view(j: IndexJob) -> dict:
    return {
        "id": j.id,
        "kind": j.kind,
        "trigger": j.trigger,
        "status": j.status,
        "commit_sha": j.commit_sha,
        "progress": j.progress or {},
        "error": j.error,
        "started_at": j.started_at.isoformat(),
        "finished_at": j.finished_at.isoformat() if j.finished_at else None,
    }


async def _get_repo(repo_id: str) -> Repo:
    async with session_scope() as s:
        r = await s.get(Repo, repo_id)
        if r is None:
            raise HTTPException(status_code=404, detail="unknown repository")
        s.expunge(r)
        return r


class ImportRequest(BaseModel):
    repo: str | None = Field(default=None, description="owner/name or GitHub URL")
    branch: str | None = None
    local_path: str | None = None


@router.post("/repos", dependencies=[Depends(require_import_rights)], status_code=201)
async def import_repo(req: ImportRequest) -> dict:
    settings = get_settings()
    async with session_scope() as s:
        if await s.scalar(select(func.count()).select_from(Repo)) >= settings.max_repos:
            raise HTTPException(status_code=409, detail=f"repository limit ({settings.max_repos}) reached")

    if req.local_path:
        if not settings.allow_local_repos:
            raise HTTPException(status_code=403, detail="local repositories are disabled")
        path = Path(req.local_path).expanduser()
        if not path.is_dir():
            raise HTTPException(status_code=422, detail="local_path is not a directory")
        full_name, source, branch, installation_id = f"local/{path.name}", "local", req.branch or "main", None
    elif req.repo:
        full_name, source = parse_full_name(req.repo), "github"
        gh = await client_for(full_name)
        try:
            info = await gh.get_repo(full_name)
        except GitHubError as e:
            hint = "" if gh.auth != "anonymous" else " (private repos need the GitHub App installed)"
            raise HTTPException(status_code=404 if e.status == 404 else 502, detail=f"{e}{hint}") from e
        full_name, branch, installation_id = (
            info["full_name"],
            req.branch or info["default_branch"],
            gh.installation_id,
        )
    else:
        raise HTTPException(status_code=422, detail="give repo or local_path")

    rid = repo_id_for(full_name, source)
    async with session_scope() as s:
        repo = await s.get(Repo, rid)
        if repo is None:
            s.add(
                Repo(
                    id=rid, full_name=full_name, source=source, default_branch=branch, installation_id=installation_id,
                    local_path=str(Path(req.local_path).expanduser().resolve()) if req.local_path else None,
                )
            )  # fmt: skip
    job_id = await start_job(rid, trigger="import")
    return {"id": rid, "job_id": job_id}


@router.get("/repos")
async def list_repos() -> list[dict]:
    async with session_scope() as s:
        repos = (await s.scalars(select(Repo).order_by(Repo.created_at.desc()))).all()
        return [repo_view(r) for r in repos]


@router.get("/repos/{repo_id}")
async def get_repo(repo_id: str) -> dict:
    r = await _get_repo(repo_id)
    async with session_scope() as s:
        job = await s.scalar(
            select(IndexJob).where(IndexJob.repo_id == repo_id).order_by(IndexJob.started_at.desc())
        )
        docs = (
            await s.scalars(
                select(RepoDoc)
                .where(RepoDoc.repo_id == repo_id, RepoDoc.kind == "module")
                .order_by(RepoDoc.key)
            )
        ).all()
        ops = (
            await s.scalars(
                select(ApiOperation).where(ApiOperation.repo_id == repo_id).order_by(ApiOperation.path)
            )
        ).all()
    return {
        **repo_view(r, job),
        "overview": r.overview,
        "modules": [{"key": d.key, "body": d.body, "generated_by": d.generated_by} for d in docs],
        "api_operations": [
            {"operation_id": o.operation_id, "method": o.method, "path": o.path, "summary": o.summary}
            for o in ops
        ],
    }


@router.delete("/repos/{repo_id}", dependencies=[Depends(require_admin)])
async def delete_repo(repo_id: str) -> dict:
    """Removes the repo and everything derived from it (files, chunks, docs, jobs, tickets, notifications)."""
    async with session_scope() as s:
        r = await s.get(Repo, repo_id)
        if r is None:
            raise HTTPException(status_code=404, detail="unknown repository")
        await s.delete(r)
    return {"deleted": repo_id}


@router.get("/repos/{repo_id}/jobs")
async def list_jobs(repo_id: str, limit: int = 20) -> list[dict]:
    async with session_scope() as s:
        jobs = (
            await s.scalars(
                select(IndexJob)
                .where(IndexJob.repo_id == repo_id)
                .order_by(IndexJob.started_at.desc())
                .limit(limit)
            )
        ).all()
        return [job_view(j) for j in jobs]


@router.get("/jobs/{job_id}/trace")
async def job_trace(job_id: str) -> dict:
    return await load_trace(job_id)


@router.post("/repos/{repo_id}/reindex", dependencies=[Depends(require_import_rights)])
async def reindex(repo_id: str) -> dict:
    await _get_repo(repo_id)
    return {"job_id": await start_job(repo_id, trigger="manual")}


class RepoSettings(BaseModel):
    api_base_url: str | None = None
    api_token: str | None = None
    api_spec_url: str | None = None
    auto_fix: bool | None = Field(default=None, description="open fix pull requests for confirmed bugs")
    business_name: str | None = None


@router.patch("/repos/{repo_id}/settings", dependencies=[Depends(require_admin)])
async def update_settings(repo_id: str, body: RepoSettings) -> dict:
    async with session_scope() as s:
        r = await s.get(Repo, repo_id)
        if r is None:
            raise HTTPException(status_code=404, detail="unknown repository")
        r.settings = {**(r.settings or {}), **body.model_dump(exclude_none=True)}
        return public_settings(r.settings)


@router.get("/repos/{repo_id}/search")
async def search_repo(repo_id: str, q: str, k: int = 8, kind: str | None = None) -> list[dict]:
    await _get_repo(repo_id)
    hits = await search(repo_id, q, k=min(k, 25), kinds=(kind,) if kind else None)
    return [h.to_dict() | {"cite": h.cite()} for h in hits]


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)


@router.post("/repos/{repo_id}/ask")
async def ask_repo(repo_id: str, body: AskRequest) -> dict:
    r = await _get_repo(repo_id)
    if r.status not in ("ready", "indexing") or not r.indexed_at:
        raise HTTPException(status_code=409, detail="repository is not indexed yet")
    return await ask(repo_id, body.question)


@router.get("/repos/{repo_id}/files")
async def list_files(repo_id: str, prefix: str = "") -> list[dict]:
    async with session_scope() as s:
        rows = (
            await s.execute(
                select(RepoFile.path, RepoFile.language, RepoFile.size)
                .where(RepoFile.repo_id == repo_id, RepoFile.path.startswith(prefix))
                .order_by(RepoFile.path)
                .limit(3000)
            )
        ).all()
    return [{"path": p, "language": lang, "size": size} for p, lang, size in rows]


@router.get("/repos/{repo_id}/file")
async def get_file(repo_id: str, path: str) -> dict:
    async with session_scope() as s:
        f = await s.scalar(select(RepoFile).where(RepoFile.repo_id == repo_id, RepoFile.path == path))
        if f is None:
            raise HTTPException(status_code=404, detail="file not indexed")
        return {"path": f.path, "language": f.language, "content": f.content, "outline": f.outline}


@router.get("/github/status")
async def github_status() -> dict:
    s = get_settings()
    return {
        "auth": auth_mode(),
        "app_slug": s.github_app_slug or None,
        "install_url": f"https://github.com/apps/{s.github_app_slug}/installations/new"
        if s.github_app_slug
        else None,
        "webhook_configured": bool(s.github_webhook_secret),
        "open_import": s.open_import,
        "allow_local_repos": s.allow_local_repos,
    }
