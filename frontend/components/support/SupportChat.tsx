"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { type FormEvent, useEffect, useMemo, useRef, useState } from "react";

import { Checks } from "@/components/app/TicketView";
import { Markdown, Spinner, cx } from "@/components/app/ui";
import { Gem, Logo } from "@/components/brand/Gem";
import { AssistantRow, UserBubble } from "@/components/chat/primitives";
import { Bolt, Check, Refresh, Search, Send, Shield, Sparkle } from "@/components/ui/icons";
import { usePoll } from "@/lib/usePoll";
import { useSessionToken } from "@/lib/session";
import { type AgentTurn, useTicketChat } from "@/lib/useTicketChat";
import { api } from "@/lib/workspace";

const STEP_LABEL: Record<string, string> = {
  context: "Understand",
  triage: "Triage",
  explain: "Explain",
  assist: "Plan action",
  act: "Act",
  verify: "Verify",
  fix: "Fix",
  feature: "Product team",
  escalate: "Hand over",
  respond: "Reply",
};
const STEP_ICON: Record<string, React.ReactNode> = {
  context: <Search className="h-4 w-4" />,
  triage: <Sparkle className="h-4 w-4" />,
  fix: <Bolt className="h-4 w-4" />,
  verify: <Shield className="h-4 w-4" />,
  act: <Bolt className="h-4 w-4" />,
};

const DEMO_PEOPLE = [
  { name: "Maya Chen", ref: "c_maya", email: "maya@example.com" },
  { name: "Jordan Blake", ref: "c_jordan", email: "jordan@example.com" },
];
const SLICE_PROMPTS = [
  "Checkout keeps saying 'Invalid address' for 12 Oak St Apt #4B. I can't order!",
  "The app crashes when I tap Reorder. Could you place my last order again for me?",
  "Why do I pay a delivery fee? Isn't delivery free?",
  "Please cancel my latest order.",
];
const GENERIC_PROMPTS = ["Something isn't working: I get an error when I try to…", "How does … work?", "Can you do … for me?"];

function StepTrail({ turn, ticketId }: { turn: AgentTurn; ticketId: string | null }) {
  const [open, setOpen] = useState(false);
  const steps = turn.steps.filter((s) => s.step !== "respond");
  if (!steps.length) return null;
  return (
    <div className="rounded-[18px] border border-line bg-panel-strong px-4 py-3">
      <button onClick={() => setOpen(!open)} className="flex w-full flex-wrap items-center gap-x-3 gap-y-2 text-left">
        {steps.map((s) => (
          <span key={s.step} className="flex items-center gap-1.5 text-[13px]">
            <span className={cx("flex h-5 w-5 items-center justify-center rounded-full", s.status === "done" ? "bg-success/15 text-success" : "bg-indigo-400/20 text-lavender-200")}>
              {s.status === "done" ? <Check className="h-3 w-3" /> : <Spinner className="h-3 w-3" />}
            </span>
            <span className={s.status === "done" ? "text-text-300" : "text-text-100"}>{STEP_LABEL[s.step] ?? s.step}</span>
          </span>
        ))}
        <span className="ml-auto text-[12px] text-lavender-200">{open ? "Hide" : "Details"}</span>
      </button>
      {open ? (
        <ul className="mt-3 space-y-2 border-t border-line pt-3">
          {steps.map((s) => (
            <li key={s.step} className="text-[13px]">
              <div className="flex items-center gap-2 text-text-100">
                <span className="text-indigo-400">{STEP_ICON[s.step] ?? <Sparkle className="h-4 w-4" />}</span>
                {STEP_LABEL[s.step] ?? s.step}
              </div>
              <p className="ml-6 text-text-300">{s.detail}</p>
              {s.history.length > 1 ? (
                <ul className="ml-6 mt-1 space-y-0.5 font-mono text-[12px] text-text-300/80">
                  {s.history.slice(1).map((h, i) => (
                    <li key={i}>› {h}</li>
                  ))}
                </ul>
              ) : null}
            </li>
          ))}
          {ticketId ? (
            <li>
              <Link href={`/app/tickets/${ticketId}`} target="_blank" className="text-[12px] text-lavender-200 hover:text-white">
                Open full trace for {ticketId} ↗
              </Link>
            </li>
          ) : null}
        </ul>
      ) : null}
    </div>
  );
}

