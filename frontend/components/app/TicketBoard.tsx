"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import { Bolt, Search } from "@/components/ui/icons";
import { usePoll } from "@/lib/usePoll";
import { api, type TicketStatus, type TicketSummary } from "@/lib/workspace";

import { CATEGORY_COLORS, CATEGORY_LABEL } from "./Charts";
import { Badge, cx, Empty, ErrorNote, Input, StatusBadge, Tabs, timeAgo } from "./ui";
import { TicketList } from "./Workspace";

const COLUMNS: { id: string; title: string; hint: string; statuses: TicketStatus[]; dot: string }[] = [
  { id: "customer", title: "With the customer", hint: "answered, asked, or awaiting their OK", statuses: ["open", "answered", "awaiting_confirmation"], dot: "bg-indigo-400" },
  { id: "engineering", title: "With engineering", hint: "bug reported or fix in review", statuses: ["reported", "fix_in_review", "fix_failed"], dot: "bg-warning" },
  { id: "verified", title: "Fix verified", hint: "CI passed, waiting for merge", statuses: ["fix_verified"], dot: "bg-success" },
  { id: "human", title: "Needs a human", hint: "escalated to your team", statuses: ["escalated"], dot: "bg-danger" },
  { id: "resolved", title: "Resolved", hint: "closed and learned from", statuses: ["resolved"], dot: "bg-success" },
];

function TicketCard({ t, i }: { t: TicketSummary; i: number }) {
  const color = CATEGORY_COLORS[t.category ?? "other"] ?? CATEGORY_COLORS.other;
  return (
    <Link
      href={`/app/tickets/${t.id}`}
      style={{ animationDelay: `${Math.min(i, 8) * 50}ms` }}
      className="anim-fade-up lift relative block overflow-hidden rounded-2xl border border-line bg-panel-strong p-3.5 pl-4"
    >
      <span className="absolute inset-y-0 left-0 w-1" style={{ background: color }} aria-hidden />
      <div className="flex items-center gap-2 text-[11.5px]">
        <span className="font-mono text-text-300">{t.id}</span>
        {t.channel === "mcp" ? (
          <span className="flex items-center gap-1 rounded-full bg-indigo-400/15 px-1.5 py-0.5 text-lavender-200">
            <Bolt className="h-3 w-3" /> MCP
          </span>
        ) : null}
        <span className="ml-auto text-text-300">{timeAgo(t.created_at)}</span>
      </div>
      <p className="mt-1.5 line-clamp-2 text-[14px] font-semibold leading-snug text-white">{t.subject || "(no subject yet)"}</p>
      <div className="mt-2.5 flex flex-wrap items-center gap-1.5">
        <span className="flex items-center gap-1.5 text-[12px] text-text-300">
          <span className="h-2 w-2 rounded-[3px]" style={{ background: color }} />
          {CATEGORY_LABEL[t.category ?? "other"] ?? t.category ?? "Untriaged"}
        </span>
        <span className="ml-auto" />
        <StatusBadge status={t.status} />
      </div>
      {t.pr_url || t.customer?.name ? (
        <div className="mt-2.5 flex items-center gap-2 border-t border-line/60 pt-2 text-[12px] text-text-300">
          {t.customer?.name ? <span className="truncate">{t.customer.name}</span> : null}
          {t.pr_url ? (
            <span className="ml-auto flex items-center gap-1.5 whitespace-nowrap">
              PR #{t.pr_url.split("/pull/")[1]}
              {t.ci ? (
                <span className={cx("h-2 w-2 rounded-full", t.ci === "success" ? "bg-success" : t.ci === "failure" ? "bg-danger" : "bg-warning animate-pulse")} title={`CI ${t.ci}`} />
              ) : null}
            </span>
          ) : null}
        </div>
      ) : null}
    </Link>
  );
}

