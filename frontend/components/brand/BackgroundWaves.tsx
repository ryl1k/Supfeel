/** Large soft sapphire→indigo waves sweeping from the top-right and bottom (landing mock). */
export function BackgroundWaves() {
  return (
    <div aria-hidden className="pointer-events-none absolute inset-0 overflow-hidden">
      <svg
        className="absolute inset-0 h-full w-full"
        viewBox="0 0 1440 900"
        preserveAspectRatio="xMidYMid slice"
      >
        <defs>
          <linearGradient id="w1" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stopColor="#4353F0" stopOpacity="0.55" />
            <stop offset="1" stopColor="#2F3FE0" stopOpacity="0.15" />
          </linearGradient>
          <linearGradient id="w2" x1="0" y1="1" x2="1" y2="0">
            <stop offset="0" stopColor="#6B6FF2" stopOpacity="0.5" />
            <stop offset="1" stopColor="#4353F0" stopOpacity="0.05" />
          </linearGradient>
          <filter id="soft" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="18" />
          </filter>
        </defs>
        <path
          d="M1120 -40 C 1000 140, 1180 300, 1460 260 L 1460 -40 Z"
          fill="url(#w1)"
          filter="url(#soft)"
        />
        <path
          d="M760 900 C 900 640, 1180 560, 1460 420 L 1460 900 Z"
          fill="url(#w2)"
          filter="url(#soft)"
        />
        <path
          d="M-40 900 C 240 780, 520 800, 820 900 Z"
          fill="url(#w2)"
          opacity="0.6"
          filter="url(#soft)"
        />
        <path
          d="M640 300 C 760 520, 980 640, 1460 560"
          stroke="#6B6FF2"
          strokeOpacity="0.18"
          strokeWidth="80"
          fill="none"
          filter="url(#soft)"
        />
      </svg>
    </div>
  );
}
