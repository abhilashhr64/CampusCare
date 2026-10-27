import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.core.database import get_app_db
from src.api.dependencies import require_permission, get_current_actor
from src.modules.access.policy import Actor, authorize
from src.modules.attendance.service import (
    AttendanceService,
    SessionCreateRequest,
    SessionResponse,
    AttendanceOpEntry,
    SyncOutcome,
)

router = APIRouter(prefix="/attendance", tags=["Attendance Workflows"])


@router.post("/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
@require_permission("attendance:mark")
def create_attendance_session(
    data: SessionCreateRequest,
    db: Session = Depends(get_app_db),
    actor: Actor = Depends(get_current_actor),
):
    decision = authorize(
        actor,
        "attendance:mark",
        resource={"college_id": actor.college_id if actor else None, "class_section_id": data.class_section_id},
    )
    if not decision.allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=decision.reason_code)

    return AttendanceService.create_session(db, actor.college_id, actor.user_id, data)


@router.post("/sync", response_model=List[SyncOutcome])
@require_permission("attendance:sync_offline")
def sync_attendance_batch(
    batch: List[AttendanceOpEntry],
    db: Session = Depends(get_app_db),
    actor: Actor = Depends(get_current_actor),
):
    """Batch synchronization endpoint for offline attendance operations (Rule C7)."""
    decision = authorize(
        actor,
        "attendance:sync_offline",
        resource={"college_id": actor.college_id if actor else None},
    )
    if not decision.allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=decision.reason_code)

    return AttendanceService.sync_batch_operations(db, actor.college_id, actor.user_id, batch)


@router.get("/summary/me")
@require_permission("attendance:read")
def get_my_attendance_summary(
    db: Session = Depends(get_app_db),
    actor: Actor = Depends(get_current_actor),
):
    """Real-time attendance standing and what-if projection for authenticated student."""
    decision = authorize(
        actor,
        "attendance:read",
        resource={"college_id": actor.college_id if actor else None, "student_id": actor.user_id if actor else None},
    )
    if not decision.allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=decision.reason_code)

    return AttendanceService.get_student_overall_summary(db, actor.college_id, actor.user_id)
