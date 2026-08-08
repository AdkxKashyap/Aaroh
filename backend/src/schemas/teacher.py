"""
Teacher Schemas

Responsibility:
    Request models for teacher APIs.
"""

import uuid

from pydantic import BaseModel, EmailStr


class InviteTeacherRequest(BaseModel):
    username: str
    email: EmailStr
    password: str

class AssignTeacherRequest(BaseModel):
    class_id: uuid.UUID