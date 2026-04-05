import type {
  AdminUser,
  ApiResponse,
  AuthUser,
  AuditFeedItem,
  CandidateDetail,
  CandidateListItem,
  CandidatePoolListItem,
  DashboardStats,
  FixtureDetail,
  FixtureSummary,
  PipelineResult,
  PipelineMetrics,
  RecommendationStatus,
  ReviewerAction,
  SessionInfo,
} from "@/types";
import type { Locale } from "@/lib/i18n";

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
    credentials: "same-origin",
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

  patch: <T>(path: string, body: unknown) =>
    request<T>(path, { method: "PATCH", body: JSON.stringify(body) }),
};

export const reviewerApi = {
  getDashboardStats: () => api.get<DashboardStats>("/api/backend/dashboard/stats"),
  listDashboardCandidates: () =>
    api.get<CandidateListItem[]>("/api/backend/dashboard/candidates"),
  listCandidatePool: () =>
    api.get<CandidatePoolListItem[]>("/api/backend/dashboard/candidate-pool"),
  getCandidateDetail: (candidateId: string, locale: Locale) =>
    api.get<CandidateDetail>(`/api/backend/dashboard/candidates/${candidateId}?locale=${locale}`),
  recordCandidateViewed: (candidateId: string) =>
    api.post<ReviewerAction>(`/api/backend/dashboard/candidates/${candidateId}/viewed`, {}),
  submitCommitteeDecision: (
    candidateId: string,
    body: {
      new_status: RecommendationStatus;
      comment: string;
    },
  ) => api.post<ReviewerAction>(`/api/backend/dashboard/candidates/${candidateId}/decision`, body),
  listAuditFeed: (limit = 100) =>
    api.get<AuditFeedItem[]>(`/api/backend/audit/feed?limit=${limit}`),
};

export const pipelineApi = {
  submitCandidate: (body: unknown) =>
    api.post<PipelineResult>("/api/backend/pipeline/submit", body),
};

export const authApi = {
  login: (body: { email: string; password: string }) =>
    api.post<SessionInfo>("/api/backend/auth/login", body),
  me: () => api.get<AuthUser>("/api/backend/auth/me"),
  logout: () =>
    api.post<{ logged_out: boolean; user_id: string }>("/api/backend/auth/logout", {}),
};

export const adminApi = {
  listUsers: () => api.get<AdminUser[]>("/api/backend/admin/users"),
  getPipelineMetrics: (limit = 100) =>
    api.get<PipelineMetrics>(`/api/backend/admin/metrics/pipeline?limit=${limit}`),
  createUser: (body: {
    email: string;
    full_name: string;
    password: string;
    role: "admin" | "chair" | "reviewer";
    is_active: boolean;
  }) => api.post<AdminUser>("/api/backend/admin/users", body),
  updateUser: (
    userId: string,
    body: Partial<{
      full_name: string;
      password: string;
      role: "admin" | "chair" | "reviewer";
      is_active: boolean;
    }>,
  ) => api.patch<AdminUser>(`/api/backend/admin/users/${userId}`, body),
};

export const demoApi = {
  listFixtures: () =>
    api.get<FixtureSummary[]>("/api/backend/demo/candidates"),
  getFixture: (slug: string) =>
    api.get<FixtureDetail>(`/api/backend/demo/candidates/${slug}`),
  runFixture: (slug: string) =>
    api.post<PipelineResult>(`/api/backend/demo/candidates/${slug}/run`, {}),
};
