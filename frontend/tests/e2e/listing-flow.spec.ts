import { expect, test } from "@playwright/test";

test("submitting the intake form creates an item", async ({ page }) => {
  await page.route("**/api/items", async (route) => {
    await route.fulfill({ status: 201, json: { item_id: "item-e2e-1" } });
  });

  await page.goto("/");
  await page.getByLabel("Description").fill("Vintage table lamp");
  await page.getByLabel("No known defects").check();
  await page.getByLabel("Target price (EUR)").fill("80.00");
  await page
    .getByLabel("Photos")
    .setInputFiles({ name: "lamp.jpg", mimeType: "image/jpeg", buffer: Buffer.from("fake") });
  await page.getByRole("button", { name: "Continue" }).click();

  await expect(page.getByRole("status")).toHaveText(/item-e2e-1/);
});

test("tracks outbound and inbound packages and reflects a simulated login refresh", async ({
  page,
}) => {
  const records: Array<Record<string, unknown>> = [];

  await page.route("**/api/tracking*", async (route) => {
    if (route.request().method() === "GET") {
      await route.fulfill({ status: 200, json: records });
      return;
    }
    const url = new URL(route.request().url());
    const record = {
      id: `rec-${records.length + 1}`,
      direction: url.searchParams.get("direction"),
      carrier: url.searchParams.get("carrier"),
      tracking_number: url.searchParams.get("tracking_number"),
      label: url.searchParams.get("label"),
      item_id: url.searchParams.get("item_id") || null,
      status: "UNKNOWN",
      last_refreshed_at: null,
    };
    records.push(record);
    await route.fulfill({ status: 201, json: { id: record.id, direction: record.direction, status: record.status } });
  });

  await page.goto("/");
  await page.getByRole("button", { name: "Tracking" }).click();

  await page.getByLabel("Carrier").fill("dhl");
  await page.getByLabel("Tracking number", { exact: true }).fill("JD0001");
  await page.getByLabel("Label").fill("Sold: lens");
  await page.getByLabel("Linked item (optional)").fill("item-e2e-1");
  await page.getByRole("button", { name: "Add tracking number" }).click();
  await expect(page.getByText("JD0001")).toBeVisible();

  await page.getByLabel("Direction").selectOption("INBOUND");
  await page.getByLabel("Carrier").fill("ups");
  await page.getByLabel("Tracking number", { exact: true }).fill("1Z999");
  await page.getByLabel("Label").fill("Replacement battery");
  await page.getByRole("button", { name: "Add tracking number" }).click();
  await expect(page.getByText("1Z999")).toBeVisible();

  // Simulate the login-triggered refresh by updating the fixture data and reloading.
  records[0].status = "IN_TRANSIT";
  records[1].status = "DELIVERED";
  await page.reload();
  await page.getByRole("button", { name: "Tracking" }).click();

  await expect(page.getByText("IN_TRANSIT")).toBeVisible();
  await expect(page.getByText("DELIVERED")).toBeVisible();
});
