import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Boolean, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.infrastructure.database import Base


def utc_now():
    """Returns current UTC timestamp with timezone awareness."""
    return datetime.now(timezone.utc)


class User(Base):
    """User account model for authentication and conversation ownership."""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    # Relationships
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")


class Conversation(Base):
    """Conversation session model mapped to a LangGraph checkpoint thread."""
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), default="New Chat", nullable=False)

    # Unique thread identifier mapped to LangGraph PostgreSQL checkpoints
    thread_id = Column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
        default=lambda: f"thread_{uuid.uuid4().hex[:12]}",
    )

    # Concurrency and generation lifecycle control
    is_processing = Column(Boolean, default=False, server_default=text("false"), nullable=False)
    cancel_requested = Column(Boolean, default=False, server_default=text("false"), nullable=False)

    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )


class Message(Base):
    """Individual chat bubble record associated with a conversation."""
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)

    # Message participant role ("user" or "assistant")
    role = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)

    created_at = Column(DateTime(timezone=True), default=utc_now)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
