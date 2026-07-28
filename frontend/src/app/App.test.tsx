import { render, screen } from "@testing-library/react";
import { it, expect } from "vitest";

import { App } from "./App";

it("shows the active environment", () => {
  render(<App environment="sandbox" />);
  expect(screen.getByText("Sandbox")).toBeVisible();
});
