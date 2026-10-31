import type { Metadata } from "next";

import { Board } from "@/components/app/Board";
import { Shell } from "@/components/app/Shell";

export const metadata: Metadata = { title: "Board · Supfeel" };

export default function BoardPage() {
  return (
    <Shell>
      <Board />
    </Shell>
  );
}
