"use client";

import { Fragment, type ReactNode } from "react";

export function cx(...parts: (string | false | null | undefined)[]) {
  return parts.filter(Boolean).join(" ");
}

export function Card({ children, className, title, action }: { children: ReactNode; className?: string; title?: ReactNode; action?: ReactNode }) {
  return (
    <section className={cx("rounded-[20px] border border-line bg-panel p-5 backdrop-blur-md transition-colors sm:p-6", className)}>
      {title || action ? (
        <header className="mb-4 flex items-center justify-between gap-3">
          {title ? <h2 className="text-[15px] font-semibold tracking-wide text-lavender-200">{title}</h2> : <span />}
          {action}
        </header>
      ) : null}
      {children}
    </section>
  );
}

const TONES = {
  neutral: "border-line text-text-300",
  info: "border-indigo-400/40 bg-indigo-400/10 text-lavender-200",
  success: "border-success/40 bg-success/10 text-success",
  warning: "border-warning/40 bg-warning/10 text-warning",
  danger: "border-danger/40 bg-danger/10 text-danger",
} as const;
export type Tone = keyof typeof TONES;

export function Badge({ children, tone = "neutral", className }: { children: ReactNode; tone?: Tone; className?: string }) {
  return (
    <span className={cx("inline-flex items-center gap-1 whitespace-nowrap rounded-full border px-2.5 py-0.5 text-[12px] font-medium", TONES[tone], className)}>
      {children}
    </span>
  );
}

const STATUS: Record<string, [string, Tone]> = {
  pending: ["Pending", "neutral"],
  indexing: ["Indexing", "info"],
  ready: ["Ready", "success"],
  failed: ["Failed", "danger"],
  running: ["Running", "info"],
  queued: ["Queued", "neutral"],
  done: ["Done", "success"],
  open: ["Open", "neutral"],
  answered: ["Answered", "info"],
  awaiting_confirmation: ["Awaiting OK", "warning"],
  fix_in_review: ["Fix in review", "info"],
  fix_verified: ["Fix verified", "success"],
  fix_failed: ["Fix failed CI", "danger"],
  reported: ["Bug reported", "warning"],
  resolved: ["Resolved", "success"],
  escalated: ["Escalated", "warning"],
  success: ["CI passed", "success"],
  failure: ["CI failed", "danger"],
  none: ["No CI", "neutral"],
};

export function StatusBadge({ status }: { status: string }) {
  const [label, tone] = STATUS[status] ?? [status, "neutral"];
  return (
    <Badge tone={tone}>
      {tone === "info" ? <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-current" /> : null}
      {label}
    </Badge>
  );
}

const CATEGORY: Record<string, [string, Tone]> = {
  bug: ["Technical issue", "danger"],
  misunderstanding: ["Explanation", "info"],
  assisted_action: ["Assisted action", "warning"],
  feature_request: ["Feature request", "neutral"],
  other: ["Other", "neutral"],
};

export function CategoryBadge({ category }: { category: string | null }) {
  if (!category) return null;
  const [label, tone] = CATEGORY[category] ?? [category, "neutral"];
  return <Badge tone={tone}>{label}</Badge>;
}

export function Button({
  children,
  onClick,
  variant = "primary",
  disabled,
  type = "button",
  className,
}: {
  children: ReactNode;
  onClick?: () => void;
  variant?: "primary" | "ghost" | "danger";
  disabled?: boolean;
  type?: "button" | "submit";
  className?: string;
}) {
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={cx(
        "inline-flex items-center justify-center gap-2 rounded-full px-4 py-2 text-[14px] font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-50",
        variant === "primary" && "btn-primary text-white",
        variant === "ghost" && "border border-line text-lavender-200 hover:border-lavender-300/60",
        variant === "danger" && "border border-danger/40 text-danger hover:bg-danger/10",
        className,
      )}
    >
      {children}
    </button>
  );
}

export function Input(props: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      {...props}
      className={cx(
        "w-full rounded-xl border border-line bg-bg-0/60 px-3.5 py-2.5 text-[14px] text-text-100 outline-none placeholder:text-text-300/60 focus:border-indigo-400",
        props.className,
      )}
    />
  );
}

export function Tabs<T extends string>({ tabs, value, onChange }: { tabs: { id: T; label: ReactNode }[]; value: T; onChange: (t: T) => void }) {
  return (
    <div role="tablist" className="scrollbar-thin flex gap-1 overflow-x-auto rounded-full border border-line bg-panel-strong p-1">
      {tabs.map((t) => (
        <button
          key={t.id}
          role="tab"
          aria-selected={value === t.id}
          onClick={() => onChange(t.id)}
          className={cx(
            "whitespace-nowrap rounded-full px-4 py-1.5 text-[14px] transition-colors",
            value === t.id ? "bg-sapphire-600 text-white shadow-[0_6px_20px_-8px_rgba(47,63,224,0.9)]" : "text-text-300 hover:bg-panel hover:text-text-100",
          )}
        >
          {t.label}
        </button>
      ))}
    </div>
  );
}

