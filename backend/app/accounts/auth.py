"""Email + password accounts with bearer session tokens, and per-repository API (MCP) keys.

Passwords: scrypt. Session tokens and API keys: random, only their sha256 is stored.
`x-admin-token` (ADMIN_TOKEN) is an operator override that sees every account.
"""

import hashlib
import hmac
import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import Depends, Header, HTTPException
from sqlalchemy import select, update

from app.accounts import billing
from app.config import get_settings
from app.db.models import Account, ApiKey, Repo, User, UserSession
from app.db.session import session_scope

SESSION_DAYS = 30
KEY_PREFIX = "sf_live_"


@dataclass
class Principal:
    account_id: str | None  # None = operator (admin token)
    user_id: str | None = None
    email: str | None = None

    @property
    def is_admin(self) -> bool:
        return self.account_id is None


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
    return f"scrypt${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _, salt_hex, digest_hex = stored.split("$")
    except ValueError:
        return False
    digest = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt_hex), n=2**14, r=8, p=1)
    return hmac.compare_digest(digest.hex(), digest_hex)


class AuthError(ValueError):
    pass


async def signup(email: str, name: str, password: str, company: str = "") -> tuple[str, Principal]:
    email = email.strip().lower()
    if len(password) < 8:
        raise AuthError("password must be at least 8 characters")
    async with session_scope() as s:
        if await s.scalar(select(User).where(User.email == email)):
            raise AuthError("an account with this email already exists")
        acc = Account(
            id="acc_" + uuid.uuid4().hex[:12], name=company.strip() or f"{name.strip() or email}'s workspace"
        )
        user = User(id="usr_" + uuid.uuid4().hex[:12], account_id=acc.id, email=email, name=name.strip() or email.split("@")[0],
                    password_hash=hash_password(password))  # fmt: skip
        s.add(acc)
        await s.flush()
        s.add(user)
    await billing.grant(acc.id, billing.FREE_GRANT_CENTS, "Welcome credit")
    return await _new_session(user.id), Principal(acc.id, user.id, email)


async def login(email: str, password: str) -> tuple[str, Principal]:
    async with session_scope() as s:
        user = await s.scalar(select(User).where(User.email == email.strip().lower()))
    if user is None or not verify_password(password, user.password_hash):
        raise AuthError("wrong email or password")
    return await _new_session(user.id), Principal(user.account_id, user.id, user.email)


async def _new_session(user_id: str) -> str:
    token = secrets.token_urlsafe(32)
    async with session_scope() as s:
        s.add(
            UserSession(
                token_hash=_sha(token),
                user_id=user_id,
                expires_at=datetime.now(UTC) + timedelta(days=SESSION_DAYS),
            )
        )
    return token


async def logout(token: str) -> None:
    async with session_scope() as s:
        row = await s.get(UserSession, _sha(token))
        if row:
            await s.delete(row)


async def principal_from_token(token: str) -> Principal | None:
    async with session_scope() as s:
        sess = await s.get(UserSession, _sha(token))
        if sess is None or sess.expires_at <= datetime.now(UTC):
            return None
        user = await s.get(User, sess.user_id)
    return Principal(user.account_id, user.id, user.email) if user else None


async def require_principal(
    authorization: str = Header(default=""), x_admin_token: str = Header(default="")
) -> Principal:
    """FastAPI dependency for dashboard endpoints."""
    if x_admin_token and hmac.compare_digest(x_admin_token, get_settings().admin_token):
        return Principal(None)
    if authorization.startswith("Bearer "):
        p = await principal_from_token(authorization[7:].strip())
        if p:
            return p
    raise HTTPException(status_code=401, detail="sign in required")


CurrentPrincipal = Annotated[Principal, Depends(require_principal)]


async def repo_for(principal: Principal, repo_id: str) -> Repo:
    async with session_scope() as s:
        repo = await s.get(Repo, repo_id)
        if repo is None or not (principal.is_admin or repo.account_id == principal.account_id):
            raise HTTPException(status_code=404, detail="unknown repository")
        s.expunge(repo)
        return repo


# ----------------------------------------------------------------------------------------- API (MCP) keys


async def create_key(account_id: str, repo_id: str, name: str) -> dict:
    raw = KEY_PREFIX + secrets.token_urlsafe(24)
    key = ApiKey(id="key_" + uuid.uuid4().hex[:12], account_id=account_id, repo_id=repo_id, name=name.strip()[:120] or "MCP key",
                 prefix=raw[:14], key_hash=_sha(raw))  # fmt: skip
    async with session_scope() as s:
        s.add(key)
    return {"id": key.id, "name": key.name, "prefix": key.prefix, "key": raw}


async def list_keys(account_id: str | None, repo_id: str) -> list[dict]:
    stmt = (
        select(ApiKey)
        .where(ApiKey.repo_id == repo_id, ApiKey.revoked.is_(False))
        .order_by(ApiKey.created_at.desc())
    )
    if account_id:
        stmt = stmt.where(ApiKey.account_id == account_id)
    async with session_scope() as s:
        rows = (await s.scalars(stmt)).all()
    return [
        {"id": k.id, "name": k.name, "prefix": k.prefix, "created_at": k.created_at.isoformat(),
         "last_used_at": k.last_used_at.isoformat() if k.last_used_at else None}
        for k in rows
    ]  # fmt: skip


async def revoke_key(account_id: str | None, key_id: str) -> bool:
    async with session_scope() as s:
        k = await s.get(ApiKey, key_id)
        if k is None or (account_id and k.account_id != account_id):
            return False
        k.revoked = True
        return True


@dataclass
class KeyContext:
    key_id: str
    key_name: str
    account_id: str
    repo_id: str


async def resolve_key(raw: str) -> KeyContext | None:
    if not raw.startswith(KEY_PREFIX):
        return None
    async with session_scope() as s:
        k = await s.scalar(select(ApiKey).where(ApiKey.key_hash == _sha(raw), ApiKey.revoked.is_(False)))
        if k is None:
            return None
        await s.execute(update(ApiKey).where(ApiKey.id == k.id).values(last_used_at=datetime.now(UTC)))
        return KeyContext(k.id, k.name, k.account_id, k.repo_id)


async def me(principal: Principal) -> dict:
    if principal.is_admin:
        return {"user": None, "account": None, "admin": True}
    async with session_scope() as s:
        user = await s.get(User, principal.user_id)
        acc = await s.get(Account, principal.account_id)
    return {
        "admin": False,
        "user": {"id": user.id, "email": user.email, "name": user.name},
        "account": {"id": acc.id, "name": acc.name},
    }
