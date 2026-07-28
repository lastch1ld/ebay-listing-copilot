import { render, screen } from "@testing-library/react";
import { it, expect } from "vitest";

import type { ListingSummary } from "../../api/types";
import { ListingDashboard } from "./ListingDashboard";

it("shows local/eBay state, last sync, and the listing URL", () => {
  const listings: ListingSummary[] = [
    {
      itemId: "item-1",
      state: "LIVE",
      offerId: "offer-1",
      listingId: "listing-1",
      listingUrl: "https://www.ebay.it/itm/listing-1",
      lastSyncedAt: "2026-01-01T00:00:00Z",
    },
  ];
  render(<ListingDashboard listings={listings} />);
  expect(screen.getByText("LIVE")).toBeVisible();
  expect(screen.getByRole("link", { name: "listing-1" })).toHaveAttribute(
    "href",
    "https://www.ebay.it/itm/listing-1",
  );
  expect(screen.getByText("2026-01-01T00:00:00Z")).toBeVisible();
});