export function Spinner({ className = "h-4 w-4" }: { className?: string }) {
  return <span className={cx("inline-block animate-spin rounded-full border-2 border-lavender-300/30 border-t-lavender-200", className)} aria-label="Loading" />;
}

export function Empty({ children }: { children: ReactNode }) {
  return <div className="rounded-2xl border border-dashed border-line px-5 py-8 text-center text-[14px] text-text-300">{children}</div>;
}

export function ErrorNote({ children }: { children: ReactNode }) {
  return <div className="rounded-xl border border-danger/40 bg-danger/10 px-4 py-3 text-[14px] text-danger">{children}</div>;
}

export function Stat({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="rounded-2xl border border-line bg-panel-strong px-4 py-3">
      <div className="text-[12px] uppercase tracking-wider text-text-300">{label}</div>
      <div className="mt-1 text-[20px] font-semibold text-text-100">{value}</div>
    </div>
  );
}

export function timeAgo(iso: string | null | undefined): string {
  if (!iso) return "never";
  const s = Math.max(0, (Date.now() - new Date(iso).getTime()) / 1000);
  if (s < 60) return "just now";
  if (s < 3600) return `${Math.floor(s / 60)}m ago`;
  if (s < 86400) return `${Math.floor(s / 3600)}h ago`;
  return `${Math.floor(s / 86400)}d ago`;
}

export function usd(n: number | undefined | null, digits = 4) {
  return `$${(n ?? 0).toFixed(digits)}`;
}

export function ms(n: number) {
  return n >= 1000 ? `${(n / 1000).toFixed(n >= 10000 ? 0 : 1)}s` : `${n}ms`;
}

// ------------------------------------------------------------------ markdown (safe subset, no HTML)

function inline(text: string): ReactNode[] {
  return text.split(/(\*\*[^*]+\*\*|`[^`]+`)/g).map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**") && part.length > 4)
      return (
        <strong key={i} className="font-semibold text-white">
          {part.slice(2, -2)}
        </strong>
      );
    if (part.startsWith("`") && part.endsWith("`") && part.length > 2)
      return (
        <code key={i} className="rounded-md bg-bg-0/70 px-1.5 py-0.5 font-mono text-[0.88em] text-lavender-200">
          {part.slice(1, -1)}
        </code>
      );
    return <Fragment key={i}>{part}</Fragment>;
  });
}

export function Markdown({ text, className }: { text: string; className?: string }) {
  const out: ReactNode[] = [];
  const lines = text.split("\n");
  let i = 0;
  while (i < lines.length) {
    const line = lines[i];
    if (line.startsWith("```")) {
      const code: string[] = [];
      i++;
      while (i < lines.length && !lines[i].startsWith("```")) code.push(lines[i++]);
      i++;
      out.push(
        <pre key={out.length} className="scrollbar-thin overflow-x-auto rounded-xl border border-line bg-bg-0/70 p-3 font-mono text-[12.5px] leading-relaxed text-lavender-200">
          {code.join("\n")}
        </pre>,
      );
      continue;
    }
    const h = line.match(/^(#{1,4})\s+(.*)$/);
    if (h) {
      const size = ["text-[20px]", "text-[17px]", "text-[15px]", "text-[14px]"][h[1].length - 1];
      out.push(
        <p key={out.length} className={cx(size, "pt-2 font-semibold text-text-100")}>
          {inline(h[2])}
        </p>,
      );
      i++;
      continue;
    }
    const bullet = /^\s*[-•*]\s+/;
    const numbered = /^\s*\d+[.)]\s+/;
    if (bullet.test(line) || numbered.test(line)) {
      const ordered = numbered.test(line);
      const items: string[] = [];
      while (i < lines.length && (ordered ? numbered : bullet).test(lines[i])) items.push(lines[i++].replace(ordered ? numbered : bullet, ""));
      const Tag = ordered ? "ol" : "ul";
      out.push(
        <Tag key={out.length} className={cx("space-y-1 pl-5 marker:text-lavender-300", ordered ? "list-decimal" : "list-disc")}>
          {items.map((it, k) => (
            <li key={k}>{inline(it)}</li>
          ))}
        </Tag>,
      );
      continue;
    }
    if (line.trim()) out.push(<p key={out.length}>{inline(line)}</p>);
    i++;
  }
  return <div className={cx("space-y-2 text-[14px] leading-relaxed text-text-300 [&_strong]:text-text-100", className)}>{out}</div>;
}
