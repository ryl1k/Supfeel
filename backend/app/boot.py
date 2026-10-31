"""Container start-up: create schema, seed demo data if the DB is empty, embed the knowledge base.

Idempotent and cheap on warm starts (no reseed, no re-embedding of unchanged chunks).
Run: `uv run python -m app.boot`
"""

import asyncio

from sqlalchemy import func, select

from app.config import get_settings
from app.db.models import Customer
from app.db.seed import init_db, reset_demo
from app.db.session import dispose_engine, session_scope
from app.rag.ingest import ingest
from app.repos.indexer import recover_stale_jobs


async def main() -> None:
    settings = get_settings()
    await init_db()
    async with session_scope() as s:
        customers = await s.scalar(select(func.count()).select_from(Customer))
    if not customers:
        await reset_demo()
        print("boot: seeded demo data")
    print("boot: knowledge base", await ingest())
    print("boot: stale index jobs recovered:", await recover_stale_jobs())
    print(f"boot: ready (LLM_MODE={settings.llm_mode}, model={settings.claude_model})")
    await dispose_engine()


if __name__ == "__main__":
    asyncio.run(main())
