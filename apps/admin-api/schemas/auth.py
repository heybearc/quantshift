"""Authentication schemas."""

from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from uuid import UUID

class LoginRequest(BaseModel):
    """Login request schema."""
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    """Token response schema."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class UserResponse(BaseModel):
    """User response schema."""
    id: UUID
    email: str
    full_name: Optional[str]
    role: str
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]

    class Config:
        from_attributes = True

class LoginResponse(BaseModel):
    """Login response schema."""
    user: UserResponse
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
