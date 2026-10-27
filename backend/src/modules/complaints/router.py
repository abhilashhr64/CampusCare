import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.core.database import get_app_db
from src.api.dependencies import require_permission, get_current_actor
from src.modules.access.policy import Actor, authorize
from src.modules.complaints.service import (
    ComplaintsService,
    ComplaintCreate,
    ComplaintResponse,
    AssignComplaintRequest,
    ResolveComplaintRequest,
    ResolutionConfirmRequest,
)

router = APIRouter(prefix="/complaints", tags=["Complaints & Service Promise"])


@router.post("", response_model=ComplaintResponse, status_code=status.HTTP_201_CREATED)
@require_permission("complaints:create")
def create_complaint(
    data: ComplaintCreate,
    db: Session = Depends(get_app_db),
    actor: Actor = Depends(get_current_actor),
):
    decision = authorize(actor, "complaints:create", resource={"college_id": actor.college_id if actor else None})
    if not decision.allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=decision.reason_code)

    return ComplaintsService.create_complaint(db, actor.college_id, actor.user_id, data)


@router.get("", response_model=List[ComplaintResponse])
@require_permission("complaints:read")
def list_complaints(
    db: Session = Depends(get_app_db),
    actor: Actor = Depends(get_current_actor),
):
    decision = authorize(actor, "complaints:read", resource={"college_id": actor.college_id if actor else None})
    if not decision.allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=decision.reason_code)

    return ComplaintsService.list_complaints(db, actor.college_id, actor)


@router.get("/{complaint_id}", response_model=ComplaintResponse)
@require_permission("complaints:read")
def get_complaint(
    complaint_id: uuid.UUID,
    db: Session = Depends(get_app_db),
    actor: Actor = Depends(get_current_actor),
):
    complaint = ComplaintsService.get_complaint(db, actor.college_id, complaint_id)
    if not complaint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found.")

    decision = authorize(
        actor,
        "complaints:read",
        resource={
            "college_id": actor.college_id,
            "creator_id": complaint.creator_id,
            "is_sensitive": complaint.is_sensitive,
        },
    )
    if not decision.allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=decision.reason_code)

    return complaint


@router.post("/{complaint_id}/assign", response_model=ComplaintResponse)
@require_permission("complaints:assign")
def assign_complaint(
    complaint_id: uuid.UUID,
    data: AssignComplaintRequest,
    db: Session = Depends(get_app_db),
    actor: Actor = Depends(get_current_actor),
):
    complaint = ComplaintsService.get_complaint(db, actor.college_id, complaint_id)
    if not complaint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found.")

    decision = authorize(
        actor,
        "complaints:assign",
        resource={"college_id": actor.college_id, "is_sensitive": complaint.is_sensitive},
    )
    if not decision.allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=decision.reason_code)

    return ComplaintsService.assign_complaint(db, actor.college_id, complaint_id, actor.user_id, data)


@router.post("/{complaint_id}/resolve", response_model=ComplaintResponse)
@require_permission("complaints:resolve")
def resolve_complaint(
    complaint_id: uuid.UUID,
    data: ResolveComplaintRequest,
    db: Session = Depends(get_app_db),
    actor: Actor = Depends(get_current_actor),
):
    complaint = ComplaintsService.get_complaint(db, actor.college_id, complaint_id)
    if not complaint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found.")

    decision = authorize(
        actor,
        "complaints:resolve",
        resource={"college_id": actor.college_id, "is_sensitive": complaint.is_sensitive},
    )
    if not decision.allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=decision.reason_code)

    return ComplaintsService.resolve_complaint(db, actor.college_id, complaint_id, actor.user_id, data)


@router.post("/{complaint_id}/closed-loop-confirm", response_model=ComplaintResponse)
@require_permission("complaints:create")
def confirm_or_reopen_resolution(
    complaint_id: uuid.UUID,
    data: ResolutionConfirmRequest,
    db: Session = Depends(get_app_db),
    actor: Actor = Depends(get_current_actor),
):
    """Closed-loop resolution: original student confirms or reopens the issue (Rule B3)."""
    try:
        return ComplaintsService.confirm_or_reopen(db, actor.college_id, complaint_id, actor.user_id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
