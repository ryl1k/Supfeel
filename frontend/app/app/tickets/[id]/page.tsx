import type { Metadata } from "next";
import { Suspense } from "react";

import { Shell } from "@/components/app/Shell";
import { TicketView } from "@/components/app/TicketView";
import { Spinner } from "@/components/app/ui";

export const metadata: Metadata = { title: "Ticket · Supfeel" };

export default function TicketPage() {
  return (
    <Suspense fallback={<Spinner />}>
      <Shell>
        <TicketView />
      </Shell>
    </Suspense>
  );
}
