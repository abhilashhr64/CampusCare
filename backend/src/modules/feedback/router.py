import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.core.database import get_app_db
from src.api.dependencies import require_permission, get_current_actor
from src.modules.access.policy import Actor, authorize
from src.modules.feedback.service import (
    FeedbackService,
    FeedbackCycleCreate,
    FeedbackCycleResponse,
    FeedbackSubmitRequest,
    FeedbackAggregateResponse,
)

router = APIRouter(prefix="/feedback", tags=["Anonymous Teacher Feedback"])


@router.post("/cycles", response_model=FeedbackCycleResponse, status_code=status.HTTP_201_CREATED)
@require_permission("access:approve_role")
def create_feedback_cycle(
    data: FeedbackCycleCreate,
    db: Session = Depends(get_app_db),
    actor: Actor = Depends(get_current_actor),
):
    decision = authorize(actor, "access:approve_role", resource={"college_id": actor.college_id if actor else None})
    if not decision.allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=decision.reason_code)

    return FeedbackService.create_cycle(db, actor.college_id, data)


@router.get("/cycles", response_model=List[FeedbackCycleResponse])
@require_permission("directory:read")
def list_feedback_cycles(
    db: Session = Depends(get_app_db),
    actor: Actor = Depends(get_current_actor),
):
    decision = authorize(actor, "directory:read", resource={"college_id": actor.college_id if actor else None})
    if not decision.allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=decision.reason_code)

    return FeedbackService.list_active_cycles(db, actor.college_id)


@router.post("/submit")
@require_permission("feedback:submit")
def submit_feedback(
    data: FeedbackSubmitRequest,
    db: Session = Depends(get_app_db),
    actor: Actor = Depends(get_current_actor),
):
    """Submits student feedback with cryptographic unlinkability (Rule NR-10)."""
    decision = authorize(actor, "feedback:submit", resource={"college_id": actor.college_id if actor else None})
    if not decision.allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=decision.reason_code)

    try:
        return FeedbackService.submit_anonymous_feedback(db, actor.college_id, actor.user_id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/aggregates/{lecturer_id}", response_model=FeedbackAggregateResponse)
@require_permission("feedback:view_aggregates")
def get_lecturer_feedback_aggregates(
    lecturer_id: uuid.UUID,
    cycle_id: uuid.UUID,
    db: Session = Depends(get_app_db),
    actor: Actor = Depends(get_current_actor),
):
    """Returns lecturer aggregate feedback with k-anonymity enforcement (Rule AZ-6, NR-10)."""
    # Check permission
    decision = authorize(actor, "feedback:view_aggregates", resource={"college_id": actor.college_id if actor else None, "response_count": 5})
    if not decision.allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=decision.reason_code)

    return FeedbackService.get_lecturer_aggregates(db, actor.college_id, lecturer_id, cycle_id)
