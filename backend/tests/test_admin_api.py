from httpx import ASGITransport, AsyncClient

from app.main import app


async def test_demo_customers_and_reset(demo_db):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        customers = (await client.get("/api/customers/demo")).json()
        assert {c["id"] for c in customers} >= {"cus_maya", "cus_jordan"}
        assert (await client.post("/api/admin/reset")).status_code == 401
        ok = await client.post("/api/admin/reset", headers={"x-admin-token": "dev-admin-token"})
        assert ok.json() == {"status": "reset"}
        usage = (await client.get("/api/admin/usage", headers={"x-admin-token": "dev-admin-token"})).json()
        assert "anthropic_usd" in usage
