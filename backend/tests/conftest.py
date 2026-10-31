import os

os.environ["DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5433/supfeel_test"
)
os.environ["LLM_MODE"] = "mock"
os.environ["ANTHROPIC_API_KEY"] = ""
os.environ["OPENAI_API_KEY"] = ""
# Never reach real integrations from tests, whatever is in the developer's .env.
for _var in (
    "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID", "SLACK_WEBHOOK_URL", "DISCORD_WEBHOOK_URL",
    "GITHUB_APP_ID", "GITHUB_APP_PRIVATE_KEY", "GITHUB_APP_PRIVATE_KEY_PATH", "GITHUB_TOKEN", "GITHUB_WEBHOOK_SECRET",
):  # fmt: skip
    os.environ[_var] = ""

import pytest  # noqa: E402

from app.db.seed import init_db, reset_demo  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
async def _schema():
    await init_db()
    yield


@pytest.fixture
async def demo_db():
    """Fresh demo state for tests that mutate business data."""
    await reset_demo()
    yield
