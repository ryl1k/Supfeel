"use client";

import { useCallback, useRef, useState } from "react";

import { type Check, type Fix, type TicketAction, type TicketEvent, type TicketStatus, type TicketSummary, ticketStream } from "./workspace";

export interface StepState {
  step: string;
  status: "running" | "done";
  detail: string;
  history: string[]; // successive "running" details (e.g. fix agent tool calls)
}

export interface AgentTurn {
  kind: "agent";
  id: string;
  text: string;
  steps: StepState[];
  proposed: TicketAction[];
  confirmation: "pending" | "approved" | "declined" | null;
  verified: { title: string; ok: boolean; checks: Check[] }[];
  fix: Fix | null;
  status: TicketStatus | null;
  streaming: boolean;
  error: string | null;
}

export type ChatTurn = { kind: "customer"; id: string; text: string } | AgentTurn;

const rid = () => Math.random().toString(36).slice(2, 10);

function reduce(t: AgentTurn, e: TicketEvent): AgentTurn {
  switch (e.event) {
    case "step": {
      const steps = [...t.steps];
      const i = steps.findIndex((s) => s.step === e.data.step);
      const prev = i >= 0 ? steps[i] : { step: e.data.step, status: e.data.status, detail: "", history: [] };
      const next: StepState = {
        ...prev,
        status: e.data.status,
        detail: e.data.detail || prev.detail,
        history: e.data.status === "running" && e.data.detail ? [...prev.history, e.data.detail].slice(-12) : prev.history,
      };
      if (i >= 0) steps[i] = next;
      else steps.push(next);
      return { ...t, steps };
    }
    case "token":
      return { ...t, text: t.text + e.data.text };
    case "action_proposed":
      return { ...t, proposed: e.data.actions, confirmation: "pending" };
    case "verified":
      return { ...t, verified: [...t.verified, { title: e.data.title, ok: e.data.ok, checks: e.data.checks }] };
    case "fix":
      return { ...t, fix: e.data };
    case "error":
      return { ...t, error: e.data.message, streaming: false };
    case "done":
      return { ...t, status: e.data.status, streaming: false, confirmation: e.data.status === "awaiting_confirmation" ? "pending" : t.confirmation };
    default:
      return t;
  }
}

export function useTicketChat(repoId: string, customer: TicketSummary["customer"]) {
  const [turns, setTurns] = useState<ChatTurn[]>([]);
  const [ticketId, setTicketId] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const abort = useRef<AbortController | null>(null);
  const idRef = useRef<string | null>(null);

  const reset = useCallback(() => {
    abort.current?.abort();
    idRef.current = null;
    setTicketId(null);
    setTurns([]);
    setBusy(false);
  }, []);

  const run = useCallback(async (start: (on: (e: TicketEvent) => void, signal: AbortSignal) => Promise<void>) => {
    const turn: AgentTurn = { kind: "agent", id: rid(), text: "", steps: [], proposed: [], confirmation: null, verified: [], fix: null, status: null, streaming: true, error: null };
    setTurns((all) => [...all, turn]);
    setBusy(true);
    const controller = new AbortController();
    abort.current = controller;
    const update = (fn: (a: AgentTurn) => AgentTurn) => setTurns((all) => all.map((x) => (x.kind === "agent" && x.id === turn.id ? fn(x) : x)));
    try {
      await start((e) => {
        if (e.event === "ticket") {
          idRef.current = e.data.ticket_id;
          setTicketId(e.data.ticket_id);
        }
        update((a) => reduce(a, e));
      }, controller.signal);
      update((a) => (a.streaming ? { ...a, streaming: false } : a));
    } catch (err) {
      if (!controller.signal.aborted)
        update((a) => ({ ...a, streaming: false, error: err instanceof Error ? `Can't reach support right now (${err.message}).` : "Something went wrong." }));
    } finally {
      if (abort.current === controller) setBusy(false);
    }
  }, []);

  const send = useCallback(
    async (text: string) => {
      const message = text.trim();
      if (!message || busy) return;
      setTurns((all) => [
        ...all.map((x) => (x.kind === "agent" && x.confirmation === "pending" ? { ...x, confirmation: null } : x)),
        { kind: "customer", id: rid(), text: message },
      ]);
      const current = idRef.current;
      await run((on, signal) => (current ? ticketStream.message(current, message, on, signal) : ticketStream.create(repoId, customer, message, on, signal)));
    },
    [busy, customer, repoId, run],
  );

  const confirm = useCallback(
    async (turnId: string, approved: boolean) => {
      const current = idRef.current;
      if (busy || !current) return;
      setTurns((all) => [
        ...all.map((x) => (x.kind === "agent" && x.id === turnId ? { ...x, confirmation: approved ? ("approved" as const) : ("declined" as const) } : x)),
        { kind: "customer", id: rid(), text: approved ? "Yes, go ahead." : "No, don't do that." },
      ]);
      await run((on, signal) => ticketStream.confirm(current, approved, on, signal));
    },
    [busy, run],
  );

  return { turns, ticketId, busy, send, confirm, reset };
}
