import { useEffect, useState } from "react";

import { addTracking, listTracking, refreshTracking } from "../api/client";
import type { TrackingRecordDTO } from "../api/types";
import { NotificationCenter } from "../features/activity/NotificationCenter";
import { ListingDashboard } from "../features/listings/ListingDashboard";
import { DraftReview } from "../features/review/DraftReview";
import { TrackingList } from "../features/tracking/TrackingList";

const ROUTES = ["review", "listings", "activity", "tracking"] as const;
type Route = (typeof ROUTES)[number];

const ROUTE_LABELS: Record<Route, string> = {
  review: "Review",
  listings: "Listings",
  activity: "Activity",
  tracking: "Tracking",
};

function TrackingContainer() {
  const [records, setRecords] = useState<TrackingRecordDTO[]>([]);

  useEffect(() => {
    const controller = new AbortController();
    listTracking(controller.signal)
      .then(setRecords)
      .catch(() => undefined); // errors surface via a route-level state in a future pass
    return () => controller.abort();
  }, []);

  const reload = () => {
    listTracking()
      .then(setRecords)
      .catch(() => undefined);
  };

  return (
    <TrackingList
      records={records}
      onAdd={(params) => addTracking(params).then(reload)}
      onRefresh={(recordId) => refreshTracking(recordId).then(reload)}
    />
  );
}

export function AppRouter() {
  const [route, setRoute] = useState<Route>("listings");

  return (
    <div>
      <nav aria-label="Main navigation">
        {ROUTES.map((candidate) => (
          <button
            key={candidate}
            type="button"
            aria-current={route === candidate ? "page" : undefined}
            onClick={() => setRoute(candidate)}
          >
            {ROUTE_LABELS[candidate]}
          </button>
        ))}
      </nav>
      <main>
        {route === "review" && <DraftReview draft={null} />}
        {route === "listings" && <ListingDashboard />}
        {route === "activity" && <NotificationCenter />}
        {route === "tracking" && <TrackingContainer />}
      </main>
    </div>
  );
}
