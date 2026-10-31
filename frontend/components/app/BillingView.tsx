"use client";

import { type FormEvent, useState } from "react";

import { CountUp } from "@/components/motion/CountUp";
import { usePoll } from "@/lib/usePoll";
import { api, type Billing } from "@/lib/workspace";

import { money } from "./Shell";
import { Badge, Button, Card, cx, Empty, ErrorNote, Input, Spinner, Stat, timeAgo } from "./ui";

const AMOUNTS = [1000, 2500, 5000, 10000];
const METRIC_LABEL: Record<string, string> = { ticket: "Tickets", fix: "Fix runs", ask: "Questions", index: "Index runs" };

function CardForm({ onSaved, submitLabel, amount }: { onSaved: (b: Billing) => void; submitLabel: string; amount?: number }) {
  const [card, setCard] = useState({ number: "", name: "" });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      onSaved(amount ? await api.topup(amount, card) : await api.saveCard(card));
      setCard({ number: "", name: "" });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Payment failed");
    } finally {
      setBusy(false);
    }
  };
  return (
    <form onSubmit={submit} className="space-y-3">
      <div className="grid gap-3 sm:grid-cols-[1.4fr_1fr]">
        <Input inputMode="numeric" placeholder="Card number (mock: 4242 4242 4242 4242)" value={card.number} onChange={(e) => setCard({ ...card, number: e.target.value })} aria-label="Card number" required />
        <Input placeholder="Name on card" value={card.name} onChange={(e) => setCard({ ...card, name: e.target.value })} aria-label="Name on card" />
      </div>
      {error ? <ErrorNote>{error}</ErrorNote> : null}
      <div className="flex flex-wrap items-center gap-3">
        <Button type="submit" disabled={busy}>
          {busy ? <Spinner /> : null} {submitLabel}
        </Button>
        <span className="text-[12px] text-text-300">Payments are simulated: no real card is charged. 4000 0000 0000 0002 is declined.</span>
      </div>
    </form>
  );
}

function TopUp({ b, onChange }: { b: Billing; onChange: (b: Billing) => void }) {
  const [amount, setAmount] = useState(2500);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const pay = async () => {
    setBusy(true);
    setError(null);
    try {
      onChange(await api.topup(amount));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Payment failed");
    } finally {
      setBusy(false);
    }
  };
  return (
    <Card title="Add credit">
      <div className="mb-4 flex flex-wrap gap-2">
        {AMOUNTS.map((a) => (
          <button
            key={a}
            onClick={() => setAmount(a)}
            className={cx("rounded-full border px-4 py-1.5 text-[14px]", amount === a ? "border-indigo-400 bg-sapphire-600/25 text-text-100" : "border-line text-text-300")}
          >
            {money(a)}
          </button>
        ))}
      </div>
      {b.payment_method ? (
        <div className="space-y-3">
          <p className="text-[14px] text-text-300">
            Pay with {b.payment_method.brand} •••• {b.payment_method.last4}
          </p>
          {error ? <ErrorNote>{error}</ErrorNote> : null}
          <Button onClick={pay} disabled={busy}>
            {busy ? <Spinner /> : null} Add {money(amount)}
          </Button>
        </div>
      ) : (
        <CardForm amount={amount} submitLabel={`Pay ${money(amount)}`} onSaved={onChange} />
      )}
    </Card>
  );
}

function Limits({ b, onChange }: { b: Billing; onChange: (b: Billing) => void }) {
  const [limit, setLimit] = useState(String(b.month.limit_cents / 100));
  const [auto, setAuto] = useState(b.auto_recharge);
  const [msg, setMsg] = useState<string | null>(null);
  const pct = b.month.limit_cents ? Math.min(100, (b.month.spent_cents / b.month.limit_cents) * 100) : 100;
  const save = async (e: FormEvent) => {
    e.preventDefault();
    setMsg(null);
    try {
      onChange(
        await api.billingSettings({
          monthly_limit_cents: Math.round(Number(limit) * 100),
          auto_recharge_enabled: auto.enabled,
          auto_recharge_threshold_cents: auto.threshold_cents,
          auto_recharge_amount_cents: auto.amount_cents,
        }),
      );
      setMsg("Saved");
    } catch (err) {
      setMsg(err instanceof Error ? err.message : "Failed");
    }
  };
  return (
    <Card title="Monthly spend limit">
      <div className="mb-1 flex justify-between text-[13px] text-text-300">
        <span>
          {money(b.month.spent_cents)} of {money(b.month.limit_cents)} this month
        </span>
        <span>resets {new Date(b.month.resets_at).toLocaleDateString(undefined, { month: "short", day: "numeric" })}</span>
      </div>
      <div className="mb-5 h-2 overflow-hidden rounded-full bg-bg-0/70">
        <div className={cx("anim-grow-x h-full rounded-full transition-[width] duration-700", pct >= 90 ? "bg-warning" : "bg-indigo-400")} style={{ width: `${pct}%` }} />
      </div>
      <form onSubmit={save} className="space-y-4">
        <label className="block space-y-1.5">
          <span className="text-[13px] text-lavender-200">Limit per calendar month (USD)</span>
          <Input type="number" min={0} step={1} value={limit} onChange={(e) => setLimit(e.target.value)} />
          <span className="text-[12px] text-text-300">When the limit is reached, MCP calls return a clear error until the 1st of next month.</span>
        </label>
        <div className="rounded-2xl border border-line bg-bg-0/40 p-4">
          <label className="flex items-center gap-3 text-[14px] font-medium text-text-100">
            <input type="checkbox" checked={auto.enabled} onChange={(e) => setAuto({ ...auto, enabled: e.target.checked })} className="h-4 w-4 accent-[var(--sapphire-500)]" />
            Auto-recharge
          </label>
          <div className="mt-3 flex flex-wrap items-center gap-2 text-[14px] text-text-300">
            <span className="whitespace-nowrap">Add $</span>
            <Input className="w-24 py-1.5" type="number" min={5} value={auto.amount_cents / 100} onChange={(e) => setAuto({ ...auto, amount_cents: Math.round(Number(e.target.value) * 100) })} aria-label="Recharge amount" />
            <span className="whitespace-nowrap">when the balance drops below $</span>
            <Input className="w-24 py-1.5" type="number" min={0} value={auto.threshold_cents / 100} onChange={(e) => setAuto({ ...auto, threshold_cents: Math.round(Number(e.target.value) * 100) })} aria-label="Recharge threshold" />
          </div>
        </div>
        {auto.enabled && !b.payment_method ? <p className="text-[12px] text-warning">Add a card to use auto-recharge.</p> : null}
        <div className="flex items-center gap-3">
          <Button type="submit" variant="ghost">
            Save
          </Button>
          {msg ? <span className="text-[13px] text-text-300">{msg}</span> : null}
        </div>
      </form>
    </Card>
  );
}

