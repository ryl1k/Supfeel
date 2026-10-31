import type { ReactNode } from "react";

import { Gem } from "@/components/brand/Gem";
import { Bolt, Chat, Search, Shield, UserIcon } from "@/components/ui/icons";

function Node({ icon, title, sub, strong }: { icon: ReactNode; title: string; sub: string; strong?: boolean }) {
  return (
    <div
      className={`lift flex min-w-[170px] items-center gap-3 rounded-2xl border px-4 py-3.5 ${
        strong ? "border-indigo-400/60 bg-sapphire-600/20 shadow-[0_20px_60px_-30px_rgba(67,83,240,0.9)]" : "border-line bg-panel-strong"
      }`}
    >
      <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full border border-line text-lavender-200">{icon}</span>
      <span>
        <span className="block text-[15px] font-medium text-text-100">{title}</span>
        <span className="block text-[12.5px] text-text-300">{sub}</span>
      </span>
    </div>
  );
}

/** Animated connector: dashes flow toward the next node, with a label. Vertical on small screens. */
function Link({ label }: { label?: string }) {
  return (
    <div className="flex shrink-0 flex-col items-center justify-center gap-1 py-1 lg:py-0" aria-hidden>
      {label ? <span className="text-[11px] uppercase tracking-[0.18em] text-lavender-300">{label}</span> : null}
      <svg width="70" height="14" viewBox="0 0 70 14" className="hidden lg:block">
        <path d="M2 7h62" stroke="var(--indigo-400)" strokeWidth="2" className="flow-dash" fill="none" />
        <path d="M58 2l6 5-6 5" stroke="var(--indigo-400)" strokeWidth="2" fill="none" />
      </svg>
      <svg width="14" height="34" viewBox="0 0 14 34" className="lg:hidden">
        <path d="M7 2v26" stroke="var(--indigo-400)" strokeWidth="2" className="flow-dash" fill="none" />
        <path d="M2 22l5 6 5-6" stroke="var(--indigo-400)" strokeWidth="2" fill="none" />
      </svg>
    </div>
  );
}

const OUTCOMES: [ReactNode, string, string][] = [
  [<Chat key="c" className="h-4 w-4" />, "Explain", "from your code and docs"],
  [<Bolt key="b" className="h-4 w-4" />, "Act", "via your API, after an OK"],
  [<Search key="s" className="h-4 w-4" />, "Fix", "pull request + regression test"],
];

export function EscalationFlow() {
  return (
    <div className="glass mt-12 rounded-[28px] p-5 sm:p-8">
      <div className="flex flex-col items-center gap-1 lg:flex-row lg:items-center lg:justify-between lg:gap-0">
        <Node icon={<UserIcon className="h-5 w-5" />} title="Customer" sub="stuck on a problem" />
        <Link />
        <Node icon={<Chat className="h-5 w-5" />} title="Your support bot" sub="first line, can't solve it" />
        <Link label="MCP" />
        <Node icon={<Gem size={26} />} title="Supfeel" sub="reads your repo" strong />
        <Link />
        <div className="flex flex-col gap-2">
          {OUTCOMES.map(([icon, t, sub], i) => (
            <div
              key={t}
              className="anim-fade-up flex items-center gap-2.5 rounded-xl border border-line bg-panel-strong px-3 py-2 text-[13px]"
              style={{ animationDelay: `${i * 120}ms` }}
            >
              <span className="text-indigo-400">{icon}</span>
              <span className="font-medium text-text-100">{t}</span>
              <span className="text-text-300">{sub}</span>
            </div>
          ))}
        </div>
        <Link />
        <Node icon={<Shield className="h-5 w-5" />} title="Verified" sub="read-back or CI, then relayed" />
      </div>
    </div>
  );
}