export function TicketBoard() {
  const tickets = usePoll(() => api.tickets(), "tickets-board", 5000);
  const [view, setView] = useState<"board" | "list">("board");
  const [q, setQ] = useState("");
  const [category, setCategory] = useState<string | null>(null);
  const [channel, setChannel] = useState<"all" | "mcp" | "web">("all");

  const filtered = useMemo(() => {
    const needle = q.trim().toLowerCase();
    return (tickets.data ?? []).filter(
      (t) =>
        (!category || t.category === category) &&
        (channel === "all" || t.channel === channel) &&
        (!needle || `${t.id} ${t.subject} ${t.customer?.name ?? ""}`.toLowerCase().includes(needle)),
    );
  }, [tickets.data, q, category, channel]);
  const counts = useMemo(() => {
    const c: Record<string, number> = {};
    for (const t of tickets.data ?? []) c[t.category ?? "other"] = (c[t.category ?? "other"] ?? 0) + 1;
    return c;
  }, [tickets.data]);

  return (
    <div className="space-y-5">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-[28px] font-bold tracking-tight">Tickets</h1>
          <p className="mt-1 text-[14px] text-text-300">Every escalation, by stage. Click a card for the conversation, fix and full trace.</p>
        </div>
        <Tabs<"board" | "list">
          value={view}
          onChange={setView}
          tabs={[
            { id: "board", label: "Board" },
            { id: "list", label: "List" },
          ]}
        />
      </div>

      <div className="flex flex-col gap-3 lg:flex-row lg:items-center">
        <div className="relative lg:w-72">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-300" />
          <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search tickets" aria-label="Search tickets" className="pl-9" />
        </div>
        <div className="scrollbar-thin flex flex-1 gap-1.5 overflow-x-auto">
          <button onClick={() => setCategory(null)} className={cx("whitespace-nowrap rounded-full border px-3 py-1.5 text-[13px]", !category ? "border-indigo-400 bg-sapphire-600/25 text-white" : "border-line text-text-300")}>
            All {tickets.data ? `(${tickets.data.length})` : ""}
          </button>
          {Object.keys(CATEGORY_LABEL).map((k) => (
            <button
              key={k}
              onClick={() => setCategory(category === k ? null : k)}
              className={cx("flex items-center gap-1.5 whitespace-nowrap rounded-full border px-3 py-1.5 text-[13px]", category === k ? "border-indigo-400 bg-sapphire-600/25 text-white" : "border-line text-text-300")}
            >
              <span className="h-2 w-2 rounded-[3px]" style={{ background: CATEGORY_COLORS[k] }} />
              {CATEGORY_LABEL[k]} {counts[k] ? `(${counts[k]})` : ""}
            </button>
          ))}
        </div>
        <select
          value={channel}
          onChange={(e) => setChannel(e.target.value as typeof channel)}
          aria-label="Channel"
          className="rounded-full border border-line bg-bg-0/60 px-3 py-1.5 text-[13px] text-text-100"
        >
          <option value="all">All channels</option>
          <option value="mcp">Via MCP</option>
          <option value="web">Playground</option>
        </select>
      </div>

      {tickets.error && !tickets.data ? <ErrorNote>{tickets.error}</ErrorNote> : null}
      {!tickets.data ? (
        <div className="grid gap-4 md:grid-cols-3 xl:grid-cols-5">
          {COLUMNS.map((c) => (
            <div key={c.id} className="skeleton h-64" />
          ))}
        </div>
      ) : view === "list" ? (
        <div className="rounded-[20px] border border-line bg-panel p-5">
          <TicketList tickets={filtered} />
        </div>
      ) : (
        <div className="scrollbar-thin -mx-4 flex snap-x gap-4 overflow-x-auto px-4 pb-3 xl:mx-0 xl:grid xl:grid-cols-5 xl:overflow-visible xl:px-0">
          {COLUMNS.map((col) => {
            const items = filtered.filter((t) => col.statuses.includes(t.status));
            return (
              <section key={col.id} className="flex w-[290px] shrink-0 snap-start flex-col rounded-[20px] border border-line bg-panel/70 p-3 xl:w-auto">
                <header className="mb-3 px-1">
                  <div className="flex items-center gap-2">
                    <span className={cx("h-2.5 w-2.5 rounded-full", col.dot)} />
                    <h2 className="text-[15px] font-bold text-white">{col.title}</h2>
                    <Badge className="ml-auto">{items.length}</Badge>
                  </div>
                  <p className="mt-0.5 pl-[18px] text-[12px] text-text-300">{col.hint}</p>
                </header>
                <div className="flex flex-1 flex-col gap-2.5">
                  {items.length ? items.map((t, i) => <TicketCard key={t.id} t={t} i={i} />) : <Empty>Nothing here</Empty>}
                </div>
              </section>
            );
          })}
        </div>
      )}
    </div>
  );
}
