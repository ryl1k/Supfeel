"""Chunk knowledge-base/**/*.md on '##' headings and upsert embeddings into kb_chunks.

Idempotent: chunks whose (model, text) hash already exists are not re-embedded.
Run: `uv run python -m app.rag.ingest`
"""

import asyncio
import hashlib
from dataclasses import dataclass
from pathlib import Path

import frontmatter
from sqlalchemy import delete, select

from app.config import get_settings
from app.db.models import KbChunk
from app.db.seed import init_db
from app.db.session import session_scope
from app.rag.embeddings import active_model, embed


@dataclass
class Chunk:
    doc_id: str
    doc_title: str
    heading: str
    text: str
    audience: str
    tags: list[str]

    def embed_text(self) -> str:
        return f"{self.doc_title} — {self.heading}\n\n{self.text}"


def chunk_file(path: Path) -> list[Chunk]:
    post = frontmatter.load(path)
    meta = post.metadata
    doc_id = meta.get("id", path.stem)
    title = meta.get("title", path.stem)
    chunks: list[Chunk] = []
    heading, buf = None, []

    def flush():
        body = "\n".join(buf).strip()
        if heading and body:
            chunks.append(
                Chunk(
                    doc_id, title, heading, body, meta.get("audience", "customer"), list(meta.get("tags", []))
                )
            )

    for line in post.content.splitlines():
        if line.startswith("## "):
            flush()
            heading, buf = line[3:].strip(), []
        elif line.startswith("# "):
            continue
        else:
            buf.append(line)
    flush()
    return chunks


def load_chunks(kb_dir: Path | None = None) -> list[Chunk]:
    kb_dir = kb_dir or get_settings().knowledge_base_dir
    chunks: list[Chunk] = []
    for path in sorted(kb_dir.rglob("*.md")):
        if path.name.lower() == "readme.md":
            continue
        chunks.extend(chunk_file(path))
    return chunks


async def ingest(kb_dir: Path | None = None) -> dict:
    model = active_model()
    chunks = load_chunks(kb_dir)
    hashes = {hashlib.sha256(f"{model}\n{c.embed_text()}".encode()).hexdigest(): c for c in chunks}

    async with session_scope() as s:
        existing = set(
            (await s.scalars(select(KbChunk.content_hash).where(KbChunk.embedding_model == model))).all()
        )
        # Drop chunks for this model that no longer exist in the KB.
        stale = existing - set(hashes)
        if stale:
            await s.execute(delete(KbChunk).where(KbChunk.content_hash.in_(stale)))

    new = [(h, c) for h, c in hashes.items() if h not in existing]
    if new:
        vectors = await embed([c.embed_text() for _, c in new], node="kb_ingest")
        async with session_scope() as s:
            for (h, c), v in zip(new, vectors, strict=True):
                s.add(
                    KbChunk(
                        doc_id=c.doc_id,
                        doc_title=c.doc_title,
                        heading=c.heading,
                        text=c.text,
                        audience=c.audience,
                        tags=c.tags,
                        content_hash=h,
                        embedding_model=model,
                        embedding=v,
                    )
                )
    return {"model": model, "chunks": len(chunks), "embedded": len(new), "removed": len(stale)}


async def _main() -> None:
    await init_db()
    print(await ingest())


if __name__ == "__main__":
    asyncio.run(_main())
