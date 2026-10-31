import type { Metadata } from "next";

import { TicketBoard } from "@/components/app/TicketBoard";
import { Shell } from "@/components/app/Shell";

export const metadata: Metadata = { title: "Tickets · Supfeel" };

export default function TicketsPage() {
  return (
    <Shell>
      <TicketBoard />
    </Shell>
  );
}
