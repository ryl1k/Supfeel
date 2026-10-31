import type { Metadata } from "next";

import { AllTickets } from "@/components/app/Lists";
import { Shell } from "@/components/app/Shell";

export const metadata: Metadata = { title: "Tickets · Supfeel" };

export default function TicketsPage() {
  return (
    <Shell>
      <AllTickets />
    </Shell>
  );
}
