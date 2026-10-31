"use client";

import { useState } from "react";

import { InfoCard } from "@/components/chat/primitives";
import { Check, Cross, Shield } from "@/components/ui/icons";
import type { AgentAction, Check as CheckT, Recommendation } from "@/lib/types";

export function ConfirmCard({
  actions,
  state,
  disabled,
  onDecide,
}: {
  actions: AgentAction[];
  state: "pending" | "approved" | "declined" | null;
  disabled: boolean;
  onDecide: (approved: boolean) => void;
}) {
  return (
    <div className="w-full rounded-[18px] border border-warning/40 bg-panel-strong p-4">
      <div className="mb-3 flex items-center gap-2 text-[13px] font-medium uppercase tracking-wider text-warning">
        <Shield className="h-4 w-4" /> Needs your OK
      </div>
      <ul className="space-y-2.5">
        {actions.map((a) => (
          <li key={a.action_id} className="rounded-[12px] border border-line px-3.5 py-2.5">
            <div className="text-[15px] font-medium">{a.title}</div>
            <div className="text-[13.5px] leading-snug text-text-300">{a.description}</div>
          </li>
        ))}
      </ul>
      {state === "pending" ? (
        <div className="mt-4 flex gap-2.5">
          <button
            type="button"
            disabled={disabled}
            onClick={() => onDecide(true)}
            className="btn-primary flex items-center gap-2 rounded-full px-5 py-2 text-[14px] font-medium disabled:opacity-50"
          >
            <Check /> Approve
          </button>
          <button
            type="button"
            disabled={disabled}
            onClick={() => onDecide(false)}
            className="flex items-center gap-2 rounded-full border border-line px-5 py-2 text-[14px] text-text-300 transition-colors hover:text-white disabled:opacity-50"
          >
            <Cross /> Decline
          </button>
        </div>
      ) : state ? (
        <div className={`mt-3 text-[13px] ${state === "approved" ? "text-success" : "text-text-300"}`}>
          {state === "approved" ? "Approved" : "Declined: nothing was changed"}
        </div>
      ) : (
        <div className="mt-3 text-[13px] text-text-300">Superseded by your next message</div>
      )}
    </div>
  );
}

function Checks({ checks }: { checks: CheckT[] }) {
  return (
    <ul className="mt-2 space-y-1">
      {checks.map((c) => (
        <li key={c.label} className="flex items-center gap-2 text-[12.5px] text-text-300">
          <span className={c.ok ? "text-success" : "text-danger"}>{c.ok ? <Check className="h-3.5 w-3.5" /> : <Cross className="h-3.5 w-3.5" />}</span>
          {c.label}
          {c.detail ? <span className="truncate text-text-300/70">· {c.detail}</span> : null}
        </li>
      ))}
    </ul>
  );
}

export function ActionResults({
  actions,
  verified,
}: {
  actions: AgentAction[];
  verified: Record<string, { ok: boolean; checks: CheckT[] }>;
}) {
  if (!actions.length) return null;
  return (
    <div className="grid w-full gap-2">
      {actions.map((a) => {
        const v = verified[a.action_id] ?? a.verification;
        const failed = a.status === "failed";
        return (
          <div key={a.action_id} className="rise rounded-[16px] border border-line bg-panel-strong px-4 py-3">
            <div className="flex items-center gap-3">
              <span className="flex-1 text-[14.5px] font-medium">{a.title}</span>
              {failed ? (
                <span className="rounded-full bg-danger/15 px-2.5 py-0.5 text-[12px] text-danger">Failed</span>
              ) : v ? (
                <span
                  className={`flex items-center gap-1 rounded-full px-2.5 py-0.5 text-[12px] ${
                    v.ok ? "bg-success/15 text-success" : "bg-danger/15 text-danger"
                  }`}
                >
                  {v.ok ? <Check className="h-3 w-3" /> : <Cross className="h-3 w-3" />}
                  {v.ok ? "Verified" : "Check failed"}
                </span>
              ) : (
                <span className="rounded-full bg-sapphire-600/30 px-2.5 py-0.5 text-[12px] text-lavender-200">Done</span>
              )}
            </div>
            {failed && a.error ? <div className="mt-1 text-[12.5px] text-text-300">{a.error.message}</div> : null}
            {v ? <Checks checks={v.checks} /> : null}
          </div>
        );
      })}
    </div>
  );
}

export function RecommendationCard({ items, provider }: { items: Recommendation[]; provider: string }) {
  const [open, setOpen] = useState(false);
  if (!items.length) return null;
  return (
    <div className="w-full">
      <InfoCard
        title="Personalized recommendations"
        subtitle={provider === "qloo" ? "powered by Qloo" : "matched to your style and fit"}
        onClick={() => setOpen((o) => !o)}
      />
      {open ? (
        <ul className="rise mt-2 grid gap-2">
          {items.map((r, i) => (
            <li key={r.sku} className="flex items-center gap-3 rounded-[14px] border border-line bg-panel-strong px-4 py-3">
              <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-line text-[13px] text-lavender-300">
                {i + 1}
              </span>
              <span className="min-w-0 flex-1">
                <span className="block text-[14.5px] font-medium">
                  {r.name} · {r.color}
                </span>
                <span className="block text-[12.5px] text-text-300">
                  Size {r.size} {r.width === "2E" ? "Wide (2E)" : "Standard"} · {r.reason}
                </span>
              </span>
              <span className="text-[14px] text-lavender-200">{r.price}</span>
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}
