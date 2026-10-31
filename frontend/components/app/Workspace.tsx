"use client";

import Link from "next/link";
import { type FormEvent, useState } from "react";

import { ArrowRight } from "@/components/ui/icons";
import { usePoll } from "@/lib/usePoll";
import { api, type GithubStatus, type Repo, setAdminToken, useAdminTokenField } from "@/lib/workspace";

import { Badge, Button, Card, CategoryBadge, Empty, ErrorNote, Input, Spinner, StatusBadge, timeAgo } from "./ui";

export function JobProgress({ repo }: { repo: Repo }) {
  const job = repo.job;
  if (!job || (job.status !== "running" && job.status !== "queued")) return null;
  const p = job.progress;
  const pct = p.chunks_total ? Math.round(((p.chunks_done ?? 0) / p.chunks_total) * 100) : null;
  const phase = { download: "Downloading", embed: "Embedding code", explain: "Writing explanations" }[p.phase ?? ""] ?? "Starting";
  return (
    <div className="mt-3">
      <div className="mb-1 flex justify-between text-[12px] text-text-300">
        <span>{phase}…</span>
        {pct !== null && p.phase === "embed" ? <span>{pct}%</span> : null}
      </div>
      <div className="h-1.5 overflow-hidden rounded-full bg-bg-0/70">
        <div
          className="h-full rounded-full bg-indigo-400 transition-all"
          style={{ width: `${p.phase === "explain" ? 90 : p.phase === "embed" && pct !== null ? 20 + pct * 0.65 : 10}%` }}
        />
      </div>
    </div>
  );
}

function RepoCard({ repo }: { repo: Repo }) {
  const langs = Object.entries(repo.stats.languages ?? {}).slice(0, 4);
  return (
    <Link href={`/app/repos/${repo.id}`} className="group block rounded-[20px] border border-line bg-panel p-5 transition-colors hover:border-lavender-300/50">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="truncate text-[16px] font-semibold text-text-100">{repo.full_name}</div>
          <div className="mt-0.5 text-[12px] text-text-300">
            {repo.source === "github" ? "GitHub" : "Local"} · {repo.default_branch}
            {repo.head_sha ? ` @ ${repo.head_sha.slice(0, 7)}` : ""} · indexed {timeAgo(repo.indexed_at)}
          </div>
        </div>
        <StatusBadge status={repo.status} />
      </div>
      {repo.error ? <p className="mt-3 line-clamp-2 text-[13px] text-danger">{repo.error}</p> : null}
      <JobProgress repo={repo} />
      <div className="mt-4 flex flex-wrap gap-1.5">
        {repo.stats.files !== undefined ? <Badge>{repo.stats.files} files</Badge> : null}
        {repo.stats.modules ? <Badge>{repo.stats.modules} modules</Badge> : null}
        {repo.stats.api_operations ? <Badge tone="warning">{repo.stats.api_operations} API actions</Badge> : null}
        {langs.map(([l, n]) => (
          <Badge key={l}>
            {l} {n}
          </Badge>
        ))}
      </div>
      <div className="mt-4 flex items-center gap-1 text-[13px] text-lavender-200 opacity-80 group-hover:opacity-100">
        Open <ArrowRight />
      </div>
    </Link>
  );
}

