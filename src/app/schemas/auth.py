import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class UserRegister(BaseModel):
    """Schema for user registration requests."""
    email: str = Field(..., min_length=3, max_length=255, description="User email address")
    password: str = Field(..., min_length=6, max_length=100, description="Password (at least 6 characters)")


class UserLogin(BaseModel):
    """Schema for user login credentials."""
    email: str
    password: str


class TokenResponse(BaseModel):
    """Schema for JWT authentication token responses."""
    access_token: str
    token_type: str = "bearer"
    user_id: uuid.UUID
    email: str


class UserOut(BaseModel):
    """Public user profile schema."""
    id: uuid.UUID
    email: str
    created_at: datetime

    class Config:
        from_attributes = True
