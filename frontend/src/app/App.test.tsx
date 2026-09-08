import { render, screen } from "@testing-library/react";
import { it, expect } from "vitest";

import { App } from "./App";

it("shows the active environment", () => {
  const { container } = render(<App environment="sandbox" />);

  expect(screen.getByText("Listing Copilot")).toBeVisible();
  expect(screen.getByText("Sandbox")).toBeVisible();
  expect(screen.queryByText("Seller workspace")).not.toBeInTheDocument();
  expect(container.querySelector(".brand-mark")).not.toBeInTheDocument();
  expect(screen.getByLabelText("Active environment")).toHaveTextContent("Sandbox");
});
