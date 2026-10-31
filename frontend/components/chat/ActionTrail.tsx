"use client";

import { useState } from "react";

import { Check, ChevronDown } from "@/components/ui/icons";
import type { StepEvent, StepName } from "@/lib/types";

const LABELS: Record<StepName, string> = {
  understand: "Understand",
  investigate: "Investigate",
  policy: "Policy",
  plan: "Plan",
  act: "Act",
  verify: "Verify",
  respond: "Respond",
};
const ORDER: StepName[] = ["understand", "investigate", "policy", "plan", "act", "verify"];

function Dot({ status }: { status?: "running" | "done" }) {
  if (status === "done")
    return (
      <span className="flex h-5 w-5 items-center justify-center rounded-full bg-sapphire-600 text-white">
        <Check className="h-3 w-3" />
      </span>
    );
  if (status === "running")
    return <span className="h-5 w-5 animate-spin rounded-full border-2 border-lavender-300/30 border-t-lavender-300" />;
  return <span className="h-5 w-5 rounded-full border border-line" />;
}

/** Compact, collapsible timeline of the agent's steps for one turn. */
export function ActionTrail({ steps, streaming }: { steps: Partial<Record<StepName, StepEvent>>; streaming: boolean }) {
  const [open, setOpen] = useState(false);
  const visible = ORDER.filter((s) => steps[s]);
  if (!visible.length) return null;
  const current = [...visible].reverse().find((s) => steps[s]?.status === "running") ?? visible[visible.length - 1];
  const offline = Object.values(steps).some((s) => s?.brain === "rules");

  return (
    <div className="w-full rounded-[16px] border border-line bg-panel-strong/60 text-[13px]">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center gap-3 px-4 py-2.5 text-left"
        aria-expanded={open}
      >
        <span className="flex items-center gap-1.5">
          {ORDER.map((s) => (
            <span
              key={s}
              title={LABELS[s]}
              className={`h-1.5 w-5 rounded-full ${
                steps[s]?.status === "done"
                  ? "bg-sapphire-500"
                  : steps[s]?.status === "running"
                    ? "bg-lavender-300 animate-pulse"
                    : "bg-line"
              }`}
            />
          ))}
        </span>
        <span className="flex-1 truncate text-text-300">
          {streaming ? `${LABELS[current]}: ${steps[current]?.detail ?? ""}` : `${visible.length} steps`}
          {offline ? " · offline reasoning" : ""}
        </span>
        <ChevronDown className={`h-4 w-4 text-lavender-200 transition-transform ${open ? "rotate-180" : ""}`} />
      </button>
      {open ? (
        <ol className="space-y-3 border-t border-line px-4 py-3">
          {visible.map((s) => {
            const st = steps[s]!;
            return (
              <li key={s} className="flex gap-3">
                <Dot status={st.status} />
                <div className="min-w-0 flex-1">
                  <div className="font-medium text-lavender-200">{LABELS[s]}</div>
                  {st.detail ? <div className="text-text-300">{st.detail}</div> : null}
                  {st.citations?.length ? (
                    <div className="mt-1 flex flex-wrap gap-1.5">
                      {st.citations.map((c) => (
                        <span key={c} className="rounded-full border border-line px-2 py-0.5 text-[12px] text-lavender-300">
                          {c}
                        </span>
                      ))}
                    </div>
                  ) : null}
                </div>
              </li>
            );
          })}
        </ol>
      ) : null}
    </div>
  );
}
