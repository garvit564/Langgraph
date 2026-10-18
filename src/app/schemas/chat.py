from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(
        min_length=1,
        max_length=10000,
    )
    thread_id: str = Field(
        min_length=1,
        max_length=100,
    )


class ChatResponse(BaseModel):
    answer: str # Direct, clean, natural formatted response