function ProposalCard({ turn, onDecide, disabled }: { turn: AgentTurn; onDecide: (ok: boolean) => void; disabled: boolean }) {
  if (!turn.proposed.length) return null;
  const a = turn.proposed[0];
  const body = (a.args?.body ?? {}) as Record<string, unknown>;
  return (
    <div className="rounded-[18px] border border-warning/40 bg-warning/5 px-5 py-4">
      <div className="text-[12px] uppercase tracking-wider text-warning">Needs your OK</div>
      <div className="mt-1 text-[15px] font-medium text-text-100">{a.title}</div>
      {a.why ? <p className="mt-1 text-[13px] text-text-300">{a.why}</p> : null}
      {Object.keys(body).length ? (
        <pre className="scrollbar-thin mt-2 max-h-40 overflow-auto rounded-lg bg-bg-0/60 p-2 font-mono text-[11.5px] text-text-300">{JSON.stringify(body, null, 2)}</pre>
      ) : null}
      {turn.confirmation === "pending" ? (
        <div className="mt-3 flex gap-2">
          <button disabled={disabled} onClick={() => onDecide(true)} className="btn-primary rounded-full px-4 py-2 text-[14px] font-medium text-white disabled:opacity-50">
            Approve
          </button>
          <button disabled={disabled} onClick={() => onDecide(false)} className="rounded-full border border-line px-4 py-2 text-[14px] text-lavender-200 disabled:opacity-50">
            Not now
          </button>
        </div>
      ) : turn.confirmation ? (
        <p className="mt-2 text-[13px] text-text-300">{turn.confirmation === "approved" ? "Approved" : "Declined"}</p>
      ) : null}
    </div>
  );
}

function VerifiedCard({ v }: { v: AgentTurn["verified"][number] }) {
  return (
    <div className={cx("rounded-[18px] border px-5 py-4", v.ok ? "border-success/40 bg-success/5" : "border-danger/40 bg-danger/5")}>
      <div className={cx("flex items-center gap-2 text-[12px] uppercase tracking-wider", v.ok ? "text-success" : "text-danger")}>
        <Shield className="h-4 w-4" /> {v.ok ? "Verified" : "Verification failed"}
      </div>
      <div className="mt-1 text-[15px] font-medium text-text-100">{v.title}</div>
      <div className="mt-2">
        <Checks checks={v.checks} />
      </div>
    </div>
  );
}

function FixCard({ turn }: { turn: AgentTurn }) {
  const fix = turn.fix;
  if (!fix) return null;
  return (
    <div className="rounded-[18px] border border-indigo-400/40 bg-sapphire-600/10 px-5 py-4">
      <div className="flex items-center gap-2 text-[12px] uppercase tracking-wider text-lavender-200">
        <Bolt className="h-4 w-4" /> {fix.pr_url ? "Fix in review" : "Fix prepared"}
      </div>
      <p className="mt-1 text-[14px] text-text-100">{fix.root_cause}</p>
      <p className="mt-1 text-[13px] text-text-300">
        {fix.pr_url ? "Our engineers have the fix; automated tests are verifying it now." : "Our engineers have the fix and will release it shortly."}
      </p>
    </div>
  );
}

