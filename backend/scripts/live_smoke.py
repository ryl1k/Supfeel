"""Live end-to-end smoke test against the real Claude API (costs ~$0.07 on a cold cache).

Usage: LLM_MODE=live uv run python -m scripts.live_smoke
Re-runs with identical prompts are served from .llm-cache/ for free.
"""

import asyncio
import json
import uuid

from app.agent import service
from app.llm import ledger


def _print_event(event: str, data: dict) -> None:
    if event == "step" and data["status"] == "done":
        brain = f" brain={data['brain']}" if "brain" in data else ""
        print(f"  [{data['step']}] {data['detail'][:140]}{brain}")
    elif event == "action_proposed":
        print("  PROPOSED:", [a["title"] for a in data["actions"]])
    elif event == "action_done":
        a = data["action"]
        print("  DONE:", a["title"], a["status"], a.get("error"))
    elif event == "verified":
        print("  VERIFIED:", data["title"], data["ok"])
    elif event in ("notice", "error", "recommendations"):
        print(f"  {event.upper()}:", json.dumps(data)[:300])
    elif event == "done":
        print("  OUTCOME:", data)


async def turn(events, label: str) -> None:
    print(f"\n=== {label}")
    reply: list[str] = []
    async for ev in events:
        if ev["event"] == "token":
            reply.append(ev["data"]["text"])
        else:
            _print_event(ev["event"], ev["data"])
    print("  REPLY:", "".join(reply))


async def main() -> None:
    conv = "live-" + uuid.uuid4().hex[:6]
    await turn(
        service.handle_message(
            conv, "cus_maya", "I bought these sneakers, but they're uncomfortable. Can you help?"
        ),
        "maya 1",
    )
    await turn(
        service.handle_message(conv, "cus_maya", "They feel too narrow, pinching on the sides."), "maya 2"
    )
    await turn(service.handle_confirm(conv, True), "maya confirm")
    await turn(
        service.handle_message(
            "live-" + uuid.uuid4().hex[:6], "cus_alex", "Why was I charged twice for my order??"
        ),
        "alex",
    )
    summary = await ledger.summary()
    print("\nSPEND (USD): anthropic", summary["anthropic_usd"], "openai", summary["openai_usd"])
    for row in summary["breakdown"]:
        print("  ", row)


if __name__ == "__main__":
    asyncio.run(main())
