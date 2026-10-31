"""Callbacks to the escalating agent: when a ticket changes after the MCP call returned (CI verdict, merge),
POST the relay view to the `callback_url` it gave us. Best effort, traced, signed with the key's id."""

import hashlib
import hmac
import json
import logging

import httpx

from app.config import get_settings
from app.db.models import ApiKey, Ticket
from app.db.session import session_scope
from app.obs import trace

log = logging.getLogger(__name__)


async def fire(ticket_id: str, event: str) -> bool:
    from app.support.service import relay  # late import: service → graph → ci → callbacks

    async with session_scope() as s:
        t = await s.get(Ticket, ticket_id)
        url = (t.meta or {}).get("callback_url") if t else None
        key = await s.get(ApiKey, (t.meta or {}).get("key_id", "")) if t else None
        secret = key.key_hash if key else get_settings().admin_token
    if not url:
        return False
    body = json.dumps({"event": event, "ticket": await relay(ticket_id)}, default=str).encode()
    # Signed with sha256(<your sf_live_ key>) as the HMAC secret: the receiver recomputes it from its own key.
    sig = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    async with trace.span(f"callback {event}", kind="http", trace_id=ticket_id, url=url) as sp:
        try:
            async with httpx.AsyncClient(timeout=10) as http:
                r = await http.post(
                    url,
                    content=body,
                    headers={
                        "Content-Type": "application/json",
                        "X-Supfeel-Event": event,
                        "X-Supfeel-Signature": f"sha256={sig}",
                    },
                )
            sp.set(status=r.status_code)
            return r.status_code < 400
        except httpx.HTTPError as e:
            sp.set(error=str(e)[:200])
            log.warning("callback for %s failed: %s", ticket_id, e)
            return False
