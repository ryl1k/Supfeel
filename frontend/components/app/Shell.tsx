"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { type ReactNode, useEffect } from "react";

import { Logo } from "@/components/brand/Gem";
import { usePoll } from "@/lib/usePoll";
import { setSessionToken, useSessionToken } from "@/lib/session";
import { api } from "@/lib/workspace";

import { cx } from "./ui";

const NAV = [
  { href: "/app", label: "Workspace" },
  { href: "/app/tickets", label: "Tickets" },
  { href: "/app/inbox", label: "Inbox" },
  { href: "/app/billing", label: "Billing" },
];

export function money(cents: number) {
  return `$${(cents / 100).toFixed(2)}`;
}

function Account() {
  const router = useRouter();
  const me = usePoll(() => api.me(), "me", 20_000);
  const logout = async () => {
    try {
      await api.logout();
    } catch {
      // session already gone
    }
    setSessionToken(null);
    router.replace("/login");
  };
  const balance = me.data?.billing?.balance_cents;
  return (
    <div className="flex shrink-0 items-center gap-2">
      {balance !== undefined ? (
        <Link
          href="/app/billing"
          className={cx(
            "rounded-full border px-3 py-1.5 text-[13px] tabular-nums",
            balance < 100 ? "border-warning/50 text-warning" : "border-line text-lavender-200 hover:border-lavender-300/60",
          )}
          title="Credit balance"
        >
          {money(balance)}
        </Link>
      ) : null}
      <span className="hidden max-w-[160px] truncate text-[13px] text-text-300 md:block">{me.data?.account?.name ?? me.data?.user?.email}</span>
      <button onClick={logout} className="rounded-full px-2.5 py-1.5 text-[13px] text-text-300 hover:text-text-100">
        Sign out
      </button>
    </div>
  );
}

export function Shell({ children }: { children: ReactNode }) {
  const path = usePathname();
  const router = useRouter();
  const token = useSessionToken();
  useEffect(() => {
    if (token === "") router.replace(`/login?next=${encodeURIComponent(path)}`);
  }, [token, path, router]);

  return (
    <div className="relative min-h-dvh bg-[radial-gradient(120%_80%_at_0%_0%,#0b1240_0%,#060a2b_60%)]">
      <header className="sticky top-0 z-20 border-b border-line bg-bg-0/70 backdrop-blur-md">
        <div className="mx-auto flex max-w-[1320px] items-center gap-4 px-4 py-3.5 sm:gap-6 sm:px-8">
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
          {token ? <Account /> : null}
        </div>
      </header>
      <main key={path} className="page-enter mx-auto max-w-[1320px] px-4 py-6 sm:px-8 sm:py-8">
        {token ? children : <div className="skeleton h-40" />}
      </main>
    </div>
  );
}
