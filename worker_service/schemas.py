from pydantic import BaseModel, Field


class EmailTaskRequest(BaseModel):
    """Schema for requesting an asynchronous email dispatch."""
    to_email: str = Field(..., description="Recipient email address")
    subject: str = Field(..., min_length=1, max_length=255, description="Subject line")
    body: str = Field(..., min_length=1, description="Email content body")


class TaskResponse(BaseModel):
    """Schema for task dispatch acknowledgement."""
    task_id: str
    status: str = "queued"
    message: str


class TaskStatusResponse(BaseModel):
    """Schema for checking Celery task execution status."""
    task_id: str
    state: str
    result: dict | str | None = None
