"""Live end-to-end check of the code-support pipeline (real Claude + OpenAI, ≈ $0.5–1.5 on a cold cache).

Indexes a scratch copy of examples/slice-pizza (local source: fixes become patches, no GitHub needed) and runs
one ticket per route. Run: `LLM_MODE=live uv run python -m scripts.live_support_smoke`
"""

import asyncio
import shutil
import tempfile
from pathlib import Path

import httpx
from sqlalchemy import delete

import app.main  # noqa: F401  (demo store on sys.path)
from app.config import REPO_ROOT, get_settings
from app.db.models import Repo
from app.db.seed import init_db
from app.db.session import session_scope
from app.llm import ledger
from app.repos.indexer import start_job
from app.support import assist, service

RID = "local__smoke__slice"


async def spend() -> float:
    return (await ledger.summary())["anthropic_usd"]


async def run(label: str, events) -> dict:
    out: dict = {"tokens": []}
    async for ev in events:
        e, d = ev["event"], ev["data"]
        if e == "step" and d.get("status") == "done" or e == "step" and d.get("step") == "fix":
            print(f"   · {d['step']}: {d.get('detail', '')[:140]}")
        elif e == "token":
            out["tokens"].append(d["text"])
        elif e in ("ticket", "done", "action_proposed", "verified", "fix", "error"):
            out[e] = d
    print(f"   reply: {''.join(out['tokens']).strip()[:600]}")
    print(f"   done: {out.get('done') or out.get('error')}")
    return out


async def main() -> None:
    s = get_settings()
    assert s.llm_mode == "live", "set LLM_MODE=live"
    await init_db()
    from slice_api import store
    from slice_api.main import app as slice_app

    store.reset()
    assist.transport = httpx.ASGITransport(app=slice_app)
    root = Path(tempfile.mkdtemp()) / "slice"
    shutil.copytree(
        REPO_ROOT / "examples/slice-pizza",
        root,
        ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"),
    )
    async with session_scope() as db:
        await db.execute(delete(Repo).where(Repo.id == RID))
        db.add(Repo(id=RID, full_name="smoke/slice", source="local", local_path=str(root),
                    settings={"api_base_url": "http://slice.test", "api_token": "demo-service-token", "business_name": "Slice"}))  # fmt: skip

    t0 = await spend()
    print("1) index")
    await start_job(RID, trigger="import", background=False)
    async with session_scope() as db:
        r = await db.get(Repo, RID)
        print(
            f"   status={r.status} stats={ {k: r.stats.get(k) for k in ('files', 'chunks', 'api_operations', 'modules', 'last_job_claude_usd')} }"
        )
        print("   overview:", r.overview[:300].replace("\n", " "))
    t1 = await spend()
    print(f"   cost ${t1 - t0:.4f}")

    print("2) explanation ticket")
    maya = {"name": "Maya Chen", "ref": "c_maya"}
    await run(
        "explain",
        service.create_ticket(RID, maya, "Why did I pay $3.99 delivery on my last order? It was almost $25."),
    )
    t2 = await spend()
    print(f"   cost ${t2 - t1:.4f}")

    print("3) assisted action ticket")
    jordan = {"name": "Jordan Blake", "ref": "c_jordan"}
    res = await run(
        "assist",
        service.create_ticket(
            RID, jordan, "The app crashes when I tap Reorder. Could you place my last order again for me?"
        ),
    )
    if res.get("done", {}).get("status") == "awaiting_confirmation":
        print("   proposed:", res["action_proposed"]["actions"][0]["title"])
        await run("confirm", service.confirm(res["ticket"]["ticket_id"], True))
    t3 = await spend()
    print(f"   cost ${t3 - t2:.4f}")

    print("4) bug ticket (fix agent)")
    res = await run(
        "bug",
        service.create_ticket(
            RID, maya, "Checkout keeps saying 'Invalid address' for 12 Oak St Apt #4B. I can't order!"
        ),
    )
    t = await service.get_ticket(res["ticket"]["ticket_id"])
    fix = t["fix"] or {}
    print(f"   decision={fix.get('decision')} mode={fix.get('mode')} files={fix.get('files')}")
    print(f"   root cause: {fix.get('root_cause')}")
    print("   diff:\n" + "\n".join("     " + ln for ln in (fix.get("diff") or "").splitlines()[:60]))
    t4 = await spend()
    print(f"   cost ${t4 - t3:.4f}")
    print(
        f"TOTAL Claude ${t4 - t0:.4f} (all-time ${t4:.4f}); OpenAI all-time ${(await ledger.summary())['openai_usd']:.4f}"
    )


if __name__ == "__main__":
    asyncio.run(main())
