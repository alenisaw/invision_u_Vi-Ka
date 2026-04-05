from __future__ import annotations

from collections import Counter, defaultdict
from statistics import mean
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.admin.schemas import (
    AdminUserCreateRequest,
    AdminUserResponse,
    AdminUserUpdateRequest,
    PipelineMetricsOverviewResponse,
    PipelineMetricsResponse,
    PipelineRunMetricResponse,
)
from app.modules.auth.schemas import UserResponse
from app.modules.auth.service import hash_password, normalize_email
from app.modules.storage import StorageRepository, User


class AdminService:
    def __init__(self, session: AsyncSession) -> None:
        self.repository = StorageRepository(session)

    async def list_users(self) -> list[AdminUserResponse]:
        users = await self.repository.list_users()
        return [self._to_response(user) for user in users]

    async def get_pipeline_metrics(self, *, limit: int = 200) -> PipelineMetricsResponse:
        audit_logs = await self.repository.list_audit_logs(limit=max(limit, 50))
        pipeline_logs = [log for log in audit_logs if log.action == "pipeline_completed"]

        recent_runs = [
            PipelineRunMetricResponse(
                audit_id=log.id,
                candidate_id=log.entity_id,
                recommendation_status=log.details.get("recommendation_status"),
                pipeline_quality_status=log.details.get("pipeline_quality_status", "healthy"),
                quality_flags=list(log.details.get("quality_flags") or []),
                total_latency_ms=float(log.details.get("total_latency_ms") or 0.0),
                stage_latencies_ms={
                    key: float(value)
                    for key, value in (log.details.get("stage_latencies_ms") or {}).items()
                },
                created_at=log.created_at,
                details=log.details,
            )
            for log in pipeline_logs[:limit]
        ]

        if not recent_runs:
            return PipelineMetricsResponse(
                overview=PipelineMetricsOverviewResponse(
                    total_runs=0,
                    healthy_runs=0,
                    degraded_runs=0,
                    partial_runs=0,
                    manual_review_runs=0,
                    degraded_rate=0.0,
                    manual_review_rate=0.0,
                    avg_total_latency_ms=0.0,
                    p50_total_latency_ms=0.0,
                    p95_total_latency_ms=0.0,
                ),
                recent_runs=[],
            )

        latencies = [run.total_latency_ms for run in recent_runs]
        stage_buckets: dict[str, list[float]] = defaultdict(list)
        flag_counts: Counter[str] = Counter()
        fallback_counts: Counter[str] = Counter()
        status_counts: Counter[str] = Counter(run.pipeline_quality_status for run in recent_runs)

        for run in recent_runs:
            for stage, latency in run.stage_latencies_ms.items():
                stage_buckets[stage].append(latency)
            for flag in run.quality_flags:
                flag_counts[flag] += 1
                if "fallback" in flag or flag in {"asr_processing_failed", "empty_signal_envelope"}:
                    fallback_counts[flag] += 1

        total_runs = len(recent_runs)
        degraded_runs = status_counts.get("degraded", 0)
        manual_review_runs = status_counts.get("manual_review_required", 0)
        overview = PipelineMetricsOverviewResponse(
            total_runs=total_runs,
            healthy_runs=status_counts.get("healthy", 0),
            degraded_runs=degraded_runs,
            partial_runs=status_counts.get("partial", 0),
            manual_review_runs=manual_review_runs,
            degraded_rate=round(degraded_runs / total_runs, 4),
            manual_review_rate=round(manual_review_runs / total_runs, 4),
            avg_total_latency_ms=round(mean(latencies), 2),
            p50_total_latency_ms=round(self._percentile(latencies, 0.50), 2),
            p95_total_latency_ms=round(self._percentile(latencies, 0.95), 2),
            avg_stage_latencies_ms={
                stage: round(mean(values), 2) for stage, values in stage_buckets.items()
            },
            fallback_counts=dict(sorted(fallback_counts.items())),
            quality_flag_counts=dict(sorted(flag_counts.items())),
        )
        return PipelineMetricsResponse(overview=overview, recent_runs=recent_runs)

    async def create_user(
        self,
        payload: AdminUserCreateRequest,
        *,
        actor: UserResponse,
    ) -> AdminUserResponse:
        email = normalize_email(payload.email)
        existing = await self.repository.get_user_by_email(email)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this email already exists",
            )

        user = await self.repository.create_user(
            email=email,
            full_name=payload.full_name.strip(),
            password_hash=hash_password(payload.password),
            role=payload.role,
            is_active=payload.is_active,
        )
        await self.repository.create_audit_log(
            entity_type="user",
            entity_id=user.id,
            action="user_created",
            actor=actor.email,
            details={"role": user.role, "email": user.email, "is_active": user.is_active},
        )
        await self.repository.commit()
        return self._to_response(user)

    async def update_user(
        self,
        user_id: UUID,
        payload: AdminUserUpdateRequest,
        *,
        actor: UserResponse,
    ) -> AdminUserResponse:
        user = await self.repository.get_user(user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        changed_fields: dict[str, object] = {}
        if payload.full_name is not None and payload.full_name != user.full_name:
            user.full_name = payload.full_name
            changed_fields["full_name"] = payload.full_name
        if payload.password is not None:
            user.password_hash = hash_password(payload.password)
            changed_fields["password_reset"] = True
        if payload.role is not None and payload.role != user.role:
            user.role = payload.role
            changed_fields["role"] = payload.role
        if payload.is_active is not None and payload.is_active != user.is_active:
            user.is_active = payload.is_active
            changed_fields["is_active"] = payload.is_active

        if not changed_fields:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No user changes were provided",
            )

        if actor.id == user.id and payload.is_active is False:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="You cannot deactivate your own account",
            )

        if payload.password is not None or payload.is_active is False:
            await self.repository.delete_user_sessions_for_user(user.id)

        await self.repository.create_audit_log(
            entity_type="user",
            entity_id=user.id,
            action="user_updated",
            actor=actor.email,
            details=changed_fields,
        )
        await self.repository.commit()
        return self._to_response(user)

    def _to_response(self, user: User) -> AdminUserResponse:
        return AdminUserResponse.model_validate(user)

    @staticmethod
    def _percentile(values: list[float], p: float) -> float:
        ordered = sorted(values)
        if not ordered:
            return 0.0
        if len(ordered) == 1:
            return ordered[0]
        index = (len(ordered) - 1) * p
        lower = int(index)
        upper = min(lower + 1, len(ordered) - 1)
        fraction = index - lower
        return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction
