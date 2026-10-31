"use client";

import { type FormEvent, useState } from "react";

import { API_URL } from "@/lib/api";
import { usePoll } from "@/lib/usePoll";
import { api, type ApiKey, type RepoDetail } from "@/lib/workspace";

import { Badge, Button, Card, cx, Empty, ErrorNote, Input, Spinner, Tabs, timeAgo } from "./ui";

const TOOLS: [string, string, string][] = [
  ["escalate", "Hand over a customer's problem with the conversation so far. Returns what to tell the customer.", "$0.15 + $1.00 per fix run"],
  ["reply", "Send the customer's next message on a ticket.", "included"],
  ["confirm", "Pass on the customer's yes/no for a proposed action (marked destructive).", "included"],
  ["get_ticket", "Status, next step, PR and CI state (for long fixes).", "free"],
  ["ask_product", "Quick, cited answer about how the product works.", "$0.02"],
  ["get_product_overview", "What the product is, its modules and the actions available.", "free"],
  ["list_tickets", "Recent tickets for this product.", "free"],
];

type Client = "claude-code" | "cursor" | "desktop" | "python";

function snippet(client: Client, url: string, key: string) {
  switch (client) {
    case "claude-code":
      return `claude mcp add --transport http supfeel ${url} \\\n  --header "Authorization: Bearer ${key}"`;
    case "cursor":
      return JSON.stringify({ mcpServers: { supfeel: { url, headers: { Authorization: `Bearer ${key}` } } } }, null, 2);
    case "desktop":
      return JSON.stringify(
        { mcpServers: { supfeel: { command: "npx", args: ["-y", "mcp-remote", url, "--header", `Authorization:Bearer ${key}`] } } },
        null,
        2,
      );
    case "python":
      return `import httpx2
from mcp import Client
from mcp.client.streamable_http import streamable_http_client

http = httpx2.AsyncClient(headers={"Authorization": "Bearer ${key}"}, timeout=180)
async with Client(streamable_http_client("${url}", http_client=http)) as supfeel:
    result = await supfeel.call_tool("escalate", {
        "message": customer_message,
        "conversation": transcript,          # [{"role": "customer" | "assistant", "content": ...}]
        "attempted": "what your bot already tried",
        "customer": {"name": name, "ref": customer_id},
    })
    # send result.structured_content["customer_reply"] to the customer`;
  }
}

const HINT: Record<Client, string> = {
  "claude-code": "Run in a terminal. Your Claude Code agent can then escalate customer issues to Supfeel.",
  cursor: "Add to .cursor/mcp.json (project) or ~/.cursor/mcp.json.",
  desktop: "Add to claude_desktop_config.json (uses the mcp-remote bridge).",
  python: "Your own support bot, with the official MCP Python SDK.",
};

function Copy({ text }: { text: string }) {
  const [done, setDone] = useState(false);
  return (
    <button
      onClick={async () => {
        try {
          await navigator.clipboard.writeText(text);
          setDone(true);
          setTimeout(() => setDone(false), 1500);
        } catch {
          // clipboard blocked: the text is selectable
        }
      }}
      className="rounded-full border border-line px-3 py-1 text-[12px] text-lavender-200 hover:border-lavender-300/60"
    >
      {done ? "Copied" : "Copy"}
    </button>
  );
}

