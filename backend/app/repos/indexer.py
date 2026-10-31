"""Index a repository into pgvector: files, code/doc chunks, API operations, module summaries, overview.

Every run downloads one snapshot (one tarball request) and re-embeds only files whose content changed, so a
re-index after a push costs roughly the size of the diff. One job runs per repo at a time; a push that
arrives mid-run queues exactly one follow-up run.

Each job is a trace (trace_id = job id) visible in the dashboard.
"""

import asyncio
import hashlib
import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import delete, func, select, update

from app.config import get_settings
from app.db.models import ApiOperation, IndexJob, LlmUsage, Repo, RepoChunk, RepoDoc, RepoFile
from app.db.session import session_scope
from app.obs import trace
from app.rag.embeddings import active_model, embed
from app.repos import explain, openapi, source
from app.repos.chunker import chunk_file, language_for, outline
from app.repos.github import client_for

log = logging.getLogger(__name__)
INSERT_BATCH = 200
_tasks: set[asyncio.Task] = set()


def repo_id_for(full_name: str, src: str = "github") -> str:
    name = full_name.strip().strip("/").lower()
    if src == "github":
        return name.replace("/", "__")
    return "local__" + name.removeprefix("local/").replace("/", "__")


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


async def _progress(job_id: str, **kv: Any) -> None:
    async with session_scope() as s:
        job = await s.get(IndexJob, job_id)
        if job:
            job.progress = {**(job.progress or {}), **kv}


# ---------------------------------------------------------------------------------------------- jobs


async def start_job(repo_id: str, trigger: str = "manual", background: bool = True) -> str:
    """Create an index job. If one is already running for this repo, request a follow-up run instead."""
    async with session_scope() as s:
        running = await s.scalar(
            select(IndexJob).where(IndexJob.repo_id == repo_id, IndexJob.status.in_(("queued", "running")))
        )
        if running:
            running.progress = {**(running.progress or {}), "rerun_requested": True}
            return running.id
        job = IndexJob(
            id="job_" + uuid.uuid4().hex[:12],
            repo_id=repo_id,
            kind="full" if trigger == "import" else "incremental",
            trigger=trigger,
        )
        s.add(job)
        await s.execute(update(Repo).where(Repo.id == repo_id).values(status="indexing", error=None))
        job_id = job.id
    if background:
        task = asyncio.create_task(run_job(job_id))
        _tasks.add(task)
        task.add_done_callback(_tasks.discard)
    else:
        await run_job(job_id)
    return job_id


async def run_job(job_id: str) -> None:
    async with session_scope() as s:
        job = await s.get(IndexJob, job_id)
        job.status = "running"
        repo_id = job.repo_id
    try:
        async with trace.span("index repository", kind="run", trace_id=job_id, repo_id=repo_id) as sp:
            result = await index_repo(repo_id, job_id)
            sp.set(**{k: v for k, v in result.items() if not isinstance(v, (dict, list))})
        async with session_scope() as s:
            job = await s.get(IndexJob, job_id)
            job.status, job.finished_at, job.commit_sha = "done", datetime.now(UTC), result.get("sha")
            job.progress = {**(job.progress or {}), **result, "phase": "done"}
            rerun = (job.progress or {}).get("rerun_requested")
    except Exception as e:  # surface the failure on the repo and the job
        log.exception("index job %s failed", job_id)
        async with session_scope() as s:
            job = await s.get(IndexJob, job_id)
            job.status, job.finished_at, job.error = (
                "failed",
                datetime.now(UTC),
                f"{type(e).__name__}: {e}"[:1000],
            )
            rerun = False
            await s.execute(update(Repo).where(Repo.id == repo_id).values(status="failed", error=job.error))
        return
    if rerun:
        await start_job(repo_id, trigger="push")


async def recover_stale_jobs() -> int:
    """On boot: jobs left 'running' by a restart can never finish; mark them failed."""
    async with session_scope() as s:
        res = await s.execute(
            update(IndexJob)
            .where(IndexJob.status.in_(("queued", "running")))
            .values(status="failed", error="interrupted by a restart", finished_at=datetime.now(UTC))
        )
        await s.execute(
            update(Repo).where(Repo.status == "indexing").values(status="failed", error="interrupted")
        )
        return res.rowcount or 0


# ---------------------------------------------------------------------------------------------- indexing


