import Link from "next/link";

import { Logo } from "@/components/brand/Gem";
import { EscalationFlow } from "@/components/landing/EscalationFlow";
import { Reveal } from "@/components/motion/Reveal";
import { ArrowRight, Bolt, Chat, Search, Shield } from "@/components/ui/icons";

const FEATURES = [
  {
    icon: <Search />,
    title: "Learns your product",
    body: "Import a GitHub repo. Supfeel indexes code, docs and API specs, explains every module, and re-indexes on every push.",
  },
  {
    icon: <Chat />,
    title: "Explains what customers misread",
    body: "Fees, limits, rules: answered from your own code and docs, so the answer matches how the product really behaves.",
  },
  {
    icon: <Bolt />,
    title: "Does it for them, or fixes it",
    body: "Customer can't order? Supfeel places it through your API. Real bug? It opens a pull request with the fix and a test.",
  },
  {
    icon: <Shield />,
    title: "Verified and transparent",
    body: "Actions are read back from your API, fixes are proven by your CI, and every call is traced in a graph you can inspect.",
  },
];

const STEPS = [
  ["Sign up and import", "Create a workspace and connect your repository through the GitHub App."],
  ["Supfeel learns it", "Code, docs and API become a knowledge base, re-indexed on every push."],
  ["Add the MCP server", "One line in your support agent's config: Claude, Cursor or your own bot."],
  ["Your bot escalates", "When it's stuck, it calls escalate with the conversation so far."],
  ["Supfeel resolves", "Explains, acts through your API after the customer's OK, or ships a fix PR."],
  ["Verified, then relayed", "Read-back checks and CI prove it; your bot sends the reply."],
];

export function Features() {
  return (
    <section id="features" className="relative z-10 mx-auto w-full max-w-[1320px] scroll-mt-10 px-4 py-20 sm:px-8">
      <p className="text-[15px] uppercase tracking-[0.2em] text-lavender-300">Features</p>
      <h2 className="mt-3 max-w-[760px] text-[34px] font-light leading-tight sm:text-[46px]">
        More than answers: <span className="text-gradient italic">real solutions.</span>
      </h2>
      <Reveal stagger className="mt-12 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {FEATURES.map((f) => (
          <div key={f.title} className="glass lift rounded-[24px] p-7">
            <span className="flex h-11 w-11 items-center justify-center rounded-full border border-line text-lavender-300">
              {f.icon}
            </span>
            <h3 className="mt-5 text-[19px] font-medium">{f.title}</h3>
            <p className="mt-2 text-[15px] leading-relaxed text-text-300">{f.body}</p>
          </div>
        ))}
      </Reveal>
    </section>
  );
}

export function HowItWorks() {
  return (
    <section id="how-it-works" className="relative z-10 mx-auto w-full max-w-[1320px] scroll-mt-10 px-4 py-20 sm:px-8">
      <p className="text-[15px] uppercase tracking-[0.2em] text-lavender-300">How it works</p>
      <h2 className="mt-3 text-[34px] font-light leading-tight sm:text-[46px]">From stuck customer to verified fix</h2>
      <Reveal>
        <EscalationFlow />
      </Reveal>
      <Reveal as="ol" stagger className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {STEPS.map(([title, body], i) => (
          <li key={title} className="glass lift flex gap-5 rounded-[22px] p-6">
            <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-sapphire-600 text-[15px] font-semibold">
              {i + 1}
            </span>
            <div>
              <h3 className="text-[18px] font-medium">{title}</h3>
              <p className="mt-1 text-[15px] leading-relaxed text-text-300">{body}</p>
            </div>
          </li>
        ))}
      </Reveal>
    </section>
  );
}

