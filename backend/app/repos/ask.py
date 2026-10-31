"""Developer/support Q&A over an indexed repository, grounded in retrieved chunks with citations."""

import uuid

from pydantic import BaseModel, Field

from app.accounts.context import current_account
from app.llm.client import BudgetExceeded, LlmUnavailable, complete_json
from app.obs import trace
from app.repos.search import Hit, search

ASK_SYSTEM = """You answer questions about a software repository using ONLY the numbered context excerpts
(code, docs, generated module summaries, API operations, past support tickets).
- Be concise and concrete; reference files as `path:line`.
- If the excerpts do not contain the answer, say so plainly and suggest where to look.
- `citations` lists the excerpt ids you actually used."""


class Answer(BaseModel):
    answer: str = Field(description="markdown answer")
    citations: list[str] = Field(
        description="ids of the context excerpts used, e.g. 'slice_api/pricing.py:10-20'"
    )
    confidence: float = Field(description="0..1")


def context_block(hits: list[Hit], max_chars: int = 1600) -> str:
    return "\n\n".join(h.prompt_block(max_chars) for h in hits)


def rules_answer(question: str, hits: list[Hit]) -> Answer:
    if not hits:
        return Answer(
            answer="I couldn't find anything relevant in this repository.", citations=[], confidence=0.0
        )
    lines = ["Most relevant places in the code:"]
    for h in hits[:5]:
        first = next((ln.strip() for ln in h.text.splitlines() if ln.strip()), "")[:140]
        lines.append(f"- `{h.cite()}`{' · ' + h.symbol if h.symbol else ''}: {first}")
    return Answer(answer="\n".join(lines), citations=[h.cite() for h in hits[:5]], confidence=0.3)


async def ask(repo_id: str, question: str, account_id: str | None = None) -> dict:
    trace_id = "ask_" + uuid.uuid4().hex[:12]
    current_account.set(account_id)
    async with trace.span("ask repository", kind="run", trace_id=trace_id, question=question[:500]) as sp:
        hits = await search(repo_id, question, k=8)
        brain = "llm"
        try:
            ans = await complete_json(
                node="repo_ask",
                system=ASK_SYSTEM,
                user=f"Context:\n{context_block(hits)}\n\nQuestion: {question}",
                schema=Answer,
                max_tokens=900,
                conversation_id=trace_id,
            )
        except (LlmUnavailable, BudgetExceeded):
            ans, brain = rules_answer(question, hits), "rules"
        sp.set(brain=brain, citations=ans.citations)
    return {
        "trace_id": trace_id,
        "brain": brain,
        **ans.model_dump(),
        "sources": [h.to_dict() | {"text": h.text[:600], "cite": h.cite()} for h in hits],
    }
