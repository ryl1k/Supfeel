import type { Metadata } from "next";
import { Suspense } from "react";

import { Spinner } from "@/components/app/ui";
import { SupportChat } from "@/components/support/SupportChat";

export const metadata: Metadata = { title: "Support · Supfeel" };

export default function SupportPage() {
  return (
    <Suspense fallback={<Spinner />}>
      <SupportChat />
    </Suspense>
  );
}
