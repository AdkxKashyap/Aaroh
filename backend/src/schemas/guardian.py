"""
Guardian Schemas

Responsibility:
    Request and response models for guardian APIs.
"""

import uuid

from pydantic import BaseModel, ConfigDict


class CreateGuardianRequest(BaseModel):
    username: str
    email: str
    password: str


class GuardianLinkResponse(BaseModel):
    id: uuid.UUID
    guardian_user_id: uuid.UUID
    student_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)
