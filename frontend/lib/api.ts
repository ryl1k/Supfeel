import type { AgentEvent, DemoCustomer } from "./types";

export const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/$/, "");

/** POST + Server-Sent Events. EventSource only supports GET, so parse the stream by hand. */
export async function streamPost<E = AgentEvent>(
  path: string,
  body: unknown,
  onEvent: (e: E) => void,
  signal?: AbortSignal,
  extraHeaders: Record<string, string> = {},
) {
  const res = await fetch(`${API_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "text/event-stream", ...extraHeaders },
    body: JSON.stringify(body),
    signal,
  });
  if (!res.ok || !res.body) {
    let detail = `Request failed (${res.status})`;
    try {
      const j = await res.json();
      if (typeof j.detail === "string") detail = j.detail;
    } catch {
      // keep default
    }
    throw new Error(detail);
  }
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true }).replace(/\r\n/g, "\n");
    let sep = buffer.indexOf("\n\n");
    while (sep !== -1) {
      const block = buffer.slice(0, sep);
      buffer = buffer.slice(sep + 2);
      let name = "";
      const data: string[] = [];
      for (const line of block.split("\n")) {
        if (line.startsWith("event:")) name = line.slice(6).trim();
        else if (line.startsWith("data:")) data.push(line.slice(5).trimStart());
      }
      if (name && data.length) {
        try {
          onEvent({ event: name, data: JSON.parse(data.join("\n")) } as E);
        } catch {
          // ignore malformed event
        }
      }
      sep = buffer.indexOf("\n\n");
    }
  }
}

export function sendMessage(
  conversationId: string,
  customerId: string,
  message: string,
  onEvent: (e: AgentEvent) => void,
  signal?: AbortSignal,
) {
  return streamPost(
    "/api/chat",
    { conversation_id: conversationId, customer_id: customerId, message },
    onEvent,
    signal,
  );
}

export function sendConfirmation(
  conversationId: string,
  approved: boolean,
  onEvent: (e: AgentEvent) => void,
  signal?: AbortSignal,
) {
  return streamPost("/api/chat/confirm", { conversation_id: conversationId, approved }, onEvent, signal);
}

export async function getDemoCustomers(): Promise<DemoCustomer[]> {
  const res = await fetch(`${API_URL}/api/customers/demo`);
  if (!res.ok) throw new Error(`Could not load demo customers (${res.status})`);
  return res.json();
}

export async function resetDemo(): Promise<void> {
  const res = await fetch(`${API_URL}/api/demo/reset`, { method: "POST" });
  if (!res.ok) throw new Error(`Reset failed (${res.status})`);
}

export function newConversationId(): string {
  const rand =
    typeof crypto !== "undefined" && "randomUUID" in crypto
      ? crypto.randomUUID().replace(/-/g, "").slice(0, 16)
      : Math.random().toString(36).slice(2, 18);
  return `c_${rand}`;
}
