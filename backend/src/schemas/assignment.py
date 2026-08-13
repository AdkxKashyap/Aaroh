"""
Assignment Schemas

Responsibility:
    Request and response models for assignment APIs.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, model_validator
from src.enums.assignment import AssignmentStatus


class CreateAssignmentRequest(BaseModel):
    title: str
    description: str
    due_date: datetime
    class_id: uuid.UUID | None = None
    class_name: str | None = None

    @model_validator(mode="after")
    def validate_class_reference(self):
        if self.class_id is None and not self.class_name:
            raise ValueError("Either class_id or class_name is required.")
        return self


class AssignmentResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: str
    due_date: datetime
    teacher_id: uuid.UUID
    class_id: uuid.UUID
    status: AssignmentStatus
    teacher_name: str | None = None
    class_name: str | None = None

    model_config = ConfigDict(
        from_attributes=True,
    )


class CreateAssignmentRequestWithClassName(BaseModel):
    title: str
    description: str
    due_date: datetime
    class_name: str
