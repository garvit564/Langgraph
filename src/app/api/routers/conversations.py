import logging
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.cancellation_manager import cancellation_manager
from app.infrastructure.database import get_db
from app.models.chat import Conversation, User
from app.schemas.conversation import ConversationCreate, ConversationOut, MessageOut
from app.services.conversation_service import (
    create_new_conversation,
    delete_conversation_by_id,
    get_messages_by_conversation_id,
    list_conversations_for_user,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/conversations", tags=["Conversations"])


@router.post("", response_model=ConversationOut, status_code=status.HTTP_201_CREATED)
def create_conversation(
    payload: ConversationCreate | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Creates a new conversation session for the authenticated user."""
    title = payload.title if payload else None
    return create_new_conversation(db=db, user_id=current_user.id, title=title)


@router.get("", response_model=list[ConversationOut])
def list_my_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieves all conversation sessions belonging to the authenticated user."""
    return list_conversations_for_user(db=db, user_id=current_user.id)


@router.get("/{conversation_id}/messages", response_model=list[MessageOut])
def get_conversation_messages(
    conversation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieves chronological message history for a specific conversation."""
    try:
        return get_messages_by_conversation_id(
            db=db,
            conversation_id=conversation_id,
            user_id=current_user.id,
        )
    except ValueError as e:
        logger.warning("Failed to fetch messages for conversation: %s (%s)", conversation_id, e)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post("/{conversation_id}/stop", status_code=status.HTTP_200_OK)
def stop_conversation(
    conversation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Instantly aborts an in-flight AI generation for a conversation.
    Cancels the underlying asyncio task immediately, terminates the LLM connection,
    releases conversation concurrency locks, and discards partial responses.
    """
    conv = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.user_id == current_user.id)
        .first()
    )
    if not conv:
        logger.warning("Stop request rejected: conversation %s not found for user: %s", conversation_id, current_user.id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found or access denied.",
        )

    # 1. Instantly abort the in-flight generation task in memory
    was_aborted = cancellation_manager.abort_task(conversation_id)

    # 2. Reset database concurrency locks immediately
    was_processing = conv.is_processing
    conv.is_processing = False
    conv.cancel_requested = True
    db.commit()

    logger.info("Generation aborted for conversation: %s (was_running: %s)", conversation_id, was_aborted or was_processing)
    return {
        "message": "Generation stopped immediately.",
        "was_running": was_aborted or was_processing,
    }


@router.delete("/{conversation_id}", status_code=status.HTTP_200_OK)
def delete_conversation(
    conversation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Deletes an entire conversation session and all its message history."""
    try:
        delete_conversation_by_id(
            db=db,
            conversation_id=conversation_id,
            user_id=current_user.id,
        )
        return {"message": "Conversation deleted successfully."}
    except ValueError as e:
        logger.warning("Failed to delete conversation: %s (%s)", conversation_id, e)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
