"""Find your Telegram chat id and send a test message.

1. Create a bot with @BotFather (/newbot) and put the token in .env as TELEGRAM_BOT_TOKEN.
2. Send any message to the bot (or add it to a group and send a message there).
3. Run: `uv run python -m scripts.telegram_setup`
"""

import asyncio

import httpx

from app.config import get_settings


async def main() -> None:
    s = get_settings()
    if not s.telegram_bot_token:
        print("TELEGRAM_BOT_TOKEN is not set in .env")
        return
    base = f"https://api.telegram.org/bot{s.telegram_bot_token}"
    async with httpx.AsyncClient(timeout=15) as http:
        me = (await http.get(f"{base}/getMe")).json()
        if not me.get("ok"):
            print("Token rejected by Telegram:", me.get("description"))
            return
        print(f"Bot: @{me['result']['username']}")
        updates = (await http.get(f"{base}/getUpdates")).json().get("result", [])
        chats = {}
        for u in updates:
            msg = u.get("message") or u.get("channel_post") or u.get("my_chat_member") or {}
            chat = msg.get("chat")
            if chat:
                chats[chat["id"]] = chat.get("title") or chat.get("username") or chat.get("first_name")
        if not chats:
            print(
                "No chats yet: send a message to the bot (or in the group with the bot), then run this again."
            )
        for cid, name in chats.items():
            print(f"chat: {name!r}  ->  TELEGRAM_CHAT_ID={cid}")
        if s.telegram_chat_id:
            r = (
                await http.post(
                    f"{base}/sendMessage",
                    json={"chat_id": s.telegram_chat_id, "text": "✅ Supfeel notifications are connected."},
                )
            ).json()
            print("test message:", "sent" if r.get("ok") else r.get("description"))


if __name__ == "__main__":
    asyncio.run(main())
