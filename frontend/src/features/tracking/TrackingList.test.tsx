import { render, screen } from "@testing-library/react";
import { expect, it, vi } from "vitest";

import { TrackingList } from "./TrackingList";

it("presents outbound tracking fields with one sequential numbered hierarchy", () => {
  render(<TrackingList onAdd={vi.fn()} />);

  expect(screen.getByRole("group", { name: "1 Direction" })).toBeVisible();
  expect(screen.getByRole("group", { name: "2 Carrier" })).toBeVisible();
  expect(screen.getByRole("group", { name: "3 Tracking number" })).toBeVisible();
  expect(screen.getByRole("group", { name: "4 Label" })).toBeVisible();
  expect(screen.getByRole("group", { name: "5 Linked item" })).toBeVisible();
  expect(screen.getByLabelText("Direction")).toBeVisible();
  expect(screen.getByLabelText("Tracking number")).toBeVisible();
});
