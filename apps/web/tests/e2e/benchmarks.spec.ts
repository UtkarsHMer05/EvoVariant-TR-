import { expect, test } from "@playwright/test";

test.describe("benchmark hub", () => {
  test("loads the generated manifest and headline metrics", async ({ page, request }) => {
    const manifestResponse = await request.get("/benchmarks/benchmark-manifest.json");
    expect(manifestResponse.ok()).toBeTruthy();
    const manifest = (await manifestResponse.json()) as {
      benchmarks: Array<{ id: string }>;
      headline_cards: Array<{ id: string; value: number }>;
    };
    expect(manifest.benchmarks).toHaveLength(68);

    await page.goto("/benchmarks");
    await expect(page.getByRole("heading", { name: "EvoVariant-TR Research Benchmarks" })).toBeVisible();
    await expect(page.getByRole("link", { name: "Benchmarks" })).toBeVisible();
    await expect(page.getByText("0.9092", { exact: true })).toBeVisible();
    await expect(page.getByText("60", { exact: true }).first()).toBeVisible();
    expect(manifest.headline_cards.find((card) => card.id === "locked_n")?.value).toBe(946);
  });

  test("switches evidence tabs and renders figures", async ({ page }) => {
    await page.goto("/benchmarks");
    await page.getByRole("tab", { name: "Core Baseline" }).click();
    await expect(page.getByRole("heading", { name: "Primary frozen temporal result" })).toBeVisible();
    await expect(page.getByRole("img").first()).toBeVisible();

    await page.getByRole("tab", { name: "Evidence Quality" }).click();
    await expect(page.getByRole("heading", { name: "Evidence quality" })).toBeVisible();
    await expect(page.getByText("2 stars", { exact: true })).toBeVisible();

    await page.getByRole("tab", { name: "Temporal Difficulty" }).click();
    await expect(page.getByRole("heading", { name: "Temporal difficulty", exact: true })).toBeVisible();

    await page.getByRole("tab", { name: "Generalization" }).click();
    await expect(page.getByText("Leave-one-chromosome-out", { exact: true })).toBeVisible();

    await page.getByRole("tab", { name: "Model Disagreement" }).click();
    await expect(page.getByRole("heading", { name: "Model disagreement", exact: true })).toBeVisible();
  });

  test("keeps fine-tuning boundary and downloads visible", async ({ page }) => {
    await page.goto("/benchmarks");
    await page.getByRole("tab", { name: "Fine-Tuning Attempt" }).click();
    await expect(page.getByText("Foundation-model fine-tuning in primary result", { exact: true })).toBeVisible();
    await expect(page.getByText("Complete fine-tuned benchmark study", { exact: true })).toBeVisible();
    await expect(page.getByText("NO", { exact: true }).last()).toBeVisible();
    await expect(page.getByRole("link", { name: "encoder_update_proof.json" })).toHaveAttribute("href", "/benchmarks/downloads/encoder_update_proof.json");

    await page.getByRole("tab", { name: "Downloads" }).click();
    await expect(page.getByRole("link", { name: "Download" }).first()).toBeVisible();
    await expect(page.getByRole("link", { name: "Download" })).toHaveCount(10);
  });

  test("preserves the existing prediction workflow and mobile layout", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByText("Variant Analysis", { exact: true }).first()).toBeVisible();
    await expect(page.getByRole("link", { name: "Benchmarks" })).toBeVisible();

    await page.goto("/benchmarks");
    await page.setViewportSize({ width: 390, height: 844 });
    await expect(page.getByRole("heading", { name: "EvoVariant-TR Research Benchmarks" })).toBeVisible();
    const noHorizontalOverflow = await page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth + 1);
    expect(noHorizontalOverflow).toBeTruthy();
  });
});
