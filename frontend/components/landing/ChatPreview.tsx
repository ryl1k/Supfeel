import Link from "next/link";

import { AssistantAvatar, AssistantBubble, AssistantRow, UserBubble } from "@/components/chat/primitives";
import { Bolt, Check, Dots, Send } from "@/components/ui/icons";

const STEPS = [
  "Read the checkout code (3 files)",
  "Root cause: the address check rejects “#”",
  "Pull request #12 with a regression test",
  "CI passed: fix verified",
];

/** The landing story, played once: a customer's bot escalates to Supfeel, which finds and fixes the bug. */
export function ChatPreview() {
  return (
    <div className="glass anim-scale-in d-3 w-full max-w-[612px] rounded-[28px] shadow-[0_40px_120px_-40px_rgba(10,14,60,0.9)]">
      <div className="flex items-center gap-4 border-b border-line px-6 py-5 sm:px-9">
        <span className="anim-float">
          <AssistantAvatar size={54} />
        </span>
        <div className="flex-1">
          <div className="text-[22px] font-medium leading-tight">Supfeel</div>
          <div className="flex items-center gap-2 text-[15px] text-text-300">
            <span className="relative flex h-2.5 w-2.5">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-success opacity-60 motion-reduce:hidden" />
              <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-success" />
            </span>
            Working behind your support bot
          </div>
        </div>
        <Dots className="h-6 w-6 text-lavender-200" />
      </div>

      <div className="flex flex-col gap-4 px-4 py-6 sm:px-7">
        <div className="anim-fade-up" style={{ animationDelay: "500ms" }}>
          <UserBubble>Checkout keeps saying “Invalid address” for Apt #4B. I can&apos;t order!</UserBubble>
        </div>
        <div className="anim-fade-up flex justify-center" style={{ animationDelay: "1100ms" }}>
          <span className="flex items-center gap-2 rounded-full border border-indigo-400/40 bg-sapphire-600/15 px-3.5 py-1.5 text-[13px] text-lavender-200">
            <Bolt className="h-4 w-4" /> Slice bot escalated to Supfeel over MCP
          </span>
        </div>
        <AssistantRow>
          <div className="anim-fade-up rounded-[18px] border border-line bg-panel-strong px-5 py-4" style={{ animationDelay: "1500ms" }}>
            <ul className="space-y-2.5">
              {STEPS.map((s, i) => (
                <li key={s} className="anim-fade-up flex items-center gap-3 text-[14px] text-lavender-200" style={{ animationDelay: `${1800 + i * 550}ms` }}>
                  <span className="anim-pop flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-success/15 text-success" style={{ animationDelay: `${2000 + i * 550}ms` }}>
                    <Check className="h-3 w-3" />
                  </span>
                  {s}
                </li>
              ))}
            </ul>
          </div>
          <div className="anim-fade-up" style={{ animationDelay: "4300ms" }}>
            <AssistantBubble>Found it, and a fix is on its way. Until it ships, enter “Apt 4B” without the #.</AssistantBubble>
          </div>
        </AssistantRow>
      </div>

      <div className="px-4 pb-6 sm:px-7">
        <Link
          href="/signup"
          className="group flex items-center rounded-full border border-line py-2 pl-6 pr-2 text-[17px] text-text-300 transition-colors hover:border-lavender-300/50"
        >
          <span className="flex-1">Connect your repo…</span>
          <span className="flex h-11 w-11 items-center justify-center rounded-full bg-sapphire-500 text-white transition-transform group-hover:translate-x-0.5">
            <Send />
          </span>
        </Link>
      </div>
    </div>
  );
}
