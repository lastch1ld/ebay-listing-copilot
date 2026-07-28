import { render, screen } from "@testing-library/react";
import { it, expect } from "vitest";

import type { ActivityEventDTO } from "../../api/types";
import { NotificationCenter } from "./NotificationCenter";

it("shows event type, listing title, status, and time without buyer data", () => {
  const events: ActivityEventDTO[] = [
    {
      eventType: "SALE",
      listingTitle: "Vintage table lamp",
      amount: "80.00",
      currency: "EUR",
      status: "FULFILLED",
      time: "2026-01-01T00:00:00Z",
      readState: "UNREAD",
    },
  ];
  render(<NotificationCenter events={events} />);
  expect(screen.getByText(/SALE/)).toBeVisible();
  expect(screen.getByText(/Vintage table lamp/)).toBeVisible();
  expect(screen.getByText(/FULFILLED/)).toBeVisible();
  expect(screen.queryByText(/@/)).not.toBeInTheDocument();
});
