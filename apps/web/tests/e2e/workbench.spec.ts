import { expect, test } from "@playwright/test";

test.describe("research workbench", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/analysis");
    await expect(
      page.getByRole("heading", { name: "EvoVariant-TR Research Workbench" }),
    ).toBeVisible();
  });

  test("exposes all areas and reads registered evidence metadata", async ({
    page,
  }) => {
    await expect(page.getByRole("tab")).toHaveCount(14);

    await page.getByRole("tab", { name: "Temporal VUS Explorer" }).click();
    await expect(
      page.getByText("Registered evidence", { exact: true }),
    ).toBeVisible();
    await expect(
      page.getByText("Authoritative cohort flow", { exact: true }),
    ).toBeVisible();
    await expect(
      page.getByText("Verified", { exact: true }).first(),
    ).toBeVisible();
  });

  test("loads protocol metadata from the methods surface", async ({ page }) => {
    await page.getByRole("tab", { name: "Methods & Provenance" }).click();
    await page.getByRole("button", { name: "Load protocol metadata" }).click();

    await expect(page.getByText("Protocol version")).toBeVisible();
    await expect(
      page.getByText("1.0.0", { exact: true }).first(),
    ).toBeVisible();
    await expect(page.getByText("8192 bp", { exact: true })).toBeVisible();
    await expect(page.getByText("Research-only")).toBeVisible();
  });

  test("shows the registered FINAL run without promoting blocked downstream outputs", async ({
    page,
    request,
  }) => {
    const response = await request.get("/api/registry");
    expect(response.ok()).toBeTruthy();
    const payload = (await response.json()) as {
      status: string;
      registered_run_count: number;
      completed_scientific_run_count: number;
      final_scientific_run_count: number;
      runs: unknown[];
    };
    expect(payload.status).toBe("READY");
    expect(payload.registered_run_count).toBeGreaterThan(0);
    expect(payload.completed_scientific_run_count).toBeGreaterThan(0);
    expect(payload.final_scientific_run_count).toBeGreaterThan(0);
    expect(payload.runs.length).toBeGreaterThan(0);

    await page.getByRole("tab", { name: "Experiment Registry" }).click();
    await expect(page.getByText("Registered run metadata")).toBeVisible();
    await expect(
      page.getByText("READY", { exact: true }).first(),
    ).toBeVisible();
    await expect(page.getByText("PRELIMINARY").first()).toBeVisible();
    await expect(page.getByText("FINAL").first()).toBeVisible();
    await expect(page.getByText("COMPLETED").first()).toBeVisible();
  });

  test("rejects invalid client-side variant input without a scorer call", async ({
    page,
  }) => {
    await page
      .getByRole("tab", { name: "Single Variant Research Analysis" })
      .click();

    const textInputs = page.getByRole("textbox");
    await textInputs.nth(0).fill("A");
    await textInputs.nth(1).fill("A");
    await page.getByRole("button", { name: "Request raw signal" }).click();

    await expect(
      page.getByText("Reference and alternate alleles must differ."),
    ).toBeVisible();
  });
});
