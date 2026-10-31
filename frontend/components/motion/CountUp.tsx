"use client";

import { useEffect, useRef, useState } from "react";

/** Animates a number from its previous value to `value` (ease-out, ~700 ms). */
export function CountUp({ value, format = (n) => String(Math.round(n)), duration = 700 }: { value: number; format?: (n: number) => string; duration?: number }) {
  const [shown, setShown] = useState(0);
  const from = useRef(0);
  useEffect(() => {
    const reduce = typeof window !== "undefined" && window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
    const start = performance.now();
    const a = from.current;
    let frame = 0;
    const tick = (t: number) => {
      const p = reduce ? 1 : Math.min(1, (t - start) / duration);
      const eased = 1 - Math.pow(1 - p, 3);
      setShown(a + (value - a) * eased);
      if (p < 1) frame = requestAnimationFrame(tick);
      else from.current = value;
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [value, duration]);
  return <span className="tabular-nums">{format(shown)}</span>;
}
