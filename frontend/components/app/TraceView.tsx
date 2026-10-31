"use client";

import { Fragment, useMemo, useState } from "react";

import type { Span, Trace } from "@/lib/workspace";

import { Badge, cx, Empty, ms, usd } from "./ui";

export const KIND_COLORS: Record<Span["kind"], string> = {
  run: "#a9adf7",
  step: "#4353f0",
  llm: "#9b7bff",
  embedding: "#38c6d9",
  retrieval: "#3ddc84",
  tool: "#f5b54a",
  http: "#8a90c8",
};
const KIND_LABEL: Record<string, string> = {
  run: "run",
  step: "step",
  llm: "Claude",
  embedding: "embedding",
  retrieval: "search",
  tool: "tool / API",
  http: "GitHub",
};

interface Node extends Span {
  depth: number;
  children: Node[];
  start: number;
  end: number;
}

function build(spans: Span[]) {
  const t0 = Math.min(...spans.map((s) => new Date(s.started_at).getTime()));
  const nodes = new Map<string, Node>();
  for (const s of spans) {
    const start = new Date(s.started_at).getTime() - t0;
    nodes.set(s.id, { ...s, depth: 0, children: [], start, end: start + s.duration_ms });
  }
  const roots: Node[] = [];
  for (const n of nodes.values()) {
    const parent = n.parent_id ? nodes.get(n.parent_id) : undefined;
    if (parent) parent.children.push(n);
    else roots.push(n);
  }
  const sort = (xs: Node[]) => xs.sort((a, b) => a.start - b.start);
  const flat: Node[] = [];
  const walk = (n: Node, depth: number) => {
    n.depth = depth;
    flat.push(n);
    sort(n.children).forEach((c) => walk(c, depth + 1));
  };
  sort(roots).forEach((r) => walk(r, 0));
  const total = Math.max(1, ...flat.map((n) => n.end));
  return { roots, flat, total };
}

function descendants(n: Node): Node[] {
  return n.children.flatMap((c) => [c, ...descendants(c)]);
}

function rollup(n: Node) {
  const all = [n, ...descendants(n)];
  const counts: Record<string, number> = {};
  for (const d of all.slice(1)) counts[d.kind] = (counts[d.kind] ?? 0) + 1;
  return { cost: all.reduce((a, d) => a + d.cost_usd, 0), counts, errors: all.filter((d) => d.status === "error").length };
}

function FlowGraph({ roots, onSelect, selected }: { roots: Node[]; onSelect: (id: string) => void; selected: string | null }) {
  return (
    <div className="space-y-4">
      {roots.map((run, ri) => {
        const steps = run.children.length ? run.children : [run];
        const r = rollup(run);
        return (
          <div key={run.id}>
            <div className="mb-2 flex flex-wrap items-center gap-2 text-[13px] text-text-300">
              <span className="font-medium text-lavender-200">
                {ri + 1}. {run.name}
              </span>
              <span>· {ms(run.duration_ms)}</span>
              <span>· {usd(r.cost)}</span>
              {r.errors ? <Badge tone="danger">{r.errors} error(s)</Badge> : null}
            </div>
            <div className="scrollbar-thin flex items-stretch gap-0 overflow-x-auto pb-2">
              {steps.map((s, i) => {
                const sr = rollup(s);
                return (
                  <Fragment key={s.id}>
                    {i > 0 ? (
                      <div className="flex shrink-0 items-center px-1" aria-hidden>
                        <svg width="28" height="12" viewBox="0 0 28 12">
                          <path d="M0 6h24m-5-5 5 5-5 5" fill="none" stroke="var(--lavender-300)" strokeOpacity=".6" strokeWidth="1.5" />
                        </svg>
                      </div>
                    ) : null}
                    <button
                      onClick={() => onSelect(s.id)}
                      className={cx(
                        "min-w-[150px] shrink-0 rounded-2xl border px-3.5 py-3 text-left transition-colors",
                        selected === s.id ? "border-indigo-400 bg-sapphire-600/20" : "border-line bg-panel-strong hover:border-lavender-300/50",
                        s.status === "error" && "border-danger/60",
                      )}
                    >
                      <div className="flex items-center gap-2">
                        <span className="h-2 w-2 rounded-full" style={{ background: KIND_COLORS[s.kind] }} />
                        <span className="text-[14px] font-semibold capitalize text-text-100">{s.name}</span>
                      </div>
                      <div className="mt-1 text-[12px] text-text-300">
                        {ms(s.duration_ms)}
                        {sr.cost > 0 ? ` · ${usd(sr.cost)}` : ""}
                      </div>
                      <div className="mt-2 flex flex-wrap gap-1">
                        {Object.entries(sr.counts).map(([k, v]) => (
                          <span key={k} className="rounded-full px-1.5 py-0.5 text-[11px]" style={{ background: `${KIND_COLORS[k as Span["kind"]]}22`, color: KIND_COLORS[k as Span["kind"]] }}>
                            {v} {KIND_LABEL[k] ?? k}
                          </span>
                        ))}
                      </div>
                    </button>
                  </Fragment>
                );
              })}
            </div>
          </div>
        );
      })}
    </div>
  );
}

