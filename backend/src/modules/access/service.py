import uuid
import datetime
from datetime import timezone
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session
from sqlalchemy import select, update
from src.core.rls import set_tenant_context
from src.core.outbox import publish_event
from src.modules.access.models import RoleGrant
from src.modules.audit.service import AuditService


class RoleGrantCreate(BaseModel):
    user_id: uuid.UUID
    role: str
    scope: Dict[str, Any] = {}
    reason: str
    expires_at: Optional[datetime.datetime] = None


class RoleGrantResponse(BaseModel):
    id: uuid.UUID
    college_id: uuid.UUID
    user_id: uuid.UUID
    role: str
    scope: Dict[str, Any]
    granted_by: Optional[uuid.UUID]
    reason: str
    expires_at: Optional[datetime.datetime]
    is_revoked: bool
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class AccessService:
    @staticmethod
    def get_user_active_roles(db: Session, college_id: uuid.UUID, user_id: uuid.UUID) -> List[str]:
        """Returns the list of currently active granted role names for a user (Rule AZ-5)."""
        set_tenant_context(db, college_id=college_id)
        now = datetime.datetime.now(timezone.utc)
        stmt = (
            select(RoleGrant.role)
            .where(
                RoleGrant.college_id == college_id,
                RoleGrant.user_id == user_id,
                RoleGrant.is_revoked == False,
                (RoleGrant.expires_at == None) | (RoleGrant.expires_at > now),
            )
        )
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_role_grants_for_college(db: Session, college_id: uuid.UUID) -> List[RoleGrant]:
        set_tenant_context(db, college_id=college_id)
        stmt = (
            select(RoleGrant)
            .where(RoleGrant.college_id == college_id)
            .order_by(RoleGrant.created_at.desc())
        )
        return list(db.scalars(stmt).all())

    @staticmethod
    def grant_role(
        db: Session,
        college_id: uuid.UUID,
        granted_by: uuid.UUID,
        data: RoleGrantCreate,
    ) -> RoleGrant:
        """Grants an explicit role with approver, scope, and audit trail (Rule AZ-5, NR-5, BR-1)."""
        set_tenant_context(db, college_id=college_id, user_id=granted_by)

        grant = RoleGrant(
            college_id=college_id,
            user_id=data.user_id,
            role=data.role,
            scope=data.scope,
            granted_by=granted_by,
            reason=data.reason,
            expires_at=data.expires_at,
            is_revoked=False,
        )
        db.add(grant)
        db.flush()

        # Audit entry via AuditService interface (Rule BR-1, B3)
        AuditService.record_entry(
            db=db,
            college_id=college_id,
            actor_id=granted_by,
            action="ROLE_GRANTED",
            resource_type="access_role_grant",
            resource_id=str(grant.id),
            payload={
                "target_user_id": str(data.user_id),
                "role": data.role,
                "scope": data.scope,
                "reason": data.reason,
            },
        )

        # Transactional outbox event
        publish_event(
            db,
            topic="access.role_granted",
            payload={
                "grant_id": str(grant.id),
                "user_id": str(data.user_id),
                "role": data.role,
                "college_id": str(college_id),
            },
            college_id=college_id,
        )

        db.commit()
        db.refresh(grant)
        return grant

    @staticmethod
    def revoke_role(
        db: Session,
        college_id: uuid.UUID,
        grant_id: uuid.UUID,
        revoked_by: uuid.UUID,
        reason: str,
    ) -> RoleGrant:
        """Revokes a role grant and invalidates active sessions (Rule AZ-5, BR-1)."""
        set_tenant_context(db, college_id=college_id, user_id=revoked_by)

        grant = db.get(RoleGrant, grant_id)
        if not grant or grant.college_id != college_id:
            raise ValueError("Role grant not found.")

        now = datetime.datetime.now(timezone.utc)
        grant.is_revoked = True
        grant.revoked_by = revoked_by
        grant.revoked_at = now

        # Audit entry via AuditService interface (Rule BR-1, B3)
        AuditService.record_entry(
            db=db,
            college_id=college_id,
            actor_id=revoked_by,
            action="ROLE_REVOKED",
            resource_type="access_role_grant",
            resource_id=str(grant.id),
            payload={
                "grant_id": str(grant.id),
                "revoked_user_id": str(grant.user_id),
                "role": grant.role,
                "revocation_reason": reason,
            },
        )

        # Transactional outbox event
        publish_event(
            db,
            topic="access.role_revoked",
            payload={
                "grant_id": str(grant.id),
                "user_id": str(grant.user_id),
                "role": grant.role,
                "college_id": str(college_id),
            },
            college_id=college_id,
        )

        db.commit()
        db.refresh(grant)
        return grant
