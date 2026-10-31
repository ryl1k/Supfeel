"use client";

import Link from "next/link";
import { useParams } from "next/navigation";

import { Check, Cross } from "@/components/ui/icons";
import { usePoll } from "@/lib/usePoll";
import { api, type Fix, type Notification, type TicketAction, type TicketDetail } from "@/lib/workspace";

import { TraceView } from "./TraceView";
import { Badge, Card, CategoryBadge, cx, Empty, ErrorNote, Markdown, Spinner, StatusBadge, timeAgo } from "./ui";

const LIVE = new Set(["fix_in_review", "fix_verified", "awaiting_confirmation", "open"]);

export function DiffView({ diff }: { diff: string }) {
  return (
    <pre className="scrollbar-thin max-h-[420px] overflow-auto rounded-xl border border-line bg-bg-0/70 p-3 font-mono text-[12px] leading-relaxed">
      {diff.split("\n").map((line, i) => (
        <div
          key={i}
          className={cx(
            line.startsWith("+") && !line.startsWith("+++") && "bg-success/10 text-success",
            line.startsWith("-") && !line.startsWith("---") && "bg-danger/10 text-danger",
            line.startsWith("@@") && "text-indigo-400",
            (line.startsWith("+++") || line.startsWith("---")) && "text-lavender-200",
            !/^[-+@]/.test(line) && "text-text-300",
          )}
        >
          {line || " "}
        </div>
      ))}
    </pre>
  );
}

export function Checks({ checks }: { checks: { name: string; ok: boolean; detail?: string }[] }) {
  return (
    <ul className="space-y-1">
      {checks.map((c, i) => (
        <li key={i} className="flex items-start gap-2 text-[13px]">
          <span className={cx("mt-0.5", c.ok ? "text-success" : "text-danger")}>{c.ok ? <Check /> : <Cross />}</span>
          <span className="text-text-100">{c.name}</span>
          {c.detail ? <span className="text-text-300">· {c.detail}</span> : null}
        </li>
      ))}
    </ul>
  );
}

function FixCard({ fix }: { fix: Fix }) {
  if (!fix || !fix.decision) return null;
  const ci = fix.ci;
  return (
    <Card
      title="Engineering"
      action={
        fix.pr_url ? (
          <a href={fix.pr_url} target="_blank" rel="noreferrer" className="text-[13px] text-lavender-200 hover:text-white">
            Pull request #{fix.pr_number} ↗
          </a>
        ) : null
      }
    >
      <div className="space-y-4 text-[14px]">
        <div className="flex flex-wrap gap-2">
          <Badge tone={fix.decision === "fixed" ? "success" : fix.decision === "not_a_bug" ? "info" : "warning"}>
            {{ fixed: "Fixed", not_a_bug: "Works as designed", gave_up: "No safe fix", report: "Reported" }[fix.decision] ?? fix.decision}
          </Badge>
          {fix.mode ? <Badge>{fix.mode === "pr" ? "pull request" : "patch"}</Badge> : null}
          {ci ? <StatusBadge status={ci.state === "pending" ? "running" : ci.state} /> : null}
          {typeof fix.confidence === "number" && fix.confidence > 0 ? <Badge>confidence {Math.round(fix.confidence * 100)}%</Badge> : null}
        </div>
        {fix.root_cause ? (
          <div>
            <div className="text-[12px] uppercase tracking-wider text-text-300">Root cause</div>
            <p className="mt-1 text-text-100">{fix.root_cause}</p>
          </div>
        ) : null}
        {fix.summary ? (
          <div>
            <div className="text-[12px] uppercase tracking-wider text-text-300">Change</div>
            <p className="mt-1 text-text-100">{fix.summary}</p>
          </div>
        ) : null}
        {fix.test ? (
          <div>
            <div className="text-[12px] uppercase tracking-wider text-text-300">Regression test</div>
            <p className="mt-1 text-text-100">{fix.test}</p>
          </div>
        ) : null}
        {fix.explanation ? <p className="text-text-300">{fix.explanation}</p> : null}
        {fix.note ? <p className="text-warning">{fix.note}</p> : null}
        {fix.suspects?.length ? (
          <div>
            <div className="text-[12px] uppercase tracking-wider text-text-300">Suspect locations</div>
            <ul className="mt-1 space-y-0.5 font-mono text-[12.5px] text-lavender-200">
              {fix.suspects.map((s) => (
                <li key={s}>{s}</li>
              ))}
            </ul>
          </div>
        ) : null}
        {ci?.checks?.length ? (
          <div>
            <div className="mb-1 text-[12px] uppercase tracking-wider text-text-300">CI checks (verification)</div>
            <Checks checks={ci.checks.map((c) => ({ name: c.name, ok: c.conclusion === "success" || c.conclusion === "skipped", detail: c.conclusion ?? c.status }))} />
          </div>
        ) : null}
        {fix.diff ? (
          <details open>
            <summary className="cursor-pointer text-[13px] text-lavender-200">Diff ({fix.files?.join(", ")})</summary>
            <div className="mt-2">
              <DiffView diff={fix.diff} />
            </div>
          </details>
        ) : null}
      </div>
    </Card>
  );
}

