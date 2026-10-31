"use client";

import Link from "next/link";
import { useParams, useSearchParams } from "next/navigation";
import { type FormEvent, useEffect, useState } from "react";

import { ArrowRight, Refresh } from "@/components/ui/icons";
import { usePoll } from "@/lib/usePoll";
import { type AskAnswer, api, type Repo, type RepoDetail, type Trace } from "@/lib/workspace";

import { ConnectPanel } from "./ConnectPanel";
import { TraceView } from "./TraceView";
import { Badge, Button, Card, Empty, ErrorNote, Input, Markdown, Spinner, Stat, StatusBadge, Tabs, timeAgo, usd } from "./ui";
import { JobProgress, TicketList } from "./Workspace";

type Tab = "connect" | "overview" | "modules" | "ask" | "api" | "tickets" | "index" | "settings";

function Overview({ repo }: { repo: RepoDetail }) {
  const chunks = repo.stats.chunks ?? {};
  return (
    <div className="grid gap-5 lg:grid-cols-[1fr_320px]">
      <Card title="What this product is and how it works">
        {repo.overview ? <Markdown text={repo.overview} /> : <Empty>The overview appears when indexing finishes.</Empty>}
      </Card>
      <div className="space-y-3">
        <div className="grid grid-cols-2 gap-3">
          <Stat label="Files" value={repo.stats.files ?? "–"} />
          <Stat label="Chunks" value={Object.values(chunks).reduce((a, b) => a + b, 0) || "–"} />
          <Stat label="Modules" value={repo.stats.modules ?? "–"} />
          <Stat label="API actions" value={repo.stats.api_operations ?? 0} />
        </div>
        <Card title="Index">
          <div className="space-y-2 text-[13px] text-text-300">
            <div className="flex flex-wrap gap-1.5">
              {Object.entries(chunks).map(([k, v]) => (
                <Badge key={k}>
                  {k} {v}
                </Badge>
              ))}
            </div>
            <p>Embeddings: {repo.stats.embedding_model ?? "–"}</p>
            <p>Last index Claude cost: {usd(repo.stats.last_job_claude_usd)}</p>
            {repo.stats.skipped && Object.keys(repo.stats.skipped).length ? (
              <p>Skipped: {Object.entries(repo.stats.skipped).map(([k, v]) => `${k} ${v}`).join(", ")}</p>
            ) : null}
          </div>
        </Card>
      </div>
    </div>
  );
}

function Modules({ repo }: { repo: RepoDetail }) {
  const [open, setOpen] = useState<string | null>(repo.modules[0]?.key ?? null);
  if (!repo.modules.length) return <Empty>No modules yet.</Empty>;
  return (
    <div className="space-y-2">
      {repo.modules.map((m) => (
        <div key={m.key} className="rounded-2xl border border-line bg-panel">
          <button onClick={() => setOpen(open === m.key ? null : m.key)} className="flex w-full items-center justify-between gap-3 px-5 py-3.5 text-left">
            <span className="font-mono text-[14px] text-text-100">{m.key}</span>
            <Badge tone={m.generated_by === "llm" ? "info" : "neutral"}>{m.generated_by === "llm" ? "explained by Claude" : "outline"}</Badge>
          </button>
          {open === m.key ? (
            <div className="border-t border-line px-5 py-4">
              <Markdown text={m.body} />
            </div>
          ) : null}
        </div>
      ))}
    </div>
  );
}

