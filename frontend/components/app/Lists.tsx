"use client";

import { usePoll } from "@/lib/usePoll";
import { api } from "@/lib/workspace";

import { NotificationItem } from "./TicketView";
import { Card, Empty, Spinner } from "./ui";
import { TicketList } from "./Workspace";

export function AllTickets() {
  const tickets = usePoll(() => api.tickets(), "", 5000);
  return (
    <div className="space-y-5">
      <h1 className="text-[26px] font-semibold tracking-tight">Tickets</h1>
      <Card>
        <TicketList tickets={tickets.data ?? []} loading={!tickets.data} />
      </Card>
    </div>
  );
}

export function Inbox() {
  const notes = usePoll(() => api.notifications(), "", 5000);
  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-[26px] font-semibold tracking-tight">Business inbox</h1>
        <p className="mt-1 text-[14px] text-text-300">Everything Supfeel told your team: bugs found, fix PRs, CI results, actions taken, escalations. Mirrored to Telegram, Slack or Discord when configured.</p>
      </div>
      <Card>
        {!notes.data ? (
          <Spinner />
        ) : notes.data.length ? (
          <ul className="divide-y divide-line/60">
            {notes.data.map((n) => (
              <NotificationItem key={n.id} n={n} />
            ))}
          </ul>
        ) : (
          <Empty>No notifications yet.</Empty>
        )}
      </Card>
    </div>
  );
}
