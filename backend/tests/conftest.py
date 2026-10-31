import os

os.environ["DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5433/supfeel_test"
)
os.environ["LLM_MODE"] = "mock"
os.environ["ANTHROPIC_API_KEY"] = ""
os.environ["OPENAI_API_KEY"] = ""

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
