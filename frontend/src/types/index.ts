export type RecommendationStatus =
  | "STRONG_RECOMMEND"
  | "RECOMMEND"
  | "REVIEW_NEEDED"
  | "LOW_SIGNAL"
  | "MANUAL_REVIEW";

export type ReviewRecommendation =
  | "FAST_TRACK_REVIEW"
  | "STANDARD_REVIEW"
  | "REQUIRES_MANUAL_REVIEW";

export interface SubScores {
  leadership_potential: number;
  growth_trajectory: number;
  motivation_clarity: number;
  initiative_agency: number;
  learning_agility: number;
  communication_clarity: number;
  ethical_reasoning: number;
  program_fit: number;
}

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

export interface CandidateDetail {
  score: CandidateScore;
  explanation: ExplainabilityReport;
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
