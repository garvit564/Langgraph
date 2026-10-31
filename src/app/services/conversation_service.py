import logging
import uuid
from sqlalchemy.orm import Session
from app.models.chat import Conversation, Message

logger = logging.getLogger(__name__)


def create_new_conversation(
    db: Session,
    user_id: uuid.UUID,
    title: str | None = None,
) -> Conversation:
    """Creates a new conversation session associated with the authenticated user."""
    conv_title = title.strip() if title and title.strip() else "New Chat"

    new_conv = Conversation(
        user_id=user_id,
        title=conv_title,
    )
    db.add(new_conv)
    db.commit()
    db.refresh(new_conv)
    logger.info("Created new conversation: %s (thread_id: %s) for user: %s", new_conv.id, new_conv.thread_id, user_id)
    return new_conv


def list_conversations_for_user(
    db: Session,
    user_id: uuid.UUID,
) -> list[Conversation]:
    """Retrieves all conversation sessions for the user, ordered by most recently updated."""
    conversations = (
        db.query(Conversation)
        .filter(Conversation.user_id == user_id)
        .order_by(Conversation.updated_at.desc())
        .all()
    )
    logger.debug("Retrieved %d conversations for user: %s", len(conversations), user_id)
    return conversations


def get_messages_by_conversation_id(
    db: Session,
    conversation_id: uuid.UUID,
    user_id: uuid.UUID,
) -> list[Message]:
    """Retrieves all chronological chat messages for a validated conversation."""
    # 1. Verify conversation exists and belongs to the requesting user
    conv = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.user_id == user_id)
        .first()
    )
    if not conv:
        logger.warning("Unauthorized or non-existent conversation access attempt: %s by user: %s", conversation_id, user_id)
        raise ValueError("Conversation not found or access denied.")

    # 2. Query ordered messages
    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
        .all()
    )
    logger.debug("Fetched %d messages for conversation: %s", len(messages), conversation_id)
    return messages


def delete_conversation_by_id(
    db: Session,
    conversation_id: uuid.UUID,
    user_id: uuid.UUID,
) -> bool:
    """Deletes a conversation and its messages via cascade delete after ownership validation."""
    conv = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.user_id == user_id)
        .first()
    )
    if not conv:
        logger.warning("Attempted deletion of non-existent or unowned conversation: %s by user: %s", conversation_id, user_id)
        raise ValueError("Conversation not found or access denied.")

    db.delete(conv)
    db.commit()
    logger.info("Deleted conversation: %s for user: %s", conversation_id, user_id)
    return True
