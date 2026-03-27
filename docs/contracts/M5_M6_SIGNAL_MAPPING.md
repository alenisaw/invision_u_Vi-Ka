# M5 -> M6 Signal Mapping

## Purpose

This table tells NLP exactly how each signal is consumed by `M6`.

## Core scoring signals

| Signal name | Required | M6 target | Role |
|---|---|---|---|
| `leadership_indicators` | yes | `leadership_potential` | core score |
| `team_leadership` | no | `leadership_potential` | core score |
| `growth_trajectory` | yes | `growth_trajectory` | core score |
| `challenges_overcome` | no | `growth_trajectory` | core score |
| `motivation_clarity` | yes | `motivation_clarity` | core score |
| `goal_specificity` | no | `motivation_clarity` | core score |
| `agency_signals` | yes | `initiative_agency` | core score |
| `self_started_projects` | no | `initiative_agency` | core score |
| `proactivity_examples` | no | `initiative_agency` | core score |
| `learning_agility` | yes | `learning_agility` | core score |
| `clarity_score` | yes | `communication_clarity` | core score |
| `structure_score` | no | `communication_clarity` | core score |
| `idea_articulation` | no | `communication_clarity` | core score |
| `ethical_reasoning` | yes | `ethical_reasoning` | core score |
| `civic_orientation` | no | `ethical_reasoning` | core score |
| `program_alignment` | yes | `program_fit` | core score |

## Modifier and flag signals

| Signal name | Required | M6 target | Role |
|---|---|---|---|
| `essay_transcript_consistency` | no | confidence | caution / confidence modifier |
| `claims_evidence_match` | no | confidence | caution / confidence modifier |
| `ai_writing_risk` | no | flags | caution / manual review input |
| `voice_consistency` | no | confidence | confidence modifier |
| `specificity_score` | no | confidence | confidence modifier |

## Internal sub-score weighting

These are the current within-subscore weights used by `M6`.

| Sub-score | Signal weights |
|---|---|
| `leadership_potential` | `leadership_indicators 0.6`, `team_leadership 0.4` |
| `growth_trajectory` | `growth_trajectory 0.6`, `challenges_overcome 0.4` |
| `motivation_clarity` | `motivation_clarity 0.6`, `goal_specificity 0.4` |
| `initiative_agency` | `agency_signals 0.4`, `self_started_projects 0.3`, `proactivity_examples 0.3` |
| `learning_agility` | `learning_agility 1.0` |
| `communication_clarity` | `clarity_score 0.4`, `structure_score 0.3`, `idea_articulation 0.3` |
| `ethical_reasoning` | `ethical_reasoning 0.7`, `civic_orientation 0.3` |
| `program_fit` | `program_alignment 1.0` |

## Recommendation logic summary

- `M6` computes the eight sub-scores first
- then computes `baseline_rpi`
- then blends baseline with ML refinement
- then applies completeness penalty
- then assigns `recommendation_status`
- low quality or conflicting inputs can end up in `MANUAL_REVIEW`
