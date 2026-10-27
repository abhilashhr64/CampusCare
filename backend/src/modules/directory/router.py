import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.core.database import get_app_db
from src.api.dependencies import require_permission, get_current_actor
from src.modules.access.policy import Actor, authorize
from src.modules.directory.service import (
    DirectoryService,
    DepartmentCreate,
    DepartmentResponse,
    CourseCreate,
    CourseResponse,
    ClassSectionCreate,
    ClassSectionResponse,
)

router = APIRouter(prefix="/directory", tags=["Directory & Rosters"])


@router.get("/departments", response_model=List[DepartmentResponse])
@require_permission("directory:read")
def list_departments(
    db: Session = Depends(get_app_db),
    actor: Actor = Depends(get_current_actor),
):
    decision = authorize(actor, "directory:read", resource={"college_id": actor.college_id if actor else None})
    if not decision.allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=decision.reason_code)

    return DirectoryService.list_departments(db, actor.college_id)


@router.post("/departments", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
@require_permission("directory:manage_department")
def create_department(
    data: DepartmentCreate,
    db: Session = Depends(get_app_db),
    actor: Actor = Depends(get_current_actor),
):
    decision = authorize(actor, "directory:manage_department", resource={"college_id": actor.college_id if actor else None})
    if not decision.allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=decision.reason_code)

    return DirectoryService.create_department(db, actor.college_id, data)


@router.get("/courses", response_model=List[CourseResponse])
@require_permission("directory:read")
def list_courses(
    department_id: Optional[uuid.UUID] = None,
    db: Session = Depends(get_app_db),
    actor: Actor = Depends(get_current_actor),
):
    decision = authorize(actor, "directory:read", resource={"college_id": actor.college_id if actor else None})
    if not decision.allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=decision.reason_code)

    return DirectoryService.list_courses(db, actor.college_id, department_id)


@router.post("/courses", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
@require_permission("directory:manage_course")
def create_course(
    data: CourseCreate,
    db: Session = Depends(get_app_db),
    actor: Actor = Depends(get_current_actor),
):
    decision = authorize(
        actor,
        "directory:manage_course",
        resource={"college_id": actor.college_id if actor else None, "department_id": data.department_id},
    )
    if not decision.allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=decision.reason_code)

    return DirectoryService.create_course(db, actor.college_id, data)


@router.get("/classes", response_model=List[ClassSectionResponse])
@require_permission("directory:read")
def list_classes(
    lecturer_id: Optional[uuid.UUID] = None,
    db: Session = Depends(get_app_db),
    actor: Actor = Depends(get_current_actor),
):
    decision = authorize(actor, "directory:read", resource={"college_id": actor.college_id if actor else None})
    if not decision.allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=decision.reason_code)

    # Scoped lecturer access (Rule AZ-6)
    if "LECTURER" in actor.roles and not ({"COLLEGE_ADMIN", "DEPARTMENT_ADMIN"} & set(actor.roles)):
        lecturer_id = actor.user_id

    return DirectoryService.list_classes(db, actor.college_id, lecturer_id)