async def index_repo(repo_id: str, job_id: str) -> dict[str, Any]:
    model = active_model()
    async with session_scope() as s:
        repo = await s.get(Repo, repo_id)
        s.expunge(repo)

    await _progress(job_id, phase="download")
    async with trace.span("download snapshot", kind="step", source=repo.source) as sp:
        gh = None
        if repo.source == "github":
            gh = await client_for(repo.full_name, repo.installation_id)
            if gh.installation_id and gh.installation_id != repo.installation_id:
                async with session_scope() as s:
                    (await s.get(Repo, repo_id)).installation_id = gh.installation_id
        snap = await source.fetch(repo.source, repo.full_name, repo.default_branch, gh, repo.local_path)
        sp.set(
            sha=snap.sha,
            files=len(snap.files),
            skipped=snap.skipped,
            bytes=snap.total_bytes,
            auth=gh.auth if gh else "local",
        )

    # --- diff against what is stored
    async with session_scope() as s:
        existing = {
            p: h
            for p, h in (
                await s.execute(
                    select(RepoFile.path, RepoFile.content_hash).where(RepoFile.repo_id == repo_id)
                )
            ).all()
        }
        has_model_chunks = bool(
            await s.scalar(
                select(func.count())
                .select_from(RepoChunk)
                .where(RepoChunk.repo_id == repo_id, RepoChunk.embedding_model == model)
            )
        )
    hashes = {p: _sha(t) for p, t in snap.files.items()}
    if existing and not has_model_chunks:
        existing = {}  # embedding model changed (e.g. mock -> OpenAI): rebuild everything
    changed = [p for p, h in hashes.items() if existing.get(p) != h]
    deleted = [p for p in existing if p not in hashes]
    outlines = {p: outline(t, language_for(p)) for p, t in snap.files.items()}

    async with trace.span("update files", kind="step", changed=len(changed), deleted=len(deleted)):
        async with session_scope() as s:
            stale = changed + deleted
            for i in range(0, len(stale), 500):
                part = stale[i : i + 500]
                await s.execute(delete(RepoFile).where(RepoFile.repo_id == repo_id, RepoFile.path.in_(part)))
                await s.execute(
                    delete(RepoChunk).where(
                        RepoChunk.repo_id == repo_id,
                        RepoChunk.kind.in_(("code", "doc")),
                        RepoChunk.path.in_(part),
                    )
                )
            if not existing:
                await s.execute(
                    delete(RepoChunk).where(
                        RepoChunk.repo_id == repo_id, RepoChunk.kind.in_(("code", "doc", "summary", "api"))
                    )
                )
                await s.execute(delete(RepoFile).where(RepoFile.repo_id == repo_id))
                # Docs are regenerated too, so their summary chunks come back with the new embedding model
                # (identical Claude requests are served from the request cache, so this costs nothing twice).
                await s.execute(delete(RepoDoc).where(RepoDoc.repo_id == repo_id))
            for p in changed:
                s.add(
                    RepoFile(
                        repo_id=repo_id, path=p, language=language_for(p), size=len(snap.files[p]),
                        content_hash=hashes[p], content=snap.files[p], outline=outlines[p],
                    )
                )  # fmt: skip

    # --- chunk + embed changed files
    chunks = [c for p in changed for c in chunk_file(p, snap.files[p], language_for(p))]
    await _progress(
        job_id,
        phase="embed",
        files=len(snap.files),
        changed=len(changed),
        chunks_total=len(chunks),
        chunks_done=0,
    )
    async with trace.span("embed chunks", kind="step", chunks=len(chunks), model=model):
        for i in range(0, len(chunks), INSERT_BATCH):
            part = chunks[i : i + INSERT_BATCH]
            texts = [c.embed_text(language_for(c.path)) for c in part]
            vectors = await embed(texts, node="repo_index")
            async with session_scope() as s:
                for c, t, v in zip(part, texts, vectors, strict=True):
                    s.add(
                        RepoChunk(
                            repo_id=repo_id, kind=c.kind, path=c.path, symbol=c.symbol[:200], start_line=c.start_line,
                            end_line=c.end_line, text=c.text, content_hash=_sha(model + t), embedding_model=model, embedding=v,
                        )
                    )  # fmt: skip
            await _progress(job_id, chunks_done=min(i + INSERT_BATCH, len(chunks)))

    await _reembed_tickets(repo_id, model)
    ops = await _index_api(repo, snap.files, model)
    await _progress(job_id, phase="explain")
    modules_done = await _explain(repo, snap.files, outlines, job_id, model)

    # --- stats
    async with session_scope() as s:
        files_n = await s.scalar(
            select(func.count()).select_from(RepoFile).where(RepoFile.repo_id == repo_id)
        )
        chunk_rows = (
            await s.execute(
                select(RepoChunk.kind, func.count())
                .where(RepoChunk.repo_id == repo_id)
                .group_by(RepoChunk.kind)
            )
        ).all()
        langs = (
            await s.execute(
                select(RepoFile.language, func.count())
                .where(RepoFile.repo_id == repo_id)
                .group_by(RepoFile.language)
            )
        ).all()
        cost = await s.scalar(
            select(func.coalesce(func.sum(LlmUsage.cost_usd), 0)).where(
                LlmUsage.conversation_id == f"job:{job_id}"
            )
        )
        r = await s.get(Repo, repo_id)
        r.head_sha, r.status, r.error, r.indexed_at = snap.sha, "ready", None, datetime.now(UTC)
        r.stats = {
            "files": files_n,
            "chunks": dict(chunk_rows),
            "languages": dict(sorted(langs, key=lambda x: -x[1])),
            "api_operations": ops,
            "modules": modules_done["modules"],
            "skipped": snap.skipped,
            "bytes": snap.total_bytes,
            "embedding_model": model,
            "last_job_claude_usd": float(cost or 0),
        }
    return {
        "sha": snap.sha, "files": len(snap.files), "changed": len(changed), "deleted": len(deleted),
        "chunks_embedded": len(chunks), "api_operations": ops, **modules_done,
    }  # fmt: skip


