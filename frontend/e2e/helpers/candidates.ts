import { expect, type APIRequestContext } from "@playwright/test";

import type { CandidateDetail, RecommendationStatus } from "../../src/types";

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
        phone: "+77010000000",
        telegram: "@e2e_candidate",
      },
      academic: {
        selected_program: "Innovative IT Product Design and Development",
        language_exam_type: "IELTS",
        language_score: 6.5,
      },
      content: {
        essay_text:
          "I led a student design club, organized project teams, learned from setbacks, and want to build digital products that improve access to education.",
        project_descriptions: [
          "Built a mentoring tracker for new students and coordinated a three-person product team.",
        ],
        experience_summary:
          "Led school initiatives, coordinated volunteers, and documented project outcomes.",
      },
      internal_test: { answers: [] },
    },
  };
}

export async function submitCandidate(
  request: APIRequestContext,
  payload: Record<string, unknown>,
): Promise<CandidateDetail> {
  const response = await request.post("/api/backend/pipeline/submit-async", {
    data: payload,
  });
  const body = await response.json();

  expect(response.ok(), JSON.stringify(body)).toBeTruthy();
  expect(body.success).toBe(true);
  const candidateId = body.data.candidate_id as string;

  const startedAt = Date.now();
  while (Date.now() - startedAt < 180000) {
    const statusResponse = await request.get(
      `/api/backend/pipeline/candidates/${candidateId}/status`,
    );
    const statusBody = await statusResponse.json();

    expect(statusResponse.ok(), JSON.stringify(statusBody)).toBeTruthy();
    expect(statusBody.success).toBe(true);

    const pipelineStatus = statusBody.data.pipeline_status as string;
    if (pipelineStatus === "completed") {
      const detailResponse = await request.get(
        `/api/backend/dashboard/candidates/${candidateId}`,
      );
      const detailBody = await detailResponse.json();
      expect(detailResponse.ok(), JSON.stringify(detailBody)).toBeTruthy();
      expect(detailBody.success).toBe(true);
      return detailBody.data as CandidateDetail;
    }

    if (pipelineStatus === "failed" || pipelineStatus === "requires_manual_review") {
      throw new Error(`Candidate processing finished with status: ${pipelineStatus}`);
    }

    await new Promise((resolve) => setTimeout(resolve, 1500));
  }

  throw new Error("Timed out while waiting for asynchronous candidate processing.");
}

export function chooseShortlistOverrideStatus(
  currentStatus: RecommendationStatus,
): RecommendationStatus {
  if (currentStatus === "STRONG_RECOMMEND") {
    return "RECOMMEND";
  }

  return "STRONG_RECOMMEND";
}
