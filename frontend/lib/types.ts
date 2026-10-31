// Mirrors backend/app/agent/events.py + docs/features/resolution-agent/data-model.md. Change both together.

export type StepName = "understand" | "investigate" | "policy" | "plan" | "act" | "verify" | "respond";

export type StepEvent = {
  step: StepName;
  status: "running" | "done";
  detail: string;
  brain?: "llm" | "rules";
  citations?: string[];
  decision?: string;
  actions?: string[];
  calls?: string[];
};

export type Check = { label: string; ok: boolean; detail: string };

export type Verification = { ok: boolean; checks: Check[] };

export type AgentAction = {
  action_id: string;
  tool: string;
  title: string;
  description: string;
  amount_cents: number;
  needs_confirmation: boolean;
  status: "proposed" | "approved" | "declined" | "done" | "failed";
  result: Record<string, unknown> | null;
  error: { error: string; message: string } | null;
  verification: Verification | null;
};

export type Recommendation = {
  sku: string;
  product_id: string;
  name: string;
  color: string;
  size: number;
  width: string;
  price: string;
  reason: string;
};

export type Outcome =
  | "asked"
  | "awaiting_confirmation"
  | "resolved"
  | "partially_resolved"
  | "declined"
  | "not_allowed"
  | "escalated"
  | "answered";

export type AgentEvent =
  | { event: "step"; data: StepEvent }
  | { event: "token"; data: { text: string } }
  | { event: "action_proposed"; data: { actions: AgentAction[] } }
  | { event: "action_done"; data: { action: AgentAction } }
  | { event: "verified"; data: { action_id: string; title: string; ok: boolean; checks: Check[] } }
  | { event: "recommendations"; data: { provider: string; items: Recommendation[] } }
  | { event: "notice"; data: { kind: "fallback" | "budget"; node: string; message: string } }
  | { event: "error"; data: { code: string; message: string } }
  | { event: "done"; data: { outcome: Outcome; status: string; brain?: string } };

export type DemoCustomer = { id: string; name: string; tier: string; persona: string };

export type UserTurn = { kind: "user"; id: string; text: string };

export type AssistantTurn = {
  kind: "assistant";
  id: string;
  text: string;
  steps: Partial<Record<StepName, StepEvent>>;
  proposed: AgentAction[];
  confirmation: "pending" | "approved" | "declined" | null;
  done: AgentAction[];
  verified: Record<string, { ok: boolean; checks: Check[] }>;
  recommendations: { provider: string; items: Recommendation[] } | null;
  notices: string[];
  outcome: Outcome | null;
  streaming: boolean;
  error: string | null;
};

export type Turn = UserTurn | AssistantTurn;
