"use client";

import { type ElementType, type ReactNode, useEffect, useRef, useState } from "react";

/** Adds `.is-visible` the first time the element scrolls into view (CSS does the animation). */
export function Reveal({
  children,
  as: Tag = "div",
  className = "",
  stagger = false,
  id,
}: {
  children: ReactNode;
  as?: ElementType;
  className?: string;
  stagger?: boolean;
  id?: string;
}) {
  const ref = useRef<HTMLElement>(null);
  const [visible, setVisible] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el || typeof IntersectionObserver === "undefined") {
      setVisible(true);
      return;
    }
    const io = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setVisible(true);
          io.disconnect();
        }
      },
      { rootMargin: "0px 0px -10% 0px", threshold: 0.12 },
    );
    io.observe(el);
    return () => io.disconnect();
  }, []);
  return (
    <Tag ref={ref} id={id} className={`${stagger ? "reveal-stagger" : "reveal"} ${visible ? "is-visible" : ""} ${className}`}>
      {children}
    </Tag>
  );
}
