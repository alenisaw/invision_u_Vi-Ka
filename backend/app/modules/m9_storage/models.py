from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, LargeBinary, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class Candidate(Base):
    __tablename__ = "candidates"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    intake_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        default=uuid4,
        unique=True,
        index=True,
        nullable=False,
    )
    selected_program: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    pipeline_status: Mapped[str] = mapped_column(
        String(50),
        default="pending",
        index=True,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    pii_record: Mapped[CandidatePII | None] = relationship(
        back_populates="candidate",
        uselist=False,
        cascade="all, delete-orphan",
    )
    metadata_record: Mapped[CandidateMetadata | None] = relationship(
        back_populates="candidate",
        uselist=False,
        cascade="all, delete-orphan",
    )
    model_input_record: Mapped[CandidateModelInput | None] = relationship(
        back_populates="candidate",
        uselist=False,
        cascade="all, delete-orphan",
    )
    nlp_signal_record: Mapped[NLPSignal | None] = relationship(
        back_populates="candidate",
        uselist=False,
        cascade="all, delete-orphan",
    )
    score_record: Mapped[CandidateScore | None] = relationship(
        back_populates="candidate",
        uselist=False,
        cascade="all, delete-orphan",
    )
    explanation_record: Mapped[CandidateExplanation | None] = relationship(
        back_populates="candidate",
        uselist=False,
        cascade="all, delete-orphan",
    )
    reviewer_actions: Mapped[list[ReviewerAction]] = relationship(
        back_populates="candidate",
        cascade="all, delete-orphan",
    )


class CandidatePII(TimestampMixin, Base):
    __tablename__ = "candidate_pii"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    candidate_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("candidates.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    encrypted_data: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)

    candidate: Mapped[Candidate] = relationship(back_populates="pii_record")


class CandidateMetadata(TimestampMixin, Base):
    __tablename__ = "candidate_metadata"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    candidate_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("candidates.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    age_eligible: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    language_threshold_met: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    language_exam_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    has_video: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    data_completeness: Mapped[float | None] = mapped_column(Float, nullable=True)
    data_flags: Mapped[list | dict] = mapped_column(JSONB, default=list, nullable=False)

    candidate: Mapped[Candidate] = relationship(back_populates="metadata_record")


class CandidateModelInput(TimestampMixin, Base):
    __tablename__ = "candidate_model_inputs"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    candidate_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("candidates.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    video_transcript: Mapped[str | None] = mapped_column(Text, nullable=True)
    essay_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    internal_test_answers: Mapped[list | dict] = mapped_column(JSONB, default=list, nullable=False)
    project_descriptions: Mapped[list | dict] = mapped_column(JSONB, default=list, nullable=False)
    experience_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    asr_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    asr_flags: Mapped[list | dict] = mapped_column(JSONB, default=list, nullable=False)

    candidate: Mapped[Candidate] = relationship(back_populates="model_input_record")


class NLPSignal(TimestampMixin, Base):
    __tablename__ = "nlp_signals"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    candidate_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("candidates.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    signals: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    model_used: Mapped[str | None] = mapped_column(String(255), nullable=True)
    processing_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    candidate: Mapped[Candidate] = relationship(back_populates="nlp_signal_record")


class CandidateScore(TimestampMixin, Base):
    __tablename__ = "candidate_scores"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    candidate_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("candidates.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    sub_scores: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    review_priority_index: Mapped[float | None] = mapped_column(Float, nullable=True, index=True)
    recommendation_status: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    shortlist_eligible: Mapped[bool | None] = mapped_column(Boolean, nullable=True, index=True)
    ranking_position: Mapped[int | None] = mapped_column(Integer, nullable=True)
    scoring_version: Mapped[str | None] = mapped_column(String(50), nullable=True)

    candidate: Mapped[Candidate] = relationship(back_populates="score_record")


class CandidateExplanation(TimestampMixin, Base):
    __tablename__ = "candidate_explanations"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    candidate_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("candidates.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    positive_factors: Mapped[list | dict] = mapped_column(JSONB, default=list, nullable=False)
    caution_flags: Mapped[list | dict] = mapped_column(JSONB, default=list, nullable=False)
    data_quality_notes: Mapped[list | dict] = mapped_column(JSONB, default=list, nullable=False)
    reviewer_guidance: Mapped[str | None] = mapped_column(Text, nullable=True)

    candidate: Mapped[Candidate] = relationship(back_populates="explanation_record")


class ReviewerAction(TimestampMixin, Base):
    __tablename__ = "reviewer_actions"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    candidate_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("candidates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    reviewer_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    action_type: Mapped[str] = mapped_column(String(50), nullable=False)
    previous_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    new_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    candidate: Mapped[Candidate] = relationship(back_populates="reviewer_actions")


class AuditLog(TimestampMixin, Base):
    __tablename__ = "audit_log"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entity_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    actor: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    details: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)


class Program(TimestampMixin, Base):
    __tablename__ = "programs"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    key_competencies: Mapped[list | dict] = mapped_column(JSONB, default=list, nullable=False)
