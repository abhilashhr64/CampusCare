from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.core.database import get_app_db
from src.api.dependencies import require_permission, get_current_actor
from src.modules.access.policy import Actor, authorize
from src.modules.tenancy.service import TenancyService, CollegeResponse, CollegeCreate

router = APIRouter(prefix="/tenancy", tags=["Tenancy"])


@router.get("/colleges", response_model=List[CollegeResponse])
@require_permission("auth:login")
def list_active_colleges(
    db: Session = Depends(get_app_db),
    actor: Actor = Depends(get_current_actor),
):
    decision = authorize(actor, "auth:login")
    if not decision.allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=decision.reason_code)
    return TenancyService.get_all_active_colleges(db)
