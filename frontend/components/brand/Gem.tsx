type GemProps = { size?: number; className?: string };

/** Sapphire gem mark: logo and assistant avatar only (design-system.md: no gems elsewhere). */
export function Gem({ size = 36, className }: GemProps) {
  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img src="/gem.svg" width={size} height={size} alt="" aria-hidden className={className} />
  );
}

export function Logo() {
  return (
    <span className="flex items-center gap-3">
      <Gem size={40} />
      <span className="text-[26px] font-medium tracking-tight">Supfeel</span>
    </span>
  );
}
