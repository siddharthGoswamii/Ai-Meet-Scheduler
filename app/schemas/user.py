"""
User Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    display_name: str


class UserCreate(UserBase):
    """Schema for creating a user"""
    teams_user_id: str
    timezone: str = "UTC"


class UserUpdate(BaseModel):
    """Schema for updating a user"""
    display_name: Optional[str] = None
    timezone: Optional[str] = None


class UserResponse(BaseModel):
    """Schema for user response"""
    user_id: str
    email: str
    display_name: str
    timezone: str
    created_at: datetime
    last_login: Optional[datetime]
    
    class Config:
        from_attributes = True


class TokenData(BaseModel):
    """Schema for token data"""
    access_token: str
    refresh_token: str
    expires_at: datetime
    token_type: str = "bearer"

# Made with Bob
