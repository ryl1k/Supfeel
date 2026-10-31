from app.tools import registry


async def run(tool, args, customer_id, conversation_id="conv-test"):
    action_id = await registry.propose(tool, args, conversation_id=conversation_id, needs_confirmation=False)
    return action_id, await registry.execute(
        action_id, customer_id=customer_id, conversation_id=conversation_id
    )


async def test_read_tools_are_scoped_to_customer(demo_db):
    own = await registry.call_read("get_order", {"order_id": "V1042"}, customer_id="cus_maya")
    assert own["order_id"] == "V1042" and own["within_30_day_window"] is True
    other = await registry.call_read("get_order", {"order_id": "V1042"}, customer_id="cus_jordan")
    assert other["error"] == "order_not_found"


async def test_lost_shipment_assessment(demo_db):
    res = await registry.call_read("get_shipment", {"order_id": "V1077"}, customer_id="cus_jordan")
    assert res["shipment"]["assessment"] == "lost"


async def test_duplicate_payment_flagged(demo_db):
    res = await registry.call_read("get_payments", {"order_id": "V1090"}, customer_id="cus_alex")
    assert any(p.get("possible_duplicate_of") == "PAY-7060" for p in res["payments"])


async def test_comfort_exchange_and_label_verified(demo_db):
    order = await registry.call_read("get_order", {"order_id": "V1042"}, customer_id="cus_maya")
    item_id = order["items"][0]["order_item_id"]
    recs = await registry.call_read(
        "get_recommendations",
        {"product_id": "cloud-runner-slate", "size": 10, "fit_problem": "narrow"},
        customer_id="cus_maya",
    )
    top = recs["recommendations"][0]
    assert top["width"] == "2E" and top["product_id"] == "cloud-runner-slate"

    _, ex = await run(
        "create_exchange",
        {
            "order_item_id": item_id,
            "new_sku": top["sku"],
            "reason": "too narrow",
            "use_comfort_guarantee": True,
        },
        "cus_maya",
    )
    assert ex["ok"] and ex["verification"]["ok"], ex
    _, label = await run("create_return_label", {"order_item_id": item_id}, "cus_maya")
    assert label["ok"] and label["verification"]["ok"]

    # Comfort guarantee can be used only once per item.
    _, again = await run(
        "create_exchange",
        {"order_item_id": item_id, "new_sku": top["sku"], "reason": "again", "use_comfort_guarantee": True},
        "cus_maya",
    )
    assert not again["ok"] and again["error"]["error"] == "comfort_guarantee_used"


async def test_refund_is_idempotent(demo_db):
    args = {
        "payment_id": "PAY-7061",
        "amount_cents": 14295,
        "method": "original",
        "reason": "duplicate charge",
    }
    action_id, first = await run("create_refund", args, "cus_alex")
    assert first["ok"] and first["verification"]["ok"]
    second = await registry.execute(action_id, customer_id="cus_alex", conversation_id="conv-test")
    assert second.get("replayed") and second["result"]["refund_id"] == first["result"]["refund_id"]
    _, over = await run("create_refund", args, "cus_alex")
    assert not over["ok"] and over["error"]["error"] == "amount_exceeds_refundable"


async def test_authorization_hold_cannot_be_refunded(demo_db):
    _, res = await run(
        "create_refund", {"payment_id": "PAY-7091", "amount_cents": 1800, "reason": "dup"}, "cus_alex"
    )
    assert res["error"]["error"] == "not_captured"


async def test_reship_lost_order(demo_db):
    _, res = await run("reship_order", {"order_id": "V1077", "reason": "lost in transit"}, "cus_jordan")
    assert res["ok"] and res["verification"]["ok"]


async def test_cancel_membership_with_renewal_refund(demo_db):
    _, res = await run(
        "cancel_subscription", {"refund_renewal": True, "reason": "did not intend to renew"}, "cus_sam"
    )
    assert res["ok"] and res["verification"]["ok"]
    assert res["result"]["renewal_refund"]["amount_cents"] == 999


async def test_pause_membership(demo_db):
    _, res = await run("pause_subscription", {"months": 2}, "cus_sam")
    assert res["ok"] and res["verification"]["ok"]


async def test_address_change_only_while_processing(demo_db):
    addr = {"line1": "12 New St", "city": "Boston", "state": "MA", "zip": "02108", "country": "US"}
    _, ok = await run("update_address", {"order_id": "V1101", "address": addr}, "cus_lee")
    assert ok["ok"] and ok["verification"]["ok"]
    _, shipped = await run("update_address", {"order_id": "V1012", "address": addr}, "cus_lee")
    assert shipped["error"]["error"] == "already_shipped"


async def test_cancel_processing_order_releases_hold(demo_db):
    _, res = await run("cancel_order", {"order_id": "V1101", "reason": "changed mind"}, "cus_lee")
    assert res["ok"] and res["verification"]["ok"]
    assert res["result"]["authorizations_released"] == ["PAY-7101"]


async def test_escalation(demo_db):
    _, res = await run(
        "escalate_to_human", {"reason": "customer_request", "summary": "wants a human"}, "cus_lee"
    )
    assert res["ok"] and res["verification"]["ok"]


def test_catalog_is_stable():
    assert registry.tool_catalog() == registry.tool_catalog()
    assert "create_refund(" in registry.tool_catalog()