async def _reembed_tickets(repo_id: str, model: str) -> None:
    """Learned tickets survive an embedding-model switch: re-embed them with the active model."""
    async with session_scope() as s:
        old = (
            await s.scalars(
                select(RepoChunk).where(
                    RepoChunk.repo_id == repo_id,
                    RepoChunk.kind == "ticket",
                    RepoChunk.embedding_model != model,
                )
            )
        ).all()
        if not old:
            return
        vectors = await embed([c.text for c in old], node="ticket_learn")
        for c, v in zip(old, vectors, strict=True):
            c.embedding, c.embedding_model, c.content_hash = v, model, _sha(model + c.text)


async def _index_api(repo: Repo, files: dict[str, str], model: str) -> int:
    async with trace.span("discover api", kind="step") as sp:
        ops: list[dict[str, Any]] = []
        for path, doc in openapi.find_specs(files):
            ops += openapi.operations(doc, path)
        spec_url = (repo.settings or {}).get("api_spec_url")
        if spec_url:
            try:
                doc = await openapi.fetch_spec(spec_url)
                if doc:
                    ops += openapi.operations(doc, spec_url)
            except Exception as e:  # a down API must not fail indexing
                sp.set(spec_error=str(e)[:200])
        seen: set[str] = set()
        ops = [o for o in ops if not (o["operation_id"] in seen or seen.add(o["operation_id"]))]
        texts = [openapi.describe(o) for o in ops]
        vectors = await embed(texts, node="repo_index") if texts else []
        async with session_scope() as s:
            await s.execute(delete(ApiOperation).where(ApiOperation.repo_id == repo.id))
            await s.execute(delete(RepoChunk).where(RepoChunk.repo_id == repo.id, RepoChunk.kind == "api"))
            for o, t, v in zip(ops, texts, vectors, strict=True):
                s.add(ApiOperation(repo_id=repo.id, **o))
                s.add(
                    RepoChunk(
                        repo_id=repo.id,
                        kind="api",
                        path=o["source"],
                        symbol=o["operation_id"],
                        text=t,
                        content_hash=_sha(model + t),
                        embedding_model=model,
                        embedding=v,
                    )
                )
        sp.set(operations=len(ops))
        return len(ops)


