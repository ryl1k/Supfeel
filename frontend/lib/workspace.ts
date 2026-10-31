import { API_URL, streamPost } from "./api";
import { authHeaders, setSessionToken } from "./session";

// ------------------------------------------------------------------ types (mirror backend/app/api/*.py)

export type RepoStatus = "pending" | "indexing" | "ready" | "failed";

export interface IndexJob {
  id: string;
  kind: string;
  trigger: string;
  status: "queued" | "running" | "done" | "failed";
  commit_sha: string | null;
  progress: Record<string, unknown> & { phase?: string; chunks_done?: number; chunks_total?: number };
  error: string | null;
  started_at: string;
  finished_at: string | null;
}

export interface Repo {
  id: string;
  full_name: string;
  source: "github" | "local";
  default_branch: string;
  head_sha: string | null;
  status: RepoStatus;
  error: string | null;
  stats: {
    files?: number;
    chunks?: Record<string, number>;
    languages?: Record<string, number>;
    api_operations?: number;
    modules?: number;
    skipped?: Record<string, number>;
    embedding_model?: string;
    last_job_claude_usd?: number;
  };
  settings: { api_base_url?: string; api_token?: string; api_spec_url?: string; auto_fix?: boolean; business_name?: string };
  indexed_at: string | null;
  created_at: string;
  html_url: string | null;
  job: IndexJob | null;
}

export interface RepoDetail extends Repo {
  overview: string;
  modules: { key: string; body: string; generated_by: string }[];
  api_operations: { operation_id: string; method: string; path: string; summary: string }[];
}

export interface GithubStatus {
  auth: "app" | "token" | "anonymous";
  app_slug: string | null;
  install_url: string | null;
  webhook_configured: boolean;
  open_import: boolean;
  allow_local_repos: boolean;
}

export type TicketStatus =
  | "open"
  | "answered"
  | "awaiting_confirmation"
  | "fix_in_review"
  | "fix_verified"
  | "fix_failed"
  | "reported"
  | "resolved"
  | "escalated";

export interface TicketSummary {
  id: string;
  repo_id: string;
  subject: string;
  category: string | null;
  confidence: number | null;
  status: TicketStatus;
  customer: { name?: string; email?: string; ref?: string };
  channel?: "web" | "mcp" | "api";
  pr_url: string | null;
  ci: string | null;
  learned: boolean;
  created_at: string;
  updated_at: string;
}

export interface Check {
  name: string;
  ok: boolean;
  detail?: string;
}

export interface TicketAction {
  id: string;
  operation_id: string;
  method: string;
  path: string;
  args: Record<string, unknown>;
  title: string;
  status: string;
  why?: string;
  response?: { status: number; data: unknown } | null;
  verification?: { ok: boolean; checks: Check[] } | null;
}

export interface Fix {
  decision?: string;
  mode?: "pr" | "patch";
  root_cause?: string;
  summary?: string;
  test?: string;
  confidence?: number;
  workaround?: string;
  files?: string[];
  diff?: string;
  suspects?: string[];
  explanation?: string;
  note?: string;
  branch?: string;
  pr_number?: number;
  pr_url?: string;
  ci?: { state: string; checks: { name: string; status: string; conclusion: string | null; url: string | null }[] };
}

export interface Notification {
  id: number;
  repo_id: string;
  ticket_id: string | null;
  kind: string;
  title: string;
  body: string;
  url: string | null;
  delivered: string[];
  created_at: string;
}

export interface TicketDetail extends TicketSummary {
  triage: Record<string, unknown> & { summary?: string; route?: string; brain?: Record<string, string>; bug_hypothesis?: string };
  resolution: { summary?: string; kind?: string };
  fix: Fix;
  pending_action: TicketAction | null;
  messages: { role: "customer" | "agent" | "frontline" | "system"; content: string; created_at: string }[];
  actions: TicketAction[];
  notifications: Notification[];
}

export interface Span {
  id: string;
  parent_id: string | null;
  name: string;
  kind: "run" | "step" | "llm" | "embedding" | "tool" | "retrieval" | "http";
  status: "ok" | "error";
  attributes: Record<string, unknown>;
  cost_usd: number;
  started_at: string;
  ended_at: string | null;
  duration_ms: number;
}

export interface Trace {
  trace_id: string;
  spans: Span[];
  summary: {
    spans: number;
    cost_usd: number;
    duration_ms: number;
    errors: number;
    by_kind: Record<string, { count: number; duration_ms: number; cost_usd: number }>;
    tokens: Record<string, number>;
  };
}

export interface Hit {
  id: number;
  kind: string;
  path: string;
  symbol: string;
  start_line: number;
  end_line: number;
  text: string;
  score: number;
  cite: string;
}

export interface AskAnswer {
  trace_id: string;
  brain: string;
  answer: string;
  citations: string[];
  confidence: number;
  sources: Hit[];
}

export type TicketEvent =
  | { event: "ticket"; data: { ticket_id: string } }
  | { event: "step"; data: { step: string; status: "running" | "done"; detail: string; [k: string]: unknown } }
  | { event: "token"; data: { text: string } }
  | { event: "action_proposed"; data: { actions: TicketAction[] } }
  | { event: "action_done"; data: { action: TicketAction } }
  | { event: "verified"; data: { action_id: string; title: string; ok: boolean; checks: Check[] } }
  | { event: "fix"; data: Fix }
  | { event: "done"; data: { ticket_id: string; status: TicketStatus; category?: string; route?: string } }
  | { event: "error"; data: { code: string; message: string } };

// ------------------------------------------------------------------ calls

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