export function ConnectPanel({ repo }: { repo: RepoDetail }) {
  const url = `${API_URL}/mcp`;
  const keys = usePoll(() => api.keys(repo.id), repo.id, 30_000);
  const [created, setCreated] = useState<ApiKey | null>(null);
  const [name, setName] = useState("Support bot");
  const [client, setClient] = useState<Client>("claude-code");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const key = created?.key ?? "sf_live_…your-key…";

  const create = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      setCreated(await api.createKey(repo.id, name));
      await keys.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed");
    } finally {
      setBusy(false);
    }
  };
  const revoke = async (id: string) => {
    await api.revokeKey(id);
    if (created?.id === id) setCreated(null);
    await keys.refresh();
  };

  return (
    <div className="space-y-5">
      <Card title="Connect your support agent over MCP">
        <p className="max-w-3xl text-[14px] text-text-300">
          Supfeel works behind your first-line support agent. When it can&apos;t solve a problem, it calls <code className="text-lavender-200">escalate</code>: Supfeel reads this
          repository&apos;s code, then explains, acts through your API after the customer confirms, or fixes the bug with a pull request, and hands back the reply to send.
        </p>
        <div className="mt-4 flex flex-wrap items-center gap-2 rounded-xl border border-line bg-bg-0/60 px-3 py-2">
          <span className="text-[12px] uppercase tracking-wider text-text-300">Endpoint</span>
          <code className="flex-1 truncate font-mono text-[13px] text-text-100">{url}</code>
          <Badge>streamable HTTP</Badge>
          <Copy text={url} />
        </div>
      </Card>

      <div className="grid gap-5 lg:grid-cols-[1fr_1.3fr]">
        <Card title="1. Create a key">
          <form onSubmit={create} className="flex flex-col gap-3 sm:flex-row">
            <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="Key name, e.g. Intercom bot" aria-label="Key name" />
            <Button type="submit" disabled={busy}>
              {busy ? <Spinner /> : null} Create key
            </Button>
          </form>
          {error ? <div className="mt-3"><ErrorNote>{error}</ErrorNote></div> : null}
          {created?.key ? (
            <div className="mt-4 rounded-xl border border-success/40 bg-success/5 p-3">
              <div className="mb-1 flex items-center justify-between gap-2">
                <span className="text-[12px] uppercase tracking-wider text-success">Copy it now: it won&apos;t be shown again</span>
                <Copy text={created.key} />
              </div>
              <code className="block break-all font-mono text-[13px] text-text-100">{created.key}</code>
            </div>
          ) : null}
          <div className="mt-5">
            <div className="mb-2 text-[12px] uppercase tracking-wider text-text-300">Active keys</div>
            {!keys.data ? (
              <Spinner />
            ) : keys.data.length ? (
              <ul className="divide-y divide-line/60">
                {keys.data.map((k) => (
                  <li key={k.id} className="flex flex-wrap items-center gap-2 py-2 text-[13px]">
                    <span className="text-text-100">{k.name}</span>
                    <code className="font-mono text-text-300">{k.prefix}…</code>
                    <span className="text-text-300">· last used {timeAgo(k.last_used_at)}</span>
                    <Button variant="danger" className="ml-auto px-3 py-1 text-[12px]" onClick={() => revoke(k.id)}>
                      Revoke
                    </Button>
                  </li>
                ))}
              </ul>
            ) : (
              <Empty>No keys yet.</Empty>
            )}
          </div>
        </Card>

        <Card title="2. Add Supfeel to your agent">
          <Tabs<Client>
            value={client}
            onChange={setClient}
            tabs={[
              { id: "claude-code", label: "Claude Code" },
              { id: "cursor", label: "Cursor" },
              { id: "desktop", label: "Claude Desktop" },
              { id: "python", label: "Your bot (SDK)" },
            ]}
          />
          <p className="mt-3 text-[13px] text-text-300">{HINT[client]}</p>
          <div className="relative mt-2">
            <pre className={cx("scrollbar-thin overflow-x-auto rounded-xl border border-line bg-bg-0/70 p-3 pr-20 font-mono text-[12.5px] leading-relaxed text-lavender-200")}>
              {snippet(client, url, key)}
            </pre>
            <div className="absolute right-2 top-2">
              <Copy text={snippet(client, url, key)} />
            </div>
          </div>
          {!created?.key ? <p className="mt-2 text-[12px] text-text-300">Create a key to fill it in.</p> : null}
        </Card>
      </div>

      <Card title="Tools your agent gets">
        <ul className="divide-y divide-line/60">
          {TOOLS.map(([n, d, price]) => (
            <li key={n} className="flex flex-col gap-1 py-2.5 sm:flex-row sm:items-center sm:gap-4">
              <code className="w-44 shrink-0 font-mono text-[13px] text-text-100">{n}</code>
              <span className="flex-1 text-[13px] text-text-300">{d}</span>
              <span className="text-[12px] text-lavender-200">{price}</span>
            </li>
          ))}
        </ul>
      </Card>
    </div>
  );
}
