"""
User Schemas

Responsibility:
    Defines request and response models for user APIs.
"""

from uuid import UUID

from pydantic import BaseModel, EmailStr


class UserRegistrationRequest(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserUpdateRequest(BaseModel):
    email: EmailStr
    is_active: bool


class UserResponse(BaseModel):
    id: UUID
    username: str
    email: EmailStr

    class Config:
        from_attributes = True
