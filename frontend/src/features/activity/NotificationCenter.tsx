import type { ActivityEventDTO } from "../../api/types";

export function NotificationCenter({
  events = [],
  onMarkRead,
}: {
  events?: ActivityEventDTO[];
  onMarkRead?: (index: number) => void;
}) {
  if (events.length === 0) {
    return <p className="empty-state">No activity yet.</p>;
  }

  return (
    <section aria-label="Notifications" className="card">
      <h1>Activity</h1>
      <div className="stack" style={{ marginTop: "var(--space-4)" }}>
        {events.map((event, index) => (
          <div key={`${event.eventType}-${event.time}-${index}`}>
            <p>
              <span className="badge badge--accent">{event.eventType}</span>{" "}
              {event.listingTitle} — {event.status}
              {event.amount && event.currency && (
                <>
                  {" "}
                  ({event.currency} {event.amount})
                </>
              )}
            </p>
            <p className="section-label" style={{ marginTop: "var(--space-1)" }}>
              {event.time}
              {event.readState === "UNREAD" && (
                <button
                  type="button"
                  className="button"
                  style={{ marginLeft: "var(--space-3)" }}
                  onClick={() => onMarkRead?.(index)}
                >
                  Mark read
                </button>
              )}
            </p>
          </div>
        ))}
      </div>
    </section>
  );
}
