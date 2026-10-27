import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from sqlalchemy import String, Integer, DateTime, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, Session
from sqlalchemy.dialects.postgresql import UUID
from src.core.database import Base
from src.core.rls import set_tenant_context


class OutboxEvent(Base):
    """Transactional Outbox Table (Rule EV-1).
    Ensures state changes and emitted events commit atomically in the same transaction.
    """
    __tablename__ = "outbox_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    college_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    topic: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    payload: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="PENDING", index=True)  # PENDING, PROCESSED, FAILED, DEAD_LETTER
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


def publish_event(
    session: Session,
    topic: str,
    payload: Dict[str, Any],
    college_id: Optional[uuid.UUID] = None,
) -> OutboxEvent:
    """Enqueues an event to the transactional outbox table within the caller's transaction."""
    if college_id and not session.info.get("college_id"):
        set_tenant_context(session, college_id=college_id)

    event = OutboxEvent(
        college_id=college_id,
        topic=topic,
        payload=payload,
        status="PENDING",
        created_at=datetime.now(timezone.utc),
    )
    session.add(event)
    return event
