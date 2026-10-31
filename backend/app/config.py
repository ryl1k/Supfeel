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

    # GitHub App (preferred) or a personal access token fallback. See docs/project/github-app-setup.md.
    github_app_id: str = ""
    github_app_slug: str = ""
    github_app_private_key: str = ""
    github_app_private_key_path: str = ""
    github_webhook_secret: str = ""
    github_token: str = ""
    github_api_url: str = "https://api.github.com"

    # Business notifications (optional; always stored in the dashboard inbox too).
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    slack_webhook_url: str = ""
    discord_webhook_url: str = ""
    public_app_url: str = "http://localhost:3000"

    # Repository indexing limits (protect the budget and the 512 MB free instance).
    repo_max_files: int = 2000
    repo_max_file_bytes: int = 200_000
    repo_max_total_bytes: int = 25_000_000
    repo_max_modules_summarized: int = 30
    max_repos: int = 20
    index_cap_usd: float = 2.0  # Claude spend per index job (module summaries + overview)
    allow_local_repos: bool = False  # dev/tests: import a local directory instead of GitHub
    # The Slice demo store API (examples/slice-pizza) is mounted at /demo-store so assisted actions have a
    # live business API on the same free instance.
    mount_demo_store: bool = True
    demo_store_dir: Path = REPO_ROOT / "examples" / "slice-pizza"
    # Per-ticket Claude cap. Fixes run a multi-turn tool loop, so they get more headroom than a chat turn.
    ticket_cap_usd: float = 0.40
    fix_cap_usd: float = 1.50
    fix_max_turns: int = 16
    ci_poll_seconds: float = 20.0
    ci_poll_max: int = 45  # ≈ 15 minutes of polling per fix PR
    # Allow anyone to import repositories (otherwise the x-admin-token header is required).
    open_import: bool = False

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def github_private_key(self) -> str:
        if self.github_app_private_key:
            return self.github_app_private_key.replace("\\n", "\n").strip()
        if self.github_app_private_key_path:
            return Path(self.github_app_private_key_path).expanduser().read_text().strip()
        return ""

    @property
    def github_app_configured(self) -> bool:
        return bool(self.github_app_id and (self.github_app_private_key or self.github_app_private_key_path))

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
