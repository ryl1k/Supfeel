"use client";

import Link from "next/link";
import { type ReactNode, useState } from "react";

import { Bolt, Check, Cross, Search, Shield, Sparkle, UserIcon } from "@/components/ui/icons";
import type { Notification } from "@/lib/workspace";

import { cx, timeAgo } from "./ui";

type Kind = { label: string; icon: ReactNode; tone: string };
const KINDS: Record<string, Kind> = {
  bug_reported: { label: "Bug reported", icon: <Search className="h-4 w-4" />, tone: "danger" },
  pr_opened: { label: "Fix PR opened", icon: <Bolt className="h-4 w-4" />, tone: "info" },
  ci_passed: { label: "Fix verified", icon: <Shield className="h-4 w-4" />, tone: "success" },
  ci_failed: { label: "CI failed", icon: <Cross className="h-4 w-4" />, tone: "danger" },
  ci_missing: { label: "Fix unverified", icon: <Shield className="h-4 w-4" />, tone: "warning" },
  pr_merged: { label: "Fix shipped", icon: <Check className="h-4 w-4" />, tone: "success" },
  action_taken: { label: "Done for customer", icon: <Check className="h-4 w-4" />, tone: "success" },
  escalation: { label: "Needs a human", icon: <UserIcon className="h-4 w-4" />, tone: "warning" },
  feature_request: { label: "Feature request", icon: <Sparkle className="h-4 w-4" />, tone: "info" },
};
const TONE: Record<string, { chip: string; icon: string; bar: string }> = {
  danger: { chip: "border-danger/40 bg-danger/10 text-danger", icon: "bg-danger/15 text-danger", bar: "bg-danger" },
  warning: { chip: "border-warning/40 bg-warning/10 text-warning", icon: "bg-warning/15 text-warning", bar: "bg-warning" },
  success: { chip: "border-success/40 bg-success/10 text-success", icon: "bg-success/15 text-success", bar: "bg-success" },
  info: { chip: "border-indigo-400/40 bg-indigo-400/10 text-lavender-200", icon: "bg-indigo-400/20 text-lavender-200", bar: "bg-indigo-400" },
};

/** "🐞 Bug reported in ticket T-1: Checkout fails" → "Checkout fails". */
function headline(title: string): string {
  const clean = title.replace(/^[^\p{L}\p{N}]+/u, "").trim();
  const i = clean.indexOf(": ");
  return i >= 0 ? clean.slice(i + 2) : clean;
}

function parseBody(body: string) {
  const lines = body.split("\n").map((l) => l.trim()).filter(Boolean);
  const suspects = lines.find((l) => l.startsWith("Suspect locations:"))?.replace("Suspect locations:", "").split(",").map((s) => s.trim()).filter(Boolean) ?? [];
  const facts = lines.filter((l) => !l.startsWith("Suspect locations:") && !/^Suspected cause:\s*-?$/.test(l));
  const keyed = facts.map((l) => {
    const m = l.match(/^(Root cause|Fix|Test|Failing|Suspected cause):\s*(.*)$/);
    return m ? { key: m[1], value: m[2] } : { key: "", value: l };
  });
  return { keyed, suspects };
}

export function ActivityItem({ n, compact = false }: { n: Notification; compact?: boolean }) {
  const [open, setOpen] = useState(false);
  const kind = KINDS[n.kind] ?? { label: n.kind.replace(/_/g, " "), icon: <Sparkle className="h-4 w-4" />, tone: "info" };
  const tone = TONE[kind.tone];
  const { keyed, suspects } = parseBody(n.body);
  const summary = keyed.find((k) => k.key === "Root cause") ?? keyed.find((k) => k.key !== "Test") ?? keyed[0];
  const title = headline(n.title);
  const showSummary = summary && summary.value !== title;

  return (
    <li className="relative flex gap-3.5 py-4">
      <span className={cx("mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-xl", tone.icon)}>{kind.icon}</span>
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          <span className={cx("rounded-full border px-2 py-0.5 text-[11.5px] font-semibold uppercase tracking-wide", tone.chip)}>{kind.label}</span>
          {n.ticket_id ? (
            <Link href={`/app/tickets/${n.ticket_id}`} className="rounded-md bg-bg-0/60 px-1.5 py-0.5 font-mono text-[11.5px] text-lavender-200 hover:text-white">
              {n.ticket_id}
            </Link>
          ) : null}
          <span className="ml-auto whitespace-nowrap text-[12px] text-text-300">{timeAgo(n.created_at)}</span>
        </div>
        <p className={cx("mt-1.5 font-semibold leading-snug text-white", compact ? "line-clamp-2 text-[14.5px]" : "text-[15px]")}>{title}</p>
        {showSummary ? (
          <p className="mt-1 line-clamp-2 text-[13px] text-text-300">
            {summary.key ? <span className="text-lavender-200">{summary.key}: </span> : null}
            {summary.value}
          </p>
        ) : null}
        <div className="mt-2 flex flex-wrap items-center gap-3 text-[12.5px]">
          {n.url && !n.url.includes("/app/tickets/") ? (
            <a href={n.url} target="_blank" rel="noreferrer" className="font-medium text-lavender-200 hover:text-white">
              {n.url.includes("/pull/") ? `View PR #${n.url.split("/pull/")[1]}` : "Open"} ↗
            </a>
          ) : null}
          {keyed.length > 1 || suspects.length ? (
            <button onClick={() => setOpen(!open)} className="text-text-300 hover:text-text-100">
              {open ? "Hide details" : suspects.length ? `Details · ${suspects.length} suspect location${suspects.length === 1 ? "" : "s"}` : "Details"}
            </button>
          ) : null}
          {n.delivered.length ? <span className="text-text-300">sent to {n.delivered.join(", ")}</span> : null}
        </div>
        {open ? (
          <div className="anim-fade-up mt-2 space-y-1.5 rounded-xl border border-line bg-bg-0/50 p-3 text-[12.5px]">
            {keyed.map((k, i) => (
              <p key={i} className="text-text-300">
                {k.key ? <span className="font-medium text-text-100">{k.key}: </span> : null}
                {k.value}
              </p>
            ))}
            {suspects.length ? (
              <ul className="space-y-0.5 font-mono text-[12px] text-lavender-200">
                {suspects.map((s) => (
                  <li key={s}>{s}</li>
                ))}
              </ul>
            ) : null}
          </div>
        ) : null}
      </div>
    </li>
  );
}
