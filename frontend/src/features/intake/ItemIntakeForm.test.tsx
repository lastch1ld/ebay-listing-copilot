import { fireEvent, render, screen } from "@testing-library/react";
import { it, expect, vi } from "vitest";

import { ItemIntakeForm } from "./ItemIntakeForm";

function jpegFile(name = "lamp.jpg"): File {
  return new File(["fake-jpeg-bytes"], name, { type: "image/jpeg" });
}

it("uses a collaborative intake headline", () => {
  render(<ItemIntakeForm onSubmit={vi.fn()} />);

  expect(
    screen.getByRole("heading", { level: 1, name: "What are we selling?" }),
  ).toBeVisible();
});

it("presents every intake field with one sequential numbered hierarchy", () => {
  render(<ItemIntakeForm onSubmit={vi.fn()} />);

  expect(screen.getByRole("group", { name: "1 Add your photos" })).toBeVisible();
  expect(screen.getByRole("group", { name: "2 Description" })).toBeVisible();
  expect(screen.getByRole("group", { name: "3 Known defects" })).toBeVisible();
  expect(screen.getByRole("group", { name: "4 Target price" })).toBeVisible();
});

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

it("explains photo requirements and announces every selected file", () => {
  render(<ItemIntakeForm onSubmit={vi.fn()} />);

  expect(screen.getByText(/jpeg, png or webp/i)).toBeVisible();

  fireEvent.change(screen.getByLabelText("Photos"), {
    target: { files: [jpegFile("front.jpg"), jpegFile("detail.jpg")] },
  });

  expect(screen.getByText("2 photos ready")).toBeVisible();
  expect(screen.getByText("front.jpg")).toBeVisible();
  expect(screen.getByText("detail.jpg")).toBeVisible();
});
