import uuid
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Schema for incoming chat prompt requests."""
    conversation_id: uuid.UUID = Field(..., description="Target conversation identifier")
    message: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="User text message to the AI assistant",
    )


class ChatResponse(BaseModel):
    """Schema for AI generated assistant answers."""
    answer: str = Field(..., description="Generated markdown answer from the AI assistant")
