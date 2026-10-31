from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(REPO_ROOT / ".env", BACKEND_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    anthropic_api_key: str = ""
    claude_model: str = "claude-sonnet-5-5"
    openai_api_key: str = ""
    embedding_model: str = "text-embedding-3-small"

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5433/supfeel"
    cors_origins: str = "http://localhost:3000"
    # Optional regex for extra origins, e.g. Vercel previews: https://supfeel-.*\.vercel\.app
    cors_origin_regex: str = ""
    admin_token: str = "dev-admin-token"

    llm_mode: Literal["live", "replay", "mock"] = "mock"
    llm_budget_hard_cap_usd: float = 60.0
    llm_session_cap_usd: float = 0.50
    embedding_budget_hard_cap_usd: float = 3.0
    llm_cache_dir: Path = BACKEND_ROOT / ".llm-cache"

    knowledge_base_dir: Path = REPO_ROOT / "knowledge-base"
    qloo_api_key: str = ""

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def async_database_url(self) -> str:
        """Normalize Neon/Railway style URLs to the asyncpg driver."""
        url = self.database_url
        for prefix in ("postgres://", "postgresql://"):
            if url.startswith(prefix):
                url = "postgresql+asyncpg://" + url[len(prefix) :]
        # asyncpg does not understand libpq's sslmode/channel_binding query params.
        if "?" in url:
            base, query = url.split("?", 1)
            params = [p for p in query.split("&") if not p.startswith(("sslmode=", "channel_binding="))]
            url = base + ("?" + "&".join(params) if params else "")
        return url

    @property
    def database_requires_ssl(self) -> bool:
        return "sslmode=require" in self.database_url or "neon.tech" in self.database_url


@lru_cache
def get_settings() -> Settings:
    return Settings()
