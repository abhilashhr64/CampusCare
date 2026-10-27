import uuid
from datetime import datetime, timezone, date
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    String,
    Integer,
    Boolean,
    DateTime,
    Date,
    ForeignKeyConstraint,
    UniqueConstraint,
    Index,
    Text,
    JSON,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.core.database import TenantBase


class KnowledgeDocument(TenantBase):
    """Institutional reference document (handbook, academic regulations, syllabus, guidelines) (C2, TN-6)."""
    __tablename__ = "knowledge_documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # ACADEMIC, HOSTEL, DISCIPLINE, IT, SCHOLARSHIP
    audience: Mapped[str] = mapped_column(String(50), default="ALL", nullable=False)  # ALL, STUDENT, STAFF, FACULTY
    source_ref: Mapped[str] = mapped_column(String(255), nullable=False)  # e.g., "Handbook 2026-27 Section 4.2"
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
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
        UniqueConstraint("college_id", "id", name="uq_knowledge_documents_college_id"),
        Index("ix_knowledge_documents_tenant_category", "college_id", "category"),
    )


class DocumentChunk(TenantBase):
    """Text chunk with embedding representation for hybrid citation-grounded retrieval (TN-6)."""
    __tablename__ = "document_chunks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding_json: Mapped[List[float]] = mapped_column(JSON, default=list, nullable=False)
    audience: Mapped[str] = mapped_column(String(50), default="ALL", nullable=False)
    validity_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    __table_args__ = (
        ForeignKeyConstraint(
            ["college_id", "document_id"],
            ["knowledge_documents.college_id", "knowledge_documents.id"],
            name="fk_doc_chunks_document_composite",
            ondelete="CASCADE",
        ),
        UniqueConstraint("college_id", "id", name="uq_document_chunks_college_id"),
        Index("ix_doc_chunks_search", "college_id", "document_id", "audience"),
    )
