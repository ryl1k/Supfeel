/** Large soft sapphire→indigo waves sweeping from the top-right and bottom (landing mock).
 *  The layer extends below its container and fades out, so sections below blend in. */
export function BackgroundWaves() {
  return (
    <div
      aria-hidden
      className="pointer-events-none absolute inset-x-0 top-0 h-[calc(100%+220px)] overflow-hidden [mask-image:linear-gradient(to_bottom,black_70%,transparent)]"
    >
      <svg className="absolute inset-0 h-full w-full" viewBox="0 0 1440 1000" preserveAspectRatio="xMidYMid slice">
        <defs>
          <linearGradient id="w-top" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stopColor="#4D5BF2" stopOpacity="0.75" />
            <stop offset="1" stopColor="#2F3FE0" stopOpacity="0.25" />
          </linearGradient>
          <linearGradient id="w-band" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0" stopColor="#2F3FE0" stopOpacity="0" />
            <stop offset="0.5" stopColor="#3D4BE8" stopOpacity="0.45" />
            <stop offset="1" stopColor="#6B6FF2" stopOpacity="0.7" />
          </linearGradient>
          <linearGradient id="w-bottom" x1="0" y1="1" x2="1" y2="0">
            <stop offset="0" stopColor="#5560F0" stopOpacity="0.65" />
            <stop offset="0.6" stopColor="#3442E4" stopOpacity="0.35" />
            <stop offset="1" stopColor="#2F3FE0" stopOpacity="0" />
          </linearGradient>
          <filter id="soft" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="14" />
          </filter>
        </defs>
        {/* top-right sweep */}
        <path d="M1040 -20 C 980 150, 1120 300, 1460 330 L 1460 -20 Z" fill="url(#w-top)" filter="url(#soft)" />
        {/* diagonal band through the chat window area */}
        <path
          d="M560 180 C 760 300, 900 520, 1460 470 L 1460 640 C 1000 700, 760 520, 560 180 Z"
          fill="url(#w-band)"
          filter="url(#soft)"
        />
        {/* bottom wave */}
        <path
          d="M-40 1000 C 200 860, 460 780, 760 800 C 1040 820, 1240 720, 1460 640 L 1460 1000 Z"
          fill="url(#w-bottom)"
          filter="url(#soft)"
        />
        <path
          d="M420 1000 C 700 900, 1000 900, 1460 760 L 1460 1000 Z"
          fill="#6B6FF2"
          fillOpacity="0.28"
          filter="url(#soft)"
        />
      </svg>
    </div>
  );
}
