import type { ActivityEventDTO } from "../../api/types";

export function NotificationCenter({
  events = [],
  onMarkRead,
}: {
  events?: ActivityEventDTO[];
  onMarkRead?: (index: number) => void;
}) {
  if (events.length === 0) {
    return <p>No activity yet.</p>;
  }

  return (
    <section aria-label="Notifications">
      <h1>Activity</h1>
      <ul>
        {events.map((event, index) => (
          <li key={`${event.eventType}-${event.time}-${index}`}>
            <strong>{event.eventType}</strong> — {event.listingTitle} — {event.status}
            {event.amount && event.currency && (
              <>
                {" "}
                ({event.currency} {event.amount})
              </>
            )}
            {" — "}
            {event.time}
            {event.readState === "UNREAD" && (
              <button type="button" onClick={() => onMarkRead?.(index)}>
                Mark read
              </button>
            )}
          </li>
        ))}
      </ul>
    </section>
  );
}