async def _explain(
    repo: Repo, files: dict[str, str], outlines: dict[str, list[dict]], job_id: str, model: str
) -> dict[str, Any]:
    settings = get_settings()
    modules = explain.group_modules(files)
    async with session_scope() as s:
        docs = {d.key: d for d in (await s.scalars(select(RepoDoc).where(RepoDoc.repo_id == repo.id))).all()}
        for d in docs.values():
            s.expunge(d)

    async with trace.span("explain modules", kind="step", modules=len(modules)) as sp:
        inputs = {m.key: explain.module_input(m, files, outlines) for m in modules}
        todo = [
            m
            for m in modules
            if (d := docs.get(m.key)) is None
            or d.kind != "module"
            or d.input_hash != explain.input_hash(inputs[m.key])
        ]
        llm_keys = {m.key for m in modules[: settings.repo_max_modules_summarized]}

        async def one(m):
            res = await explain.summarize_module(inputs[m.key], job_id) if m.key in llm_keys else None
            body, by = res if res else (explain.rules_module_summary(m, outlines, files), "rules")
            return m, body, by

        results = await explain.gather_limited([one(m) for m in todo])
        sp.set(regenerated=len(todo), llm=sum(by == "llm" for _, _, by in results))

    summaries = {k: d.body for k, d in docs.items() if d.kind == "module"}
    texts = []
    for m, body, _ in results:
        summaries[m.key] = body
        texts.append(f"Module {m.key} summary\n\n{body}")
    vectors = await embed(texts, node="repo_index") if texts else []
    current = {m.key for m in modules}
    async with session_scope() as s:
        await s.execute(
            delete(RepoDoc).where(
                RepoDoc.repo_id == repo.id, RepoDoc.kind == "module", RepoDoc.key.notin_(current)
            )
        )
        await s.execute(
            delete(RepoChunk).where(
                RepoChunk.repo_id == repo.id, RepoChunk.kind == "summary", RepoChunk.path.notin_(current)
            )
        )
        for (m, body, by), t, v in zip(results, texts, vectors, strict=True):
            await s.execute(
                delete(RepoDoc).where(
                    RepoDoc.repo_id == repo.id, RepoDoc.key == m.key, RepoDoc.kind == "module"
                )
            )
            await s.execute(
                delete(RepoChunk).where(
                    RepoChunk.repo_id == repo.id, RepoChunk.kind == "summary", RepoChunk.path == m.key
                )
            )
            s.add(
                RepoDoc(
                    repo_id=repo.id,
                    kind="module",
                    key=m.key,
                    title=m.key,
                    body=body,
                    input_hash=explain.input_hash(inputs[m.key]),
                    generated_by=by,
                )
            )
            s.add(
                RepoChunk(
                    repo_id=repo.id,
                    kind="summary",
                    path=m.key,
                    symbol="module summary",
                    text=body,
                    content_hash=_sha(model + t),
                    embedding_model=model,
                    embedding=v,
                )
            )

    async with trace.span("write overview", kind="step") as sp:
        ov_input = explain.overview_input(repo.full_name, files, modules, summaries)
        ov_hash = explain.input_hash(ov_input)
        old = docs.get(".") if docs.get(".") and docs["."].kind == "overview" else None
        if old and old.input_hash == ov_hash and repo.overview:
            sp.set(skipped=True)
        else:
            body = await explain.summarize_overview(ov_input, job_id)
            by = "llm" if body else "rules"
            body = body or explain.rules_overview(repo.full_name, files, modules, summaries)
            [v] = await embed([f"Repository overview {repo.full_name}\n\n{body}"], node="repo_index")
            async with session_scope() as s:
                await s.execute(delete(RepoDoc).where(RepoDoc.repo_id == repo.id, RepoDoc.kind == "overview"))
                await s.execute(
                    delete(RepoChunk).where(
                        RepoChunk.repo_id == repo.id, RepoChunk.kind == "summary", RepoChunk.path == "."
                    )
                )
                s.add(
                    RepoDoc(
                        repo_id=repo.id,
                        kind="overview",
                        key=".",
                        title="Overview",
                        body=body,
                        input_hash=ov_hash,
                        generated_by=by,
                    )
                )
                s.add(
                    RepoChunk(
                        repo_id=repo.id,
                        kind="summary",
                        path=".",
                        symbol="repository overview",
                        text=body,
                        content_hash=_sha(model + body),
                        embedding_model=model,
                        embedding=v,
                    )
                )
                (await s.get(Repo, repo.id)).overview = body
            sp.set(generated_by=by)
    return {"modules": len(modules), "modules_regenerated": len(results)}
