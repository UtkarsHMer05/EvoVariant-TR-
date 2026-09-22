import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/e2e",
  testMatch: "**/*.spec.ts",
  fullyParallel: true,
  reporter: "list",
  use: {
    baseURL: "http://127.0.0.1:3100",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  webServer: {
    command:
      "NEXT_PUBLIC_ANALYZE_SINGLE_VARIANT_BASE_URL=http://127.0.0.1:8000 npm run start -- -p 3100",
    url: "http://127.0.0.1:3100/analysis",
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
});
