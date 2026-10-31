import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import admin, chat
from app.config import get_settings
from app.db.session import dispose_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await dispose_engine()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Supfeel API", version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_origin_regex=settings.cors_origin_regex or None,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/health")
    async def health() -> dict:
        return {"status": "ok", "llm_mode": settings.llm_mode, "model": settings.claude_model}

    app.include_router(admin.router)
    app.include_router(chat.router)
    _mount_demo_store(app)
    return app


def _mount_demo_store(app: FastAPI) -> None:
    settings = get_settings()
    root = settings.demo_store_dir
    if not settings.mount_demo_store or not (root / "slice_api").is_dir():
        return
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from slice_api.main import app as slice_app

    app.mount("/demo-store", slice_app)


app = create_app()
