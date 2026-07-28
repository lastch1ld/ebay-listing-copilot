import { fireEvent, render, screen } from "@testing-library/react";
import { it, expect, vi } from "vitest";

import { ItemIntakeForm } from "./ItemIntakeForm";

function jpegFile(name = "lamp.jpg"): File {
  return new File(["fake-jpeg-bytes"], name, { type: "image/jpeg" });
}

it("blocks submission without a defects acknowledgement", () => {
  const onSubmit = vi.fn();
  render(<ItemIntakeForm onSubmit={onSubmit} />);

  fireEvent.change(screen.getByLabelText("Description"), {
    target: { value: "Vintage lamp" },
  });
  fireEvent.change(screen.getByLabelText("Target price (EUR)"), {
    target: { value: "80.00" },
  });
  fireEvent.change(screen.getByLabelText("Photos"), {
    target: { files: [jpegFile()] },
  });
  fireEvent.click(screen.getByRole("button", { name: "Continue" }));

  expect(onSubmit).not.toHaveBeenCalled();
  expect(screen.getByRole("alert")).toHaveTextContent(/no known defects/i);
});

it("submits once description, defects acknowledgement, price, and a photo are provided", () => {
  const onSubmit = vi.fn();
  render(<ItemIntakeForm onSubmit={onSubmit} />);

  fireEvent.change(screen.getByLabelText("Description"), {
    target: { value: "Vintage lamp" },
  });
  fireEvent.click(screen.getByLabelText("No known defects"));
  fireEvent.change(screen.getByLabelText("Target price (EUR)"), {
    target: { value: "80.00" },
  });
  fireEvent.change(screen.getByLabelText("Photos"), {
    target: { files: [jpegFile()] },
  });
  fireEvent.click(screen.getByRole("button", { name: "Continue" }));

  expect(onSubmit).toHaveBeenCalledWith(
    expect.objectContaining({
      description: "Vintage lamp",
      defects: "No known defects",
      targetPriceValue: "80.00",
    }),
  );
});
