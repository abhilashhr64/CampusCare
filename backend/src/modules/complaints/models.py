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


class Complaint(TenantBase):
    """Complaint / grievance workflow entity with SLA clocks and closed-loop resolution (B3)."""
    __tablename__ = "complaints"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_number: Mapped[str] = mapped_column(String(50), nullable=False)
    creator_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # FACILITY, HOSTEL, ACADEMIC, IT, GRIEVANCE_SENSITIVE
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    location_tag: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)  # QR code location (B3)
    is_sensitive: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(30), default="SUBMITTED", nullable=False, index=True)  # SUBMITTED, ASSIGNED, IN_PROGRESS, RESOLVED, CLOSED, REOPENED
    assigned_to_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    assigned_department_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    sla_committed_hours: Mapped[int] = mapped_column(Integer, default=48, nullable=False)  # Service promise
    sla_deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    student_confirmed: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)  # Closed-loop resolution (B3)
    student_feedback_rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    student_feedback_comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        ForeignKeyConstraint(
            ["college_id", "creator_id"],
            ["users.college_id", "users.id"],
            name="fk_complaints_creator_composite",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["college_id", "assigned_to_user_id"],
            ["users.college_id", "users.id"],
            name="fk_complaints_assignee_composite",
            ondelete="SET NULL",
        ),
        UniqueConstraint("college_id", "ticket_number", name="uq_complaints_college_ticket"),
        UniqueConstraint("college_id", "id", name="uq_complaints_college_id"),
        Index("ix_complaints_status_deadline", "college_id", "status", "sla_deadline"),
    )


class ComplaintEvent(TenantBase):
    """Audit lifecycle event for complaint timeline and SLA tracking."""
    __tablename__ = "complaint_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    complaint_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    actor_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)  # CREATED, ASSIGNED, STATUS_CHANGE, RESOLVED, CONFIRMED, REOPENED
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    __table_args__ = (
        ForeignKeyConstraint(
            ["college_id", "complaint_id"],
            ["complaints.college_id", "complaints.id"],
            name="fk_complaint_events_complaint_composite",
            ondelete="CASCADE",
        ),
        UniqueConstraint("college_id", "id", name="uq_complaint_events_college_id"),
    )
