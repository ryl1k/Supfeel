import type { Metadata } from "next";

import { Shell } from "@/components/app/Shell";
import { Welcome } from "@/components/app/Welcome";

export const metadata: Metadata = { title: "Set up · Supfeel" };

export default function WelcomePage() {
  return (
    <Shell>
      <Welcome />
    </Shell>
  );
}
