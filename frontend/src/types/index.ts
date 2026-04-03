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
  shortlist_eligible: boolean;
  review_recommendation: ReviewRecommendation;
  review_reasons: string[];
  top_strengths: string[];
  top_risks: string[];
  ranking_position: number | null;
  caution_flags: string[];
  scoring_version: string;
}


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

export interface ExplainabilityReport {
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
  shortlist_eligible: boolean;
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
  shortlist_eligible: boolean;
  ranking_position: number | null;
  top_strengths: string[];
  caution_flags: string[];
  created_at: string;
}

export interface RawCandidateContent {
  essay_text: string | null;
  video_transcript: string | null;
}

export interface CandidateDetail {
  candidate_id: string;
  name: string;
  score: CandidateScore;
  explanation: ExplainabilityReport;
  raw_content?: RawCandidateContent | null;
  audit_logs?: ReviewerAction[];
  committee_members?: CommitteeMemberStatus[];
}

export interface ReviewerAction {
  id: string;
  candidate_id: string;
  reviewer_id: string;
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

export interface AuditFeedItem {
  id: string;
  entity_type: string;
  entity_id: string | null;
  candidate_id: string | null;
  action_type: string;
  actor: string;
  reviewer_id: string | null;
  previous_status: string | null;
  new_status: string | null;
  comment: string | null;
  details: Record<string, unknown>;
  created_at: string;
}

export interface DashboardStats {
  total_candidates: number;
  shortlisted: number;
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

export interface PipelineResult {
  candidate_id: string;
  pipeline_status: string;
  score: CandidateScore;
  completeness: number;
  data_flags: string[];
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
