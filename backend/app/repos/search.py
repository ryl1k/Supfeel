"""Retrieval over repo_chunks: semantic (pgvector cosine) with a light keyword boost for exact
identifiers and paths, which pure embeddings often miss in code."""

import re
from dataclasses import asdict, dataclass

from sqlalchemy import or_, select

from app.db.models import RepoChunk
from app.db.session import session_scope
from app.obs import trace
from app.rag.embeddings import active_model, embed

_IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_./-]{3,}")


@dataclass
class Hit:
    id: int
    kind: str
    path: str
    symbol: str
    start_line: int
    end_line: int
    text: str
    score: float

    def to_dict(self) -> dict:
        return asdict(self)

    def cite(self) -> str:
        if self.kind in ("code", "doc") and self.start_line:
            return f"{self.path}:{self.start_line}-{self.end_line}"
        return f"{self.kind}:{self.symbol or self.path}"

    def prompt_block(self, max_chars: int = 1800) -> str:
        return f"[{self.cite()}] ({self.kind}{', ' + self.symbol if self.symbol else ''})\n{self.text[:max_chars]}"


def _identifiers(query: str) -> list[str]:
    return [t for t in _IDENT.findall(query) if any(c in t for c in "_./") or re.search(r"[a-z][A-Z]", t)][:5]


async def search(repo_id: str, query: str, k: int = 8, kinds: tuple[str, ...] | None = None) -> list[Hit]:
    async with trace.span("search code", kind="retrieval", query=query[:300], kinds=list(kinds or [])) as sp:
        model = active_model()
        [qvec] = await embed([query[:4000]], node="repo_query")
        distance = RepoChunk.embedding.cosine_distance(qvec)
        stmt = select(RepoChunk, distance.label("d")).where(
            RepoChunk.repo_id == repo_id, RepoChunk.embedding_model == model
        )
        if kinds:
            stmt = stmt.where(RepoChunk.kind.in_(kinds))
        async with session_scope() as s:
            rows = (await s.execute(stmt.order_by(distance).limit(k * 3))).all()
            idents = _identifiers(query)
            keyword = []
            if idents:
                kstmt = select(RepoChunk, distance.label("d")).where(
                    RepoChunk.repo_id == repo_id,
                    RepoChunk.embedding_model == model,
                    or_(*[RepoChunk.text.contains(t) | RepoChunk.path.contains(t) for t in idents]),
                )
                if kinds:
                    kstmt = kstmt.where(RepoChunk.kind.in_(kinds))
                keyword = (await s.execute(kstmt.limit(k))).all()
        hits: dict[int, Hit] = {}
        for c, d in [*rows, *keyword]:
            score = 1 - float(d)
            if any(t in c.text or t in c.path for t in idents):
                score += 0.15
            if c.id not in hits or hits[c.id].score < score:
                hits[c.id] = Hit(
                    c.id, c.kind, c.path, c.symbol, c.start_line, c.end_line, c.text, round(score, 4)
                )
        out = sorted(hits.values(), key=lambda h: -h.score)[:k]
        sp.set(results=[h.cite() for h in out])
        return out