export function About() {
  return (
    <section id="about" className="relative z-10 mx-auto w-full max-w-[1320px] scroll-mt-10 px-4 py-20 sm:px-8">
      <Reveal className="glass grid gap-10 rounded-[28px] p-8 sm:p-12 lg:grid-cols-[1.3fr_1fr]">
        <div>
          <p className="text-[15px] uppercase tracking-[0.2em] text-lavender-300">About</p>
          <h2 className="mt-3 text-[30px] font-light leading-tight sm:text-[40px]">
            Support that takes responsibility
          </h2>
          <p className="mt-5 text-[16px] leading-relaxed text-text-300">
            Traditional support bounces customers between an FAQ, an agent and an engineering backlog. Supfeel has
            read your codebase, so it knows when the customer misunderstood, when it can simply do the thing for them,
            and when the product is broken, and then it fixes the code. It reasons with Claude, runs as a LangGraph
            state machine, and never claims a fix it hasn&apos;t verified.
          </p>
          <p className="mt-4 text-[16px] leading-relaxed text-text-300">
            The demo runs against Slice, a small pizza-delivery API with a couple of real bugs. Import it, open
            its support page, and watch a customer message turn into a verified pull request.
          </p>
        </div>
        <ul className="grid content-start gap-3 text-[15px]">
          {[
            ["Grounded in code", "Answers cite your repo, not a guess"],
            ["Human in the loop", "Writes need the customer's OK; PRs need review"],
            ["Safe by design", "Scoped to the customer's own account"],
            ["Transparent", "Every step, call and cost is traced"],
          ].map(([t, d]) => (
            <li key={t} className="rounded-[16px] border border-line bg-panel-strong px-5 py-4">
              <span className="font-medium">{t}</span>
              <span className="block text-text-300">{d}</span>
            </li>
          ))}
        </ul>
      </Reveal>
    </section>
  );
}

const PRICING = [
  ["Escalated ticket", "$0.15", "Investigation, explanation or action, verification, reply"],
  ["Fix run", "$1.00", "Root cause, code change, regression test, pull request"],
  ["Product question", "$0.02", "Cited answer from your code and docs"],
  ["Index run", "$0.10", "Import or re-index (changed files only)"],
];

export function Pricing() {
  return (
    <section id="pricing" className="relative z-10 mx-auto w-full max-w-[1320px] scroll-mt-10 px-4 py-20 sm:px-8">
      <p className="text-[15px] uppercase tracking-[0.2em] text-lavender-300">Pricing</p>
      <h2 className="mt-3 text-[34px] font-light leading-tight sm:text-[46px]">
        Pay as you go. <span className="text-gradient italic">No subscription.</span>
      </h2>
      <p className="mt-4 max-w-[640px] text-[16px] text-text-300">
        Start with $5 of free credit. Top up when you need to, set a monthly spend limit (it resets on the 1st), or turn on auto-recharge.
      </p>
      <Reveal stagger className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {PRICING.map(([name, price, body]) => (
          <div key={name} className="glass lift rounded-[22px] p-6">
            <div className="text-[15px] text-lavender-200">{name}</div>
            <div className="mt-2 text-[34px] font-semibold">{price}</div>
            <p className="mt-2 text-[14px] leading-relaxed text-text-300">{body}</p>
          </div>
        ))}
      </Reveal>
    </section>
  );
}

export function FinalCta() {
  return (
    <Reveal as="section" className="relative z-10 mx-auto w-full max-w-[1320px] px-4 pb-24 pt-6 text-center sm:px-8">
      <h2 className="text-[32px] font-light sm:text-[44px]">
        See it <span className="text-gradient italic">solve</span>, not just reply.
      </h2>
      <Link
        href="/signup"
        className="btn-primary anim-pulse-cta mt-8 inline-flex items-center gap-3 rounded-full px-10 py-4 text-[18px] font-medium"
      >
        Get started free <ArrowRight className="h-5 w-5" />
      </Link>
    </Reveal>
  );
}

export function Footer() {
  return (
    <footer className="relative z-10 mx-auto flex w-full max-w-[1320px] flex-col items-center justify-between gap-4 border-t border-line px-4 py-8 text-[14px] text-text-300 sm:flex-row sm:px-8">
      <Logo />
      <span>More than answers: real solutions. Built for a hackathon.</span>
    </footer>
  );
}
