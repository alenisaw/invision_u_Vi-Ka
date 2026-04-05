"""
File: ranker.py
Purpose: Batch ranking helpers for scoring-stage candidate scores.
"""

from __future__ import annotations

from .schemas import CandidateScore


def rank_scores(scores: list[CandidateScore]) -> list[CandidateScore]:
    """Sort scores and assign ranking positions."""

    sorted_scores = sorted(
        scores,
        key=lambda score: (-score.review_priority_index, -score.confidence, str(score.candidate_id)),
    )

    ranked_scores: list[CandidateScore] = []
    for position, score in enumerate(sorted_scores, start=1):
        ranked_scores.append(score.model_copy(update={"ranking_position": position}))

    return ranked_scores

