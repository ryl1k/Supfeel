from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from app.accounts import auth, billing
from app.accounts.auth import CurrentPrincipal, Principal

router = APIRouter(prefix="/api")


class Signup(BaseModel):
    email: str = Field(min_length=3, max_length=200, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    name: str = Field(default="", max_length=120)
    password: str = Field(min_length=8, max_length=200)
    company: str = Field(default="", max_length=120)


class Login(BaseModel):
    email: str = Field(max_length=200)
    password: str = Field(max_length=200)


async def _session_payload(token: str, p: Principal) -> dict:
    return {"token": token, **(await auth.me(p))}


@router.post("/auth/signup", status_code=201)
async def signup(body: Signup) -> dict:
    try:
        token, p = await auth.signup(body.email, body.name, body.password, body.company)
    except auth.AuthError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    return await _session_payload(token, p)


@router.post("/auth/login")
async def login(body: Login) -> dict:
    try:
        token, p = await auth.login(body.email, body.password)
    except auth.AuthError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e
    return await _session_payload(token, p)


@router.post("/auth/logout")
async def logout(authorization: str = Header(default="")) -> dict:
    if authorization.startswith("Bearer "):
        await auth.logout(authorization[7:].strip())
    return {"ok": True}


@router.get("/me")
async def me(p: CurrentPrincipal) -> dict:
    out = await auth.me(p)
    if not p.is_admin:
        out["billing"] = await billing.summary(p.account_id)
    return out


# ----------------------------------------------------------------------------------------- billing (pay as you go, mocked)


def _account(p: Principal) -> str:
    if p.is_admin:
        raise HTTPException(status_code=400, detail="billing needs a signed-in user")
    return p.account_id


@router.get("/billing")
async def get_billing(p: CurrentPrincipal) -> dict:
    acc = _account(p)
    return {**(await billing.summary(acc)), "statement": await billing.statement(acc)}


class Card(BaseModel):
    number: str = Field(max_length=30, description="mock: any 12+ digits; 4000 0000 0000 0002 is declined")
    name: str = Field(default="", max_length=120)


class TopUp(BaseModel):
    amount_cents: int = Field(ge=billing.MIN_TOPUP_CENTS, le=billing.MAX_TOPUP_CENTS)
    card: Card | None = Field(default=None, description="omit to use the saved card")


def _card(card: Card) -> dict:
    try:
        return billing.mock_card(card.number, card.name)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    except billing.PaymentRequired as e:
        raise HTTPException(status_code=402, detail=str(e)) from e


@router.post("/billing/topup")
async def topup(body: TopUp, p: CurrentPrincipal) -> dict:
    acc = _account(p)
    current = (await billing.summary(acc))["payment_method"]
    method = _card(body.card) if body.card else current
    if not method:
        raise HTTPException(status_code=402, detail="add a card first (mock: any 16 digits)")
    if body.card:
        await billing.update_settings(acc, payment_method=method)
    await billing.topup(acc, body.amount_cents, method)
    return await get_billing(p)


@router.put("/billing/card")
async def save_card(body: Card, p: CurrentPrincipal) -> dict:
    acc = _account(p)
    await billing.update_settings(acc, payment_method=_card(body))
    return await get_billing(p)


class BillingSettings(BaseModel):
    monthly_limit_cents: int | None = Field(default=None, ge=0, le=1_000_000)
    auto_recharge_enabled: bool | None = None
    auto_recharge_threshold_cents: int | None = Field(default=None, ge=0, le=100_000)
    auto_recharge_amount_cents: int | None = Field(
        default=None, ge=billing.MIN_TOPUP_CENTS, le=billing.MAX_TOPUP_CENTS
    )


@router.patch("/billing/settings")
async def billing_settings(body: BillingSettings, p: CurrentPrincipal) -> dict:
    acc = _account(p)
    current = (await billing.summary(acc))["auto_recharge"]
    recharge = None
    if any(
        v is not None
        for v in (
            body.auto_recharge_enabled,
            body.auto_recharge_threshold_cents,
            body.auto_recharge_amount_cents,
        )
    ):
        recharge = {
            "enabled": current.get("enabled", False)
            if body.auto_recharge_enabled is None
            else body.auto_recharge_enabled,
            "threshold_cents": body.auto_recharge_threshold_cents or current.get("threshold_cents", 500),
            "amount_cents": body.auto_recharge_amount_cents or current.get("amount_cents", 2000),
        }
    await billing.update_settings(acc, monthly_limit_cents=body.monthly_limit_cents, auto_recharge=recharge)
    return await get_billing(p)


# ----------------------------------------------------------------------------------------- MCP keys


class NewKey(BaseModel):
    name: str = Field(default="MCP key", max_length=120)


@router.get("/repos/{repo_id}/keys")
async def list_keys(repo_id: str, p: CurrentPrincipal) -> list[dict]:
    await auth.repo_for(p, repo_id)
    return await auth.list_keys(p.account_id, repo_id)


@router.post("/repos/{repo_id}/keys", status_code=201)
async def create_key(repo_id: str, body: NewKey, p: CurrentPrincipal) -> dict:
    repo = await auth.repo_for(p, repo_id)
    if not repo.account_id:
        raise HTTPException(status_code=400, detail="this repository has no owning workspace")
    return await auth.create_key(repo.account_id, repo_id, body.name)


@router.delete("/keys/{key_id}")
async def revoke_key(key_id: str, p: CurrentPrincipal) -> dict:
    if not await auth.revoke_key(p.account_id, key_id):
        raise HTTPException(status_code=404, detail="unknown key")
    return {"revoked": key_id}
