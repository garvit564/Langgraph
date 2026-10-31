import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class ConversationCreate(BaseModel):
    """Schema for creating a new conversation."""
    title: str | None = Field(default="New Chat", max_length=255, description="Optional conversation title")


class ConversationOut(BaseModel):
    """Schema for public conversation details."""
    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    thread_id: str
    is_processing: bool = False
    cancel_requested: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MessageOut(BaseModel):
    """Schema for public chat message bubble items."""
    id: uuid.UUID
    conversation_id: uuid.UUID
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True
