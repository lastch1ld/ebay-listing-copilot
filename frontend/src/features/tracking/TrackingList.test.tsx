import { render, screen } from "@testing-library/react";
import { expect, it, vi } from "vitest";

import { TrackingList } from "./TrackingList";

it("presents outbound tracking fields with one sequential numbered hierarchy", () => {
  render(<TrackingList onAdd={vi.fn()} />);

  expect(screen.getByRole("group", { name: "Step 1" })).toBeVisible();
  expect(screen.getByRole("group", { name: "Step 2" })).toBeVisible();
  expect(screen.getByRole("group", { name: "Step 3" })).toBeVisible();
  expect(screen.getByRole("group", { name: "Step 4" })).toBeVisible();
  expect(screen.getByRole("group", { name: "Step 5" })).toBeVisible();
  expect(screen.getByLabelText("Direction")).toBeVisible();
  expect(screen.getByLabelText("Tracking number")).toBeVisible();
  // The step wrapper must not repeat the field's own name: when it did, a
  // partial-match lookup for "Carrier" resolved to both the group and the
  // input, which is ambiguous for assistive tech and hard-fails Playwright.
  expect(screen.getAllByLabelText(/Carrier/)).toHaveLength(1);
});
