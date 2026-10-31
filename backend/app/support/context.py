"""Context for a ticket: relevant code/docs/summaries, similar past tickets and candidate API operations."""

from typing import Any

from sqlalchemy import select

from app.db.models import ApiOperation
from app.db.session import session_scope
from app.obs import trace
from app.repos.search import Hit, search


async def gather(repo_id: str, text: str, extra_queries: list[str] | None = None) -> dict[str, Any]:
    async with trace.span("gather context", kind="step") as sp:
        hits: dict[int, Hit] = {}
        for q in [text, *(extra_queries or [])][:4]:
            for h in await search(repo_id, q, k=6, kinds=("code", "doc", "summary")):
                if h.id not in hits or hits[h.id].score < h.score:
                    hits[h.id] = h
        code = sorted(hits.values(), key=lambda h: -h.score)[:10]
        tickets = [h for h in await search(repo_id, text, k=3, kinds=("ticket",)) if h.score >= 0.35]
        api_hits = await search(repo_id, text, k=6, kinds=("api",))
        async with session_scope() as s:
            ops = (await s.scalars(select(ApiOperation).where(ApiOperation.repo_id == repo_id))).all()
            op_list = [
                {
                    "operation_id": o.operation_id,
                    "method": o.method,
                    "path": o.path,
                    "summary": o.summary,
                    "parameters": o.parameters,
                    "body_schema": o.body_schema,
                }
                for o in ops
            ]
        sp.set(
            code=[h.cite() for h in code],
            similar_tickets=[h.path for h in tickets],
            api_operations=len(op_list),
        )
    return {
        "hits": [h.to_dict() for h in code],
        "tickets": [h.to_dict() for h in tickets],
        "api_hits": [h.symbol for h in api_hits],
        "operations": op_list,
    }


def hits_block(ctx: dict[str, Any], max_chars: int = 1500) -> str:
    out = []
    for h in ctx.get("hits", []):
        cite = (
            f"{h['path']}:{h['start_line']}-{h['end_line']}"
            if h["start_line"]
            else f"{h['kind']}:{h['path']}"
        )
        out.append(
            f"[{cite}] ({h['kind']}{', ' + h['symbol'] if h['symbol'] else ''})\n{h['text'][:max_chars]}"
        )
    return "\n\n".join(out) or "(nothing relevant found)"


def tickets_block(ctx: dict[str, Any]) -> str:
    return "\n\n".join(f"[{h['path']}]\n{h['text'][:900]}" for h in ctx.get("tickets", [])) or "(none)"


def operations_block(ctx: dict[str, Any]) -> str:
    lines = []
    for o in ctx.get("operations", []):
        params = ", ".join(f"{p['name']} ({p['in']})" for p in o["parameters"])
        body = ", ".join(((o.get("body_schema") or {}).get("properties") or {}).keys())
        lines.append(
            f"- {o['operation_id']}: {o['method']} {o['path']} | {o['summary']} | params: {params or '-'} | body: {body or '-'}"
        )
    return "\n".join(lines) or "(no business API connected)"
