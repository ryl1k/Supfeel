import Link from "next/link";

import { Logo } from "@/components/brand/Gem";
import { ArrowRight } from "@/components/ui/icons";

const LINKS = [
  { href: "#features", label: "Features" },
  { href: "#about", label: "About" },
  { href: "#how-it-works", label: "How it works" },
  { href: "#pricing", label: "Pricing" },
];

export function Nav() {
  return (
    <header className="relative z-10 mx-auto flex w-full max-w-[1320px] items-center justify-between px-4 py-6 sm:px-8 lg:py-9">
      <Link href="/" aria-label="Supfeel home">
        <Logo />
      </Link>
      <nav className="hidden items-center gap-14 text-[17px] text-text-300 md:flex">
        {LINKS.map((l) => (
          <a key={l.href} href={l.href} className="transition-colors hover:text-text-100">
            {l.label}
          </a>
        ))}
      </nav>
      <Link
        href="/app"
        className="flex items-center gap-2 rounded-full border border-line px-5 py-2.5 text-[15px] transition-colors hover:border-lavender-300/60 sm:px-7 sm:py-3 sm:text-[17px]"
      >
        Open workspace <ArrowRight />
      </Link>
    </header>
  );
}
