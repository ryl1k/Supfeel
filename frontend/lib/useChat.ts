"use client";

import { useCallback, useRef, useState } from "react";

import { newConversationId, sendConfirmation, sendMessage } from "./api";
import type { AgentEvent, AssistantTurn, Turn } from "./types";

function emptyAssistant(): AssistantTurn {
  return {
    kind: "assistant",
    id: `a_${Math.random().toString(36).slice(2, 10)}`,
    text: "",
    steps: {},
    proposed: [],
    confirmation: null,
    done: [],
    verified: {},
    recommendations: null,
    notices: [],
    outcome: null,
    streaming: true,
    error: null,
  };
}

function reduce(turn: AssistantTurn, e: AgentEvent): AssistantTurn {
  switch (e.event) {
    case "step":
      return { ...turn, steps: { ...turn.steps, [e.data.step]: e.data } };
    case "token":
      return { ...turn, text: turn.text + e.data.text };
    case "action_proposed":
      return { ...turn, proposed: e.data.actions, confirmation: "pending" };
    case "action_done":
      return { ...turn, done: [...turn.done.filter((a) => a.action_id !== e.data.action.action_id), e.data.action] };
    case "verified":
      return { ...turn, verified: { ...turn.verified, [e.data.action_id]: { ok: e.data.ok, checks: e.data.checks } } };
    case "recommendations":
      return { ...turn, recommendations: e.data };
    case "notice":
      return { ...turn, notices: [...turn.notices, e.data.message] };
    case "error":
      return { ...turn, error: e.data.message, streaming: false };
    case "done":
      return {
        ...turn,
        outcome: e.data.outcome,
        streaming: false,
        confirmation: e.data.outcome === "awaiting_confirmation" ? "pending" : turn.confirmation,
      };
  }
}

export function useChat(customerId: string | null) {
  const [turns, setTurns] = useState<Turn[]>([]);
  const [busy, setBusy] = useState(false);
  // Created lazily (in event handlers) so nothing random runs during prerender.
  const conversationId = useRef<string | null>(null);
  const convId = () => (conversationId.current ??= newConversationId());
  const abort = useRef<AbortController | null>(null);

  const reset = useCallback(() => {
    abort.current?.abort();
    conversationId.current = null;
    setTurns([]);
    setBusy(false);
  }, []);

  const run = useCallback(async (start: (onEvent: (e: AgentEvent) => void, signal: AbortSignal) => Promise<void>) => {
    const assistant = emptyAssistant();
    setTurns((t) => [...t, assistant]);
    setBusy(true);
    const controller = new AbortController();
    abort.current = controller;
    const update = (fn: (a: AssistantTurn) => AssistantTurn) =>
      setTurns((all) => all.map((t) => (t.kind === "assistant" && t.id === assistant.id ? fn(t) : t)));
    try {
      await start((e) => update((a) => reduce(a, e)), controller.signal);
      update((a) => (a.streaming ? { ...a, streaming: false } : a));
    } catch (err) {
      if (!controller.signal.aborted) {
        update((a) => ({
          ...a,
          streaming: false,
          error: err instanceof Error ? `Can't reach Supfeel right now (${err.message}).` : "Something went wrong.",
        }));
      }
    } finally {
      if (abort.current === controller) setBusy(false);
    }
  }, []);

  const send = useCallback(
    async (text: string) => {
      const message = text.trim();
      if (!message || !customerId || busy) return;
      // Typing instead of clicking settles any open proposal on the client too.
      setTurns((t) => [
        ...t.map((x) =>
          x.kind === "assistant" && x.confirmation === "pending" ? { ...x, confirmation: null } : x,
        ),
        { kind: "user", id: `u_${Date.now()}`, text: message },
      ]);
      await run((onEvent, signal) => sendMessage(convId(), customerId, message, onEvent, signal));
    },
    [busy, customerId, run],
  );

  const confirm = useCallback(
    async (turnId: string, approved: boolean) => {
      if (busy) return;
      setTurns((t) => [
        ...t.map((x) =>
          x.kind === "assistant" && x.id === turnId
            ? { ...x, confirmation: approved ? ("approved" as const) : ("declined" as const) }
            : x,
        ),
        { kind: "user", id: `u_${Date.now()}`, text: approved ? "Yes, go ahead." : "No, don't do that." },
      ]);
      await run((onEvent, signal) => sendConfirmation(convId(), approved, onEvent, signal));
    },
    [busy, run],
  );

  return { turns, busy, send, confirm, reset };
}
