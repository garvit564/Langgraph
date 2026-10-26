import uuid
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    conversation_id: uuid.UUID  # Ab thread_id ki jagah conversation_id aayegi
    message: str = Field(
        ...,
        min_length=1,
        max_length=10000,
    )


class ChatResponse(BaseModel):
    answer: str  # Ye pehle jaisa hi SAME hai