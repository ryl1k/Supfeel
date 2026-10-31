from sqlalchemy import func, select

from app.db.models import Customer, Order, Payment, Variant
from app.db.session import session_scope


async def test_seed_creates_demo_scenarios(demo_db):
    async with session_scope() as s:
        assert await s.scalar(select(func.count()).select_from(Customer)) == 6
        assert await s.scalar(select(func.count()).select_from(Variant)) > 100
        hero = await s.get(Order, "V1042")
        assert hero.status == "delivered"
        dupes = (await s.scalars(select(Payment).where(Payment.order_id == "V1090"))).all()
        assert [p.status for p in dupes] == ["captured", "captured"]
