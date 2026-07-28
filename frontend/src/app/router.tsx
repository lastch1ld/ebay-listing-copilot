import { useEffect, useState } from "react";

import { addTracking, createItem, listTracking, refreshTracking } from "../api/client";
import type { TrackingRecordDTO } from "../api/types";
import { NotificationCenter } from "../features/activity/NotificationCenter";
import { ItemIntakeForm } from "../features/intake/ItemIntakeForm";
import { ListingDashboard } from "../features/listings/ListingDashboard";
import { DraftReview } from "../features/review/DraftReview";
import { TrackingList } from "../features/tracking/TrackingList";

const ROUTES = ["intake", "review", "listings", "activity", "tracking"] as const;
type Route = (typeof ROUTES)[number];

const ROUTE_LABELS: Record<Route, string> = {
  intake: "New item",
  review: "Review",
  listings: "Listings",
  activity: "Activity",
  tracking: "Tracking",
};

function IntakeContainer() {
  const [confirmation, setConfirmation] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  return (
    <>
      <ItemIntakeForm
        onSubmit={(submission) => {
          setError(null);
          createItem({
            description: submission.description,
            defects: submission.defects,
            targetPriceCurrency: "EUR",
            targetPriceValue: submission.targetPriceValue,
            photos: submission.photos,
          })
            .then((result) => setConfirmation(result.item_id))
            .catch(() => setError("Could not create the item. Please try again."));
        }}
      />
      {confirmation && (
        <p className="status" role="status">
          Item created: {confirmation}
        </p>
      )}
      {error && (
        <p className="alert" role="alert">
          {error}
        </p>
      )}
    </>
  );
}

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
  const [route, setRoute] = useState<Route>("intake");

  return (
    <div>
      <nav className="app-nav" aria-label="Main navigation">
        {ROUTES.map((candidate) => (
          <button
            key={candidate}
            type="button"
            className="app-nav__tab"
            aria-current={route === candidate ? "page" : undefined}
            onClick={() => setRoute(candidate)}
          >
            {ROUTE_LABELS[candidate]}
          </button>
        ))}
      </nav>
      <main className="app-content">
        {route === "intake" && <IntakeContainer />}
        {route === "review" && <DraftReview draft={null} />}
        {route === "listings" && <ListingDashboard />}
        {route === "activity" && <NotificationCenter />}
        {route === "tracking" && <TrackingContainer />}
      </main>
    </div>
  );
}
