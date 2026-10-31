"use client";

import Link from "next/link";
import { type FormEvent, type ReactNode, useState } from "react";

import { Gem } from "@/components/brand/Gem";
import { ArrowRight, Check } from "@/components/ui/icons";
import { API_URL } from "@/lib/api";
import { usePoll } from "@/lib/usePoll";
import { api, type ApiKey, type RepoDetail } from "@/lib/workspace";

import { Button, cx, ErrorNote, Input, Markdown, Spinner } from "./ui";

type StepId = "import" | "learn" | "api" | "connect" | "try";
const STEPS: { id: StepId; title: string; sub: string }[] = [
  { id: "import", title: "Import your repository", sub: "GitHub, through the Supfeel App" },
  { id: "learn", title: "Supfeel learns your product", sub: "code, docs, API, explanations" },
  { id: "api", title: "Connect your API", sub: "optional: act for customers" },
  { id: "connect", title: "Add Supfeel to your agent", sub: "one MCP key, one line of config" },
  { id: "try", title: "Send a first escalation", sub: "see it explain, act or fix" },
];

function Panel({ children, k }: { children: ReactNode; k: string }) {
  return (
    <div key={k} className="anim-fade-up glass rounded-[24px] p-6 sm:p-8">
      {children}
    </div>
  );
}

const PHASES = [
  ["download", "Downloading the repository"],
  ["embed", "Reading and embedding the code"],
  ["explain", "Writing explanations of every module"],
  ["done", "Ready"],
] as const;

function Learning({ repo }: { repo: RepoDetail }) {
  const phase = repo.status === "ready" ? "done" : (repo.job?.progress.phase ?? "download");
  const idx = PHASES.findIndex(([p]) => p === phase);
  const p = repo.job?.progress;
  return (
    <div className="space-y-5">
      <ol className="space-y-3">
        {PHASES.map(([id, label], i) => (
          <li key={id} className="flex items-center gap-3 text-[15px]">
            <span
              className={cx(
                "flex h-7 w-7 items-center justify-center rounded-full",
                i < idx || phase === "done" ? "anim-pop bg-success/20 text-success" : i === idx ? "bg-sapphire-600/30 text-lavender-200" : "border border-line text-text-300",
              )}
            >
              {i < idx || phase === "done" ? <Check className="h-3.5 w-3.5" /> : i === idx ? <Spinner className="h-3.5 w-3.5" /> : i + 1}
            </span>
            <span className={i <= idx ? "text-text-100" : "text-text-300"}>
              {label}
              {id === "embed" && i === idx && p?.chunks_total ? (
                <span className="ml-2 text-[13px] text-text-300">
                  {p.chunks_done ?? 0}/{p.chunks_total}
                </span>
              ) : null}
            </span>
          </li>
        ))}
      </ol>
      {repo.status === "failed" ? <ErrorNote>{repo.error}</ErrorNote> : null}
      {repo.status === "ready" ? (
        <div className="anim-fade-up rounded-2xl border border-line bg-bg-0/50 p-4">
          <div className="mb-2 flex flex-wrap gap-2 text-[12px] text-text-300">
            <span>{repo.stats.files} files</span>·<span>{repo.stats.modules} modules</span>·<span>{repo.stats.api_operations ?? 0} API actions</span>
          </div>
          <div className="max-h-48 overflow-hidden [mask-image:linear-gradient(to_bottom,black_60%,transparent)]">
            <Markdown text={repo.overview.split("\n").slice(0, 14).join("\n")} />
          </div>
        </div>
      ) : null}
    </div>
  );
}

