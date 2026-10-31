import Link from "next/link";

import { ChatPreview } from "@/components/landing/ChatPreview";
import { ArrowRight } from "@/components/ui/icons";

export function Hero() {
  return (
    <section className="relative z-10 mx-auto grid w-full max-w-[1320px] items-center gap-14 px-4 pb-20 pt-8 sm:px-8 lg:grid-cols-[1.05fr_1fr] lg:gap-10 lg:pb-32 lg:pt-16">
      <div>
        <h1 className="tracking-[-0.02em]">
          <span className="block text-[64px] font-semibold leading-[1.02] sm:text-[84px] lg:text-[96px]">
            Supfeel
          </span>
          <span className="block text-[44px] font-light leading-[1.12] text-lavender-200 sm:text-[64px] lg:text-[80px]">
            AI support that
          </span>
          <span className="text-gradient block pb-2 text-[44px] font-light italic leading-[1.12] sm:text-[64px] lg:text-[80px]">
            truly helps
          </span>
        </h1>
        <p className="mt-7 max-w-[520px] text-[19px] leading-relaxed sm:text-[22px]">
          Understand your problem, <span className="text-text-300">take action,</span>
          <br className="hidden sm:block" /> and get real solutions{" "}
          <span className="text-text-300">— not just answers.</span>
        </p>
        <div className="mt-12 flex flex-wrap items-center gap-4">
          <Link
            href="/signup"
            className="btn-primary inline-flex items-center gap-3 rounded-full px-10 py-4 text-[19px] font-medium"
          >
            Get started <ArrowRight className="h-5 w-5" />
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
