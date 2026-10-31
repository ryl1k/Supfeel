import type { Metadata } from "next";

import { BackgroundWaves } from "@/components/brand/BackgroundWaves";
import { ChatApp } from "@/components/chat/ChatApp";

export const metadata: Metadata = {
  title: "Chat with Supfeel",
};

export default function ChatPage() {
  return (
    <main className="relative min-h-dvh overflow-hidden bg-[radial-gradient(120%_90%_at_0%_0%,#0b1240_0%,#060a2b_55%)]">
      <div className="opacity-70">
        <BackgroundWaves />
      </div>
      <ChatApp />
    </main>
  );
}
