import path from "node:path";
import { defineConfig, devices } from "@playwright/test";

const frontendRoot = process.cwd();
const repoRoot = path.resolve(frontendRoot, "..");

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  workers: 1,
  retries: process.env.CI ? 2 : 0,
  reporter: process.env.CI ? [["list"], ["html", { open: "never" }]] : "list",
  use: {
    baseURL: "http://127.0.0.1:3000",
    trace: "retain-on-failure",
  },
  webServer: [
    {
      command:
        "python3 -m alembic upgrade head && python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000",
      cwd: path.join(repoRoot, "backend"),
      url: "http://127.0.0.1:8000/health",
      timeout: 180_000,
      reuseExistingServer: !process.env.CI,
      env: {
        ...process.env,
        API_KEY: process.env.API_KEY ?? "test-reviewer-key",
      },
    },
    {
      command: "npm run dev -- --hostname 127.0.0.1 --port 3000",
      cwd: frontendRoot,
      url: "http://127.0.0.1:3000",
      timeout: 180_000,
      reuseExistingServer: !process.env.CI,
      env: {
        ...process.env,
        NEXT_PUBLIC_API_URL:
          process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000",
        REVIEWER_API_KEY:
          process.env.REVIEWER_API_KEY ??
          process.env.API_KEY ??
          "test-reviewer-key",
      },
    },
  ],
  projects: [
    {
      name: "chromium",
      use: {
        ...devices["Desktop Chrome"],
      },
    },
  ],
});
