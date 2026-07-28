import { render, screen } from "@testing-library/react";
import { it, expect } from "vitest";

import type { DraftReviewData } from "../../api/types";
import { DraftReview } from "./DraftReview";

const draftFixture: DraftReviewData = {
  photos: ["https://example.invalid/lamp.jpg"],
  title: "Vintage table lamp",
  category: "Table Lamps",
  conditionDescription: "Small scratch on left side of the base",
  targetPrice: { currency: "EUR", value: "80.00" },
  recommendedPrice: { currency: "EUR", value: "95.00" },
  researchFields: [
    {
      fieldName: "Model",
      value: "Model X",
      provenance: "INFERRED",
      confidence: 0.65,
      sources: [],
    },
  ],
  shippingZones: [
    {
      zone: "NON_EU_CONTINENTAL",
      publishable: true,
      customsWarning: "Duties and customs paperwork may apply.",
      selectedPriceLabel: "€12.00",
    },
  ],
  feeEstimate: null,
  policies: { payment: "Standard", return: "30-day returns", fulfillment: "Standard shipping" },
  warnings: [],
  questions: [],
  ebayWarnings: [],
  isStale: false,
};

it("shows every consequential field before approval", () => {
  render(<DraftReview draft={draftFixture} />);
  expect(screen.getByText(/scratch on left side/i)).toBeVisible();
  expect(screen.getByText(/inferred/i)).toBeVisible();
  expect(screen.getByText(/target €80.00/i)).toBeVisible();
  expect(screen.getByText(/non-eu customs/i)).toBeVisible();
});

it("disables approval when the draft is stale", () => {
  render(<DraftReview draft={{ ...draftFixture, isStale: true }} />);
  expect(screen.getByRole("button", { name: "Approve this exact draft" })).toBeDisabled();
});
