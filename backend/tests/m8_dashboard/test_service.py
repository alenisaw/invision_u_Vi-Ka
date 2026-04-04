from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.core.security import encrypt_json
from app.modules.auth.schemas import UserResponse
from app.modules.m8_dashboard.service import DashboardService


def _make_candidate(
    *,
    first_name: str = "Aida",
    last_name: str = "Kim",
    selected_program: str = "Innovative IT Product Design and Development",
):
    candidate_id = uuid4()
    return SimpleNamespace(
        id=candidate_id,
        selected_program=selected_program,
        created_at=datetime(2026, 3, 28, 10, 30, tzinfo=timezone.utc),
        pii_record=SimpleNamespace(
            encrypted_data=encrypt_json(
                {
                    "personal": {
                        "first_name": first_name,
                        "last_name": last_name,
                        "patronymic": "Should Not Leak",
                    }
                }
            )
        ),
        model_input_record=None,
        reviewer_actions=[],
        score_record=None,
        explanation_record=None,
    )


def _make_score(candidate, **overrides):
    defaults = {
        "candidate_id": candidate.id,
        "candidate": candidate,
        "created_at": datetime(2026, 3, 28, 11, 0, tzinfo=timezone.utc),
        "score_payload": {},
        "sub_scores": {"leadership_potential": 0.88},
        "program_id": "prog-it-design-001",
        "program_weight_profile": {"leadership_potential": 0.2},
        "review_priority_index": 0.84,
        "recommendation_status": "STRONG_RECOMMEND",
        "decision_summary": "Strong signals across the main dimensions.",
        "confidence": 0.91,
        "confidence_band": "HIGH",
        "manual_review_required": False,
        "human_in_loop_required": False,
        "uncertainty_flag": False,
        "shortlist_eligible": True,
        "review_recommendation": "FAST_TRACK_REVIEW",
        "review_reasons": ["high confidence"],
        "top_strengths": ["Leadership"],
        "top_risks": ["Limited transcript coverage"],
        "score_delta_vs_baseline": 0.06,
        "ranking_position": 2,
        "caution_flags": ["Essay mismatch"],
        "score_breakdown": {"baseline_rpi": 0.78},
        "model_family": "gbr",
        "scoring_version": "m6-v1",
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _make_explanation(candidate, **overrides):
    defaults = {
        "candidate_id": candidate.id,
        "report_payload": {},
        "scoring_version": "m6-v1",
        "program_id": "prog-it-design-001",
        "recommendation_status": "STRONG_RECOMMEND",
        "review_priority_index": 0.84,
        "confidence": 0.91,
        "manual_review_required": False,
        "human_in_loop_required": False,
        "review_recommendation": "FAST_TRACK_REVIEW",
        "summary": "Strong candidate with stable supporting evidence.",
        "positive_factors": [
            {
                "factor": "leadership_potential",
                "title": "Leadership",
                "summary": "Built and led a student initiative.",
                "score": 0.88,
                "score_contribution": 0.17,
                "evidence": [
                    {
                        "source": "essay",
                        "quote": "I led a student team of 20 peers.",
                    }
                ],
            }
        ],
        "caution_flags": [
            {
                "flag": "essay_mismatch",
                "severity": "warning",
                "title": "Essay mismatch",
                "summary": "The essay and transcript diverge on one project timeline.",
                "suggested_action": "Verify chronology during committee review.",
            }
        ],
        "data_quality_notes": ["confidence_band=HIGH"],
        "reviewer_guidance": "Fast-track review is reasonable.",
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _make_user(role: str = "admin") -> UserResponse:
    now = datetime(2026, 4, 4, 9, 0, tzinfo=timezone.utc)
    return UserResponse(
        id=uuid4(),
        email="admin@invisionu.local",
        full_name="Main Admin",
        role=role,  # type: ignore[arg-type]
        is_active=True,
        last_login_at=now,
        created_at=now,
    )


@pytest.mark.asyncio
async def test_get_stats_aggregates_dashboard_values() -> None:
    service = DashboardService(MagicMock())
    service.repository = AsyncMock()
    service.repository.list_candidates.return_value = [object(), object(), object()]
    service.repository.list_ranked_scores.return_value = [
        SimpleNamespace(
            confidence=0.9,
            manual_review_required=False,
            review_recommendation="FAST_TRACK_REVIEW",
            recommendation_status="STRONG_RECOMMEND",
        ),
        SimpleNamespace(
            confidence=0.6,
            manual_review_required=True,
            review_recommendation="REQUIRES_MANUAL_REVIEW",
            recommendation_status="WAITLIST",
        ),
    ]

    stats = await service.get_stats()

    assert stats.total_candidates == 3
    assert stats.processed == 2
    assert stats.pending_review == 1
    assert stats.avg_confidence == 0.75
    assert stats.by_status["STRONG_RECOMMEND"] == 1
    assert stats.by_status["WAITLIST"] == 1
    assert stats.by_status["RECOMMEND"] == 0


@pytest.mark.asyncio
async def test_list_candidates_decrypts_safe_display_name() -> None:
    service = DashboardService(MagicMock())
    service.repository = AsyncMock()

    candidate = _make_candidate(first_name="Aida", last_name="Kim")
    score = _make_score(candidate, recommendation_status="RECOMMEND", ranking_position=4)
    service.repository.list_ranked_scores.return_value = [score]

    items = await service.list_candidates()

    assert len(items) == 1
    assert items[0].name == "Aida Kim"
    assert "Should Not Leak" not in items[0].name
    assert items[0].selected_program == candidate.selected_program
    assert items[0].ranking_position == 4
    assert items[0].recommendation_status == "RECOMMEND"
    assert set(items[0].model_dump().keys()) == {
        "candidate_id",
        "name",
        "selected_program",
        "review_priority_index",
        "recommendation_status",
        "confidence",
        "ranking_position",
        "top_strengths",
        "caution_flags",
        "created_at",
    }


@pytest.mark.asyncio
async def test_get_candidate_detail_falls_back_to_scalar_columns_when_payloads_missing() -> None:
    service = DashboardService(MagicMock())
    service.repository = AsyncMock()

    candidate = _make_candidate(first_name="Dana", last_name="Sarsen")
    score = _make_score(
        candidate,
        score_payload={},
        recommendation_status="RECOMMEND",
        decision_summary="Solid overall profile.",
        confidence=0.81,
        review_recommendation="STANDARD_REVIEW",
    )
    explanation = _make_explanation(
        candidate,
        report_payload={},
        recommendation_status="RECOMMEND",
        summary="The candidate is promising but benefits from standard committee review.",
        review_recommendation="STANDARD_REVIEW",
        confidence=0.81,
        review_priority_index=0.84,
    )
    candidate.score_record = score
    candidate.explanation_record = explanation
    service.repository.get_candidate_with_related.return_value = candidate

    detail = await service.get_candidate_detail(candidate.id, _make_user())

    assert detail.candidate_id == candidate.id
    assert detail.name == "Dana Sarsen"
    assert detail.score.selected_program == candidate.selected_program
    assert detail.score.decision_summary == "Solid overall profile."
    assert detail.score.recommendation_status == "RECOMMEND"
    assert detail.explanation.summary.startswith("The candidate is promising")
    assert detail.explanation.selected_program == candidate.selected_program
    assert detail.explanation.caution_blocks[0].flag == "essay_mismatch"
    assert set(detail.model_dump().keys()) == {
        "candidate_id",
        "name",
        "score",
        "explanation",
        "raw_content",
        "audit_logs",
        "committee_members",
        "committee_resolution",
    }
