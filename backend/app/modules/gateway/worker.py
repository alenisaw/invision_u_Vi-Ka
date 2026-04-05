# app/modules/gateway/worker.py
"""
Background worker loop for persistent pipeline jobs.

Purpose:
- Pull queued jobs from the transport layer.
- Execute stages with retry and dead-letter policies.
"""

from __future__ import annotations

import asyncio
import logging
from uuid import UUID

from app.core.config import get_settings
from app.core.database import AsyncSessionLocal
from app.core.queue import JobQueue, get_job_queue
from app.modules.gateway.orchestrator import PipelineOrchestrator
from app.modules.storage import StorageRepository


logger = logging.getLogger(__name__)
NON_RETRYABLE_ERROR_CODES = {"insufficient_data", "missing_payload"}
STAGE_RETRY_POLICIES = {
    "asr": {
        "max_attempts": 2,
        "retryable_error_codes": {"asr_stage_failed", "asr_provider_failed"},
    },
    "nlp": {
        "max_attempts": 3,
        "retryable_error_codes": {
            "m5_processing_failed",
            "nlp_stage_failed",
            "llm_rate_limited",
            "llm_timeout",
            "llm_provider_failed",
        },
    },
    "explainability": {
        "max_attempts": 2,
        "retryable_error_codes": {"explainability_stage_failed", "m7_generation_failed"},
    },
}

# Internal queue stage codes stay stable because job records and retry history persist them.


class PipelineWorker:
    def __init__(
        self,
        job_queue: JobQueue | None = None,
        *,
        poll_timeout_seconds: int | None = None,
    ) -> None:
        self.job_queue = job_queue or get_job_queue()
        self.poll_timeout_seconds = (
            get_settings().pipeline_worker_poll_timeout_seconds
            if poll_timeout_seconds is None
            else poll_timeout_seconds
        )

    async def run_once(self) -> bool:
        await self.job_queue.promote_due_jobs()
        reserved_job_id = await self.job_queue.reserve_job(self.poll_timeout_seconds)
        if reserved_job_id is None:
            return False

        try:
            async with AsyncSessionLocal() as session:
                orchestrator = PipelineOrchestrator(session, job_queue=self.job_queue)
                job_status = await orchestrator.process_pipeline_job(UUID(reserved_job_id))
        except Exception:
            logger.exception("Worker failed while processing job %s", reserved_job_id)
            await self.job_queue.fail_job(reserved_job_id)
            return True

        if job_status.status in {"completed", "requires_manual_review"}:
            await self.job_queue.ack_job(reserved_job_id)
        elif job_status.status == "failed":
            retry_scheduled = await self._schedule_retry_if_allowed(job_status)
            if retry_scheduled:
                await self.job_queue.retry_job(
                    reserved_job_id,
                    delay_seconds=self._retry_delay_seconds(job_status),
                )
            else:
                await self._mark_dead_letter(job_status)
                await self.job_queue.fail_job(reserved_job_id)
        else:
            await self.job_queue.retry_job(reserved_job_id, delay_seconds=1)

        return True

    async def run_forever(self) -> None:
        while True:
            processed = await self.run_once()
            if not processed:
                await asyncio.sleep(0.5)

    async def _schedule_retry_if_allowed(self, job_status) -> bool:
        retry_decision = self.inspect_retry_decision(job_status)
        if not bool(retry_decision["retry_eligible"]):
            return False

        stage_name = str(retry_decision["stage_name"])
        stage_attempt_count = int(retry_decision["stage_attempt_count"])

        async with AsyncSessionLocal() as session:
            repository = StorageRepository(session)
            await repository.update_pipeline_status(UUID(job_status.candidate_id), "queued")
            await repository.update_pipeline_job(
                UUID(job_status.job_id),
                status="retry_scheduled",
                current_stage=stage_name,
                finished_at=None,
                error_code=None,
                error_message=None,
            )
            await repository.update_pipeline_stage_run(
                UUID(job_status.job_id),
                stage_name,
                status="retry_scheduled",
                finished_at=None,
                error_code=None,
                error_message=None,
                duration_ms=None,
            )
            await repository.create_pipeline_job_event(
                job_id=UUID(job_status.job_id),
                event_type="job_retry_scheduled",
                stage_name=stage_name,
                status="retry_scheduled",
                payload={
                    "attempt_count": stage_attempt_count,
                    "delay_seconds": int(retry_decision["retry_delay_seconds"]),
                    "error_code": job_status.error_code,
                    "reason": retry_decision["reason"],
                },
            )
            await repository.commit()
        return True

    def _retry_delay_seconds(self, job_status) -> int:
        attempt_count = self._get_stage_attempt_count(job_status)
        return min(60, 2 ** attempt_count)

    def inspect_retry_decision(self, job_status) -> dict[str, object]:
        stage_name = job_status.current_stage or ""
        policy = STAGE_RETRY_POLICIES.get(stage_name)
        stage_attempt_count = self._get_stage_attempt_count(job_status)
        error_code = job_status.error_code or ""

        if policy is None:
            return {
                "stage_name": stage_name,
                "stage_attempt_count": stage_attempt_count,
                "max_attempts": 0,
                "retry_eligible": False,
                "retry_delay_seconds": 0,
                "reason": "no_retry_policy",
                "error_code": error_code,
                "retryable_error_codes": [],
            }

        max_attempts = int(policy["max_attempts"])
        retryable_error_codes = sorted(set(policy["retryable_error_codes"]))
        if stage_attempt_count >= max_attempts:
            return {
                "stage_name": stage_name,
                "stage_attempt_count": stage_attempt_count,
                "max_attempts": max_attempts,
                "retry_eligible": False,
                "retry_delay_seconds": 0,
                "reason": "max_attempts_exhausted",
                "error_code": error_code,
                "retryable_error_codes": retryable_error_codes,
            }

        if error_code in NON_RETRYABLE_ERROR_CODES:
            return {
                "stage_name": stage_name,
                "stage_attempt_count": stage_attempt_count,
                "max_attempts": max_attempts,
                "retry_eligible": False,
                "retry_delay_seconds": 0,
                "reason": "non_retryable_error_code",
                "error_code": error_code,
                "retryable_error_codes": retryable_error_codes,
            }

        if error_code not in retryable_error_codes:
            return {
                "stage_name": stage_name,
                "stage_attempt_count": stage_attempt_count,
                "max_attempts": max_attempts,
                "retry_eligible": False,
                "retry_delay_seconds": 0,
                "reason": "error_code_not_retryable",
                "error_code": error_code,
                "retryable_error_codes": retryable_error_codes,
            }

        return {
            "stage_name": stage_name,
            "stage_attempt_count": stage_attempt_count,
            "max_attempts": max_attempts,
            "retry_eligible": True,
            "retry_delay_seconds": self._retry_delay_seconds(job_status),
            "reason": "retryable_stage_failure",
            "error_code": error_code,
            "retryable_error_codes": retryable_error_codes,
        }

    def _get_stage_attempt_count(self, job_status) -> int:
        stage_name = job_status.current_stage or ""
        for stage_run in job_status.stage_runs:
            if stage_run.stage_name == stage_name:
                return max(1, stage_run.attempt_count)
        return 1

    async def _mark_dead_letter(self, job_status) -> None:
        retry_decision = self.inspect_retry_decision(job_status)
        async with AsyncSessionLocal() as session:
            repository = StorageRepository(session)
            await repository.update_pipeline_job(
                UUID(job_status.job_id),
                status="dead_letter",
                current_stage=job_status.current_stage,
            )
            await repository.create_pipeline_job_event(
                job_id=UUID(job_status.job_id),
                event_type="job_dead_lettered",
                stage_name=job_status.current_stage,
                status="dead_letter",
                payload={
                    "error_code": job_status.error_code,
                    "reason": retry_decision["reason"],
                    "stage_attempt_count": retry_decision["stage_attempt_count"],
                    "max_attempts": retry_decision["max_attempts"],
                },
            )
            await repository.create_audit_log(
                entity_type="pipeline_job",
                entity_id=UUID(job_status.job_id),
                action="pipeline_job_dead_lettered",
                actor="system",
                details={
                    "candidate_id": job_status.candidate_id,
                    "current_stage": job_status.current_stage,
                    "error_code": job_status.error_code,
                    "reason": retry_decision["reason"],
                    "stage_attempt_count": retry_decision["stage_attempt_count"],
                    "max_attempts": retry_decision["max_attempts"],
                },
            )
            await repository.commit()


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    worker = PipelineWorker()
    await worker.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