function ActionsCard({ actions }: { actions: TicketAction[] }) {
  if (!actions.length) return null;
  return (
    <Card title="Actions on the customer's behalf">
      <ul className="space-y-4">
        {actions.map((a) => (
          <li key={a.id} className="rounded-xl border border-line bg-bg-0/40 p-3.5">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-[14px] font-medium text-text-100">{a.title}</span>
              <Badge tone={a.status === "done" ? "success" : a.status === "failed" ? "danger" : a.status === "declined" ? "neutral" : "warning"}>{a.status}</Badge>
              <span className="font-mono text-[12px] text-text-300">
                {a.method} {a.path}
              </span>
            </div>
            <details className="mt-2">
              <summary className="cursor-pointer text-[12px] text-lavender-200">Request and response</summary>
              <pre className="scrollbar-thin mt-2 max-h-60 overflow-auto whitespace-pre-wrap rounded-lg bg-bg-0/70 p-2 font-mono text-[12px] text-text-300">
                {JSON.stringify({ args: a.args, response: a.response }, null, 2)}
              </pre>
            </details>
            {a.verification ? (
              <div className="mt-2">
                <div className="mb-1 text-[12px] uppercase tracking-wider text-text-300">Verification {a.verification.ok ? "passed" : "failed"}</div>
                <Checks checks={a.verification.checks} />
              </div>
            ) : null}
          </li>
        ))}
      </ul>
    </Card>
  );
}

export function NotificationItem({ n }: { n: Notification }) {
  return (
    <li className="py-3">
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-[14px] text-text-100">{n.title}</span>
        {n.delivered.map((d) => (
          <Badge key={d} tone="success">
            {d}
          </Badge>
        ))}
        <span className="ml-auto text-[12px] text-text-300">{timeAgo(n.created_at)}</span>
      </div>
      {n.body ? <p className="mt-1 whitespace-pre-wrap text-[13px] text-text-300">{n.body}</p> : null}
      <div className="mt-1 flex gap-3 text-[12px]">
        {n.ticket_id ? (
          <Link href={`/app/tickets/${n.ticket_id}`} className="text-lavender-200 hover:text-white">
            {n.ticket_id}
          </Link>
        ) : null}
        {n.url && !n.url.includes("/app/tickets/") ? (
          <a href={n.url} target="_blank" rel="noreferrer" className="text-lavender-200 hover:text-white">
            Open ↗
          </a>
        ) : null}
      </div>
    </li>
  );
}

function Conversation({ t }: { t: TicketDetail }) {
  return (
    <Card title="Conversation">
      <ul className="space-y-3">
        {t.messages.map((m, i) => (
          <li key={i} className={cx("flex", m.role === "customer" ? "justify-end" : "justify-start")}>
            <div className={cx("max-w-[85%] rounded-2xl border px-4 py-2.5 text-[14px]", m.role === "customer" ? "border-line bg-bubble" : "border-indigo-400/30 bg-sapphire-600/15")}>
              <div className="mb-0.5 text-[11px] uppercase tracking-wider text-text-300">
                {m.role === "customer" ? t.customer.name || "Customer" : m.role === "frontline" ? "First-line agent" : "Supfeel"}
              </div>
              <Markdown text={m.content} className="text-text-100" />
            </div>
          </li>
        ))}
      </ul>
    </Card>
  );
}

export function TicketView() {
  const { id } = useParams<{ id: string }>();
  const ticket = usePoll(() => api.ticket(id), id, 4000, (d) => !d || LIVE.has(d.status));
  const trace = usePoll(() => api.ticketTrace(id), id, 6000, () => !ticket.data || LIVE.has(ticket.data.status));
  if (ticket.error && !ticket.data) return <ErrorNote>{ticket.error}</ErrorNote>;
  if (!ticket.data) return <Spinner className="h-6 w-6" />;
  const t = ticket.data;
  const brain = t.triage?.brain ?? {};

  return (
    <div className="space-y-6">
      <div>
        <Link href={`/app/repos/${t.repo_id}`} className="text-[13px] text-text-300 hover:text-text-100">
          ← {t.repo_id}
        </Link>
        <h1 className="mt-1 text-[24px] font-semibold tracking-tight">{t.subject || t.id}</h1>
        <div className="mt-2 flex flex-wrap items-center gap-2 text-[13px] text-text-300">
          <span className="font-mono">{t.id}</span>
          <StatusBadge status={t.status} />
          <CategoryBadge category={t.category} />
          {t.channel === "mcp" ? <Badge tone="info">via MCP</Badge> : null}
          {t.confidence !== null ? <Badge>triage {Math.round((t.confidence ?? 0) * 100)}%</Badge> : null}
          {t.learned ? <Badge tone="success">added to knowledge</Badge> : null}
          {Object.entries(brain).map(([node, b]) => (
            <Badge key={node} tone={b === "llm" ? "info" : "neutral"}>
              {node}: {b === "llm" ? "Claude" : "rules"}
            </Badge>
          ))}
          <span>
            · {t.customer.name || "anonymous"}
            {t.customer.ref ? ` (${t.customer.ref})` : ""} · {timeAgo(t.created_at)}
          </span>
        </div>
      </div>

      <div className="grid gap-5 lg:grid-cols-2">
        <div className="space-y-5">
          <Conversation t={t} />
          {t.resolution?.summary ? (
            <Card title="Resolution">
              <p className="text-[14px] text-text-100">{t.resolution.summary}</p>
              {t.triage?.bug_hypothesis ? <p className="mt-2 text-[13px] text-text-300">Triage hypothesis: {String(t.triage.bug_hypothesis)}</p> : null}
            </Card>
          ) : null}
        </div>
        <div className="space-y-5">
          <FixCard fix={t.fix} />
          <ActionsCard actions={t.actions} />
          <Card title="Business notifications">
            {t.notifications.length ? (
              <ul className="divide-y divide-line/60">
                {t.notifications.map((n) => (
                  <NotificationItem key={n.id} n={n} />
                ))}
              </ul>
            ) : (
              <Empty>No notifications for this ticket.</Empty>
            )}
          </Card>
        </div>
      </div>

      <Card title="Trace: every step, model call, search, API and GitHub request">
        <TraceView trace={trace.data} />
      </Card>
    </div>
  );
}
