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

MOCK_MODEL = "mock-hash-v1"
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
    if model == MOCK_MODEL:
        return [mock_embed(t) for t in texts]

    hashes = [_hash(model, t) for t in texts]
    async with session_scope() as s:
        cached = {
            row.text_hash: list(row.embedding)
            for row in (
                await s.scalars(select(EmbeddingCache).where(EmbeddingCache.text_hash.in_(hashes)))
            ).all()
        }
    missing = [(h, t) for h, t in zip(hashes, texts, strict=True) if h not in cached]
    if missing:
        est_tokens = sum(len(t) for _, t in missing) / 3.5
        await ledger.check_caps("openai", est_tokens * price_for(model).input / 1_000_000)
        global _openai
        if _openai is None:
            _openai = AsyncOpenAI(api_key=get_settings().openai_api_key)
        response = await _openai.embeddings.create(model=model, input=[t for _, t in missing])
        await ledger.record(
            provider="openai", model=model, node=node, mode="live", input_tokens=response.usage.prompt_tokens
        )
        async with session_scope() as s:
            for (h, _), item in zip(missing, response.data, strict=True):
                cached[h] = item.embedding
                s.add(EmbeddingCache(text_hash=h, model=model, embedding=item.embedding))
    return [cached[h] for h in hashes]
