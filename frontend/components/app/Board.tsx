"use client";

import Link from "next/link";
import type { ReactNode } from "react";

import { CountUp } from "@/components/motion/CountUp";
import { ArrowRight, Check } from "@/components/ui/icons";
import { usePoll } from "@/lib/usePoll";
import { api, type Dashboard } from "@/lib/workspace";

import { CategoryBar, DailyBars, Ring } from "./Charts";
import { money } from "./Shell";
import { NotificationItem } from "./TicketView";
import { Card, cx, Empty, ErrorNote } from "./ui";
import { GithubCard, ImportCard, RepoCard, TicketList } from "./Workspace";

interface Step {
  done: boolean;
  title: string;
  body: string;
  href: string;
  cta: string;
  optional?: boolean;
}

function steps(d: Dashboard): Step[] {
  const repo = d.onboarding.first_repo_id;
  const repoHref = (tab = "") => (repo ? `/app/repos/${repo}${tab ? `?tab=${tab}` : ""}` : "/app/welcome");
  return [
    { done: d.onboarding.repo_imported, title: "Import your repository", body: "Supfeel reads the code, docs and API spec.", href: "/app/welcome", cta: "Import" },
    { done: d.onboarding.repo_ready, title: "Let Supfeel learn it", body: "Indexing and explanations finish in about a minute.", href: repoHref(), cta: "View progress" },
    { done: d.onboarding.api_connected, title: "Connect your business API", body: "So Supfeel can act for customers.", href: repoHref("settings"), cta: "Connect", optional: true },
    { done: d.onboarding.key_created, title: "Create an MCP key", body: "One key per agent that escalates to Supfeel.", href: repoHref("connect"), cta: "Create key" },
    { done: d.onboarding.first_mcp_escalation || d.onboarding.first_ticket, title: "Send your first escalation", body: "From your agent, or try it in the playground.", href: repo ? `/support/${repo}` : "/app/welcome", cta: "Try it" },
    { done: d.onboarding.payment_method, title: "Add a card", body: "Pay as you go when the free credit runs out.", href: "/app/billing", cta: "Add card", optional: true },
  ];
}

