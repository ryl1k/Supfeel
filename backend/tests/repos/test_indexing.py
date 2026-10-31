import json
import shutil
from pathlib import Path

import pytest
from sqlalchemy import delete, func, select

from app.config import REPO_ROOT
from app.db.models import ApiOperation, Repo, RepoChunk, RepoDoc, RepoFile
from app.db.session import session_scope
from app.repos import openapi, source
from app.repos.chunker import chunk_file, language_for, outline
from app.repos.indexer import repo_id_for, start_job
from app.repos.search import search

SLICE = REPO_ROOT / "examples" / "slice-pizza"


def test_keep_path_filters():
    assert source.keep_path("src/app.py") is None
    assert source.keep_path("node_modules/x/index.js") == "ignored_dir"
    assert source.keep_path("package-lock.json") == "lockfile"
    assert source.keep_path(".env") == "secret"
    assert source.keep_path("logo.png") == "binary"


def test_outline_and_chunks_for_python():
    code = (SLICE / "slice_api" / "pricing.py").read_text()
    symbols = [o["symbol"] for o in outline(code, "python")]
    assert {"subtotal", "discount", "delivery_fee", "price", "PromoError"} <= set(symbols)
    chunks = chunk_file("slice_api/pricing.py", code, "python")
    assert chunks and all(c.kind == "code" for c in chunks)
    assert chunks[0].start_line == 1 and chunks[-1].end_line >= len(code.splitlines()) - 1
    assert language_for("README.md") == "markdown" and language_for("Dockerfile") == "docker"


def test_openapi_operations():
    doc = openapi.parse((SLICE / "openapi.json").read_text())
    ops = {o["operation_id"]: o for o in openapi.operations(doc, "openapi.json")}
    assert {"list_menu", "create_order", "cancel_order", "get_order", "add_address"} <= set(ops)
    assert ops["create_order"]["method"] == "POST"
    assert "items" in ops["create_order"]["body_schema"]["properties"]
    assert ops["cancel_order"]["parameters"][0]["name"] == "order_id"


@pytest.fixture
async def slice_repo(tmp_path: Path):
    root = tmp_path / "slice"
    shutil.copytree(SLICE, root, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
    rid = repo_id_for("demo/slice", "local")
    async with session_scope() as s:
        await s.execute(delete(Repo).where(Repo.id == rid))
        s.add(Repo(id=rid, full_name="demo/slice", source="local", local_path=str(root)))
    yield rid, root
    async with session_scope() as s:
        await s.execute(delete(Repo).where(Repo.id == rid))


async def _count(model, repo_id, **filters):
    async with session_scope() as s:
        stmt = select(func.count()).select_from(model).where(model.repo_id == repo_id)
        for k, v in filters.items():
            stmt = stmt.where(getattr(model, k) == v)
        return await s.scalar(stmt)


async def test_index_local_repo_end_to_end(slice_repo):
    rid, root = slice_repo
    await start_job(rid, trigger="import", background=False)
    async with session_scope() as s:
        repo = await s.get(Repo, rid)
        assert repo.status == "ready", repo.error
        assert repo.stats["files"] >= 8
        assert repo.stats["api_operations"] >= 6
        assert repo.overview
    assert await _count(ApiOperation, rid) >= 6
    assert await _count(RepoDoc, rid, kind="overview") == 1
    assert await _count(RepoDoc, rid, kind="module") >= 3
    assert await _count(RepoChunk, rid, kind="code") > 0

    hits = await search(rid, "invalid address street number validation regex", k=5)
    assert any(h.path == "slice_api/validation.py" for h in hits)

    # unchanged re-index embeds nothing
    job = await start_job(rid, trigger="push", background=False)
    from app.db.models import IndexJob

    async with session_scope() as s:
        progress = (await s.get(IndexJob, job)).progress
    assert progress["changed"] == 0 and progress["chunks_embedded"] == 0

    # a changed file is the only thing re-embedded; deleted files disappear
    (root / "slice_api" / "pricing.py").write_text(
        (root / "slice_api" / "pricing.py").read_text() + "\n# touched\n"
    )
    (root / "docs" / "support-faq.md").unlink()
    job = await start_job(rid, trigger="push", background=False)
    async with session_scope() as s:
        progress = (await s.get(IndexJob, job)).progress
        paths = set((await s.scalars(select(RepoFile.path).where(RepoFile.repo_id == rid))).all())
    assert progress["changed"] == 1 and progress["deleted"] == 1
    assert "docs/support-faq.md" not in paths


async def test_index_job_is_traced(slice_repo):
    from app.obs.trace import load_trace

    rid, _ = slice_repo
    job = await start_job(rid, trigger="import", background=False)
    t = await load_trace(job)
    names = {s["name"] for s in t["spans"]}
    assert {
        "index repository",
        "download snapshot",
        "embed chunks",
        "explain modules",
        "write overview",
    } <= names
    root = next(s for s in t["spans"] if s["parent_id"] is None)
    assert all(s["parent_id"] == root["id"] for s in t["spans"] if s["name"] == "embed chunks")
    assert json.dumps(t)  # serializable for the API
