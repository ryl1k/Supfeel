"use client";

import { usePoll } from "@/lib/usePoll";
import { api } from "@/lib/workspace";

import { ActivityItem } from "./Activity";
import { Card, Empty, Spinner } from "./ui";

export function Inbox() {
  const notes = usePoll(() => api.notifications(), "", 5000);
  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-[28px] font-bold tracking-tight">Business inbox</h1>
        <p className="mt-1 text-[14px] text-text-300">Everything Supfeel told your team: bugs found, fix PRs, CI results, actions taken, escalations. Mirrored to Telegram, Slack or Discord when configured.</p>
      </div>
      <Card>
        {!notes.data ? (
          <Spinner />
        ) : notes.data.length ? (
          <ul className="stagger divide-y divide-line/60">
            {notes.data.map((n) => (
              <ActivityItem key={n.id} n={n} />
            ))}
          </ul>
        ) : (
          <Empty>No notifications yet.</Empty>
        )}
      </Card>
    </div>
  );
}
