import type { Metadata } from "next";
import { Suspense } from "react";

import { RepoView } from "@/components/app/RepoView";
import { Shell } from "@/components/app/Shell";
import { Spinner } from "@/components/app/ui";

export const metadata: Metadata = { title: "Repository · Supfeel" };

export default function RepoPage() {
  return (
    <Suspense fallback={<Spinner />}>
      <Shell>
        <RepoView />
      </Shell>
    </Suspense>
  );
}
