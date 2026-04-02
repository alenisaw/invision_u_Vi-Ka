export type RecommendationStatus =
  | "STRONG_RECOMMEND"
  | "RECOMMEND"
  | "WAITLIST"
  | "DECLINED";

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

export interface RawCandidateContent {
  essay_text: string | null;
  video_transcript: string | null;
  project_descriptions: string[];
  experience_summary: string | null;
}

export interface CandidateDetail {
  candidate_id: string;
  name: string;
  score: CandidateScore;
  explanation: ExplainabilityReport;
  raw_content?: RawCandidateContent | null;
  audit_logs?: ReviewerAction[];
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

export interface PipelineStageRun {
  id: string;
  stage_name: string;
  status: string;
  attempt_count: number;
  started_at: string | null;
  finished_at: string | null;
  duration_ms: number | null;
  error_code: string | null;
  error_message: string | null;
  output_ref: Record<string, unknown> | null;
  created_at: string;
}

export interface PipelineJobEvent {
  id: string;
  event_type: string;
  stage_name: string | null;
  status: string | null;
  payload: Record<string, unknown>;
  created_at: string;
}

export interface PipelineJobStatus {
  job_id: string;
  candidate_id: string;
  job_type: string;
  status: string;
  current_stage: string | null;
  requested_by: string;
  execution_mode: string;
  attempt_count: number;
  error_code: string | null;
  error_message: string | null;
  queued_at: string;
  started_at: string | null;
  finished_at: string | null;
  payload_schema_version: string | null;
  stage_runs: PipelineStageRun[];
}

export interface AsyncPipelineSubmitResponse {
  candidate_id: string;
  job_id: string;
  pipeline_status: string;
  job_status: string;
  current_stage: string | null;
  message: string;
}

export interface CandidatePipelineStatus {
  candidate_id: string;
  pipeline_status: string;
  selected_program: string | null;
  latest_job: PipelineJobStatus | null;
}

export interface FixtureMeta {
  slug: string;
  display_name: string;
  program: string;
  language: string;
  essay_preview: string;
}

export interface FixtureSummary {
  meta: FixtureMeta;
}

export interface FixtureDetail {
  meta: FixtureMeta;
  payload: Record<string, unknown>;
}