function Checklist({ d }: { d: Dashboard }) {
  const list = steps(d);
  const required = list.filter((s) => !s.optional);
  const progress = list.filter((s) => s.done).length / list.length;
  if (required.every((s) => s.done)) return null;
  const next = list.find((s) => !s.done && !s.optional) ?? list.find((s) => !s.done);
  return (
    <section className="anim-fade-up rounded-[24px] border border-indigo-400/40 bg-[linear-gradient(120deg,rgba(47,63,224,0.22),rgba(30,38,110,0.35))] p-5 sm:p-7">
      <div className="flex flex-col gap-5 lg:flex-row lg:items-center">
        <div className="flex items-center gap-4 lg:w-72">
          <Ring value={progress} />
          <div>
            <h2 className="text-[18px] font-semibold">Get Supfeel working</h2>
            <p className="text-[13px] text-text-300">
              {list.filter((s) => s.done).length} of {list.length} done
            </p>
          </div>
        </div>
        <ol className="stagger grid flex-1 gap-2 sm:grid-cols-2 xl:grid-cols-3">
          {list.map((s, i) => (
            <li key={s.title}>
              <Link
                href={s.href}
                className={cx(
                  "lift flex h-full items-start gap-3 rounded-2xl border px-3.5 py-3",
                  s === next ? "border-indigo-400 bg-sapphire-600/25" : "border-line bg-panel-strong/70",
                  s.done && "opacity-70",
                )}
              >
                <span
                  className={cx(
                    "mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-[12px] font-semibold",
                    s.done ? "anim-pop bg-success/20 text-success" : s === next ? "bg-sapphire-600 text-white" : "border border-line text-text-300",
                  )}
                >
                  {s.done ? <Check className="h-3.5 w-3.5" /> : i + 1}
                </span>
                <span className="min-w-0 flex-1">
                  <span className={cx("block text-[14px] font-medium", s.done ? "text-text-300 line-through decoration-text-300/40" : "text-text-100")}>
                    {s.title}
                    {s.optional ? <span className="ml-1.5 text-[11px] font-normal text-text-300">optional</span> : null}
                  </span>
                  <span className="block text-[12.5px] text-text-300">{s.body}</span>
                </span>
                {!s.done ? <span className="mt-0.5 shrink-0 text-[12px] text-lavender-200">{s.cta} →</span> : null}
              </Link>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}

function Kpi({ label, value, sub, href }: { label: string; value: ReactNode; sub?: ReactNode; href?: string }) {
  const body = (
    <>
      <div className="text-[12px] uppercase tracking-wider text-text-300">{label}</div>
      <div className="mt-1.5 text-[28px] font-semibold leading-none text-text-100">{value}</div>
      {sub ? <div className="mt-2 text-[12.5px] text-text-300">{sub}</div> : null}
    </>
  );
  return href ? (
    <Link href={href} className="lift block rounded-[20px] border border-line bg-panel px-5 py-4">
      {body}
    </Link>
  ) : (
    <div className="lift rounded-[20px] border border-line bg-panel px-5 py-4">{body}</div>
  );
}

function greeting() {
  const h = new Date().getHours();
  return h < 5 ? "Good night" : h < 12 ? "Good morning" : h < 18 ? "Good afternoon" : "Good evening";
}

export function Board() {
  const dash = usePoll(() => api.dashboard(), "dash", 8000);
  const me = usePoll(() => api.me(), "me-board", 60_000);
  const status = usePoll(() => api.githubStatus(), "gh", 60_000);
  const repos = usePoll(() => api.repos(), "repos", 3000, (d) => !!d?.some((r) => r.status === "indexing" || r.status === "pending"));
  const tickets = usePoll(() => api.tickets(), "tickets", 10_000);
  const notes = usePoll(() => api.notifications(), "notes", 10_000);
  const d = dash.data;
  const b = d?.billing;
  const name = me.data?.user?.name?.split(" ")[0];

  return (
    <div className="space-y-6">
      <div className="anim-fade-up flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-[28px] font-semibold tracking-tight sm:text-[34px]">
            {greeting()}
            {name ? `, ${name}` : ""}
          </h1>
          <p className="mt-1 text-[15px] text-text-300">{me.data?.account?.name ?? "Your workspace"}: last 30 days</p>
        </div>
        <div className="flex gap-2">
          {d?.onboarding.first_repo_id ? (
            <Link href={`/support/${d.onboarding.first_repo_id}`} className="rounded-full border border-line px-4 py-2 text-[14px] text-lavender-200 hover:border-lavender-300/60">
              Playground
            </Link>
          ) : null}
          <Link href="/app/welcome" className="btn-primary inline-flex items-center gap-2 rounded-full px-4 py-2 text-[14px] font-medium text-white">
            Add repository <ArrowRight />
          </Link>
        </div>
      </div>

      {dash.error && !d ? <ErrorNote>Can&apos;t reach the Supfeel API: {dash.error}</ErrorNote> : null}
      {!d ? (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {[0, 1, 2, 3].map((i) => (
            <div key={i} className="skeleton h-[104px]" />
          ))}
        </div>
      ) : (
        <>
          <Checklist d={d} />
          <div className="stagger grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <Kpi label="Tickets" value={<CountUp value={d.tickets} />} sub={`${d.by_channel.mcp ?? 0} via MCP · ${d.by_channel.web ?? 0} playground`} href="/app/tickets" />
            <Kpi
              label="Handled by Supfeel"
              value={<CountUp value={d.tickets ? (d.automated / d.tickets) * 100 : 0} format={(n) => `${Math.round(n)}%`} />}
              sub={`${d.escalated_to_human} handed to a human`}
            />
            <Kpi label="Fixes" value={<CountUp value={d.fixes.prs + d.fixes.patches} />} sub={`${d.fixes.prs} PRs · ${d.fixes.ci_passed} passed CI`} />
            <Kpi
              label="Credit"
              value={<CountUp value={(b?.balance_cents ?? 0) / 100} format={(n) => `$${n.toFixed(2)}`} />}
              sub={b ? `${money(b.month.spent_cents)} of ${money(b.month.limit_cents)} this month` : ""}
              href="/app/billing"
            />
          </div>
          <div className="grid gap-5 lg:grid-cols-[1.5fr_1fr]">
            <Card title="Tickets per day" action={<span className="text-[12px] text-text-300">last 14 days</span>}>
              <DailyBars data={d.daily} />
            </Card>
            <Card title="What customers needed">
              <CategoryBar counts={d.by_category} />
              <div className="mt-5 grid grid-cols-3 gap-2 border-t border-line pt-4 text-center">
                <div>
                  <div className="text-[18px] font-semibold"><CountUp value={d.actions.verified} /></div>
                  <div className="text-[11.5px] text-text-300">actions verified</div>
                </div>
                <div>
                  <div className="text-[18px] font-semibold"><CountUp value={d.fixes.not_a_bug} /></div>
                  <div className="text-[11.5px] text-text-300">&quot;bugs&quot; that weren&apos;t</div>
                </div>
                <div>
                  <div className="text-[18px] font-semibold"><CountUp value={d.learned} /></div>
                  <div className="text-[11.5px] text-text-300">tickets learned</div>
                </div>
              </div>
            </Card>
          </div>
        </>
      )}

      <div className="grid gap-5 lg:grid-cols-[1.5fr_1fr]">
        <Card
          title="Recent tickets"
          action={
            <Link href="/app/tickets" className="text-[13px] text-lavender-200 hover:text-white">
              All tickets
            </Link>
          }
        >
          <TicketList tickets={(tickets.data ?? []).slice(0, 7)} loading={!tickets.data} />
        </Card>
        <Card
          title="Activity"
          action={
            <Link href="/app/inbox" className="text-[13px] text-lavender-200 hover:text-white">
              Inbox
            </Link>
          }
        >
          {!notes.data ? (
            <div className="space-y-3">
              <div className="skeleton h-10" />
              <div className="skeleton h-10" />
            </div>
          ) : notes.data.length ? (
            <ul className="stagger divide-y divide-line/60">
              {notes.data.slice(0, 6).map((n) => (
                <NotificationItem key={n.id} n={n} />
              ))}
            </ul>
          ) : (
            <Empty>Bugs found, PRs, CI results and escalations show up here.</Empty>
          )}
        </Card>
      </div>

      <section>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-[15px] font-semibold text-lavender-200">Repositories</h2>
          <span className="text-[12px] text-text-300">{repos.data ? `${repos.data.length} connected` : ""}</span>
        </div>
        {!repos.data ? (
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            <div className="skeleton h-40" />
            <div className="skeleton h-40" />
          </div>
        ) : repos.data.length ? (
          <div className="stagger grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {repos.data.map((r) => (
              <RepoCard key={r.id} repo={r} />
            ))}
          </div>
        ) : (
          <Empty>
            No repositories yet.{" "}
            <Link href="/app/welcome" className="text-lavender-200 hover:text-white">
              Start the setup
            </Link>
          </Empty>
        )}
      </section>

      {repos.data?.length ? (
        <details className="group rounded-[20px] border border-line bg-panel/60">
          <summary className="cursor-pointer list-none px-5 py-4 text-[14px] text-lavender-200">Import another repository · GitHub connection</summary>
          <div className="grid gap-5 px-5 pb-5 lg:grid-cols-[1.4fr_1fr]">
            <ImportCard status={status.data} onImported={() => repos.refresh()} />
            <GithubCard status={status.data} />
          </div>
        </details>
      ) : null}
    </div>
  );
}
