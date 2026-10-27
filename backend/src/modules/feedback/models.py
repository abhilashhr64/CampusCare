import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import (
    String,
    Integer,
    Boolean,
    DateTime,
    ForeignKeyConstraint,
    UniqueConstraint,
    Index,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from src.core.database import TenantBase


class FeedbackCycle(TenantBase):
    """Institutional evaluation window for course feedback."""
    __tablename__ = "feedback_cycles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    academic_term: Mapped[str] = mapped_column(String(50), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    k_anonymity_threshold: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("college_id", "id", name="uq_feedback_cycles_college_id"),
    )


class FeedbackParticipation(TenantBase):
    """Records voter participation to prevent duplicate voting (Rule NR-10, ADR-004).
    Contains ZERO link, reference, or key to the answers table.
    """
    __tablename__ = "feedback_participations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cycle_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    class_section_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    __table_args__ = (
        ForeignKeyConstraint(
            ["college_id", "cycle_id"],
            ["feedback_cycles.college_id", "feedback_cycles.id"],
            name="fk_fb_participations_cycle_composite",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["college_id", "student_id"],
            ["users.college_id", "users.id"],
            name="fk_fb_participations_student_composite",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["college_id", "class_section_id"],
            ["directory_class_sections.college_id", "directory_class_sections.id"],
            name="fk_fb_participations_section_composite",
            ondelete="CASCADE",
        ),
        UniqueConstraint("college_id", "cycle_id", "student_id", "class_section_id", name="uq_fb_student_vote_once"),
        UniqueConstraint("college_id", "id", name="uq_feedback_participations_college_id"),
    )


class FeedbackAnswer(TenantBase):
    """Cryptographically decoupled anonymous answer records (Rule NR-10, ADR-004).
    Physical unlinkability: NO student_id, NO participation_id, NO session_id, NO IP address.
    Timestamp is truncated to an epoch bucket to prevent millisecond correlation attacks.
    """
    __tablename__ = "feedback_answers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cycle_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    course_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    lecturer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    rating_pedagogy: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-5
    rating_clarity: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-5
    rating_engagement: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-5
    rating_punctuality: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-5
    comment_clean: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    epoch_bucket: Mapped[str] = mapped_column(String(30), nullable=False, index=True)  # e.g., '2026-10-27-B2'
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    __table_args__ = (
        ForeignKeyConstraint(
            ["college_id", "cycle_id"],
            ["feedback_cycles.college_id", "feedback_cycles.id"],
            name="fk_fb_answers_cycle_composite",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["college_id", "course_id"],
            ["directory_courses.college_id", "directory_courses.id"],
            name="fk_fb_answers_course_composite",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["college_id", "lecturer_id"],
            ["users.college_id", "users.id"],
            name="fk_fb_answers_lecturer_composite",
            ondelete="CASCADE",
        ),
        UniqueConstraint("college_id", "id", name="uq_feedback_answers_college_id"),
        Index("ix_fb_answers_lookup", "college_id", "course_id", "lecturer_id"),
    )
