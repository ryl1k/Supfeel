import type { Metadata } from "next";

import { BillingView } from "@/components/app/BillingView";
import { Shell } from "@/components/app/Shell";

export const metadata: Metadata = { title: "Billing · Supfeel" };

export default function BillingPage() {
  return (
    <Shell>
      <BillingView />
    </Shell>
  );
}
