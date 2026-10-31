"""End-to-end agent scenarios in mock mode (rule brain, hash embeddings): zero API spend."""

import uuid

import pytest

from app.agent import service
from app.rag.ingest import ingest


@pytest.fixture(scope="module", autouse=True)
async def kb():
    await ingest()
    yield


async def collect(gen):
    events = [ev async for ev in gen]
    done = next(e["data"] for e in events if e["event"] == "done")
    reply = "".join(e["data"]["text"] for e in events if e["event"] == "token")
    return events, done, reply


def of(events, name):
    return [e["data"] for e in events if e["event"] == name]


def conv():
    return f"test-{uuid.uuid4().hex[:8]}"


async def test_hero_comfort_exchange(demo_db):
    cid = conv()
    events, done, reply = await collect(
        service.handle_message(
            cid, "cus_maya", "I bought these sneakers, but they're uncomfortable. Can you help?"
        )
    )
    assert done["outcome"] == "asked" and "narrow" in reply

    events, done, reply = await collect(
        service.handle_message(cid, "cus_maya", "They're too narrow on the sides")
    )
    assert done["outcome"] == "awaiting_confirmation"
    proposed = of(events, "action_proposed")[0]["actions"]
    assert [a["tool"] for a in proposed] == ["create_exchange", "create_return_label"]
    assert "2E" in proposed[0]["title"]
    assert of(events, "recommendations")
    steps = [s["step"] for s in of(events, "step") if s["status"] == "done"]
    assert steps == ["understand", "investigate", "policy", "plan", "respond"]

    events, done, reply = await collect(service.handle_confirm(cid, approved=True))
    assert done["outcome"] == "resolved"
    verified = of(events, "verified")
    assert len(verified) == 2 and all(v["ok"] for v in verified)
    assert "verified" in reply


async def test_lost_package_reship_with_typed_yes(demo_db):
    cid = conv()
    _, done, _ = await collect(
        service.handle_message(cid, "cus_jordan", "My package never arrived, it's been two weeks")
    )
    assert done["outcome"] == "awaiting_confirmation"
    events, done, _ = await collect(service.handle_message(cid, "cus_jordan", "yes please"))
    assert done["outcome"] == "resolved"
    assert of(events, "action_done")[0]["action"]["tool"] == "reship_order"


async def test_double_charge_refunded_autonomously(demo_db):
    events, done, reply = await collect(
        service.handle_message(conv(), "cus_alex", "I was charged twice for my last order!")
    )
    assert done["outcome"] == "resolved"
    assert not of(events, "action_proposed")
    assert of(events, "action_done")[0]["action"]["tool"] == "create_refund"
    assert all(v["ok"] for v in of(events, "verified"))


async def test_membership_offers_pause_once_then_cancels_with_refund(demo_db):
    cid = conv()
    _, done, reply = await collect(service.handle_message(cid, "cus_sam", "Please cancel my membership"))
    assert done["outcome"] == "asked" and "pause" in reply.lower()
    events, done, _ = await collect(service.handle_message(cid, "cus_sam", "No, just cancel it"))
    assert done["outcome"] == "awaiting_confirmation"
    assert of(events, "action_proposed")[0]["actions"][0]["title"] == "Cancel membership + refund renewal"
    _, done, reply = await collect(service.handle_confirm(cid, approved=True))
    assert done["outcome"] == "resolved"


async def test_out_of_window_return_declined(demo_db):
    _, done, reply = await collect(
        service.handle_message(conv(), "cus_lee", "I want to return my shoes for a refund")
    )
    assert done["outcome"] == "not_allowed"
    assert "30-day" in reply


async def test_warranty_replacement(demo_db):
    cid = conv()
    _, done, _ = await collect(
        service.handle_message(cid, "cus_priya", "The sole on my Court sneakers is separating")
    )
    assert done["outcome"] == "awaiting_confirmation"
    events, done, _ = await collect(service.handle_confirm(cid, approved=True))
    assert done["outcome"] == "resolved"
    assert {a["action"]["tool"] for a in of(events, "action_done")} == {
        "create_exchange",
        "create_return_label",
    }


async def test_decline_changes_nothing(demo_db):
    cid = conv()
    await collect(service.handle_message(cid, "cus_jordan", "where is my order? it seems lost"))
    events, done, reply = await collect(service.handle_confirm(cid, approved=False))
    assert done["outcome"] == "declined"
    assert not of(events, "action_done")


async def test_human_request_escalates(demo_db):
    _, done, _ = await collect(service.handle_message(conv(), "cus_lee", "I want to talk to a real person"))
    assert done["outcome"] == "escalated"


async def test_policy_question_answered(demo_db):
    _, done, reply = await collect(
        service.handle_message(conv(), "cus_maya", "How should I wash my knit sneakers?")
    )
    assert done["outcome"] == "answered"
    assert reply


async def test_confirm_without_pending_errors(demo_db):
    cid = conv()
    await collect(service.handle_message(cid, "cus_maya", "hello"))
    events = [e async for e in service.handle_confirm(cid, approved=True)]
    assert events[0]["event"] == "error"


@pytest.mark.parametrize(
    "message, intent",
    [
        ("Please cancel my Velora Club membership.", "cancel_membership"),
        ("Can you pause my club membership for two months?", "pause_membership"),
        ("Please ship my new order to 12 Beacon St, Boston, MA 02108", "change_address"),
        ("The sole on my Court sneakers is coming apart.", "damaged_or_defective"),
        ("Why was I charged twice for my last order?", "double_charge"),
    ],
)
def test_rule_brain_routes_suggested_prompts(message, intent):
    from app.agent.rules import understand

    assert understand(message).intent == intent


async def test_switch_to_refund_while_reship_pending(demo_db):
    cid = conv()
    _, done, _ = await collect(service.handle_message(cid, "cus_jordan", "My package still hasn't arrived."))
    assert done["outcome"] == "awaiting_confirmation"
    events, done, _ = await collect(
        service.handle_message(cid, "cus_jordan", "Can I just get a refund instead?")
    )
    assert done["outcome"] == "awaiting_confirmation"
    assert of(events, "action_proposed")[0]["actions"][0]["tool"] == "create_refund"


async def test_address_change_for_processing_order(demo_db):
    cid = conv()
    events, done, _ = await collect(
        service.handle_message(cid, "cus_lee", "Please ship my new order to 12 Beacon St, Boston, MA 02108")
    )
    assert done["outcome"] == "resolved"
    assert of(events, "action_done")[0]["action"]["tool"] == "update_address"
