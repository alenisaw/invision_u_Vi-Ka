export type RecommendationStatus =
  | "STRONG_RECOMMEND"
  | "RECOMMEND"
  | "WAITLIST"
  | "DECLINED";

export type UserRole = "admin" | "chair" | "reviewer";

export type ReviewRecommendation =
  | "FAST_TRACK_REVIEW"
  | "STANDARD_REVIEW"
  | "REQUIRES_MANUAL_REVIEW";

export type SubScores = Record<string, number>;

export interface CandidateScore {
  candidate_id: string;
  selected_program: string;
  program_id: string;
  sub_scores: SubScores;
  review_priority_index: number;
  recommendation_status: RecommendationStatus;
  decision_summary: string;
  confidence: number;
  confidence_band: string;
  manual_review_required: boolean;
  human_in_loop_required: boolean;
  uncertainty_flag: boolean;
  review_recommendation: ReviewRecommendation;
  review_reasons: string[];
  top_strengths: string[];
  top_risks: string[];
  ranking_position: number | null;
  caution_flags: string[];
  scoring_version: string;
}

export type PipelineQualityStatus =
  | "healthy"
  | "degraded"
  | "partial"
  | "manual_review_required";


export interface EvidenceItem {
  source: string;
  quote: string;
}

export interface FactorBlock {
  factor: string;
  title: string;
  summary: string;
  score: number;
  score_contribution: number;
  evidence: EvidenceItem[];
}

export interface CautionBlock {
  flag: string;
  severity: string;
  title: string;
  summary: string;
  suggested_action: string;
}

export interface ExplanationReport {
  candidate_id: string;
  scoring_version: string;
  selected_program: string;
  program_id: string;
  recommendation_status: RecommendationStatus;
  review_priority_index: number;
  confidence: number;
  manual_review_required: boolean;
  human_in_loop_required: boolean;
  review_recommendation: ReviewRecommendation;
  summary: string;
  positive_factors: FactorBlock[];
  caution_blocks: CautionBlock[];
  reviewer_guidance: string;
  data_quality_notes: string[];
}

export interface CandidateListItem {
  candidate_id: string;
  name: string;
  selected_program: string;
  review_priority_index: number;
  recommendation_status: RecommendationStatus;
  confidence: number;
  ranking_position: number;
  top_strengths: string[];
  caution_flags: string[];
  created_at: string;
}

export interface CandidatePoolListItem {
  candidate_id: string;
  name: string;
  selected_program: string;
  pipeline_status: string;
  stage: "processed" | "raw";
  data_completeness: number | null;
  data_flags: string[];
  review_priority_index: number | null;
  recommendation_status: RecommendationStatus | null;
  confidence: number | null;
  ranking_position: number | null;
  top_strengths: string[];
  caution_flags: string[];
  created_at: string;
}

export interface RawCandidateContent {
  essay: LocalizedTextContent | null;
  video_transcript: LocalizedTextContent | null;
}

export interface LocalizedTextContent {
  original_text: string;
  original_locale: "ru" | "en" | null;
  interface_text: string | null;
  interface_locale: "ru" | "en" | null;
}

export interface CandidateDetail {
  candidate_id: string;
  name: string;
  score: CandidateScore;
  explanation: ExplanationReport;
  raw_content?: RawCandidateContent | null;
  audit_logs?: ReviewerAction[];
  committee_members?: CommitteeMemberStatus[];
  committee_resolution?: CommitteeResolutionSummary | null;
}

export interface ReviewerAction {
  id: string;
  candidate_id: string;
  reviewer_user_id: string | null;
  reviewer_name: string;
  action_type: string;
  previous_status: string;
  new_status: string;
  comment: string;
  created_at: string;
}

export interface CommitteeMemberStatus {
  user_id: string;
  full_name: string;
  role: UserRole;
  has_viewed: boolean;
  has_recommendation: boolean;
  recommendation_status: RecommendationStatus | null;
  recommendation_comment: string | null;
  last_activity_at: string | null;
}

export interface CommitteeResolutionSummary {
  chair_user_id: string | null;
  chair_name: string;
  decision_status: RecommendationStatus;
  decision_comment: string | null;
  decided_at: string;
}

export interface AuditFeedItem {
  id: string;
  entity_type: string;
  entity_id: string | null;
  candidate_id: string | null;
  action_type: string;
  actor: string;
  reviewer_user_id: string | null;
  reviewer_name: string | null;
  previous_status: string | null;
  new_status: string | null;
  comment: string | null;
  details: Record<string, unknown>;
  created_at: string;
}

export interface DashboardStats {
  total_candidates: number;
  pending_review: number;
  processed: number;
  avg_confidence: number;
  by_status: Record<RecommendationStatus, number>;
}

export interface ApiResponse<T> {
  success: boolean;
  data: T;
  error: { code: string; message: string; details?: Record<string, unknown> } | null;
  meta: { timestamp: string; version: string };
}

export interface AuthUser {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  last_login_at: string | null;
  created_at: string;
}

export interface SessionInfo {
  user: AuthUser;
  expires_at: string;
}

export interface AdminUser extends AuthUser {}

export interface PipelineMetricsOverview {
  total_runs: number;
  healthy_runs: number;
  degraded_runs: number;
  partial_runs: number;
  manual_review_runs: number;
  degraded_rate: number;
  manual_review_rate: number;
  avg_total_latency_ms: number;
  p50_total_latency_ms: number;
  p95_total_latency_ms: number;
  avg_stage_latencies_ms: Record<string, number>;
  fallback_counts: Record<string, number>;
  quality_flag_counts: Record<string, number>;
}

export interface PipelineRunMetric {
  audit_id: string;
  candidate_id: string | null;
  recommendation_status: string | null;
  pipeline_quality_status: PipelineQualityStatus;
  quality_flags: string[];
  total_latency_ms: number;
  stage_latencies_ms: Record<string, number>;
  created_at: string;
  details: Record<string, unknown>;
}

export interface PipelineMetrics {
  overview: PipelineMetricsOverview;
  recent_runs: PipelineRunMetric[];
}

export interface PipelineResult {
  candidate_id: string;
  pipeline_status: string;
  score: CandidateScore;
  completeness: number;
  data_flags: string[];
  pipeline_quality_status?: PipelineQualityStatus;
  quality_flags?: string[];
  stage_latencies_ms?: Record<string, number>;
  total_latency_ms?: number;
}

export interface FixtureMeta {
  slug: string;
  display_name: string;
  program: string;
  language: string;
  content_preview: string;
}

export interface FixtureSummary {
  meta: FixtureMeta;
}

export interface FixtureDetail {
  meta: FixtureMeta;
  payload: Record<string, unknown>;
}
