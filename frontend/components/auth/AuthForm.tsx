"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { type FormEvent, useState } from "react";

import { Button, ErrorNote, Input, Spinner } from "@/components/app/ui";
import { Gem, Logo } from "@/components/brand/Gem";
import { setSessionToken } from "@/lib/session";
import { api } from "@/lib/workspace";

export function AuthForm({ mode }: { mode: "login" | "signup" }) {
  const router = useRouter();
  const [form, setForm] = useState({ email: "", password: "", name: "", company: "" });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) => setForm({ ...form, [k]: e.target.value });

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const res = mode === "signup" ? await api.signup(form) : await api.login({ email: form.email, password: form.password });
      setSessionToken(res.token);
      const next = new URLSearchParams(window.location.search).get("next");
      router.replace(next && next.startsWith("/") ? next : "/app");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setBusy(false);
    }
  };

  return (
    <main className="flex min-h-dvh flex-col bg-[radial-gradient(120%_90%_at_0%_0%,#0b1240_0%,#060a2b_55%)]">
      <header className="mx-auto w-full max-w-[1100px] px-4 py-5 sm:px-8">
        <Link href="/" aria-label="Supfeel home">
          <Logo />
        </Link>
      </header>
      <div className="flex flex-1 items-start justify-center px-4 pb-16 pt-6 sm:pt-12">
        <form onSubmit={submit} className="glass w-full max-w-[420px] space-y-4 rounded-[24px] p-6 sm:p-8">
          <div className="flex flex-col items-center gap-3 text-center">
            <Gem size={52} />
            <h1 className="text-[24px] font-semibold">{mode === "signup" ? "Create your workspace" : "Welcome back"}</h1>
            <p className="text-[14px] text-text-300">
              {mode === "signup"
                ? "Import your repo, connect your support agent over MCP. $5 of free credit, then pay as you go."
                : "Sign in to your Supfeel workspace."}
            </p>
          </div>
          {mode === "signup" ? (
            <div className="grid gap-3 sm:grid-cols-2">
              <Input placeholder="Your name" value={form.name} onChange={set("name")} aria-label="Name" autoComplete="name" />
              <Input placeholder="Company" value={form.company} onChange={set("company")} aria-label="Company" autoComplete="organization" />
            </div>
          ) : null}
          <Input type="email" required placeholder="Email" value={form.email} onChange={set("email")} aria-label="Email" autoComplete="email" />
          <Input
            type="password"
            required
            minLength={mode === "signup" ? 8 : undefined}
            placeholder={mode === "signup" ? "Password (8+ characters)" : "Password"}
            value={form.password}
            onChange={set("password")}
            aria-label="Password"
            autoComplete={mode === "signup" ? "new-password" : "current-password"}
          />
          {error ? <ErrorNote>{error}</ErrorNote> : null}
          <Button type="submit" disabled={busy} className="w-full py-3">
            {busy ? <Spinner /> : null} {mode === "signup" ? "Create workspace" : "Sign in"}
          </Button>
          <p className="text-center text-[13px] text-text-300">
            {mode === "signup" ? (
              <>
                Already have an account?{" "}
                <Link href="/login" className="text-lavender-200 hover:text-white">
                  Sign in
                </Link>
              </>
            ) : (
              <>
                New to Supfeel?{" "}
                <Link href="/signup" className="text-lavender-200 hover:text-white">
                  Create a workspace
                </Link>
              </>
            )}
          </p>
        </form>
      </div>
    </main>
  );
}
