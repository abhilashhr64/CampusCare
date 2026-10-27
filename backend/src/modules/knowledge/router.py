import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from src.core.database import get_app_db
from src.api.dependencies import get_current_actor, require_permission
from src.modules.access.policy import Actor
from src.modules.knowledge.service import (
    KnowledgeService,
    KnowledgeDocCreate,
    ChunkCreate,
    SearchResult,
)

router = APIRouter(prefix="/knowledge", tags=["Knowledge Base"])


@router.post("/documents", status_code=status.HTTP_201_CREATED)
@require_permission("knowledge:create")
def create_document(
    data: KnowledgeDocCreate,
    actor: Actor = Depends(get_current_actor),
    db: Session = Depends(get_app_db),
):
    """Registers an institutional document under tenant RLS (Rule TN-6)."""
    return KnowledgeService.create_document(db, actor.college_id, data)


@router.post("/documents/{doc_id}/chunks", status_code=status.HTTP_201_CREATED)
@require_permission("knowledge:create")
def add_chunks(
    doc_id: uuid.UUID,
    chunks: List[ChunkCreate],
    actor: Actor = Depends(get_current_actor),
    db: Session = Depends(get_app_db),
):
    """Ingests chunks into an institutional document."""
    return KnowledgeService.add_chunks(db, actor.college_id, doc_id, chunks)


@router.get("/search", response_model=List[SearchResult])
@require_permission("knowledge:read")
def search_knowledge(
    q: str = Query(..., min_length=2, description="Query string for hybrid semantic retrieval"),
    audience: Optional[str] = Query("ALL", description="Audience filter"),
    limit: int = Query(5, ge=1, le=20),
    actor: Actor = Depends(get_current_actor),
    db: Session = Depends(get_app_db),
):
    """Searches verified knowledge chunks strictly isolated to the caller's college (Rule TN-6)."""
    user_audience = "STUDENT" if "STUDENT" in actor.roles else "ALL"
    return KnowledgeService.search_chunks(
        db,
        actor.college_id,
        query=q,
        audience=user_audience if audience == "ALL" else audience,
        limit=limit,
    )
