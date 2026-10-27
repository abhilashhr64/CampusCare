import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import (
    String,
    Integer,
    DateTime,
    ForeignKeyConstraint,
    UniqueConstraint,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from src.core.database import TenantBase


class Department(TenantBase):
    """Academic department within a college."""
    __tablename__ = "directory_departments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("college_id", "code", name="uq_departments_college_code"),
        UniqueConstraint("college_id", "id", name="uq_departments_college_id"),
    )


class Course(TenantBase):
    """Curricular subject/course offered by a department."""
    __tablename__ = "directory_courses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    department_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    credits: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    __table_args__ = (
        ForeignKeyConstraint(
            ["college_id", "department_id"],
            ["directory_departments.college_id", "directory_departments.id"],
            name="fk_courses_department_composite",
            ondelete="CASCADE",
        ),
        UniqueConstraint("college_id", "code", name="uq_courses_college_code"),
        UniqueConstraint("college_id", "id", name="uq_courses_college_id"),
    )


class ClassSection(TenantBase):
    """Specific cohort / section of a course in an academic term (Rule AZ-6)."""
    __tablename__ = "directory_class_sections"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    lecturer_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    section_name: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., "Sec A"
    semester: Mapped[int] = mapped_column(Integer, nullable=False)
    academic_year: Mapped[str] = mapped_column(String(20), nullable=False)  # e.g., "2026-2027"
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    __table_args__ = (
        ForeignKeyConstraint(
            ["college_id", "course_id"],
            ["directory_courses.college_id", "directory_courses.id"],
            name="fk_class_sections_course_composite",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["college_id", "lecturer_id"],
            ["users.college_id", "users.id"],
            name="fk_class_sections_lecturer_composite",
            ondelete="SET NULL",
        ),
        UniqueConstraint("college_id", "id", name="uq_class_sections_college_id"),
    )


class Enrollment(TenantBase):
    """Student roster enrollment in a class section."""
    __tablename__ = "directory_enrollments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    class_section_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    roll_number: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    __table_args__ = (
        ForeignKeyConstraint(
            ["college_id", "class_section_id"],
            ["directory_class_sections.college_id", "directory_class_sections.id"],
            name="fk_enrollments_section_composite",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["college_id", "student_id"],
            ["users.college_id", "users.id"],
            name="fk_enrollments_student_composite",
            ondelete="CASCADE",
        ),
        UniqueConstraint("college_id", "class_section_id", "student_id", name="uq_enrollments_student_section"),
        UniqueConstraint("college_id", "id", name="uq_enrollments_college_id"),
    )
