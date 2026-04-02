import { expect, type APIRequestContext } from "@playwright/test";

import type { PipelineResult, RecommendationStatus } from "../../src/types";

export interface TestCandidateFixture {
  payload: Record<string, unknown>;
  fullName: string;
  uniqueKey: string;
}

export function buildCandidatePayload(prefix: string): TestCandidateFixture {
  const uniqueKey = `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
  const firstName = "E2E";
  const lastName = `Candidate-${uniqueKey}`;

  return {
    uniqueKey,
    fullName: `${firstName} ${lastName}`,
    payload: {
      personal: {
        first_name: firstName,
        last_name: lastName,
        date_of_birth: "2007-06-15",
      },
      contacts: {
        email: `${uniqueKey}@example.com`,
        phone: "+77010000000",
        telegram: "@e2e_candidate",
      },
      academic: {
        selected_program: "Innovative IT Product Design and Development",
        language_exam_type: "IELTS",
        language_score: 6.5,
      },
      content: {
        video_url: `https://example.com/interview/${uniqueKey}`,
        essay_text:
          "I led a student design club, organized project teams, learned from setbacks, and want to build digital products that improve access to education.",
      },
      internal_test: { answers: [] },
    },
  };
}

export async function submitCandidate(
  request: APIRequestContext,
  payload: Record<string, unknown>,
): Promise<PipelineResult> {
  const response = await request.post("/api/backend/pipeline/submit", {
    data: payload,
  });
  const body = await response.json();

  expect(response.ok(), JSON.stringify(body)).toBeTruthy();
  expect(body.success).toBe(true);

  return body.data as PipelineResult;
}

export function chooseShortlistOverrideStatus(
  currentStatus: RecommendationStatus,
): RecommendationStatus {
  if (currentStatus === "STRONG_RECOMMEND") {
    return "RECOMMEND";
  }

  return "STRONG_RECOMMEND";
}
