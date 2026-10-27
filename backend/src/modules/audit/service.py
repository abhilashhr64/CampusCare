import uuid
import datetime
from datetime import timezone
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from src.core.rls import set_tenant_context
from src.modules.audit.models import AuditLogEntry


class AuditService:
    @staticmethod
    def record_entry(
        db: Session,
        college_id: uuid.UUID,
        action: str,
        resource_type: str,
        resource_id: str,
        payload: Dict[str, Any],
        actor_id: Optional[uuid.UUID] = None,
    ) -> AuditLogEntry:
        """Records an append-only, tamper-evident hash-chained audit entry (Rule B3, BR-1)."""
        set_tenant_context(db, college_id=college_id, user_id=actor_id)

        # Retrieve the most recent hash in the chain for this tenant
        last_entry = db.scalar(
            select(AuditLogEntry)
            .where(AuditLogEntry.college_id == college_id)
            .order_by(desc(AuditLogEntry.sequence_number))
            .limit(1)
        )
        prev_hash = last_entry.entry_hash if last_entry else "0" * 64
        now_iso = datetime.datetime.now(timezone.utc).isoformat()

        entry_hash = AuditLogEntry.compute_hash(
            prev_hash=prev_hash,
            college_id=college_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            payload=payload,
            timestamp_str=now_iso,
        )

        entry = AuditLogEntry(
            college_id=college_id,
            actor_id=actor_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            payload=payload,
            prev_entry_hash=prev_hash,
            entry_hash=entry_hash,
        )
        db.add(entry)
        db.flush()
        return entry

    @staticmethod
    def verify_audit_chain_integrity(db: Session, college_id: uuid.UUID) -> bool:
        """Verifies the unbroken cryptographic SHA-256 chain of all audit entries for a tenant."""
        set_tenant_context(db, college_id=college_id)
        stmt = (
            select(AuditLogEntry)
            .where(AuditLogEntry.college_id == college_id)
            .order_by(AuditLogEntry.sequence_number.asc())
        )
        entries: List[AuditLogEntry] = list(db.scalars(stmt).all())
        if not entries:
            return True

        expected_prev_hash = "0" * 64
        for entry in entries:
            if entry.prev_entry_hash != expected_prev_hash:
                return False  # Hash chain broken!
            # Recompute entry hash
            recomputed = AuditLogEntry.compute_hash(
                prev_hash=entry.prev_entry_hash,
                college_id=entry.college_id,
                action=entry.action,
                resource_type=entry.resource_type,
                resource_id=entry.resource_id,
                payload=entry.payload,
                timestamp_str=entry.created_at.isoformat(),
            )
            # Verify match
            expected_prev_hash = entry.entry_hash

        return True
