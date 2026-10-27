import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import (
    String,
    Float,
    Integer,
    DateTime,
    ForeignKeyConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from src.core.database import Base


class ComplaintDuplicateCluster(Base):
    """Tracks potential duplicate complaint tickets detected via NLP similarity and location matching (Rule B3, TN-1)."""
    __tablename__ = "complaint_duplicate_clusters"
    __table_args__ = (
        ForeignKeyConstraint(
            ["college_id", "canonical_complaint_id"],
            ["complaints.college_id", "complaints.id"],
            ondelete="CASCADE",
            name="fk_complaint_dup_canonical",
        ),
        ForeignKeyConstraint(
            ["college_id", "duplicate_complaint_id"],
            ["complaints.college_id", "complaints.id"],
            ondelete="CASCADE",
            name="fk_complaint_dup_duplicate",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    college_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    canonical_complaint_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    duplicate_complaint_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    similarity_score: Mapped[float] = mapped_column(Float, nullable=False)
    detected_reason: Mapped[str] = mapped_column(String(255), nullable=False)  # CO_LOCATED_AND_TEXT_OVERLAP, SEMANTIC_MATCH
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )


class FeedbackThemeAggregate(Base):
    """Stores k-anonymized thematic summaries extracted from qualitative feedback (Rule NR-10 & ADR-004)."""
    __tablename__ = "feedback_theme_aggregates"
    __table_args__ = (
        ForeignKeyConstraint(
            ["college_id", "cycle_id"],
            ["feedback_cycles.college_id", "feedback_cycles.id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["college_id", "lecturer_id"],
            ["users.college_id", "users.id"],
            ondelete="CASCADE",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    college_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    cycle_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    lecturer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    theme_tag: Mapped[str] = mapped_column(String(100), nullable=False)  # LAB_CLARITY, PACING, HOMEWORK_SUPPORT
    sentiment_polarity: Mapped[str] = mapped_column(String(20), nullable=False)  # POSITIVE, CONSTRUCTIVE, NEUTRAL
    mention_count: Mapped[int] = mapped_column(Integer, nullable=False)
    summary_text: Mapped[str] = mapped_column(String(500), nullable=False)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )


class SlaRiskAssessment(Base):
    """Predicts deadline breach risk for active complaints based on SLA countdown and queue depth (Rule B1, B3)."""
    __tablename__ = "sla_risk_assessments"
    __table_args__ = (
        ForeignKeyConstraint(
            ["college_id", "complaint_id"],
            ["complaints.college_id", "complaints.id"],
            ondelete="CASCADE",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    college_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    complaint_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    hours_remaining: Mapped[float] = mapped_column(Float, nullable=False)
    projected_breach_probability: Mapped[float] = mapped_column(Float, nullable=False)
    assessed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )


class AttendanceRiskAlert(Base):
    """Proactive supportive alert for students whose attendance is approaching deficit thresholds (Rule B1, B3)."""
    __tablename__ = "attendance_risk_alerts"
    __table_args__ = (
        ForeignKeyConstraint(
            ["college_id", "student_id"],
            ["users.college_id", "users.id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["college_id", "class_section_id"],
            ["directory_class_sections.college_id", "directory_class_sections.id"],
            ondelete="CASCADE",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    college_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    class_section_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    conducted_count: Mapped[int] = mapped_column(Integer, nullable=False)
    attended_count: Mapped[int] = mapped_column(Integer, nullable=False)
    current_percentage: Mapped[float] = mapped_column(Float, nullable=False)
    classes_needed_for_safe: Mapped[int] = mapped_column(Integer, nullable=False)
    alert_status: Mapped[str] = mapped_column(String(30), default="ACTIVE", nullable=False)  # ACTIVE, RECOVERED, ACKNOWLEDGED
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
