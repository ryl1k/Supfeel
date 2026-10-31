"""The MCP server end to end over streamable HTTP (in-process ASGI), with keys, billing and relay results."""

import asyncio
import json
import uuid

import httpx2
import pytest
from mcp import Client
from mcp.client.streamable_http import streamable_http_client

from app.accounts import auth, billing
from app.db.models import Repo
from app.db.session import session_scope
from app.main import app
from app.mcp_server import mcp


@pytest.fixture(scope="module", autouse=True)
async def mcp_running():
    # The SDK's session manager can run once per process (the app lifespan does this in production). It owns an
    # anyio task group, so it must enter and exit in one task: run it in its own.
    started, stop = asyncio.Event(), asyncio.Event()

    async def runner():
        async with mcp.session_manager.run():
            started.set()
            await stop.wait()

    task = asyncio.create_task(runner())
    await started.wait()
    yield
    stop.set()
    await task


@pytest.fixture
async def workspace(slice_repo):
    """A fresh workspace that owns the Slice repo, with an MCP key."""
    _, principal = await auth.signup(f"owner-{uuid.uuid4().hex[:8]}@example.com", "Owner", "correct-horse")
    async with session_scope() as s:
        (await s.get(Repo, slice_repo)).account_id = principal.account_id
    key = await auth.create_key(principal.account_id, slice_repo, "Test bot")
    yield principal.account_id, key["key"]
    async with session_scope() as s:
        (await s.get(Repo, slice_repo)).account_id = None


def client(key: str | None):
    headers = {"Authorization": f"Bearer {key}"} if key else {}
    http = httpx2.AsyncClient(
        transport=httpx2.ASGITransport(app=app), base_url="http://test", headers=headers, timeout=60
    )
    return Client(streamable_http_client("http://test/mcp", http_client=http))


def data(result):
    if result.structured_content is not None:
        sc = result.structured_content
        return sc.get("result", sc) if isinstance(sc, dict) and set(sc) == {"result"} else sc
    return json.loads(result.content[0].text)


async def test_tools_and_auth(workspace):
    _, key = workspace
    async with client(key) as c:
        names = {t.name for t in (await c.list_tools()).tools}
        assert {
            "escalate",
            "reply",
            "confirm",
            "get_ticket",
            "ask_product",
            "get_product_overview",
            "list_tickets",
        } <= names
        confirm = next(t for t in (await c.list_tools()).tools if t.name == "confirm")
        assert confirm.annotations.destructive_hint is True
        overview = data(await c.call_tool("get_product_overview", {}))
        assert (
            overview["product"] == "Slice"
            and "create_order: Place an order for a customer" in overview["actions_available"]
        )
    async with client("sf_live_wrong") as c:
        res = await c.call_tool("get_product_overview", {})
        assert res.is_error and "key" in res.content[0].text.lower()


async def test_escalate_explain_with_handoff_and_billing(workspace):
    account, key = workspace
    before = await billing.balance_cents(account)
    async with client(key) as c:
        res = data(await c.call_tool("escalate", {
            "message": "Why did I pay a delivery fee on my last order?",
            "customer": {"name": "Maya Chen", "ref": "c_maya"},
            "conversation": [{"role": "customer", "content": "Hi, question about my bill"},
                             {"role": "assistant", "content": "Our delivery fee is $3.99."}],
            "attempted": "Told the customer the fee amount.",
            "agent": "Slice FAQ bot",
        }))  # fmt: skip
        assert res["status"] == "answered" and res["customer_reply"]
        assert res["next_step"] and res["trace_url"].endswith(res["ticket_id"])
        done = data(
            await c.call_tool("reply", {"ticket_id": res["ticket_id"], "message": "thanks, that helps"})
        )
        assert done["status"] == "resolved"
        asked = data(await c.call_tool("ask_product", {"question": "What are the opening hours?"}))
        assert asked["answer"]
    assert (
        before - await billing.balance_cents(account)
        == billing.PRICES["ticket"].cents + billing.PRICES["ask"].cents
    )
    from app.support.service import get_ticket

    t = await get_ticket(res["ticket_id"])
    assert t["channel"] == "mcp"
    assert [m["role"] for m in t["messages"][:3]] == ["customer", "frontline", "customer"]


async def test_escalate_action_needs_customer_confirmation(workspace, slice_api):
    _, key = workspace
    async with client(key) as c:
        res = data(await c.call_tool("escalate", {
            "message": "The app crashes on Reorder. Can you place my last order again for me?",
            "customer": {"name": "Jordan Blake", "ref": "c_jordan"},
        }))  # fmt: skip
        assert res["status"] == "awaiting_confirmation"
        assert "?" in res["needs_confirmation"]["question"]
        before = len(slice_api.DB["orders"])
        done = data(await c.call_tool("confirm", {"ticket_id": res["ticket_id"], "approved": True}))
        assert done["status"] == "resolved" and len(slice_api.DB["orders"]) == before + 1
        again = await c.call_tool("confirm", {"ticket_id": res["ticket_id"], "approved": True})
        assert again.is_error  # nothing pending any more


async def test_out_of_credit_is_a_clear_tool_error(workspace):
    account, key = workspace
    await billing.update_settings(account, monthly_limit_cents=0)
    async with client(key) as c:
        res = await c.call_tool("escalate", {"message": "Why is delivery not free?"})
        assert res.is_error and "Monthly spend limit" in res.content[0].text


async def test_other_products_tickets_are_invisible(workspace):
    _, key = workspace
    async with client(key) as c:
        res = await c.call_tool("get_ticket", {"ticket_id": "T-NOPE00"})
        assert res.is_error


async def test_dashboard_reflects_onboarding_and_tickets(workspace):
    import httpx

    account, key = workspace
    async with session_scope() as s:
        from sqlalchemy import select

        from app.db.models import User

        user = await s.scalar(select(User).where(User.account_id == account))
    token = await auth._new_session(user.id)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as c:
        d = (await c.get("/api/dashboard", headers={"Authorization": f"Bearer {token}"})).json()
        assert (
            d["onboarding"]["repo_ready"]
            and d["onboarding"]["key_created"]
            and d["onboarding"]["api_connected"]
        )
        assert len(d["daily"]) == 14 and d["billing"]["balance_cents"] <= billing.FREE_GRANT_CENTS
        assert (await c.get("/api/dashboard")).status_code == 401
