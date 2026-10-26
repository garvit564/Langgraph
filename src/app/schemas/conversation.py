import uuid
from datetime import datetime
from pydantic import BaseModel, Field


# Request schema: Nayi conversation create karne ke liye (Title optional hai)
class ConversationCreate(BaseModel):
    title: str | None = Field(default="New Chat", max_length=255)


# Response schema: Conversation ki details return karne ke liye
class ConversationOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    thread_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Response schema: Chat bubble message return karne ke liye
class MessageOut(BaseModel):
    id: uuid.UUID
    conversation_id: uuid.UUID
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True