import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    String,
    Float,
    DateTime,
    ForeignKeyConstraint,
    UniqueConstraint,
    Index,
    Text,
    JSON,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from src.core.database import TenantBase


class AssistantConversation(TenantBase):
    """Student/Staff interactive conversation session with the grounded AI assistant."""
    __tablename__ = "assistant_conversations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), default="New Inquiry", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        ForeignKeyConstraint(
            ["college_id", "user_id"],
            ["users.college_id", "users.id"],
            name="fk_assistant_conv_user_composite",
            ondelete="CASCADE",
        ),
        UniqueConstraint("college_id", "id", name="uq_assistant_conversations_college_id"),
        Index("ix_assistant_conv_user", "college_id", "user_id"),
    )


class AssistantMessage(TenantBase):
    """Citation-grounded conversation turn with confidence score and proposed draft action (Rule B2, B3)."""
    __tablename__ = "assistant_messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    sender_role: Mapped[str] = mapped_column(String(20), nullable=False)  # USER, ASSISTANT
    content: Mapped[str] = mapped_column(Text, nullable=False)
    citations_json: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    routing_action: Mapped[str] = mapped_column(String(50), default="DIRECT_ANSWER", nullable=False)  # DIRECT_ANSWER, ROUTE_TO_DEPT, PROPOSED_DRAFT
    draft_action_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    __table_args__ = (
        ForeignKeyConstraint(
            ["college_id", "conversation_id"],
            ["assistant_conversations.college_id", "assistant_conversations.id"],
            name="fk_assistant_msg_conv_composite",
            ondelete="CASCADE",
        ),
        UniqueConstraint("college_id", "id", name="uq_assistant_messages_college_id"),
        Index("ix_assistant_msg_lookup", "college_id", "conversation_id", "created_at"),
    )
