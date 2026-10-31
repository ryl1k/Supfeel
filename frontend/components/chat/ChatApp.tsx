"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";

import { Logo } from "@/components/brand/Gem";
import { ActionResults, ConfirmCard, RecommendationCard } from "@/components/chat/ActionCards";
import { ActionTrail } from "@/components/chat/ActionTrail";
import { AssistantAvatar, AssistantBubble, AssistantRow, UserBubble } from "@/components/chat/primitives";
import { RichText } from "@/components/chat/RichText";
import { Dots, Refresh, Send } from "@/components/ui/icons";
import { getDemoCustomers, resetDemo } from "@/lib/api";
import type { AssistantTurn, DemoCustomer } from "@/lib/types";
import { useChat } from "@/lib/useChat";

const PROMPTS: Record<string, string[]> = {
  cus_maya: ["I bought these sneakers, but they're uncomfortable. Can you help?", "How should I wash my knit sneakers?"],
  cus_jordan: ["My package still hasn't arrived. It's been two weeks.", "Can I just get a refund instead?"],
  cus_alex: ["Why was I charged twice for my last order?", "I see two pending charges for my socks order"],
  cus_sam: ["Please cancel my Velora Club membership.", "I didn't mean to renew my membership"],
  cus_lee: [
    "I'd like to return the shoes I bought last month.",
    "Please ship my new order to 12 Beacon St, Boston, MA 02108",
  ],
  cus_priya: ["The sole on my Court sneakers is coming apart.", "I want to talk to a real person"],
};

function Typing() {
  return (
    <span className="typing inline-flex gap-1 py-1" aria-label="Supfeel is typing">
      <span className="h-2 w-2 rounded-full bg-lavender-300" />
      <span className="h-2 w-2 rounded-full bg-lavender-300" />
      <span className="h-2 w-2 rounded-full bg-lavender-300" />
    </span>
  );
}

function AssistantTurnView({
  turn,
  busy,
  onConfirm,
}: {
  turn: AssistantTurn;
  busy: boolean;
  onConfirm: (approved: boolean) => void;
}) {
  return (
    <AssistantRow>
      <ActionTrail steps={turn.steps} streaming={turn.streaming} />
      {turn.done.length ? <ActionResults actions={turn.done} verified={turn.verified} /> : null}
      {turn.text || turn.streaming ? (
        <AssistantBubble>{turn.text ? <RichText text={turn.text} /> : <Typing />}</AssistantBubble>
      ) : null}
      {turn.recommendations ? (
        <RecommendationCard items={turn.recommendations.items} provider={turn.recommendations.provider} />
      ) : null}
      {turn.proposed.length && turn.outcome !== null ? (
        <ConfirmCard actions={turn.proposed} state={turn.confirmation} disabled={busy} onDecide={onConfirm} />
      ) : null}
      {turn.notices.length ? (
        <div className="text-[12px] text-text-300">Claude unavailable for a step; used offline reasoning.</div>
      ) : null}
      {turn.error ? (
        <div className="rounded-[14px] border border-danger/40 bg-danger/10 px-4 py-2.5 text-[14px] text-danger">
          {turn.error}
        </div>
      ) : null}
    </AssistantRow>
  );
}

