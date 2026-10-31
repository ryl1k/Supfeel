"""Business notifications: always stored (dashboard inbox), mirrored to Telegram / Slack / Discord when
configured. Delivery failures never break a ticket."""

import logging
from typing import Any

import httpx

from app.config import get_settings
from app.db.models import Notification
from app.db.session import session_scope
from app.obs import trace

log = logging.getLogger(__name__)
ICONS = {
    "bug_reported": "🐞", "pr_opened": "🛠️", "ci_passed": "✅", "ci_failed": "❌", "pr_merged": "🚀",
    "escalation": "🙋", "feature_request": "💡", "action_taken": "⚡", "ci_missing": "⚠️",
}  # fmt: skip


def _text(title: str, body: str, url: str | None) -> str:
    return "\n".join(x for x in (title, body.strip()[:1500], url) if x)


async def _telegram(http: httpx.AsyncClient, token: str, chat_id: str, text: str) -> None:
    r = await http.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": chat_id, "text": text[:4000], "disable_web_page_preview": True},
    )
    r.raise_for_status()


async def notify(
    repo_id: str, kind: str, title: str, body: str = "", url: str | None = None, ticket_id: str | None = None
) -> dict[str, Any]:
    settings = get_settings()
    title = f"{ICONS.get(kind, '🔔')} {title}"
    text = _text(title, body, url)
    delivered: list[str] = []
    async with trace.span(f"notify {kind}", kind="tool", kind_=kind, title=title) as sp:
        async with httpx.AsyncClient(timeout=10) as http:
            targets = []
            if settings.telegram_bot_token and settings.telegram_chat_id:
                targets.append(
                    (
                        "telegram",
                        _telegram(http, settings.telegram_bot_token, settings.telegram_chat_id, text),
                    )
                )
            if settings.slack_webhook_url:
                targets.append(("slack", http.post(settings.slack_webhook_url, json={"text": text})))
            if settings.discord_webhook_url:
                targets.append(
                    ("discord", http.post(settings.discord_webhook_url, json={"content": text[:1900]}))
                )
            for name, coro in targets:
                try:
                    res = await coro
                    if isinstance(res, httpx.Response):
                        res.raise_for_status()
                    delivered.append(name)
                except Exception as e:  # noqa: BLE001 - delivery is best effort
                    log.warning("notification via %s failed: %s", name, e)
                    sp.set(**{f"{name}_error": str(e)[:200]})
        sp.set(delivered=delivered)
    async with session_scope() as s:
        n = Notification(
            repo_id=repo_id,
            ticket_id=ticket_id,
            kind=kind,
            title=title,
            body=body,
            url=url,
            delivered=delivered,
        )
        s.add(n)
        await s.flush()
        return {"id": n.id, "kind": kind, "title": title, "delivered": delivered}
