import { BackgroundWaves } from "@/components/brand/BackgroundWaves";
import { Hero } from "@/components/landing/Hero";
import { Nav } from "@/components/landing/Nav";
import { About, Features, FinalCta, Footer, HowItWorks } from "@/components/landing/Sections";

export default function Home() {
  return (
    <div className="relative flex min-h-screen flex-col overflow-x-hidden bg-[radial-gradient(120%_90%_at_0%_0%,#0b1240_0%,#060a2b_55%)]">
      <div className="relative">
        <BackgroundWaves />
        <Nav />
        <Hero />
      </div>
      <Features />
      <HowItWorks />
      <About />
      <FinalCta />
      <Footer />
    </div>
  );
}
