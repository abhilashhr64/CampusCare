import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.core.database import get_app_db
from src.api.dependencies import get_current_actor, require_permission
from src.modules.access.policy import Actor
from src.modules.assistant.service import (
    AssistantService,
    ConversationCreate,
    ChatRequest,
    ChatResponse,
)

router = APIRouter(prefix="/assistant", tags=["Campus AI Assistant"])


@router.post("/conversations", status_code=status.HTTP_201_CREATED)
@require_permission("assistant:chat")
def create_conversation(
    data: ConversationCreate,
    actor: Actor = Depends(get_current_actor),
    db: Session = Depends(get_app_db),
):
    """Initializes a new grounded assistant conversation under tenant context."""
    return AssistantService.create_conversation(db, actor.college_id, actor.user_id, data)


@router.get("/conversations")
@require_permission("assistant:chat")
def list_conversations(
    actor: Actor = Depends(get_current_actor),
    db: Session = Depends(get_app_db),
):
    """Lists recent conversations for the current user."""
    return AssistantService.list_conversations(db, actor.college_id, actor.user_id)


@router.get("/conversations/{conv_id}/messages")
@require_permission("assistant:chat")
def list_messages(
    conv_id: uuid.UUID,
    actor: Actor = Depends(get_current_actor),
    db: Session = Depends(get_app_db),
):
    """Lists message history in a conversation."""
    return AssistantService.list_messages(db, actor.college_id, actor.user_id, conv_id)


@router.post("/conversations/{conv_id}/chat")
@require_permission("assistant:chat")
def chat_with_assistant(
    conv_id: uuid.UUID,
    request: ChatRequest,
    actor: Actor = Depends(get_current_actor),
    db: Session = Depends(get_app_db),
):
    """Executes citation-grounded RAG with confidence routing and draft actions (Rule B2, B3)."""
    audience = "STUDENT" if "STUDENT" in actor.roles else "STAFF"
    req = ChatRequest(query=request.query, audience=audience)
    msg = AssistantService.chat_grounded(db, actor.college_id, actor.user_id, conv_id, req)
    return {
        "id": msg.id,
        "conversation_id": msg.conversation_id,
        "sender_role": msg.sender_role,
        "content": msg.content,
        "citations": msg.citations_json,
        "confidence_score": msg.confidence_score,
        "routing_action": msg.routing_action,
        "draft_action": msg.draft_action_json,
        "created_at": msg.created_at,
    }
