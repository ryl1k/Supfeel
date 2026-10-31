"use client";

import { useCallback, useEffect, useRef, useState } from "react";

/** Fetch on mount (and whenever `key` changes), then every `intervalMs` while `active(data)` is true
 * (or always when `active` is omitted). */
export function usePoll<T>(fetcher: () => Promise<T>, key: string, intervalMs = 3000, active?: (d: T | null) => boolean) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fetcherRef = useRef(fetcher);
  const activeRef = useRef(active);
  useEffect(() => {
    fetcherRef.current = fetcher;
    activeRef.current = active;
  });

  const refresh = useCallback(async () => {
    try {
      const d = await fetcherRef.current();
      setData(d);
      setError(null);
      return d;
    } catch (e) {
      setError(e instanceof Error ? e.message : "Request failed");
      return null;
    }
  }, []);

  useEffect(() => {
    let stopped = false;
    let timer: ReturnType<typeof setTimeout> | undefined;
    const tick = async () => {
      const d = await refresh();
      if (stopped) return;
      if (!activeRef.current || activeRef.current(d)) timer = setTimeout(tick, intervalMs);
    };
    tick();
    return () => {
      stopped = true;
      if (timer) clearTimeout(timer);
    };
  }, [refresh, intervalMs, key]);

  return { data, error, refresh };
}