function Attributes({ span }: { span: Node }) {
  const entries = Object.entries(span.attributes);
  return (
    <div className="rounded-xl border border-line bg-bg-0/60 p-3 text-[12.5px]">
      <div className="mb-2 flex flex-wrap items-center gap-2">
        <span className="font-semibold text-text-100">{span.name}</span>
        <Badge>{KIND_LABEL[span.kind] ?? span.kind}</Badge>
        <span className="text-text-300">
          {ms(span.duration_ms)} · {usd(span.cost_usd, 5)}
        </span>
        {span.status === "error" ? <Badge tone="danger">error</Badge> : null}
      </div>
      {entries.length ? (
        <dl className="grid gap-x-4 gap-y-1.5 sm:grid-cols-[160px_1fr]">
          {entries.map(([k, v]) => (
            <Fragment key={k}>
              <dt className="text-text-300">{k}</dt>
              <dd className="min-w-0 whitespace-pre-wrap break-words font-mono text-lavender-200">
                {typeof v === "string" ? v : JSON.stringify(v, null, 1)}
              </dd>
            </Fragment>
          ))}
        </dl>
      ) : (
        <p className="text-text-300">No attributes.</p>
      )}
    </div>
  );
}

export function TraceView({ trace }: { trace: Trace | null }) {
  const [selected, setSelected] = useState<string | null>(null);
  const [kinds, setKinds] = useState<Set<string>>(new Set());
  const built = useMemo(() => (trace && trace.spans.length ? build(trace.spans) : null), [trace]);
  if (!trace || !built) return <Empty>No trace recorded yet.</Empty>;
  const { roots, flat, total } = built;
  const sel = flat.find((n) => n.id === selected) ?? null;
  const visible = kinds.size ? flat.filter((n) => n.depth === 0 || kinds.has(n.kind)) : flat;
  const s = trace.summary;
  const toggle = (k: string) =>
    setKinds((prev) => {
      const next = new Set(prev);
      if (next.has(k)) next.delete(k);
      else next.add(k);
      return next;
    });

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap gap-2 text-[13px]">
        <Badge tone="info">{s.spans} spans</Badge>
        <Badge>{usd(s.cost_usd)}</Badge>
        <Badge>
          {(s.tokens.input_tokens ?? 0) + (s.tokens.cache_read_tokens ?? 0)} in / {s.tokens.output_tokens ?? 0} out tokens
        </Badge>
        {s.tokens.cache_read_tokens ? <Badge tone="success">{s.tokens.cache_read_tokens} cached</Badge> : null}
        {s.errors ? <Badge tone="danger">{s.errors} errors</Badge> : null}
      </div>

      <FlowGraph roots={roots} onSelect={setSelected} selected={selected} />

      <div>
        <div className="mb-2 flex flex-wrap items-center gap-1.5">
          <span className="mr-1 text-[12px] uppercase tracking-wider text-text-300">Filter</span>
          {Object.entries(s.by_kind)
            .filter(([k]) => k !== "run")
            .map(([k, v]) => (
              <button
                key={k}
                onClick={() => toggle(k)}
                className={cx("rounded-full border px-2.5 py-0.5 text-[12px]", kinds.has(k) ? "border-indigo-400 text-text-100" : "border-line text-text-300")}
              >
                <span className="mr-1 inline-block h-2 w-2 rounded-full" style={{ background: KIND_COLORS[k as Span["kind"]] }} />
                {KIND_LABEL[k] ?? k} {v.count}
              </button>
            ))}
        </div>
        <div className="scrollbar-thin max-h-[520px] overflow-auto rounded-2xl border border-line">
          {visible.map((n) => (
            <button
              key={n.id}
              onClick={() => setSelected(n.id === selected ? null : n.id)}
              className={cx("grid w-full grid-cols-[minmax(150px,38%)_1fr_64px] items-center gap-3 border-b border-line/50 px-3 py-1.5 text-left text-[12.5px] last:border-0 hover:bg-panel-strong", selected === n.id && "bg-panel-strong")}
            >
              <span className="flex min-w-0 items-center gap-1.5" style={{ paddingLeft: Math.min(n.depth, 6) * 12 }}>
                <span className="h-2 w-2 shrink-0 rounded-full" style={{ background: KIND_COLORS[n.kind] }} />
                <span className={cx("truncate", n.status === "error" ? "text-danger" : "text-text-100")}>{n.name}</span>
              </span>
              <span className="relative h-2.5 rounded-full bg-bg-0/60">
                <span
                  className="absolute top-0 h-2.5 rounded-full"
                  style={{
                    left: `${(n.start / total) * 100}%`,
                    width: `${Math.max(0.6, ((n.end - n.start) / total) * 100)}%`,
                    background: KIND_COLORS[n.kind],
                    opacity: n.depth === 0 ? 0.45 : 0.9,
                  }}
                />
              </span>
              <span className="text-right tabular-nums text-text-300">{ms(n.duration_ms)}</span>
            </button>
          ))}
        </div>
      </div>
      {sel ? <Attributes span={sel} /> : <p className="text-[13px] text-text-300">Select a span to see its inputs, outputs, tokens and cost.</p>}
    </div>
  );
}
