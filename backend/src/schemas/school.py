"""
School Schemas

Responsibility:
    Request and response models for school APIs.
"""

import uuid

from pydantic import BaseModel, ConfigDict


class SchoolRegistrationRequest(BaseModel):
    name: str
    address: str | None = None


class SchoolResponse(BaseModel):
    id: uuid.UUID
    name: str
    address: str | None

    model_config = ConfigDict(
        from_attributes=True,
    )
