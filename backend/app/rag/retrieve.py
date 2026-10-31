"""Top-k policy retrieval over kb_chunks (pgvector cosine distance)."""

from dataclasses import asdict, dataclass

from sqlalchemy import select

from app.db.models import KbChunk
from app.db.session import session_scope
from app.rag.embeddings import active_model, embed


@dataclass
class RetrievedChunk:
    doc_id: str
    doc_title: str
    heading: str
    text: str
    audience: str
    score: float

    def to_dict(self) -> dict:
        return asdict(self)

    def cite(self) -> str:
        return f"{self.doc_title} › {self.heading}"


async def retrieve(
    query: str, k: int = 5, audience: str | None = None, min_score: float = 0.0
) -> list[RetrievedChunk]:
    model = active_model()
    [qvec] = await embed([query], node="kb_query")
    distance = KbChunk.embedding.cosine_distance(qvec)
    stmt = select(KbChunk, distance.label("distance")).where(KbChunk.embedding_model == model)
    if audience:
        stmt = stmt.where(KbChunk.audience == audience)
    stmt = stmt.order_by(distance).limit(k)
    async with session_scope() as s:
        rows = (await s.execute(stmt)).all()
    results = [
        RetrievedChunk(c.doc_id, c.doc_title, c.heading, c.text, c.audience, round(1 - float(d), 4))
        for c, d in rows
    ]
    return [r for r in results if r.score >= min_score]


async def get_section(doc_id: str, heading_prefix: str) -> RetrievedChunk | None:
    """Fetch a specific policy section by doc and heading (used to pin must-have policies)."""
    model = active_model()
    async with session_scope() as s:
        c = await s.scalar(
            select(KbChunk).where(
                KbChunk.embedding_model == model,
                KbChunk.doc_id == doc_id,
                KbChunk.heading.ilike(f"{heading_prefix}%"),
            )
        )
    return RetrievedChunk(c.doc_id, c.doc_title, c.heading, c.text, c.audience, 1.0) if c else None
