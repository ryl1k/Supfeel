import uuid

import pytest

from app.accounts import auth, billing


@pytest.fixture
async def account():
    _, p = await auth.signup(f"b-{uuid.uuid4().hex[:8]}@example.com", "B", "longenough1")
    return p.account_id


async def test_welcome_credit_charge_and_statement(account):
    assert await billing.balance_cents(account) == billing.FREE_GRANT_CENTS
    await billing.charge(account, "ticket", ref="T-1")
    await billing.charge(account, "fix", ref="T-1")
    assert await billing.balance_cents(account) == billing.FREE_GRANT_CENTS - 115
    s = await billing.summary(account)
    assert s["month"]["spent_cents"] == 115 and s["month"]["by_metric"]["fix"] == {
        "quantity": 1,
        "cents": 100,
    }
    kinds = [e["kind"] for e in await billing.statement(account)]
    assert kinds == ["usage", "usage", "grant"]


async def test_balance_and_monthly_limit(account):
    await billing.update_settings(account, monthly_limit_cents=120)
    await billing.charge(account, "fix")
    with pytest.raises(billing.PaymentRequired, match="Monthly spend limit"):
        await billing.charge(account, "fix")
    await billing.update_settings(account, monthly_limit_cents=100_000)
    for _ in range(4):
        await billing.charge(account, "fix")
    with pytest.raises(billing.PaymentRequired, match="Not enough credit"):
        await billing.charge(account, "fix")


async def test_topup_card_and_auto_recharge(account):
    with pytest.raises(billing.PaymentRequired):
        billing.mock_card("4000 0000 0000 0002", "Declined")
    card = billing.mock_card("4242 4242 4242 4242", "Ada")
    assert card == {"brand": "Visa", "last4": "4242", "name": "Ada"}
    await billing.topup(account, 1000, card)
    assert await billing.balance_cents(account) == 1500
    await billing.update_settings(
        account,
        payment_method=card,
        auto_recharge={"enabled": True, "threshold_cents": 200, "amount_cents": 2000},
    )
    for _ in range(14):  # 14 fixes = $14: auto-recharge keeps it going
        await billing.charge(account, "fix")
    assert any(e["description"].startswith("Auto-recharge") for e in await billing.statement(account))


def test_month_boundaries():
    from datetime import UTC, datetime

    assert billing.next_month_start(datetime(2026, 12, 15, tzinfo=UTC)) == datetime(2027, 1, 1, tzinfo=UTC)
    assert billing.month_start(datetime(2026, 10, 31, 23, tzinfo=UTC)) == datetime(2026, 10, 1, tzinfo=UTC)


async def test_refund_reduces_month_spend(account):
    await billing.charge(account, "fix", ref="T-9")
    await billing.refund(account, "fix", "T-9", "not performed")
    s = await billing.summary(account)
    assert s["month"]["spent_cents"] == 0 and s["balance_cents"] == billing.FREE_GRANT_CENTS