function ImportCard({ status, onImported }: { status: GithubStatus | null; onImported: (id: string) => void }) {
  const [repo, setRepo] = useState("");
  const [local, setLocal] = useState("");
  const [token, setToken] = useAdminTokenField();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const needsToken = status ? !status.open_import : true;

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    if (needsToken) setAdminToken(token);
    try {
      const res = await api.importRepo(local ? { local_path: local } : { repo });
      setRepo("");
      setLocal("");
      onImported(res.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Import failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <Card title="Import a repository">
      <form onSubmit={submit} className="space-y-3">
        <Input placeholder="owner/repo or https://github.com/owner/repo" value={repo} onChange={(e) => setRepo(e.target.value)} aria-label="GitHub repository" />
        {status?.allow_local_repos ? (
          <Input placeholder="…or a local path (dev only)" value={local} onChange={(e) => setLocal(e.target.value)} aria-label="Local path" />
        ) : null}
        {needsToken ? (
          <Input type="password" placeholder="Admin token" value={token} onChange={(e) => setToken(e.target.value)} aria-label="Admin token" />
        ) : null}
        {error ? <ErrorNote>{error}</ErrorNote> : null}
        <div className="flex flex-wrap items-center gap-3">
          <Button type="submit" disabled={busy || (!repo.trim() && !local.trim())}>
            {busy ? <Spinner /> : null} Import and index
          </Button>
          <span className="text-[12px] text-text-300">We index code, docs and API specs, then explain every module.</span>
        </div>
      </form>
    </Card>
  );
}

function GithubCard({ status }: { status: GithubStatus | null }) {
  if (!status) return <Card title="GitHub">{<Spinner />}</Card>;
  const label = { app: "GitHub App connected", token: "Personal token", anonymous: "Public repos only" }[status.auth];
  return (
    <Card title="GitHub">
      <div className="space-y-3 text-[14px] text-text-300">
        <div className="flex flex-wrap gap-2">
          <Badge tone={status.auth === "anonymous" ? "warning" : "success"}>{label}</Badge>
          <Badge tone={status.webhook_configured ? "success" : "neutral"}>{status.webhook_configured ? "Push webhooks on" : "No webhook secret"}</Badge>
        </div>
        <p>
          {status.auth === "app"
            ? "Supfeel reads code, opens fix pull requests, follows CI and re-indexes on every push to the default branch."
            : "Connect the GitHub App so Supfeel can open fix pull requests and re-index on push."}
        </p>
        {status.install_url ? (
          <a href={status.install_url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-lavender-200 hover:text-white">
            Install on a repository <ArrowRight />
          </a>
        ) : null}
      </div>
    </Card>
  );
}

export function Workspace() {
  const status = usePoll(() => api.githubStatus(), "", 60_000);
  const repos = usePoll(() => api.repos(), "", 2500, (d) => !!d?.some((r) => r.status === "indexing" || r.status === "pending"));
  const tickets = usePoll(() => api.tickets(), "", 10_000);

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-[28px] font-semibold tracking-tight sm:text-[34px]">
            Your <span className="text-gradient">support workspace</span>
          </h1>
          <p className="mt-1 max-w-2xl text-[15px] text-text-300">
            Import a product&apos;s repository. Supfeel learns it, then resolves tickets: it explains, acts through your API, or ships a verified fix.
          </p>
        </div>
      </div>

      <div className="grid gap-5 lg:grid-cols-[1.4fr_1fr]">
        <ImportCard status={status.data} onImported={() => repos.refresh()} />
        <GithubCard status={status.data} />
      </div>

      <section>
        <h2 className="mb-3 text-[15px] font-semibold text-lavender-200">Repositories</h2>
        {repos.error ? <ErrorNote>Can&apos;t reach the Supfeel API: {repos.error}</ErrorNote> : null}
        {!repos.data ? (
          <Spinner />
        ) : repos.data.length ? (
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {repos.data.map((r) => (
              <RepoCard key={r.id} repo={r} />
            ))}
          </div>
        ) : (
          <Empty>No repositories yet. Import one above, e.g. the Slice demo store.</Empty>
        )}
      </section>

      <Card
        title="Recent tickets"
        action={
          <Link href="/app/tickets" className="text-[13px] text-lavender-200 hover:text-white">
            All tickets
          </Link>
        }
      >
        <TicketList tickets={(tickets.data ?? []).slice(0, 8)} loading={!tickets.data} />
      </Card>
    </div>
  );
}

export function TicketList({ tickets, loading }: { tickets: import("@/lib/workspace").TicketSummary[]; loading?: boolean }) {
  if (loading) return <Spinner />;
  if (!tickets.length) return <Empty>No tickets yet. Open the support page of a repository to send one.</Empty>;
  return (
    <ul className="divide-y divide-line/60">
      {tickets.map((t) => (
        <li key={t.id}>
          <Link href={`/app/tickets/${t.id}`} className="flex flex-col gap-1.5 py-3 hover:bg-panel-strong/40 sm:flex-row sm:items-center sm:gap-4">
            <span className="w-24 shrink-0 font-mono text-[12px] text-text-300">{t.id}</span>
            <span className="min-w-0 flex-1 truncate text-[14px] text-text-100">{t.subject || "(no subject yet)"}</span>
            <span className="flex flex-wrap items-center gap-1.5">
              <CategoryBadge category={t.category} />
              <StatusBadge status={t.status} />
              {t.learned ? <Badge tone="success">learned</Badge> : null}
              <span className="w-16 text-right text-[12px] text-text-300">{timeAgo(t.created_at)}</span>
            </span>
          </Link>
        </li>
      ))}
    </ul>
  );
}
