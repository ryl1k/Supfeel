import Link from "next/link";

import { Logo } from "@/components/brand/Gem";
import { ArrowRight, Bolt, Chat, Search, Shield } from "@/components/ui/icons";

const FEATURES = [
  {
    icon: <Chat />,
    title: "Understands the real problem",
    body: "“They’re uncomfortable” becomes “too narrow, a wide fit fixes it”. Supfeel asks one sharp question, never a form.",
  },
  {
    icon: <Search />,
    title: "Investigates on its own",
    body: "Orders, tracking, payments and memberships are checked automatically. No order numbers, no copy-pasting.",
  },
  {
    icon: <Bolt />,
    title: "Takes real action",
    body: "Exchanges, refunds, reships, address changes, pauses. Executed through business tools within written policy.",
  },
  {
    icon: <Shield />,
    title: "Verifies the fix",
    body: "Every action is re-checked against live system state before Supfeel says it’s done. You see the receipts.",
  },
];

const STEPS = [
  ["Understand", "Identify the underlying problem behind the message."],
  ["Investigate", "Gather facts from connected business systems."],
  ["Check policy", "Ground the decision in the company knowledge base."],
  ["Plan", "Choose the best fix and ask before anything sensitive."],
  ["Act", "Execute through tools: refunds, exchanges, reships…"],
  ["Verify", "Read back system state to confirm it actually worked."],
];

export function Features() {
  return (
    <section id="features" className="relative z-10 mx-auto w-full max-w-[1320px] scroll-mt-10 px-4 py-20 sm:px-8">
      <p className="text-[15px] uppercase tracking-[0.2em] text-lavender-300">Features</p>
      <h2 className="mt-3 max-w-[760px] text-[34px] font-light leading-tight sm:text-[46px]">
        More than answers: <span className="text-gradient italic">real solutions.</span>
      </h2>
      <div className="mt-12 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {FEATURES.map((f) => (
          <div key={f.title} className="glass rounded-[24px] p-7">
            <span className="flex h-11 w-11 items-center justify-center rounded-full border border-line text-lavender-300">
              {f.icon}
            </span>
            <h3 className="mt-5 text-[19px] font-medium">{f.title}</h3>
            <p className="mt-2 text-[15px] leading-relaxed text-text-300">{f.body}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

export function HowItWorks() {
  return (
    <section id="how-it-works" className="relative z-10 mx-auto w-full max-w-[1320px] scroll-mt-10 px-4 py-20 sm:px-8">
      <p className="text-[15px] uppercase tracking-[0.2em] text-lavender-300">How it works</p>
      <h2 className="mt-3 text-[34px] font-light leading-tight sm:text-[46px]">From message to verified fix</h2>
      <ol className="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {STEPS.map(([title, body], i) => (
          <li key={title} className="glass flex gap-5 rounded-[22px] p-6">
            <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-sapphire-600 text-[15px] font-semibold">
              {i + 1}
            </span>
            <div>
              <h3 className="text-[18px] font-medium">{title}</h3>
              <p className="mt-1 text-[15px] leading-relaxed text-text-300">{body}</p>
            </div>
          </li>
        ))}
      </ol>
    </section>
  );
}

export function About() {
  return (
    <section id="about" className="relative z-10 mx-auto w-full max-w-[1320px] scroll-mt-10 px-4 py-20 sm:px-8">
      <div className="glass grid gap-10 rounded-[28px] p-8 sm:p-12 lg:grid-cols-[1.3fr_1fr]">
        <div>
          <p className="text-[15px] uppercase tracking-[0.2em] text-lavender-300">About</p>
          <h2 className="mt-3 text-[30px] font-light leading-tight sm:text-[40px]">
            Support that takes responsibility
          </h2>
          <p className="mt-5 text-[16px] leading-relaxed text-text-300">
            Traditional support is reactive: customers explain, receive generic answers and get bounced between
            departments. Supfeel owns the outcome. It reasons with Claude, orchestrates its work as a LangGraph state
            machine, grounds every decision in written policy, and never claims a fix it hasn&apos;t verified.
          </p>
          <p className="mt-4 text-[16px] leading-relaxed text-text-300">
            The demo runs against Velora, a fictional footwear store with real (mock) orders, payments and
            memberships. Pick a customer and try to break it.
          </p>
        </div>
        <ul className="grid content-start gap-3 text-[15px]">
          {[
            ["Policy-grounded", "Decisions cite the knowledge base"],
            ["Human in the loop", "Sensitive actions need your OK"],
            ["Safe by design", "Over $200 goes to a specialist"],
            ["Transparent", "Every step and check is visible"],
          ].map(([t, d]) => (
            <li key={t} className="rounded-[16px] border border-line bg-panel-strong px-5 py-4">
              <span className="font-medium">{t}</span>
              <span className="block text-text-300">{d}</span>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}

export function FinalCta() {
  return (
    <section className="relative z-10 mx-auto w-full max-w-[1320px] px-4 pb-24 pt-6 text-center sm:px-8">
      <h2 className="text-[32px] font-light sm:text-[44px]">
        See it <span className="text-gradient italic">solve</span>, not just reply.
      </h2>
      <Link
        href="/chat"
        className="btn-primary mt-8 inline-flex items-center gap-3 rounded-full px-10 py-4 text-[18px] font-medium"
      >
        Start chatting <ArrowRight className="h-5 w-5" />
      </Link>
    </section>
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
