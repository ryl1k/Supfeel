"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

import { Logo } from "@/components/brand/Gem";

import { cx } from "./ui";

const NAV = [
  { href: "/app", label: "Workspace" },
  { href: "/app/tickets", label: "Tickets" },
  { href: "/app/inbox", label: "Inbox" },
];

export function Shell({ children }: { children: ReactNode }) {
  const path = usePathname();
  return (
    <div className="relative min-h-dvh bg-[radial-gradient(120%_80%_at_0%_0%,#0b1240_0%,#060a2b_60%)]">
      <header className="sticky top-0 z-20 border-b border-line bg-bg-0/70 backdrop-blur-md">
        <div className="mx-auto flex max-w-[1320px] items-center gap-6 px-4 py-3.5 sm:px-8">
          <Link href="/" aria-label="Supfeel home" className="shrink-0 scale-90 sm:scale-100">
            <Logo />
          </Link>
          <nav className="scrollbar-thin flex flex-1 items-center gap-1 overflow-x-auto">
            {NAV.map((n) => {
              const active = n.href === "/app" ? path === "/app" || path.startsWith("/app/repos") : path.startsWith(n.href);
              return (
                <Link
                  key={n.href}
                  href={n.href}
                  className={cx(
                    "whitespace-nowrap rounded-full px-3.5 py-1.5 text-[14px] transition-colors",
                    active ? "bg-panel-strong text-text-100" : "text-text-300 hover:text-text-100",
                  )}
                >
                  {n.label}
                </Link>
              );
            })}
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-[1320px] px-4 py-6 sm:px-8 sm:py-8">{children}</main>
    </div>
  );
}
