import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from src.core.rls import set_tenant_context
from src.modules.knowledge.service import KnowledgeService, SearchResult
from src.modules.assistant.models import AssistantConversation, AssistantMessage


class ConversationCreate(BaseModel):
    title: Optional[str] = "New Campus Inquiry"


class ChatRequest(BaseModel):
    query: str
    audience: Optional[str] = "STUDENT"


class Citation(BaseModel):
    document_title: str
    source_ref: str
    category: str
    excerpt: str


class ChatResponse(BaseModel):
    message_id: uuid.UUID
    conversation_id: uuid.UUID
    sender_role: str
    content: str
    citations: List[Citation]
    confidence_score: float
    routing_action: str  # DIRECT_ANSWER, ROUTE_TO_DEPT, PROPOSED_DRAFT
    draft_action: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AssistantService:
    @staticmethod
    def create_conversation(
        db: Session,
        college_id: uuid.UUID,
        user_id: uuid.UUID,
        data: ConversationCreate,
    ) -> AssistantConversation:
        """Initializes a new assistant conversation under tenant RLS."""
        set_tenant_context(db, college_id=college_id, user_id=user_id)

        now = datetime.now(timezone.utc)
        conv = AssistantConversation(
            college_id=college_id,
            user_id=user_id,
            title=data.title or "New Campus Inquiry",
            created_at=now,
            updated_at=now,
        )
        db.add(conv)
        db.commit()
        db.refresh(conv)
        return conv

    @staticmethod
    def list_conversations(
        db: Session,
        college_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> List[AssistantConversation]:
        set_tenant_context(db, college_id=college_id, user_id=user_id)
        stmt = (
            select(AssistantConversation)
            .where(
                AssistantConversation.college_id == college_id,
                AssistantConversation.user_id == user_id,
            )
            .order_by(desc(AssistantConversation.updated_at))
        )
        return list(db.scalars(stmt).all())

    @staticmethod
    def list_messages(
        db: Session,
        college_id: uuid.UUID,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID,
    ) -> List[AssistantMessage]:
        set_tenant_context(db, college_id=college_id, user_id=user_id)
        stmt = (
            select(AssistantMessage)
            .where(
                AssistantMessage.college_id == college_id,
                AssistantMessage.conversation_id == conversation_id,
            )
            .order_by(AssistantMessage.created_at.asc())
        )
        return list(db.scalars(stmt).all())

    @staticmethod
    def chat_grounded(
        db: Session,
        college_id: uuid.UUID,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID,
        request: ChatRequest,
    ) -> AssistantMessage:
        """Executes citation-grounded RAG with confidence-aware routing and confirmed draft actions (Rule B2, B3, TN-6)."""
        set_tenant_context(db, college_id=college_id, user_id=user_id)

        conv = db.get(AssistantConversation, conversation_id)
        if not conv or conv.college_id != college_id or conv.user_id != user_id:
            raise ValueError("Conversation not found or unauthorized.")

        now = datetime.now(timezone.utc)

        # 1. Record incoming user message
        user_msg = AssistantMessage(
            college_id=college_id,
            conversation_id=conversation_id,
            sender_role="USER",
            content=request.query,
            citations_json=[],
            confidence_score=1.0,
            routing_action="NONE",
            draft_action_json=None,
            created_at=now,
        )
        db.add(user_msg)

        # 2. Retrieve grounded verified institutional chunks under strict tenant scoping (TN-6)
        results: List[SearchResult] = KnowledgeService.search_chunks(
            db=db,
            college_id=college_id,
            query=request.query,
            audience=request.audience or "STUDENT",
            limit=3,
        )

        # 3. Compute Grounding Confidence Score
        # Top score dictates certainty; empty yields 0.0
        top_score = results[0].similarity_score if results else 0.0

        citations_list = [
            {
                "document_title": r.document_title,
                "source_ref": r.source_ref,
                "category": r.category,
                "excerpt": r.content[:200] + ("..." if len(r.content) > 200 else ""),
            }
            for r in results
        ]

        # 4. Confidence-Aware Routing (Rule B2, B3)
        if top_score >= 0.50:
            # High Confidence: Direct Grounded Answer with verified citations
            top_chunk = results[0]
            answer_content = (
                f"According to verified institutional policy in **{top_chunk.document_title}** ({top_chunk.source_ref}):\n\n"
                f"> {top_chunk.content}\n\n"
                f"Institutional Reference Citation: `[{top_chunk.document_title} - {top_chunk.source_ref}]`"
            )
            routing_action = "DIRECT_ANSWER"
            draft_action = None

        elif top_score >= 0.25:
            # Medium Confidence: Qualified answer + Suggest contacting Department Admin
            top_chunk = results[0]
            answer_content = (
                f"We found relevant reference guidelines in **{top_chunk.document_title}** ({top_chunk.source_ref}), "
                f"but your inquiry may involve department-specific conditions:\n\n"
                f"> {top_chunk.content}\n\n"
                f"Recommendation: For definitive clarification, please consult your department academic advisor."
            )
            routing_action = "ROUTE_TO_DEPT"
            draft_action = {
                "action_type": "CONTACT_DEPARTMENT",
                "recommended_department": top_chunk.category,
                "inquiry_summary": request.query,
            }

        else:
            # Low Confidence: Explicitly prevent hallucination and offer a Confirmed Draft Action (Rule B3, B4)
            answer_content = (
                "I could not locate an official policy covering this specific question in the institutional knowledge base. "
                "Rather than guessing, I have prepared a draft grievance/inquiry ticket for human staff review. "
                "Would you like to confirm and submit this ticket?"
            )
            routing_action = "PROPOSED_DRAFT"
            draft_action = {
                "action_type": "CREATE_COMPLAINT_DRAFT",
                "category": "ACADEMIC",
                "title": f"Inquiry regarding: {request.query[:80]}",
                "description": f"Automated inquiry draft raised by student via Campus AI assistant. Query: {request.query}",
                "location_tag": "CAMPUS-PORTAL-AI",
                "sla_committed_hours": 48,
                "requires_confirmation": True,
            }

        # 5. Persist assistant response
        assistant_msg = AssistantMessage(
            college_id=college_id,
            conversation_id=conversation_id,
            sender_role="ASSISTANT",
            content=answer_content,
            citations_json=citations_list,
            confidence_score=top_score,
            routing_action=routing_action,
            draft_action_json=draft_action,
            created_at=datetime.now(timezone.utc),
        )
        db.add(assistant_msg)

        conv.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(assistant_msg)
        return assistant_msg
