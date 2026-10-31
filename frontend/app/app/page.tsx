import type { Metadata } from "next";

import { Shell } from "@/components/app/Shell";
import { Workspace } from "@/components/app/Workspace";

export const metadata: Metadata = { title: "Workspace · Supfeel" };

export default function WorkspacePage() {
  return (
    <Shell>
      <Workspace />
    </Shell>
  );
}
