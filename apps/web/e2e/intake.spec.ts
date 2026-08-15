import { expect, test } from "@playwright/test";

test("renders the issue intake workflow", async ({ page }) => {
  await page.route("http://localhost:8000/api/v1/runs", (route) => route.fulfill({ json: [] }));
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Investigate a GitHub issue" })).toBeVisible();
  await expect(page.getByPlaceholder("https://github.com/owner/repo/issues/123")).toBeVisible();
  await expect(page.getByRole("heading", { name: "How an investigation works" })).toBeVisible();
});

test("shows investigation progress immediately after submission", async ({ page }) => {
  let markHistoryLoaded!: () => void;
  const historyLoaded = new Promise<void>((resolve) => {
    markHistoryLoaded = resolve;
  });
  await page.route("**/api/v1/runs", async (route) => {
    await route.fulfill({ json: [] });
    markHistoryLoaded();
  });
  await page.route("**/api/v1/issues/intake", (route) =>
    route.fulfill({ status: 202, json: { id: "job-1", status: "queued", run_id: null, error: "", stage: "queued", stage_detail: "Waiting for a worker." } }),
  );
  await page.route("**/api/v1/jobs/job-1", (route) =>
    route.fulfill({ json: { id: "job-1", status: "running", run_id: null, error: "", stage: "preparing_workspace", stage_detail: "Cloning the repository into an isolated workspace." } }),
  );

  await page.goto("/");
  await historyLoaded;
  await page.getByLabel("GitHub issue URL").fill("https://github.com/acme/example/issues/42");
  await page.getByRole("button", { name: "Investigate issue" }).click();

  await expect(page.getByRole("heading", { name: "Investigating issue" })).toBeVisible();
  await expect(page.getByText("https://github.com/acme/example/issues/42")).toBeVisible();
  await expect(page.getByText("Reproduce the problem")).toBeVisible();
  await expect(page.getByText("Prepare a workspace").locator("..").locator("..")).toHaveAttribute("aria-current", "step");
});
