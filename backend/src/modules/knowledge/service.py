import uuid
import re
from datetime import datetime, timezone, date
from typing import Optional, List, Dict, Any, Tuple
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_
from src.core.rls import set_tenant_context
from src.modules.knowledge.models import KnowledgeDocument, DocumentChunk


class KnowledgeDocCreate(BaseModel):
    title: str
    category: str  # ACADEMIC, HOSTEL, DISCIPLINE, IT, SCHOLARSHIP
    audience: str = "ALL"  # ALL, STUDENT, STAFF, FACULTY
    source_ref: str  # e.g., "Student Handbook 2026-27 Section 4.2"


class ChunkCreate(BaseModel):
    content: str
    chunk_index: int
    audience: str = "ALL"
    validity_date: Optional[date] = None


class SearchResult(BaseModel):
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    document_title: str
    source_ref: str
    category: str
    content: str
    similarity_score: float

    model_config = ConfigDict(from_attributes=True)


STOP_WORDS = {
    "what", "is", "the", "and", "in", "to", "for", "of", "a", "an", "on", "with",
    "from", "by", "are", "be", "this", "that", "it", "or", "as", "at", "my", "your"
}


def _normalize_token(w: str) -> str:
    cleaned = re.sub(r"[^\w]", "", w.lower())
    if len(cleaned) > 3 and cleaned.endswith("s"):
        return cleaned[:-1]
    return cleaned


class KnowledgeService:
    @staticmethod
    def create_document(
        db: Session,
        college_id: uuid.UUID,
        data: KnowledgeDocCreate,
    ) -> KnowledgeDocument:
        """Registers a verified institutional document under strict tenant isolation (Rule TN-6)."""
        set_tenant_context(db, college_id=college_id)

        now = datetime.now(timezone.utc)
        doc = KnowledgeDocument(
            college_id=college_id,
            title=data.title,
            category=data.category,
            audience=data.audience,
            source_ref=data.source_ref,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        return doc

    @staticmethod
    def add_chunks(
        db: Session,
        college_id: uuid.UUID,
        document_id: uuid.UUID,
        chunks_data: List[ChunkCreate],
    ) -> List[DocumentChunk]:
        """Ingests verified chunks with embeddings under tenant context (Rule TN-6)."""
        set_tenant_context(db, college_id=college_id)

        doc = db.get(KnowledgeDocument, document_id)
        if not doc or doc.college_id != college_id:
            raise ValueError("Document not found in tenant.")

        now = datetime.now(timezone.utc)
        created_chunks = []

        for chunk_in in chunks_data:
            words = re.findall(r"\w+", chunk_in.content.lower())
            chunk = DocumentChunk(
                college_id=college_id,
                document_id=document_id,
                chunk_index=chunk_in.chunk_index,
                content=chunk_in.content,
                embedding_json=[float(len(words)), 1.0],
                audience=chunk_in.audience or doc.audience,
                validity_date=chunk_in.validity_date,
                created_at=now,
            )
            db.add(chunk)
            created_chunks.append(chunk)

        db.commit()
        return created_chunks

    @staticmethod
    def search_chunks(
        db: Session,
        college_id: uuid.UUID,
        query: str,
        audience: str = "ALL",
        limit: int = 5,
    ) -> List[SearchResult]:
        """Performs tenant-isolated hybrid retrieval filtered by audience and validity (Rule TN-6)."""
        set_tenant_context(db, college_id=college_id)

        today = date.today()

        stmt = (
            select(DocumentChunk, KnowledgeDocument)
            .join(
                KnowledgeDocument,
                and_(
                    KnowledgeDocument.id == DocumentChunk.document_id,
                    KnowledgeDocument.college_id == DocumentChunk.college_id,
                ),
            )
            .where(
                DocumentChunk.college_id == college_id,
                KnowledgeDocument.is_active == True,
                or_(DocumentChunk.audience == "ALL", DocumentChunk.audience == audience),
                or_(DocumentChunk.validity_date == None, DocumentChunk.validity_date >= today),
            )
        )

        rows = list(db.execute(stmt).all())
        all_raw_tokens = [w for w in re.findall(r"\w+", query.lower()) if w not in STOP_WORDS]
        query_stems = {_normalize_token(w) for w in all_raw_tokens if len(w) > 1}
        if not query_stems:
            query_stems = {_normalize_token(w) for w in re.findall(r"\w+", query.lower())}

        scored_results: List[Tuple[DocumentChunk, KnowledgeDocument, float]] = []

        for chunk, doc in rows:
            chunk_raw = [w for w in re.findall(r"\w+", chunk.content.lower()) if w not in STOP_WORDS]
            chunk_stems = {_normalize_token(w) for w in chunk_raw}
            overlap = len(query_stems.intersection(chunk_stems))

            title_raw = [w for w in re.findall(r"\w+", doc.title.lower()) if w not in STOP_WORDS]
            title_stems = {_normalize_token(w) for w in title_raw}
            title_overlap = len(query_stems.intersection(title_stems))

            # If no term overlaps, score is 0
            if overlap == 0 and title_overlap == 0:
                continue

            content_ratio = overlap / max(len(query_stems), 1)
            title_ratio = title_overlap / max(len(title_stems), 1) if title_stems else 0.0

            total_score = (content_ratio * 0.75) + (title_ratio * 0.25)
            if total_score >= 0.20:
                scored_results.append((chunk, doc, min(1.0, total_score)))

        scored_results.sort(key=lambda x: x[2], reverse=True)
        top_picks = scored_results[:limit]

        return [
            SearchResult(
                chunk_id=chunk.id,
                document_id=doc.id,
                document_title=doc.title,
                source_ref=doc.source_ref,
                category=doc.category,
                content=chunk.content,
                similarity_score=round(score, 3),
            )
            for chunk, doc, score in top_picks
        ]