export function Welcome() {
  const status = usePoll(() => api.githubStatus(), "gh-welcome", 60_000);
  const dash = usePoll(() => api.dashboard(), "dash-welcome", 4000);
  const [repoId, setRepoId] = useState<string | null>(null);
  const rid = repoId ?? dash.data?.onboarding.first_repo_id ?? null;
  const repo = usePoll(() => (rid ? api.repo(rid) : Promise.resolve(null)), rid ?? "none", 2000, (d) => !!rid && (!d || d.status !== "ready"));
  const [step, setStep] = useState<StepId | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [url, setUrl] = useState("");
  const [apiDraft, setApiDraft] = useState<{ base: string | null; token: string | null }>({ base: null, token: null });
  const [key, setKey] = useState<ApiKey | null>(null);
  const [copied, setCopied] = useState(false);

  // Derive the current step from progress unless the user picked one.
  const o = dash.data?.onboarding;
  const auto: StepId = !rid ? "import" : repo.data?.status !== "ready" ? "learn" : !o?.api_connected && !key ? "api" : !o?.key_created && !key ? "connect" : "try";
  const current = step ?? auto;
  const doneMap: Record<StepId, boolean> = {
    import: !!rid,
    learn: repo.data?.status === "ready",
    api: !!o?.api_connected,
    connect: !!o?.key_created || !!key,
    try: !!o?.first_ticket,
  };
  const demo = status.data?.demo;

  // Prefill the demo store's API for the Slice demo; anything the user types wins.
  const isDemo = !!demo && !!repo.data?.full_name.toLowerCase().includes("slice");
  const apiForm = {
    base: apiDraft.base ?? (isDemo ? `${API_URL}${demo!.api_base_url_path}` : ""),
    token: apiDraft.token ?? (isDemo ? demo!.api_token : ""),
  };
  const setApiForm = (v: { base: string; token: string }) => setApiDraft(v);

  const run = async (fn: () => Promise<void>) => {
    setBusy(true);
    setError(null);
    try {
      await fn();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setBusy(false);
    }
  };

  const importRepo = (body: { repo?: string; local_path?: string }) =>
    run(async () => {
      const res = await api.importRepo(body);
      setRepoId(res.id);
      setStep("learn"); // stay to show what Supfeel learned, even when indexing is instant
    });

  const saveApi = (e: FormEvent) => {
    e.preventDefault();
    run(async () => {
      await api.updateSettings(rid!, { api_base_url: apiForm.base, api_token: apiForm.token, ...(demo && apiForm.base.endsWith(demo.api_base_url_path) ? { business_name: demo.business_name } : {}) });
      await dash.refresh();
      setStep("connect");
    });
  };

  const createKey = () =>
    run(async () => {
      setKey(await api.createKey(rid!, "My support agent"));
      await dash.refresh();
    });

  const command = `claude mcp add --transport http supfeel ${API_URL}/mcp --header "Authorization: Bearer ${key?.key ?? "sf_live_…"}"`;

  return (
    <div className="mx-auto grid max-w-[1100px] gap-6 lg:grid-cols-[300px_1fr]">
      <aside className="anim-fade-up">
        <div className="mb-6 flex items-center gap-3">
          <span className="anim-float">
            <Gem size={44} />
          </span>
          <div>
            <h1 className="text-[22px] font-semibold">Set up Supfeel</h1>
            <p className="text-[13px] text-text-300">About five minutes</p>
          </div>
        </div>
        <ol className="relative space-y-1">
          <span className="absolute bottom-4 left-[15px] top-4 w-px bg-line" aria-hidden />
          {STEPS.map((s, i) => {
            const active = s.id === current;
            const done = doneMap[s.id];
            return (
              <li key={s.id} className="relative">
                <button
                  onClick={() => setStep(s.id)}
                  disabled={!rid && s.id !== "import"}
                  className={cx("flex w-full items-start gap-3 rounded-2xl px-1 py-2.5 text-left transition-colors disabled:opacity-50", active && "bg-panel-strong/70")}
                >
                  <span
                    className={cx(
                      "relative z-10 flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-[13px] font-semibold transition-colors",
                      done ? "anim-pop bg-success text-bg-0" : active ? "bg-sapphire-600 text-white shadow-[0_0_0_4px_rgba(67,83,240,0.25)]" : "border border-line bg-bg-0 text-text-300",
                    )}
                  >
                    {done ? <Check className="h-4 w-4" /> : i + 1}
                  </span>
                  <span>
                    <span className={cx("block text-[14.5px] font-medium", active ? "text-text-100" : "text-text-300")}>{s.title}</span>
                    <span className="block text-[12.5px] text-text-300">{s.sub}</span>
                  </span>
                </button>
              </li>
            );
          })}
        </ol>
        <Link href="/app" className="mt-6 inline-block text-[13px] text-text-300 hover:text-text-100">
          Skip to the board →
        </Link>
      </aside>

      <section>
        {error ? (
          <div className="mb-4">
            <ErrorNote>{error}</ErrorNote>
          </div>
        ) : null}

        {current === "import" ? (
          <Panel k="import">
            <h2 className="text-[22px] font-semibold">Which product should Supfeel support?</h2>
            <p className="mt-1 text-[14px] text-text-300">Supfeel reads the repository (code, docs, OpenAPI spec) to understand how your product really behaves.</p>
            <form
              className="mt-5 flex flex-col gap-3 sm:flex-row"
              onSubmit={(e) => {
                e.preventDefault();
                importRepo({ repo: url });
              }}
            >
              <Input value={url} onChange={(e) => setUrl(e.target.value)} placeholder="github.com/owner/repo" aria-label="Repository" />
              <Button type="submit" disabled={busy || !url.trim()}>
                {busy ? <Spinner /> : null} Import
              </Button>
            </form>
            <div className="mt-4 flex flex-wrap items-center gap-3 text-[13px] text-text-300">
              {status.data?.install_url ? (
                <a href={status.data.install_url} target="_blank" rel="noreferrer" className="text-lavender-200 hover:text-white">
                  Private repo? Install the Supfeel GitHub App first ↗
                </a>
              ) : null}
            </div>
            {demo ? (
              <div className="mt-6 rounded-2xl border border-indigo-400/40 bg-sapphire-600/10 p-4">
                <div className="text-[14px] font-medium text-text-100">No repo handy? Use the demo</div>
                <p className="mt-1 text-[13px] text-text-300">Slice is a small pizza-delivery API with two real bugs and an OpenAPI spec, made for trying Supfeel.</p>
                <Button variant="ghost" className="mt-3" disabled={busy} onClick={() => importRepo(demo.repo ? { repo: demo.repo } : { local_path: demo.local_path })}>
                  Import {demo.label}
                </Button>
              </div>
            ) : null}
          </Panel>
        ) : null}

        {current === "learn" && repo.data ? (
          <Panel k="learn">
            <h2 className="text-[22px] font-semibold">Learning {repo.data.full_name}</h2>
            <p className="mb-5 mt-1 text-[14px] text-text-300">Every later push re-indexes only what changed.</p>
            <Learning repo={repo.data} />
            {repo.data.status === "ready" ? (
              <Button className="mt-6" onClick={() => setStep("api")}>
                Continue <ArrowRight />
              </Button>
            ) : null}
          </Panel>
        ) : null}

        {current === "api" && rid ? (
          <Panel k="api">
            <h2 className="text-[22px] font-semibold">Let Supfeel act for your customers</h2>
            <p className="mt-1 text-[14px] text-text-300">
              {repo.data?.api_operations.length
                ? `Found ${repo.data.api_operations.length} API operations in your spec. Point Supfeel at the running API to use them; writes always need the customer's OK and are verified.`
                : "No OpenAPI spec was found, so Supfeel can explain and fix but not act. You can add a spec URL later in Settings."}
            </p>
            <form onSubmit={saveApi} className="mt-5 space-y-3">
              <Input value={apiForm.base} onChange={(e) => setApiForm({ ...apiForm, base: e.target.value })} placeholder="https://api.yourproduct.com" aria-label="API base URL" />
              <Input type="password" value={apiForm.token} onChange={(e) => setApiForm({ ...apiForm, token: e.target.value })} placeholder="Service token (Bearer)" aria-label="Service token" />
              <div className="flex gap-3">
                <Button type="submit" disabled={busy || !apiForm.base}>
                  Save and continue
                </Button>
                <Button variant="ghost" onClick={() => setStep("connect")}>
                  Skip for now
                </Button>
              </div>
            </form>
          </Panel>
        ) : null}

        {current === "connect" && rid ? (
          <Panel k="connect">
            <h2 className="text-[22px] font-semibold">Add Supfeel to your support agent</h2>
            <p className="mt-1 text-[14px] text-text-300">Your agent escalates over MCP when it can&apos;t solve a problem. Create a key, then add the server.</p>
            {!key ? (
              <Button className="mt-5" onClick={createKey} disabled={busy}>
                {busy ? <Spinner /> : null} Create MCP key
              </Button>
            ) : (
              <div className="anim-fade-up mt-5 space-y-4">
                <div className="rounded-xl border border-success/40 bg-success/5 p-3">
                  <div className="mb-1 text-[12px] uppercase tracking-wider text-success">Your key: copy it now, it won&apos;t be shown again</div>
                  <code className="block break-all font-mono text-[13px]">{key.key}</code>
                </div>
                <div>
                  <div className="mb-1.5 text-[13px] text-text-300">Claude Code (other clients are in the repo&apos;s Connect tab):</div>
                  <div className="relative">
                    <pre className="scrollbar-thin overflow-x-auto rounded-xl border border-line bg-bg-0/70 p-3 pr-20 font-mono text-[12.5px] text-lavender-200">{command}</pre>
                    <button
                      onClick={async () => {
                        try {
                          await navigator.clipboard.writeText(command);
                          setCopied(true);
                        } catch {
                          // selectable anyway
                        }
                      }}
                      className="absolute right-2 top-2 rounded-full border border-line px-3 py-1 text-[12px] text-lavender-200"
                    >
                      {copied ? "Copied" : "Copy"}
                    </button>
                  </div>
                </div>
                <Button onClick={() => setStep("try")}>
                  Continue <ArrowRight />
                </Button>
              </div>
            )}
          </Panel>
        ) : null}

        {current === "try" && rid ? (
          <Panel k="try">
            {o?.first_ticket ? (
              <div className="flex flex-col items-center py-6 text-center">
                <span className="anim-pop flex h-16 w-16 items-center justify-center rounded-full bg-success/20 text-success">
                  <Check className="h-8 w-8" />
                </span>
                <h2 className="mt-4 text-[24px] font-semibold">You&apos;re set up</h2>
                <p className="mt-1 max-w-md text-[14px] text-text-300">Supfeel handled its first ticket. Every escalation from now on shows up on your board, with its full trace.</p>
                <Link href="/app" className="btn-primary mt-6 inline-flex items-center gap-2 rounded-full px-6 py-3 text-[15px] font-medium text-white">
                  Go to the board <ArrowRight />
                </Link>
              </div>
            ) : (
              <>
                <h2 className="text-[22px] font-semibold">Send a first escalation</h2>
                <p className="mt-1 text-[14px] text-text-300">Ask your agent to escalate a customer problem to Supfeel, or play the customer in the playground. This page updates when the first ticket arrives.</p>
                <div className="mt-5 grid gap-3 sm:grid-cols-2">
                  <Link href={`/support/${rid}`} target="_blank" className="lift rounded-2xl border border-line bg-panel-strong p-4">
                    <div className="text-[15px] font-medium">Open the playground ↗</div>
                    <div className="mt-1 text-[13px] text-text-300">Try “Checkout says my address is invalid” or “please reorder my last order”.</div>
                  </Link>
                  <div className="rounded-2xl border border-line bg-panel-strong p-4">
                    <div className="text-[15px] font-medium">From your agent</div>
                    <div className="mt-1 text-[13px] text-text-300">
                      “A customer says checkout rejects their address. Escalate it to Supfeel.”
                    </div>
                  </div>
                </div>
                <div className="mt-5 flex items-center gap-2 text-[13px] text-text-300">
                  <Spinner className="h-3.5 w-3.5" /> Waiting for the first ticket…
                </div>
              </>
            )}
          </Panel>
        ) : null}
      </section>
    </div>
  );
}
