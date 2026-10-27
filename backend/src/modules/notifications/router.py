import uuid
from typing import List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from src.core.database import get_app_db
from src.api.dependencies import get_current_actor, require_permission
from src.modules.access.policy import Actor
from src.modules.notifications.service import (
    NotificationService,
    PreferenceUpdate,
    NotificationOut,
)

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("/preferences")
@require_permission("notifications:read")
def get_preferences(
    actor: Actor = Depends(get_current_actor),
    db: Session = Depends(get_app_db),
):
    """Retrieves user notification preferences under tenant RLS (Rule EV-3)."""
    return NotificationService.list_preferences(db, actor.college_id, actor.user_id)


@router.put("/preferences")
@require_permission("notifications:manage")
def update_preference(
    data: PreferenceUpdate,
    actor: Actor = Depends(get_current_actor),
    db: Session = Depends(get_app_db),
):
    """Updates user notification delivery preference."""
    return NotificationService.update_preference(db, actor.college_id, actor.user_id, data)


@router.get("/inbox", response_model=List[NotificationOut])
@require_permission("notifications:read")
def list_inbox(
    limit: int = Query(20, ge=1, le=100),
    actor: Actor = Depends(get_current_actor),
    db: Session = Depends(get_app_db),
):
    """Lists notifications delivered to current user under tenant isolation."""
    return NotificationService.list_user_notifications(db, actor.college_id, actor.user_id, limit=limit)
