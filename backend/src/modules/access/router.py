import uuid
from typing import List
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.core.database import get_app_db
from src.api.dependencies import require_permission, get_current_actor
from src.modules.access.policy import Actor, authorize
from src.modules.access.service import (
    AccessService,
    RoleGrantCreate,
    RoleGrantResponse,
)

router = APIRouter(prefix="/access", tags=["Access & Role Approvals"])


class RevokeRequest(BaseModel):
    reason: str


@router.get("/grants", response_model=List[RoleGrantResponse])
@require_permission("access:approve_role")
def list_role_grants(
    db: Session = Depends(get_app_db),
    actor: Actor = Depends(get_current_actor),
):
    decision = authorize(actor, "access:approve_role", resource={"college_id": actor.college_id if actor else None})
    if not decision.allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=decision.reason_code)

    return AccessService.get_role_grants_for_college(db, actor.college_id)


@router.post("/grants", response_model=RoleGrantResponse, status_code=status.HTTP_201_CREATED)
@require_permission("access:approve_role")
def grant_role(
    data: RoleGrantCreate,
    db: Session = Depends(get_app_db),
    actor: Actor = Depends(get_current_actor),
):
    decision = authorize(actor, "access:approve_role", resource={"college_id": actor.college_id if actor else None})
    if not decision.allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=decision.reason_code)

    grant = AccessService.grant_role(
        db,
        college_id=actor.college_id,
        granted_by=actor.user_id,
        data=data,
    )
    return grant


@router.post("/grants/{grant_id}/revoke", response_model=RoleGrantResponse)
@require_permission("access:revoke_role")
def revoke_role_grant(
    grant_id: uuid.UUID,
    data: RevokeRequest,
    db: Session = Depends(get_app_db),
    actor: Actor = Depends(get_current_actor),
):
    decision = authorize(actor, "access:revoke_role", resource={"college_id": actor.college_id if actor else None})
    if not decision.allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=decision.reason_code)

    try:
        revoked = AccessService.revoke_role(
            db,
            college_id=actor.college_id,
            grant_id=grant_id,
            revoked_by=actor.user_id,
            reason=data.reason,
        )
        return revoked
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
