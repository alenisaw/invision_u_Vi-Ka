import { expect, test, type Page } from "@playwright/test";

import {
  buildCandidatePayload,
  chooseCommitteeStatus,
  submitCandidate,
} from "./helpers/candidates";

async function loginAs(page: Page, email: string, password: string) {
  await page.goto("/login");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel(/Password|Пароль/).fill(password);
  await page.getByRole("button", { name: /Sign in|Войти/ }).click();
}

test("submits a candidate from upload and shows it in the dashboard", async ({ page }) => {
  const candidate = buildCandidatePayload("upload");

  await loginAs(page, "reviewer@invisionu.local", "333333");
  await page.goto("/upload");
  await page.getByTestId("candidate-json-input").fill(
    JSON.stringify(candidate.payload, null, 2),
  );
  await page.getByTestId("submit-candidate-button").click();

  await expect(page.getByText(/Pipeline|Готово|completed/i)).toBeVisible();
  await page.goto("/dashboard");
  await page.getByTestId("dashboard-search-input").fill(candidate.uniqueKey);
  await expect(page.locator("a", { hasText: candidate.fullName }).first()).toBeVisible();
});

test("opens a real candidate detail page from dashboard data", async ({ page, request }) => {
  const candidate = buildCandidatePayload("detail");
  const result = await submitCandidate(request, candidate.payload);

  await loginAs(page, "reviewer@invisionu.local", "333333");
  await page.goto("/dashboard");
  await page.getByTestId("dashboard-search-input").fill(candidate.uniqueKey);
  await page.locator("a", { hasText: candidate.fullName }).first().click();

  await expect(page.getByRole("heading", { name: candidate.fullName })).toBeVisible();
  await expect(page).toHaveURL(new RegExp(result.candidate_id));
});

test("records a committee recommendation and exposes it in admin audit", async ({
  page,
  request,
}) => {
  const candidate = buildCandidatePayload("committee");
  const result = await submitCandidate(request, candidate.payload);
  const targetStatus = chooseCommitteeStatus(result.score.recommendation_status);
  const comment = `Smoke committee note ${candidate.uniqueKey}`;

  await loginAs(page, "reviewer@invisionu.local", "333333");
  await page.goto(`/dashboard/${result.candidate_id}`);
  await page.getByTestId("committee-status-select").selectOption(targetStatus);
  await page.getByTestId("committee-comment-input").fill(comment);
  await page.getByTestId("submit-committee-decision-button").click();

  await expect(page.getByText(comment)).toBeVisible();

  await page.context().clearCookies();
  await loginAs(page, "admin@invisionu.local", "admin");
  await page.goto("/audit");
  await expect(page.getByText("Miras Reviewer")).toBeVisible();
  await expect(page.getByText(comment)).toBeVisible();
});
