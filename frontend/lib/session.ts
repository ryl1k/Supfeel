"use client";

import { useSyncExternalStore } from "react";

const KEY = "supfeel_session";
const listeners = new Set<() => void>();

export function getSessionToken(): string {
  try {
    return localStorage.getItem(KEY) ?? "";
  } catch {
    return "";
  }
}

export function setSessionToken(token: string | null) {
  try {
    if (token) localStorage.setItem(KEY, token);
    else localStorage.removeItem(KEY);
  } catch {
    // storage unavailable: the session lasts for this page only
  }
  listeners.forEach((l) => l());
}

function subscribe(cb: () => void) {
  listeners.add(cb);
  const onStorage = (e: StorageEvent) => e.key === KEY && cb();
  window.addEventListener("storage", onStorage);
  return () => {
    listeners.delete(cb);
    window.removeEventListener("storage", onStorage);
  };
}

/** "" while prerendering or signed out. `null` means "not known yet" (server snapshot). */
export function useSessionToken(): string | null {
  return useSyncExternalStore(subscribe, getSessionToken, () => null);
}

export function authHeaders(): Record<string, string> {
  const t = getSessionToken();
  return t ? { Authorization: `Bearer ${t}` } : {};
}
