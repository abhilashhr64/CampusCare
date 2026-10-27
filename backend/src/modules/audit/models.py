import uuid
import hashlib
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy import (
    String,
    BigInteger,
    DateTime,
    ForeignKeyConstraint,
    UniqueConstraint,
    Index,
    JSON,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from src.core.database import TenantBase


class AuditLogEntry(TenantBase):
    """Append-only, hash-chained tamper-evident audit ledger (B3 signature capability)."""
    __tablename__ = "audit_log_entries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sequence_number: Mapped[int] = mapped_column(BigInteger, autoincrement=True, nullable=False, index=True)
    actor_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)
    resource_id: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    prev_entry_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    entry_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("college_id", "sequence_number", name="uq_audit_college_sequence"),
        UniqueConstraint("college_id", "id", name="uq_audit_college_id"),
        Index("ix_audit_lookup", "college_id", "action", "resource_type", "resource_id"),
    )

    @staticmethod
    def compute_hash(
        prev_hash: str,
        college_id: uuid.UUID,
        action: str,
        resource_type: str,
        resource_id: str,
        payload: Dict[str, Any],
        timestamp_str: str,
    ) -> str:
        """Computes deterministic SHA-256 hash chaining previous entry hash and new record."""
        canonical_payload = json.dumps(payload, sort_keys=True)
        raw_string = f"{prev_hash}|{college_id}|{action}|{resource_type}|{resource_id}|{canonical_payload}|{timestamp_str}"
        return hashlib.sha256(raw_string.encode("utf-8")).hexdigest()
