from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select

from app.config import get_settings
from app.db.models import Customer
from app.db.seed import reset_demo
from app.db.session import session_scope
from app.llm import ledger
from app.rag.retrieve import retrieve

router = APIRouter(prefix="/api")


def require_admin(x_admin_token: str = Header(default="")) -> None:
    if x_admin_token != get_settings().admin_token:
        raise HTTPException(status_code=401, detail="invalid admin token")


@router.get("/customers/demo")
async def list_demo_customers() -> list[dict]:
    async with session_scope() as s:
        customers = (await s.scalars(select(Customer).order_by(Customer.id))).all()
    return [{"id": c.id, "name": c.name, "tier": c.tier, "persona": c.persona} for c in customers]


@router.post("/admin/reset", dependencies=[Depends(require_admin)])
async def reset() -> dict:
    await reset_demo()
    return {"status": "reset"}


@router.post("/demo/reset")
async def public_reset() -> dict:
    """Demo convenience: anyone viewing the demo can restore the seeded state (mock data only)."""
    await reset_demo()
    return {"status": "reset"}


@router.get("/admin/usage", dependencies=[Depends(require_admin)])
async def usage() -> dict:
    return await ledger.summary()


@router.get("/admin/kb/search", dependencies=[Depends(require_admin)])
async def kb_search(q: str, k: int = 5) -> list[dict]:
    return [r.to_dict() for r in await retrieve(q, k=k)]
