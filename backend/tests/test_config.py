from app.config import Settings


def test_neon_url_normalized_for_asyncpg():
    s = Settings(
        database_url="postgresql://u:p@ep-cool-1.eu-central-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
    )
    assert s.async_database_url == "postgresql+asyncpg://u:p@ep-cool-1.eu-central-1.aws.neon.tech/neondb"
    assert s.database_requires_ssl


def test_local_url_untouched():
    s = Settings(database_url="postgresql+asyncpg://postgres:postgres@localhost:5433/supfeel")
    assert s.async_database_url.endswith("localhost:5433/supfeel")
    assert not s.database_requires_ssl


def test_railway_postgres_scheme():
    s = Settings(database_url="postgres://u:p@host:5432/db")
    assert s.async_database_url.startswith("postgresql+asyncpg://")
