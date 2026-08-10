"""
Student Schemas

Responsibility:
    Request and response models for student APIs.
"""

import uuid

from pydantic import BaseModel, ConfigDict, EmailStr


class CreateStudentRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    class_id: uuid.UUID


class StudentResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    school_id: uuid.UUID
    class_id: uuid.UUID
    username: str | None = None
    class_name: str | None = None
    school_name: str | None = None
    student_name: str | None = None

    model_config = ConfigDict(
        from_attributes=True,
    )
