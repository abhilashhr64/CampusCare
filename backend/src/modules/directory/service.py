import uuid
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session
from sqlalchemy import select
from src.core.rls import set_tenant_context
from src.modules.directory.models import Department, Course, ClassSection, Enrollment


class DepartmentCreate(BaseModel):
    code: str
    name: str


class DepartmentResponse(BaseModel):
    id: uuid.UUID
    college_id: uuid.UUID
    code: str
    name: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CourseCreate(BaseModel):
    department_id: uuid.UUID
    code: str
    title: str
    credits: int = 3


class CourseResponse(BaseModel):
    id: uuid.UUID
    college_id: uuid.UUID
    department_id: uuid.UUID
    code: str
    title: str
    credits: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ClassSectionCreate(BaseModel):
    course_id: uuid.UUID
    lecturer_id: Optional[uuid.UUID] = None
    section_name: str
    semester: int
    academic_year: str


class ClassSectionResponse(BaseModel):
    id: uuid.UUID
    college_id: uuid.UUID
    course_id: uuid.UUID
    lecturer_id: Optional[uuid.UUID]
    section_name: str
    semester: int
    academic_year: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DirectoryService:
    @staticmethod
    def list_departments(db: Session, college_id: uuid.UUID) -> List[Department]:
        set_tenant_context(db, college_id=college_id)
        stmt = select(Department).where(Department.college_id == college_id).order_by(Department.name)
        return list(db.scalars(stmt).all())

    @staticmethod
    def create_department(db: Session, college_id: uuid.UUID, data: DepartmentCreate) -> Department:
        set_tenant_context(db, college_id=college_id)
        dept = Department(
            college_id=college_id,
            code=data.code,
            name=data.name,
        )
        db.add(dept)
        db.commit()
        db.refresh(dept)
        return dept

    @staticmethod
    def list_courses(db: Session, college_id: uuid.UUID, department_id: Optional[uuid.UUID] = None) -> List[Course]:
        set_tenant_context(db, college_id=college_id)
        stmt = select(Course).where(Course.college_id == college_id)
        if department_id:
            stmt = stmt.where(Course.department_id == department_id)
        return list(db.scalars(stmt.order_by(Course.code)).all())

    @staticmethod
    def create_course(db: Session, college_id: uuid.UUID, data: CourseCreate) -> Course:
        set_tenant_context(db, college_id=college_id)
        course = Course(
            college_id=college_id,
            department_id=data.department_id,
            code=data.code,
            title=data.title,
            credits=data.credits,
        )
        db.add(course)
        db.commit()
        db.refresh(course)
        return course

    @staticmethod
    def list_classes(db: Session, college_id: uuid.UUID, lecturer_id: Optional[uuid.UUID] = None) -> List[ClassSection]:
        set_tenant_context(db, college_id=college_id)
        stmt = select(ClassSection).where(ClassSection.college_id == college_id)
        if lecturer_id:
            stmt = stmt.where(ClassSection.lecturer_id == lecturer_id)
        return list(db.scalars(stmt).all())

    @staticmethod
    def create_class_section(db: Session, college_id: uuid.UUID, data: ClassSectionCreate) -> ClassSection:
        set_tenant_context(db, college_id=college_id)
        section = ClassSection(
            college_id=college_id,
            course_id=data.course_id,
            lecturer_id=data.lecturer_id,
            section_name=data.section_name,
            semester=data.semester,
            academic_year=data.academic_year,
        )
        db.add(section)
        db.commit()
        db.refresh(section)
        return section

    @staticmethod
    def list_enrollments_with_course(db: Session, college_id: uuid.UUID) -> list[tuple[uuid.UUID, uuid.UUID, str, str]]:
        """Returns list of (student_id, class_section_id, course_code, course_title) under tenant RLS."""
        set_tenant_context(db, college_id=college_id)
        stmt = (
            select(Enrollment.student_id, ClassSection.id, Course.code, Course.title)
            .join(ClassSection, ClassSection.id == Enrollment.class_section_id)
            .join(Course, Course.id == ClassSection.course_id)
            .where(Enrollment.college_id == college_id)
        )
        return list(db.execute(stmt).all())
