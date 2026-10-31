"use client";

import { useState } from "react";

/* Categorical slots (validated with the dataviz validator against the panel surface #10164a, dark mode:
   CVD ΔE ≥ 8.4, normal-vision ΔE ≥ 19.3, all ≥ 3:1). Fixed order; color follows the category, never rank. */
export const CATEGORY_COLORS: Record<string, string> = {
  bug: "#3987e5",
  misunderstanding: "#d95926",
  assisted_action: "#199e70",
  feature_request: "#c98500",
  other: "#d55181",
};
export const CATEGORY_LABEL: Record<string, string> = {
  bug: "Technical issue",
  misunderstanding: "Explanation",
  assisted_action: "Assisted action",
  feature_request: "Feature request",
  other: "Other",
};
const ORDER = ["bug", "misunderstanding", "assisted_action", "feature_request", "other"];

/** Tickets per day: single series (no legend; the card title names it), 2px-gap bars with 4px rounded tops. */
export function DailyBars({ data }: { data: { date: string; count: number }[] }) {
  const [hover, setHover] = useState<number | null>(null);
  const max = Math.max(1, ...data.map((d) => d.count));
  const total = data.reduce((a, d) => a + d.count, 0);
  const fmt = (iso: string) => new Date(iso + "T00:00:00").toLocaleDateString(undefined, { month: "short", day: "numeric" });
  return (
    <figure aria-label={`Tickets per day, last ${data.length} days: ${total} total`}>
      <div className="relative flex h-36 items-end gap-[2px]" onMouseLeave={() => setHover(null)}>
        {/* recessive gridline at the max */}
        <div className="pointer-events-none absolute inset-x-0 top-0 border-t border-dashed border-line" />
        <span className="pointer-events-none absolute -top-2.5 right-0 bg-transparent text-[11px] text-text-300">{max}</span>
        {data.map((d, i) => (
          <div key={d.date} className="relative flex h-full flex-1 items-end" onMouseEnter={() => setHover(i)}>
            <div
              className="anim-grow-y w-full rounded-t-[4px]"
              style={{
                height: `${Math.max(d.count ? 4 : 1.5, (d.count / max) * 100)}%`,
                background: d.count ? "#3987e5" : "rgba(169,173,247,0.18)",
                opacity: hover === null || hover === i ? 1 : 0.55,
                animationDelay: `${i * 30}ms`,
              }}
            />
            {hover === i ? (
              <div className="pointer-events-none absolute bottom-full left-1/2 z-10 mb-2 -translate-x-1/2 whitespace-nowrap rounded-lg border border-line bg-bg-1 px-2.5 py-1.5 text-[12px] shadow-xl">
                <div className="text-text-300">{fmt(d.date)}</div>
                <div className="font-medium text-text-100">
                  {d.count} ticket{d.count === 1 ? "" : "s"}
                </div>
              </div>
            ) : null}
          </div>
        ))}
      </div>
      <figcaption className="mt-2 flex justify-between text-[11px] text-text-300">
        <span>{fmt(data[0]?.date ?? "")}</span>
        <span>today</span>
      </figcaption>
    </figure>
  );
}

/** Share of tickets by category: one stacked bar (2px surface gaps), legend + direct counts. */
export function CategoryBar({ counts }: { counts: Record<string, number> }) {
  const [hover, setHover] = useState<string | null>(null);
  const items = ORDER.filter((k) => counts[k]).map((k) => ({ k, n: counts[k] }));
  const total = items.reduce((a, b) => a + b.n, 0);
  if (!total) return <p className="text-[13px] text-text-300">No tickets in the last 30 days.</p>;
  return (
    <figure aria-label={`Tickets by category: ${items.map((i) => `${CATEGORY_LABEL[i.k]} ${i.n}`).join(", ")}`}>
      <div className="flex h-3.5 gap-[2px] overflow-hidden rounded-[4px]" onMouseLeave={() => setHover(null)}>
        {items.map(({ k, n }, i) => (
          <div
            key={k}
            onMouseEnter={() => setHover(k)}
            className="anim-grow-x h-full first:rounded-l-[4px] last:rounded-r-[4px]"
            style={{ width: `${(n / total) * 100}%`, background: CATEGORY_COLORS[k], opacity: hover && hover !== k ? 0.45 : 1, animationDelay: `${i * 90}ms` }}
            title={`${CATEGORY_LABEL[k]}: ${n}`}
          />
        ))}
      </div>
      <ul className="mt-4 grid grid-cols-2 gap-x-4 gap-y-2">
        {items.map(({ k, n }) => (
          <li
            key={k}
            onMouseEnter={() => setHover(k)}
            onMouseLeave={() => setHover(null)}
            className={`flex items-center gap-2 text-[13px] transition-opacity ${hover && hover !== k ? "opacity-50" : ""}`}
          >
            <span className="h-2.5 w-2.5 shrink-0 rounded-[3px]" style={{ background: CATEGORY_COLORS[k] }} />
            <span className="text-text-300">{CATEGORY_LABEL[k]}</span>
            <span className="ml-auto tabular-nums text-text-100">{n}</span>
          </li>
        ))}
      </ul>
    </figure>
  );
}

/** Progress ring for the onboarding checklist. */
export function Ring({ value, size = 64 }: { value: number; size?: number }) {
  const r = (size - 8) / 2;
  const c = 2 * Math.PI * r;
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} role="img" aria-label={`${Math.round(value * 100)}% complete`}>
      <circle cx={size / 2} cy={size / 2} r={r} stroke="rgba(169,173,247,0.18)" strokeWidth="6" fill="none" />
      <circle
        cx={size / 2}
        cy={size / 2}
        r={r}
        stroke="var(--indigo-400)"
        strokeWidth="6"
        fill="none"
        strokeLinecap="round"
        strokeDasharray={c}
        strokeDashoffset={c * (1 - value)}
        transform={`rotate(-90 ${size / 2} ${size / 2})`}
        style={{ transition: "stroke-dashoffset 0.9s cubic-bezier(0.2,0.7,0.2,1)" }}
      />
      <text x="50%" y="50%" dominantBaseline="central" textAnchor="middle" className="fill-text-100 text-[14px] font-semibold">
        {Math.round(value * 100)}%
      </text>
    </svg>
  );
}