async function call<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = { "Content-Type": "application/json", ...authHeaders() };
  const res = await fetch(`${API_URL}${path}`, { ...init, headers: { ...headers, ...(init.headers as object) } });
  if (res.status === 401 && !path.startsWith("/api/auth/")) {
    setSessionToken(null); // expired or revoked: the shell sends the user to /login
  }
  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      if (body.detail) detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
    } catch {
      // keep default message
    }
    throw new ApiError(res.status, detail);
  }
  return res.json() as Promise<T>;
}

export interface Me {
  admin: boolean;
  user: { id: string; email: string; name: string } | null;
  account: { id: string; name: string } | null;
  billing?: Billing;
}

export interface Price {
  metric: string;
  cents: number;
  unit: string;
  description: string;
}

export interface Billing {
  balance_cents: number;
  month: {
    start: string;
    resets_at: string;
    spent_cents: number;
    limit_cents: number;
    by_metric: Record<string, { quantity: number; cents: number }>;
    ai_cost_usd: number;
  };
  repos: number;
  auto_recharge: { enabled: boolean; threshold_cents: number; amount_cents: number };
  payment_method: { brand: string; last4: string; name?: string } | null;
  prices: Price[];
  statement?: {
    id: number;
    kind: "grant" | "topup" | "usage" | "refund";
    metric: string | null;
    quantity: number;
    amount_cents: number;
    description: string;
    repo_id: string | null;
    ref: string | null;
    created_at: string;
  }[];
}

export interface ApiKey {
  id: string;
  name: string;
  prefix: string;
  created_at: string;
  last_used_at: string | null;
  key?: string;
}

export const api = {
  signup: (body: { email: string; password: string; name: string; company: string }) =>
    call<Me & { token: string }>("/api/auth/signup", { method: "POST", body: JSON.stringify(body) }),
  login: (body: { email: string; password: string }) =>
    call<Me & { token: string }>("/api/auth/login", { method: "POST", body: JSON.stringify(body) }),
  logout: () => call<{ ok: boolean }>("/api/auth/logout", { method: "POST" }),
  me: () => call<Me>("/api/me"),
  billing: () => call<Billing>("/api/billing"),
  topup: (amount_cents: number, card?: { number: string; name: string }) =>
    call<Billing>("/api/billing/topup", { method: "POST", body: JSON.stringify({ amount_cents, card }) }),
  saveCard: (card: { number: string; name: string }) => call<Billing>("/api/billing/card", { method: "PUT", body: JSON.stringify(card) }),
  billingSettings: (body: Record<string, number | boolean>) =>
    call<Billing>("/api/billing/settings", { method: "PATCH", body: JSON.stringify(body) }),
  keys: (repoId: string) => call<ApiKey[]>(`/api/repos/${repoId}/keys`),
  createKey: (repoId: string, name: string) => call<ApiKey>(`/api/repos/${repoId}/keys`, { method: "POST", body: JSON.stringify({ name }) }),
  revokeKey: (keyId: string) => call<{ revoked: string }>(`/api/keys/${keyId}`, { method: "DELETE" }),
  deleteRepo: (id: string) => call<{ deleted: string }>(`/api/repos/${id}`, { method: "DELETE" }),
  githubStatus: () => call<GithubStatus>("/api/github/status"),
  repos: () => call<Repo[]>("/api/repos"),
  repo: (id: string) => call<RepoDetail>(`/api/repos/${id}`),
  jobs: (id: string) => call<IndexJob[]>(`/api/repos/${id}/jobs`),
  importRepo: (body: { repo?: string; local_path?: string; branch?: string }) =>
    call<{ id: string; job_id: string }>("/api/repos", { method: "POST", body: JSON.stringify(body) }),
  reindex: (id: string) => call<{ job_id: string }>(`/api/repos/${id}/reindex`, { method: "POST" }),
  updateSettings: (id: string, body: Partial<Repo["settings"]>) =>
    call<Repo["settings"]>(`/api/repos/${id}/settings`, { method: "PATCH", body: JSON.stringify(body) }),
  search: (id: string, q: string) => call<Hit[]>(`/api/repos/${id}/search?q=${encodeURIComponent(q)}`),
  ask: (id: string, question: string) =>
    call<AskAnswer>(`/api/repos/${id}/ask`, { method: "POST", body: JSON.stringify({ question }) }),
  file: (id: string, path: string) =>
    call<{ path: string; language: string; content: string }>(`/api/repos/${id}/file?path=${encodeURIComponent(path)}`),
  tickets: (repoId?: string) => call<TicketSummary[]>(`/api/tickets${repoId ? `?repo_id=${repoId}` : ""}`),
  ticket: (id: string) => call<TicketDetail>(`/api/tickets/${id}`),
  ticketTrace: (id: string) => call<Trace>(`/api/tickets/${id}/trace`),
  jobTrace: (id: string) => call<Trace>(`/api/jobs/${id}/trace`),
  notifications: (repoId?: string) => call<Notification[]>(`/api/notifications${repoId ? `?repo_id=${repoId}` : ""}`),
};

export const ticketStream = {
  create: (repoId: string, customer: TicketSummary["customer"], message: string, on: (e: TicketEvent) => void, signal?: AbortSignal) =>
    streamPost<TicketEvent>(`/api/repos/${repoId}/tickets`, { customer, message }, on, signal, authHeaders()),
  message: (ticketId: string, message: string, on: (e: TicketEvent) => void, signal?: AbortSignal) =>
    streamPost<TicketEvent>(`/api/tickets/${ticketId}/messages`, { message }, on, signal, authHeaders()),
  confirm: (ticketId: string, approved: boolean, on: (e: TicketEvent) => void, signal?: AbortSignal) =>
    streamPost<TicketEvent>(`/api/tickets/${ticketId}/confirm`, { approved }, on, signal, authHeaders()),
};
