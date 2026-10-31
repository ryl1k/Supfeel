import Link from "next/link";

import { ChatPreview } from "@/components/landing/ChatPreview";
import { ArrowRight } from "@/components/ui/icons";

export function Hero() {
  return (
    <section className="relative z-10 mx-auto grid w-full max-w-[1320px] items-center gap-14 px-4 pb-20 pt-8 sm:px-8 lg:grid-cols-[1.05fr_1fr] lg:gap-10 lg:pb-32 lg:pt-16">
      <div>
        <h1 className="tracking-[-0.02em]">
          <span className="anim-fade-up block text-[64px] font-semibold leading-[1.02] sm:text-[84px] lg:text-[96px]">
            Supfeel
          </span>
          <span className="anim-fade-up d-1 block text-[44px] font-light leading-[1.12] text-lavender-200 sm:text-[64px] lg:text-[80px]">
            AI support that
          </span>
          <span className="anim-fade-up d-2 block pb-2 text-[44px] font-light italic leading-[1.12] sm:text-[64px] lg:text-[80px]">
            <span className="text-shimmer">
            truly helps</span>
          </span>
        </h1>
        <p className="anim-fade-up d-3 mt-7 max-w-[520px] text-[19px] leading-relaxed sm:text-[22px]">
          An MCP server for your AI support.
          <br className="hidden sm:block" /> Keep your agent{" "}
          <span className="text-text-300">— just add us as a tool.</span>
        </p>
        <div className="anim-fade-up d-4 mt-12 flex flex-wrap items-center gap-4">
          <Link
            href="/signup"
            className="btn-primary anim-pulse-cta group inline-flex items-center gap-3 rounded-full px-10 py-4 text-[19px] font-medium"
          >
            Get started <ArrowRight className="h-5 w-5 transition-transform group-hover:translate-x-1" />
          </Link>
          <span className="text-[15px] text-text-300">$5 free credit · pay as you go · works over MCP</span>
        </div>
      </div>
      <div className="flex justify-center lg:justify-end">
        <ChatPreview />
      </div>
    </section>
  );
}
