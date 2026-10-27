import uuid
from typing import List
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from src.core.database import get_app_db
from src.api.dependencies import get_current_actor, require_permission
from src.modules.access.policy import Actor
from src.modules.analytics.service import (
    AnalyticsService,
    DuplicateClusterOut,
    SlaRiskOut,
    AttendanceRiskOut,
    FeedbackThemeOut,
)

router = APIRouter(prefix="/analytics", tags=["Intelligence & Analytics"])


@router.post("/complaints/{complaint_id}/duplicates", response_model=List[DuplicateClusterOut])
@require_permission("analytics:view_duplicates")
def detect_duplicate_complaints(
    complaint_id: uuid.UUID,
    threshold: float = Query(0.35, ge=0.1, le=1.0),
    actor: Actor = Depends(get_current_actor),
    db: Session = Depends(get_app_db),
):
    """Detects co-located and textually similar duplicate complaints within the tenant (Rule B3)."""
    return AnalyticsService.detect_duplicate_complaints(
        db, actor.college_id, complaint_id, threshold=threshold
    )


@router.get("/sla-risks", response_model=List[SlaRiskOut])
@require_permission("analytics:view_sla_risk")
def assess_sla_risks(
    actor: Actor = Depends(get_current_actor),
    db: Session = Depends(get_app_db),
):
    """Calculates SLA deadline breach risk for department admins (Rule B1, B3)."""
    return AnalyticsService.assess_sla_risks(db, actor.college_id)


@router.post("/attendance-alerts/scan", response_model=List[AttendanceRiskOut])
@require_permission("analytics:manage_attendance_alerts")
def scan_attendance_deficits(
    target_percentage: float = Query(75.0, ge=50.0, le=100.0),
    actor: Actor = Depends(get_current_actor),
    db: Session = Depends(get_app_db),
):
    """Scans student attendance and triggers proactive supportive recovery alerts (Rule B1, B3)."""
    return AnalyticsService.generate_supportive_attendance_alerts(
        db, actor.college_id, target_percentage=target_percentage
    )


@router.get("/feedback-themes", response_model=List[FeedbackThemeOut])
@require_permission("analytics:view_feedback_themes")
def get_feedback_themes(
    cycle_id: uuid.UUID = Query(...),
    lecturer_id: uuid.UUID = Query(...),
    actor: Actor = Depends(get_current_actor),
    db: Session = Depends(get_app_db),
):
    """Extracts qualitative feedback themes under strict k-anonymity (Rule NR-10 & ADR-004)."""
    try:
        return AnalyticsService.aggregate_feedback_themes(
            db, actor.college_id, cycle_id, lecturer_id
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
