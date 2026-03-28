# M6 -> M7 Explainability Handoff v1

## Purpose

This document defines the handoff contract from:
- `M6. Scoring & Ranking Engine`
- to `M7. Explainability Service`

`M7` is not implemented yet.
This contract lets the future `M7` module start without changing `M6` scoring internals.

## Ownership split

- `M6` provides:
  - final score data
  - sub-scores
  - confidence and uncertainty markers
  - score contributions
  - caution flags
  - normalized signal context copied from the `M5` envelope

- `M7` should provide:
  - human-readable summary
  - top positive factors formatted for UI
  - caution block formatted for UI
  - reviewer guidance
  - final explanation payload for dashboard/API

## Canonical handoff object

```json
{
  "candidate_id": "uuid",
  "scoring_version": "m6-v1",
  "selected_program": "Инновационные цифровые продукты и сервисы",
  "program_id": "digital_products_and_services",
  "recommendation_status": "RECOMMEND",
  "review_priority_index": 0.71,
  "confidence": 0.79,
  "uncertainty_flag": false,
  "manual_review_required": false,
  "human_in_loop_required": false,
  "review_recommendation": "STANDARD_REVIEW",
  "review_reasons": [],
  "sub_scores": {
    "leadership_potential": 0.74,
    "growth_trajectory": 0.77,
    "motivation_clarity": 0.72,
    "initiative_agency": 0.69,
    "learning_agility": 0.81,
    "communication_clarity": 0.70,
    "ethical_reasoning": 0.68,
    "program_fit": 0.78
  },
  "score_breakdown": {
    "baseline_rpi": 0.70,
    "ml_rpi": 0.73,
    "blended_rpi": 0.71,
    "mean_signal_confidence": 0.82,
    "signal_coverage": 0.88,
    "completeness": 0.91,
    "model_disagreement": 0.03
  },
  "positive_factors": [
    {
      "factor": "learning_agility",
      "sub_score": "learning_agility",
      "score": 0.81,
      "score_contribution": 0.0972
    }
  ],
  "caution_flags": [
    {
      "flag": "possible_ai_use",
      "severity": "advisory",
      "reason": "derived from modifier signals or data flags"
    }
  ],
  "signal_context": {
    "learning_agility": {
      "value": 0.81,
      "confidence": 0.84,
      "source": ["essay", "internal_test_answers"],
      "evidence": ["candidate adapted quickly to a new environment"],
      "reasoning": "learning agility is explicit"
    }
  },
  "data_quality_notes": [
    "completeness=0.91",
    "signal_coverage=0.88",
    "mean_signal_confidence=0.82"
  ]
}
```

## Required fields

| Field | Required | Source | Notes |
|---|---|---|---|
| `candidate_id` | yes | M6 | stable candidate id |
| `scoring_version` | yes | M6 | scoring contract version |
| `selected_program` | yes | M6 | raw safe program label |
| `program_id` | yes | M6 | canonical program id |
| `recommendation_status` | yes | M6 | final score bucket |
| `review_priority_index` | yes | M6 | final post-penalty score |
| `confidence` | yes | M6 | compact confidence signal |
| `uncertainty_flag` | yes | M6 | manual review trigger |
| `manual_review_required` | yes | M6 | operational escalation flag |
| `human_in_loop_required` | yes | M6 | explicit HITL flag for downstream modules/UI |
| `review_recommendation` | yes | M6 | fast-track / standard / manual-review routing |
| `review_reasons` | yes | M6 | compact reviewer reasons |
| `sub_scores` | yes | M6 | eight explainable dimensions |
| `score_breakdown` | yes | M6 | score internals |
| `positive_factors` | yes | M6 | top score contributors |
| `caution_flags` | yes | M6 | normalized caution items |
| `signal_context` | yes | M5 copied by M6 | evidence and reasoning context |
| `data_quality_notes` | yes | M6 | compact notes for reviewer-facing explanation |

## What M7 should do with it

### 1. Build summary

Generate a short summary like:
- "Candidate shows strong learning agility and growth trajectory."
- "Recommendation is limited by low signal coverage and consistency concerns."

### 2. Format positive factors

Turn the top `positive_factors` into UI-ready blocks:
- human title
- short explanation
- evidence snippets from `signal_context`

### 3. Format caution flags

Turn normalized `caution_flags` into:
- title
- description
- severity
- suggested reviewer action

### 4. Build reviewer guidance

Use:
- `uncertainty_flag`
- `caution_flags`
- low-coverage or low-confidence signals

to create a short guidance string.

## Constraints

- `M7` should not alter the numeric output of `M6`
- `M7` should format and explain scores, not recompute them
- evidence must come from `signal_context`, not invented text
- if evidence is weak, `M7` should say so explicitly
