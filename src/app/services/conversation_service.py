import uuid
from sqlalchemy.orm import Session
from app.models.chat import Conversation, Message


def create_new_conversation(
    db: Session,
    user_id: uuid.UUID,
    title: str | None = None,
) -> Conversation:
    """Nayi conversation create karke database me save karta hai."""
    conv_title = title.strip() if title and title.strip() else "New Chat"

    new_conv = Conversation(
        user_id=user_id,
        title=conv_title,
    )
    db.add(new_conv)
    db.commit()
    db.refresh(new_conv)
    return new_conv


def list_conversations_for_user(
    db: Session,
    user_id: uuid.UUID,
) -> list[Conversation]:
    """Logged-in user ki saari conversations fetch karta hai (latest updated first)."""
    return (
        db.query(Conversation)
        .filter(Conversation.user_id == user_id)
        .order_by(Conversation.updated_at.desc())
        .all()
    )


def get_messages_by_conversation_id(
    db: Session,
    conversation_id: uuid.UUID,
    user_id: uuid.UUID,
) -> list[Message]:
    """Conversation ownership verify karke uske saare chat messages fetch karta hai."""
    # 1. Ownership check:
    conv = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.user_id == user_id)
        .first()
    )
    if not conv:
        raise ValueError("Conversation not found or access denied.")

    # 2. Fetch messages:
    return (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
        .all()
    )


def delete_conversation_by_id(
    db: Session,
    conversation_id: uuid.UUID,
    user_id: uuid.UUID,
) -> bool:
    """Conversation ownership verify karke use delete karta hai."""
    conv = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.user_id == user_id)
        .first()
    )
    if not conv:
        raise ValueError("Conversation not found or access denied.")

    db.delete(conv)
    db.commit()
    return True