import uuid
from datetime import datetime, timezone, date, time
from typing import Optional
from sqlalchemy import (
    String,
    Integer,
    DateTime,
    Date,
    Time,
    ForeignKeyConstraint,
    UniqueConstraint,
    Index,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from src.core.database import TenantBase


class AttendanceSession(TenantBase):
    """Lecture or laboratory session in which attendance is taken (Rule TN-1, C7)."""
    __tablename__ = "attendance_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    class_section_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    lecturer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    session_date: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    topic: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)  # Concurrency version (C7)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    __table_args__ = (
        ForeignKeyConstraint(
            ["college_id", "class_section_id"],
            ["directory_class_sections.college_id", "directory_class_sections.id"],
            name="fk_att_sessions_section_composite",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["college_id", "lecturer_id"],
            ["users.college_id", "users.id"],
            name="fk_att_sessions_lecturer_composite",
            ondelete="CASCADE",
        ),
        UniqueConstraint("college_id", "id", name="uq_attendance_sessions_college_id"),
        Index("ix_att_sessions_lookup", "college_id", "class_section_id", "session_date"),
    )


class AttendanceRecord(TenantBase):
    """Individual student attendance mark in a session."""
    __tablename__ = "attendance_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # PRESENT, ABSENT, EXCUSED
    remarks: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
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
            ["college_id", "session_id"],
            ["attendance_sessions.college_id", "attendance_sessions.id"],
            name="fk_att_records_session_composite",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["college_id", "student_id"],
            ["users.college_id", "users.id"],
            name="fk_att_records_student_composite",
            ondelete="CASCADE",
        ),
        UniqueConstraint("college_id", "session_id", "student_id", name="uq_att_records_student_session"),
        UniqueConstraint("college_id", "id", name="uq_attendance_records_college_id"),
        Index("ix_att_records_student_status", "college_id", "student_id", "status"),
    )