export function BillingView() {
  const billing = usePoll(() => api.billing(), "billing", 15_000);
  const [override, setOverride] = useState<Billing | null>(null);
  const b = override ?? billing.data;
  if (billing.error && !b) return <ErrorNote>{billing.error}</ErrorNote>;
  if (!b)
    return (
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {[0, 1, 2, 3].map((i) => (
          <div key={i} className="skeleton h-20" />
        ))}
      </div>
    );

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-[28px] font-semibold tracking-tight">Billing</h1>
        <p className="mt-1 text-[15px] text-text-300">Pay as you go: prepaid credit, charged per unit of work. No subscription.</p>
      </div>
      <div className="stagger grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Stat label="Credit balance" value={<CountUp value={b.balance_cents / 100} format={(n) => `$${n.toFixed(2)}`} />} />
        <Stat label="Spent this month" value={<CountUp value={b.month.spent_cents / 100} format={(n) => `$${n.toFixed(2)}`} />} />
        <Stat label="Monthly limit" value={money(b.month.limit_cents)} />
        <Stat label="Repositories" value={<CountUp value={b.repos} />} />
      </div>
      <div className="grid gap-5 lg:grid-cols-2">
        <TopUp b={b} onChange={setOverride} />
        <Limits b={b} onChange={setOverride} />
      </div>
      <div className="grid gap-5 lg:grid-cols-[1fr_1.2fr]">
        <Card title="Prices">
          <ul className="divide-y divide-line/60">
            {b.prices.map((p) => (
              <li key={p.metric} className="flex items-start justify-between gap-4 py-3">
                <div>
                  <div className="text-[14px] text-text-100">{METRIC_LABEL[p.metric] ?? p.metric}</div>
                  <div className="text-[12.5px] text-text-300">{p.description}</div>
                </div>
                <span className="whitespace-nowrap text-[14px] font-medium text-lavender-200">
                  {money(p.cents)} / {p.unit}
                </span>
              </li>
            ))}
          </ul>
          <p className="mt-3 text-[12px] text-text-300">Product overview, ticket status and listing tools are free. Fix runs that never reach the model are refunded.</p>
        </Card>
        <Card title="This month">
          {Object.keys(b.month.by_metric).length ? (
            <ul className="space-y-2">
              {Object.entries(b.month.by_metric).map(([m, v]) => (
                <li key={m} className="flex justify-between text-[14px]">
                  <span className="text-text-300">
                    {METRIC_LABEL[m] ?? m} × {v.quantity}
                  </span>
                  <span className="tabular-nums text-text-100">{money(v.cents)}</span>
                </li>
              ))}
            </ul>
          ) : (
            <Empty>No usage yet this month.</Empty>
          )}
          <p className="mt-4 text-[12px] text-text-300">Model cost behind this usage (Claude + embeddings): ${b.month.ai_cost_usd.toFixed(4)}</p>
        </Card>
      </div>
      <Card title="Statement">
        {b.statement?.length ? (
          <div className="scrollbar-thin overflow-x-auto">
            <table className="w-full min-w-[560px] text-left text-[13px]">
              <thead className="text-text-300">
                <tr>
                  <th className="py-2 font-normal">When</th>
                  <th className="py-2 font-normal">Type</th>
                  <th className="py-2 font-normal">Description</th>
                  <th className="py-2 text-right font-normal">Amount</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line/60">
                {b.statement.map((e) => (
                  <tr key={e.id}>
                    <td className="py-2 text-text-300">{timeAgo(e.created_at)}</td>
                    <td className="py-2">
                      <Badge tone={e.amount_cents > 0 ? "success" : "neutral"}>{e.kind}</Badge>
                    </td>
                    <td className="py-2 text-text-100">
                      {e.description}
                      {e.ref ? <span className="ml-2 font-mono text-[12px] text-text-300">{e.ref}</span> : null}
                    </td>
                    <td className={cx("py-2 text-right tabular-nums", e.amount_cents > 0 ? "text-success" : "text-text-100")}>
                      {e.amount_cents > 0 ? "+" : "−"}
                      {money(Math.abs(e.amount_cents))}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <Empty>No transactions yet.</Empty>
        )}
      </Card>
      {b.payment_method ? (
        <Card title="Payment method">
          <p className="mb-3 text-[14px] text-text-300">
            {b.payment_method.brand} •••• {b.payment_method.last4}
            {b.payment_method.name ? ` · ${b.payment_method.name}` : ""}
          </p>
          <CardForm submitLabel="Replace card" onSaved={setOverride} />
        </Card>
      ) : null}
    </div>
  );
}
