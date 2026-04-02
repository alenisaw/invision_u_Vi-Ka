import type {
  ApiResponse,
  AuditFeedItem,
  CandidateDetail,
  CandidateListItem,
  DashboardStats,
  FixtureDetail,
  FixtureSummary,
  PipelineResult,
  RecommendationStatus,
  ReviewerAction,
} from "@/types";

export class ApiError extends Error {
  status: number;
  code?: string;
  details?: Record<string, unknown>;

  constructor(
    message: string,
    status: number,
    code?: string,
    details?: Record<string, unknown>,
  ) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers ?? {}),
    },
    ...options,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => null);
    const message = body?.error?.message ?? `API error ${res.status}`;
    throw new ApiError(message, res.status, body?.error?.code, body?.error?.details);
  }

  const envelope: ApiResponse<T> = await res.json();
  if (!envelope.success) {
    throw new ApiError(
      envelope.error?.message ?? "Unknown API error",
      res.status,
      envelope.error?.code,
      envelope.error?.details,
    );
  }

  return envelope.data;
}

export const api = {
  get: <T>(path: string) => request<T>(path),

  post: <T>(path: string, body: unknown) =>
    request<T>(path, { method: "POST", body: JSON.stringify(body) }),
};

export const reviewerApi = {
  getDashboardStats: () => api.get<DashboardStats>("/api/backend/dashboard/stats"),
  listDashboardCandidates: () =>
    api.get<CandidateListItem[]>("/api/backend/dashboard/candidates"),
  getCandidateDetail: (candidateId: string) =>
    api.get<CandidateDetail>(`/api/backend/dashboard/candidates/${candidateId}`),
  overrideCandidateDecision: (
    candidateId: string,
    body: {
      reviewer_id: string;
      new_status: RecommendationStatus;
      comment: string;
    },
  ) =>
    api.post<ReviewerAction>(
      `/api/backend/dashboard/candidates/${candidateId}/override`,
      body,
    ),
  listShortlist: () => api.get<CandidateListItem[]>("/api/backend/dashboard/shortlist"),
  listAuditFeed: (limit = 100) =>
    api.get<AuditFeedItem[]>(`/api/backend/audit/feed?limit=${limit}`),
};

export const pipelineApi = {
  submitCandidate: (body: unknown) =>
    api.post<PipelineResult>("/api/backend/pipeline/submit", body),
};

export const demoApi = {
  listFixtures: () =>
    api.get<FixtureSummary[]>("/api/backend/demo/candidates"),
  getFixture: (slug: string) =>
    api.get<FixtureDetail>(`/api/backend/demo/candidates/${slug}`),
  runFixture: (slug: string) =>
    api.post<PipelineResult>(`/api/backend/demo/candidates/${slug}/run`, {}),
};
