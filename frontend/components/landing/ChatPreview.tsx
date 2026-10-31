import Link from "next/link";

import { AssistantAvatar, AssistantBubble, AssistantRow, InfoCard, UserBubble } from "@/components/chat/primitives";
import { Dots, Send } from "@/components/ui/icons";

/** Static preview of the chat window from the landing mock. Links into the real chat. */
export function ChatPreview() {
  return (
    <div className="glass w-full max-w-[612px] rounded-[28px] shadow-[0_40px_120px_-40px_rgba(10,14,60,0.9)]">
      <div className="flex items-center gap-4 border-b border-line px-6 py-5 sm:px-9">
        <AssistantAvatar size={54} />
        <div className="flex-1">
          <div className="text-[22px] font-medium leading-tight">Supfeel</div>
          <div className="flex items-center gap-2 text-[15px] text-text-300">
            <span className="h-2.5 w-2.5 rounded-full bg-success" /> Online
          </div>
        </div>
        <Dots className="h-6 w-6 text-lavender-200" />
      </div>

      <div className="flex flex-col gap-5 px-4 py-6 sm:px-7">
        <UserBubble>I bought these sneakers, but they&apos;re uncomfortable. Can you help?</UserBubble>
        <AssistantRow>
          <AssistantBubble>Of course! Let&apos;s find a better option that matches your style.</AssistantBubble>
          <InfoCard title="Personalized recommendations" subtitle="matched to your style and fit" />
        </AssistantRow>
      </div>

      <div className="px-4 pb-6 sm:px-7">
        <Link
          href="/chat"
          className="flex items-center rounded-full border border-line py-2 pl-6 pr-2 text-[17px] text-text-300 transition-colors hover:border-lavender-300/50"
        >
          <span className="flex-1">Ask anything…</span>
          <span className="flex h-11 w-11 items-center justify-center rounded-full bg-sapphire-500 text-white">
            <Send />
          </span>
        </Link>
      </div>
    </div>
  );
}
