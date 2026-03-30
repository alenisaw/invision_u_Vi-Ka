import { expect, test } from "@playwright/test";

import {
  buildCandidatePayload,
  chooseShortlistOverrideStatus,
  submitCandidate,
} from "./helpers/candidates";

test("submits a candidate from upload and shows it in the dashboard", async ({
  page,
}) => {
  const candidate = buildCandidatePayload("upload");

  await page.goto("/upload");
  await page.getByTestId("candidate-json-input").fill(
    JSON.stringify(candidate.payload, null, 2),
  );
  await page.getByTestId("submit-candidate-button").click();

  await expect(page.getByText("Пайплайн завершён", { exact: false })).toBeVisible();
  await page.getByRole("link", { name: "Перейти в рейтинг" }).click();

  await page.getByTestId("dashboard-search-input").fill(candidate.uniqueKey);
  await expect(page.locator("a", { hasText: candidate.fullName }).first()).toBeVisible();
});

test("opens a real candidate detail page from dashboard data", async ({
  page,
  request,
}) => {
  const candidate = buildCandidatePayload("detail");
  const result = await submitCandidate(request, candidate.payload);

  await page.goto("/dashboard");
  await page.getByTestId("dashboard-search-input").fill(candidate.uniqueKey);
  await page.locator("a", { hasText: candidate.fullName }).first().click();

  await expect(
    page.getByRole("heading", { name: candidate.fullName }),
  ).toBeVisible();
  await expect(page.getByText("Заключение ИИ")).toBeVisible();
  await expect(page.getByText("Профиль оценок")).toBeVisible();
  await expect(page).toHaveURL(new RegExp(result.candidate_id));
});

test("creates an override and exposes it in shortlist and audit", async ({
  page,
  request,
}) => {
  const candidate = buildCandidatePayload("override");
  const result = await submitCandidate(request, candidate.payload);
  const targetStatus = chooseShortlistOverrideStatus(
    result.score.recommendation_status,
  );
  const comment = `Smoke override ${candidate.uniqueKey}`;

  await page.goto(`/dashboard/${result.candidate_id}`);
  await page.getByTestId("reviewer-id-input").fill("e2e-reviewer");
  await page.getByTestId("override-status-select").selectOption(targetStatus);
  await page.getByTestId("override-comment-input").fill(comment);
  await page.getByTestId("submit-override-button").click();

  await expect(
    page.getByText("Изменение сохранено в журнале", { exact: false }),
  ).toBeVisible();

  await page.goto("/shortlist");
  await expect(page.getByText(candidate.fullName)).toBeVisible();

  await page.goto("/audit");
  await expect(page.getByText("e2e-reviewer")).toBeVisible();
  await expect(page.getByText(comment)).toBeVisible();
});
