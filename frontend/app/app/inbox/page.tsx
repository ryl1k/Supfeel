import type { Metadata } from "next";

import { Inbox } from "@/components/app/Lists";
import { Shell } from "@/components/app/Shell";

export const metadata: Metadata = { title: "Inbox · Supfeel" };

export default function InboxPage() {
  return (
    <Shell>
      <Inbox />
    </Shell>
  );
}