function CustomerPicker({
  customers,
  selected,
  onSelect,
  onReset,
  resetting,
}: {
  customers: DemoCustomer[];
  selected: string | null;
  onSelect: (id: string) => void;
  onReset: () => void;
  resetting: boolean;
}) {
  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <span className="text-[13px] uppercase tracking-[0.18em] text-lavender-300">Demo customer</span>
        <button
          type="button"
          onClick={onReset}
          disabled={resetting}
          className="flex items-center gap-1.5 text-[13px] text-text-300 transition-colors hover:text-white disabled:opacity-50"
          title="Restore all demo orders, payments and memberships"
        >
          <Refresh className={`h-3.5 w-3.5 ${resetting ? "animate-spin" : ""}`} /> Reset data
        </button>
      </div>
      <div className="-mx-4 flex gap-2.5 overflow-x-auto px-4 pb-1 scrollbar-thin lg:mx-0 lg:flex-col lg:overflow-visible lg:px-0">
        {customers.map((c) => (
          <button
            key={c.id}
            type="button"
            onClick={() => onSelect(c.id)}
            className={`min-w-[220px] rounded-[16px] border px-4 py-3 text-left transition-colors lg:min-w-0 ${
              selected === c.id
                ? "border-sapphire-500 bg-sapphire-600/25"
                : "border-line bg-panel hover:border-lavender-300/40"
            }`}
          >
            <span className="flex items-center justify-between gap-2">
              <span className="text-[15px] font-medium">{c.name}</span>
              <span className="text-[11px] uppercase tracking-wider text-text-300">{c.tier}</span>
            </span>
            <span className="mt-0.5 block text-[13px] leading-snug text-text-300">{c.persona}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

export function ChatApp() {
  const [customers, setCustomers] = useState<DemoCustomer[]>([]);
  const [customerId, setCustomerId] = useState<string | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [resetting, setResetting] = useState(false);
  const [input, setInput] = useState("");
  const { turns, busy, send, confirm, reset } = useChat(customerId);
  const scroller = useRef<HTMLDivElement>(null);

  useEffect(() => {
    getDemoCustomers()
      .then((list) => {
        // Show personas in demo order (hero first); unknown ones go last.
        const order = Object.keys(PROMPTS);
        const rank = (id: string) => (order.includes(id) ? order.indexOf(id) : order.length);
        const sorted = [...list].sort((a, b) => rank(a.id) - rank(b.id));
        setCustomers(sorted);
        setCustomerId((cur) => cur ?? sorted[0]?.id ?? null);
      })
      .catch((e: Error) => setLoadError(e.message));
  }, []);

  useEffect(() => {
    scroller.current?.scrollTo({ top: scroller.current.scrollHeight, behavior: "smooth" });
  }, [turns]);

  const selectCustomer = (id: string) => {
    if (id === customerId) return;
    setCustomerId(id);
    reset();
  };

  const onReset = async () => {
    setResetting(true);
    try {
      await resetDemo();
      reset();
    } catch (e) {
      setLoadError(e instanceof Error ? e.message : "Reset failed");
    } finally {
      setResetting(false);
    }
  };

  const submit = (text: string) => {
    if (!text.trim() || busy) return;
    setInput("");
    void send(text);
  };

  const current = customers.find((c) => c.id === customerId);
  const suggestions = (customerId && PROMPTS[customerId]) || [];

  return (
    <div className="relative z-10 mx-auto flex h-dvh w-full max-w-[1320px] flex-col gap-5 px-4 py-4 sm:px-8 lg:flex-row lg:gap-8 lg:py-8">
      <aside className="flex shrink-0 flex-col gap-5 lg:w-[300px]">
        <Link href="/" aria-label="Back to home">
          <Logo />
        </Link>
        {loadError ? (
          <div className="rounded-[14px] border border-danger/40 bg-danger/10 px-4 py-3 text-[14px] text-danger">
            Backend unavailable: {loadError}
          </div>
        ) : (
          <CustomerPicker
            customers={customers}
            selected={customerId}
            onSelect={selectCustomer}
            onReset={onReset}
            resetting={resetting}
          />
        )}
        <p className="hidden text-[13px] leading-relaxed text-text-300 lg:block">
          Velora is a fictional store. Every action changes mock data only. Sensitive actions wait for your approval,
          and every change is verified against the database.
        </p>
      </aside>

      <section className="glass flex min-h-0 flex-1 flex-col rounded-[28px]">
        <header className="flex items-center gap-4 border-b border-line px-5 py-4 sm:px-8">
          <AssistantAvatar size={48} />
          <div className="flex-1">
            <div className="text-[20px] font-medium leading-tight">Supfeel</div>
            <div className="flex items-center gap-2 text-[14px] text-text-300">
              <span className="h-2.5 w-2.5 rounded-full bg-success" />
              {current ? `Online · helping ${current.name.split(" ")[0]}` : "Online"}
            </div>
          </div>
          <button
            type="button"
            onClick={reset}
            className="rounded-full p-2 text-lavender-200 transition-colors hover:bg-white/5"
            title="New conversation"
            aria-label="New conversation"
          >
            <Dots className="h-6 w-6" />
          </button>
        </header>

        <div ref={scroller} className="scrollbar-thin flex min-h-0 flex-1 flex-col gap-5 overflow-y-auto px-4 py-6 sm:px-7">
          {turns.length === 0 ? (
            <div className="m-auto max-w-[460px] text-center">
              <h2 className="text-[26px] font-light">
                How can I <span className="text-gradient italic">help</span>
                {current ? `, ${current.name.split(" ")[0]}` : ""}?
              </h2>
              <p className="mt-2 text-[15px] text-text-300">
                Describe the problem. I&apos;ll look into your account, fix it, and verify it worked.
              </p>
            </div>
          ) : null}
          {turns.map((t) =>
            t.kind === "user" ? (
              <div key={t.id} className="rise">
                <UserBubble>{t.text}</UserBubble>
              </div>
            ) : (
              <div key={t.id} className="rise">
                <AssistantTurnView turn={t} busy={busy} onConfirm={(ok) => void confirm(t.id, ok)} />
              </div>
            ),
          )}
        </div>

        <div className="px-4 pb-5 sm:px-7">
          {suggestions.length && !busy ? (
            <div className="scrollbar-thin -mx-1 mb-3 flex gap-2 overflow-x-auto px-1 pb-1">
              {suggestions.map((s) => (
                <button
                  key={s}
                  type="button"
                  onClick={() => submit(s)}
                  className="shrink-0 rounded-full border border-line bg-panel px-4 py-2 text-[13.5px] text-lavender-200 transition-colors hover:border-lavender-300/50"
                >
                  {s}
                </button>
              ))}
            </div>
          ) : null}
          <form
            onSubmit={(e) => {
              e.preventDefault();
              submit(input);
            }}
            className="flex items-center rounded-full border border-line py-2 pl-6 pr-2 focus-within:border-lavender-300/60"
          >
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask anything…"
              aria-label="Message"
              maxLength={2000}
              disabled={!customerId}
              className="flex-1 bg-transparent text-[16px] text-white placeholder:text-text-300 focus:outline-none"
            />
            <button
              type="submit"
              disabled={busy || !input.trim() || !customerId}
              aria-label="Send"
              className="flex h-11 w-11 items-center justify-center rounded-full bg-sapphire-500 text-white transition-opacity disabled:opacity-40"
            >
              <Send />
            </button>
          </form>
        </div>
      </section>
    </div>
  );
}
