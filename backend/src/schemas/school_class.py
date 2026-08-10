"""
School Class Schemas

Responsibility:
    Request and response models for class APIs.
"""

import uuid

from pydantic import BaseModel, ConfigDict


class CreateSchoolClassRequest(BaseModel):
    name: str


class UpdateSchoolClassRequest(BaseModel):
    name: str


class SchoolClassResponse(BaseModel):
    id: uuid.UUID
    name: str
    school_id: uuid.UUID
    school_name: str | None = None

    model_config = ConfigDict(
        from_attributes=True,
    )
