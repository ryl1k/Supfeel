"""Text embeddings.

- LLM_MODE=mock (or no OPENAI_API_KEY): deterministic hashed bag-of-words vectors. Free, offline,
  good enough for keyword-ish retrieval in tests and UI work.
- otherwise: OpenAI text-embedding-3-small, cached in embedding_cache, spend recorded in llm_usage.
"""

import hashlib
import math
import re

from openai import AsyncOpenAI
from sqlalchemy import select

from app.config import get_settings
from app.db.models import EMBEDDING_DIM, EmbeddingCache
from app.db.session import session_scope
from app.llm import ledger
from app.llm.pricing import price_for
from app.obs import trace

MOCK_MODEL = "mock-hash-v1"
BATCH = 256  # inputs per OpenAI request (limit 2048 inputs / 300k tokens)
MAX_CHARS = 24_000  # ≈ 6k tokens, under the 8,191-token input limit
_TOKEN = re.compile(r"[a-z0-9]+")
_STOP = {
    "the", "a", "an", "and", "or", "to", "of", "in", "on", "for", "is", "are", "be", "it", "my", "i", "you",
    "your", "we", "with", "this", "that", "can", "at", "by", "as", "if", "from", "not", "no", "do", "me",
}  # fmt: skip

_openai: AsyncOpenAI | None = None


def active_model() -> str:
    settings = get_settings()
    if settings.llm_mode == "mock" or not settings.openai_api_key:
        return MOCK_MODEL
    return settings.embedding_model


def _stem(word: str) -> str:
    for suffix in ("ing", "ed", "es", "s"):
        if len(word) > 4 and word.endswith(suffix):
            return word[: -len(suffix)]
    return word


def mock_embed(text: str) -> list[float]:
    vec = [0.0] * EMBEDDING_DIM
    for word in _TOKEN.findall(text.lower()):
        if word in _STOP:
            continue
        h = int(hashlib.md5(_stem(word).encode()).hexdigest(), 16)
        vec[h % EMBEDDING_DIM] += 1.0 if (h >> 64) & 1 else -1.0
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def _hash(model: str, text: str) -> str:
    return hashlib.sha256(f"{model}\n{text}".encode()).hexdigest()


async def embed(texts: list[str], *, node: str = "embed") -> list[list[float]]:
    model = active_model()
    texts = [t[:MAX_CHARS] for t in texts]
    if model == MOCK_MODEL:
        return [mock_embed(t) for t in texts]
    async with trace.span(f"embed.{node}", kind="embedding", model=model, inputs=len(texts)) as sp:
        vectors, fresh = await _embed_openai(model, texts, node)
        sp.set(embedded=fresh, cached=len(texts) - fresh)
        return vectors


async def _embed_openai(model: str, texts: list[str], node: str) -> tuple[list[list[float]], int]:

    hashes = [_hash(model, t) for t in texts]
    cached: dict[str, list[float]] = {}
    unique = list(dict.fromkeys(hashes))
    for i in range(0, len(unique), 1000):
        async with session_scope() as s:
            rows = await s.scalars(
                select(EmbeddingCache).where(EmbeddingCache.text_hash.in_(unique[i : i + 1000]))
            )
            cached.update({row.text_hash: list(row.embedding) for row in rows.all()})
    missing = list({h: t for h, t in zip(hashes, texts, strict=True) if h not in cached}.items())
    global _openai
    for i in range(0, len(missing), BATCH):
        batch = missing[i : i + BATCH]
        est_tokens = sum(len(t) for _, t in batch) / 3.5
        await ledger.check_caps("openai", est_tokens * price_for(model).input / 1_000_000)
        if _openai is None:
            _openai = AsyncOpenAI(api_key=get_settings().openai_api_key)
        response = await _openai.embeddings.create(model=model, input=[t for _, t in batch])
        await ledger.record(
            provider="openai", model=model, node=node, mode="live", input_tokens=response.usage.prompt_tokens
        )
        async with session_scope() as s:
            for (h, _), item in zip(batch, response.data, strict=True):
                cached[h] = item.embedding
                s.add(EmbeddingCache(text_hash=h, model=model, embedding=item.embedding))
    return [cached[h] for h in hashes], len(missing)
