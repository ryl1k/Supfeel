import type { ReactNode } from "react";

import { Gem } from "@/components/brand/Gem";
import { ChevronRight, Sparkle, UserIcon } from "@/components/ui/icons";

export function AssistantAvatar({ size = 44 }: { size?: number }) {
  return <Gem size={size} className="shrink-0" />;
}

export function UserAvatar() {
  return (
    <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full border border-line bg-bubble text-lavender-200">
      <UserIcon />
    </span>
  );
}

export function UserBubble({ children }: { children: ReactNode }) {
  return (
    <div className="flex items-start justify-end gap-3">
      <div className="max-w-[78%] whitespace-pre-wrap rounded-[20px] border border-line bg-bubble px-5 py-3.5 text-[15px] leading-relaxed text-text-100 sm:text-base">
        {children}
      </div>
      <UserAvatar />
    </div>
  );
}

export function AssistantRow({ children }: { children: ReactNode }) {
  return (
    <div className="flex items-start gap-3">
      <AssistantAvatar />
      <div className="flex min-w-0 max-w-[88%] flex-1 flex-col gap-2.5">{children}</div>
    </div>
  );
}

export function AssistantBubble({ children }: { children: ReactNode }) {
  return (
    <div className="w-fit max-w-full rounded-[20px] border border-line bg-bubble px-5 py-3.5 text-[15px] leading-relaxed text-text-100 sm:text-base">
      {children}
    </div>
  );
}

/** Rich card inside an assistant turn (mock: "Personalized recommendations…"). */
export function InfoCard({
  title,
  subtitle,
  icon,
  onClick,
}: {
  title: string;
  subtitle?: string;
  icon?: ReactNode;
  onClick?: () => void;
}) {
  const Tag = onClick ? "button" : "div";
  return (
    <Tag
      onClick={onClick}
      className="flex w-full items-center gap-4 rounded-[18px] border border-line bg-panel-strong px-5 py-4 text-left transition-colors hover:border-lavender-300/40"
    >
      <span className="text-indigo-400">{icon ?? <Sparkle />}</span>
      <span className="flex-1 text-[14px] leading-snug text-lavender-200">
        {title}
        {subtitle ? <span className="block text-text-300">{subtitle}</span> : null}
      </span>
      <ChevronRight className="h-5 w-5 text-lavender-200" />
    </Tag>
  );
}