function Ask({ repo }: { repo: RepoDetail }) {
  const [q, setQ] = useState("");
  const [busy, setBusy] = useState(false);
  const [ans, setAns] = useState<AskAnswer | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [trace, setTrace] = useState<Trace | null>(null);
  const submit = async (e: FormEvent) => {
    e.preventDefault();
    if (!q.trim()) return;
    setBusy(true);
    setError(null);
    setTrace(null);
    try {
      const a = await api.ask(repo.id, q);
      setAns(a);
      setTrace(await api.ticketTrace(a.trace_id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed");
    } finally {
      setBusy(false);
    }
  };
  return (
    <div className="space-y-5">
      <Card title="Ask the codebase">
        <form onSubmit={submit} className="flex flex-col gap-3 sm:flex-row">
          <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="e.g. How is the delivery fee calculated?" aria-label="Question" />
          <Button type="submit" disabled={busy}>
            {busy ? <Spinner /> : null} Ask
          </Button>
        </form>
        {error ? <div className="mt-3"><ErrorNote>{error}</ErrorNote></div> : null}
      </Card>
      {ans ? (
        <Card title={<span>Answer <Badge className="ml-2">{ans.brain === "llm" ? "Claude" : "search only"}</Badge></span>}>
          <Markdown text={ans.answer} />
          <div className="mt-4 space-y-2">
            {ans.sources.slice(0, 6).map((s) => (
              <details key={s.id} className="rounded-xl border border-line bg-bg-0/50 px-3 py-2">
                <summary className="cursor-pointer text-[13px] text-lavender-200">
                  <span className="font-mono">{s.cite}</span>
                  <span className="ml-2 text-text-300">
                    {s.kind} · score {s.score.toFixed(2)}
                    {ans.citations.includes(s.cite) ? " · cited" : ""}
                  </span>
                </summary>
                <pre className="scrollbar-thin mt-2 overflow-x-auto whitespace-pre-wrap font-mono text-[12px] text-text-300">{s.text}</pre>
              </details>
            ))}
          </div>
        </Card>
      ) : null}
      {trace ? (
        <Card title="Trace">
          <TraceView trace={trace} />
        </Card>
      ) : null}
    </div>
  );
}

function ApiOps({ repo }: { repo: RepoDetail }) {
  if (!repo.api_operations.length)
    return <Empty>No OpenAPI spec found. Add one to the repo or set a spec URL in Settings so Supfeel can act on customers&apos; behalf.</Empty>;
  return (
    <Card title="Actions Supfeel can take through your API">
      <ul className="divide-y divide-line/60">
        {repo.api_operations.map((o) => (
          <li key={o.operation_id} className="flex flex-col gap-1 py-2.5 sm:flex-row sm:items-center sm:gap-4">
            <Badge tone={o.method === "GET" ? "neutral" : "warning"} className="w-16 justify-center">
              {o.method}
            </Badge>
            <span className="font-mono text-[13px] text-text-100">{o.path}</span>
            <span className="flex-1 text-[13px] text-text-300">{o.summary}</span>
            <span className="font-mono text-[12px] text-text-300">{o.operation_id}</span>
          </li>
        ))}
      </ul>
      <p className="mt-3 text-[12px] text-text-300">Reads run automatically; writes always need the customer&apos;s confirmation, are scoped to their account and verified by reading back.</p>
    </Card>
  );
}

function IndexJobs({ repo }: { repo: RepoDetail }) {
  const jobs = usePoll(() => api.jobs(repo.id), repo.id, 3000, (d) => !!d?.some((j) => j.status === "running" || j.status === "queued"));
  const [sel, setSel] = useState<string | null>(null);
  const [trace, setTrace] = useState<Trace | null>(null);
  useEffect(() => {
    if (sel) api.jobTrace(sel).then(setTrace).catch(() => setTrace(null));
  }, [sel]);
  if (!jobs.data) return <Spinner />;
  return (
    <div className="space-y-5">
      <Card title="Index runs">
        <ul className="divide-y divide-line/60">
          {jobs.data.map((j) => (
            <li key={j.id}>
              <button onClick={() => setSel(j.id)} className="flex w-full flex-wrap items-center gap-3 py-2.5 text-left text-[13px] hover:bg-panel-strong/40">
                <span className="font-mono text-text-300">{j.id}</span>
                <Badge>{j.trigger}</Badge>
                <StatusBadge status={j.status} />
                <span className="text-text-300">
                  {typeof j.progress.changed === "number" ? `${j.progress.changed} changed · ${j.progress.chunks_embedded ?? 0} chunks embedded` : ""}
                </span>
                <span className="ml-auto text-text-300">{timeAgo(j.started_at)}</span>
              </button>
              {j.error ? <p className="pb-2 text-[12px] text-danger">{j.error}</p> : null}
            </li>
          ))}
        </ul>
        <p className="mt-3 text-[12px] text-text-300">Pushes to the default branch re-index automatically; only changed files are re-embedded.</p>
      </Card>
      {sel ? (
        <Card title={`Trace · ${sel}`}>
          <TraceView trace={trace} />
        </Card>
      ) : null}
    </div>
  );
}

function Settings({ repo, onSaved }: { repo: Repo; onSaved: () => void }) {
  const [form, setForm] = useState({
    business_name: repo.settings.business_name ?? "",
    api_base_url: repo.settings.api_base_url ?? "",
    api_spec_url: repo.settings.api_spec_url ?? "",
    api_token: "",
    auto_fix: repo.settings.auto_fix !== false,
  });
  const [msg, setMsg] = useState<string | null>(null);
  const save = async (e: FormEvent) => {
    e.preventDefault();
    setMsg(null);
    try {
      const body: Record<string, unknown> = { ...form };
      if (!form.api_token) delete body.api_token;
      await api.updateSettings(repo.id, body);
      setMsg("Saved. Re-index to pick up a new spec URL.");
      onSaved();
    } catch (err) {
      setMsg(err instanceof Error ? err.message : "Failed");
    }
  };
  const field = (key: keyof typeof form, label: string, hint: string, type = "text") => (
    <label className="block space-y-1.5">
      <span className="text-[13px] text-lavender-200">{label}</span>
      <Input type={type} value={String(form[key])} onChange={(e) => setForm({ ...form, [key]: e.target.value })} placeholder={hint} />
    </label>
  );
  return (
    <Card title="Settings">
      <form onSubmit={save} className="grid gap-4 md:grid-cols-2">
        {field("business_name", "Business name", "Shown to customers, e.g. Slice")}
        {field("api_base_url", "Business API base URL", "https://api.example.com")}
        {field("api_spec_url", "OpenAPI spec URL (optional)", "https://api.example.com/openapi.json")}
        {field("api_token", "Service token", repo.settings.api_token ? `current ${repo.settings.api_token}` : "Bearer token for the API", "password")}
        <label className="flex items-center gap-3 text-[14px] text-text-300 md:col-span-2">
          <input type="checkbox" checked={form.auto_fix} onChange={(e) => setForm({ ...form, auto_fix: e.target.checked })} className="h-4 w-4 accent-[var(--sapphire-500)]" />
          Open fix pull requests automatically for confirmed bugs
        </label>
        <div className="flex items-center gap-3 md:col-span-2">
          <Button type="submit">Save settings</Button>
          {msg ? <span className="text-[13px] text-text-300">{msg}</span> : null}
        </div>
      </form>
    </Card>
  );
}

export function RepoView() {
  const { id } = useParams<{ id: string }>();
  const initial = useSearchParams().get("tab") as Tab | null;
  const [tab, setTab] = useState<Tab>(initial ?? "overview");
  const repo = usePoll(() => api.repo(id), id, 2500, (d) => !d || d.status === "indexing" || d.status === "pending");
  const tickets = usePoll(() => api.tickets(id), id, 10_000);
  const [reindexing, setReindexing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (repo.error && !repo.data) return <ErrorNote>{repo.error}</ErrorNote>;
  if (!repo.data)
    return (
      <div className="space-y-4">
        <div className="skeleton h-12 w-1/2" />
        <div className="skeleton h-10" />
        <div className="skeleton h-80" />
      </div>
    );
  const r = repo.data;

  const reindex = async () => {
    setReindexing(true);
    setError(null);
    try {
      await api.reindex(r.id);
      await repo.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed");
    } finally {
      setReindexing(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0">
          <Link href="/app" className="text-[13px] text-text-300 hover:text-text-100">
            ← Workspace
          </Link>
          <h1 className="mt-1 flex flex-wrap items-center gap-3 text-[26px] font-semibold tracking-tight">
            <span className="truncate">{r.full_name}</span>
            <StatusBadge status={r.status} />
          </h1>
          <p className="mt-1 text-[13px] text-text-300">
            {r.default_branch}
            {r.head_sha ? ` @ ${r.head_sha.slice(0, 7)}` : ""} · indexed {timeAgo(r.indexed_at)}
            {r.html_url ? (
              <>
                {" · "}
                <a href={r.html_url} target="_blank" rel="noreferrer" className="text-lavender-200 hover:text-white">
                  GitHub
                </a>
              </>
            ) : null}
          </p>
          {r.error ? <p className="mt-2 text-[13px] text-danger">{r.error}</p> : null}
          <div className="max-w-md">
            <JobProgress repo={r} />
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="ghost" onClick={reindex} disabled={reindexing || r.status === "indexing"}>
            <Refresh /> Re-index
          </Button>
          <Link href={`/support/${r.id}`} className="btn-primary inline-flex items-center gap-2 rounded-full px-4 py-2 text-[14px] font-medium text-white">
            Playground <ArrowRight />
          </Link>
        </div>
      </div>
      {error ? <ErrorNote>{error}</ErrorNote> : null}

      <Tabs<Tab>
        value={tab}
        onChange={setTab}
        tabs={[
          { id: "overview", label: "Overview" },
          { id: "connect", label: "Connect (MCP)" },
          { id: "modules", label: `Modules${r.modules.length ? ` (${r.modules.length})` : ""}` },
          { id: "ask", label: "Ask" },
          { id: "api", label: `API actions${r.api_operations.length ? ` (${r.api_operations.length})` : ""}` },
          { id: "tickets", label: `Tickets${tickets.data?.length ? ` (${tickets.data.length})` : ""}` },
          { id: "index", label: "Index runs" },
          { id: "settings", label: "Settings" },
        ]}
      />

      <div key={tab} className="anim-fade-up">
      {tab === "overview" ? <Overview repo={r} /> : null}
      {tab === "connect" ? <ConnectPanel repo={r} /> : null}
      {tab === "modules" ? <Modules repo={r} /> : null}
      {tab === "ask" ? <Ask repo={r} /> : null}
      {tab === "api" ? <ApiOps repo={r} /> : null}
      {tab === "tickets" ? (
        <Card title="Tickets">
          <TicketList tickets={tickets.data ?? []} loading={!tickets.data} />
        </Card>
      ) : null}
      {tab === "index" ? <IndexJobs repo={r} /> : null}
      {tab === "settings" ? <Settings repo={r} onSaved={() => repo.refresh()} /> : null}
      </div>
    </div>
  );
}