export function SupportChat() {
  const { repoId } = useParams<{ repoId: string }>();
  const router = useRouter();
  const token = useSessionToken();
  useEffect(() => {
    if (token === "") router.replace(`/login?next=/support/${repoId}`);
  }, [token, repoId, router]);
  const repo = usePoll(() => api.repo(repoId), repoId, 30_000);
  const [person, setPerson] = useState(DEMO_PEOPLE[0]);
  const [custom, setCustom] = useState({ name: "", ref: "" });
  const isSlice = useMemo(() => /slice/i.test(repo.data?.full_name ?? "") || (repo.data?.api_operations ?? []).some((o) => o.operation_id === "create_order"), [repo.data]);
  const customer = isSlice ? person : { ...custom, email: "" };
  const chat = useTicketChat(repoId, customer);
  const [text, setText] = useState("");
  const bottom = useRef<HTMLDivElement>(null);
  useEffect(() => {
    bottom.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [chat.turns]);
  const business = repo.data?.settings.business_name || repo.data?.full_name.split("/").pop() || "Support";

  const submit = (e: FormEvent) => {
    e.preventDefault();
    chat.send(text);
    setText("");
  };

  return (
    <div className="relative flex min-h-dvh flex-col bg-[radial-gradient(120%_90%_at_0%_0%,#0b1240_0%,#060a2b_55%)]">
      <header className="mx-auto flex w-full max-w-[1100px] items-center justify-between gap-3 px-4 py-4 sm:px-8">
        <Link href="/" aria-label="Supfeel home" className="scale-90 sm:scale-100">
          <Logo />
        </Link>
        <div className="flex items-center gap-2">
          {chat.ticketId ? (
            <Link href={`/app/tickets/${chat.ticketId}`} target="_blank" className="hidden rounded-full border border-line px-3 py-1.5 font-mono text-[12px] text-text-300 hover:text-text-100 sm:block">
              {chat.ticketId} ↗
            </Link>
          ) : null}
          <button onClick={chat.reset} className="flex items-center gap-1.5 rounded-full border border-line px-3 py-1.5 text-[13px] text-lavender-200 hover:border-lavender-300/60">
            <Refresh /> New ticket
          </button>
        </div>
      </header>

      <div className="mx-auto grid w-full max-w-[1100px] flex-1 gap-5 px-4 pb-6 sm:px-8 lg:grid-cols-[260px_1fr]">
        <aside className="space-y-4">
          <div className="rounded-[20px] border border-indigo-400/40 bg-sapphire-600/10 p-4 text-[13px] text-text-300">
            <div className="mb-1 text-[12px] uppercase tracking-wider text-lavender-200">Playground</div>
            In production your own support agent sends these escalations over MCP (
            <Link href={`/app/repos/${repoId}`} className="text-lavender-200 hover:text-white">
              Connect tab
            </Link>
            ). Here you play the customer. Each ticket uses credit like a real one.
          </div>
          <div className="glass rounded-[20px] p-4">
            <div className="text-[12px] uppercase tracking-wider text-text-300">Support for</div>
            <div className="mt-1 text-[18px] font-semibold">{business}</div>
            <p className="mt-1 text-[13px] text-text-300">Answers come from {business}&apos;s own code and docs. Bugs go straight to engineering with a fix.</p>
          </div>
          <div className="glass rounded-[20px] p-4">
            <div className="mb-2 text-[12px] uppercase tracking-wider text-text-300">You are</div>
            {isSlice ? (
              <div className="space-y-1.5">
                {DEMO_PEOPLE.map((p) => (
                  <button
                    key={p.ref}
                    disabled={!!chat.ticketId}
                    onClick={() => setPerson(p)}
                    className={cx("w-full rounded-xl border px-3 py-2 text-left text-[14px] disabled:opacity-60", person.ref === p.ref ? "border-indigo-400 bg-sapphire-600/20" : "border-line")}
                  >
                    {p.name} <span className="font-mono text-[11px] text-text-300">{p.ref}</span>
                  </button>
                ))}
              </div>
            ) : (
              <div className="space-y-2">
                <input className="w-full rounded-xl border border-line bg-bg-0/60 px-3 py-2 text-[14px]" placeholder="Your name" value={custom.name} onChange={(e) => setCustom({ ...custom, name: e.target.value })} />
                <input className="w-full rounded-xl border border-line bg-bg-0/60 px-3 py-2 text-[14px]" placeholder="Account id (optional)" value={custom.ref} onChange={(e) => setCustom({ ...custom, ref: e.target.value })} />
              </div>
            )}
          </div>
        </aside>

        <section className="glass flex min-h-[70dvh] flex-col rounded-[24px]">
          <div className="scrollbar-thin flex-1 space-y-5 overflow-y-auto p-4 sm:p-6">
            {!chat.turns.length ? (
              <div className="flex flex-col items-center gap-4 py-10 text-center">
                <Gem size={64} />
                <h1 className="text-[24px] font-semibold">How can we help?</h1>
                <p className="max-w-md text-[14px] text-text-300">Describe what happened. Supfeel investigates, then explains, does it for you, or gets it fixed, and shows every step.</p>
                <div className="mt-2 grid w-full max-w-xl gap-2">
                  {(isSlice ? SLICE_PROMPTS : GENERIC_PROMPTS).map((p) => (
                    <button key={p} onClick={() => (isSlice ? chat.send(p) : setText(p))} className="rounded-2xl border border-line bg-panel-strong px-4 py-3 text-left text-[14px] text-lavender-200 hover:border-lavender-300/50">
                      {p}
                    </button>
                  ))}
                </div>
              </div>
            ) : null}
            {chat.turns.map((t) =>
              t.kind === "customer" ? (
                <UserBubble key={t.id}>{t.text}</UserBubble>
              ) : (
                <AssistantRow key={t.id}>
                  <StepTrail turn={t} ticketId={chat.ticketId} />
                  <ProposalCard turn={t} disabled={chat.busy} onDecide={(ok) => chat.confirm(t.id, ok)} />
                  {t.verified.map((v, i) => (
                    <VerifiedCard key={i} v={v} />
                  ))}
                  <FixCard turn={t} />
                  {t.text ? (
                    <div className="w-fit max-w-full rounded-[20px] border border-line bg-bubble px-5 py-3.5">
                      <Markdown text={t.text} className="text-[15px] text-text-100" />
                    </div>
                  ) : t.streaming ? (
                    <div className="typing flex w-fit gap-1 rounded-[20px] border border-line bg-bubble px-5 py-4">
                      <span className="h-2 w-2 rounded-full bg-lavender-200" />
                      <span className="h-2 w-2 rounded-full bg-lavender-200" />
                      <span className="h-2 w-2 rounded-full bg-lavender-200" />
                    </div>
                  ) : null}
                  {t.error ? <p className="text-[13px] text-danger">{t.error}</p> : null}
                </AssistantRow>
              ),
            )}
            <div ref={bottom} />
          </div>
          <form onSubmit={submit} className="flex items-center gap-2 border-t border-line p-3 sm:p-4">
            <input
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Type your message…"
              aria-label="Message"
              className="flex-1 rounded-full border border-line bg-bg-0/60 px-5 py-3 text-[15px] outline-none placeholder:text-text-300/60 focus:border-indigo-400"
            />
            <button type="submit" disabled={chat.busy || !text.trim()} aria-label="Send" className="btn-primary flex h-12 w-12 items-center justify-center rounded-full text-white disabled:opacity-50">
              {chat.busy ? <Spinner /> : <Send />}
            </button>
          </form>
        </section>
      </div>
    </div>
  );
}
