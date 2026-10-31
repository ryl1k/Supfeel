"""Learning from tickets: every closed ticket becomes a `ticket` chunk in the repo's vector index, so similar
future tickets see how it was resolved (triage examples, known bugs, working explanations)."""

import hashlib

from sqlalchemy import delete

from app.db.models import RepoChunk, Ticket
from app.db.session import session_scope
from app.obs import trace
from app.rag.embeddings import active_model, embed

LEARNABLE = {"answered", "resolved", "fix_in_review", "fix_verified", "reported", "escalated"}


def ticket_text(t: Ticket, messages: list[dict]) -> str:
    customer = next((m["content"] for m in messages if m["role"] == "customer"), "")
    reply = next((m["content"] for m in reversed(messages) if m["role"] == "agent"), "")
    res = t.resolution or {}
    fix = t.fix or {}
    lines = [
        f"Past ticket {t.id} [{t.category}] status={t.status}: {t.subject}",
        f"Customer said: {customer[:600]}",
        f"Resolution: {res.get('summary', '')}",
    ]
    if fix.get("root_cause"):
        lines.append(f"Root cause: {fix['root_cause']}")
    if fix.get("files"):
        lines.append(f"Files changed: {', '.join(fix['files'])}")
    if fix.get("pr_url"):
        lines.append(f"Fix PR: {fix['pr_url']} (CI: {(fix.get('ci') or {}).get('state', 'n/a')})")
    if reply:
        lines.append(f"Our reply: {reply[:600]}")
    return "\n".join(lines)


async def learn(ticket_id: str, messages: list[dict]) -> bool:
    async with session_scope() as s:
        t = await s.get(Ticket, ticket_id)
        if t is None or t.status not in LEARNABLE:
            return False
        text = ticket_text(t, messages)
        repo_id = t.repo_id
    async with trace.span("learn from ticket", kind="step"):
        model = active_model()
        [vec] = await embed([text], node="ticket_learn")
        async with session_scope() as s:
            await s.execute(
                delete(RepoChunk).where(
                    RepoChunk.repo_id == repo_id, RepoChunk.kind == "ticket", RepoChunk.path == ticket_id
                )
            )
            s.add(
                RepoChunk(
                    repo_id=repo_id, kind="ticket", path=ticket_id, symbol=f"ticket {ticket_id}", text=text,
                    content_hash=hashlib.sha256((model + text).encode()).hexdigest(), embedding_model=model, embedding=vec,
                )
            )  # fmt: skip
            (await s.get(Ticket, ticket_id)).learned = True
    return True
