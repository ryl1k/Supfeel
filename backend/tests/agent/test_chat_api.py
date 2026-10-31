import json

from httpx import ASGITransport, AsyncClient

from app.main import app
from app.rag.ingest import ingest


def parse_sse(body: str) -> list[tuple[str, dict]]:
    events = []
    for block in body.replace("\r\n", "\n").split("\n\n"):
        name, data = None, None
        for line in block.splitlines():
            if line.startswith("event:"):
                name = line[6:].strip()
            elif line.startswith("data:"):
                data = line[5:].strip()
        if name and data:
            events.append((name, json.loads(data)))
    return events


async def test_chat_stream_and_confirm(demo_db):
    await ingest()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test", timeout=30) as client:
        r = await client.post(
            "/api/chat",
            json={
                "conversation_id": "api-test-1",
                "customer_id": "cus_alex",
                "message": "I got charged twice",
            },
        )
        events = parse_sse(r.text)
        names = [n for n, _ in events]
        assert "step" in names and "token" in names and names[-1] == "done"
        assert events[-1][1]["outcome"] == "resolved"

        t = (await client.get("/api/conversations/api-test-1")).json()
        assert [m["role"] for m in t["messages"]] == ["user", "assistant"]

        bad = await client.post(
            "/api/chat", json={"conversation_id": "api-test-2", "customer_id": "nobody", "message": "hi"}
        )
        assert parse_sse(bad.text)[0][0] == "error"
